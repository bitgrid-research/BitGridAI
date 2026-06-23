"""Tests für das SoC-Band-Studien-Set (Verifikation + Freeze über dieselbe Pipeline)."""

from __future__ import annotations

from pathlib import Path

from src.core import rule_engine
from src.sim.study_freeze import freeze_all
from src.sim.study_scenarios_soc_band import SOC_BAND_CONFIG, SOC_BAND_SCENARIOS


def test_all_soc_band_scenarios_trigger_expected_code() -> None:
    """Jeder Snapshot löst seinen erwarteten decision_code aus (13/13)."""
    assert len(SOC_BAND_SCENARIOS) == 13
    for sc in SOC_BAND_SCENARIOS:
        event = rule_engine.evaluate(
            sc.state,
            SOC_BAND_CONFIG,
            last_action=sc.last_action,
            blocks_since_last_change=sc.blocks_since_change,
            now=sc.now,
        )
        assert event.decision_code == sc.expected_code, (
            f"{sc.sid} {sc.clock}: erwartet {sc.expected_code}, "
            f"erhalten {event.decision_code}"
        )


def test_soc_band_freeze_group_a(tmp_path: Path) -> None:
    """Das SoC-Band-Set lässt sich durch study_freeze einfrieren (Gruppe A gefüllt)."""
    items = freeze_all(
        tmp_path,
        ollama_host="",
        scenarios=SOC_BAND_SCENARIOS,
        config=SOC_BAND_CONFIG,
    )
    assert len(items) == 13
    assert all(it["verified"] for it in items)
    # Gruppe-A-Erklärung deterministisch gefüllt, Gruppe B noch Platzhalter (kein LLM).
    assert all(it["explanation"]["group_a"]["short"] for it in items)
    assert all(it["explanation"]["group_b"] is None for it in items)
