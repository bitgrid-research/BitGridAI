"""
R2 Autarkie — Schützt Batteriespeicher und begrenzt Grid-Import.

Soft-Min: NOOP (kein neuer Start)
Hard-Min: STOP (laufenden Miner sofort stoppen)

Netzbezug: bewertet den **Netto-Bezug** (grid_import − grid_export). Bei
3-Phasen-Schieflage kann phasenweiser Bezug >0 sein, obwohl netto eingespeist
wird — dann darf R2 nicht fälschlich stoppen (siehe FINDINGS, reale S8-Blöcke).

Abendregel: Ab evening_start_hour_utc (17:00 UTC = 19:00 CEST) gelten erhöhte
Schwellen, damit genug Kapazität für die Nacht bleibt. Deaktiviert wenn
evening_soc_min_pct == 0.0 (Default).
"""

from __future__ import annotations

from datetime import timezone

from src.core.models import EnergyState, RuleVote


def evaluate(
    state: EnergyState,
    soc_soft_min_pct: float = 58.0,
    soc_hard_min_pct: float = 50.0,
    max_grid_import_w: float = 500.0,
    evening_soc_min_pct: float = 0.0,
    evening_start_hour_utc: int = 17,
) -> RuleVote | None:
    """
    Gibt RuleVote zurück wenn R2 ein Veto einlegt, sonst None.
    """
    effective_hard = soc_hard_min_pct
    effective_soft = soc_soft_min_pct
    is_evening = False

    if evening_soc_min_pct > soc_hard_min_pct:
        utc_hour = state.window_start.astimezone(timezone.utc).hour
        if utc_hour >= evening_start_hour_utc:
            effective_hard = evening_soc_min_pct
            effective_soft = evening_soc_min_pct + (soc_soft_min_pct - soc_hard_min_pct)
            is_evening = True

    if state.battery_soc_pct <= effective_hard:
        return RuleVote(
            rule="R2",
            action="STOP",
            confidence=1.0,
            reason="SOC_EVENING_HARD_MIN" if is_evening else "SOC_HARD_MIN",
        )

    if state.battery_soc_pct <= effective_soft:
        return RuleVote(
            rule="R2",
            action="NOOP",
            confidence=0.95,
            reason="SOC_EVENING_SOFT_MIN" if is_evening else "SOC_SOFT_MIN",
        )

    net_import_w = state.grid_import_w - (state.grid_export_w or 0.0)
    if net_import_w > max_grid_import_w:
        return RuleVote(
            rule="R2",
            action="STOP",
            confidence=0.9,
            reason="GRID_IMPORT_EXCEEDED",
        )

    return None
