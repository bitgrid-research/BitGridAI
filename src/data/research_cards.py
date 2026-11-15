"""Research cards for the dashboard: night balance and forecast vs. actual.

Nightly cron on the HA host (after the KPI rebuild). Opens ``bitgrid.db``
read-only and writes ``www/research_cards.json`` for the Forschung tab:

- **Akku über Nacht**: every night from dusk to dawn, with the SoC at which the
  miners stopped, the SoC in the morning, house consumption and grid import.
  Monthly verdict on the seasonal reserve ("Hausreserve", ADR 028): its goal
  is 15 % left in the morning. Only nights after mining days can judge the
  reserve; on days without mining the battery was not drained by the miners.
- **Solarprognose**: daily PV forecast (``pv_forecast_kw``) against the
  measured PV energy. Basis for R4 (forecast veto) and for knowing how far the
  forecast can be trusted.

The same night logic feeds the KI hamster (``src/explain/bithamster_season``),
so the card and the hamster can never disagree. Pure read-only reporting: no
entity, no automation, no feedback into thresholds.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from src.data import automation_cards, thesis_notes
from src.data.recording_status import open_readonly, write_atomic

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1

# Longest night per month in hours, identical to sensor.mvp_saison_status,
# automation.mvp_saison_automatik and the "Saisonale Schwellwerte" card.
NIGHT_HOURS: dict[int, float] = {
    1: 15.75,
    2: 14.5833,
    3: 12.9667,
    4: 11.0667,
    5: 9.3167,
    6: 8.0,
    7: 8.8167,
    8: 10.5,
    9: 12.3167,
    10: 14.1333,
    11: 15.5167,
    12: 15.85,
}
# ADR 033 (13.11.2026): the formula has three measured terms besides the
# base load. Defaults = initial values in mvp_auto.yaml.
#   Hausreserve = Grundlast x (Nacht + Abendluecke) / (Akku x Wirkungsgrad) + Boden
# Until 13.11.2026 the floor was a fixed 15 % (10 % deep-discharge + 5 %
# buffer); the SMA discharges to 0 %, so only the 5 % buffer remains.
RESERVE_FLOOR_PCT = 5.0
EVENING_GAP_H = 0.75
EFFICIENCY = 0.80
RESERVE_CAP_PCT = 95.0
# Offsets above the stop threshold, as in mvp_saison_automatik.
OFFSETS = {"eco": 10, "std_off": 20, "std": 25, "super_off": 35, "super": 40}
# Same fallbacks as mvp_auto.yaml; measured median since 28.08.2026 (ADR 033).
BASELOAD_DEFAULT_W = 570.0
CAPACITY_DEFAULT_KWH = 12.5

# The live formula exists since 27.08.2026 (ADR 028); earlier nights ran
# under other thresholds and would blur the check.
FORMULA_SINCE = "2026-08-28"
# ADR 033 went live on this day. Nights before it ran with the old formula;
# a verdict built only from them describes a problem that is already fixed.
RESERVE_FORMULA_V2_SINCE = "2026-11-13"
MIN_BLOCKS_PER_DAY = 140
PV_DARK_W = 20.0
MINER_ON_W = 300.0
MIN_NIGHTS = 5
MIN_MINED_NIGHTS = 3
# Verdict around the floor (target = floor in the morning): below
# max(floor - 3, 1) the battery ran (nearly) empty, above floor + 15 the
# miners could have run longer.
VERDICT_LOW_MARGIN_PCT = 3.0
VERDICT_HIGH_MARGIN_PCT = 15.0
EMPTY_PCT = 1.0
RULE_TOLERANCE_PCT = 3.0
RULE_HOLDS_SHARE = 0.8

CARD_NIGHTS = 14
CARD_FORECAST_DAYS = 14
# Offset between the block holding a forecast value and the block it is
# compared with. forecast.yaml asks Open-Meteo for "now + 60 min", but the
# sensor only refreshes hourly and Open-Meteo values are hourly means, so the
# stored value describes roughly the current hour. Determined from the data
# (13.11.2026): offsets of -30/0/+30/+60 min gave a log-ratio spread over the
# hours of 0.23/0.17/0.41/0.76 (July) and 0.44/0.22/0.26/0.52 (October);
# 0 is flattest in both. The first version used 60 min and showed a false
# "afternoons far too high" pattern.
FORECAST_LEAD_BLOCKS = 0
MIN_FORECAST_SHARE = 0.9
# Days with less PV are left out of the error: a tiny denominator turns a
# few hundred Wh into a huge percentage.
MIN_FORECAST_KWH = 1.0


def season_table(
    baseload_w: float,
    capacity_kwh: float,
    gap_h: float = EVENING_GAP_H,
    efficiency: float = EFFICIENCY,
    floor_pct: float = RESERVE_FLOOR_PCT,
) -> list[dict[str, Any]]:
    """The twelve rows of the "Saisonale Schwellwerte" card, same formula.

    Values over 100 % are not reachable in that month; the tier follows the
    start threshold (Standard/Super blocked), as in sensor.mvp_saison_status.
    """
    rows = []
    usable = capacity_kwh * efficiency
    for month, hours in NIGHT_HOURS.items():
        reserve = (
            baseload_w * (hours + gap_h) / 1000 / usable * 100 if usable > 0 else 100
        )
        stop = min(floor_pct + reserve, RESERVE_CAP_PCT)
        if stop + OFFSETS["super"] <= 100:
            tier = "Voll (Eco/Standard/Super)"
        elif stop + OFFSETS["std"] <= 100:
            tier = "Eco + Standard"
        else:
            tier = "Nur Eco"
        row: dict[str, Any] = {
            "month": month,
            "night_h": hours,
            "night_kwh": baseload_w * (hours + gap_h) / 1000,
            "stop": round(stop),
            "tier": tier,
        }
        for key, off in OFFSETS.items():
            row[key] = round(stop + off) if stop + off <= 100 else None
        if row["std"] is None:
            row["std_off"] = None
        if row["super"] is None:
            row["super_off"] = None
        rows.append(row)
    return rows


def _battery_need_w(row: tuple[Any, ...]) -> float:
    """House load without miners that the sun does not cover (W, one block).

    Between miner stop and sunset the PV still covers part of the house, so
    the plain house load would overstate what the battery has to deliver.
    Battery losses are ignored, which makes a "too low" verdict conservative.
    """
    house, miner, pv = (row[3] or 0.0), row[4], (row[1] or 0.0)
    return float(max(house - miner - pv, 0.0))


# A day with at least this many blocks that are not quality=ok (warn or
# error) is left out of every day-based card. Since 14.11.2026 this also
# covers blocks that were stored but not measured (frozen values or 0 W
# house load, marked by ha_history_sync); before, they counted as measured.
UNMEASURED_MIN_BLOCKS = 6


def unmeasured_days(conn: sqlite3.Connection) -> set[str]:
    """Days with at least UNMEASURED_MIN_BLOCKS blocks that are not ok."""
    try:
        rows = conn.execute(
            "SELECT substr(block_id, 1, 10) FROM energy_states"
            " WHERE quality <> 'ok' GROUP BY 1 HAVING COUNT(*) >= ?",
            (UNMEASURED_MIN_BLOCKS,),
        ).fetchall()
    except sqlite3.OperationalError:
        return set()
    return {str(r[0]) for r in rows}


def night_rows(
    conn: sqlite3.Connection, since: str = FORMULA_SINCE
) -> list[dict[str, Any]]:
    """One entry per measured night since ``since`` (energy_states, read-only).

    A night runs from the last block with PV >= 20 W on day d to the first
    such block on day d+1 (UTC dates; the dark hours never cross a UTC date
    boundary here). Days with fewer than 140 of 144 blocks are skipped, as are
    nights whose SoC rises (charging or filled-in data). For days on which the
    miners ran (> 300 W), the energy from the last mining block to the morning
    is what the stop threshold has to cover.
    """
    try:
        rows = conn.execute(
            "SELECT block_id, pv_power_w, battery_soc_pct, house_load_w,"
            " COALESCE(miner_power_w, 0), COALESCE(grid_import_w, 0)"
            " FROM energy_states WHERE block_id >= ? ORDER BY block_id",
            (since,),
        ).fetchall()
    except sqlite3.OperationalError:  # table missing (fresh or partial DB)
        return []
    days: dict[str, list[tuple[Any, ...]]] = defaultdict(list)
    for row in rows:
        days[str(row[0])[:10]].append(row)

    out: list[dict[str, Any]] = []
    ordered = sorted(days)
    skip = unmeasured_days(conn)
    for day, nxt in zip(ordered, ordered[1:]):
        a, b = days[day], days[nxt]
        if len(a) < MIN_BLOCKS_PER_DAY or len(b) < MIN_BLOCKS_PER_DAY:
            continue
        if day in skip or nxt in skip:
            continue
        lit_a = [r for r in a if (r[1] or 0) >= PV_DARK_W]
        lit_b = [r for r in b if (r[1] or 0) >= PV_DARK_W]
        if not lit_a or not lit_b:
            continue
        eve, morn = lit_a[-1], lit_b[0]
        if eve[2] is None or morn[2] is None or morn[2] > eve[2] + 2:
            continue
        both = a + b
        night = [r for r in both if eve[0] < r[0] < morn[0]]
        if not night:
            continue
        entry: dict[str, Any] = {
            "day": day,
            "dusk": str(eve[0]),
            "dawn": str(morn[0]),
            "hours": len(night) / 6,
            "load_kwh": sum(_battery_need_w(r) for r in night) / 6000,
            "grid_kwh": sum(r[5] for r in night) / 6000,
            "eve_soc": float(eve[2]),
            "morning_soc": float(morn[2]),
            "mined": False,
            "stop_block": None,
            "stop_soc": None,
            "from_stop_kwh": None,
        }
        mined = [r for r in a if r[4] > MINER_ON_W and r[2] is not None]
        if mined:
            last = mined[-1]
            after = [r for r in both if last[0] < r[0] < morn[0]]
            entry.update(
                mined=True,
                stop_block=str(last[0]),
                stop_soc=float(last[2]),
                from_stop_kwh=sum(_battery_need_w(r) for r in after) / 6000,
            )
        out.append(entry)
    return out


def low_limit(floor_pct: float) -> float:
    """Morning SoC below this after a mining day: reserve too low."""
    return max(floor_pct - VERDICT_LOW_MARGIN_PCT, EMPTY_PCT)


def summarize_nights(
    nights: list[dict[str, Any]],
    capacity_kwh: float,
    efficiency: float = EFFICIENCY,
    floor_pct: float = RESERVE_FLOOR_PCT,
) -> dict[int, dict[str, Any]]:
    """Aggregate night_rows per calendar month."""
    per_month: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for night in nights:
        per_month[int(night["day"][5:7])].append(night)
    result: dict[int, dict[str, Any]] = {}
    for month, group in per_month.items():
        n = len(group)
        hours = sum(x["hours"] for x in group)
        with_mining = [x for x in group if x["mined"]]
        summary: dict[str, Any] = {
            "nights": n,
            "last_day": max(x["day"] for x in group),
            "night_h": hours / n,
            "load_kwh": sum(x["load_kwh"] for x in group) / n,
            "load_w": (
                sum(x["load_kwh"] for x in group) * 1000 / hours if hours else None
            ),
            "morning_soc": sum(x["morning_soc"] for x in group) / n,
            "morning_low": sum(
                1 for x in group if x["morning_soc"] < low_limit(floor_pct)
            ),
            "floor_pct": floor_pct,
            "grid_kwh": sum(x["grid_kwh"] for x in group),
            # Only this part can a higher reserve avoid: on days without
            # mining the battery was not drained by the miners.
            "grid_kwh_after_mining": sum(x["grid_kwh"] for x in with_mining),
            "mined_nights": len(with_mining),
            "stop_socs": [x["stop_soc"] for x in with_mining],
            "morning_after_mining": None,
            "from_stop_kwh": None,
            "needed_stop": None,
        }
        if with_mining:
            k = len(with_mining)
            from_stop = sum(x["from_stop_kwh"] for x in with_mining) / k
            summary["morning_after_mining"] = (
                sum(x["morning_soc"] for x in with_mining) / k
            )
            summary["from_stop_kwh"] = from_stop
            if capacity_kwh > 0 and efficiency > 0:
                summary["needed_stop"] = min(
                    from_stop / (capacity_kwh * efficiency) * 100 + floor_pct, 100.0
                )
        result[month] = summary
    return result


def night_check(
    conn: sqlite3.Connection,
    capacity_kwh: float,
    since: str = FORMULA_SINCE,
    efficiency: float = EFFICIENCY,
    floor_pct: float = RESERVE_FLOOR_PCT,
) -> dict[int, dict[str, Any]]:
    """Measured nights per calendar month since ``since`` (read-only)."""
    return summarize_nights(
        night_rows(conn, since), capacity_kwh, efficiency, floor_pct
    )


def reserve_verdict(check: dict[str, Any]) -> str | None:
    """ "zu_niedrig" / "zu_hoch" / "passt", or None without enough mining days."""
    if check["nights"] < MIN_NIGHTS or check["mined_nights"] < MIN_MINED_NIGHTS:
        return None
    morning = check["morning_after_mining"]
    floor = check.get("floor_pct", RESERVE_FLOOR_PCT)
    if morning < low_limit(floor):
        return "zu_niedrig"
    if morning > floor + VERDICT_HIGH_MARGIN_PCT:
        return "zu_hoch"
    return "passt"


def rule_holds(check: dict[str, Any], target: float) -> tuple[int, bool]:
    """(days stopped at the threshold ±3 %, True if that is >= 80 % of mining days)."""
    at_stop = sum(
        1 for v in check["stop_socs"] if abs(v - target) <= RULE_TOLERANCE_PCT
    )
    return at_stop, at_stop >= RULE_HOLDS_SHARE * check["mined_nights"]


def forecast_days(
    conn: sqlite3.Connection, now: datetime, days: int = CARD_FORECAST_DAYS
) -> list[dict[str, Any]]:
    """Daily PV forecast vs. measured PV for the last ``days`` complete days.

    Block b is compared with the forecast stored FORECAST_LEAD_BLOCKS blocks
    earlier (0, determined from the data, see the constant). Days
    with fewer than 140 blocks, or with a forecast in less than 90 % of the
    blocks, are left out.
    """
    end = now.astimezone(timezone.utc).strftime("%Y-%m-%d")
    start_dt = now.astimezone(timezone.utc) - timedelta(days=days + 1)
    try:
        rows = conn.execute(
            "SELECT block_id, pv_power_w, pv_forecast_kw FROM energy_states"
            " WHERE block_id >= ? AND block_id < ? ORDER BY block_id",
            (start_dt.strftime("%Y-%m-%d"), end),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    forecast_by_block = {str(r[0]): r[2] for r in rows}
    per_day: dict[str, list[tuple[float, float | None]]] = defaultdict(list)
    for block_id, pv, _ in rows:
        ts = datetime.fromisoformat(str(block_id))
        earlier = (ts - timedelta(minutes=10 * FORECAST_LEAD_BLOCKS)).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        per_day[str(block_id)[:10]].append(
            (float(pv or 0.0), forecast_by_block.get(earlier))
        )
    first_day = (now.astimezone(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%d"
    )
    frozen = frozen_forecast_days(conn) | unmeasured_days(conn)
    out = []
    for day in sorted(per_day):
        if day < first_day or day in frozen:
            continue
        blocks = per_day[day]
        with_fc = [fc for _, fc in blocks if fc is not None]
        if len(blocks) < MIN_BLOCKS_PER_DAY or len(with_fc) < MIN_FORECAST_SHARE * len(
            blocks
        ):
            continue
        actual = sum(pv for pv, _ in blocks) / 6000
        forecast = sum(float(fc) for fc in with_fc) / 6
        out.append(
            {
                "day": day,
                "actual_kwh": round(actual, 2),
                "forecast_kwh": round(forecast, 2),
                "error_pct": (
                    round((forecast - actual) / actual * 100, 1)
                    if actual >= MIN_FORECAST_KWH
                    else None
                ),
            }
        )
    return out


# A forecast above this value in the night hours (UTC 22-01) is a frozen
# value, not a forecast: 27.-31.05. and 14.-19.08.2026 the stored forecast
# stood on one number (6.87 / 7.41 kW) day and night (found 14.11.2026).
FORECAST_NIGHT_MAX_KW = 0.05
# Not 02 UTC: the stored value is the forecast for the next hour, and in
# June that is already sunrise (first version flagged half of June).
NIGHT_HOURS_UTC = ("22", "23", "00", "01")


def frozen_forecast_days(conn: sqlite3.Connection) -> set[str]:
    """Days whose stored forecast is a held value (see FORECAST_NIGHT_MAX_KW)."""
    marks = ",".join("?" * len(NIGHT_HOURS_UTC))
    try:
        rows = conn.execute(
            "SELECT DISTINCT substr(block_id, 1, 10) FROM energy_states"
            f" WHERE substr(block_id, 12, 2) IN ({marks}) AND pv_forecast_kw > ?",
            (*NIGHT_HOURS_UTC, FORECAST_NIGHT_MAX_KW),
        ).fetchall()
    except sqlite3.OperationalError:
        return set()
    return {str(r[0]) for r in rows}


def forecast_months(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Forecast against measured PV per month over the whole recording.

    The card's 14 days are all winter days since November; alone they read
    as "the forecast is useless" (hamster, live 14.11.2026). Per month the
    picture is a season pattern: July 12 % too low, November 75 % too high,
    worst in the morning. The model is irradiance x kWp x 0.75 without
    horizon shading, which hurts most at low winter sun. Same day rules as
    forecast_days (complete days, forecast in 90 % of the blocks).
    """
    try:
        rows = conn.execute(
            "SELECT substr(block_id, 1, 10), COUNT(*), COUNT(pv_forecast_kw),"
            " SUM(COALESCE(pv_power_w, 0)) / 6000.0,"
            " SUM(pv_forecast_kw) / 6.0 FROM energy_states GROUP BY 1"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    frozen = frozen_forecast_days(conn) | unmeasured_days(conn)
    acc: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0, 0])
    for day, blocks, with_fc, actual, forecast in rows:
        a = acc[str(day)[:7]]
        a[3] += 1
        if blocks < MIN_BLOCKS_PER_DAY or with_fc < MIN_FORECAST_SHARE * blocks:
            continue
        if str(day) in frozen:
            continue
        if float(actual or 0) < MIN_FORECAST_KWH:
            continue
        a[0] += float(actual)
        a[1] += float(forecast or 0)
        a[2] += 1
    return [
        {
            "month": month,
            "days": int(a[2]),
            "days_total": int(a[3]),
            "actual_kwh": round(a[0]),
            "forecast_kwh": round(a[1]),
            "bias_pct": round((a[1] - a[0]) / a[0] * 100, 1) if a[0] else None,
        }
        for month, a in sorted(acc.items())
    ]


def forecast_by_hour(
    conn: sqlite3.Connection, days: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Mean actual vs. forecast PV power per local hour over the usable days.

    Shows WHEN the forecast is off. Hour = local time of the server (the
    house). Only meaningful with the right time alignment, see
    FORECAST_LEAD_BLOCKS.
    """
    usable = {d["day"] for d in days if d["error_pct"] is not None}
    if not usable:
        return []
    first, last = min(usable), max(usable)
    rows = conn.execute(
        "SELECT block_id, pv_power_w, pv_forecast_kw FROM energy_states"
        " WHERE block_id >= ? AND block_id < ? ORDER BY block_id",
        (
            (datetime.fromisoformat(first) - timedelta(days=1)).strftime("%Y-%m-%d"),
            (datetime.fromisoformat(last) + timedelta(days=1)).strftime("%Y-%m-%d"),
        ),
    ).fetchall()
    fc = {str(r[0]): r[2] for r in rows}
    acc: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for block_id, pv, _ in rows:
        if str(block_id)[:10] not in usable:
            continue
        ts = datetime.fromisoformat(str(block_id)).replace(tzinfo=timezone.utc)
        earlier = (ts - timedelta(minutes=10 * FORECAST_LEAD_BLOCKS)).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        f = fc.get(earlier)
        if f is None:
            continue
        a = acc[ts.astimezone().hour]
        a[0] += float(pv or 0.0) / 1000
        a[1] += float(f)
        a[2] += 1
    return [
        {
            "hour": h,
            "actual_kw": round(v[0] / v[2], 2),
            "forecast_kw": round(v[1] / v[2], 2),
        }
        for h, v in sorted(acc.items())
        if v[2] and (v[0] > 0 or v[1] > 0)
    ]


def forecast_summary(days: list[dict[str, Any]]) -> dict[str, Any]:
    """Bias (sum forecast vs. sum actual) and mean absolute daily error."""
    usable = [d for d in days if d["error_pct"] is not None]
    actual = sum(d["actual_kwh"] for d in usable)
    forecast = sum(d["forecast_kwh"] for d in usable)
    return {
        "days_used": len(usable),
        "bias_pct": round((forecast - actual) / actual * 100, 1) if actual else None,
        "mae_pct": (
            round(sum(abs(d["error_pct"]) for d in usable) / len(usable), 1)
            if usable
            else None
        ),
    }


# Miner efficiency trend (hamster proposal 13.11.2026, "Werden die Miner
# schlechter?"). W/TH of a whole day mixes the modes (Super needs ~2 W/TH
# more than Eco), so the raw daily value moved 16.2 -> 17.2 -> 16.4 with the
# season, not with wear. Only days in one single mode are comparable: Eco
# for at least EFF_MIN_ECO_H hours and no Standard/Super minute.
EFF_MIN_ECO_H = 2.0
# Change of the monthly Eco median against the first month that counts as
# drift (fans/paste/hashboard); measured spread of the Eco days is ~±2 %.
EFF_DRIFT_PCT = 5.0
EFF_MIN_DAYS = 3


def efficiency_trend(conn: sqlite3.Connection) -> dict[str, Any]:
    """Monthly median W/TH per miner on pure-Eco days (read-only)."""
    try:
        rows = conn.execute(
            "SELECT miner, day, w_per_th FROM daily_miner_kpi"
            " WHERE w_per_th IS NOT NULL AND h_eco >= ?"
            " AND COALESCE(h_standard, 0) = 0 AND COALESCE(h_super, 0) = 0"
            " ORDER BY miner, day",
            (EFF_MIN_ECO_H,),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    groups: dict[str, dict[str, list[float]]] = {}
    # Same day rule as the other cards (15.11.2026): days with blocks that
    # were stored but not measured (filled-in values) are left out.
    skip = unmeasured_days(conn)
    for miner, day, wpt in rows:
        if str(day)[:10] in skip:
            continue
        groups.setdefault(str(miner), {}).setdefault(str(day)[:7], []).append(
            float(wpt)
        )
    miners = []
    for miner, by_month in sorted(groups.items()):
        months: list[dict[str, Any]] = [
            {"month": m, "days": len(v), "w_per_th": round(statistics.median(v), 2)}
            for m, v in sorted(by_month.items())
        ]
        valid = [m for m in months if int(m["days"]) >= EFF_MIN_DAYS]
        change = (
            round(
                (float(valid[-1]["w_per_th"]) / float(valid[0]["w_per_th"]) - 1) * 100,
                1,
            )
            if len(valid) >= 2
            else None
        )
        miners.append(
            {
                "miner": miner,
                "months": months,
                "change_pct": change,
                "verdict": (
                    None
                    if change is None
                    else "schlechter" if change > EFF_DRIFT_PCT else "stabil"
                ),
            }
        )
    return {
        "min_eco_h": EFF_MIN_ECO_H,
        "drift_pct": EFF_DRIFT_PCT,
        "min_days": EFF_MIN_DAYS,
        "miners": miners,
    }


# "Akku-Hoechststand vs. Ziel" (hamster proposal 13.11.2026). R7 in
# mvp_auto.yaml starts Eco at SoC >= Eco start once the cooldown since the
# last stop is over (1 h; 15 min if PV >= pv_start). The sun is no start
# condition (first version of this card wrongly required both). Per day:
# highest SoC, highest PV, and the blocks with SoC >= Eco start.
PEAK_DAYS = 14
PV_START_DEFAULT_W = 6000.0


def peak_days(
    conn: sqlite3.Connection,
    now: datetime,
    table: dict[int, dict[str, Any]],
    pv_start_w: float,
    days: int = PEAK_DAYS,
) -> list[dict[str, Any]]:
    """Last ``days`` complete days: SoC/PV peak against the Eco start (read-only)."""
    today = now.astimezone(timezone.utc).date()
    start = (today - timedelta(days=days)).isoformat()
    try:
        rows = conn.execute(
            "SELECT block_id, battery_soc_pct, pv_power_w FROM energy_states"
            " WHERE block_id >= ? AND block_id < ? ORDER BY block_id",
            (start, today.isoformat()),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    by_day: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for block, soc, pv in rows:
        if soc is not None and pv is not None:
            by_day[str(block)[:10]].append((float(soc), float(pv)))
    skip = unmeasured_days(conn)
    out = []
    for day in sorted(by_day):
        blocks = by_day[day]
        if len(blocks) < MIN_BLOCKS_PER_DAY or day in skip:
            continue
        eco = table[int(day[5:7])]["eco"] or 100
        both = sum(1 for soc, _ in blocks if soc >= eco)
        out.append(
            {
                "day": day,
                "soc_max": round(max(soc for soc, _ in blocks), 1),
                "pv_max_w": round(max(pv for _, pv in blocks)),
                "eco_start": eco,
                "pv_start_w": pv_start_w,
                "start_blocks": both,
                "missing": None if both else "akku",
            }
        )
    return out


# Winter priority (13.11.2026, user decision): the battery first, mining
# second. The AC ELWA 2 heating rod regulates on the meter surplus by itself
# and is read-only in HA; from 15.10. to 13.11.2026 it took 46 kWh of PV,
# all of it while the battery was below 95 %, and the battery was empty
# every November morning. Measured here so a change on the device shows.
WINTER_MONTHS = (11, 12, 1, 2)
BATTERY_FULL_PCT = 95.0
EMPTY_MORNING_PCT = 5.0


def heizstab_vs_battery(
    conn: sqlite3.Connection, now: datetime, days: int = PEAK_DAYS
) -> dict[str, Any]:
    """Heating-rod energy while the battery was not full, last ``days`` days."""
    today = now.astimezone(timezone.utc).date()
    start = (today - timedelta(days=days)).isoformat()
    try:
        rows = conn.execute(
            "SELECT substr(block_id, 1, 10), COALESCE(heizstab_power_w, 0),"
            " battery_soc_pct, substr(block_id, 12, 2) FROM energy_states"
            " WHERE block_id >= ? AND block_id < ? ORDER BY block_id",
            (start, today.isoformat()),
        ).fetchall()
    except sqlite3.OperationalError:
        return {"days": 0}
    per_day: dict[str, dict[str, float]] = {}
    for day, heiz_w, soc, hour in rows:
        d = per_day.setdefault(day, {"kwh": 0.0, "kwh_not_full": 0.0, "blocks": 0})
        d["blocks"] += 1
        kwh = float(heiz_w) / 6000.0  # 10-minute block
        d["kwh"] += kwh
        if soc is not None and float(soc) < BATTERY_FULL_PCT:
            d["kwh_not_full"] += kwh
        # Morning = the 06 UTC block row (07 local in winter): battery level.
        if hour == "06" and soc is not None and "morning" not in d:
            d["morning"] = float(soc)
    skip = unmeasured_days(conn)
    full = {
        k: v
        for k, v in per_day.items()
        if v["blocks"] >= MIN_BLOCKS_PER_DAY and k not in skip
    }
    return {
        "days": len(full),
        "heizstab_kwh": round(sum(v["kwh"] for v in full.values()), 1),
        "heizstab_kwh_not_full": round(
            sum(v["kwh_not_full"] for v in full.values()), 1
        ),
        "empty_mornings": sum(
            1 for v in full.values() if v.get("morning", 100.0) < EMPTY_MORNING_PCT
        ),
    }


# Formula inputs: key -> (HA entity, default, factor to the internal unit).
FORMULA_ENTITIES: dict[str, tuple[str, float, float]] = {
    "baseload_w": ("input_number.mvp_night_baseload_w", BASELOAD_DEFAULT_W, 1.0),
    "capacity_kwh": ("input_number.battery_capacity_kwh", CAPACITY_DEFAULT_KWH, 1.0),
    "gap_h": ("input_number.mvp_evening_gap_h", EVENING_GAP_H, 1.0),
    "efficiency": ("input_number.mvp_battery_efficiency_pct", EFFICIENCY, 0.01),
    "floor_pct": ("input_number.mvp_reserve_floor_pct", RESERVE_FLOOR_PCT, 1.0),
    # Not a formula term; the start condition for the peak card.
    "pv_start_w": ("input_number.mvp_pv_start_w", PV_START_DEFAULT_W, 1.0),
}


def default_settings() -> dict[str, float]:
    return {k: d for k, (_, d, _) in FORMULA_ENTITIES.items()}


def settings_from_states(states: dict[str, dict[str, Any]]) -> dict[str, float]:
    """Formula inputs from HA states; missing/unavailable -> documented default."""
    out = default_settings()
    for key, (entity, _, factor) in FORMULA_ENTITIES.items():
        try:
            out[key] = float(str((states.get(entity) or {}).get("state"))) * factor
        except (TypeError, ValueError):
            pass
    return out


def build_cards(
    conn: sqlite3.Connection,
    now: datetime,
    settings: dict[str, float] | None = None,
    settings_source: str = "default",
) -> dict[str, Any]:
    """Everything the two cards show, as one JSON-serialisable dict."""
    st = settings or default_settings()
    capacity_kwh = st["capacity_kwh"]
    table = {
        r["month"]: r
        for r in season_table(
            st["baseload_w"],
            capacity_kwh,
            st["gap_h"],
            st["efficiency"],
            st["floor_pct"],
        )
    }
    nights = night_rows(conn)
    months = summarize_nights(nights, capacity_kwh, st["efficiency"], st["floor_pct"])
    month_rows = []
    for month in sorted(months):
        c = months[month]
        target = table[month]["stop"]
        at_stop, holds = rule_holds(c, target) if c["mined_nights"] else (0, False)
        old_formula = str(c.get("last_day") or "") < RESERVE_FORMULA_V2_SINCE
        # 15.11.2026: before ADR 033 another formula set the stop; today's
        # target says nothing about those nights. The measured stop (SoC at
        # the last mining block, median) is what applied then.
        stop_measured = (
            round(statistics.median(c["stop_socs"])) if c["stop_socs"] else None
        )
        month_rows.append(
            {
                "month": month,
                "stop_target": target,
                "nights": c["nights"],
                "mined_nights": c["mined_nights"],
                "at_stop": at_stop,
                "rule_holds": (
                    holds
                    if c["mined_nights"] >= MIN_MINED_NIGHTS and not old_formula
                    else None
                ),
                "stop_measured": stop_measured,
                "load_w": c["load_w"],
                "morning_soc": c["morning_soc"],
                "morning_after_mining": c["morning_after_mining"],
                "grid_kwh": round(c["grid_kwh"], 1),
                "grid_kwh_after_mining": round(c["grid_kwh_after_mining"], 1),
                "verdict": reserve_verdict(c),
                # The month's last night ran before ADR 033: its verdict
                # describes the old formula (card shows it in past tense).
                "before_formula_v2": old_formula,
            }
        )
    recent = []
    for n in nights[-CARD_NIGHTS:]:
        month = int(n["day"][5:7])
        recent.append(
            {
                "day": n["day"],
                "mined": n["mined"],
                "stop_block": n["stop_block"],
                "stop_soc": n["stop_soc"],
                "stop_target": table[month]["stop"],
                "before_formula_v2": n["day"] < RESERVE_FORMULA_V2_SINCE,
                "eve_soc": n["eve_soc"],
                "morning_soc": n["morning_soc"],
                "hours": round(n["hours"], 1),
                "load_kwh": round(n["load_kwh"], 1),
                "grid_kwh": round(n["grid_kwh"], 1),
            }
        )
    all_hours = sum(n["hours"] for n in nights)
    fc_days = forecast_days(conn, now)
    cards: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "generated_at": now.astimezone(timezone.utc).isoformat(),
        "settings": {**st, "source": settings_source},
        "nights": {
            "since": FORMULA_SINCE,
            "measured_load_w": (
                round(sum(n["load_kwh"] for n in nights) * 1000 / all_hours)
                if all_hours
                else None
            ),
            "months": month_rows,
            "recent": recent,
        },
        "forecast": {
            "lead_min": FORECAST_LEAD_BLOCKS * 10,
            "days": fc_days,
            "by_hour": forecast_by_hour(conn, fc_days) if fc_days else [],
            "months": forecast_months(conn),
            **forecast_summary(fc_days),
        },
        "efficiency": efficiency_trend(conn),
        "peak": peak_days(conn, now, table, st.get("pv_start_w", PV_START_DEFAULT_W)),
        "heizstab": heizstab_vs_battery(conn, now),
        "automation": automation_cards.build(conn, now),
    }
    # Built last: the notes quote numbers of the cards above.
    cards["thesis"] = thesis_notes.build(conn, cards)
    return cards


def read_settings(base_url: str, token: str) -> dict[str, float] | None:
    """Formula inputs from HA (GET only); None if HA is unreachable."""
    states: dict[str, dict[str, Any]] = {}
    for entity, _, _ in FORMULA_ENTITIES.values():
        req = Request(
            base_url.rstrip("/") + "/api/states/" + entity,
            headers={"Authorization": f"Bearer {token}"},
            method="GET",
        )
        try:
            with urlopen(req, timeout=15) as resp:  # noqa: S310 (fixed local URL)
                states[entity] = json.loads(resp.read().decode())
        except Exception:  # card falls back to the documented defaults
            log.warning("research_cards: %s not readable, using default", entity)
            if entity.endswith(("baseload_w", "capacity_kwh")):
                return None
    return settings_from_states(states)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    p = argparse.ArgumentParser(description="Research cards JSON (read-only)")
    p.add_argument("--db", required=True)
    p.add_argument("--out", required=True)
    # Stichtag fuer die Masterarbeit (14.11.2026): die Karten aendern sich jede
    # Nacht; eine Zahl in der Arbeit muss auf eine feste Fassung zeigen.
    p.add_argument(
        "--snapshot-dir",
        default=None,
        help="zusaetzlich research_cards_JJJJ-MM-TT.json hier ablegen (Stichtag)",
    )
    args = p.parse_args(argv)
    if os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.split(" #")[0].strip().strip("\"'"))
    host, token = os.getenv("UMBREL_HOST", ""), os.getenv("HA_TOKEN", "")
    settings = (
        read_settings(f"http://{host}:{os.getenv('HA_PORT', '8123')}", token)
        if host and token
        else None
    )
    now = datetime.now(timezone.utc)
    try:
        conn = open_readonly(args.db)
    except sqlite3.Error as exc:
        log.error("research_cards: database not readable: %s", exc)
        return 1
    try:
        if settings:
            cards = build_cards(conn, now, settings, "home_assistant")
        else:
            cards = build_cards(conn, now)
    finally:
        conn.close()
    write_atomic(cards, Path(args.out))
    if args.snapshot_dir:
        snap = Path(args.snapshot_dir) / f"research_cards_{now.date().isoformat()}.json"
        snap.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(cards, snap)
        log.info("research_cards: Stichtag abgelegt in %s", snap)
    log.info(
        "research_cards: %d nights, %d forecast days",
        len(cards["nights"]["recent"]),
        len(cards["forecast"]["days"]),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
