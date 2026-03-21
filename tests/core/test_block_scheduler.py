"""Unit-Tests für BlockScheduler."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core import block_scheduler


def test_block_id_rounds_to_10_min() -> None:
    t = datetime(2024, 1, 15, 10, 7, 33, tzinfo=timezone.utc)
    block_id = block_scheduler.get_block_id(t)
    assert block_id == "2024-01-15T10:00:00"


def test_block_id_at_exact_boundary() -> None:
    t = datetime(2024, 1, 15, 10, 10, 0, tzinfo=timezone.utc)
    block_id = block_scheduler.get_block_id(t)
    assert block_id == "2024-01-15T10:10:00"


def test_window_duration_is_10_min() -> None:
    t = datetime(2024, 1, 15, 10, 3, tzinfo=timezone.utc)
    start, end = block_scheduler.get_window(t)
    delta = end - start
    assert delta.total_seconds() == 600


def test_valid_until_is_two_blocks_ahead() -> None:
    t = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    valid_until = block_scheduler.get_valid_until(t)
    expected = datetime(2024, 1, 15, 10, 20, tzinfo=timezone.utc)
    assert valid_until == expected
