"""
R1 Profitabilität — Start wenn PV-Überschuss und Preis ok.

Prüft:
- surplus_kw >= surplus_min_kw
- energy_price_ct_kwh <= price_max_ct_kwh (falls Preis verfügbar)
"""

from __future__ import annotations

from src.core.models import EnergyState, RuleVote


def evaluate(
    state: EnergyState,
    surplus_min_kw: float = 1.5,
    price_max_ct_kwh: float | None = 25.0,
) -> RuleVote:
    if state.surplus_kw < surplus_min_kw:
        return RuleVote(
            rule="R1",
            action="NOOP",
            confidence=0.9,
            reason="INSUFFICIENT_SURPLUS",
        )

    if (
        price_max_ct_kwh is not None
        and state.energy_price_ct_kwh is not None
        and state.energy_price_ct_kwh > price_max_ct_kwh
    ):
        return RuleVote(
            rule="R1",
            action="NOOP",
            confidence=0.8,
            reason="PRICE_TOO_HIGH",
        )

    return RuleVote(
        rule="R1",
        action="START",
        confidence=0.9,
        reason="SURPLUS_OK",
    )
