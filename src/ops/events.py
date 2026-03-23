"""
Health- und System-Event-Typen für ops/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


@dataclass
class ComponentHealth:
    component: str  # "core" | "mqtt" | "db" | "config"
    status: Literal["ok", "warn", "error"]
    message: str | None = None
    last_ok: datetime | None = None


@dataclass
class SystemHealth:
    status: Literal["ok", "warn", "error"]
    components: dict[str, ComponentHealth] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    config_version: str = ""

    def aggregate(self) -> None:
        """Berechnet Gesamt-Status aus Komponenten-Status."""
        statuses = [c.status for c in self.components.values()]
        if "error" in statuses:
            self.status = "error"
        elif "warn" in statuses:
            self.status = "warn"
        else:
            self.status = "ok"
