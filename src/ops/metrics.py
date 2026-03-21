"""
Metriken — KPI-Berechnung pro Block.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class BlockMetrics:
    block_id: str
    timestamp: datetime
    decision_latency_ms: float | None = None
    explanation_latency_ms: float | None = None
    thermal_incidents: int = 0
    flapping_rate: float = 0.0
    grid_import_wh: float = 0.0
    explainability_coverage: float = 100.0


class MetricsCollector:
    """Sammelt Metriken pro Block und gibt BlockMetrics zurück."""

    def __init__(self) -> None:
        self._current: BlockMetrics | None = None

    def start_block(self, block_id: str) -> None:
        self._current = BlockMetrics(
            block_id=block_id,
            timestamp=datetime.now(tz=timezone.utc),
        )

    def record_decision_latency(self, ms: float) -> None:
        if self._current:
            self._current.decision_latency_ms = ms

    def record_thermal_incident(self) -> None:
        if self._current:
            self._current.thermal_incidents += 1

    def record_grid_import(self, wh: float) -> None:
        if self._current:
            self._current.grid_import_wh += wh

    def get(self) -> BlockMetrics | None:
        return self._current
