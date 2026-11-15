"""Done-date ledger for the thesis plan (synthetic steps only)."""

from __future__ import annotations

from datetime import date

from src.data import thesis_sync as ts


def _steps() -> list[dict[str, object]]:
    return [
        {"key": "a", "state": "erledigt"},
        {"key": "b", "state": "jetzt"},
        {"key": "c", "state": "erledigt"},
    ]


def test_new_done_step_gets_today_and_keeps_old_day() -> None:
    steps = _steps()
    ledger = ts.stamp_done(steps, {"a": "2026-11-10"}, date(2026, 11, 15))
    assert ledger == {"a": "2026-11-10", "c": "2026-11-15"}
    assert [s["nr"] for s in steps] == [1, 2, 3]
    assert steps[0]["done_at"] == "2026-11-10"
    assert "done_at" not in steps[1]


def test_reopened_step_loses_its_day() -> None:
    steps = _steps()
    steps[0]["state"] = "offen"
    ledger = ts.stamp_done(steps, {"a": "2026-11-10"}, date(2026, 11, 15))
    assert "a" not in ledger
