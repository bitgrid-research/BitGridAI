"""Tests für den Studien-Freeze: Determinismus + Basis-Code-Normalisierung."""

from __future__ import annotations

from src.core import rule_engine
from src.core.rule_engine import RuleEngineConfig
from src.sim.study_freeze import base_code, freeze_all
from src.sim.study_scenarios import STUDY_SCENARIOS


def test_all_scenarios_produce_expected_code() -> None:
    """Jedes Szenario liefert exakt seinen erwarteten decision_code."""
    for sc in STUDY_SCENARIOS:
        event = rule_engine.evaluate(
            sc.state,
            config=RuleEngineConfig(),
            last_action=sc.last_action,
            blocks_since_last_change=sc.blocks_since_change,
        )
        assert event.decision_code == sc.expected_code, sc.sid


def test_base_code_strips_suffix() -> None:
    assert base_code("STOP_R3_OVERTEMP_T90") == "STOP_R3_OVERTEMP"
    assert base_code("STOP_R3_COMM_TIMEOUT_AGE75") == "STOP_R3_COMM_TIMEOUT"
    assert base_code("START_R1_SURPLUS_OK") == "START_R1_SURPLUS_OK"


def test_freeze_all_writes_verified_items(tmp_path) -> None:  # type: ignore[no-untyped-def]
    items = freeze_all(tmp_path, ollama_host="")
    assert len(items) == len(STUDY_SCENARIOS)
    assert all(it["verified"] for it in items)
    # Gruppe A gefüllt, Gruppe B Platzhalter (kein Ollama)
    for it in items:
        assert it["explanation"]["group_a"]["short"]
        assert it["explanation"]["group_b"] is None
    assert (tmp_path / "index.json").exists()
    assert (tmp_path / "S1.json").exists()


def test_freeze_includes_hamster_and_reference(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Jedes Szenario trägt eine Hamster-Anzeige und eine Gruppe-B-Gold-Referenz."""
    items = freeze_all(tmp_path, ollama_host="")
    for it in items:
        # Hamster-Anzeige spiegelt die Aktion.
        assert it["hamster"]["anzeige"], it["sid"]
        # Eine einzelne Gold-Referenz (String), nicht leer.
        ref = it["explanation"]["group_b_reference"]
        assert isinstance(ref, str) and ref, it["sid"]
