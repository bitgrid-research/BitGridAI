"""Unit-Tests für OverrideHandler."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from src.core.override_handler import OverrideHandler


def test_override_accepted() -> None:
    handler = OverrideHandler()
    accepted, msg = handler.request("STOP", duration_min=30, command_id=str(uuid.uuid4()))
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
