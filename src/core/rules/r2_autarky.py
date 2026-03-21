"""
R2 Autarkie — Schützt Batteriespeicher und begrenzt Grid-Import.

Soft-Min: NOOP (kein neuer Start)
Hard-Min: STOP (laufenden Miner sofort stoppen)
"""

from __future__ import annotations

from src.core.models import EnergyState, RuleVote


def evaluate(
    state: EnergyState,
    soc_soft_min_pct: float = 20.0,
    soc_hard_min_pct: float = 10.0,
    max_grid_import_w: float = 500.0,
) -> RuleVote | None:
    """
    Gibt RuleVote zurück wenn R2 ein Veto einlegt, sonst None.
    """
    if state.battery_soc_pct <= soc_hard_min_pct:
        return RuleVote(
            rule="R2",
            action="STOP",
            confidence=1.0,
            reason="SOC_HARD_MIN",
        )

    if state.battery_soc_pct <= soc_soft_min_pct:
        return RuleVote(
            rule="R2",
            action="NOOP",
            confidence=0.95,
            reason="SOC_SOFT_MIN",
        )

    if state.grid_import_w > max_grid_import_w:
        return RuleVote(
            rule="R2",
            action="STOP",
            confidence=0.9,
            reason="GRID_IMPORT_EXCEEDED",
        )

    return None
