"""
StateStore — persistiert EnergyState-Snapshots für Replay.

Replay-Safe: gibt exakt dieselben Werte zurück, die beim Schreiben übergeben wurden.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from src.core.models import EnergyState


class StateStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def write(self, state: EnergyState) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO energy_states
            (block_id, window_start, window_end, pv_power_w, house_load_w,
             grid_import_w, battery_soc_pct, miner_temp_c, miner_heartbeat_age_sec,
             surplus_kw, quality, missing_signals_json,
             grid_export_w, energy_price_ct_kwh, pv_forecast_kw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state.block_id,
                state.window_start.isoformat(),
                state.window_end.isoformat(),
                state.pv_power_w,
                state.house_load_w,
                state.grid_import_w,
                state.battery_soc_pct,
                state.miner_temp_c,
                state.miner_heartbeat_age_sec,
                state.surplus_kw,
                state.quality,
                json.dumps(list(state.missing_signals)),
                state.grid_export_w,
                state.energy_price_ct_kwh,
                state.pv_forecast_kw,
            ),
        )
        self._conn.commit()

    def read(self, block_id: str) -> EnergyState | None:
        cur = self._conn.execute(
            "SELECT * FROM energy_states WHERE block_id = ?", (block_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return self._row_to_state(dict(zip([d[0] for d in cur.description], row)))

    def read_range(self, start: datetime, end: datetime) -> list[EnergyState]:
        cur = self._conn.execute(
            "SELECT * FROM energy_states WHERE window_start BETWEEN ? AND ? ORDER BY window_start",
            (start.isoformat(), end.isoformat()),
        )
        cols = [d[0] for d in cur.description]
        return [self._row_to_state(dict(zip(cols, row))) for row in cur.fetchall()]

    def _row_to_state(self, row: dict[str, Any]) -> EnergyState:
        return EnergyState(
            block_id=row["block_id"],
            window_start=datetime.fromisoformat(row["window_start"]),
            window_end=datetime.fromisoformat(row["window_end"]),
            pv_power_w=row["pv_power_w"],
            house_load_w=row["house_load_w"],
            grid_import_w=row["grid_import_w"],
            battery_soc_pct=row["battery_soc_pct"],
            miner_temp_c=row["miner_temp_c"],
            miner_heartbeat_age_sec=row["miner_heartbeat_age_sec"],
            surplus_kw=row["surplus_kw"],
            quality=row["quality"],
            missing_signals=tuple(json.loads(row["missing_signals_json"] or "[]")),
            grid_export_w=row.get("grid_export_w"),
            energy_price_ct_kwh=row.get("energy_price_ct_kwh"),
            pv_forecast_kw=row.get("pv_forecast_kw"),
        )
