"""
Unit-Tests für R3 Safety.

R3 ist non-negotiable: Safety überstimmt alle anderen Regeln.
"""

from __future__ import annotations

import pytest

from src.core.models import EnergyState
from src.core.rules import r3_safety


def test_overtemp_triggers_stop(overtemp_state: EnergyState) -> None:
    vote = r3_safety.evaluate(overtemp_state, max_chip_temp_c=85.0)
    assert vote is not None
    assert vote.action == "STOP"
    assert vote.rule == "R3"
    assert "OVERTEMP" in vote.reason


def test_normal_temp_returns_none(nominal_state: EnergyState) -> None:
    vote = r3_safety.evaluate(nominal_state, max_chip_temp_c=85.0)
    assert vote is None


def test_comm_timeout_triggers_stop(nominal_state: EnergyState) -> None:
    stale = EnergyState(
        **{**nominal_state.__dict__, "miner_heartbeat_age_sec": 120.0}  # type: ignore[arg-type]
    )
    vote = r3_safety.evaluate(stale, comm_timeout_sec=60.0)
    assert vote is not None
    assert vote.action == "STOP"
    assert "COMM_TIMEOUT" in vote.reason


def test_absolute_safety_limit_cannot_be_overridden(nominal_state: EnergyState) -> None:
    """Auch wenn config max_chip_temp_c > Absolut-Limit gesetzt wird, greift R3 trotzdem."""
    hot_state = EnergyState(
        **{**nominal_state.__dict__, "miner_temp_c": 97.0}  # type: ignore[arg-type]
    )
    # Config-Schwelle höher als Absolut-Limit (95°C)
    vote = r3_safety.evaluate(hot_state, max_chip_temp_c=100.0)
    assert vote is not None
    assert vote.action == "STOP"


def test_confidence_is_one_for_safety(overtemp_state: EnergyState) -> None:
    vote = r3_safety.evaluate(overtemp_state)
    assert vote is not None
    assert vote.confidence == 1.0
