"""
Unit-Tests für die Rule Engine.

Kritische Invarianten:
- R3 Safety überstimmt IMMER alle anderen Regeln
- Gleicher Input → gleicher Output (Determinismus)
- DecisionEvent enthält immer decision_code, reason, params
"""

from __future__ import annotations

from src.core import rule_engine
from src.core.models import EnergyState
from src.core.rule_engine import RuleEngineConfig


def test_r3_overrides_r1_when_overtemp(overtemp_state: EnergyState) -> None:
    """R3 Safety muss R1 Profitabilität immer überstimmen."""
    event = rule_engine.evaluate(overtemp_state)
    assert event.decision.action == "STOP"
    assert "R3" in event.decision_code
    assert "OVERTEMP" in event.reason


def test_r2_stops_when_soc_critical(low_soc_state: EnergyState) -> None:
    """R2 stoppt den Miner wenn SoC unter Hard-Min."""
    event = rule_engine.evaluate(low_soc_state)
    assert event.decision.action == "STOP"
    assert "R2" in event.decision_code


def test_r1_starts_with_surplus(nominal_state: EnergyState) -> None:
    """R1 startet den Miner bei ausreichendem Überschuss."""
    event = rule_engine.evaluate(nominal_state)
    assert event.decision.action == "START"
    assert "R1" in event.decision_code


def test_no_surplus_produces_noop(no_surplus_state: EnergyState) -> None:
    event = rule_engine.evaluate(no_surplus_state)
    assert event.decision.action == "NOOP"


def test_determinism_same_input_same_output(nominal_state: EnergyState) -> None:
    """Gleicher Input → gleicher Output. Immer."""
    e1 = rule_engine.evaluate(nominal_state)
    e2 = rule_engine.evaluate(nominal_state)
    assert e1.decision.action == e2.decision.action
    assert e1.decision_code == e2.decision_code
    assert e1.reason == e2.reason


def test_decision_event_has_required_fields(nominal_state: EnergyState) -> None:
    event = rule_engine.evaluate(nominal_state)
    assert event.decision_code
    assert event.reason
    assert isinstance(event.params, dict)
    assert event.state_snapshot is nominal_state
    assert event.trigger in ("BLOCK_TICK", "SAFETY_ASYNC", "OVERRIDE")


def test_r3_safety_beats_r2_when_both_triggered(overtemp_state: EnergyState) -> None:
    """Übertemperatur + niedriger SoC → R3 gewinnt."""
    from src.core.models import EnergyState as ES

    combined = EnergyState(
        **{**overtemp_state.__dict__, "battery_soc_pct": 5.0}  # type: ignore[arg-type]
    )
    event = rule_engine.evaluate(combined)
    assert "R3" in event.decision_code


def test_deadband_keeps_decision_stable(nominal_state: EnergyState) -> None:
    """R5 Deadband hält Decision stabil — kein Flapping."""
    e1 = rule_engine.evaluate(
        nominal_state, last_action="START", blocks_since_last_change=1
    )
    assert e1.decision.action == "NOOP"
    assert "R5" in e1.decision_code


# ── Autonomie-Modi ────────────────────────────────────────────────────────────


def test_manual_mode_produces_noop_when_surplus(nominal_state: EnergyState) -> None:
    """MANUAL-Modus: kein automatischer Start trotz Überschuss."""
    event = rule_engine.evaluate(nominal_state, autonomy_level="MANUAL")
    assert event.decision.action == "NOOP"
    assert event.decision_code == "NOOP_MANUAL_MODE"
    assert event.reason == "MANUAL_MODE"


def test_manual_mode_produces_noop_when_low_soc(low_soc_state: EnergyState) -> None:
    """MANUAL-Modus: kein automatischer Stop durch R2 (außer R3)."""
    event = rule_engine.evaluate(low_soc_state, autonomy_level="MANUAL")
    assert event.decision.action == "NOOP"
    assert event.decision_code == "NOOP_MANUAL_MODE"


def test_manual_mode_r3_safety_still_fires(overtemp_state: EnergyState) -> None:
    """MANUAL-Modus: R3 Safety bleibt in allen Modi aktiv."""
    event = rule_engine.evaluate(overtemp_state, autonomy_level="MANUAL")
    assert event.decision.action == "STOP"
    assert "R3" in event.decision_code


def test_semi_mode_blocks_r2_stop(low_soc_state: EnergyState) -> None:
    """SEMI-Modus: R2-STOP wird zu NOOP — nur R3 darf stoppen."""
    event = rule_engine.evaluate(low_soc_state, autonomy_level="SEMI")
    assert event.decision.action == "NOOP"
    assert "R2" in event.decision_code


def test_semi_mode_r3_safety_still_fires(overtemp_state: EnergyState) -> None:
    """SEMI-Modus: R3 Safety bleibt aktiv."""
    event = rule_engine.evaluate(overtemp_state, autonomy_level="SEMI")
    assert event.decision.action == "STOP"
    assert "R3" in event.decision_code


def test_full_mode_is_default_behavior(nominal_state: EnergyState) -> None:
    """FULL-Modus verhält sich identisch zum Default."""
    event_default = rule_engine.evaluate(nominal_state)
    event_full = rule_engine.evaluate(nominal_state, autonomy_level="FULL")
    assert event_default.decision.action == event_full.decision.action
    assert event_default.decision_code == event_full.decision_code


def test_manual_mode_noop_contains_autonomy_level_param(
    nominal_state: EnergyState,
) -> None:
    """NOOP_MANUAL_MODE trägt autonomy_level im params-Dict."""
    event = rule_engine.evaluate(nominal_state, autonomy_level="MANUAL")
    assert event.params.get("autonomy_level") == "MANUAL"
