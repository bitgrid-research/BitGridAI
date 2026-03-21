"""Unit-Tests für R1 Profitabilität."""

from __future__ import annotations

from src.core.models import EnergyState
from src.core.rules import r1_profitability


def test_sufficient_surplus_triggers_start(nominal_state: EnergyState) -> None:
    vote = r1_profitability.evaluate(nominal_state, surplus_min_kw=1.5)
    assert vote.action == "START"
    assert vote.rule == "R1"


def test_insufficient_surplus_triggers_noop(no_surplus_state: EnergyState) -> None:
    vote = r1_profitability.evaluate(no_surplus_state, surplus_min_kw=1.5)
    assert vote.action == "NOOP"
    assert "INSUFFICIENT_SURPLUS" in vote.reason


def test_high_price_blocks_start(nominal_state: EnergyState) -> None:
    from dataclasses import replace
    expensive = EnergyState(
        **{**nominal_state.__dict__, "energy_price_ct_kwh": 30.0}  # type: ignore[arg-type]
    )
    vote = r1_profitability.evaluate(expensive, price_max_ct_kwh=25.0)
    assert vote.action == "NOOP"
    assert "PRICE_TOO_HIGH" in vote.reason


def test_no_price_filter_when_none(nominal_state: EnergyState) -> None:
    vote = r1_profitability.evaluate(nominal_state, price_max_ct_kwh=None)
    assert vote.action == "START"
