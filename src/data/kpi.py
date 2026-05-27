"""
KPI — berechnet und speichert KPIs pro Block.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


def write_kpi(
    conn: sqlite3.Connection,
    block_id: str,
    decision_latency_ms: float | None = None,
    explanation_latency_ms: float | None = None,
    thermal_incidents: int = 0,
    flapping_rate: float = 0.0,
    grid_import_wh: float = 0.0,
    explainability_coverage: float = 100.0,
    self_consumption_wh: float = 0.0,
    battery_soc_pct: float | None = None,
    miner_runtime_blocks: int = 0,
    override_active: int = 0,
) -> None:
    conn.execute(
        """
        INSERT INTO kpi_log
        (block_id, timestamp, decision_latency_ms, explanation_latency_ms,
         thermal_incidents, flapping_rate, grid_import_wh, explainability_coverage,
         self_consumption_wh, battery_soc_pct, miner_runtime_blocks, override_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            block_id,
            datetime.now(tz=timezone.utc).isoformat(),
            decision_latency_ms,
            explanation_latency_ms,
            thermal_incidents,
            flapping_rate,
            grid_import_wh,
            explainability_coverage,
            self_consumption_wh,
            battery_soc_pct,
            miner_runtime_blocks,
            override_active,
        ),
    )
    conn.commit()
