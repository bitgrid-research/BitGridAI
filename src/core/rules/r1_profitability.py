"""
R1 Profitabilität — Start wenn PV-Überschuss vorhanden ist.

Strategie: **Eigenverbrauch vor Einspeisung** — Überschuss soll von den Minern
abgefangen werden, bevor er ins Netz exportiert wird. Die Break-Even-Bewertung
gegen die Einspeisevergütung ist bewusst **nur Anzeige** (siehe economics-Layer),
kein Start-Gate: das System mint auch, wenn Mining marginal weniger bringt als
Einspeisen.

Drei-Band-Logik nach Überschuss (Eigenverbrauch maximieren):
- surplus_kw <  surplus_throttle_min_kw → NOOP (zu wenig)
- surplus_throttle_min_kw <= surplus_kw < surplus_min_kw → THROTTLE (Eco-Modus)
- surplus_kw >= surplus_min_kw → START (Voll-Last)

THROTTLE = Miner läuft gedrosselt (Avalon-Q-Eco-Modus): fängt auch marginalen
Überschuss ab, statt ihn einzuspeisen, ohne die volle Last zu ziehen.
energy_price_ct_kwh > price_max_ct_kwh bleibt eine Restschranke gegen Netz-Mining.
"""

from __future__ import annotations

from src.core.models import EnergyState, RuleVote


def evaluate(
    state: EnergyState,
    surplus_min_kw: float = 1.5,
    price_max_ct_kwh: float | None = 25.0,
    surplus_throttle_min_kw: float = 0.8,
) -> RuleVote:
    if state.surplus_kw < surplus_throttle_min_kw:
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

    if state.surplus_kw < surplus_min_kw:
        return RuleVote(
            rule="R1",
            action="THROTTLE",
            confidence=0.8,
            reason="SURPLUS_THROTTLE",
        )

    return RuleVote(
        rule="R1",
        action="START",
        confidence=0.9,
        reason="SURPLUS_OK",
    )
