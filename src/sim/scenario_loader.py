"""
ScenarioLoader — liest CSV-Szenarien und JSON-Fixtures ein.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

from src.core.models import EnergyState


def load_csv_scenario(path: str | Path) -> list[dict[str, Any]]:
    """
    Liest ein CSV-Szenario und gibt eine Liste von Row-Dicts zurück.

    Leerzeilen und #-Kommentare werden ignoriert.
    """
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            rows.append(
                {
                    "timestamp_offset_min": int(parts[0]),
                    "pv_power_w": float(parts[1]),
                    "house_load_w": float(parts[2]),
                    "grid_import_w": float(parts[3]),
                    "battery_soc_pct": float(parts[4]),
                    "miner_temp_c": float(parts[5]),
                    "miner_heartbeat_age_sec": float(parts[6]),
                    "energy_price_ct_kwh": (
                        float(parts[7]) if len(parts) > 7 and parts[7] else None
                    ),
                    "pv_forecast_kw": (
                        float(parts[8]) if len(parts) > 8 and parts[8] else None
                    ),
                }
            )
    return rows


def rows_to_energy_states(
    rows: list[dict[str, Any]],
    base_time: datetime | None = None,
) -> list[EnergyState]:
    """Konvertiert CSV-Rows in EnergyState-Objekte."""
    if base_time is None:
        base_time = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)

    states = []
    for row in rows:
        offset = timedelta(minutes=row["timestamp_offset_min"])
        window_start = base_time + offset
        window_end = window_start + timedelta(minutes=10)
        block_id = window_start.strftime("%Y-%m-%dT%H:%M:%S")

        pv = row["pv_power_w"]
        load = row["house_load_w"]
        surplus_kw = (pv - load) / 1000.0

        states.append(
            EnergyState(
                block_id=block_id,
                window_start=window_start,
                window_end=window_end,
                pv_power_w=pv,
                house_load_w=load,
                grid_import_w=row["grid_import_w"],
                battery_soc_pct=row["battery_soc_pct"],
                miner_temp_c=row["miner_temp_c"],
                miner_heartbeat_age_sec=row["miner_heartbeat_age_sec"],
                surplus_kw=surplus_kw,
                quality="ok",
                missing_signals=(),
                energy_price_ct_kwh=row.get("energy_price_ct_kwh"),
                pv_forecast_kw=row.get("pv_forecast_kw"),
            )
        )
    return states


def load_fixture(path: str | Path) -> dict[str, Any]:
    """Liest ein JSON-Fixture und gibt das Dict zurück."""
    with open(path, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))
