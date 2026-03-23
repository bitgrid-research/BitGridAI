"""
HealthMonitor — überwacht Verbindungs-Health und Timeout-Detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

log = logging.getLogger(__name__)


@dataclass
class AdapterHealth:
    adapter: str
    status: Literal["ok", "warn", "error"]
    last_seen: datetime
    missing_signals: list[str] = field(default_factory=list)
    error_message: str | None = None


class HealthMonitor:
    """Meldet Adapter-Health basierend auf Stale-Detection."""

    def __init__(
        self, stale_warn_sec: float = 30.0, stale_error_sec: float = 60.0
    ) -> None:
        self._stale_warn = stale_warn_sec
        self._stale_error = stale_error_sec
        self._last_seen: dict[str, datetime] = {}

    def heartbeat(self, adapter: str) -> None:
        self._last_seen[adapter] = datetime.now(tz=timezone.utc)

    def get(self, adapter: str) -> AdapterHealth:
        now = datetime.now(tz=timezone.utc)
        last = self._last_seen.get(adapter)

        if last is None:
            return AdapterHealth(
                adapter=adapter,
                status="error",
                last_seen=now,
                error_message="Noch kein Heartbeat empfangen",
            )

        age = (now - last).total_seconds()
        if age > self._stale_error:
            status: Literal["ok", "warn", "error"] = "error"
        elif age > self._stale_warn:
            status = "warn"
        else:
            status = "ok"

        return AdapterHealth(adapter=adapter, status=status, last_seen=last)
