#!/usr/bin/env python3
"""build_sim_day.py — turn a real recorded day into the lab study replay.

Reads one LOCAL day (Europe/Berlin, 00:00-24:00) from data/bitgrid.db
(energy_states, miner_states, device_states; written by ha_history_sync, keyed
in UTC) and emits two LAB-ONLY Home Assistant packages:

  src/ha/lab_only/lab_sim_day.yaml       profile, clock, weather, stepper, scripts
  src/ha/lab_only/lab_sim_entities.yaml  stand-ins for every dashboard entity the
                                          lab cannot provide (miner details,
                                          device plugs, heating rod, room sensors)

Output lives under src/ha/lab_only/ (gitignored, NOT src/ha/config/packages/), so
the prod deploy never ships it; deploy_ha_lab.py syncs lab_only/*.yaml into the
lab's packages/ dir.

Playback (15.10.2026, study run): a 1 s time_pattern computes the block from
the elapsed time, minute = start + (now - t0) / block_s * 10, block_s = 11.111 s
per 10-minute block (10 sim-minutes in 11.1 s, 54x; user decision 15.10.2026:
20-minute run). Computing from elapsed time
instead of chaining delays means the run cannot drift. The run is minute-precise:
it starts at 05:21 and stops at 23:21 (user decision 15.10.2026; 20:00 min at
11.111 s per block), no loop, so every participant sees the same stimulus.

Data provenance, recorded per row in [37] (0 = recorded, 1 = constructed):
  - Recorded: energy flows, SoC, per-miner stage/power/hashrate/temperatures/
    rejection, outdoor weather, sun elevation, PV forecast, heating rod, six
    device plugs, BTC price of the day (btc_price_daily).
  - Real external reference: block height at local midnight before/after the
    day and the difficulty valid that day (local mempool, fetched 15.10.2026);
    the height in between is linearly interpolated.
  - Prod typical profile (October, NOT the replayed month): device plugs that
    were not recorded yet, heating-rod water temperature, room sensors
    (src/ha/lab_only/prod_typprofil_20261015.json).
  - Static prod snapshot (15.10.2026): miner firmware/model/pool/share counters
    (src/ha/lab_only/prod_snapshot_20261015.json).
  - CONSTRUCTED (study requirement: every explanation branch must occur once,
    see CONSTRUCTED below): a sensor outage at the start and one over-temperature
    stop with lockout and restart. Fan speeds while mining are constructed too
    (never recorded anywhere).
  - CAPPED (consistency, 17.10.2026): the device plugs taken from the October
    typical profile are scaled down per block wherever plugs + heating rod would
    exceed GERAETE_SHARE of the recorded house load without the heating rod
    (July's house load is lower than plugs + heater in 114 of 144 blocks, the
    energy flow card showed "Geräte" above "Haus"). Recorded July plugs are only
    scaled where they alone exceed the limit. Factors per block in [43]/[44].
  - CORRECTED (17.10.2026): a heating-rod sample above the whole house load is
    impossible (the house load is the energy balance PV - export - battery -
    miners). On 2026-07-11 one block (14:20, rod 3402 W, house 423 W); the rod
    sample is set to 0 W and the row flagged in [37].

Display date (user decision 15.10.2026): the data of 2026-07-11 is SHOWN as
2026-07-21 (Tuesday). Every date of the replay moves by the same offset (+10
days): sim date, miner log, mining log, pool payout history, efficiency days,
and the BTC chart time axis (bitgrid_btc_kurs_chart.js reads
display_offset_days). All values stay the recorded ones of 2026-07-11. Study
protocol wording: "Datenbasis 11.07.2026, im Stimulus als 21.07.2026
dargestellt".

Row schema (one array per 10-min block, index = position):
  [0] pv_w  [1] house_w  [2] grid_import_w  [3] grid_export_w  [4] soc_pct
  [5] battery_w (+ charge)  [6] miner_total_w  [7] chip_max_c  [8] heartbeat_s
  [9] minute_of_day (local)  [10]/[11] miner1/2 TH/s  [12]/[13] miner1/2 stage
  (0 Standby, 1 Eco, 2 Standard, 3 Super)  [14..18] cumulative kWh since 00:00:
  pv, mining, grid_import, grid_export, house  [19] cloud_pct  [20] outdoor_c
  [21] humidity_pct  [22] sun_elevation_deg  [23] pv_forecast_kw  [24] heater_w
  [25]/[26] tmax_c  [27]/[28] itemp_c  [29]/[30] hbitemp_c  [31]/[32] hbotemp_c
  [33]/[34] miner power_w  [35]/[36] rejection_pct  [37] constructed (0/1)
  [38] sensor_dropout (0/1)  [39] block_height  [40] cumulative heater kWh
  [41] geraete_w (sum of the plugs prod's geraete_power_w adds up)
  [42] weather condition  [43]/[44] scale factor of the profile / recorded
  plugs (1.0 = unchanged, see CAPPED above)
  [42] weather condition (HA condition string)

Usage: python scripts/build_sim_day.py [--day 2026-07-11] [--db data/bitgrid.db]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import statistics
from datetime import date, datetime, time, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LAB_ONLY = REPO / "src" / "ha" / "lab_only"
J_PER_TH = 18.6  # Avalon Q efficiency (W per TH/s), fallback hashrate only
BLOCK = timedelta(minutes=10)
MODE_CODES = {"Off": 0, "Idle": 0, "Standby": 0, "Eco": 1, "Standard": 2, "Super": 3}
MODE_NAMES = ["Standby", "Eco", "Standard", "Super"]

# Real external reference per replayable day (local mempool, 15.10.2026):
# block height at local midnight before and after the day, difficulty valid then.
DAY_REF = {
    "2026-07-11": {"height_start": 957478, "height_end": 957616,
                   "difficulty": 133869853540305.4},
}

# Rule thresholds that were IN FORCE on the replayed day. The recorded stage
# switches of July 2026 sit exactly on 70/85/100 % (the fixed defaults before the
# seasonal formula of ADR 028 went live in September). Seeding today's formula
# would make the explanation text quote thresholds the replayed miner visibly
# does not follow.
THRESHOLDS = {
    "input_number.mvp_soc_stop_pct": 60,
    "input_number.mvp_soc_eco_start_pct": 70,
    "input_number.mvp_soc_std_pct": 85,
    # 83 on the day; the current +20 deadband (ADR 028, 27.08.2026) gives 80. Set
    # to 80 so the season table in Einstellungen, the threshold chart and the
    # texts agree. No switch of the day depends on it: the replay never steps
    # Standard -> Eco with the battery between 80 and 83 % (17.10.2026).
    "input_number.mvp_soc_std_off_pct": 80,
    "input_number.mvp_soc_super_pct": 100,
    "input_number.mvp_soc_super_off_pct": 95,
    "input_number.mvp_pv_start_w": 6000,
    "input_number.mvp_tmax_std_threshold_c": 112,
    "input_number.r3_max_chip_temp_c": 115,
    # Lab default 530 W (user decision 17.10.2026, evening). Known and accepted
    # trade-off: the season table in Einstellungen computes the house reserve
    # live from this baseload (reserve = 15 + W x July night 8.82 h / 12.5 kWh),
    # so July shows 52/62/72/77/87/92 % next to the 60/70/80/85/95/100 % in force
    # (the recorded switches of the day sit on those). 640 W would reproduce them
    # exactly. The day predates the season formula, no recorded baseload exists.
    "input_number.mvp_night_baseload_w": 530,
}
# Plugs + heating rod may take at most this share of the house load (CAPPED).
GERAETE_SHARE = 0.85
SOC_STOP, CHIP_THROTTLE, CHIP_STOP = 60, 112, 115

# Data day -> date shown in the lab (see docstring "Display date").
DISPLAY_DATE = {"2026-07-11": "2026-07-21"}


def shift_iso(text: str, days: int) -> str:
    """Shift the leading YYYY-MM-DD of a string by `days`."""
    if days == 0 or len(text) < 10:
        return text
    return (date.fromisoformat(text[:10]) + timedelta(days=days)).isoformat() + text[10:]


def apply_display_offset(meta: dict, display_day: str) -> None:
    """Move every date of the generated artefacts to the display date."""
    off = (date.fromisoformat(display_day) - date.fromisoformat(meta["day"])).days
    meta["display_day"], meta["display_offset_days"] = display_day, off
    if off == 0:
        return
    meta["pool_log"] = [(shift_iso(d, off), b, t) for d, b, t in meta["pool_log"]]
    meta["pool_json"]["payout_history"] = [
        [shift_iso(ts, off), desc, btc] for ts, desc, btc in meta["pool_json"]["payout_history"]]
    meta["eff_json"]["days"] = [{**e, "day": shift_iso(e["day"], off)} for e in meta["eff_json"]["days"]]
    meta["eff_json"]["generated_at"] = shift_iso(meta["eff_json"]["generated_at"], off)
    for k in ("mining_log_a", "mining_log_b"):
        meta[k] = "|".join(shift_iso(r, off) for r in meta[k].split("|") if r)
    head, *rows = meta["mining_log_csv"].rstrip("\n").split("\n")
    meta["mining_log_csv"] = "\n".join([head] + [shift_iso(r, off) for r in rows]) + "\n"


# Constructed episodes (only for the study day). Step = local minute // 10.
#  - 05:50-06:09 sensor outage after a restart -> "Verbindung wird aufgebaut".
#    17.10.2026: moved from 05:20-05:39 into the study window (it starts 05:51),
#    the branch never showed there.
#  - 13:00 over-temperature stop (chip >= 115 C) while both run Super; two hot
#    blocks, then restart via Eco and Standard, the recorded Super resumes at
#    14:20. 17.10.2026: restart moved from 13:40 to 13:20 so it follows the real
#    rules (scripts.yaml bg_stop: lockout 15 min from the stop, blocked while
#    >= 115 C; mvp_auto.yaml R7: PV bypass >= 6 kW 15 min after the switch-off,
#    PV is 8.4 kW). The old 13:20/13:30 stand-by blocks showed "Warte auf Sonne"
#    with "starts early from 6 kW" next to 8.4 kW, a false explanation. Known,
#    accepted limitation: Eco -> Standard -> Super after 30 min each, the real
#    up-cooldown is 1 h (the texts give no minutes for it).
DROPOUT_STEPS = {35, 36}
OVERHEAT = {  # step: (stage code, chip max C)
    78: (0, 116), 79: (0, 115), 80: (1, 84), 81: (1, 78),
    82: (1, 80), 83: (2, 86), 84: (2, 90), 85: (2, 92),
}
# Fan speed per stage, constructed (no fan data recorded anywhere; prod idles
# in October). Stand-by uses the real idle snapshot (0 rpm).
FAN_RPM = [0, 2400, 3600, 4800]
FAN_PCT = [0, 40, 60, 80]
MODE_POWER_OUTPUT = [0, 800, 1300, 1674]  # Avalon Q nominal, as in demo_flow

# Device plugs: DB name -> prod entity object id (src/data/ha_history_sync.py).
DB_DEVICES = {
    "buero": "shellyplugsg3_d885ac18c3b4",
    "kuehlschraenke": "shellyplugsg3_9070694abdf4",
    "tv": "shellyplugsg3_9070694c99d4",
    "waschmaschine": "shellyplugsg3_d885ac1e9adc",
    "lueftung": "shellyplusplugs_d4d4daf4eda4",
    "plug_d0cf13db3a00": "shellyplugsg3_d0cf13db3a00",
}
# Plugs prod's geraete_power_w sums up (packages/devices.yaml).
GERAETE = [
    "shellyplugsg3_9070694c577c", "shellyplugsg3_9070694b2854", "shellyplugsg3_9070694c99d4",
    "shellyplugsg3_9070694d44bc", "shellyplugsg3_90706947f288", "shellyplugsg3_d885ac18c3b4",
    "shellyplugsg3_9070694a1b6c", "shellyplugsg3_9070694abdf4", "shellyplugsg3_d885ac1e9adc",
    "shellyplugpmg3_9070695bb2a8", "shelly1pmg4_e4b06377adc0", "shellyplusplugs_d4d4daf4eda4",
    "shellyplugsg3_d0cf13db3a00", "shellyplugsg3_907069492f30",
]
# Plugs whose lab integration is disabled (house network, 15.10.2026): their
# registry entries keep the entity ids, so the lab stand-ins live under a lab_
# prefix and deploy_ha_lab.py rewrites the references.
LAB_PREFIXED = {"shellyplugsg3_dcb4d9c6b46c", "shellyplugsg3_d0cf13db3a00",
                "shellyplugsg3_dcb4d9c5567c", "shellyplugsg3_d0cf13d86254"}
MINER_PLUGS = {"shellyplugsg3_dcb4d9c5567c": 1, "shellyplugsg3_d0cf13d86254": 2}


def _last_sunday(year: int, month: int) -> date:
    d = date(year, month, 31)  # only used for March and October (31 days each)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def berlin_offset(utc: datetime) -> timedelta:
    """UTC offset of Europe/Berlin (the HA time zone) at a naive UTC instant.

    EU rule: CEST (+2) from 01:00 UTC on the last Sunday of March until 01:00 UTC
    on the last Sunday of October, CET (+1) otherwise. Hand-rolled because the
    Windows Python here has no tzdata, and the rule is fixed by EU directive.
    """
    start = datetime.combine(_last_sunday(utc.year, 3), time(1, 0))
    end = datetime.combine(_last_sunday(utc.year, 10), time(1, 0))
    return timedelta(hours=2 if start <= utc < end else 1)


def local_midnight_utc(day: date) -> datetime:
    """Naive UTC instant of local (Europe/Berlin) midnight."""
    naive = datetime.combine(day, time(0, 0))
    return naive - berlin_offset(naive - timedelta(hours=1))


def workmode_code(power_per_miner: float) -> int:
    """Map a single miner's wall power to a stage code (fallback only)."""
    if power_per_miner < 100:
        return 0
    if power_per_miner < 1000:
        return 1
    if power_per_miner < 1500:
        return 2
    return 3


def condition(cloud: float, sun_elev: float) -> str:
    """HA weather condition from recorded cloud cover and sun elevation."""
    if cloud >= 70:
        return "cloudy"
    if sun_elev <= -0.833:
        return "clear-night" if cloud < 40 else "partlycloudy"
    if cloud < 20:
        return "sunny"
    return "partlycloudy"


def history(con: sqlite3.Connection, d: date, payouts: dict[str, float], ndays: int) -> list[dict]:
    """Per-day mining summary for the ndays local days before d (newest first).

    Recorded: miner stages and wall power (bitgrid.db). Pool revenue per day:
    prod's F2Pool payout_history, where the entry dated D+1 settles day D.
    """
    fmt = "%Y-%m-%dT%H:%M:%S"
    out = []
    for k in range(1, ndays + 1):
        dd = d - timedelta(days=k)
        a, b = local_midnight_utc(dd), local_midnight_utc(dd + timedelta(days=1))
        span = (a.strftime(fmt), b.strftime(fmt))
        kwh = (con.execute("SELECT COALESCE(SUM(miner_power_w), 0) FROM energy_states"
                           " WHERE block_id >= ? AND block_id < ?", span).fetchone()[0] or 0) / 6000
        stage: dict[str, dict[str, int]] = {}
        for bid, m, st in con.execute(
                "SELECT block_id, miner, COALESCE(workmode_status, workmode_set) FROM miner_states"
                " WHERE block_id >= ? AND block_id < ?", span):
            stage.setdefault(bid, {})[m] = MODE_CODES.get(st or "", 0)
        run = sorted(bid for bid, ms in stage.items() if any(v > 0 for v in ms.values()))
        hours = [sum(1 for ms in stage.values() if ms.get("miner1", 0) == c) / 6 for c in (1, 2, 3)]

        def hm(bid: str, plus: int = 0) -> str:
            t = datetime.fromisoformat(bid)
            t = t + berlin_offset(t) + timedelta(minutes=plus)
            return t.strftime("%H:%M")

        btc = payouts.get((dd + timedelta(days=1)).isoformat(), 0.0)
        out.append({
            "day": dd.isoformat(),
            "start": hm(run[0]) if run else "--:--",
            "stop": hm(run[-1], 10) if run else "--:--",
            "tot_h": round(len(run) / 6, 2), "eco_h": round(hours[0], 1),
            "std_h": round(hours[1], 1), "sup_h": round(hours[2], 1),
            "kwh": round(kwh, 2), "btc": btc,
        })
    return out


def load_day(day: str, db_path: Path) -> tuple[list[list], dict]:
    if not db_path.exists():
        raise SystemExit(f"! database not found: {db_path}")
    d = date.fromisoformat(day)
    start = local_midnight_utc(d)
    end = local_midnight_utc(d + timedelta(days=1))
    fmt = "%Y-%m-%dT%H:%M:%S"
    span = (start.strftime(fmt), end.strftime(fmt))
    con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    try:
        energy = {r[0]: r[1:] for r in con.execute(
            "SELECT block_id, pv_power_w, house_load_w, grid_import_w, grid_export_w,"
            " battery_soc_pct, battery_power_w, miner_power_w, miner_heartbeat_age_sec,"
            " quality, cloud_coverage_pct, outdoor_temp_c, outdoor_humidity_pct,"
            " sun_elevation_deg, pv_forecast_kw, heizstab_power_w FROM energy_states"
            " WHERE block_id >= ? AND block_id < ?", span)}
        miners = {(r[0], r[1]): r[2:] for r in con.execute(
            "SELECT block_id, miner, COALESCE(workmode_status, workmode_set), power_w, ths,"
            " tmax_c, itemp_c, hbitemp_c, hbotemp_c, rejection_rate_pct FROM miner_states"
            " WHERE block_id >= ? AND block_id < ?", span)}
        devices = {(r[0], r[1]): r[2] for r in con.execute(
            "SELECT block_id, device, power_w FROM device_states"
            " WHERE block_id >= ? AND block_id < ?", span)}
        price = con.execute("SELECT price_eur FROM btc_price_daily WHERE day = ?", (day,)).fetchone()
        prev_price = con.execute("SELECT price_eur FROM btc_price_daily WHERE day = ?",
                                 ((d - timedelta(days=1)).isoformat(),)).fetchone()
        kpi = con.execute(
            "SELECT day, SUM(ths_mean) FROM daily_miner_kpi WHERE day >= ? AND day <= ?"
            " GROUP BY day ORDER BY day", ((d - timedelta(days=7)).isoformat(), day)).fetchall()
        snap = json.loads((LAB_ONLY / "prod_snapshot_20261015.json").read_text(encoding="utf-8"))
        ph = snap["sensor.pool_balance_btc"]["attributes"]["payout_history"]
        payouts = {e[0][:10]: float(e[2]) for e in ph if isinstance(e[2], (int, float))}
        first_day = date.fromisoformat(con.execute("SELECT MIN(block_id) FROM energy_states").fetchone()[0][:10])
        hist = history(con, d, payouts, max(30, (d - first_day).days))
        # Weather of the first 12 hours of the NEXT recorded day: the hourly
        # forecast runs past 23:00 (run ends 23:21) and must not run dry.
        nxt = local_midnight_utc(d + timedelta(days=1))
        tail = []
        for h in range(12):
            t = (nxt + timedelta(hours=h)).strftime(fmt)
            w = con.execute("SELECT cloud_coverage_pct, outdoor_temp_c, outdoor_humidity_pct, sun_elevation_deg"
                            " FROM energy_states WHERE block_id = ?", (t,)).fetchone()
            if w and None not in w:
                tail.append([round(w[1], 1), round(w[2]), condition(w[0], w[3])])
    finally:
        con.close()

    blocks: list[datetime] = []
    t = start
    while t < end:
        blocks.append(t)
        t += BLOCK
    bad = [b.strftime(fmt) for b in blocks if energy.get(b.strftime(fmt), (None,) * 15)[8] != "ok"]
    if bad:
        raise SystemExit(f"! {len(bad)} of {len(blocks)} blocks missing or not ok, e.g. {bad[:5]}")
    if len(blocks) != 144:
        raise SystemExit(f"! DST switch day ({len(blocks)} blocks) is not supported")
    if price is None:
        raise SystemExit(f"! no btc_price_daily row for {day}")
    ref = DAY_REF.get(day)
    if ref is None:
        raise SystemExit(f"! no DAY_REF (block height, difficulty) for {day}")

    # Per-miner stage medians of the day, used to fill the constructed blocks.
    per_stage: dict[int, dict[str, list[float]]] = {c: {"power": [], "ths": []} for c in range(4)}
    for (bid, m), mrow in miners.items():
        code = MODE_CODES.get(mrow[0] or "")
        if code is not None:
            per_stage[code]["power"].append(float(mrow[1] or 0))
            per_stage[code]["ths"].append(float(mrow[2] or 0))
    stage_power = {c: (statistics.median(v["power"]) if v["power"] else MODE_POWER_OUTPUT[c]) for c, v in per_stage.items()}
    stage_ths = {c: (statistics.median(v["ths"]) if v["ths"] else 0.0) for c, v in per_stage.items()}

    rows: list[list] = []
    for i, b in enumerate(blocks):
        bid = b.strftime(fmt)
        e = energy[bid]
        pv, load, grid_imp, grid_exp, soc = (float(x or 0) for x in e[:5])
        batt = float(e[5]) if e[5] is not None else pv + grid_imp - grid_exp - load - float(e[6] or 0)
        miner_pw = float(e[6] or 0)
        hb = float(e[7] if e[7] is not None else 5)
        cloud, out_t, hum, sun_el, pv_fc, heater = (float(x) if x is not None else 0.0 for x in e[9:15])
        local = b + berlin_offset(b)
        minute = local.hour * 60 + local.minute
        mm = []
        for m in ("miner1", "miner2"):
            r = miners.get((bid, m))
            if r is None:
                code = workmode_code(miner_pw / 2)
                mm.append([code, miner_pw / 2, stage_ths[code], 0, 0, 0, 0, 0])
                continue
            status, power, ths, tmax, itemp, hbi, hbo, rej = r
            code = MODE_CODES.get(status or "")
            if code is None:
                code = workmode_code(float(power or 0))
            mm.append([code, float(power or 0), float(ths or 0), float(tmax or 0),
                       float(itemp or 0), float(hbi or 0), float(hbo or 0), float(rej or 0)])
        constructed = 0
        if i in OVERHEAT:
            constructed = 1
            code, chip = OVERHEAT[i]
            old_pw = mm[0][1] + mm[1][1]
            for k, m in enumerate(mm):
                rec_tmax = m[3] or 1.0
                tmax = chip - 2 * k  # miner 2 runs slightly cooler
                ratio = tmax / rec_tmax
                m[0] = code
                m[1] = stage_power[code]
                m[2] = stage_ths[code]
                m[5] = round(m[5] * ratio, 1)
                m[6] = round(m[6] * ratio, 1)
                m[3] = tmax
            new_pw = mm[0][1] + mm[1][1]
            # Battery is full at 13:00, so the freed (or extra) miner power
            # moves to the grid export, house load and battery stay as recorded.
            grid_exp = max(0.0, grid_exp + old_pw - new_pw)
            miner_pw = new_pw
        dropout = 1 if i in DROPOUT_STEPS else 0
        if dropout:
            constructed = 1
        chip_max = max(mm[0][3], mm[1][3])
        height = round(ref["height_start"] + (ref["height_end"] - ref["height_start"]) * i / 144)
        clamp = lambda v, lo, hi: max(lo, min(hi, v))  # noqa: E731
        rows.append([
            round(clamp(pv, 0, 20000)), round(clamp(load, 0, 20000)),
            round(clamp(grid_imp, 0, 20000)), round(clamp(grid_exp, 0, 15000)),
            round(clamp(soc, 0, 100)), round(clamp(batt, -10000, 10000)),
            round(clamp(miner_pw, 0, 5000)), round(clamp(chip_max, 20, 120)),
            round(clamp(hb, 0, 600)), minute,
            round(mm[0][2], 1), round(mm[1][2], 1), mm[0][0], mm[1][0],
            0, 0, 0, 0, 0,  # cumulative kWh, filled below
            round(cloud), round(out_t, 1), round(hum), round(sun_el, 1), round(pv_fc, 2), round(heater),
            round(mm[0][3]), round(mm[1][3]), round(mm[0][4]), round(mm[1][4]),
            round(mm[0][5]), round(mm[1][5]), round(mm[0][6]), round(mm[1][6]),
            round(mm[0][1]), round(mm[1][1]), round(mm[0][7], 2), round(mm[1][7], 2),
            constructed, dropout, height, 0, 0, condition(cloud, sun_el),
        ])

    # CORRECTED (see docstring): before the plug cap and the cumulative kWh.
    for r in rows:
        if r[24] > r[1]:
            r[24] = 0
            r[37] = 1

    # Device plugs: recorded where available, else the prod typical profile.
    typ = json.loads((LAB_ONLY / "prod_typprofil_20261015.json").read_text(encoding="utf-8"))["slots"]
    by_obj = {obj: name for name, obj in DB_DEVICES.items()}
    dev_w: dict[str, list[float]] = {}
    dev_src: dict[str, str] = {}
    for obj in sorted(set(GERAETE) | {"shellyplugsg3_dcb4d9c6b46c"}):
        if obj in by_obj:
            series = [float(devices.get((b.strftime(fmt), by_obj[obj])) or 0) for b in blocks]
            dev_src[obj] = "recorded"
        else:
            slots = typ.get(f"sensor.{obj}_leistung") or [0] * 144
            series = [float(v or 0) for v in slots]
            has = any(v is not None for v in typ.get(f"sensor.{obj}_leistung") or [])
            dev_src[obj] = "prod_typprofil" if has else "none (0 W)"
        dev_w[obj] = [round(v, 1) for v in series]
    # CAPPED (see docstring): profile plugs first, recorded ones only if they
    # alone exceed the limit. Every downstream value (energy flow, device
    # types, rooms, floor plan, kWh) reads dev_w, so they all stay consistent.
    rec_objs = [o for o in GERAETE if dev_src[o] == "recorded"]
    prof_objs = [o for o in GERAETE if dev_src[o] != "recorded"]
    for i, r in enumerate(rows):
        limit = max(0.0, (r[1] - r[24]) * GERAETE_SHARE)
        rec = sum(dev_w[o][i] for o in rec_objs)
        prof = sum(dev_w[o][i] for o in prof_objs)
        scale_prof, scale_rec = 1.0, 1.0
        if rec + prof > limit:
            if rec <= limit:
                scale_prof = (limit - rec) / prof if prof > 0 else 1.0
            else:
                scale_prof, scale_rec = 0.0, limit / rec
        for objs, f in ((prof_objs, scale_prof), (rec_objs, scale_rec)):
            if f < 1.0:
                for o in objs:
                    dev_w[o][i] = round(dev_w[o][i] * f, 1)
        r.extend([round(scale_prof, 3), round(scale_rec, 3)])
    h = 10.0 / 60.0
    dev_kwh = {obj: [] for obj in dev_w}
    for obj, series in dev_w.items():
        acc = 0.0
        for v in series:
            acc += v / 1000 * h
            dev_kwh[obj].append(round(acc, 3))

    cum = [0.0] * 6
    for i, r in enumerate(rows):
        for k, idx in enumerate((0, 6, 2, 3, 1, 24)):
            cum[k] += r[idx] / 1000 * h
        r[14:19] = [round(c, 3) for c in cum[:5]]
        r[40] = round(cum[5], 3)
        r[41] = round(sum(dev_w[o][i] for o in GERAETE))

    # Pool earnings of the 7 days before: REAL daily revenue from prod's F2Pool
    # payout_history (15.10.2026 an FPPS estimate from the hashrate stood here,
    # it was 2.6x too high). TH/s per day: recorded daily_miner_kpi.
    diff = ref["difficulty"]
    ths_by_day = {k: float(t or 0) for k, t in kpi}
    pool_log = [(h["day"], round(h["btc"], 8), round(ths_by_day.get(h["day"], 0.0), 1)) for h in hist[:7]]
    # F2Pool account answer as it stood on the replayed day (lab-only dummy).
    # Never paid out, so balance = total income = settled revenue up to then.
    upto = [[ts, desc, btc] for ts, desc, btc in ph if ts[:10] <= day]
    settled = round(sum(e[2] for e in upto), 8)
    today_est = payouts.get((d + timedelta(days=1)).isoformat(), 0.0)
    pool_json = {
        "balance": settled, "paid": 0.0, "value": settled,
        "value_last_day": payouts.get(day, 0.0), "value_today": today_est,
        "hashrate": round(ths_by_day.get(day, 0.0) * 1e12),
        "hashes_last_day": round(ths_by_day.get((d - timedelta(days=1)).isoformat(), 0.0) * 1e12 * 86400),
        "worker_length_online": 2, "payout_history": upto,
    }
    # energy_to_sats.json of the 30 days before (sats from real payouts, kWh
    # recorded), same shape as src/data/energy_to_sats_export.py.
    eff = []
    for h in reversed(hist):
        e2s = h["btc"] * 1e8 / h["kwh"] if h["kwh"] >= 0.5 else 0.0
        eff.append({"day": h["day"], "energy_to_sats": round(e2s, 2)})
    for i, e in enumerate(eff):
        win = [x["energy_to_sats"] for x in eff[max(0, i - 6):i + 1] if x["energy_to_sats"] > 0]
        e["avg_7d"] = round(sum(win) / len(win), 2) if win else None
    eff_json = {
        "generated_at": f"{day}T00:05:00", "target_sats_per_kwh": 125.0,
        "latest_avg_7d": next((e["avg_7d"] for e in reversed(eff) if e["avg_7d"] is not None), None),
        "days": eff,
    }
    mlog_all = [f"{h['day']},{h['start']},{h['stop']},{h['tot_h']},{h['eco_h']},{h['std_h']},{h['sup_h']},{h['kwh']},"
                for h in hist]
    mlog = [m.rstrip(",") for m in mlog_all[:10]]
    meta = {
        "day": day, "btc_eur": int(price[0]), "difficulty_t": round(diff / 1e12, 2),
        # Day-start reference of the price change chip: daily price of the day
        # before (btc_price_daily), the closest recorded value to 00:00.
        "btc_eur_prev": int(prev_price[0]) if prev_price else int(price[0]),
        "dev_w": dev_w, "dev_kwh": dev_kwh, "dev_src": dev_src,
        "pool_log": pool_log, "pool_json": pool_json, "eff_json": eff_json, "forecast_tail": tail,
        "mining_log_a": "|".join(mlog[:5]), "mining_log_b": "|".join(mlog[5:10]),
        # Full mining log up to the day before (lab host /config/mining_log.csv,
        # read by sensor.mining_log_history), oldest first like prod's file.
        "mining_log_csv": "date,start,stop,total_h,eco_h,std_h,speed_h,kwh,diff\n" + "\n".join(reversed(mlog_all)) + "\n",
        "utc_offset": f"+{int(berlin_offset(start + timedelta(hours=12)).total_seconds() // 3600):02d}:00",
    }
    return rows, meta


def texts(rows: list[list]) -> dict[str, list[str]]:
    """Per-step rule code and reasoning per miner, same vocabulary as prod's
    mvp_auto (input_text.mvp_minerN_rule / _debug), thresholds of the day."""
    out = {"rule1": [], "rule2": [], "dbg1": [], "dbg2": []}
    for r in rows:
        soc = r[4]
        for n, (mode_i, tmax_i) in ((1, (12, 25)), (2, (13, 26))):
            name = MODE_NAMES[r[mode_i]]
            chip = r[tmax_i]
            if r[37] and chip >= CHIP_STOP:
                rule, dbg = "R3 Temp-Stopp", f"{name} — R3 Sicherheitsstopp: Chip {chip} °C ≥ {CHIP_STOP} °C"
            elif r[mode_i] == 0 and soc < SOC_STOP:
                rule, dbg = "R1 Stopp", f"{name} — R1 Sicherheitsstopp: SoC {soc}% < Stop {SOC_STOP}%"
            elif r[mode_i] == 3 and chip >= CHIP_THROTTLE:
                rule, dbg = "R2 Temp-Sperre", f"{name} — R2 Drosselung: Chip {chip} °C ≥ {CHIP_THROTTLE} °C"
            else:
                rule, dbg = "Regulär", f"{name} — regulär (SoC {soc}%)"
            out[f"rule{n}"].append(rule)
            out[f"dbg{n}"].append(dbg)
    return out


ROW = ("{% set s = state_attr('sensor.lab_sim_profile','steps') %}"
       "{% set i = states('input_number.sim_step')|int(0) %}"
       "{% set r = s[i] if s and i < s|length else none %}")
DEV = ("{% set i = states('input_number.sim_step')|int(0) %}"
       "{% set d = state_attr('sensor.lab_sim_devices', '{attr}') %}")


def room_day_series(rows: list[list], dev_w: dict) -> dict:
    """10-minute series of every prod room sum (sensor.raum_*_power_w).

    The room sums in packages/devices.yaml are plain sums of plug sensors; each
    input is replayed the same way as its lab stand-in: miner plugs = recorded
    miner power (row 33/34), heating rod solar = row 24, heating rod grid = 0,
    other plugs = dev_w. An input without a stand-in (FRITZ light, disabled in
    the lab) counts 0, exactly like the lab's room sensor sees it.
    """
    text = (REPO / "src" / "ha" / "config" / "packages" / "devices.yaml").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'- name: "(raum_[a-z0-9_]+_power_w)"(.*?)(?=\n\s*- name: |\Z)', text, re.S):
        series = [0.0] * len(rows)
        for sid in re.findall(r"states\('sensor\.([a-z0-9_]+)'\)", m.group(2)):
            obj = sid[: -len("_leistung")] if sid.endswith("_leistung") else None
            if sid == "ac_elwa_2_power1_solar":
                vals = [r[24] for r in rows]
            elif obj in MINER_PLUGS:
                vals = [r[33 if MINER_PLUGS[obj] == 1 else 34] for r in rows]
            elif obj in dev_w:
                vals = dev_w[obj]
            else:
                continue
            series = [a + float(b or 0) for a, b in zip(series, vals)]
        out[m.group(1)] = [round(v, 1) for v in series]
    return out


def build_day_yaml(day: str, rows: list[list], meta: dict, txt: dict) -> str:
    n = len(rows)
    steps = json.dumps(rows, separators=(",", ":"), ensure_ascii=False)
    tx = json.dumps(txt, separators=(",", ":"), ensure_ascii=False)
    seeds = "\n".join(
        f"        - service: input_number.set_value\n"
        f"          target: {{ entity_id: {eid} }}\n"
        f"          data: {{ value: {val} }}"
        for eid, val in THRESHOLDS.items())
    btc_log = "|".join(f"{d},{b}" for d, b, _ in meta["pool_log"])
    ths_log = "|".join(f"{d},{t}" for d, _, t in meta["pool_log"])
    off = meta["utc_offset"]
    constructed = [i for i, r in enumerate(rows) if r[37]]
    return f"""\
# lab_sim_day.yaml — LAB-ONLY study replay of the real day {meta['day']}, shown as {day}.
# GENERATED by scripts/build_sim_day.py — do not hand-edit; regenerate instead.
# Provenance and the constructed blocks are documented in the generator docstring.
#
# NOT part of the prod product: lives in src/ha/lab_only/ and is shipped only by
# deploy_ha_lab.py into the lab's packages/ dir. deploy_ha.sh (prod) never sees it.
#
# Two modes (input_select.lab_demo_modus, user decisions 17.10.2026):
#   Studie         05:51 -> 23:21, stops at the end, real lab miners follow.
#                  05:51 so the miners start (10:20) after 4:59 real minutes.
#   Dauerschleife  00:00 -> 24:00 -> 00:00 seamless, real lab miners off.
# Both at 11.111 s per 10-minute block (Studie 19:27 min, a full day 26:40 min).
# Controls (the clock stays frozen until Play):
#   script.lab_demo_studie_vorbereiten    mode Studie + reset (frozen at 05:51)
#   script.lab_demo_dauerschleife_starten mode Dauerschleife + reset + play
#   script.lab_demo_reset  seeds the day, stands FROZEN at the start of the mode
#   script.lab_demo_play   runs on from the frozen minute (at the end: reset first)
#   script.lab_demo_pause  freezes the current minute
#   script.lab_demo_exit   switches the dashboard back to the real (offline) sensors
# The 1 s stepper derives the block from the elapsed time since lab_demo_t0, so a
# slow tick never accumulates drift; Play shifts t0 so the run continues where
# it stood. The lab dashboard "Sim-Steuerung" (lab_only/lovelace) has the buttons.

lab_sim_day:

  input_boolean:
    lab_demo_running:
      name: Lab Demo läuft
      icon: mdi:play-box-multiple
    # On: at the end of the window the day starts over by itself (reset +
    # play). Set by lab_demo_reset from the mode (Dauerschleife on, Studie off).
    lab_demo_loop:
      name: "Lab Demo: Tag wiederholen"
      icon: mdi:repeat
    sim_sensor_dropout:
      name: "Sim: Sensor-Ausfall"
      icon: mdi:lan-disconnect

  input_select:
    lab_demo_modus:
      name: "Lab Demo Modus"
      options: [Studie, Dauerschleife]
      icon: mdi:movie-open-cog

  # Target of "Springen zu" on the lab dashboard (script.lab_demo_seek).
  input_datetime:
    lab_sim_seek:
      name: "Springen zu (Sim-Zeit)"
      has_date: false
      has_time: true

  input_number:
    sim_step:
      name: sim_step
      min: 0
      max: {n - 1}
      step: 1
      mode: box
    lab_demo_t0:
      name: "Lab Demo Startzeit (Unix)"
      min: 0
      max: 4102444800
      step: 1
      mode: box
    lab_demo_block_s:
      name: "Lab Demo Sekunden je 10-min-Block"
      min: 1
      max: 60
      step: 0.001
      mode: box
    # Run window in minutes of the day (Studie 351-1401 = 05:51-23:21,
    # Dauerschleife 0-1440 = 00:00-24:00).
    lab_demo_start_minute:
      name: "Lab Demo Startminute"
      min: 0
      max: 1440
      step: 1
      mode: box
    lab_demo_end_minute:
      name: "Lab Demo Endminute"
      min: 0
      max: 1440
      step: 1
      mode: box
    # Sim minute shown while the run is NOT running (start / stop / end), so
    # the clock freezes on the exact minute instead of the 10-minute block.
    lab_sim_minute:
      name: "Lab Sim Minute (angehalten)"
      min: 0
      max: 1440
      step: 1
      mode: box
    lab_sim_block_height:
      name: lab_sim_block_height
      min: 0
      max: 5000000
      step: 1
      mode: box
    btc_eur_price_sim:
      name: btc_eur_price_sim
      min: 0
      max: 500000
      step: 1
      unit_of_measurement: "€"
      mode: box
    pv_energy_daily_sim:
      name: pv_energy_daily_sim
      min: 0
      max: 200
      step: 0.001
      unit_of_measurement: kWh
      mode: box
    mining_energy_daily_sim:
      name: mining_energy_daily_sim
      min: 0
      max: 200
      step: 0.001
      unit_of_measurement: kWh
      mode: box
    grid_import_daily_sim:
      name: grid_import_daily_sim
      min: 0
      max: 200
      step: 0.001
      unit_of_measurement: kWh
      mode: box
    grid_export_daily_sim:
      name: grid_export_daily_sim
      min: 0
      max: 200
      step: 0.001
      unit_of_measurement: kWh
      mode: box
    house_energy_daily_sim:
      name: house_energy_daily_sim
      min: 0
      max: 200
      step: 0.001
      unit_of_measurement: kWh
      mode: box
    geraete_power_sim_w:
      name: geraete_power_sim_w
      min: 0
      max: 20000
      step: 1
      unit_of_measurement: W
      mode: box

  template:
    - sensor:
        # Static replay profile: {n} blocks of the real day {meta['day']}; state = the
        # sim date (read by the clock patch in bitgrid_card_shape.js, the
        # hamster card and the miner log). Constructed blocks: {constructed}.
        - name: lab_sim_profile
          unique_id: lab_sim_profile
          state: "{day}"
          attributes:
            steps: >-
              {{{{ {steps} }}}}
            utc_offset: "{off}"
            # State = DISPLAY date; the recorded data is of data_day.
            data_day: "{meta['day']}"
            display_offset_days: {meta['display_offset_days']}
            constructed_steps: >-
              {{{{ {json.dumps(constructed)} }}}}
            # Recorded weather of the next day, hours 00-11: [temp, humidity, condition].
            forecast_tail: >-
              {{{{ {json.dumps(meta['forecast_tail'], ensure_ascii=False)} }}}}
        - name: lab_sim_devices
          unique_id: lab_sim_devices
          state: "{day}"
          attributes:
            dev_w: >-
              {{{{ {json.dumps(meta['dev_w'], separators=(',', ':'))} }}}}
            dev_kwh: >-
              {{{{ {json.dumps(meta['dev_kwh'], separators=(',', ':'))} }}}}
            # Room sums per 10-min block (Energie-Info history in the replay,
            # window.bgaiSimSeries in www/bitgrid_card_shape.js).
            room_w: >-
              {{{{ {json.dumps(room_day_series(rows, meta['dev_w']), separators=(',', ':'))} }}}}
        - name: lab_sim_texts
          unique_id: lab_sim_texts
          state: "{day}"
          attributes:
            texts: >-
              {{{{ {tx} }}}}
        # Simulated wall-clock time (HH:MM) of the current block.
        - name: lab_sim_clock
          unique_id: lab_sim_clock
          state: >-
            {ROW}
            {{% if r %}}{{{{ '%02d:%02d'|format((r[9] // 60)|int, (r[9] % 60)|int) }}}}{{% else %}}--:--{{% endif %}}
        # Season status of the replayed day: before ADR 028 every stage was
        # allowed, which is what the explanation card's "Voll" branch encodes.
        - name: lab_sim_saison_status
          unique_id: lab_sim_saison_status
          state: "Voll (Eco/Standard/Super)"
    - binary_sensor:
        # Day/night for the background tiles from the RECORDED sun elevation
        # while the replay runs (deploy_ha_lab.py rewrites the dashboard's
        # sun.sun check to this entity), otherwise the real sun.
        - name: lab_sim_sun_up
          unique_id: lab_sim_sun_up
          state: >-
            {ROW}
            {{% if is_state('input_boolean.simulation_mode', 'on') and r %}}{{{{ r[22] > 0 }}}}
            {{% else %}}{{{{ is_state('sun.sun', 'above_horizon') }}}}{{% endif %}}
    - weather:
        # Recorded weather of the replayed day (cloud cover, outdoor temperature,
        # humidity, sun elevation); the hourly forecast is the recorded weather
        # of the following hours (a "perfect" forecast, disclosed as such).
        - name: "Lab Sim Weather"
          unique_id: lab_sim_weather
          condition: >-
            {ROW}
            {{{{ r[42] if r else 'sunny' }}}}
          temperature: >-
            {ROW}
            {{{{ r[20] if r else 20 }}}}
          humidity: >-
            {ROW}
            {{{{ r[21] if r else 50 }}}}
          temperature_unit: "°C"
          forecast_hourly: >-
            {ROW}
            {{% set ns = namespace(out=[]) %}}
            {{% set tail = state_attr('sensor.lab_sim_profile', 'forecast_tail') or [] %}}
            {{# Dauerschleife: after midnight the SAME day plays again, so its
               early hours are the honest forecast; Studie: the next day. #}}
            {{% set same_day = is_state('input_select.lab_demo_modus', 'Dauerschleife') %}}
            {{% if r %}}
              {{% for k in range(1, 9) %}}
                {{% set h = i // 6 + k %}}
                {{# Always today's REAL date, also past midnight: the forecast
                   card puts a weekday marker in front of entries of another
                   day, and that marker would name the real weekday (e.g. "Fr"),
                   not the replayed one ("So"). The hour labels alone show the
                   day change. #}}
                {{% if h < 24 and h * 6 < s|length %}}
                  {{% set ns.out = ns.out + [{{'datetime': now().strftime('%Y-%m-%d') ~ 'T%02d:00:00'|format(h) ~ now().isoformat()[-6:],
                       'condition': s[h * 6][42], 'temperature': s[h * 6][20], 'humidity': s[h * 6][21]}}] %}}
                {{% elif h >= 24 and same_day and (h - 24) * 6 < s|length %}}
                  {{% set ns.out = ns.out + [{{'datetime': now().strftime('%Y-%m-%d') ~ 'T%02d:00:00'|format(h - 24) ~ now().isoformat()[-6:],
                       'condition': s[(h - 24) * 6][42], 'temperature': s[(h - 24) * 6][20], 'humidity': s[(h - 24) * 6][21]}}] %}}
                {{% elif h >= 24 and h - 24 < tail|length %}}
                  {{% set ns.out = ns.out + [{{'datetime': now().strftime('%Y-%m-%d') ~ 'T%02d:00:00'|format(h - 24) ~ now().isoformat()[-6:],
                       'condition': tail[h - 24][2], 'temperature': tail[h - 24][0], 'humidity': tail[h - 24][1]}}] %}}
                {{% endif %}}
              {{% endfor %}}
            {{% endif %}}
            {{{{ ns.out }}}}

  script:
    # Writes block i into every sim helper. Called by the stepper and by start.
    lab_sim_apply_row:
      alias: "Lab Sim: Block anwenden"
      mode: queued
      max: 3
      fields:
        i:
          description: Block index 0..{n - 1}
      sequence:
        - variables:
            s: "{{{{ state_attr('sensor.lab_sim_profile','steps') }}}}"
            tx: "{{{{ state_attr('sensor.lab_sim_texts','texts') }}}}"
            row: "{{{{ s[i|int] if s and (i|int) < s|length else none }}}}"
        - condition: template
          value_template: "{{{{ row is not none }}}}"
        - service: "input_boolean.turn_{{{{ 'on' if row[38] == 1 else 'off' }}}}"
          target: {{ entity_id: input_boolean.sim_sensor_dropout }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.pv_power_w }}
          data: {{ value: "{{{{ row[0] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.house_load_w }}
          data: {{ value: "{{{{ row[1] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.grid_import_w }}
          data: {{ value: "{{{{ row[2] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.grid_export_w }}
          data: {{ value: "{{{{ row[3] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.battery_soc_pct }}
          data: {{ value: "{{{{ row[4] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.battery_power_w }}
          data: {{ value: "{{{{ row[5] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.miner_power_w }}
          data: {{ value: "{{{{ row[6] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.miner_temp_c }}
          data: {{ value: "{{{{ row[7] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.miner_heartbeat_age_sec }}
          data: {{ value: "{{{{ row[8] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.pv_energy_daily_sim }}
          data: {{ value: "{{{{ row[14] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.mining_energy_daily_sim }}
          data: {{ value: "{{{{ row[15] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.grid_import_daily_sim }}
          data: {{ value: "{{{{ row[16] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.grid_export_daily_sim }}
          data: {{ value: "{{{{ row[17] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.house_energy_daily_sim }}
          data: {{ value: "{{{{ row[18] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.geraete_power_sim_w }}
          data: {{ value: "{{{{ row[41] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_sim_block_height }}
          data: {{ value: "{{{{ row[39] }}}}" }}
        # Recorded stage, but ONLY while Automatik is on; a manually clicked
        # stage (which turns Automatik off) is left untouched.
        - if:
            - condition: state
              entity_id: input_boolean.miner1_auto_load_management
              state: "on"
          then:
            - service: input_select.select_option
              target: {{ entity_id: input_select.miner1_mode }}
              data: {{ option: "{{{{ ['Standby','Eco','Standard','Super'][row[12]|int] }}}}" }}
        - if:
            - condition: state
              entity_id: input_boolean.miner2_auto_load_management
              state: "on"
          then:
            - service: input_select.select_option
              target: {{ entity_id: input_select.miner2_mode }}
              data: {{ option: "{{{{ ['Standby','Eco','Standard','Super'][row[13]|int] }}}}" }}
        # Reasoning first, rule code second (prod order: the miner log reads the
        # reasoning when the rule code changes).
        - service: input_text.set_value
          target: {{ entity_id: input_text.mvp_miner1_debug }}
          data: {{ value: "{{{{ tx.dbg1[i|int] }}}}" }}
        - service: input_text.set_value
          target: {{ entity_id: input_text.mvp_miner2_debug }}
          data: {{ value: "{{{{ tx.dbg2[i|int] }}}}" }}
        - service: input_text.set_value
          target: {{ entity_id: input_text.mvp_miner1_rule }}
          data: {{ value: "{{{{ tx.rule1[i|int] }}}}" }}
        - service: input_text.set_value
          target: {{ entity_id: input_text.mvp_miner2_rule }}
          data: {{ value: "{{{{ tx.rule2[i|int] }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.sim_step }}
          data: {{ value: "{{{{ i|int }}}}" }}
        # REST sensors re-read their value template (sim price / block height
        # in the lab, see deploy_ha_lab.py LAB_REWRITES) only when polled.
        - service: homeassistant.update_entity
          target: {{ entity_id: [sensor.bitcoin_block_height, sensor.btc_eur_price] }}
          continue_on_error: true

    # Values of the replayed day. Called by lab_demo_reset AND after every HA
    # restart (lab_demo_restore_on_start): the input_numbers have `initial:`
    # values in the shared packages and fall back to them on each start, so a
    # restart during the Dauerschleife showed 83 % / 535 W again (live 17.10.2026).
    lab_demo_seed_values:
      alias: "Lab Demo: Tageswerte setzen"
      mode: queued
      sequence:
        - service: input_number.set_value
          target: {{ entity_id: input_number.block_reward_btc }}
          data: {{ value: 3.125 }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.miner_efficiency_j_th }}
          data: {{ value: 18.6 }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.grid_price_ct_kwh }}
          data: {{ value: 36.24 }}   # user default 15.10.2026
        - service: input_number.set_value
          target: {{ entity_id: input_number.feed_in_tariff_ct_kwh }}
          data: {{ value: 7.9 }}     # user default 15.10.2026
        # Thresholds in force on {day} (see generator THRESHOLDS).
{seeds}
        - service: input_number.set_value
          target: {{ entity_id: input_number.btc_eur_price_sim }}
          data: {{ value: {meta['btc_eur']} }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.btc_eur_day_start }}
          data: {{ value: {meta['btc_eur_prev']} }}
        - service: input_text.set_value
          target: {{ entity_id: input_text.pool_btc_daily_log }}
          data: {{ value: "{btc_log}" }}
        - service: input_text.set_value
          target: {{ entity_id: input_text.pool_ths_daily_log }}
          data: {{ value: "{ths_log}" }}
        # Mining log of the week before (recorded stages/kWh, real payouts).
        - service: input_text.set_value
          target: {{ entity_id: input_text.mining_daily_log }}
          data: {{ value: "{meta['mining_log_a']}" }}
        - service: input_text.set_value
          target: {{ entity_id: input_text.mining_daily_log_b }}
          data: {{ value: "{meta['mining_log_b']}" }}
        # Hardware cost for the payoff card (user default 15.10.2026, 400 EUR).
        - service: input_number.set_value
          target: {{ entity_id: input_number.hardware_cost_eur }}
          data: {{ value: 400 }}

    lab_demo_reset:
      alias: "Lab Demo zuruecksetzen (Start des Modus, angehalten)"
      icon: mdi:restart
      sequence:
        - variables:
            studie: "{{{{ not is_state('input_select.lab_demo_modus', 'Dauerschleife') }}}}"
            start_min: "{{{{ 351 if studie else 0 }}}}"     # 05:51 | 00:00
            end_min: "{{{{ 1401 if studie else 1440 }}}}"   # 23:21 | 24:00
        - service: input_boolean.turn_off
          target: {{ entity_id: input_boolean.lab_demo_running }}
        # Every prod automation is paused for the run: they react to the replayed
        # values in REAL time (cooldowns, night lock, season formula) and would
        # fight the replay over the stage selects and thresholds. Lab automations
        # (id lab_*) keep running. Not re-enabled on stop (lab is a sim box);
        # script.lab_prod_automations_on restores them by hand.
        - service: automation.turn_off
          target:
            entity_id: >-
              {{{{ states.automation | rejectattr('attributes.id', 'undefined')
                 | rejectattr('attributes.id', 'search', '^lab_')
                 | map(attribute='entity_id') | list }}}}
          data: {{ stop_actions: true }}
        # Values of the replayed day (thresholds, prices, logs): own script,
        # shared with lab_demo_restore_on_start.
        - service: script.lab_demo_seed_values
        - service: input_boolean.turn_on
          target:
            entity_id: [input_boolean.miner1_auto_load_management, input_boolean.miner2_auto_load_management]
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_demo_block_s }}
          data: {{ value: 11.111 }}   # 1 sim minute = 1.11 s
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_demo_start_minute }}
          data: {{ value: "{{{{ start_min }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_demo_end_minute }}
          data: {{ value: "{{{{ end_min }}}}" }}
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_sim_minute }}
          data: {{ value: "{{{{ start_min }}}}" }}
        - service: "input_boolean.turn_{{{{ 'off' if studie else 'on' }}}}"
          target: {{ entity_id: input_boolean.lab_demo_loop }}
        # Real lab miners follow in the study, not in the background loop
        # (relay switching cycles, lab_miner_sim.yaml).
        - service: "input_boolean.turn_{{{{ 'on' if studie else 'off' }}}}"
          target: {{ entity_id: input_boolean.lab_miner_physical }}
        # Mining log card opens on the current (sim) week.
        - service: input_number.set_value
          target: {{ entity_id: input_number.mining_log_offset }}
          data: {{ value: 0 }}
        - service: input_select.select_option
          target: {{ entity_id: input_select.mining_log_periode }}
          data: {{ option: Woche }}
        - service: input_boolean.turn_on
          target: {{ entity_id: input_boolean.simulation_mode }}
        # Empty miner logs for a clean run (event handled in mvp_auto.yaml).
        - event: bgai_miner_log_reset
        - service: script.lab_sim_apply_row
          data: {{ i: "{{{{ start_min // 10 }}}}" }}
        # t0 > 0 marks "a replay is loaded" (lab_demo_restore_on_start); Play
        # sets the real value. The run stays frozen until Play.
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_demo_t0 }}
          data: {{ value: "{{{{ as_timestamp(now()) | int }}}}" }}
        # One poll of the pool hashrate REST sensor (sim branch, see
        # deploy_ha_lab.py), otherwise it waits up to 300 s for its own poll.
        - service: homeassistant.update_entity
          target: {{ entity_id: [sensor.pool_hashrate_h1_ths, sensor.pool_balance_btc] }}
          continue_on_error: true

    # Jump to a sim time and stand FROZEN there (Play runs on from it). The time
    # is clamped into the window of the current mode.
    lab_demo_seek:
      alias: "Springen zu (angehalten)"
      icon: mdi:debug-step-over
      sequence:
        - service: script.lab_demo_pause
        - variables:
            t: "{{{{ states('input_datetime.lab_sim_seek') }}}}"
            s0: "{{{{ states('input_number.lab_demo_start_minute') | int(351) }}}}"
            e0: "{{{{ states('input_number.lab_demo_end_minute') | int(1401) }}}}"
            m: "{{{{ [[(t[0:2] | int(0)) * 60 + (t[3:5] | int(0)), s0] | max, e0 - 1] | min }}}}"
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_sim_minute }}
          data: {{ value: "{{{{ m }}}}" }}
        - service: script.lab_sim_apply_row
          data: {{ i: "{{{{ [m // 10, {n - 1}] | min }}}}" }}

    lab_demo_studie_vorbereiten:
      alias: "Studie vorbereiten (05:51, angehalten)"
      icon: mdi:account-school
      sequence:
        - service: input_select.select_option
          target: {{ entity_id: input_select.lab_demo_modus }}
          data: {{ option: Studie }}
        - service: script.lab_demo_reset

    lab_demo_dauerschleife_starten:
      alias: "Dauerschleife starten (ganzer Tag)"
      icon: mdi:repeat
      sequence:
        - service: input_select.select_option
          target: {{ entity_id: input_select.lab_demo_modus }}
          data: {{ option: Dauerschleife }}
        - service: script.lab_demo_reset
        - service: script.lab_demo_play

    lab_demo_play:
      alias: "Lab Demo abspielen"
      icon: mdi:play
      mode: single
      sequence:
        - condition: state
          entity_id: input_boolean.lab_demo_running
          state: "off"
        # At the end of the window (or nothing loaded yet) Play starts over.
        - if: >-
            {{{{ states('input_number.lab_demo_t0') | float(0) <= 0
               or states('input_number.lab_sim_minute') | int(0)
                  >= states('input_number.lab_demo_end_minute') | int(1401) }}}}
          then:
            - service: script.lab_demo_reset
        # Continue from the frozen minute: t0 such that the stepper's live
        # minute equals lab_sim_minute now. Rounded DOWN (t0 is whole seconds):
        # the live minute may run up to ~1 sim minute ahead, never behind, so
        # the stepper cannot fall back into the previous block.
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_demo_t0 }}
          data:
            value: >-
              {{{{ (as_timestamp(now())
                  - (states('input_number.lab_sim_minute') | float(321)
                     - states('input_number.lab_demo_start_minute') | float(321)) / 10
                  * ([states('input_number.lab_demo_block_s') | float(11.111), 0.5] | max))
                 | round(0, 'floor') | int }}}}
        - service: input_boolean.turn_on
          target: {{ entity_id: input_boolean.lab_demo_running }}

    lab_demo_pause:
      alias: "Lab Demo anhalten"
      icon: mdi:pause
      sequence:
        # Only a running replay has a live minute; frozen stays frozen.
        - condition: state
          entity_id: input_boolean.lab_demo_running
          state: "on"
        - service: input_number.set_value
          target: {{ entity_id: input_number.lab_sim_minute }}
          data:
            value: >-
              {{{{ [states('input_number.lab_demo_start_minute') | float(321)
                  + (as_timestamp(now()) - states('input_number.lab_demo_t0') | float(0))
                  / ([states('input_number.lab_demo_block_s') | float(11.111), 0.5] | max) * 10,
                  states('input_number.lab_demo_end_minute') | float(1401)] | min | int }}}}
        - service: input_boolean.turn_off
          target: {{ entity_id: input_boolean.lab_demo_running }}
        # The 1 s stepper may not have applied the block of the frozen minute
        # yet (paused right after a block boundary): apply it, so the frozen
        # picture matches the frozen clock.
        - if: >-
            {{{{ (states('input_number.lab_sim_minute') | int(0)) // 10
               != states('input_number.sim_step') | int(0) }}}}
          then:
            - service: script.lab_sim_apply_row
              data:
                i: "{{{{ [(states('input_number.lab_sim_minute') | int(0)) // 10, {n - 1}] | min }}}}"

    lab_demo_exit:
      alias: "Lab Demo beenden (echte Sensoren)"
      icon: mdi:stop
      sequence:
        - service: input_boolean.turn_off
          target: {{ entity_id: [input_boolean.lab_demo_running, input_boolean.sim_sensor_dropout, input_boolean.simulation_mode] }}

    lab_prod_automations_on:
      alias: "Lab: Prod-Automationen wieder einschalten"
      icon: mdi:robot
      sequence:
        - service: automation.turn_on
          target:
            entity_id: >-
              {{{{ states.automation | rejectattr('attributes.id', 'undefined')
                 | rejectattr('attributes.id', 'search', '^lab_')
                 | map(attribute='entity_id') | list }}}}

  automation:
    - id: lab_demo_stepper
      alias: "Lab Demo: Takt (zeitbasiert)"
      mode: single
      max_exceeded: silent
      trigger:
        - platform: time_pattern
          seconds: "/1"
      condition:
        - condition: state
          entity_id: input_boolean.lab_demo_running
          state: "on"
      action:
        - variables:
            start_min: "{{{{ states('input_number.lab_demo_start_minute') | int(321) }}}}"
            end_min: "{{{{ states('input_number.lab_demo_end_minute') | int(1401) }}}}"
            dt: "{{{{ [states('input_number.lab_demo_block_s') | float(11.111), 0.5] | max }}}}"
            t0: "{{{{ states('input_number.lab_demo_t0') | float(0) }}}}"
            live_min: "{{{{ start_min + (as_timestamp(now()) - t0) / dt * 10 }}}}"
            target: "{{{{ (live_min // 10) | int }}}}"
            cur: "{{{{ states('input_number.sim_step') | int(0) }}}}"
        - choose:
            - conditions: "{{{{ live_min >= end_min }}}}"
              sequence:
                - service: input_number.set_value
                  target: {{ entity_id: input_number.lab_sim_minute }}
                  data: {{ value: "{{{{ end_min }}}}" }}
                - service: input_boolean.turn_off
                  target: {{ entity_id: input_boolean.lab_demo_running }}
                # Loop: Play at the end of the window resets and starts over.
                - if:
                    - condition: state
                      entity_id: input_boolean.lab_demo_loop
                      state: "on"
                  then:
                    - service: script.lab_demo_play
            - conditions: "{{{{ target != cur }}}}"
              sequence:
                - service: script.lab_sim_apply_row
                  data: {{ i: "{{{{ target }}}}" }}

    # simulation_mode is declared with `initial: off` in the shared
    # configuration.yaml (correct for prod), so every lab restart would drop the
    # dashboard back to the real (offline) sensors. Restore it while a replay is
    # loaded, and re-apply the current block.
    - id: lab_demo_restore_on_start
      alias: "Lab Demo: Sim nach Neustart wiederherstellen"
      trigger:
        - platform: homeassistant
          event: start
      condition:
        - condition: template
          value_template: "{{{{ states('input_number.lab_demo_t0') | float(0) > 0 }}}}"
      action:
        - service: input_boolean.turn_on
          target: {{ entity_id: input_boolean.simulation_mode }}
        - service: script.lab_demo_seed_values
        - delay: 5
        - service: script.lab_sim_apply_row
          data: {{ i: "{{{{ states('input_number.sim_step') | int(32) }}}}" }}
"""


def _ent_header(meta: dict) -> str:
    return f"""\
# lab_sim_entities.yaml — LAB-ONLY stand-ins for dashboard entities the lab
# cannot provide ({meta['day']} replay). GENERATED by scripts/build_sim_day.py.
#
# Miner details reuse prod's template unique_ids (avalonq_minerN.yaml, which the
# lab deploy skips): the entity registry keeps the prod entity ids, no surgery.
# Device plugs whose ids are still held by a disabled lab integration live
# under a lab_ prefix; deploy_ha_lab.py rewrites the references.
# Sources per value: see the generator docstring (recorded / prod typical
# profile / static prod snapshot / constructed).

lab_sim_entities:
"""


def build_entities_yaml(meta: dict) -> str:
    snap = json.loads((LAB_ONLY / "prod_snapshot_20261015.json").read_text(encoding="utf-8"))

    def sv(eid: str, default: str = "") -> str:
        v = snap.get(eid, {}).get("state", default)
        return str(v).replace('"', "'")

    def fname(eid: str, fallback: str) -> str:
        return str(snap.get(eid, {}).get("attributes", {}).get("friendly_name", fallback)).replace('"', "'")

    out = [_ent_header(meta)]
    out.append("""\
  input_boolean:
    miner1_power_dialog:
      name: "miner1.power_dialog"
      icon: mdi:menu
    miner2_power_dialog:
      name: "miner2.power_dialog"
      icon: mdi:menu
    lab_miner1_relay:
      name: "Lab Miner 1 Steckdose"
      icon: mdi:power-socket-de
      initial: "on"
    lab_miner2_relay:
      name: "Lab Miner 2 Steckdose"
      icon: mdi:power-socket-de
      initial: "on"
    lab_lueftung_relay:
      name: "Lab Lueftung Steckdose"
      icon: mdi:fan
      initial: "off"
""")
    for n in (1, 2):
        out.append("".join(
            f"    miner{n}_detail_{k}:\n      name: \"miner{n}.detail_{k}\"\n      icon: {icon}\n"
            for k, icon in (("power", "mdi:flash-outline"), ("miner", "mdi:memory"),
                            ("hashboard", "mdi:expansion-card-variant"), ("cooling", "mdi:fan"),
                            ("pool", "mdi:pool"), ("log", "mdi:text-box-outline"))))

    # Script stubs the power dialog calls (prod: avalonq_minerN.yaml). "Shelly
    # Notaus" drops the simulated relay; lab_miner_sim.yaml (automation
    # lab_miner_physical_relay) carries that to the plug of the physical LAB
    # miner, never to a prod plug.
    out.append("  script:\n")
    for n in (1, 2):
        out.append(f"""\
    miner{n}_dialog_softon:
      alias: "M{n}: Normal einschalten"
      sequence:
        - service: input_select.select_option
          target: {{ entity_id: input_select.miner{n}_mode }}
          data: {{ option: Eco }}
        - service: input_boolean.turn_off
          target: {{ entity_id: input_boolean.miner{n}_power_dialog }}
    miner{n}_dialog_softoff:
      alias: "M{n}: Normal ausschalten"
      sequence:
        - service: input_select.select_option
          target: {{ entity_id: input_select.miner{n}_mode }}
          data: {{ option: Standby }}
        - service: input_boolean.turn_off
          target: {{ entity_id: input_boolean.miner{n}_power_dialog }}
    miner{n}_dialog_shelly_off:
      alias: "M{n}: Shelly Notaus (Lab: schaltet den Lab-Miner aus)"
      sequence:
        - service: input_select.select_option
          target: {{ entity_id: input_select.miner{n}_mode }}
          data: {{ option: Standby }}
        - service: input_boolean.turn_off
          target: {{ entity_id: [input_boolean.lab_miner{n}_relay, input_boolean.miner{n}_power_dialog] }}
    miner{n}_dialog_reboot:
      alias: "M{n}: Reboot"
      sequence:
        - service: input_boolean.turn_off
          target: {{ entity_id: input_boolean.miner{n}_power_dialog }}
""")

    # API status stubs (same command_line unique_ids as avalonq).
    out.append("  command_line:\n")
    for n in (1, 2):
        for api in ("stats", "litestats", "coin", "summary", "pools", "devs", "devdetails", "version", "config"):
            out.append(f"""\
    - sensor:
        unique_id: miner{n}.api.{api}
        name: "miner{n}.api.{api}"
        command: "echo OK"
        scan_interval: 3600
""")

    out.append("  template:\n    - switch:\n")
    for obj, n in MINER_PLUGS.items():
        out.append(f"""\
        - name: "{fname('switch.' + obj, 'Miner ' + str(n) + ' Steckdose')}"
          unique_id: lab_{obj}_switch
          default_entity_id: switch.lab_{obj}
          state: "{{{{ is_state('input_boolean.lab_miner{n}_relay', 'on') }}}}"
          turn_on:
            - service: input_boolean.turn_on
              target: {{ entity_id: input_boolean.lab_miner{n}_relay }}
          turn_off:
            - service: input_select.select_option
              target: {{ entity_id: input_select.miner{n}_mode }}
              data: {{ option: Standby }}
            - service: input_boolean.turn_off
              target: {{ entity_id: input_boolean.lab_miner{n}_relay }}
""")

    out.append("    - binary_sensor:\n")
    for n in (1, 2):
        out.append(f"""\
        - name: "miner{n}.LcdOnOff.Status"
          unique_id: miner{n}.LcdOnOff.Status
          icon: mdi:overscan
          state: "{{{{ is_state('input_boolean.miner{n}_lcd_lab', 'on') }}}}"
        - name: "miner{n}.Pool_Status"
          unique_id: miner{n}.Pool_Status
          device_class: connectivity
          state: "true"
""")

    out.append("    - sensor:\n")
    mode = "{{% set m = states('input_select.miner{n}_mode') %}}{{% set c = ['Standby','Eco','Standard','Super'].index(m) if m in ['Standby','Eco','Standard','Super'] else 0 %}}"

    def ms(n: int, uid: str, state: str, unit: str = "", dc: str = "", icon: str = "", sc: bool = False) -> str:
        lines = [f"        - name: \"miner{n}.{uid}\"", f"          unique_id: miner{n}.{uid}"]
        if icon:
            lines.append(f"          icon: {icon}")
        if unit:
            lines.append(f"          unit_of_measurement: \"{unit}\"")
        if dc:
            lines.append(f"          device_class: {dc}")
        if sc:
            lines.append("          state_class: measurement")
        lines.append(f"          state: >-\n            {state}")
        return "\n".join(lines) + "\n"

    for n in (1, 2):
        ti, ii, hbi, hbo, rj = (25, 27, 29, 31, 35) if n == 1 else (26, 28, 30, 32, 36)
        p = f"sensor.miner{n}_"
        md = mode.format(n=n)
        idle_sys = sv(p + "systemstatus", "Work: In Idle, Hash Board: 1")
        run_sys = idle_sys.replace("In Idle", "In Work")
        out.append(ms(n, "ITemp", f"{ROW}{{{{ r[{ii}] if r else 25 }}}}", "°C", "temperature", "mdi:thermometer", True))
        out.append(ms(n, "HBITemp", f"{ROW}{{{{ r[{hbi}] if r else 25 }}}}", "°C", "temperature", "mdi:thermometer", True))
        out.append(ms(n, "HBOTemp", f"{ROW}{{{{ r[{hbo}] if r else 25 }}}}", "°C", "temperature", "mdi:thermometer", True))
        out.append(ms(n, "TMax", f"{ROW}{{{{ r[{ti}] if r else 25 }}}}", "°C", "temperature", "mdi:thermometer-high", True))
        out.append(ms(n, "TAvg", f"{ROW}{{{{ ((r[{hbi}] + r[{hbo}] + r[{ti}]) / 3) | round(1) if r and r[{ti}] > 0 else 0 }}}}",
                      "°C", "temperature", "mdi:thermometer-auto", True))
        out.append(ms(n, "TarT", sv(p + "tart", "65.0"), "°C", "temperature", "mdi:thermometer-check"))
        for f in (1, 2, 3, 4):
            out.append(ms(n, f"Fan{f}", f"{md}{{{{ {FAN_RPM}[c] }}}}", "rpm", "", "mdi:fan"))
        out.append(ms(n, "FanR", f"{md}{{{{ {FAN_PCT}[c] }}}}", "%", "", "mdi:fan"))
        out.append(ms(n, "Cur_Load", f"{{{{ states('sensor.miner{n}_sim_power') | float(0) | round(0) }}}}", "W", "power", "mdi:flash", True))
        out.append(ms(n, "Mode_Power_Output", f"{md}{{{{ {MODE_POWER_OUTPUT}[c] }}}}", "W", "", "mdi:lightning-bolt"))
        out.append(ms(n, "THSspd",
                      f"{ROW}{md}{{{{ (r[{10 if n == 1 else 11}] if (r and is_state('input_boolean.miner{n}_auto_load_management', 'on')) else [0, 43, 70, 90][c]) }}}}",
                      "TH/s", "", "mdi:speedometer", True))
        out.append(ms(n, "Energy_per_TH",
                      f"{{% set t = states('sensor.miner{n}_thsspd') | float(0) %}}{{{{ ((states('sensor.miner{n}_cur_load') | float(0)) / t) | round(1) if t > 0 else 0 }}}}",
                      "J/TH", "", "mdi:lightning-bolt"))
        out.append(ms(n, "Rejection_Rate", f"{ROW}{{{{ r[{rj}] if r else 0 }}}}", "%", "", "mdi:trash-can-outline"))
        out.append(ms(n, "Systemstatus", f"{md}{{{{ '{run_sys}' if c > 0 else '{idle_sys}' }}}}", "", "", "mdi:comment-text-outline"))
        out.append(ms(n, "Network_Difficulty", str(meta["difficulty_t"]), "T", "", "mdi:calculator-variant-outline"))
        for uid, key, unit, icon in (
            ("State", "state", "", "mdi:list-status"), ("Uptime", "uptime", "", "mdi:timer-outline"),
            ("CPU_Model", "cpu_model", "", "mdi:memory"), ("ASIC_Model", "asic_model", "", "mdi:chip"),
            ("CPU_Freq", "cpu_freq", "MHz", "mdi:sine-wave"), ("ID", "id", "", "mdi:id-card"),
            ("Filter", "filter", "min", "mdi:air-filter"), ("Network_Errors", "network_errors", " ", "mdi:lan"),
            ("Total_ASICs", "total_asics", " ", "mdi:chip"), ("FanErr", "fanerr", "", "mdi:fan-alert"),
            ("Ping", "ping", "ms", "mdi:progress-clock"), ("Worklevel", "worklevel", "", "mdi:cog-play-outline"),
            ("Found_Blocks", "found_blocks", "", "mdi:cube-outline"),
            ("Hardware_Errors", "hardware_errors", " ", "mdi:alert-outline"),
            ("Avg_Shares_per_Min", "avg_shares_per_min", " ", "mdi:timer-outline"),
            ("Hardware_ErrorsR", "hardware_errorsr", "%", "mdi:alert-outline"), ("Pool", "pool", "", "mdi:pool"),
            ("Accepted_Shares", "accepted_shares", " ", "mdi:sticker-check"),
            ("Rejected_Shares", "rejected_shares", " ", "mdi:sticker-remove-outline"),
            ("Latest_Share", "latest_share", "s", "mdi:clock-check"),
            ("Stratum_Difficulty", "stratum_difficulty", " ", "mdi:calculator-variant-outline"),
            ("CGMiner_Version", "cgminer_version", "", "mdi:counter"),
            ("API_Version.Status", "api_version_status", "", "mdi:api"),
            ("Firmware", "firmware", "", "mdi:chip"), ("MAC_Address", "mac_address", "", "mdi:ethernet"),
        ):
            out.append(ms(n, uid, sv(p + key, "0"), unit, "", icon))
        out.append(f"""\
        - name: "miner{n}_hashrate"
          unique_id: lab_miner{n}_hashrate
          unit_of_measurement: "TH/s"
          state: "{{{{ states('sensor.miner{n}_thsspd') | float(0) }}}}"
""")

    # Device plugs (power + lifetime energy), heating rod, room sensors.
    def dev(obj: str, eid_obj: str) -> str:
        pw_id, en_id = f"sensor.{obj}_leistung", f"sensor.{obj}_energie"
        base = 0.0
        try:
            base = float(snap.get(en_id, {}).get("state", 0))
        except ValueError:
            base = 0.0
        miner = MINER_PLUGS.get(obj)
        # Miner plugs mirror the simulated miner power; outside the replay 0 W
        # (demo_flow's prod branch reads this plug, a mutual reference with
        # sensor.minerN_sim_power must not exist while simulation_mode is off).
        pw_state = (f"{{{{ (states('sensor.miner{miner}_sim_power') | float(0)) if is_state('input_boolean.simulation_mode', 'on') else 0 }}}}" if miner else
                    DEV.replace("{attr}", "dev_w") + f"{{{{ d['{obj}'][i] if d and '{obj}' in d else 0 }}}}")
        en_state = (f"{{{{ ({base} + states('sensor.mining_energy_daily') | float(0) / 2) | round(3) }}}}" if miner else
                    DEV.replace("{attr}", "dev_kwh") + f"{{{{ ({base} + (d['{obj}'][i] if d and '{obj}' in d else 0)) | round(3) }}}}")
        return f"""\
        - name: "{fname(pw_id, obj + ' Leistung')}"
          unique_id: lab_{obj}_leistung
          default_entity_id: sensor.{eid_obj}_leistung
          unit_of_measurement: "W"
          device_class: power
          state_class: measurement
          state: >-
            {pw_state}
        - name: "{fname(en_id, obj + ' Energie')}"
          unique_id: lab_{obj}_energie
          default_entity_id: sensor.{eid_obj}_energie
          unit_of_measurement: "kWh"
          device_class: energy
          state_class: total_increasing
          state: >-
            {en_state}
"""

    for obj in sorted(set(meta["dev_w"]) | set(MINER_PLUGS)):
        out.append(dev(obj, ("lab_" + obj) if obj in LAB_PREFIXED else obj))

    typ = json.loads((LAB_ONLY / "prod_typprofil_20261015.json").read_text(encoding="utf-8"))["slots"]

    def typ_sensor(eid: str, name: str, unit: str, dc: str, target: str) -> str:
        slots = [v if v is not None else 0 for v in typ.get(eid, [0] * 144)]
        return f"""\
        - name: "{name}"
          unique_id: lab_{target.split('.', 1)[1]}
          default_entity_id: {target}
          unit_of_measurement: "{unit}"
          device_class: {dc}
          state_class: measurement
          state: >-
            {{% set i = states('input_number.sim_step')|int(0) %}}{{{{ {json.dumps(slots)}[i] }}}}
          # Whole day for the "Verlauf (heute)" charts in the replay
          # (window.bgaiSimSeries in www/bitgrid_card_shape.js).
          attributes:
            day_values: >-
              {{{{ {json.dumps(slots)} }}}}
"""

    out.append(typ_sensor("sensor.ewelink_snzb_01p_temperatur", fname("sensor.ewelink_snzb_01p_temperatur", "Temperatur"),
                          "°C", "temperature", "sensor.lab_ewelink_snzb_01p_temperatur"))
    out.append(typ_sensor("sensor.ewelink_snzb_02p_temperatur_2", fname("sensor.ewelink_snzb_02p_temperatur_2", "Temperatur"),
                          "°C", "temperature", "sensor.lab_ewelink_snzb_02p_temperatur_2"))
    out.append(typ_sensor("sensor.ac_elwa_2_temperatur_1", "AC ELWA 2 Temperatur 1", "°C", "temperature",
                          "sensor.ac_elwa_2_temperatur_1"))
    out.append(f"""\
        - name: "AC ELWA 2 Power1 Solar"
          unique_id: lab_ac_elwa_2_power1_solar
          default_entity_id: sensor.ac_elwa_2_power1_solar
          unit_of_measurement: "W"
          device_class: power
          state_class: measurement
          state: >-
            {ROW}{{{{ r[24] if r else 0 }}}}
        - name: "AC ELWA 2 Power1 Grid"
          unique_id: lab_ac_elwa_2_power1_grid
          default_entity_id: sensor.ac_elwa_2_power1_grid
          unit_of_measurement: "W"
          device_class: power
          state_class: measurement
          state: "0"
        - name: "AC ELWA 2 Screen Mode"
          unique_id: lab_ac_elwa_2_screen_mode
          default_entity_id: sensor.ac_elwa_2_screen_mode
          state: "{sv('sensor.ac_elwa_2_screen_mode', 'Standby')}"
""")
    # FRITZ! stand-ins (integration disabled in the house network): state and
    # temperatures of the static prod snapshot (15.10.2026). Entities that are
    # unavailable in prod too stay unavailable here (mirror, not invent).
    for c in ("bad", "buro_michael", "davids_zimmer", "gastezimmer", "hauswirtschaftsraum",
              "kuche", "michaels_schlafzimmer", "wohnzimmer_fenster", "wohnzimmer_ofen"):
        x = snap.get(f"climate.{c}", {})
        st, a = x.get("state", "unavailable"), x.get("attributes", {})
        ok = st not in ("unavailable", "unknown")
        nm = str(a.get("friendly_name", c)).replace('"', "'")
        out.append(
            f'        - name: "{nm}"\n'
            f"          unique_id: lab_climate_{c}\n"
            f"          default_entity_id: sensor.lab_climate_{c}\n"
            f"          icon: mdi:radiator\n"
            f'          availability: "{"true" if ok else "false"}"\n'
            f'          state: "{st}"\n'
            f"          attributes:\n"
            f'            current_temperature: "{{{{ {a.get("current_temperature") or "none"} }}}}"\n'
            f'            temperature: "{{{{ {a.get("temperature") or "none"} }}}}"\n')
    out.append(
        '        - name: "Wohnwand Beleuchtung Energie"\n'
        "          unique_id: lab_wohnwand_beleuchtung_energie\n"
        "          default_entity_id: sensor.lab_wohnwand_beleuchtung_energie\n"
        '          unit_of_measurement: "kWh"\n'
        "          device_class: energy\n"
        "          state_class: total_increasing\n"
        f'          state: "{sv("sensor.wohnwand_beleuchtung_energie", "0")}"\n')
    out.append("    - binary_sensor:\n")
    for w in ("buro_grosses_fenster", "buro_kleines_fenster", "davids_zimmer", "gastezimmer", "hauswirtschaftsraum",
              "kuche", "michaels_schlafzimmer", "wohnzimmer_fenster", "wohnzimmer_ofen"):
        x = snap.get(f"binary_sensor.{w}_alarm", {})
        st, a = x.get("state", "unavailable"), x.get("attributes", {})
        ok = st not in ("unavailable", "unknown")
        nm = str(a.get("friendly_name", w)).replace('"', "'")
        out.append(
            f'        - name: "{nm}"\n'
            f"          unique_id: lab_{w}_alarm\n"
            f"          default_entity_id: binary_sensor.lab_{w}_alarm\n"
            f"          device_class: window\n"
            f'          availability: "{"true" if ok else "false"}"\n'
            f'          state: "{"true" if st == "on" else "false"}"\n')
    # Ventilation plug switch (shelly, never set up on the lab): simulated relay.
    x = snap.get("switch.shellyplusplugs_d4d4daf4eda4", {})
    nm = str(x.get("attributes", {}).get("friendly_name", "Lueftung")).replace('"', "'")
    out.append(
        "    - switch:\n"
        f'        - name: "{nm}"\n'
        "          unique_id: lab_shellyplusplugs_d4d4daf4eda4_switch\n"
        "          default_entity_id: switch.shellyplusplugs_d4d4daf4eda4\n"
        "          state: \"{{ is_state('input_boolean.lab_lueftung_relay', 'on') }}\"\n"
        "          turn_on:\n"
        "            - service: input_boolean.turn_on\n"
        "              target: { entity_id: input_boolean.lab_lueftung_relay }\n"
        "          turn_off:\n"
        "            - service: input_boolean.turn_off\n"
        "              target: { entity_id: input_boolean.lab_lueftung_relay }\n")
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default="2026-07-11", help="local date (Europe/Berlin)")
    ap.add_argument("--db", type=Path, default=REPO / "data" / "bitgrid.db")
    ap.add_argument("--display-date", default=None,
                    help="date shown in the lab (default: DISPLAY_DATE mapping, else --day)")
    args = ap.parse_args()
    rows, meta = load_day(args.day, args.db)
    display_day = args.display_date or DISPLAY_DATE.get(args.day, args.day)
    apply_display_offset(meta, display_day)
    txt = texts(rows)
    LAB_ONLY.mkdir(parents=True, exist_ok=True)
    (LAB_ONLY / "lab_sim_day.yaml").write_text(build_day_yaml(display_day, rows, meta, txt), encoding="utf-8", newline="\n")
    (LAB_ONLY / "lab_sim_entities.yaml").write_text(build_entities_yaml(meta), encoding="utf-8", newline="\n")
    www = LAB_ONLY / "www"
    www.mkdir(exist_ok=True)
    (www / "pool_dummy_balance.json").write_text(json.dumps(meta["pool_json"]), encoding="utf-8")
    (www / "energy_to_sats.json").write_text(json.dumps(meta["eff_json"]), encoding="utf-8")
    cfg = LAB_ONLY / "config"
    cfg.mkdir(exist_ok=True)
    (cfg / "mining_log.csv").write_text(meta["mining_log_csv"], encoding="utf-8", newline="\n")
    pv = [r[0] for r in rows]
    soc = [r[4] for r in rows]
    print(f"Wrote lab_sim_day.yaml + lab_sim_entities.yaml ({len(rows)} blocks, data {args.day},"
          f" shown as {display_day}, offset {meta['display_offset_days']} d)")
    print(f"  PV peak {max(pv)} W | SoC {min(soc)}-{max(soc)}% | BTC {meta['btc_eur']} EUR | "
          f"constructed blocks {[i for i, r in enumerate(rows) if r[37]]}")
    print(f"  device sources: {meta['dev_src']}")
    print(f"  pool log (real payouts): {meta['pool_log']}")
    print(f"  pool as of day: balance {meta['pool_json']['balance']} BTC, last day {meta['pool_json']['value_last_day']},"
          f" {len(meta['pool_json']['payout_history'])} payouts | eff latest_avg_7d {meta['eff_json']['latest_avg_7d']}")
    print(f"  mining log: {meta['mining_log_a'][:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
