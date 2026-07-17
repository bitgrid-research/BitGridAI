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
        **{**nominal_state.__dict__, "miner_temp_c": 122.0}  # type: ignore[arg-type]
    )
    # Config-Schwelle höher als Absolut-Limit (120°C)
    vote = r3_safety.evaluate(hot_state, max_chip_temp_c=130.0)
    assert vote is not None
    assert vote.action == "STOP"


def test_real_operating_envelope_does_not_trigger(nominal_state: EnergyState) -> None:
    """Regressionstest zum Befund 2026-07-17: das reale Betriebsfenster der
    Avalon Q (Mittel 90.8 °C, Max 113 °C ueber 7 Tage) darf R3 NICHT ausloesen.
    Das alte Hardcap von 95 °C hat hier gestoppt und haette den Miner im
    Normalbetrieb dauerhaft abgeschaltet."""
    for temp in (90.8, 95.0, 105.0, 113.0):
        state = EnergyState(
            **{**nominal_state.__dict__, "miner_temp_c": temp}  # type: ignore[arg-type]
        )
        assert (
            r3_safety.evaluate(state, max_chip_temp_c=115.0) is None
        ), f"{temp} °C liegt im gemessenen Normalbetrieb, R3 darf nicht stoppen"


def test_confidence_is_one_for_safety(overtemp_state: EnergyState) -> None:
    vote = r3_safety.evaluate(overtemp_state)
    assert vote is not None
    assert vote.confidence == 1.0
