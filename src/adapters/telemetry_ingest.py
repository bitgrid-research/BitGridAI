"""
TelemetryIngest — normalisiert eingehende Messwerte zu EnergyState-Feldern.

Einheiten-Konversion passiert hier — der Core sieht nur SI-Einheiten.
Signal-Namen werden ausschließlich als src.core.signals.Signal übergeben.
Da Signal(str, Enum), ist volle Kompatibilität mit str-basierten dict-Keys gewährleistet.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from src.core.signals import Signal

log = logging.getLogger(__name__)


@dataclass
class TelemetryFrame:
    signal: Signal
    value: float
    timestamp: datetime
    source: str
    quality: Literal["ok", "stale", "error"]


class TelemetryIngest:
    """Empfängt Rohdaten und hält den aktuellen Messwert-Cache."""

    def __init__(self, stale_threshold_sec: float = 60.0) -> None:
        self._cache: dict[Signal, TelemetryFrame] = {}
        self._stale_threshold_sec = stale_threshold_sec

    def update(self, signal: Signal, value: float, source: str = "") -> None:
        """Speichert einen neuen Messwert im Cache."""
        self._cache[signal] = TelemetryFrame(
            signal=signal,
            value=value,
            timestamp=datetime.now(tz=timezone.utc),
            source=source,
            quality="ok",
        )

    def get(self, signal: Signal) -> TelemetryFrame | None:
        """Gibt den aktuellen Messwert zurück, markiert stale wenn veraltet."""
        frame = self._cache.get(signal)
        if frame is None:
            return None
        age = (datetime.now(tz=timezone.utc) - frame.timestamp).total_seconds()
        if age > self._stale_threshold_sec:
            return TelemetryFrame(
                signal=frame.signal,
                value=frame.value,
                timestamp=frame.timestamp,
                source=frame.source,
                quality="stale",
            )
        return frame

    def get_value(self, signal: Signal) -> float | None:
        frame = self.get(signal)
        if frame is None or frame.quality == "stale":
            return None
        return frame.value

    def all_signals(self) -> dict[Signal, float | None]:
        return {sig: self.get_value(sig) for sig in self._cache}
