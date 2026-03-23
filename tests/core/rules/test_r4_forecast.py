"""
Unit-Tests für R4 Forecast.

R4 gibt nur NOOP-Empfehlungen — kein STOP, kein START.
Bei fehlendem Forecast (pv_forecast_kw=None) gibt R4 immer None zurück.
"""

from __future__ import annotations

import pytest

from src.core.models import EnergyState
from src.core.rules import r4_forecast


def _with(state: EnergyState, **kwargs) -> EnergyState:
    """Hilfsfunktion: EnergyState mit überschriebenen Feldern."""
    return EnergyState(**{**state.__dict__, **kwargs})  # type: ignore[arg-type]


def test_no_forecast_returns_none(nominal_state: EnergyState) -> None:
    """Kein Forecast verfügbar → R4 passiert durch, andere Regeln entscheiden."""
    state = _with(nominal_state, pv_forecast_kw=None)
    assert r4_forecast.evaluate(state) is None


def test_sufficient_forecast_returns_none(nominal_state: EnergyState) -> None:
    """Guter Forecast → R4 kein Veto → R1 darf entscheiden."""
    state = _with(nominal_state, pv_forecast_kw=3.0)
    vote = r4_forecast.evaluate(state, min_predicted_surplus_kw=2.0)
    assert vote is None


def test_insufficient_forecast_returns_noop(nominal_state: EnergyState) -> None:
    """PV-Prognose zu niedrig → NOOP (kein neuer Start lohnt sich)."""
    state = _with(nominal_state, pv_forecast_kw=0.5)
    vote = r4_forecast.evaluate(state, min_predicted_surplus_kw=2.0)
    assert vote is not None
    assert vote.rule == "R4"
    assert vote.action == "NOOP"
    assert "FORECAST_PV" in vote.reason


def test_price_spike_with_good_forecast_returns_noop(
    nominal_state: EnergyState,
) -> None:
    """Preis-Spike trotz guter PV-Prognose → NOOP."""
    state = _with(nominal_state, pv_forecast_kw=4.0, energy_price_ct_kwh=35.0)
    vote = r4_forecast.evaluate(state, price_spike_threshold_ct=30.0)
    assert vote is not None
    assert vote.rule == "R4"
    assert vote.action == "NOOP"
    assert "PRICE_SPIKE" in vote.reason


def test_price_spike_without_price_signal_returns_none(
    nominal_state: EnergyState,
) -> None:
    """Kein Preissignal → kein Preis-Veto (R4 ignoriert fehlende Optionalfelder)."""
    state = _with(nominal_state, pv_forecast_kw=4.0, energy_price_ct_kwh=None)
    vote = r4_forecast.evaluate(state, price_spike_threshold_ct=30.0)
    assert vote is None


def test_r4_never_returns_stop(nominal_state: EnergyState) -> None:
    """R4 darf nie STOP zurückgeben — das ist ausschließlich R3 und R2."""
    state = _with(nominal_state, pv_forecast_kw=0.0, energy_price_ct_kwh=99.0)
    vote = r4_forecast.evaluate(state)
    if vote is not None:
        assert vote.action != "STOP"


def test_r4_never_returns_start(nominal_state: EnergyState) -> None:
    """R4 darf nie START zurückgeben — das ist ausschließlich R1."""
    state = _with(nominal_state, pv_forecast_kw=10.0)
    vote = r4_forecast.evaluate(state)
    if vote is not None:
        assert vote.action != "START"


def test_confidence_below_one_for_forecast(nominal_state: EnergyState) -> None:
    """R4 Forecast-Unsicherheit → confidence < 1.0 (nicht so sicher wie R3)."""
    state = _with(nominal_state, pv_forecast_kw=0.1)
    vote = r4_forecast.evaluate(state, min_predicted_surplus_kw=2.0)
    assert vote is not None
    assert vote.confidence < 1.0
