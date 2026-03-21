"""
R4 Forecast — Vorschau auf kommende Blöcke.

Blockiert Start wenn ein PV-Einbruch erwartet wird.
Startet früher wenn ein Preis-Peak erwartet wird.
Gibt None zurück wenn kein Forecast verfügbar ist.
"""

from __future__ import annotations

from src.core.models import EnergyState, RuleVote


def evaluate(
    state: EnergyState,
    min_predicted_surplus_kw: float = 2.0,
    price_spike_threshold_ct: float = 30.0,
) -> RuleVote | None:
    """
    Gibt RuleVote zurück wenn Forecast eine Entscheidung begründet, sonst None.
    """
    if state.pv_forecast_kw is None:
        return None

    if state.pv_forecast_kw < min_predicted_surplus_kw:
        return RuleVote(
            rule="R4",
            action="NOOP",
            confidence=0.7,
            reason="FORECAST_PV_INSUFFICIENT",
        )

    if (
        state.energy_price_ct_kwh is not None
        and state.energy_price_ct_kwh >= price_spike_threshold_ct
    ):
        return RuleVote(
            rule="R4",
            action="NOOP",
            confidence=0.8,
            reason="FORECAST_PRICE_SPIKE",
        )

    return None
