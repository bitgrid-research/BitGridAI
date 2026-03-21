"""
Integrationstests für EventStore und StateStore (SQLite, tmp_path).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.core.models import Decision, DecisionEvent, EnergyState
from src.data.db import get_connection
from src.data.event_store import EventStore
from src.data.state_store import StateStore


@pytest.fixture
def db_conn(tmp_path: Path):
    conn = get_connection(tmp_path / "test.db")
    yield conn
    conn.close()


@pytest.fixture
def sample_event(nominal_state: EnergyState) -> DecisionEvent:
    return DecisionEvent(
        decision=Decision(
            action="START",
            valid_until=datetime(2024, 1, 15, 10, 20, tzinfo=timezone.utc),
            command_id="test-cmd-id-001",
        ),
        reason="SURPLUS_OK",
        trigger="BLOCK_TICK",
        params={"surplus_kw": 2.4},
        state_snapshot=nominal_state,
        decision_code="START_R1_SURPLUS_OK",
    )


def test_event_write_and_read(db_conn, sample_event: DecisionEvent) -> None:
    store = EventStore(db_conn)
    store.write(sample_event, explain_short="Überschuss verfügbar")

    result = store.read("test-cmd-id-001")
    assert result is not None
    assert result["action"] == "START"
    assert result["decision_code"] == "START_R1_SURPLUS_OK"
    assert result["explain_short"] == "Überschuss verfügbar"


def test_event_append_only(db_conn, sample_event: DecisionEvent) -> None:
    """Zweimaliges Schreiben derselben ID → kein Fehler, kein Duplikat."""
    store = EventStore(db_conn)
    store.write(sample_event)
    store.write(sample_event)  # INSERT OR IGNORE

    results = store.latest(n=10)
    ids = [r["id"] for r in results]
    assert ids.count("test-cmd-id-001") == 1


def test_state_write_and_read(db_conn, nominal_state: EnergyState) -> None:
    store = StateStore(db_conn)
    store.write(nominal_state)

    loaded = store.read(nominal_state.block_id)
    assert loaded is not None
    assert loaded.pv_power_w == nominal_state.pv_power_w
    assert loaded.surplus_kw == nominal_state.surplus_kw
    assert loaded.quality == nominal_state.quality


def test_state_replay_safe(db_conn, nominal_state: EnergyState) -> None:
    """Replay-Safe: gelesener State ist identisch mit gespeichertem."""
    store = StateStore(db_conn)
    store.write(nominal_state)
    loaded = store.read(nominal_state.block_id)

    assert loaded is not None
    assert loaded.block_id == nominal_state.block_id
    assert loaded.battery_soc_pct == nominal_state.battery_soc_pct
    assert loaded.missing_signals == nominal_state.missing_signals
