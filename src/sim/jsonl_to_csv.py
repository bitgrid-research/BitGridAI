"""
jsonl_to_csv — konvertiert aufgezeichnete MQTT-Snapshots in Szenario-CSV.

Eingabe:  JSONL-Datei vom mqtt_recorder.py (Topic: bitgrid/rec/snapshot)
Ausgabe:  CSV im scenario_loader-Format für src/sim/runner.py und replay.py

CSV-Format (scenario_loader.py):
  timestamp_offset_min, pv_power_w, house_load_w, grid_import_w,
  battery_soc_pct, miner_temp_c, miner_heartbeat_age_sec,
  [energy_price_ct_kwh], [pv_forecast_kw]

Verwendung:
  python -m src.sim.jsonl_to_csv recordings/2024-01-15.jsonl
  python -m src.sim.jsonl_to_csv recordings/2024-01-15.jsonl --out scenarios/real_2024-01-15.csv
  python -m src.sim.jsonl_to_csv recordings/2024-01-15.jsonl --from 06:00 --to 20:00
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_SNAPSHOT_TOPIC = "bitgrid/rec/snapshot"
_HB_OK_SEC = 5.0
_HB_FAIL_SEC = 120.0


def convert(
    jsonl_path: str | Path,
    out_path: str | Path | None = None,
    time_from: str | None = None,
    time_to: str | None = None,
) -> list[str]:
    """
    Liest JSONL, filtert Snapshot-Topic, gibt CSV-Zeilen zurück.

    time_from / time_to: "HH:MM" — schneidet Nacht-Stunden heraus.
    """
    records = _load_snapshots(Path(jsonl_path))

    if not records:
        print(f"Keine '{_SNAPSHOT_TOPIC}'-Einträge in {jsonl_path}", file=sys.stderr)
        return []

    records.sort(key=lambda r: r["ts"])

    if time_from or time_to:
        records = _filter_timewindow(records, time_from, time_to)

    if not records:
        print("Nach Zeitfilter keine Einträge übrig.", file=sys.stderr)
        return []

    base_ts = records[0]["ts"]
    lines = _build_csv_lines(records, base_ts)

    if out_path:
        _write(lines, Path(out_path), jsonl_path)
    else:
        default_out = Path(jsonl_path).with_suffix(".csv")
        _write(lines, default_out, jsonl_path)

    return lines


# ---------------------------------------------------------------------------
# Interne Helfer
# ---------------------------------------------------------------------------


def _load_snapshots(path: Path) -> list[dict[str, Any]]:
    records = []
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(f"Zeile {lineno}: JSON-Fehler — {exc}", file=sys.stderr)
                continue

            if entry.get("topic") != _SNAPSHOT_TOPIC:
                continue

            try:
                payload = json.loads(entry["payload"])
            except (json.JSONDecodeError, KeyError) as exc:
                print(f"Zeile {lineno}: Payload-Fehler — {exc}", file=sys.stderr)
                continue

            ts_raw = payload.get("ts") or entry.get("ts", "")
            try:
                ts = datetime.fromisoformat(ts_raw)
            except ValueError:
                print(f"Zeile {lineno}: ungültiger Timestamp '{ts_raw}'", file=sys.stderr)
                continue

            records.append({
                "ts": ts,
                "pv_w":     float(payload.get("pv_w", 0)),
                "load_w":   float(payload.get("load_w", 0)),
                "grid_w":   float(payload.get("grid_w", 0)),
                "soc":      float(payload.get("soc", 0)),
                "temp_c":   float(payload.get("temp_c", 0)),
                "hb_ok":    str(payload.get("hb_ok", "true")).lower() == "true",
                "miner_w":  float(payload.get("miner_w", 0)),
            })

    return records


def _filter_timewindow(
    records: list[dict[str, Any]],
    time_from: str | None,
    time_to: str | None,
) -> list[dict[str, Any]]:
    def _hhmm(s: str) -> tuple[int, int]:
        h, m = s.split(":")
        return int(h), int(m)

    from_hm = _hhmm(time_from) if time_from else (0, 0)
    to_hm   = _hhmm(time_to)   if time_to   else (23, 59)

    def _in_window(ts: datetime) -> bool:
        t = (ts.hour, ts.minute)
        return from_hm <= t <= to_hm

    return [r for r in records if _in_window(r["ts"])]


def _build_csv_lines(records: list[dict[str, Any]], base_ts: datetime) -> list[str]:
    lines = [
        "# BitGridAI Scenario — recorded from real data",
        f"# recorded_from: {base_ts.strftime('%Y-%m-%dT%H:%M:%S')}",
        f"# blocks: {len(records)}",
        "# offset_min,pv_w,load_w,grid_w,soc,temp_c,hb_age_sec",
    ]

    for rec in records:
        offset_min = int((rec["ts"] - base_ts).total_seconds() / 60)
        hb_age = _HB_OK_SEC if rec["hb_ok"] else _HB_FAIL_SEC
        lines.append(
            f"{offset_min},"
            f"{rec['pv_w']:.1f},"
            f"{rec['load_w']:.1f},"
            f"{rec['grid_w']:.1f},"
            f"{rec['soc']:.1f},"
            f"{rec['temp_c']:.1f},"
            f"{hb_age:.1f}"
        )

    return lines


def _write(lines: list[str], path: Path, source: str | Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: {len(lines) - 4} Bloecke -> {path}  (Quelle: {source})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Konvertiert MQTT-Aufnahmen in Szenario-CSV für den SimRunner."
    )
    parser.add_argument("input", help="JSONL-Datei vom mqtt_recorder.py")
    parser.add_argument("--out", help="Ausgabe-CSV (default: <input>.csv)")
    parser.add_argument("--from", dest="time_from", metavar="HH:MM",
                        help="Nur Einträge ab dieser Uhrzeit (z.B. 06:00)")
    parser.add_argument("--to",   dest="time_to",   metavar="HH:MM",
                        help="Nur Einträge bis zu dieser Uhrzeit (z.B. 20:00)")
    args = parser.parse_args()

    convert(
        jsonl_path=args.input,
        out_path=args.out,
        time_from=args.time_from,
        time_to=args.time_to,
    )


if __name__ == "__main__":
    main()
