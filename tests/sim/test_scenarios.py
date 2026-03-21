"""
Szenario-Tests — CSV-Szenarien durch den Core laufen lassen.

Prüft die erwartete Entscheidungsfolge pro Szenario.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.sim.replay import replay_scenario

SCENARIOS_DIR = Path(__file__).parent.parent.parent / "src" / "sim" / "scenarios"


def test_sh1_starts_with_surplus() -> None:
    """SH-1: Stabiler Überschuss → erster Block muss START sein."""
    results = replay_scenario(SCENARIOS_DIR / "sh1_stable_surplus.csv")
    assert len(results) > 0
    assert results[0]["action"] == "START"


def test_sh3_stops_when_soc_critical() -> None:
    """SH-3: SoC unter Hard-Min → irgendwann STOP wegen R2."""
    results = replay_scenario(SCENARIOS_DIR / "sh3_soc_critical.csv")
    actions = [r["action"] for r in results]
    assert "STOP" in actions


def test_sh4_safety_stop_when_overtemp() -> None:
    """SH-4: Übertemperatur → R3-Stop muss auftreten."""
    results = replay_scenario(SCENARIOS_DIR / "sh4_safety_overtemp.csv")
    r3_stops = [r for r in results if "R3" in r.get("decision_code", "")]
    assert len(r3_stops) > 0
