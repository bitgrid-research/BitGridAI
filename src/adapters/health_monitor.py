"""
HealthMonitor — überwacht Verbindungs-Health und Timeout-Detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

log = logging.getLogger(__name__)

ConnState = Literal["connected", "disconnected", "unknown"]


@dataclass
class AdapterHealth:
    adapter: str
    status: Literal["ok", "warn", "error"]
    last_seen: datetime
    conn_state: ConnState = "unknown"
    missing_signals: list[str] = field(default_factory=list)
    error_message: str | None = None


class HealthMonitor:
    """Meldet Adapter-Health basierend auf Stale-Detection und ConnState."""

    def __init__(
        self, stale_warn_sec: float = 30.0, stale_error_sec: float = 60.0
    ) -> None:
        self._stale_warn = stale_warn_sec
        self._stale_error = stale_error_sec
        self._last_seen: dict[str, datetime] = {}
        self._conn_state: dict[str, ConnState] = {}
        self._disconnect_reason: dict[str, str | None] = {}

    def heartbeat(self, adapter: str) -> None:
        self._last_seen[adapter] = datetime.now(tz=timezone.utc)

    def report_connected(self, adapter: str) -> None:
        self._conn_state[adapter] = "connected"
        self._disconnect_reason.pop(adapter, None)
        self.heartbeat(adapter)
        log.debug("Adapter %s verbunden", adapter)

    def report_disconnected(self, adapter: str, reason: str | None = None) -> None:
        self._conn_state[adapter] = "disconnected"
        self._disconnect_reason[adapter] = reason
        log.warning("Adapter %s getrennt: %s", adapter, reason or "unbekannt")

    def get(self, adapter: str) -> AdapterHealth:
        now = datetime.now(tz=timezone.utc)
        last = self._last_seen.get(adapter)
        conn_state: ConnState = self._conn_state.get(adapter, "unknown")

        if last is None:
            return AdapterHealth(
                adapter=adapter,
                status="error",
                last_seen=now,
                conn_state=conn_state,
                error_message=self._disconnect_reason.get(adapter)
                or "Noch kein Heartbeat empfangen",
            )

        age = (now - last).total_seconds()
        if conn_state == "disconnected" or age > self._stale_error:
            status: Literal["ok", "warn", "error"] = "error"
        elif age > self._stale_warn:
            status = "warn"
        else:
            status = "ok"

        return AdapterHealth(
            adapter=adapter,
            status=status,
            last_seen=last,
            conn_state=conn_state,
            error_message=(
                self._disconnect_reason.get(adapter)
                if conn_state == "disconnected"
                else None
            ),
        )

    def all_adapters(self) -> list[AdapterHealth]:
        """Gibt Health für alle bekannten Adapter zurück."""
        known = set(self._last_seen) | set(self._conn_state)
        return [self.get(a) for a in sorted(known)]
