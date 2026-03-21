"""
HealthCheck — aggregiert Komponenten-Health und gibt SystemHealth zurück.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from src.ops.events import ComponentHealth, SystemHealth


class HealthCheck:
    """Aggregiert Health-Status aller Systemkomponenten."""

    def __init__(self, config_version: str = "") -> None:
        self._components: dict[str, ComponentHealth] = {}
        self._config_version = config_version

    def report(
        self,
        component: str,
        status: Literal["ok", "warn", "error"],
        message: str | None = None,
    ) -> None:
        """Meldet den Status einer Komponente."""
        now = datetime.now(tz=timezone.utc)
        self._components[component] = ComponentHealth(
            component=component,
            status=status,
            message=message,
            last_ok=now if status == "ok" else self._components.get(component, ComponentHealth(component, "error")).last_ok,
        )

    def get(self) -> SystemHealth:
        """Gibt aggregierten SystemHealth zurück."""
        health = SystemHealth(
            status="ok",
            components=dict(self._components),
            config_version=self._config_version,
        )
        health.aggregate()
        return health
