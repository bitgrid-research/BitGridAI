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


def test_mining_value_is_monitoring_only_not_a_gate(nominal_state: EnergyState) -> None:
    """mining_value_ct_kwh ist reine Anzeige — blockiert den Start NICHT."""
    unprofitable = EnergyState(**{**nominal_state.__dict__, "mining_value_ct_kwh": 5.4})
    vote = r1_profitability.evaluate(unprofitable)
    assert vote.action == "START"  # Eigenverbrauch vor Einspeisung
    assert vote.reason == "SURPLUS_OK"


def test_marginal_surplus_triggers_throttle(nominal_state: EnergyState) -> None:
    """Überschuss im Throttle-Band (0,8–1,5 kW) → Eco-Modus statt NOOP."""
    marginal = EnergyState(**{**nominal_state.__dict__, "surplus_kw": 1.0})
    vote = r1_profitability.evaluate(
        marginal, surplus_min_kw=1.5, surplus_throttle_min_kw=0.8
    )
    assert vote.action == "THROTTLE"
    assert vote.reason == "SURPLUS_THROTTLE"


def test_below_throttle_band_triggers_noop(nominal_state: EnergyState) -> None:
    """Überschuss unter dem Throttle-Band → NOOP (zu wenig)."""
    too_low = EnergyState(**{**nominal_state.__dict__, "surplus_kw": 0.5})
    vote = r1_profitability.evaluate(
        too_low, surplus_min_kw=1.5, surplus_throttle_min_kw=0.8
    )
    assert vote.action == "NOOP"
    assert vote.reason == "INSUFFICIENT_SURPLUS"


def test_price_gate_precedes_throttle(nominal_state: EnergyState) -> None:
    """Preis-Restschranke greift auch im Throttle-Band."""
    marginal_pricey = EnergyState(
        **{**nominal_state.__dict__, "surplus_kw": 1.0, "energy_price_ct_kwh": 30.0}
    )
    vote = r1_profitability.evaluate(marginal_pricey, price_max_ct_kwh=25.0)
    assert vote.action == "NOOP"
    assert vote.reason == "PRICE_TOO_HIGH"
