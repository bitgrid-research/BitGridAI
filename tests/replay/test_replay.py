"""
Replay-Tests — historische Fixtures durch den Core laufen lassen.

Gleicher Input → gleicher Output. Keine Abweichungen erlaubt.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.sim.replay import replay_fixture, replay_scenario

FIXTURES_DIR = Path(__file__).parent.parent.parent / "src" / "sim" / "fixtures"
SCENARIOS_DIR = Path(__file__).parent.parent.parent / "src" / "sim" / "scenarios"


def test_nominal_fixture_produces_start() -> None:
    """Normalbetrieb mit PV-Überschuss → START."""
    result = replay_fixture(FIXTURES_DIR / "state_nominal.json")
    assert result["action"] == "START"
    assert "R1" in result["decision_code"]


def test_safety_fixture_produces_stop() -> None:
    """Übertemperatur → R3-Stop."""
    result = replay_fixture(FIXTURES_DIR / "state_safety_triggered.json")
    assert result["action"] == "STOP"
    assert "R3" in result["decision_code"]


def test_replay_is_deterministic() -> None:
    """Gleiche Fixture → gleiche Decision. Immer."""
    r1 = replay_fixture(FIXTURES_DIR / "state_nominal.json")
    r2 = replay_fixture(FIXTURES_DIR / "state_nominal.json")
    assert r1["action"] == r2["action"]
    assert r1["decision_code"] == r2["decision_code"]


def test_sh1_scenario_replay_consistent() -> None:
    """SH-1 zweimal replayed → identische Entscheidungsfolge."""
    r1 = replay_scenario(SCENARIOS_DIR / "sh1_stable_surplus.csv")
    r2 = replay_scenario(SCENARIOS_DIR / "sh1_stable_surplus.csv")
    for a, b in zip(r1, r2):
        assert a["action"] == b["action"]
        assert a["decision_code"] == b["decision_code"]
