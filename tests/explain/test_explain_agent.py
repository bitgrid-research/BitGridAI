"""Unit-Tests für ExplainAgent — alle 4 Bausteine (Baustein-Modell Kap. 24)."""

from __future__ import annotations

import pytest

from src.explain import decision_codes as dc
from src.explain.explain_agent import ExplainAgent, ExplainResult


@pytest.fixture
def agent() -> ExplainAgent:
    return ExplainAgent(lang="de")


@pytest.fixture
def agent_en() -> ExplainAgent:
    return ExplainAgent(lang="en")


# ── Grundstruktur ────────────────────────────────────────────────────────────

def test_result_is_explain_result(agent: ExplainAgent) -> None:
    result = agent.explain(dc.START_R1_SURPLUS_OK, {})
    assert isinstance(result, ExplainResult)


def test_all_four_baustein_fields_present(agent: ExplainAgent) -> None:
    result = agent.explain(dc.START_R1_SURPLUS_OK, {})
    assert hasattr(result, "trigger")
    assert hasattr(result, "data_basis")
    assert hasattr(result, "effect")
    assert hasattr(result, "options")


def test_decision_code_preserved(agent: ExplainAgent) -> None:
    result = agent.explain(dc.NOOP_R5_DEADBAND_ACTIVE, {})
    assert result.decision_code == dc.NOOP_R5_DEADBAND_ACTIVE


def test_lang_preserved(agent: ExplainAgent) -> None:
    result = agent.explain(dc.START_R1_SURPLUS_OK, {})
    assert result.lang == "de"


# ── Parameterinterpolation ────────────────────────────────────────────────────

def test_data_basis_interpolates_params(agent: ExplainAgent) -> None:
    params = {"pv_power_w": 4200.0, "house_load_w": 800.0, "surplus_kw": 3.4,
              "surplus_min_kw": 1.5}
    result = agent.explain(dc.START_R1_SURPLUS_OK, params)
    assert "4200" in result.data_basis
    assert "800" in result.data_basis
    assert "3.4" in result.data_basis


def test_effect_no_interpolation_needed(agent: ExplainAgent) -> None:
    result = agent.explain(dc.START_R1_SURPLUS_OK, {})
    assert result.effect == "Miner gestartet"


def test_options_interpolates_threshold(agent: ExplainAgent) -> None:
    params = {"surplus_min_kw": 2.0}
    result = agent.explain(dc.NOOP_R1_INSUFFICIENT_SURPLUS, params)
    assert "2.0" in result.options


def test_trigger_interpolates_threshold(agent: ExplainAgent) -> None:
    params = {"surplus_min_kw": 1.5}
    result = agent.explain(dc.START_R1_SURPLUS_OK, params)
    assert "1.5" in result.trigger


def test_missing_param_returns_question_mark(agent: ExplainAgent) -> None:
    # data_basis for START_R1_SURPLUS_OK uses {pv_power_w:.0f} etc.
    # _SafeDict._Missing renders "?" for any format spec.
    result = agent.explain(dc.START_R1_SURPLUS_OK, {})
    assert "?" in result.data_basis

def test_missing_simple_key_returns_question_mark(agent: ExplainAgent) -> None:
    # NOOP_R5_DEADBAND data_basis has {blocks_since_last_change} (no format spec).
    result = agent.explain(dc.NOOP_R5_DEADBAND_ACTIVE, {})
    assert "?" in result.data_basis


# ── Alle Decision-Codes haben die drei neuen Felder befüllt ──────────────────

@pytest.mark.parametrize("code", sorted(dc.ALL_CODES))
def test_all_codes_have_effect(agent: ExplainAgent, code: str) -> None:
    result = agent.explain(code, {})
    assert isinstance(result.effect, str), f"{code}: effect ist kein str"
    assert result.effect != code, f"{code}: effect hat Fallback auf Code-Name"


@pytest.mark.parametrize("code", sorted(dc.ALL_CODES))
def test_all_codes_have_data_basis(agent: ExplainAgent, code: str) -> None:
    result = agent.explain(code, {})
    assert isinstance(result.data_basis, str), f"{code}: data_basis ist kein str"


@pytest.mark.parametrize("code", sorted(dc.ALL_CODES))
def test_all_codes_have_trigger(agent: ExplainAgent, code: str) -> None:
    result = agent.explain(code, {})
    assert isinstance(result.trigger, str), f"{code}: trigger ist kein str"
    assert result.trigger != "", f"{code}: trigger ist leer"


@pytest.mark.parametrize("code", sorted(dc.ALL_CODES))
def test_all_codes_have_options_str(agent: ExplainAgent, code: str) -> None:
    result = agent.explain(code, {})
    assert isinstance(result.options, str), f"{code}: options ist kein str"


# ── Inhaltliche Korrektheit ausgewählter Codes ────────────────────────────────

def test_stop_r2_soc_hard_min_effect(agent: ExplainAgent) -> None:
    result = agent.explain(dc.STOP_R2_SOC_HARD_MIN, {})
    assert "Batteriesicherheit" in result.effect


def test_stop_r3_overtemp_effect(agent: ExplainAgent) -> None:
    result = agent.explain(dc.STOP_R3_OVERTEMP, {})
    assert "Überhitzung" in result.effect


def test_stop_r3_comm_timeout_options(agent: ExplainAgent) -> None:
    result = agent.explain(dc.STOP_R3_COMM_TIMEOUT, {})
    assert "MQTT" in result.options


def test_noop_r5_deadband_options_contains_valid_until(agent: ExplainAgent) -> None:
    params = {"valid_until": "Block 895000", "blocks_since_last_change": 2}
    result = agent.explain(dc.NOOP_R5_DEADBAND_ACTIVE, params)
    assert "Block 895000" in result.options


def test_noop_r4_forecast_pv_data_basis(agent: ExplainAgent) -> None:
    params = {"pv_forecast_kw": 0.8, "min_predicted_surplus_kw": 1.5}
    result = agent.explain(dc.NOOP_R4_FORECAST_PV_INSUFFICIENT, params)
    assert "0.8" in result.data_basis
    assert "1.5" in result.data_basis


def test_start_r1_options_is_empty(agent: ExplainAgent) -> None:
    result = agent.explain(dc.START_R1_SURPLUS_OK, {})
    assert result.options == ""


# ── NOOP ist aktive Entscheidung — effect darf nicht leer sein ───────────────

@pytest.mark.parametrize("code", [c for c in dc.ALL_CODES if c.startswith("NOOP")])
def test_noop_codes_have_nonempty_effect(agent: ExplainAgent, code: str) -> None:
    result = agent.explain(code, {})
    assert result.effect != "", f"{code}: NOOP ohne Wirkungstext"


# ── Englische Sprache ─────────────────────────────────────────────────────────

def test_en_effect_for_start(agent_en: ExplainAgent) -> None:
    result = agent_en.explain(dc.START_R1_SURPLUS_OK, {})
    assert result.effect == "Miner started"


def test_en_stop_r3_overtemp_options(agent_en: ExplainAgent) -> None:
    params = {"max_chip_temp_c": 85.0}
    result = agent_en.explain(dc.STOP_R3_OVERTEMP, params)
    assert "85" in result.options


# ── Unbekannter Code — kein Crash ─────────────────────────────────────────────

def test_unknown_code_returns_code_as_short(agent: ExplainAgent) -> None:
    result = agent.explain("UNKNOWN_CODE_XYZ", {})
    assert result.short == "UNKNOWN_CODE_XYZ"
    assert result.effect == ""
    assert result.data_basis == ""
    assert result.options == ""


# ── rule_states und energy_state_ref werden durchgereicht ────────────────────

def test_rule_states_passed_through(agent: ExplainAgent) -> None:
    states = {"R1": "ok", "R3": "blocked"}
    result = agent.explain(dc.STOP_R3_OVERTEMP, {}, rule_states=states)
    assert result.rule_states == states


def test_energy_state_ref_passed_through(agent: ExplainAgent) -> None:
    result = agent.explain(dc.START_R1_SURPLUS_OK, {}, energy_state_ref="2024-01-15T10:00:00")
    assert result.energy_state_ref == "2024-01-15T10:00:00"
