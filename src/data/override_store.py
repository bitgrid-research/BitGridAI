"""
SqliteOverrideStore — SQLite-Implementierung des OverrideStore-Ports.

Hält die Persistenz-Concern (SQL, Schema, commit) aus dem deterministischen
Kern heraus (ADR 002 Hexagonal, ADR 021). Tabellen: active_overrides (genau
ein aktiver Override) und override_log (append-only).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from src.core.override_handler import ActiveOverride


class SqliteOverrideStore:
    """Implementiert ``OverrideStore`` strukturell (Protocol, kein Erbe nötig)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def load_latest(self) -> ActiveOverride | None:
        row = self._conn.execute(
            "SELECT command_id, action, valid_until, requested_by "
            "FROM active_overrides ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        command_id, action, valid_until_str, requested_by = row
        valid_until = datetime.fromisoformat(valid_until_str)
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        return ActiveOverride(
            action=action,
            valid_until=valid_until,
            command_id=command_id,
            requested_by=requested_by,
        )

    def save(self, override: ActiveOverride) -> None:
        # Genau ein aktiver Override: alten verwerfen, neuen schreiben.
        self._conn.execute("DELETE FROM active_overrides")
        self._conn.execute(
            "INSERT INTO active_overrides "
            "(command_id, action, valid_until, requested_by, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                override.command_id,
                override.action,
                override.valid_until.isoformat(),
                override.requested_by,
                datetime.now(tz=timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def delete(self, command_id: str) -> None:
        self._conn.execute(
            "DELETE FROM active_overrides WHERE command_id = ?", (command_id,)
        )
        self._conn.commit()

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
        self._conn.execute(
            "INSERT INTO override_log "
            "(timestamp, action, duration_min, command_id, accepted, reject_reason, user_reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                timestamp.isoformat(),
                action,
                duration_min,
                command_id,
                int(accepted),
                reject_reason,
                user_reason,
            ),
        )
        self._conn.commit()
