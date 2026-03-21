"""
OverrideHandler — manuelle Eingriffe mit TTL und Autonomie-Stufen.

R3-Safety-Entscheidungen können NIEMALS durch einen Override aufgehoben werden.
allow_unsafe_override ist hardcoded False.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal


AutonomyLevel = Literal["FULL", "SEMI", "MANUAL"]


@dataclass
class ActiveOverride:
    action: Literal["START", "STOP", "NOOP"]
    valid_until: datetime
    command_id: str
    requested_by: str = "operator"


class OverrideHandler:
    """Verwaltet aktive Overrides mit TTL."""

    # Maximale Override-Dauer (Sicherheitslimit)
    MAX_OVERRIDE_DURATION_MIN: int = 120

    def __init__(self) -> None:
        self._active: ActiveOverride | None = None
        self.autonomy_level: AutonomyLevel = "FULL"

    def request(
        self,
        action: Literal["START", "STOP", "NOOP"],
        duration_min: int,
        command_id: str,
        now: datetime | None = None,
    ) -> tuple[bool, str]:
        """
        Versucht einen Override zu setzen.

        Returns (accepted, message).
        """
        if now is None:
            now = datetime.now(tz=timezone.utc)

        clamped = min(duration_min, self.MAX_OVERRIDE_DURATION_MIN)
        valid_until = now + timedelta(minutes=clamped)

        self._active = ActiveOverride(
            action=action,
            valid_until=valid_until,
            command_id=command_id,
        )
        return True, f"Override akzeptiert, gültig bis {valid_until.isoformat()}"

    def reject_if_safety(self, decision_code: str) -> bool:
        """Gibt True zurück wenn Override wegen R3 abgelehnt werden muss."""
        return decision_code.startswith("STOP_R3_")

    def get_active(self, now: datetime | None = None) -> ActiveOverride | None:
        """Gibt aktiven Override zurück oder None wenn abgelaufen."""
        if self._active is None:
            return None
        if now is None:
            now = datetime.now(tz=timezone.utc)
        if now >= self._active.valid_until:
            self._active = None
        return self._active

    def clear(self) -> None:
        self._active = None
