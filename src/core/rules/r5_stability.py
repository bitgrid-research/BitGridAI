"""
R5 Stabilität / Deadband — verhindert Flapping.

Hält die letzte Entscheidung für min. deadband_hold_blocks Blöcke stabil.
Erzwingt Mindestlaufzeit (min_runtime_blocks) und Mindestpause (min_pause_blocks).
"""

from __future__ import annotations

from src.core.models import EnergyState, RuleVote


def evaluate(
    state: EnergyState,
    last_action: str | None,
    blocks_since_last_change: int,
    deadband_hold_blocks: int = 2,
    min_runtime_blocks: int = 3,
    min_pause_blocks: int = 2,
) -> RuleVote | None:
    """
    Gibt RuleVote(NOOP) zurück wenn Deadband aktiv ist, sonst None.

    Parameters
    ----------
    last_action : letzte ausgeführte Aktion ("START" | "STOP" | None)
    blocks_since_last_change : Blöcke seit dem letzten Aktionswechsel
    """
    if last_action is None:
        return None

    if last_action == "START" and blocks_since_last_change < min_runtime_blocks:
        return RuleVote(
            rule="R5",
            action="NOOP",
            confidence=0.85,
            reason="MIN_RUNTIME_NOT_REACHED",
        )

    if last_action == "STOP" and blocks_since_last_change < min_pause_blocks:
        return RuleVote(
            rule="R5",
            action="NOOP",
            confidence=0.85,
            reason="MIN_PAUSE_NOT_REACHED",
        )

    if blocks_since_last_change < deadband_hold_blocks:
        return RuleVote(
            rule="R5",
            action="NOOP",
            confidence=0.75,
            reason="DEADBAND_ACTIVE",
        )

    return None
