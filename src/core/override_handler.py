"""
OverrideHandler — manuelle Eingriffe mit TTL und Autonomie-Stufen.

R3-Safety-Entscheidungen können NIEMALS durch einen Override aufgehoben werden.
allow_unsafe_override ist hardcoded False.

Persistenz liegt hinter dem ``OverrideStore``-Port (hexagonal, ADR 002): der
Kern kennt nur die Schnittstelle, die SQLite-Implementierung lebt in ``data/``.
Ohne Store arbeitet der Handler rein in-memory (deterministisch, replay-fähig).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Protocol

from src.core.models import AutonomyLevel


@dataclass
class ActiveOverride:
    action: Literal["START", "STOP", "NOOP"]
    valid_until: datetime
    command_id: str
    requested_by: str = "operator"


class OverrideStore(Protocol):
    """Persistenz-Port für Overrides. Implementiert in der data-Schicht.

    Es ist immer höchstens ein Override aktiv (``save`` ersetzt den vorigen).
    Expiry/TTL-Logik bleibt im Kern; der Store ist reines CRUD.
    """

    def load_latest(self) -> ActiveOverride | None:
        """Letzten gespeicherten Override zurückgeben (ohne Expiry-Prüfung)."""
        ...

    def save(self, override: ActiveOverride) -> None:
        """Aktiven Override ersetzen (alter wird verworfen)."""
        ...

    def delete(self, command_id: str) -> None:
        """Override mit dieser command_id entfernen."""
        ...

    def append_attempt(
        self,
        *,
        timestamp: datetime,
        action: str,
        duration_min: int,
        command_id: str,
        accepted: bool,
        reject_reason: str,
        user_reason: str,
    ) -> None:
        """Override-Versuch ins append-only-Log schreiben (nie DELETE)."""
        ...


class OverrideHandler:
    """Verwaltet aktive Overrides mit TTL, optional persistiert über einen Store."""

    MAX_OVERRIDE_DURATION_MIN: int = 120

    def __init__(self, store: OverrideStore | None = None) -> None:
        self._store = store
        self._active: ActiveOverride | None = None
        self.autonomy_level: AutonomyLevel = "FULL"
        if store is not None:
            self._restore_active()

    def _restore_active(self) -> None:
        """Aktiven Override aus dem Store wiederherstellen (Abgelaufenes löschen)."""
        assert self._store is not None
        stored = self._store.load_latest()
        if stored is None:
            return
        now = datetime.now(tz=timezone.utc)
        valid_until = stored.valid_until
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        if now < valid_until:
            self._active = stored
        else:
            self._store.delete(stored.command_id)

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
        if self._store is not None:
            self._store.save(self._active)

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
            if self._store is not None:
                self._store.delete(self._active.command_id)
            self._active = None
        return self._active

    def log_attempt(
        self,
        action: str,
        duration_min: int,
        command_id: str,
        accepted: bool,
        reject_reason: str = "",
        user_reason: str = "",
        now: datetime | None = None,
    ) -> None:
        """Schreibt einen Override-Versuch ins Log (append-only, nie DELETE)."""
        if self._store is None:
            return
        if now is None:
            now = datetime.now(tz=timezone.utc)
        self._store.append_attempt(
            timestamp=now,
            action=action,
            duration_min=duration_min,
            command_id=command_id,
            accepted=accepted,
            reject_reason=reject_reason,
            user_reason=user_reason,
        )

    def clear(self) -> None:
        if self._active is not None and self._store is not None:
            self._store.delete(self._active.command_id)
        self._active = None
