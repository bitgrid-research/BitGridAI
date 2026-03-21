"""
EventStore — schreibt und liest DecisionEvents (append-only).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from src.core.models import DecisionEvent


class EventStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def write(self, event: DecisionEvent, explain_short: str = "") -> None:
        """Schreibt ein DecisionEvent. Niemals UPDATE oder DELETE."""
        self._conn.execute(
            """
            INSERT OR IGNORE INTO decision_events
            (id, block_id, timestamp, action, decision_code, reason, trigger,
             params_json, valid_until, explain_short, state_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.decision.command_id,
                event.state_snapshot.block_id,
                datetime.now(timezone.utc).isoformat(),
                event.decision.action,
                event.decision_code,
                event.reason,
                event.trigger,
                json.dumps(event.params),
                event.decision.valid_until.isoformat(),
                explain_short,
                event.state_snapshot.block_id,
            ),
        )
        self._conn.commit()

    def read(self, command_id: str) -> dict | None:
        cur = self._conn.execute(
            "SELECT * FROM decision_events WHERE id = ?", (command_id,)
        )
        row = cur.fetchone()
        return dict(zip([d[0] for d in cur.description], row)) if row else None

    def latest(self, n: int = 10) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM decision_events ORDER BY timestamp DESC LIMIT ?", (n,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def read_range(self, start: datetime, end: datetime) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM decision_events WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
            (start.isoformat(), end.isoformat()),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
