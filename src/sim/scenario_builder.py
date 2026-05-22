"""
ScenarioBuilder — baut klassifizierte Szenarien aus echten HA-Logs.

Workflow:
  1. Tag aus HA-SQLite-DB exportieren (gleiche Logik wie ha_export_scenario.py)
  2. Tag automatisch klassifizieren (sunny_high, cloudy, stress_soc, ...)
  3. CSV mit Metadaten-Kommentaren annotieren
  4. library.json pflegen (Index aller realen Szenarien)

Verwendung:
  # Einzelner Tag
  python -m src.sim.scenario_builder build --db /tmp/ha.db --date 2026-05-15

  # Datumsbereich
  python -m src.sim.scenario_builder build --db /tmp/ha.db --start 2026-04-01 --end 2026-05-01

  # Bibliothek anzeigen
  python -m src.sim.scenario_builder list [--tag sunny_high]

  # Batch-Replay
  python -m src.sim.scenario_builder replay --tag sunny_high
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.sim.replay import replay_scenario
from src.sim.scenario_loader import load_csv_scenario

_ENTITIES: dict[str, str] = {
    "sensor.pv_power_w": "pv_power_w",
    "sensor.house_load_w": "house_load_w",
    "sensor.grid_import_w": "grid_import_w",
    "sensor.grid_export_w": "grid_export_w",
    "sensor.battery_soc_pct": "battery_soc_pct",
    "sensor.miner_total_power_w": "miner_power_w",
    "sensor.miner_max_chip_temp_c": "miner_temp_c",
    "sensor.ac_elwa_2_192_168_178_58_power1_solar": "heizstab_power_w",
}

_BLOCK_MIN = 10

_CSV_COLUMNS = [
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

_DEFAULT_SCENARIOS_DIR = Path("src/sim/scenarios")


# ---------------------------------------------------------------------------
# Klassifikation und Metadaten (testbar ohne DB)
# ---------------------------------------------------------------------------


def classify(rows: list[dict[str, Any]]) -> list[str]:
    """Bestimmt Tag-Typen anhand der Messwerte eines Tages."""
    pv_values = [r["pv_power_w"] for r in rows if r.get("pv_power_w") is not None]
    soc_values = [
        r["battery_soc_pct"] for r in rows if r.get("battery_soc_pct") is not None
    ]
    temp_values = [r["miner_temp_c"] for r in rows if r.get("miner_temp_c") is not None]
    import_kwh = sum(r.get("grid_import_w") or 0.0 for r in rows) * _BLOCK_MIN / 60_000

    pv_peak_kw = max(pv_values, default=0.0) / 1000.0
    pv_energy_kwh = sum(pv_values) * _BLOCK_MIN / 60_000

    tags: list[str] = []
    if pv_energy_kwh < 0.5:
        tags.append("night_only")
    elif pv_peak_kw > 7.0 and import_kwh < 1.0:
        tags.append("sunny_high")
    elif pv_peak_kw > 3.0:
        tags.append("sunny_low")
    else:
        tags.append("cloudy")

    if soc_values and min(soc_values) < 20.0:
        tags.append("stress_soc")
    if temp_values and max(temp_values) > 85.0:
        tags.append("stress_overtemp")
    if import_kwh > 5.0:
        tags.append("grid_heavy")

    return tags


def compute_meta(
    rows: list[dict[str, Any]], date: str, tags: list[str]
) -> dict[str, Any]:
    """Berechnet aggregierte Kennzahlen für einen Tag."""
    pv_values = [r["pv_power_w"] for r in rows if r.get("pv_power_w") is not None]
    soc_values = [
        r["battery_soc_pct"] for r in rows if r.get("battery_soc_pct") is not None
    ]
    temp_values = [r["miner_temp_c"] for r in rows if r.get("miner_temp_c") is not None]
    import_sum = sum(r.get("grid_import_w") or 0.0 for r in rows)
    export_sum = sum(r.get("grid_export_w") or 0.0 for r in rows)
    filled = sum(
        1
        for r in rows
        if r.get("pv_power_w") is not None and r.get("battery_soc_pct") is not None
    )
    return {
        "date": date,
        "tags": tags,
        "pv_peak_kw": round(max(pv_values, default=0.0) / 1000.0, 2),
        "pv_energy_kwh": round(sum(pv_values) * _BLOCK_MIN / 60_000, 2),
        "min_soc_pct": round(min(soc_values, default=0.0), 1),
        "grid_import_kwh": round(import_sum * _BLOCK_MIN / 60_000, 2),
        "grid_export_kwh": round(export_sum * _BLOCK_MIN / 60_000, 2),
        "max_miner_temp_c": round(max(temp_values, default=0.0), 1),
        "blocks_total": len(rows),
        "blocks_filled": filled,
    }


# ---------------------------------------------------------------------------
# KPI-Berechnung (benötigt Szenario-Rows + Replay-Ergebnisse)
# ---------------------------------------------------------------------------


def compute_kpis(
    rows: list[dict[str, Any]],
    replay_results: list[dict[str, Any]],
    surplus_min_kw: float = 1.5,
) -> dict[str, Any]:
    """
    Berechnet die 3 Kern-KPIs aus Szenario-Rows + Replay-Entscheidungen.

    KPI 1 — Mining-Fenster-Ausnutzung:
        Anteil der Blöcke mit PV-Überschuss, in denen der Miner tatsächlich lief.

    KPI 2 — Verlorener Überschuss:
        Netzeinspeisung (kWh) in Blöcken, in denen der Miner NICHT lief.

    KPI 3 — R5-Deadband-Hit-Rate:
        Anteil aller Blöcke, in denen R5 eine Entscheidung blockiert hat.
    """
    n = min(len(rows), len(replay_results))

    miner_running = False
    surplus_window_blocks = 0
    mining_in_window = 0
    lost_surplus_kwh = 0.0
    r5_hits = 0

    for i in range(n):
        row = rows[i]
        result = replay_results[i]
        action = result["action"]
        code = result.get("decision_code", "")

        if action == "START":
            miner_running = True
        elif action == "STOP":
            miner_running = False
        # NOOP: Miner behält vorherigen Zustand

        pv_w = row.get("pv_power_w") or 0.0
        load_w = row.get("house_load_w") or 0.0
        surplus_kw = (pv_w - load_w) / 1000.0

        if surplus_kw >= surplus_min_kw:
            surplus_window_blocks += 1
            if miner_running:
                mining_in_window += 1

        if not miner_running:
            export_w = row.get("grid_export_w") or 0.0
            lost_surplus_kwh += export_w * _BLOCK_MIN / 60_000

        if code.startswith("NOOP_R5_"):
            r5_hits += 1

    util_pct = (
        round(100 * mining_in_window / surplus_window_blocks, 1)
        if surplus_window_blocks > 0
        else 0.0
    )
    r5_rate_pct = round(100 * r5_hits / n, 1) if n > 0 else 0.0

    return {
        "surplus_window_blocks": surplus_window_blocks,
        "mining_in_window_blocks": mining_in_window,
        "window_utilization_pct": util_pct,
        "lost_surplus_kwh": round(lost_surplus_kwh, 2),
        "r5_hits": r5_hits,
        "r5_hit_rate_pct": r5_rate_pct,
        "total_blocks": n,
    }


# ---------------------------------------------------------------------------
# SQLite-Lesefunktionen (gleiche Logik wie scripts/ha_export_scenario.py)
# ---------------------------------------------------------------------------


def _detect_schema(conn: sqlite3.Connection) -> str:
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    return "new" if "states_meta" in tables else "old"


def _fetch_raw(
    conn: sqlite3.Connection,
    schema: str,
    entity_ids: list[str],
    start_ts: float,
    end_ts: float,
) -> dict[str, list[tuple[datetime, float]]]:
    results: dict[str, list[tuple[datetime, float]]] = {
        col: [] for col in _ENTITIES.values()
    }

    if schema == "new":
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

        params: list[Any] = list(meta.keys()) + [start_ts, end_ts]
        for mid, raw_state, ts_float in conn.execute(id_q, params):
            try:
                value = float(raw_state)
            except (ValueError, TypeError):
                continue
            entity_id = meta[mid]
            col = _ENTITIES.get(entity_id)
            if col:
                results[col].append(
                    (datetime.fromtimestamp(ts_float, tz=timezone.utc), value)
                )
    else:
        q = """
            SELECT entity_id, state, last_updated
            FROM states
            WHERE entity_id IN ({})
              AND last_updated >= ? AND last_updated < ?
              AND state NOT IN ('unknown', 'unavailable', '')
        """.format(",".join("?" * len(entity_ids)))

        start_str = datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        end_str = datetime.fromtimestamp(end_ts, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        for entity_id, raw_state, ts_str in conn.execute(
            q, entity_ids + [start_str, end_str]
        ):
            try:
                value = float(raw_state)
            except (ValueError, TypeError):
                continue
            col = _ENTITIES.get(entity_id)
            if col:
                dt = datetime.fromisoformat(ts_str.replace(" ", "T")).replace(
                    tzinfo=timezone.utc
                )
                results[col].append((dt, value))

    return results


def _floor_to_block(ts: datetime) -> datetime:
    return ts.replace(
        minute=(ts.minute // _BLOCK_MIN) * _BLOCK_MIN, second=0, microsecond=0
    )


def _resample(
    raw: dict[str, list[tuple[datetime, float]]],
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    blocks: list[datetime] = []
    t = _floor_to_block(start)
    while t < end:
        blocks.append(t)
        t += timedelta(minutes=_BLOCK_MIN)

    col_blocks: dict[str, dict[datetime, list[float]]] = {
        col: {b: [] for b in blocks} for col in raw
    }
    for col, readings in raw.items():
        for ts, val in readings:
            b = _floor_to_block(ts)
            if b in col_blocks[col]:
                col_blocks[col][b].append(val)

    col_series: dict[str, dict[datetime, float | None]] = {}
    for col, bdict in col_blocks.items():
        last: float | None = None
        series: dict[datetime, float | None] = {}
        for b in blocks:
            vals = bdict[b]
            if vals:
                last = sum(vals) / len(vals)
            series[b] = last
        col_series[col] = series

    return [
        {
            "block_ts": b,
            "timestamp_offset_min": i * _BLOCK_MIN,
            **{col: col_series[col][b] for col in col_series},
        }
        for i, b in enumerate(blocks)
    ]


# ---------------------------------------------------------------------------
# ScenarioBuilder
# ---------------------------------------------------------------------------


class ScenarioBuilder:
    def __init__(
        self,
        scenarios_dir: Path | None = None,
        library_path: Path | None = None,
    ) -> None:
        self._scenarios_dir = scenarios_dir or _DEFAULT_SCENARIOS_DIR
        self._library = library_path or (self._scenarios_dir / "library.json")
        self._scenarios_dir.mkdir(parents=True, exist_ok=True)

    def build(self, date: str, db_path: Path) -> Path:
        """Exportiert, klassifiziert und annotiert einen Tag. Gibt den CSV-Pfad zurück."""
        rows = self._export_day(date, db_path)
        if not rows:
            raise ValueError(f"Keine Daten für {date} in {db_path}")
        tags = classify(rows)
        meta = compute_meta(rows, date, tags)
        path = self._write_csv(rows, meta)
        self._update_library(meta, path)
        tag_str = ", ".join(tags)
        print(
            f"→ {date}: tags=[{tag_str}]"
            f"  pv_peak={meta['pv_peak_kw']:.1f}kW"
            f"  min_soc={meta['min_soc_pct']:.0f}%"
            f"  → {path.name}"
        )
        return path

    def build_range(self, start: str, end: str, db_path: Path) -> list[Path]:
        """Exportiert alle Tage im Bereich [start, end) in die Bibliothek."""
        d = datetime.strptime(start, "%Y-%m-%d")
        end_d = datetime.strptime(end, "%Y-%m-%d")
        paths: list[Path] = []
        while d < end_d:
            date_str = d.strftime("%Y-%m-%d")
            try:
                paths.append(self.build(date_str, db_path))
            except ValueError as exc:
                print(f"→ {date_str}: übersprungen ({exc})")
            d += timedelta(days=1)
        print(f"✓ {len(paths)} Szenarien aufgenommen")
        return paths

    def list_scenarios(self, tag: str | None = None) -> list[dict[str, Any]]:
        """Gibt alle Bibliothekseinträge zurück, optional nach Tag-Typ gefiltert."""
        entries = self._load_library()
        if tag:
            entries = [e for e in entries if tag in e.get("tags", [])]
        return entries

    def replay_tag(
        self,
        tag: str,
        surplus_min_kw: float = 1.5,
    ) -> list[dict[str, Any]]:
        """Führt replay_scenario für alle Szenarien eines Tags durch und berechnet KPIs."""
        entries = self.list_scenarios(tag)
        if not entries:
            print(f"Keine Szenarien mit Tag '{tag}' in der Bibliothek.")
            return []
        results: list[dict[str, Any]] = []
        for entry in entries:
            path = self._scenarios_dir / entry["file"]
            if not path.exists():
                print(f"  ⚠ Datei nicht gefunden: {path}")
                continue
            rows = load_csv_scenario(path)
            replay_results = replay_scenario(path)

            # Tatsächliche Miner-Uptime: START=läuft, STOP=aus, NOOP=hält vorherigen Zustand
            miner_running = False
            running_blocks = 0
            for r in replay_results:
                if r["action"] == "START":
                    miner_running = True
                elif r["action"] == "STOP":
                    miner_running = False
                if miner_running:
                    running_blocks += 1
            uptime_h = round(running_blocks * _BLOCK_MIN / 60, 1)

            kpis = compute_kpis(rows, replay_results, surplus_min_kw=surplus_min_kw)

            result: dict[str, Any] = {
                "date": entry["date"],
                "tags": entry["tags"],
                "blocks": len(replay_results),
                "replay_uptime_h": uptime_h,
                **kpis,
            }
            results.append(result)
            print(
                f"  {entry['date']}:"
                f"  Uptime={uptime_h:.1f}h"
                f"  Fenster-Ausnutzung={kpis['window_utilization_pct']:.1f}%"
                f"  Verlust={kpis['lost_surplus_kwh']:.2f}kWh"
                f"  R5={kpis['r5_hit_rate_pct']:.1f}%"
            )
        return results

    # ------------------------------------------------------------------

    def _export_day(self, date: str, db_path: Path) -> list[dict[str, Any]]:
        start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        conn = sqlite3.connect(db_path)
        try:
            schema = _detect_schema(conn)
            raw = _fetch_raw(
                conn, schema, list(_ENTITIES.keys()), start.timestamp(), end.timestamp()
            )
        finally:
            conn.close()
        return _resample(raw, start, end)

    def _write_csv(self, rows: list[dict[str, Any]], meta: dict[str, Any]) -> Path:
        date = meta["date"]
        path = self._scenarios_dir / f"real_{date}.csv"
        lines: list[str] = [
            "# scenario_builder: 1.0",
            f"# date: {date}",
            f"# tags: {' '.join(meta['tags'])}",
            f"# pv_peak_kw: {meta['pv_peak_kw']:.2f}",
            f"# pv_energy_kwh: {meta['pv_energy_kwh']:.2f}",
            f"# min_soc_pct: {meta['min_soc_pct']:.1f}",
            f"# grid_import_kwh: {meta['grid_import_kwh']:.2f}",
            f"# grid_export_kwh: {meta['grid_export_kwh']:.2f}",
            f"# max_miner_temp_c: {meta['max_miner_temp_c']:.1f}",
            f"# blocks_total: {meta['blocks_total']}",
            f"# blocks_filled: {meta['blocks_filled']}",
            "# " + ", ".join(_CSV_COLUMNS),
        ]
        for row in rows:
            out: dict[str, str] = {col: "" for col in _CSV_COLUMNS}
            out["timestamp_offset_min"] = str(row["timestamp_offset_min"])
            for col in _CSV_COLUMNS[1:]:
                val = row.get(col)
                if val is not None:
                    out[col] = f"{val:.2f}"
            if not out["miner_heartbeat_age_sec"]:
                out["miner_heartbeat_age_sec"] = (
                    "5.0" if row.get("miner_temp_c") is not None else ""
                )
            lines.append(",".join(out[col] for col in _CSV_COLUMNS))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _update_library(self, meta: dict[str, Any], path: Path) -> None:
        entries = self._load_library()
        entries = [e for e in entries if e["date"] != meta["date"]]
        entries.append(
            {
                "date": meta["date"],
                "file": path.name,
                "tags": meta["tags"],
                "pv_peak_kw": meta["pv_peak_kw"],
                "pv_energy_kwh": meta["pv_energy_kwh"],
                "min_soc_pct": meta["min_soc_pct"],
                "grid_import_kwh": meta["grid_import_kwh"],
                "grid_export_kwh": meta["grid_export_kwh"],
                "max_miner_temp_c": meta["max_miner_temp_c"],
                "blocks_total": meta["blocks_total"],
                "blocks_filled": meta["blocks_filled"],
            }
        )
        entries.sort(key=lambda e: e["date"])
        self._library.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _load_library(self) -> list[dict[str, Any]]:
        if not self._library.exists():
            return []
        try:
            data = json.loads(self._library.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="BitGridAI Szenario-Builder")
    sub = parser.add_subparsers(dest="cmd")

    build_p = sub.add_parser("build", help="Tag(e) in Bibliothek aufnehmen")
    build_p.add_argument("--db", required=True, help="Pfad zur home-assistant_v2.db")
    build_p.add_argument("--date", help="Einzelner Tag YYYY-MM-DD")
    build_p.add_argument("--start", help="Startdatum YYYY-MM-DD (Bereich)")
    build_p.add_argument("--end", help="Enddatum YYYY-MM-DD (exklusiv)")
    build_p.add_argument(
        "--out", help="Ausgabeverzeichnis (default: src/sim/scenarios)"
    )

    list_p = sub.add_parser("list", help="Bibliothek anzeigen")
    list_p.add_argument("--tag", help="Nach Tag-Typ filtern")
    list_p.add_argument("--lib", help="Pfad zu library.json")

    replay_p = sub.add_parser(
        "replay", help="Alle Szenarien eines Tags replayer + KPIs berechnen"
    )
    replay_p.add_argument("--tag", required=True, help="Tag-Typ (z.B. sunny_high)")
    replay_p.add_argument("--lib", help="Pfad zu library.json")
    replay_p.add_argument(
        "--surplus-min-kw",
        type=float,
        default=1.5,
        help="R1-Schwelle für Überschuss-Fenster (default: 1.5)",
    )
    replay_p.add_argument("--csv", help="KPI-Ergebnisse als CSV speichern (Pfad)")

    args = parser.parse_args()

    if args.cmd == "build":
        db = Path(args.db)
        if not db.exists():
            parser.error(f"DB nicht gefunden: {db}")
        out = Path(args.out) if args.out else None
        builder = ScenarioBuilder(scenarios_dir=out)
        if args.date:
            builder.build(args.date, db)
        elif args.start and args.end:
            builder.build_range(args.start, args.end, db)
        else:
            parser.error("--date oder --start + --end angeben")

    elif args.cmd == "list":
        lib = Path(args.lib) if args.lib else None
        builder = ScenarioBuilder(library_path=lib)
        entries = builder.list_scenarios(tag=args.tag)
        if not entries:
            print("Keine Szenarien in der Bibliothek.")
            return
        for e in entries:
            tags = ", ".join(e.get("tags", []))
            print(
                f"  {e['date']:12s}  [{tags:<30s}]"
                f"  PV={e.get('pv_peak_kw', 0):.1f}kW"
                f"  SoC_min={e.get('min_soc_pct', 0):.0f}%"
                f"  Import={e.get('grid_import_kwh', 0):.1f}kWh"
            )

    elif args.cmd == "replay":
        import csv as csv_mod

        lib = Path(args.lib) if args.lib else None
        builder = ScenarioBuilder(library_path=lib)
        results = builder.replay_tag(args.tag, surplus_min_kw=args.surplus_min_kw)

        if not results:
            return

        print(
            f"\n{'Datum':12s}  {'Uptime':>8s}  {'Fenster%':>9s}  "
            f"{'Verlust kWh':>11s}  {'R5%':>6s}  {'FensterBlk':>10s}"
        )
        print("-" * 68)
        for r in results:
            print(
                f"  {r['date']:10s}  {r['replay_uptime_h']:>7.1f}h"
                f"  {r['window_utilization_pct']:>8.1f}%"
                f"  {r['lost_surplus_kwh']:>10.2f}"
                f"  {r['r5_hit_rate_pct']:>5.1f}%"
                f"  {r['surplus_window_blocks']:>10d}"
            )

        n = len(results)
        avg_util = sum(r["window_utilization_pct"] for r in results) / n
        avg_loss = sum(r["lost_surplus_kwh"] for r in results) / n
        avg_r5 = sum(r["r5_hit_rate_pct"] for r in results) / n
        avg_uptime = sum(r["replay_uptime_h"] for r in results) / n
        print("-" * 68)
        print(
            f"  {'∅ ' + str(n) + ' Tage':10s}  {avg_uptime:>7.1f}h"
            f"  {avg_util:>8.1f}%"
            f"  {avg_loss:>10.2f}"
            f"  {avg_r5:>5.1f}%"
        )

        if args.csv:
            csv_path = Path(args.csv)
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            fieldnames = [
                "date",
                "tags",
                "replay_uptime_h",
                "window_utilization_pct",
                "surplus_window_blocks",
                "mining_in_window_blocks",
                "lost_surplus_kwh",
                "r5_hit_rate_pct",
                "r5_hits",
                "total_blocks",
            ]
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv_mod.DictWriter(
                    f, fieldnames=fieldnames, extrasaction="ignore"
                )
                writer.writeheader()
                for r in results:
                    row = {**r, "tags": "|".join(r.get("tags", []))}
                    writer.writerow(row)
            print(f"\n→ KPI-CSV: {csv_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
