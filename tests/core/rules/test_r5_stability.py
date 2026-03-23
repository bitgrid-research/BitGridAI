"""Unit-Tests für R5 Stabilität / Deadband."""

from __future__ import annotations

from src.core.models import EnergyState
from src.core.rules import r5_stability


def test_deadband_prevents_flapping(nominal_state: EnergyState) -> None:
    """Zwei identische States im gleichen Deadband-Fenster → NOOP."""
    vote = r5_stability.evaluate(
        nominal_state,
        last_action="START",
        blocks_since_last_change=1,
        deadband_hold_blocks=2,
        min_runtime_blocks=3,
    )
    assert vote is not None
    assert vote.action == "NOOP"


def test_min_runtime_blocks_respected(nominal_state: EnergyState) -> None:
    vote = r5_stability.evaluate(
        nominal_state,
        last_action="START",
        blocks_since_last_change=1,
        min_runtime_blocks=3,
    )
    assert vote is not None
    assert vote.action == "NOOP"
    assert "MIN_RUNTIME" in vote.reason


def test_min_pause_blocks_respected(nominal_state: EnergyState) -> None:
    vote = r5_stability.evaluate(
        nominal_state,
        last_action="STOP",
        blocks_since_last_change=0,
        min_pause_blocks=2,
    )
    assert vote is not None
    assert vote.action == "NOOP"
    assert "MIN_PAUSE" in vote.reason


def test_no_last_action_returns_none(nominal_state: EnergyState) -> None:
    vote = r5_stability.evaluate(
        nominal_state, last_action=None, blocks_since_last_change=0
    )
    assert vote is None


def test_after_deadband_returns_none(nominal_state: EnergyState) -> None:
    vote = r5_stability.evaluate(
        nominal_state,
        last_action="START",
        blocks_since_last_change=5,
        deadband_hold_blocks=2,
        min_runtime_blocks=3,
        min_pause_blocks=2,
    )
    assert vote is None
