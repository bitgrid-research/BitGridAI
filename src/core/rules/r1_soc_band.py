"""
R1 SoC-Band — additive Produktiv-Strategie (Alternative zu ``r1_profitability``).

Bildet die reale HA-Steuerung (``mvp_auto.yaml``, 2x Avalon Q) im Kern nach: Start,
Stopp und Betriebsmodus richten sich nach **SoC-Bändern** statt nach kW-Überschuss.
Aktiviert über ``RuleEngineConfig(strategy="soc_band")`` — der Default ``"surplus"``
lässt das bisherige Verhalten (und das eingefrorene Studien-Set) unangetastet.

Mapping auf die bestehenden Kern-Aktionen (Modus zusätzlich in
``DecisionEvent.params["mode"]``):

==========  ===========  ===================================
Modus       Aktion       Bedingung (SoC)
==========  ===========  ===================================
Standby     STOP         SoC < soc_stop (Hausreserve)
(Hold)      NOOP         soc_stop <= SoC < soc_eco_start
Eco         THROTTLE     soc_eco_start <= SoC < soc_standard
Standard    START        soc_standard <= SoC < soc_super
Super       START        SoC >= soc_super
==========  ===========  ===================================

Die SoC-Schwellen sind dimensionslos und **identisch** zum Realbetrieb; nur die
Leistungsschwelle ``pv_start_w`` (Eco-Frischstart) wird fürs Energielabor skaliert.
Anti-Flapping/Hysterese an den Bandgrenzen übernimmt R5 (Deadband/Min-Runtime).
"""

from __future__ import annotations

from src.core.models import EnergyState, RuleVote


def evaluate(
    state: EnergyState,
    soc_stop: float = 50.0,
    soc_eco_start: float = 58.0,
    soc_standard: float = 80.0,
    soc_super: float = 90.0,
    pv_start_w: float = 6000.0,
    last_action: str | None = None,
) -> RuleVote:
    """SoC-Band → RuleVote. Reine Funktion, kein I/O, kein globaler State."""
    soc = state.battery_soc_pct

    # Reserve-Stop (Hausreserve) — Schutzpriorität dieser Strategie.
    if soc < soc_stop:
        return RuleVote(
            rule="R1", action="STOP", confidence=1.0, reason="SOC_RESERVE_STOP"
        )

    # Super-Band: voller Modus.
    if soc >= soc_super:
        return RuleVote(rule="R1", action="START", confidence=0.9, reason="SUPER")

    # Standard-Band.
    if soc >= soc_standard:
        return RuleVote(rule="R1", action="START", confidence=0.9, reason="STANDARD")

    # Eco-Band: Frischstart braucht PV >= pv_start_w; ein laufender Miner bleibt im Eco.
    if soc >= soc_eco_start:
        running = last_action in ("START", "THROTTLE")
        if running or state.pv_power_w >= pv_start_w:
            return RuleVote(rule="R1", action="THROTTLE", confidence=0.85, reason="ECO")
        return RuleVote(rule="R1", action="NOOP", confidence=0.7, reason="SOC_HOLD_PV")

    # Hysterese-Band (soc_stop .. soc_eco_start): kein Neustart, laufender Miner bleibt (NOOP).
    return RuleVote(rule="R1", action="NOOP", confidence=0.8, reason="SOC_HOLD")
