"""
OverrideHandler — manuelle Eingriffe mit TTL und Autonomie-Stufen.

R3-Safety-Entscheidungen können NIEMALS durch einen Override aufgehoben werden.
allow_unsafe_override ist hardcoded False.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Literal

from src.core.models import AutonomyLevel

if TYPE_CHECKING:
    pass


@dataclass
class ActiveOverride:
    action: Literal["START", "STOP", "NOOP"]
    valid_until: datetime
    command_id: str
    requested_by: str = "operator"


class OverrideHandler:
    """Verwaltet aktive Overrides mit TTL, persistiert in SQLite."""

    MAX_OVERRIDE_DURATION_MIN: int = 120

    def __init__(self, conn: sqlite3.Connection | None = None) -> None:
        self._conn = conn
        self._active: ActiveOverride | None = None
        self.autonomy_level: AutonomyLevel = "FULL"
        if conn is not None:
            self._load_from_db()

    def _load_from_db(self) -> None:
        assert self._conn is not None
        now = datetime.now(tz=timezone.utc)
        row = self._conn.execute(
            "SELECT command_id, action, valid_until, requested_by "
            "FROM active_overrides ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return
        command_id, action, valid_until_str, requested_by = row
        valid_until = datetime.fromisoformat(valid_until_str)
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        if now < valid_until:
            self._active = ActiveOverride(
                action=action,
                valid_until=valid_until,
                command_id=command_id,
                requested_by=requested_by,
            )
        else:
            self._conn.execute(
                "DELETE FROM active_overrides WHERE command_id = ?", (command_id,)
            )
            self._conn.commit()

    def request(
        self,
        action: Literal["START", "STOP", "NOOP"],
        duration_min: int,
        command_id: str,
        now: datetime | None = None,
    ) -> tuple[bool, str]:
        """Versucht einen Override zu setzen. Returns (accepted, message)."""
        if now is None:
            now = datetime.now(tz=timezone.utc)

        clamped = min(duration_min, self.MAX_OVERRIDE_DURATION_MIN)
        valid_until = now + timedelta(minutes=clamped)

        self._active = ActiveOverride(
            action=action,
            valid_until=valid_until,
            command_id=command_id,
        )

        if self._conn is not None:
            self._conn.execute("DELETE FROM active_overrides")
            self._conn.execute(
                "INSERT INTO active_overrides (command_id, action, valid_until, requested_by, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    command_id,
                    action,
                    valid_until.isoformat(),
                    "operator",
                    now.isoformat(),
                ),
            )
            self._conn.commit()

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
            if self._conn is not None:
                self._conn.execute(
                    "DELETE FROM active_overrides WHERE command_id = ?",
                    (self._active.command_id,),
                )
                self._conn.commit()
            self._active = None
        return self._active

    def clear(self) -> None:
        if self._active is not None and self._conn is not None:
            self._conn.execute(
                "DELETE FROM active_overrides WHERE command_id = ?",
                (self._active.command_id,),
            )
            self._conn.commit()
        self._active = None
