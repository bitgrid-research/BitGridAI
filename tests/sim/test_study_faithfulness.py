"""Tests für die Faithfulness-Vorprüfung."""

from __future__ import annotations

from pathlib import Path

from src.sim.study_faithfulness import (
    check_dir,
    check_text,
    covers_change_condition,
)
from src.sim.study_freeze import freeze_all


def test_contradiction_detected() -> None:
    # STOP-Erklärung, die "läuft" behauptet → widersprüchlich
    assert check_text("Der Miner läuft weiter", "STOP")["action_consistent"] is False
    # STOP korrekt
    assert (
        check_text("Miner gestoppt — Überhitzung", "STOP")["action_consistent"] is True
    )
    # START korrekt
    assert (
        check_text("Überschuss da — Miner läuft", "START")["action_consistent"] is True
    )
    # START, das "gestoppt" behauptet → widersprüchlich
    assert check_text("Miner gestoppt", "START")["action_consistent"] is False


def test_has_number() -> None:
    assert check_text("Überschuss 3,0 kW", "START")["has_number"] is True
    assert check_text("Überschuss vorhanden", "START")["has_number"] is False


def test_change_condition_parity() -> None:
    # A nennt Schwelle 58 %, B trägt sie ebenfalls → Parität erfüllt
    assert covers_change_condition("Ab 58 % legt er los.", "Start ab 58 % Akku") is True
    # B lässt die Schwelle weg → Parität verletzt
    assert (
        covers_change_condition("Der Miner wartet noch.", "Start ab 58 % Akku") is False
    )
    # Dezimalkomma-Schwelle wird erkannt
    assert covers_change_condition("ab 6,0 kW geht es los", "Eco-Start ab 6,0 kW PV")
    # A ohne numerische Änderungsbedingung → nicht prüfbar
    assert covers_change_condition("egal", "") is None


def test_frozen_group_a_all_consistent(tmp_path: Path) -> None:
    freeze_all(tmp_path, ollama_host="")
    results = check_dir(tmp_path)
    assert len(results) == 10
    assert all(r["group_a"]["action_consistent"] for r in results)
    # Gruppe B noch leer → Platzhalter (None)
    assert all(r["group_b"] is None for r in results)
