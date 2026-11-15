"""
Automation cards: where does the control logic lose yield or stability?

Read-only evaluation of the research DB for three cards in the tab Forschung,
written by research_cards.py into www/research_cards.json (key "automation"):

  surplus    grid export above 1 kW while the miners stood, with the state
             the automation was in (ha_diagnose_log)
  switching  start/stop changes per day against the quality goal (<= 2,
             docs/architecture/01_introduction_and_goals/012_quality_goals.md),
             hours in manual mode
  safety     switch errors (commanded != reported) and blocks with a chip
             temperature of 110 degC or more

Limits that the cards state themselves:
  - A block counts as complete when it was transferred; if HA was down the
    sync fills with the last value. Blocks with quality != 'ok' are left out.
  - Switching is counted on the mode the miner REPORTS
    (sensor.minerN_workmode_status). A miner that drops off the network and
    comes back in another mode shows up as a change.
  - The reason of an idle block is the diagnosis of miner 1 at that time.
    The diagnosis exists since 25.06.2026, earlier blocks have no reason.

First finding (14.11.2026, data 07. to 10.2026): in 138 of 159 idle blocks
the diagnosis read "SoC < Stop": the battery was below the stop threshold
and charging at its limit, the rest of the PV went to the grid.
"""

from __future__ import annotations

import bisect
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

BLOCK_HOURS = 1.0 / 6.0
# Reported modes in which the miner does not hash. "Idle" is the short state
# between Standby and a running mode.
OFF_MODES = frozenset({"Off", "Standby", "Idle"})
# Quality goal "Flapping-Rate": at most 2 start/stop changes per day.
SWITCH_TARGET_PER_DAY = 2
# Same limit as daily_kpi.blocks_temp_ge_110 (chip temperature TMax); the
# automation steps down at 112 degC (input_number.mvp_tmax_std_threshold_c).
TMAX_LIMIT_C = 110
RECENT_DAYS = 14
# Off between two hashing modes for less than this is a dropout (miner or
# plug briefly unreachable), not a stop and a start: after a stop (R1) the
# automation blocks a restart for 15 minutes (PV bypass), so it cannot
# produce such a pair itself.
DROPOUT_MAX = timedelta(minutes=15)
# Thresholds shown with their changes (settings_history).
THRESHOLD_LABELS = {
    "input_number.mvp_soc_stop_pct": "Stopp",
    "input_number.mvp_soc_eco_start_pct": "Eco ab",
    "input_number.mvp_soc_std_off_pct": "Standard endet",
    "input_number.mvp_soc_std_pct": "Standard ab",
    "input_number.mvp_soc_super_off_pct": "Super endet",
    "input_number.mvp_soc_super_pct": "Super ab",
}
THRESHOLD_CHANGES_SHOWN = 12
# settings_history has no row between 07.05. and 14.11.2026 (the recorder
# did not keep the thresholds). A "change" whose previous row is older than
# this is no change but the first reading after a gap: the old value is
# unknown (15.11.2026, the card showed "Eco ab 58 -> 100 angehoben", 58 being
# the May value).
THRESHOLD_GAP = timedelta(days=7)
TOP_DAYS = 5
REASON_MINER = "miner1"
UNKNOWN_REASON = "unbekannt"
# Diagnosis code (packages/mvp_diagnose.yaml) -> label on the card.
REASON_LABELS = {
    "auto_off": "Handbetrieb",
    "temp_lockout": "Temperatur-Sperre",
    "cooldown": "Wartezeit nach Schaltung",
    "pv_wait": "wartet auf Solarleistung",
    "room_hot": "Raum zu warm",
    "anomaly": "Start fällig, Miner noch aus",
    "unavailable": "Sensor fehlt",
}


def reason_label(code: str, summary: str | None) -> str:
    """Readable reason why the miners stood, from the diagnosis of that time.

    Under the verdict "ok" the automation saw no reason to start; which
    threshold held it back is in the summary text.
    """
    if code != "ok":
        return REASON_LABELS.get(code, code)
    text = summary or ""
    if "< Stop" in text:
        return "Akku unter Stopp-Schwelle"
    if "< Eco-Start" in text:
        return "Akku unter Eco-Start"
    return "kein Startgrund laut Regeln"


def _rows(conn: sqlite3.Connection, sql: str, args: tuple[Any, ...] = ()) -> list[Any]:
    """Query result, or [] if a table of the decision log does not exist yet."""
    try:
        return conn.execute(sql, args).fetchall()
    except sqlite3.OperationalError:
        return []


def _parse(ts: str) -> datetime:
    out = datetime.fromisoformat(ts)
    return out if out.tzinfo else out.replace(tzinfo=timezone.utc)


def surplus_idle(conn: sqlite3.Connection) -> dict[str, Any]:
    """Export above 1 kW with idle miners, per month, with the automation state."""
    blocks = _rows(
        conn,
        "SELECT v.block_id, v.grid_export_w FROM v_ungenutzter_ueberschuss v"
        " JOIN energy_states e ON e.block_id = v.block_id"
        " WHERE e.quality = 'ok' ORDER BY v.block_id",
    )
    diag = _rows(
        conn,
        "SELECT block_id, code, summary FROM ha_diagnose_log WHERE miner = ?"
        " ORDER BY timestamp",
        (REASON_MINER,),
    )
    diag_blocks = [str(d[0]) for d in diag]
    months: dict[str, dict[str, Any]] = {}
    days: dict[str, dict[str, float]] = defaultdict(lambda: {"blocks": 0, "kwh": 0.0})
    for block_id, export_w in blocks:
        block = str(block_id)
        kwh = float(export_w or 0.0) * BLOCK_HOURS / 1000.0
        # Diagnosis valid in this block: the last change at or before it.
        i = bisect.bisect_right(diag_blocks, block) - 1
        reason = reason_label(str(diag[i][1]), diag[i][2]) if i >= 0 else UNKNOWN_REASON
        m = months.setdefault(block[:7], {"blocks": 0, "kwh": 0.0, "reasons": {}})
        m["blocks"] += 1
        m["kwh"] += kwh
        m["reasons"][reason] = m["reasons"].get(reason, 0) + 1
        days[block[:10]]["blocks"] += 1
        days[block[:10]]["kwh"] += kwh
    month_rows = [
        {
            "month": month,
            "hours": round(m["blocks"] * BLOCK_HOURS, 1),
            "export_kwh": round(m["kwh"], 1),
            "reasons": {
                k: round(v * BLOCK_HOURS, 1)
                for k, v in sorted(m["reasons"].items(), key=lambda x: -x[1])
            },
        }
        for month, m in sorted(months.items())
    ]
    top = sorted(days.items(), key=lambda x: -x[1]["kwh"])[:TOP_DAYS]
    return {
        "threshold_w": 1000,
        "reason_miner": REASON_MINER,
        "hours": round(len(blocks) * BLOCK_HOURS, 1),
        "export_kwh": round(sum(m["kwh"] for m in months.values()), 1),
        "months": month_rows,
        "top_days": [
            {
                "day": day,
                "hours": round(v["blocks"] * BLOCK_HOURS, 1),
                "export_kwh": round(v["kwh"], 1),
            }
            for day, v in top
        ],
    }


def count_switches(
    events: list[tuple[str, str, str | None, str]],
) -> dict[tuple[str, str], dict[str, int]]:
    """(day, miner) -> start_stop, level changes and dropouts from mode events.

    ``events`` are (timestamp, miner, from_state, to_state) ordered by time.
    A change between two non-hashing modes (Standby/Off/Idle) is no switch.
    A stop followed by a start of the same miner within DROPOUT_MAX is one
    dropout instead of two start/stop changes (first version, 14.11.2026,
    counted every dropout as a stop and a start: an upper bound).
    """
    out: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"start_stop": 0, "level": 0, "dropout": 0}
    )
    by_miner: dict[str, list[tuple[str, str | None, str]]] = defaultdict(list)
    for ts, miner, from_state, to_state in events:
        by_miner[str(miner)].append((str(ts), from_state, to_state))
    for miner, evs in by_miner.items():
        restarts: set[int] = set()  # starts already booked as part of a dropout
        for i, (ts, from_state, to_state) in enumerate(evs):
            if from_state is None or i in restarts:
                continue
            was_off, is_off = from_state in OFF_MODES, to_state in OFF_MODES
            if was_off and is_off:
                continue
            key = (ts[:10], miner)
            if not was_off and is_off:
                # The next change that is not off -> off ends this pause.
                j = next(
                    (
                        k
                        for k in range(i + 1, len(evs))
                        if not (evs[k][1] in OFF_MODES and evs[k][2] in OFF_MODES)
                    ),
                    None,
                )
                if (
                    j is not None
                    and evs[j][1] in OFF_MODES
                    and evs[j][2] not in OFF_MODES
                    and _parse(evs[j][0]) - _parse(ts) < DROPOUT_MAX
                ):
                    restarts.add(j)
                    out[key]["dropout"] += 1
                    continue
            out[key]["start_stop" if was_off != is_off else "level"] += 1
    return dict(out)


def threshold_changes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Newest changes of the six switching thresholds, with old value and source.

    settings_history holds one row per change (history = exact time from the
    HA recorder, snapshot = value read at sync time). On 14.11.2026 this list
    would have shown the restart that reset 'Stopp' from 95 to 60 %.
    """
    labels = ", ".join("?" * len(THRESHOLD_LABELS))
    rows = _rows(
        conn,
        "SELECT timestamp, entity, value, source FROM settings_history"
        f" WHERE key = 'state' AND entity IN ({labels}) ORDER BY entity, timestamp",
        tuple(THRESHOLD_LABELS),
    )
    out: list[dict[str, Any]] = []
    prev: dict[str, tuple[str, str]] = {}
    for ts, entity, value, source in rows:
        before = prev.get(str(entity))
        prev[str(entity)] = (str(ts), str(value))
        if before is None or before[1] == str(value):
            continue
        gap = _parse(str(ts)) - _parse(before[0]) > THRESHOLD_GAP
        out.append(
            {
                "timestamp": str(ts),
                "label": THRESHOLD_LABELS[str(entity)],
                "old": None if gap else before[1],
                "new": str(value),
                "source": str(source),
            }
        )
    out.sort(key=lambda r: r["timestamp"], reverse=True)
    return out[:THRESHOLD_CHANGES_SHOWN]


def manual_hours(diag: list[tuple[str, str, str]], now: datetime) -> dict[str, float]:
    """month -> miner hours with the automation switched off (code auto_off).

    ``diag`` are (timestamp, miner, code) ordered by time; a state lasts until
    the next row of the same miner, the last one until ``now``. A span is
    booked to the month in which it starts.
    """
    by_miner: dict[str, list[tuple[datetime, str]]] = defaultdict(list)
    for ts, miner, code in diag:
        by_miner[str(miner)].append((_parse(str(ts)), str(code)))
    out: dict[str, float] = defaultdict(float)
    for rows in by_miner.values():
        for (start, code), nxt in zip(rows, rows[1:] + [(now, "")]):
            if code == "auto_off":
                out[start.strftime("%Y-%m")] += (nxt[0] - start).total_seconds() / 3600
    return {k: round(v, 1) for k, v in out.items()}


def switching(conn: sqlite3.Connection, now: datetime) -> dict[str, Any]:
    """Start/stop changes per day against the goal, per month and recent days."""
    events = _rows(
        conn,
        "SELECT timestamp, miner, from_state, to_state FROM ha_decision_log"
        " WHERE kind = 'mode' ORDER BY timestamp",
    )
    per = count_switches(events)
    # A day is judged by its busiest miner: the goal is per device.
    # Dropouts are summed over both miners: they are not part of the goal.
    days: dict[str, dict[str, int]] = {}
    for (day, _miner), c in per.items():
        d = days.setdefault(day, {"start_stop": 0, "level": 0, "dropout": 0})
        d["start_stop"] = max(d["start_stop"], c["start_stop"])
        d["level"] = max(d["level"], c["level"])
        d["dropout"] += c["dropout"]
    manual = manual_hours(
        _rows(
            conn,
            "SELECT timestamp, miner, code FROM ha_diagnose_log ORDER BY timestamp",
        ),
        now,
    )
    # A mining day is a day with any change of a running miner (a miner that
    # ran through midnight shows only level changes or a dropout).
    months: dict[str, list[dict[str, int]]] = defaultdict(list)
    for day, d in days.items():
        if d["start_stop"] or d["level"] or d["dropout"]:
            months[day[:7]].append(d)
    month_rows = []
    for month in sorted(set(months) | set(manual)):
        ds = months.get(month, [])
        month_rows.append(
            {
                "month": month,
                "mining_days": len(ds),
                "days_over": sum(
                    1 for d in ds if d["start_stop"] > SWITCH_TARGET_PER_DAY
                ),
                "max_start_stop": max((d["start_stop"] for d in ds), default=0),
                "mean_start_stop": (
                    round(sum(d["start_stop"] for d in ds) / len(ds), 1) if ds else None
                ),
                "mean_level": (
                    round(sum(d["level"] for d in ds) / len(ds), 1) if ds else None
                ),
                "manual_h": manual.get(month, 0.0),
                "dropouts": sum(d["dropout"] for d in ds),
            }
        )
    recent = [
        {"day": day, **days[day]}
        for day in sorted(
            d for d in days if days[d]["start_stop"] or days[d]["dropout"]
        )[-RECENT_DAYS:]
    ]
    return {
        "target": SWITCH_TARGET_PER_DAY,
        "since": str(events[0][0])[:10] if events else None,
        "dropout_max_min": int(DROPOUT_MAX.total_seconds() // 60),
        "months": month_rows,
        "recent": recent,
        "threshold_changes": threshold_changes(conn),
    }


def safety(conn: sqlite3.Connection) -> dict[str, Any]:
    """Switch errors and over-temperature blocks per month and miner."""
    err = _rows(
        conn,
        "SELECT substr(block_id, 1, 7), miner, COUNT(*) FROM v_schaltfehler"
        " GROUP BY 1, 2",
    )
    last_err = _rows(
        conn,
        "SELECT block_id, miner, workmode_set, workmode_status FROM v_schaltfehler"
        " ORDER BY block_id DESC LIMIT 1",
    )
    temp = _rows(
        conn,
        "SELECT substr(day, 1, 7), miner, COALESCE(SUM(blocks_ge_110), 0),"
        " MAX(tmax_max_c) FROM daily_miner_kpi GROUP BY 1, 2",
    )
    last_hot = _rows(
        conn,
        "SELECT day, miner, blocks_ge_110, tmax_max_c FROM daily_miner_kpi"
        " WHERE blocks_ge_110 > 0 ORDER BY day DESC LIMIT 1",
    )
    cells: dict[tuple[str, str], dict[str, Any]] = {}
    for month, miner, n in err:
        cells.setdefault((str(month), str(miner)), {})["errors"] = int(n)
    for month, miner, blocks, tmax in temp:
        c = cells.setdefault((str(month), str(miner)), {})
        c["hot_blocks"] = int(blocks)
        c["tmax_c"] = None if tmax is None else round(float(tmax))
    rows = [
        {
            "month": month,
            "miner": miner,
            "errors": c.get("errors", 0),
            "hot_blocks": c.get("hot_blocks", 0),
            "tmax_c": c.get("tmax_c"),
        }
        for (month, miner), c in sorted(cells.items())
    ]
    return {
        "tmax_limit_c": TMAX_LIMIT_C,
        "errors_total": sum(r["errors"] for r in rows),
        "hot_blocks_total": sum(r["hot_blocks"] for r in rows),
        "rows": rows,
        "last_error": (
            {
                "block": str(last_err[0][0]),
                "miner": str(last_err[0][1]),
                "set": last_err[0][2],
                "status": last_err[0][3],
            }
            if last_err
            else None
        ),
        "last_hot": (
            {
                "day": str(last_hot[0][0]),
                "miner": str(last_hot[0][1]),
                "blocks": int(last_hot[0][2]),
                "tmax_c": round(float(last_hot[0][3])),
            }
            if last_hot
            else None
        ),
    }


def build(conn: sqlite3.Connection, now: datetime) -> dict[str, Any]:
    return {
        "surplus": surplus_idle(conn),
        "switching": switching(conn, now),
        "safety": safety(conn),
    }
