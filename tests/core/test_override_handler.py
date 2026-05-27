"""Unit-Tests für OverrideHandler (in-memory und DB-Persistenz)."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.core.override_handler import OverrideHandler
from src.data.db import get_connection


@pytest.fixture
def db_conn(tmp_path):
    """Temporäre SQLite-DB mit Schema."""
    return get_connection(tmp_path / "test.db")


def test_override_accepted() -> None:
    handler = OverrideHandler()
    accepted, msg = handler.request(
        "STOP", duration_min=30, command_id=str(uuid.uuid4())
    )
    assert accepted is True
    assert handler.get_active() is not None


def test_override_expires_after_ttl() -> None:
    handler = OverrideHandler()
    now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    handler.request("STOP", duration_min=30, command_id=str(uuid.uuid4()), now=now)

    future = now + timedelta(minutes=31)
    assert handler.get_active(now=future) is None


def test_override_still_active_within_ttl() -> None:
    handler = OverrideHandler()
    now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    handler.request("STOP", duration_min=30, command_id=str(uuid.uuid4()), now=now)

    within = now + timedelta(minutes=29)
    assert handler.get_active(now=within) is not None


def test_r3_decision_must_be_rejected() -> None:
    handler = OverrideHandler()
    assert handler.reject_if_safety("STOP_R3_OVERTEMP") is True
    assert handler.reject_if_safety("START_R1_SURPLUS_OK") is False


def test_max_override_duration_clamped() -> None:
    handler = OverrideHandler()
    now = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    handler.request("STOP", duration_min=9999, command_id=str(uuid.uuid4()), now=now)
    active = handler.get_active(now=now)
    assert active is not None
    max_valid = now + timedelta(minutes=handler.MAX_OVERRIDE_DURATION_MIN)
    assert active.valid_until <= max_valid


# ---------------------------------------------------------------------------
# DB-Persistenz
# ---------------------------------------------------------------------------


def test_override_persisted_to_db(db_conn) -> None:
    handler = OverrideHandler(conn=db_conn)
    cid = str(uuid.uuid4())
    handler.request("START", duration_min=10, command_id=cid)

    row = db_conn.execute(
        "SELECT command_id, action FROM active_overrides WHERE command_id = ?", (cid,)
    ).fetchone()
    assert row is not None
    assert row[1] == "START"


def test_override_loaded_from_db_on_init(db_conn) -> None:
    cid = str(uuid.uuid4())
    now = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)
    handler = OverrideHandler(conn=db_conn)
    handler.request("STOP", duration_min=60, command_id=cid, now=now)

    # Neue Instanz mit derselben DB — soll Override wiederherstellen
    handler2 = OverrideHandler(conn=db_conn)
    active = handler2.get_active(now=now)
    assert active is not None
    assert active.command_id == cid
    assert active.action == "STOP"


def test_expired_override_not_loaded_from_db(db_conn) -> None:
    cid = str(uuid.uuid4())
    past = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    handler = OverrideHandler(conn=db_conn)
    handler.request("STOP", duration_min=1, command_id=cid, now=past)

    # Neue Instanz — Override ist abgelaufen, darf nicht geladen werden
    handler2 = OverrideHandler(conn=db_conn)
    assert handler2.get_active() is None


def test_clear_removes_from_db(db_conn) -> None:
    handler = OverrideHandler(conn=db_conn)
    cid = str(uuid.uuid4())
    handler.request("NOOP", duration_min=30, command_id=cid)
    handler.clear()

    row = db_conn.execute(
        "SELECT * FROM active_overrides WHERE command_id = ?", (cid,)
    ).fetchone()
    assert row is None


def test_get_active_expired_deletes_from_db(db_conn) -> None:
    now = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
    handler = OverrideHandler(conn=db_conn)
    cid = str(uuid.uuid4())
    handler.request("START", duration_min=5, command_id=cid, now=now)

    # Zeitpunkt nach Ablauf — get_active() soll DB-Eintrag löschen
    future = now + timedelta(minutes=10)
    assert handler.get_active(now=future) is None
    row = db_conn.execute(
        "SELECT * FROM active_overrides WHERE command_id = ?", (cid,)
    ).fetchone()
    assert row is None
