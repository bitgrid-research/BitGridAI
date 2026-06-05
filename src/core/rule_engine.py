"""
RuleEngine — bewertet R1–R5 und erzeugt eine DecisionEvent.

Priorität: R3 (Safety) > R2 (Autarkie) > R4 (Forecast) > R5 (Stabilität) > R1 (Profitabilität)

R3 bricht bei Veto sofort ab — keine andere Regel kann R3 überstimmen.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from src.core import block_scheduler
from src.core.models import (
    AutonomyLevel,
    Decision,
    DecisionEvent,
    EnergyState,
    RuleVote,
)
from src.core.rules import (
    r1_profitability,
    r1_soc_band,
    r2_autarky,
    r3_safety,
    r4_forecast,
    r5_stability,
)

# Reason → Betriebsmodus (für params["mode"] in der SoC-Band-Strategie).
_SOC_BAND_MODE: dict[str, str] = {
    "SUPER": "Super",
    "STANDARD": "Standard",
    "ECO": "Eco",
    "SOC_RESERVE_STOP": "Standby",
    "SOC_HOLD": "Hold",
    "SOC_HOLD_PV": "Hold",
}


class RuleEngineConfig:
    """Konfigurationsparameter für alle Regeln."""

    def __init__(
        self,
        # R1
        surplus_min_kw: float = 1.5,
        price_max_ct_kwh: float | None = 25.0,
        surplus_throttle_min_kw: float = 0.8,
        # R2
        soc_soft_min_pct: float = 58.0,
        soc_hard_min_pct: float = 50.0,
        max_grid_import_w: float = 500.0,
        # R3
        max_chip_temp_c: float = 85.0,
        t_resume_c: float = 75.0,
        comm_timeout_sec: float = 60.0,
        # R4
        min_predicted_surplus_kw: float = 2.0,
        price_spike_threshold_ct: float = 30.0,
        # R5
        deadband_hold_blocks: int = 2,
        min_runtime_blocks: int = 3,
        min_pause_blocks: int = 2,
        # R1-Strategie (additiv) — Default "surplus" = bisheriges Verhalten.
        # "soc_band" bildet die Produktiv-Steuerung (mvp_auto.yaml) nach.
        strategy: str = "surplus",
        soc_stop_pct: float = 50.0,
        soc_eco_start_pct: float = 58.0,
        soc_standard_pct: float = 80.0,
        soc_standard_stop_pct: float = 75.0,
        soc_super_pct: float = 90.0,
        soc_super_stop_pct: float = 85.0,
        pv_start_w: float = 6000.0,
    ) -> None:
        self.surplus_min_kw = surplus_min_kw
        self.price_max_ct_kwh = price_max_ct_kwh
        self.surplus_throttle_min_kw = surplus_throttle_min_kw
        self.soc_soft_min_pct = soc_soft_min_pct
        self.soc_hard_min_pct = soc_hard_min_pct
        self.max_grid_import_w = max_grid_import_w
        self.max_chip_temp_c = max_chip_temp_c
        self.t_resume_c = t_resume_c
        self.comm_timeout_sec = comm_timeout_sec
        self.min_predicted_surplus_kw = min_predicted_surplus_kw
        self.price_spike_threshold_ct = price_spike_threshold_ct
        self.deadband_hold_blocks = deadband_hold_blocks
        self.min_runtime_blocks = min_runtime_blocks
        self.min_pause_blocks = min_pause_blocks
        self.strategy = strategy
        self.soc_stop_pct = soc_stop_pct
        self.soc_eco_start_pct = soc_eco_start_pct
        self.soc_standard_pct = soc_standard_pct
        self.soc_standard_stop_pct = soc_standard_stop_pct
        self.soc_super_pct = soc_super_pct
        self.soc_super_stop_pct = soc_super_stop_pct
        self.pv_start_w = pv_start_w


def evaluate(
    state: EnergyState,
    config: RuleEngineConfig | None = None,
    last_action: str | None = None,
    blocks_since_last_change: int = 0,
    trigger: Literal["BLOCK_TICK", "SAFETY_ASYNC", "OVERRIDE"] = "BLOCK_TICK",
    now: datetime | None = None,
    autonomy_level: AutonomyLevel = "FULL",
) -> DecisionEvent:
    """
    Pure Funktion: EnergyState → DecisionEvent.

    Gleicher Input → gleicher Output. Kein I/O, kein globaler State.
    autonomy_level: FULL = alle Regeln, SEMI = kein Auto-Stop (außer R3),
                    MANUAL = nur R3-Safety, Rest NOOP.
    """
    if config is None:
        config = RuleEngineConfig()
    if now is None:
        now = datetime.now(tz=timezone.utc)

    valid_until = block_scheduler.get_valid_until(now)
    votes: list[RuleVote] = []

    # --- R3 Safety (höchste Priorität, bricht sofort ab — in allen Modi) ---
    r3_vote = r3_safety.evaluate(
        state,
        max_chip_temp_c=config.max_chip_temp_c,
        t_resume_c=config.t_resume_c,
        comm_timeout_sec=config.comm_timeout_sec,
    )
    if r3_vote is not None:
        votes.append(r3_vote)
        decision_code = f"STOP_R3_{r3_vote.reason}"
        return DecisionEvent(
            decision=Decision(action="STOP", valid_until=valid_until),
            reason=r3_vote.reason,
            trigger="SAFETY_ASYNC" if trigger == "SAFETY_ASYNC" else "BLOCK_TICK",
            params={
                "miner_temp_c": state.miner_temp_c,
                "max_chip_temp_c": config.max_chip_temp_c,
                "miner_heartbeat_age_sec": state.miner_heartbeat_age_sec,
                "comm_timeout_sec": config.comm_timeout_sec,
            },
            state_snapshot=state,
            decision_code=decision_code,
        )

    # --- MANUAL-Modus: Nur R3 läuft — alle anderen Regeln = NOOP ---
    if autonomy_level == "MANUAL":
        return DecisionEvent(
            decision=Decision(action="NOOP", valid_until=valid_until),
            reason="MANUAL_MODE",
            trigger=trigger,
            params={"autonomy_level": autonomy_level},
            state_snapshot=state,
            decision_code="NOOP_MANUAL_MODE",
        )

    # --- R1-Strategie SoC-Band: Vote vorab berechnen. Der Reserve-Stop hat
    #     Schutzpriorität (vor R2/R4/R5, wie Produktions-P1 ohne Cooldown);
    #     die Start-/Modus-Bänder werden unten als R1-Schritt verwendet. ---
    soc_band_vote: RuleVote | None = None
    if config.strategy == "soc_band":
        soc_band_vote = r1_soc_band.evaluate(
            state,
            soc_stop=config.soc_stop_pct,
            soc_eco_start=config.soc_eco_start_pct,
            soc_standard=config.soc_standard_pct,
            soc_super=config.soc_super_pct,
            pv_start_w=config.pv_start_w,
            last_action=last_action,
        )
        if soc_band_vote.action == "STOP":
            # SEMI: kein selbstständiger Stopp (nur R3) → Reserve-Stop wird NOOP.
            reserve_action: Literal["STOP", "NOOP"] = (
                "NOOP" if autonomy_level == "SEMI" else "STOP"
            )
            return DecisionEvent(
                decision=Decision(action=reserve_action, valid_until=valid_until),
                reason=soc_band_vote.reason,
                trigger=trigger,
                params={
                    "battery_soc_pct": state.battery_soc_pct,
                    "soc_stop_pct": config.soc_stop_pct,
                    "mode": "Standby",
                    "strategy": "soc_band",
                    "autonomy_level": autonomy_level,
                },
                state_snapshot=state,
                decision_code=f"{reserve_action}_R1_{soc_band_vote.reason}",
            )

    # --- R2 Autarkie ---
    # Im SoC-Band-Modus besitzt die SoC-Band-Strategie die Hausreserve vollständig
    # (Reserve-Stop, Hold-Band, Eco-Start) — R2 prüft dann nur den Netzbezug, damit
    # es das Band nicht maskiert (Produktiv-Spiegelung, ADR 020). Im Surplus-Modus
    # (Studie) bleibt R2 die SoC-Reserve (soc_hard/soc_soft).
    r2_soc_soft = 0.0 if config.strategy == "soc_band" else config.soc_soft_min_pct
    r2_soc_hard = 0.0 if config.strategy == "soc_band" else config.soc_hard_min_pct
    r2_vote = r2_autarky.evaluate(
        state,
        soc_soft_min_pct=r2_soc_soft,
        soc_hard_min_pct=r2_soc_hard,
        max_grid_import_w=config.max_grid_import_w,
    )
    if r2_vote is not None:
        votes.append(r2_vote)
        # SEMI-Modus: R2-STOP-Entscheidungen werden blockiert (nur R3 darf stoppen)
        effective_action = (
            "NOOP"
            if autonomy_level == "SEMI" and r2_vote.action == "STOP"
            else r2_vote.action
        )
        return DecisionEvent(
            decision=Decision(action=effective_action, valid_until=valid_until),
            reason=r2_vote.reason,
            trigger=trigger,
            params={
                "battery_soc_pct": state.battery_soc_pct,
                "soc_soft_min_pct": r2_soc_soft,
                "soc_hard_min_pct": r2_soc_hard,
                "grid_import_w": state.grid_import_w,
                "max_grid_import_w": config.max_grid_import_w,
                "pv_forecast_kw": state.pv_forecast_kw,
                "autonomy_level": autonomy_level,
            },
            state_snapshot=state,
            decision_code=f"{effective_action}_R2_{r2_vote.reason}",
        )

    # --- R4 Forecast ---
    r4_vote = r4_forecast.evaluate(
        state,
        min_predicted_surplus_kw=config.min_predicted_surplus_kw,
        price_spike_threshold_ct=config.price_spike_threshold_ct,
    )
    if r4_vote is not None:
        votes.append(r4_vote)

    # --- R5 Stabilität / Deadband ---
    r5_vote = r5_stability.evaluate(
        state,
        last_action=last_action,
        blocks_since_last_change=blocks_since_last_change,
        deadband_hold_blocks=config.deadband_hold_blocks,
        min_runtime_blocks=config.min_runtime_blocks,
        min_pause_blocks=config.min_pause_blocks,
    )
    if r5_vote is not None:
        votes.append(r5_vote)
        return DecisionEvent(
            decision=Decision(action="NOOP", valid_until=valid_until),
            reason=r5_vote.reason,
            trigger=trigger,
            params={
                "blocks_since_last_change": blocks_since_last_change,
                "deadband_hold_blocks": config.deadband_hold_blocks,
                "min_runtime_blocks": config.min_runtime_blocks,
                "min_pause_blocks": config.min_pause_blocks,
                "last_action": last_action,
            },
            state_snapshot=state,
            decision_code=f"NOOP_R5_{r5_vote.reason}",
        )

    # R4 Veto nach R5 (R4 kann nur NOOP vorschlagen, nicht STOP)
    if r4_vote is not None and r4_vote.action == "NOOP":
        return DecisionEvent(
            decision=Decision(action="NOOP", valid_until=valid_until),
            reason=r4_vote.reason,
            trigger=trigger,
            params={"pv_forecast_kw": state.pv_forecast_kw},
            state_snapshot=state,
            decision_code=f"NOOP_R4_{r4_vote.reason}",
        )

    # --- R1-Schritt: strategieabhängig (Surplus-kW oder SoC-Band) ---
    params: dict[str, Any]
    if config.strategy == "soc_band":
        assert soc_band_vote is not None  # oben gesetzt; STOP wurde bereits behandelt
        r1_vote = soc_band_vote
        params = {
            "battery_soc_pct": state.battery_soc_pct,
            "soc_eco_start_pct": config.soc_eco_start_pct,
            "soc_standard_pct": config.soc_standard_pct,
            "soc_super_pct": config.soc_super_pct,
            "pv_power_w": state.pv_power_w,
            "pv_start_w": config.pv_start_w,
            "mode": _SOC_BAND_MODE.get(r1_vote.reason, "Hold"),
            "strategy": "soc_band",
        }
    else:
        r1_vote = r1_profitability.evaluate(
            state,
            surplus_min_kw=config.surplus_min_kw,
            price_max_ct_kwh=config.price_max_ct_kwh,
            surplus_throttle_min_kw=config.surplus_throttle_min_kw,
        )
        params = {
            "surplus_kw": state.surplus_kw,
            "surplus_min_kw": config.surplus_min_kw,
            "energy_price_ct_kwh": state.energy_price_ct_kwh,
            "mining_value_ct_kwh": state.mining_value_ct_kwh,
            "pv_forecast_kw": state.pv_forecast_kw,
            "pv_power_w": state.pv_power_w,
            "house_load_w": state.house_load_w,
            "battery_soc_pct": state.battery_soc_pct,
        }

    votes.append(r1_vote)

    return DecisionEvent(
        decision=Decision(action=r1_vote.action, valid_until=valid_until),
        reason=r1_vote.reason,
        trigger=trigger,
        params=params,
        state_snapshot=state,
        decision_code=f"{r1_vote.action}_R1_{r1_vote.reason}",
    )
