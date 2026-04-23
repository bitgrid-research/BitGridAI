#!/usr/bin/env python3
"""
Exportiert HA-Sensorhistorie als Simulations-Szenario-CSV.

Workflow:
  # 1. DB vom Umbrel holen
  scp umbrel@umbrel.local:~/umbrel/app-data/home-assistant/data/home-assistant_v2.db /tmp/ha.db

  # 2. Szenario exportieren
  python scripts/ha_export_scenario.py --db /tmp/ha.db --start 2026-04-01 --end 2026-04-30 --out src/sim/scenarios/real_april_2026.csv

  # 3. Optional: nur einen Tag
  python scripts/ha_export_scenario.py --db /tmp/ha.db --start 2026-04-20 --out src/sim/scenarios/real_2026-04-20.csv

Ausgabe-Spalten:
  timestamp_offset_min, pv_power_w, house_load_w, grid_import_w, battery_soc_pct,
  miner_temp_c, miner_heartbeat_age_sec, energy_price_ct_kwh, pv_forecast_kw,
  grid_export_w, miner_power_w, heizstab_power_w
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Entity-ID → Spaltenname
# ---------------------------------------------------------------------------

ENTITIES: dict[str, str] = {
    "sensor.pv_power_w":                              "pv_power_w",
    "sensor.house_load_w":                            "house_load_w",
    "sensor.grid_import_w":                           "grid_import_w",
    "sensor.grid_export_w":                           "grid_export_w",
    "sensor.battery_soc_pct":                         "battery_soc_pct",
    "sensor.miner_total_power_w":                     "miner_power_w",
    "sensor.miner_max_chip_temp_c":                   "miner_temp_c",
    "sensor.ac_elwa_2_192_168_178_58_power1_solar":   "heizstab_power_w",
}

BLOCK_MIN = 10  # Blockgröße in Minuten

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def floor_to_block(ts: datetime) -> datetime:
    """Rundet einen Zeitstempel auf den nächsten 10-Minuten-Block ab."""
    return ts.replace(minute=(ts.minute // BLOCK_MIN) * BLOCK_MIN, second=0, microsecond=0)


def detect_schema(conn: sqlite3.Connection) -> str:
    """Gibt 'new' zurück wenn states_meta existiert, sonst 'old'."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return "new" if "states_meta" in tables else "old"


def fetch_raw(
    conn: sqlite3.Connection,
    schema: str,
    entity_ids: list[str],
    start_ts: float,
    end_ts: float,
) -> dict[str, list[tuple[datetime, float]]]:
    """Lädt Rohwerte für alle Entities als {col_name: [(ts, value), ...]}."""
    results: dict[str, list[tuple[datetime, float]]] = {col: [] for col in ENTITIES.values()}

    if schema == "new":
        # HA >= 2023: states_meta trennt entity_id von states
        meta_q = "SELECT metadata_id, entity_id FROM states_meta WHERE entity_id IN ({})".format(
            ",".join("?" * len(entity_ids))
        )
        meta = {row[0]: row[1] for row in conn.execute(meta_q, entity_ids)}
        if not meta:
            return results

        id_q = """
            SELECT metadata_id, state, last_updated_ts
            FROM states
            WHERE metadata_id IN ({})
              AND last_updated_ts >= ? AND last_updated_ts < ?
              AND state NOT IN ('unknown', 'unavailable', '')
        """.format(",".join("?" * len(meta)))

        params = list(meta.keys()) + [start_ts, end_ts]
        for mid, raw_state, ts_float in conn.execute(id_q, params):
            try:
                value = float(raw_state)
            except (ValueError, TypeError):
                continue
            entity_id = meta[mid]
            col = ENTITIES.get(entity_id)
            if col:
                dt = datetime.fromtimestamp(ts_float, tz=timezone.utc)
                results[col].append((dt, value))

    else:
        # Älteres HA-Schema: entity_id direkt in states
        q = """
            SELECT entity_id, state, last_updated
            FROM states
            WHERE entity_id IN ({})
              AND last_updated >= ? AND last_updated < ?
              AND state NOT IN ('unknown', 'unavailable', '')
        """.format(",".join("?" * len(entity_ids)))

        start_str = datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        end_str = datetime.fromtimestamp(end_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        params = entity_ids + [start_str, end_str]

        for entity_id, raw_state, ts_str in conn.execute(q, params):
            try:
                value = float(raw_state)
            except (ValueError, TypeError):
                continue
            col = ENTITIES.get(entity_id)
            if col:
                dt = datetime.fromisoformat(ts_str.replace(" ", "T")).replace(tzinfo=timezone.utc)
                results[col].append((dt, value))

    return results


def resample(
    raw: dict[str, list[tuple[datetime, float]]],
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """
    Mittelt Rohwerte auf 10-Minuten-Blöcke.
    Lücken werden per Forward-Fill geschlossen.
    """
    # Alle Blöcke des Zeitraums erzeugen
    blocks: list[datetime] = []
    t = floor_to_block(start)
    while t < end:
        blocks.append(t)
        t += timedelta(minutes=BLOCK_MIN)

    # Pro Spalte: Blöcke → Mittelwert
    col_blocks: dict[str, dict[datetime, list[float]]] = {
        col: {b: [] for b in blocks} for col in raw
    }
    for col, readings in raw.items():
        for ts, val in readings:
            b = floor_to_block(ts)
            if b in col_blocks[col]:
                col_blocks[col][b].append(val)

    # Mittelwert berechnen + Forward-Fill
    col_series: dict[str, dict[datetime, float | None]] = {}
    for col, bdict in col_blocks.items():
        last: float | None = None
        series: dict[datetime, float | None] = {}
        for b in blocks:
            vals = bdict[b]
            if vals:
                last = sum(vals) / len(vals)
            series[b] = last  # None wenn noch kein Wert da
        col_series[col] = series

    # Zu Zeilen zusammenführen
    rows = []
    for i, b in enumerate(blocks):
        rows.append(
            {
                "block_ts": b,
                "timestamp_offset_min": i * BLOCK_MIN,
                **{col: col_series[col][b] for col in col_series},
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "timestamp_offset_min",
    "pv_power_w",
    "house_load_w",
    "grid_import_w",
    "battery_soc_pct",
    "miner_temp_c",
    "miner_heartbeat_age_sec",
    "energy_price_ct_kwh",
    "pv_forecast_kw",
    "grid_export_w",
    "miner_power_w",
    "heizstab_power_w",
]


def write_csv(rows: list[dict[str, Any]], out_path: Path, start: datetime, end: datetime) -> None:
    filled = sum(
        1 for r in rows
        if r.get("pv_power_w") is not None and r.get("battery_soc_pct") is not None
    )
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        f.write(f"# Exportiert aus HA-History: {start.date()} – {(end - timedelta(seconds=1)).date()}\n")
        f.write(f"# Blöcke gesamt: {len(rows)}  davon befüllt: {filled}\n")
        f.write("# " + ", ".join(CSV_COLUMNS) + "\n")
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
        for row in rows:
            out = {col: "" for col in CSV_COLUMNS}
            out["timestamp_offset_min"] = row["timestamp_offset_min"]
            for col in CSV_COLUMNS[1:]:
                val = row.get(col)
                if val is not None:
                    out[col] = f"{val:.2f}"
            # Heartbeat default: 5 sec (gesund) wenn Miner-Daten vorhanden
            if not out["miner_heartbeat_age_sec"]:
                out["miner_heartbeat_age_sec"] = "5.0" if row.get("miner_temp_c") is not None else ""
            writer.writerow(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="HA → Szenario-CSV Export")
    p.add_argument("--db", required=True, help="Pfad zur home-assistant_v2.db")
    p.add_argument("--start", required=True, help="Startdatum YYYY-MM-DD")
    p.add_argument("--end", help="Enddatum YYYY-MM-DD (exklusiv). Standard: start + 1 Tag")
    p.add_argument(
        "--out",
        help="Ausgabedatei. Standard: src/sim/scenarios/real_<start>.csv",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Fehler: DB nicht gefunden: {db_path}", file=sys.stderr)
        print("  DB vom Umbrel holen:", file=sys.stderr)
        print("  scp umbrel@umbrel.local:~/umbrel/app-data/home-assistant/data/home-assistant_v2.db /tmp/ha.db", file=sys.stderr)
        sys.exit(1)

    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = (
        datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if args.end
        else start + timedelta(days=1)
    )

    out_path = Path(args.out) if args.out else Path(f"src/sim/scenarios/real_{args.start}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"→ DB:      {db_path}")
    print(f"→ Zeitraum: {start.date()} – {(end - timedelta(seconds=1)).date()}")
    print(f"→ Ausgabe: {out_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    schema = detect_schema(conn)
    print(f"→ Schema:  {schema}")

    entity_ids = list(ENTITIES.keys())
    raw = fetch_raw(conn, schema, entity_ids, start.timestamp(), end.timestamp())
    conn.close()

    found = [e for e, col in ENTITIES.items() if raw[col]]
    missing = [e for e, col in ENTITIES.items() if not raw[col]]
    print(f"→ Sensoren gefunden ({len(found)}/{len(entity_ids)}):")
    for e in found:
        print(f"     ✓ {e}  ({len(raw[ENTITIES[e]])} Messpunkte)")
    if missing:
        print(f"→ Nicht gefunden (werden leer bleiben):")
        for e in missing:
            print(f"     ✗ {e}")

    rows = resample(raw, start, end)
    write_csv(rows, out_path, start, end)

    print(f"✓ {len(rows)} Blöcke exportiert → {out_path}")


if __name__ == "__main__":
    main()
