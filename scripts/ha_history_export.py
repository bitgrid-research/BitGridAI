#!/usr/bin/env python3
"""
Exportiert HA-History via REST-API als Szenario-CSV (kein DB-Zugriff/scp nötig).

Erzeugt dasselbe 12-Spalten-Format wie ``ha_export_scenario.py`` — pro Tag eine
CSV ``real_<date>.csv`` in ``src/sim/scenarios/`` —, damit ``augment``,
``scenario_miner`` und ``replay`` unverändert darauf laufen.

Quelle: HA History-API über VPN. Token aus --token / $BITGRIDAI_HA_TOKEN / .env.

  python scripts/ha_history_export.py --days 6
  python scripts/ha_history_export.py --start 2026-05-28 --end 2026-06-03
"""

from __future__ import annotations

import argparse
import sys
import urllib.parse
import urllib.request
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# HA-Entity-ID → CSV-Spalte (normalisierte BitGrid-Template-Sensoren)
ENTITIES: dict[str, str] = {
    "sensor.pv_power_w": "pv_power_w",
    "sensor.house_load_w": "house_load_w",
    "sensor.grid_import_w": "grid_import_w",
    "sensor.battery_soc_pct": "battery_soc_pct",
    "sensor.miner_max_chip_temp_c": "miner_temp_c",
    "sensor.miner_total_power_w": "miner_power_w",
    "sensor.grid_export_w": "grid_export_w",
    "sensor.ac_elwa_2_power1_solar": "heizstab_power_w",
}

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

BLOCK_MIN = 10


def _token(cli: str | None) -> str:
    if cli:
        return cli
    env = os.environ.get("BITGRIDAI_HA_TOKEN") or os.environ.get("HA_TOKEN")
    if env:
        return env
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            for key in ("BITGRIDAI_HA_TOKEN", "HA_TOKEN"):
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("Kein Token: --token oder BITGRIDAI_HA_TOKEN/.env setzen")


def _fetch(base: str, token: str, entity: str, start: datetime, end: datetime) -> list[tuple[datetime, float]]:
    """Holt (timestamp, value)-Punkte einer Entity im Fenster [start, end)."""
    path = urllib.parse.quote(start.isoformat())
    q = urllib.parse.urlencode(
        {"end_time": end.isoformat(), "filter_entity_id": entity, "minimal_response": ""}
    )
    url = f"{base}/api/history/period/{path}?{q}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    series = data[0] if data else []
    out: list[tuple[datetime, float]] = []
    for p in series:
        state = p.get("state")
        if state in (None, "unknown", "unavailable", ""):
            continue
        try:
            val = float(state)
        except (TypeError, ValueError):
            continue
        ts = p.get("last_changed") or p.get("last_updated")
        if not ts:
            continue
        out.append((datetime.fromisoformat(ts), val))
    return out


def _floor(ts: datetime) -> datetime:
    return ts.replace(minute=(ts.minute // BLOCK_MIN) * BLOCK_MIN, second=0, microsecond=0)


def _resample_day(
    raw: dict[str, list[tuple[datetime, float]]], day_start: datetime
) -> list[dict[str, Any]]:
    """Mittelt auf 10-Min-Blöcke eines Tages, Forward-Fill innerhalb des Tages."""
    blocks = [day_start + timedelta(minutes=i * BLOCK_MIN) for i in range(144)]
    rows: list[dict[str, Any]] = []
    # pro Spalte: Block → Werte
    per_col: dict[str, dict[datetime, list[float]]] = {
        col: {b: [] for b in blocks} for col in ENTITIES.values()
    }
    for col, pts in raw.items():
        for ts, val in pts:
            b = _floor(ts)
            if b in per_col[col]:
                per_col[col][b].append(val)
    series: dict[str, dict[datetime, float | None]] = {}
    for col, bd in per_col.items():
        last: float | None = None
        s: dict[datetime, float | None] = {}
        for b in blocks:
            if bd[b]:
                last = sum(bd[b]) / len(bd[b])
            s[b] = last
        series[col] = s
    for i, b in enumerate(blocks):
        row: dict[str, Any] = {"timestamp_offset_min": i * BLOCK_MIN}
        for col in ENTITIES.values():
            row[col] = series[col][b]
        rows.append(row)
    return rows


def _write(rows: list[dict[str, Any]], out: Path, date: str) -> int:
    filled = sum(
        1 for r in rows if r.get("pv_power_w") is not None and r.get("battery_soc_pct") is not None
    )
    lines = [
        "# ha_history_export (REST-API)",
        f"# date: {date}",
        f"# blocks_total: {len(rows)}  blocks_filled: {filled}",
        "# " + ", ".join(CSV_COLUMNS),
    ]
    for r in rows:
        cells = []
        for col in CSV_COLUMNS:
            if col == "timestamp_offset_min":
                cells.append(str(r[col]))
            elif col == "miner_heartbeat_age_sec":
                cells.append("5.0" if r.get("miner_temp_c") is not None else "")
            else:
                v = r.get(col)
                cells.append(f"{v:.2f}" if isinstance(v, (int, float)) else "")
        lines.append(",".join(cells))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return filled


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="HA-History via API → Szenario-CSVs (pro Tag)")
    p.add_argument("--host", default="http://192.168.178.62:8123")
    p.add_argument("--token", default=None)
    p.add_argument("--days", type=int, help="Letzte N volle Tage (UTC)")
    p.add_argument("--start", help="Startdatum YYYY-MM-DD (UTC)")
    p.add_argument("--end", help="Enddatum YYYY-MM-DD (exklusiv)")
    p.add_argument("--out-dir", default="src/sim/scenarios")
    args = p.parse_args()

    token = _token(args.token)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    if args.days:
        start = today - timedelta(days=args.days)
        end = today
    elif args.start:
        start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = (
            datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if args.end
            else start + timedelta(days=1)
        )
    else:
        p.error("--days oder --start angeben")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"→ Host: {args.host}   Zeitraum: {start.date()} – {(end - timedelta(days=1)).date()}")

    day = start
    while day < end:
        nxt = day + timedelta(days=1)
        raw = {
            col: _fetch(args.host, token, ent, day, nxt) for ent, col in ENTITIES.items()
        }
        rows = _resample_day(raw, day)
        date_str = day.strftime("%Y-%m-%d")
        out_path = out_dir / f"real_{date_str}.csv"
        filled = _write(rows, out_path, date_str)
        pts = sum(len(v) for v in raw.values())
        print(f"  ✓ {date_str}: {filled}/144 Blöcke befüllt ({pts} Rohpunkte) → {out_path.name}")
        day = nxt


if __name__ == "__main__":
    main()
