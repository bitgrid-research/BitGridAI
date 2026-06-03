"""
Tests für scenario_miner — Mapping decision_code → Studien-Szenario + Mining.

Match-Prädikate werden direkt geprüft; mine_files/freeze_window via tmp_path-CSV.
"""

from __future__ import annotations

from pathlib import Path

from src.sim.scenario_loader import load_csv_scenario
from src.sim.scenario_miner import (
    SCENARIO_SPECS,
    freeze_window,
    mine_files,
)


def _spec(scenario_id: str):  # type: ignore[no-untyped-def]
    return next(s for s in SCENARIO_SPECS if s.scenario_id == scenario_id)


# ---------------------------------------------------------------------------
# Match-Prädikate
# ---------------------------------------------------------------------------


def test_match_predicates_unique() -> None:
    cases = {
        "START_R1_SURPLUS_OK": "S1",
        "NOOP_R1_INSUFFICIENT_SURPLUS": "S2",
        "NOOP_R1_PRICE_TOO_HIGH": "S3",
        "STOP_R3_OVERTEMP_T90": "S4",
        "STOP_R3_COMM_TIMEOUT_AGE75": "S5",
        "NOOP_R2_SOC_SOFT_MIN": "S6",
        "STOP_R2_SOC_HARD_MIN": "S7",
        "STOP_R2_GRID_IMPORT_EXCEEDED": "S8",
        "NOOP_R4_FORECAST_PV_INSUFFICIENT": "S9",
        "NOOP_R5_MIN_RUNTIME_NOT_REACHED": "S10",
    }
    for code, expected_id in cases.items():
        hits = [s.scenario_id for s in SCENARIO_SPECS if s.match(code)]
        assert hits == [expected_id], f"{code} → {hits}"


def test_injection_only_flags() -> None:
    assert _spec("S4").injection_only
    assert _spec("S5").injection_only
    assert not _spec("S1").injection_only


# ---------------------------------------------------------------------------
# mine_files — Integration
# ---------------------------------------------------------------------------


def _write_day(path: Path) -> None:
    """Erzeugt einen Mini-Tag, der S1, S2 und S10 deterministisch produziert."""
    lines = ["# date: 2026-06-21", "# header"]
    # 4 Blöcke voller Überschuss ab 10:00 (Block 0 → START=S1, danach R5-NOOP=S10)
    for k in range(4):
        offset = 600 + k * 10
        lines.append(f"{offset},4500.00,1500.00,0.00,80.00,45.00,5.0,13.0,4.0,,,")
    # 4 Blöcke ohne Überschuss (nach Deadband → NOOP_R1_INSUFFICIENT=S2)
    for k in range(4):
        offset = 640 + k * 10
        lines.append(f"{offset},1700.00,1500.00,0.00,80.00,45.00,5.0,13.0,4.0,,,")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_mine_finds_real_blocks(tmp_path: Path) -> None:
    csv = tmp_path / "real_2026-06-21.csv"
    _write_day(csv)

    matches = mine_files([csv])

    s1 = matches["S1"]
    assert s1.found
    assert s1.decision_code == "START_R1_SURPLUS_OK"
    assert s1.state["surplus_kw"] == 3.0
    assert s1.date == "2026-06-21"
    assert s1.time_of_day() == "10:00"

    assert matches["S2"].found
    assert matches["S2"].decision_code == "NOOP_R1_INSUFFICIENT_SURPLUS"
    assert matches["S10"].found  # R5-NOOP

    # Fault-Szenarien tauchen in sauberen Daten nicht auf
    assert not matches["S4"].found
    assert not matches["S5"].found


def test_freeze_window_rebases_offsets(tmp_path: Path) -> None:
    csv = tmp_path / "real_2026-06-21.csv"
    _write_day(csv)
    matches = mine_files([csv])

    out_dir = tmp_path / "study_set"
    frozen = freeze_window(matches["S2"], [csv], window=2, out_dir=out_dir)
    assert frozen is not None
    assert frozen.exists()

    rows = load_csv_scenario(frozen)
    # Fenster = 2 Vorblöcke + Repräsentant
    assert len(rows) == 3
    # Offsets neu basiert ab 0
    assert [r["timestamp_offset_min"] for r in rows] == [0, 10, 20]
