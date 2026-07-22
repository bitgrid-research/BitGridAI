"""
DailyKPI — verdichtet energy_states und miner_states zu Tageszeilen.

Kein neuer Informationsgehalt, nur eine andere Groessenordnung: ein Monat sind
4464 Bloecke, aber 31 Zeilen in daily_kpi. Fuer einen Analyse-Agenten mit
begrenztem Kontextfenster ist das der Unterschied zwischen einer unbeantwortbaren
und einer billigen Frage. Wer Details braucht, steigt ueber block_id wieder in
die Blocktabellen ab: dort ist nichts weggeworfen.

Idempotent: jeder Lauf berechnet die betroffenen Tage neu und ersetzt sie
(INSERT OR REPLACE). Ein reparierter Rohwert schlaegt damit beim naechsten Lauf
automatisch in die Aggregate durch.

CLI:
  python -m src.data.daily_kpi                    # alle Tage in der DB
  python -m src.data.daily_kpi --days 7           # nur die letzten 7 Tage
  python -m src.data.daily_kpi --date 2026-07-20  # ein einzelner Tag
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from datetime import date, datetime, timedelta, timezone

from src.data.db import get_connection

log = logging.getLogger(__name__)

BLOCK_MINUTES = 10
BLOCKS_PER_DAY = 144
BLOCK_HOURS = BLOCK_MINUTES / 60.0
TEMP_CRIT_C = 110.0
TEMP_MISSING_C = 999.0
SURPLUS_W = 1000.0
MINER_IDLE_W = 100.0

# Muss mit SOC_BANDS in src/data/daily_report.py uebereinstimmen.
# Grenzen = Schaltschwellen aus packages/mvp_auto.yaml (60/70/85/100).
_SOC_BANDS: tuple[tuple[str, float, float], ...] = (
    ("soc_h_locked", -1.0, 60.0),
    ("soc_h_hold", 60.0, 70.0),
    ("soc_h_eco", 70.0, 85.0),
    ("soc_h_standard", 85.0, 100.0),
    ("soc_h_super", 100.0, 1000.0),
)
_MODES = (
    ("h_eco", "Eco"),
    ("h_standard", "Standard"),
    ("h_super", "Super"),
    ("h_standby", "Standby"),
)


def _bounds(day: date) -> tuple[str, str]:
    return (
        f"{day.isoformat()}T00:00:00",
        f"{(day + timedelta(days=1)).isoformat()}T00:00:00",
    )


def _kwh(sum_w: float | None) -> float | None:
    return None if sum_w is None else sum_w * BLOCK_HOURS / 1000.0


def days_in_db(conn: sqlite3.Connection) -> list[date]:
    rows = conn.execute(
        "SELECT DISTINCT substr(block_id, 1, 10) FROM energy_states ORDER BY 1"
    ).fetchall()
    return [date.fromisoformat(r[0]) for r in rows]


def compute_day(conn: sqlite3.Connection, day: date) -> bool:
    """Berechnet daily_kpi und daily_miner_kpi fuer einen Tag neu.

    Gibt False zurueck, wenn der Tag keine Bloecke hat (dann wird auch nichts
    geschrieben: eine Zeile mit Nullen waere eine Behauptung ueber einen Tag,
    ueber den wir nichts wissen).
    """
    start, end = _bounds(day)
    now = datetime.now(timezone.utc).isoformat()

    base = conn.execute(
        "SELECT COUNT(*), "
        "SUM(CASE WHEN quality = 'warn' THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN quality = 'error' THEN 1 ELSE 0 END), "
        "SUM(pv_power_w), SUM(house_load_w), SUM(grid_import_w), "
        "SUM(grid_export_w), SUM(miner_power_w), SUM(heizstab_power_w), "
        "MIN(battery_soc_pct), MAX(battery_soc_pct), AVG(battery_soc_pct) "
        "FROM energy_states WHERE block_id >= ? AND block_id < ?",
        (start, end),
    ).fetchone()
    blocks = base[0] or 0
    if blocks == 0:
        return False

    missing: dict[str, int] = {}
    for (raw,) in conn.execute(
        "SELECT missing_signals_json FROM energy_states "
        "WHERE block_id >= ? AND block_id < ? AND missing_signals_json <> '[]'",
        (start, end),
    ).fetchall():
        for field in json.loads(raw or "[]"):
            missing[field] = missing.get(field, 0) + 1

    peak = conn.execute(
        "SELECT block_id, pv_power_w FROM energy_states "
        "WHERE block_id >= ? AND block_id < ? AND pv_power_w IS NOT NULL "
        "ORDER BY pv_power_w DESC LIMIT 1",
        (start, end),
    ).fetchone()

    band_hours: dict[str, float] = {}
    for name, low, high in _SOC_BANDS:
        n = conn.execute(
            "SELECT COUNT(*) FROM energy_states WHERE block_id >= ? AND block_id < ? "
            "AND battery_soc_pct >= ? AND battery_soc_pct < ?",
            (start, end, low, high),
        ).fetchone()[0]
        band_hours[name] = n * BLOCK_HOURS

    temp_crit = conn.execute(
        "SELECT COUNT(*) FROM energy_states WHERE block_id >= ? AND block_id < ? "
        "AND miner_temp_c >= ? AND miner_temp_c < ?",
        (start, end, TEMP_CRIT_C, TEMP_MISSING_C),
    ).fetchone()[0]
    mismatch = conn.execute(
        "SELECT COUNT(*) FROM v_schaltfehler WHERE block_id >= ? AND block_id < ?",
        (start, end),
    ).fetchone()[0]
    idle = conn.execute(
        "SELECT COUNT(*) FROM v_ungenutzter_ueberschuss "
        "WHERE block_id >= ? AND block_id < ?",
        (start, end),
    ).fetchone()[0]

    conn.execute(
        "INSERT OR REPLACE INTO daily_kpi (day, blocks, coverage_pct, quality_warn,"
        " quality_error, missing_signals, pv_kwh, house_kwh, grid_import_kwh,"
        " grid_export_kwh, mining_kwh, heizstab_kwh, pv_peak_w, pv_peak_block,"
        " soc_min_pct, soc_max_pct, soc_mean_pct, soc_h_locked, soc_h_hold,"
        " soc_h_eco, soc_h_standard, soc_h_super, blocks_temp_ge_110,"
        " blocks_switch_mismatch, blocks_surplus_idle, computed_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            day.isoformat(),
            blocks,
            blocks / BLOCKS_PER_DAY * 100.0,
            base[1] or 0,
            base[2] or 0,
            json.dumps(missing, sort_keys=True) if missing else None,
            _kwh(base[3]),
            _kwh(base[4]),
            _kwh(base[5]),
            _kwh(base[6]),
            _kwh(base[7]),
            _kwh(base[8]),
            peak[1] if peak else None,
            peak[0] if peak else None,
            base[9],
            base[10],
            base[11],
            band_hours["soc_h_locked"],
            band_hours["soc_h_hold"],
            band_hours["soc_h_eco"],
            band_hours["soc_h_standard"],
            band_hours["soc_h_super"],
            temp_crit,
            mismatch,
            idle,
        )
        + (now,),
    )

    conn.execute("DELETE FROM daily_miner_kpi WHERE day = ?", (day.isoformat(),))
    miners = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT miner FROM miner_states "
            "WHERE block_id >= ? AND block_id < ? ORDER BY miner",
            (start, end),
        ).fetchall()
    ]
    for miner in miners:
        hours: dict[str, float] = {}
        for column, mode in _MODES:
            n = conn.execute(
                "SELECT COUNT(*) FROM miner_states WHERE miner = ? "
                "AND block_id >= ? AND block_id < ? AND workmode_status = ?",
                (miner, start, end, mode),
            ).fetchone()[0]
            hours[column] = n * BLOCK_HOURS

        agg = conn.execute(
            "SELECT AVG(ths), AVG(power_w), MAX(tmax_c), AVG(tmax_c), "
            "AVG(tmax_c - hbotemp_c), "
            "SUM(CASE WHEN tmax_c >= ? THEN 1 ELSE 0 END), AVG(rejection_rate_pct) "
            "FROM miner_states WHERE miner = ? AND block_id >= ? AND block_id < ? "
            "AND ths > 0",
            (TEMP_CRIT_C, miner, start, end),
        ).fetchone()
        ths_mean, watt_mean = agg[0], agg[1]
        w_per_th = watt_mean / ths_mean if ths_mean and watt_mean else None
        mism = conn.execute(
            "SELECT COUNT(*) FROM v_schaltfehler WHERE miner = ? "
            "AND block_id >= ? AND block_id < ?",
            (miner, start, end),
        ).fetchone()[0]

        conn.execute(
            "INSERT INTO daily_miner_kpi (day, miner, h_eco, h_standard, h_super,"
            " h_standby, ths_mean, watt_mean, w_per_th, tmax_max_c, tmax_mean_c,"
            " spread_mean_k, blocks_ge_110, switch_mismatches, rejection_mean_pct,"
            " computed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                day.isoformat(),
                miner,
                hours["h_eco"],
                hours["h_standard"],
                hours["h_super"],
                hours["h_standby"],
                ths_mean,
                watt_mean,
                w_per_th,
                agg[2],
                agg[3],
                agg[4],
                agg[5] or 0,
                mism,
                agg[6],
                now,
            ),
        )

    return True


def rebuild(conn: sqlite3.Connection, days: list[date]) -> int:
    written = 0
    for day in days:
        if compute_day(conn, day):
            written += 1
    conn.commit()
    return written


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tagesaggregate neu berechnen")
    parser.add_argument("--date", default=None, help="Einzelner Tag (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=None, help="Letzte N Tage")
    parser.add_argument("--db", default="data/bitgrid.db")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parse_args()
    conn = get_connection(args.db)
    try:
        if args.date:
            days = [date.fromisoformat(args.date)]
        elif args.days:
            today = datetime.now(timezone.utc).date()
            candidates = {today - timedelta(days=i) for i in range(args.days)}
            days = sorted(candidates & set(days_in_db(conn)))
        else:
            days = days_in_db(conn)
        written = rebuild(conn, days)
        print(f"daily_kpi: {written} Tage berechnet (von {len(days)} geprueft)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
