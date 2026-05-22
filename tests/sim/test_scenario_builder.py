"""
Tests für ScenarioBuilder — Klassifikation, Metadaten, CSV-Schreiben, Bibliothek.

Kein DB-Zugriff in Unit-Tests: classify() und compute_meta() arbeiten auf Dicts.
Integration (write_csv + library) nutzt pytest tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.sim.scenario_builder import (
    ScenarioBuilder,
    classify,
    compute_kpis,
    compute_meta,
)

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _rows(
    pv_w: float = 0.0,
    soc: float = 50.0,
    import_w: float = 0.0,
    export_w: float = 0.0,
    temp_c: float = 65.0,
    n: int = 144,
    offset_start: int = 0,
) -> list[dict[str, Any]]:
    return [
        {
            "timestamp_offset_min": offset_start + i * 10,
            "pv_power_w": pv_w,
            "house_load_w": 600.0,
            "grid_import_w": import_w,
            "grid_export_w": export_w,
            "battery_soc_pct": soc,
            "miner_temp_c": temp_c,
            "miner_power_w": None,
            "heizstab_power_w": None,
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# classify()
# ---------------------------------------------------------------------------


def test_classify_night_only() -> None:
    rows = _rows(pv_w=0.0)
    tags = classify(rows)
    assert "night_only" in tags
    assert "sunny_high" not in tags


def test_classify_sunny_high() -> None:
    # PV-Peak > 7 kW, kein Netzbezug → sunny_high
    rows = _rows(pv_w=8000.0, import_w=0.0)
    tags = classify(rows)
    assert "sunny_high" in tags
    assert "night_only" not in tags


def test_classify_sunny_high_blocked_by_import() -> None:
    # Peak > 7 kW aber hoher Import → kein sunny_high (Import >= 1 kWh)
    # 144 Blöcke × 100W = 144 × 100 × 10 / 60000 = 2.4 kWh Import
    rows = _rows(pv_w=8000.0, import_w=100.0)
    tags = classify(rows)
    assert "sunny_high" not in tags
    assert "sunny_low" in tags


def test_classify_sunny_low() -> None:
    rows = _rows(pv_w=5000.0, import_w=0.0)
    tags = classify(rows)
    assert "sunny_low" in tags
    assert "sunny_high" not in tags


def test_classify_cloudy() -> None:
    rows = _rows(pv_w=1500.0)
    tags = classify(rows)
    assert "cloudy" in tags


def test_classify_stress_soc() -> None:
    rows = _rows(pv_w=8000.0, soc=50.0)
    # Einen Block mit kritischem SoC einbauen
    rows[10]["battery_soc_pct"] = 15.0
    tags = classify(rows)
    assert "stress_soc" in tags
    assert "sunny_high" in tags  # beide Tags gleichzeitig möglich


def test_classify_stress_overtemp() -> None:
    rows = _rows(pv_w=5000.0, temp_c=65.0)
    rows[50]["miner_temp_c"] = 90.0
    tags = classify(rows)
    assert "stress_overtemp" in tags


def test_classify_grid_heavy() -> None:
    # 144 Blöcke × 350W Import = 144 × 350 × 10 / 60000 = 8.4 kWh > 5 kWh
    rows = _rows(pv_w=0.0, import_w=350.0)
    tags = classify(rows)
    assert "grid_heavy" in tags
    assert "night_only" in tags  # auch night_only, da kein PV


def test_classify_no_duplicate_primary_tags() -> None:
    rows = _rows(pv_w=8000.0)
    tags = classify(rows)
    primary = [
        t for t in tags if t in ("night_only", "sunny_high", "sunny_low", "cloudy")
    ]
    assert len(primary) == 1


# ---------------------------------------------------------------------------
# compute_meta()
# ---------------------------------------------------------------------------


def test_compute_meta_fields_present() -> None:
    rows = _rows(pv_w=5000.0, soc=60.0)
    meta = compute_meta(rows, "2026-05-15", ["sunny_low"])
    assert meta["date"] == "2026-05-15"
    assert meta["tags"] == ["sunny_low"]
    assert meta["pv_peak_kw"] == pytest.approx(5.0)
    assert meta["min_soc_pct"] == pytest.approx(60.0)
    assert meta["blocks_total"] == 144
    assert meta["blocks_filled"] == 144


def test_compute_meta_empty_pv() -> None:
    rows = _rows(pv_w=0.0)
    meta = compute_meta(rows, "2026-01-01", ["night_only"])
    assert meta["pv_peak_kw"] == 0.0
    assert meta["pv_energy_kwh"] == 0.0


def test_compute_meta_grid_import_kwh() -> None:
    # 144 Blöcke × 1000W = 24 kWh
    rows = _rows(import_w=1000.0)
    meta = compute_meta(rows, "2026-01-01", ["night_only"])
    assert meta["grid_import_kwh"] == pytest.approx(24.0, rel=0.01)


# ---------------------------------------------------------------------------
# ScenarioBuilder — CSV schreiben + Bibliothek (kein DB)
# ---------------------------------------------------------------------------


def test_write_csv_creates_file(tmp_path: Path) -> None:
    builder = ScenarioBuilder(
        scenarios_dir=tmp_path, library_path=tmp_path / "library.json"
    )
    rows = _rows(pv_w=6000.0, soc=70.0)
    meta = compute_meta(rows, "2026-05-10", ["sunny_low"])
    path = builder._write_csv(rows, meta)

    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "# scenario_builder: 1.0" in content
    assert "# date: 2026-05-10" in content
    assert "# tags: sunny_low" in content


def test_write_csv_readable_by_loader(tmp_path: Path) -> None:
    from src.sim.scenario_loader import load_csv_scenario

    builder = ScenarioBuilder(
        scenarios_dir=tmp_path, library_path=tmp_path / "library.json"
    )
    rows = _rows(pv_w=4000.0, soc=80.0, n=6)
    meta = compute_meta(rows, "2026-05-11", ["sunny_low"])
    path = builder._write_csv(rows, meta)

    loaded = load_csv_scenario(path)
    assert len(loaded) == 6
    assert loaded[0]["pv_power_w"] == pytest.approx(4000.0)


def test_update_library_creates_entry(tmp_path: Path) -> None:
    lib = tmp_path / "library.json"
    builder = ScenarioBuilder(scenarios_dir=tmp_path, library_path=lib)
    rows = _rows(pv_w=8000.0)
    meta = compute_meta(rows, "2026-05-12", ["sunny_high"])
    path = builder._write_csv(rows, meta)
    builder._update_library(meta, path)

    data = json.loads(lib.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["date"] == "2026-05-12"
    assert "sunny_high" in data[0]["tags"]


def test_update_library_replaces_existing(tmp_path: Path) -> None:
    lib = tmp_path / "library.json"
    builder = ScenarioBuilder(scenarios_dir=tmp_path, library_path=lib)

    rows = _rows(pv_w=5000.0)
    meta1 = compute_meta(rows, "2026-05-12", ["sunny_low"])
    path1 = builder._write_csv(rows, meta1)
    builder._update_library(meta1, path1)

    meta2 = compute_meta(rows, "2026-05-12", ["sunny_high"])
    builder._update_library(meta2, path1)

    data = json.loads(lib.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert "sunny_high" in data[0]["tags"]


def test_list_scenarios_empty(tmp_path: Path) -> None:
    builder = ScenarioBuilder(
        scenarios_dir=tmp_path, library_path=tmp_path / "library.json"
    )
    assert builder.list_scenarios() == []


# ---------------------------------------------------------------------------
# compute_kpis()
# ---------------------------------------------------------------------------


def _make_replay_result(action: str, decision_code: str = "") -> dict[str, Any]:
    return {"action": action, "decision_code": decision_code, "reason": ""}


def test_kpi_perfect_utilization() -> None:
    # Miner läuft immer wenn Überschuss vorhanden
    rows = _rows(
        pv_w=3000.0, export_w=500.0
    )  # surplus = 3000-600 = 2400W = 2.4kW ≥ 1.5
    replay = [_make_replay_result("START", "START_R1_SURPLUS_OK")] * 144
    kpis = compute_kpis(rows, replay, surplus_min_kw=1.5)
    assert kpis["window_utilization_pct"] == pytest.approx(100.0)
    assert kpis["lost_surplus_kwh"] == pytest.approx(0.0)
    assert kpis["r5_hit_rate_pct"] == pytest.approx(0.0)


def test_kpi_no_surplus_window() -> None:
    # Kein Überschuss → kein Fenster → Ausnutzung 0
    rows = _rows(pv_w=0.0)
    replay = [_make_replay_result("STOP", "NOOP_R1_INSUFFICIENT_SURPLUS")] * 144
    kpis = compute_kpis(rows, replay, surplus_min_kw=1.5)
    assert kpis["surplus_window_blocks"] == 0
    assert kpis["window_utilization_pct"] == pytest.approx(0.0)


def test_kpi_lost_surplus_when_stopped() -> None:
    # Miner immer AUS, aber Export vorhanden → verlorener Überschuss
    # 144 Blöcke × 1000W Export × 10min / 60000 = 24 kWh
    rows = _rows(pv_w=2000.0, export_w=1000.0)
    replay = [_make_replay_result("STOP")] * 144
    kpis = compute_kpis(rows, replay)
    assert kpis["lost_surplus_kwh"] == pytest.approx(24.0, rel=0.01)


def test_kpi_r5_hit_rate() -> None:
    # 48 von 144 Blöcken sind NOOP_R5 → 33.3%
    rows = _rows(pv_w=3000.0)
    replay = [_make_replay_result("START", "START_R1_SURPLUS_OK")] * 96 + [
        _make_replay_result("NOOP", "NOOP_R5_DEADBAND_ACTIVE")
    ] * 48
    kpis = compute_kpis(rows, replay, surplus_min_kw=1.5)
    assert kpis["r5_hits"] == 48
    assert kpis["r5_hit_rate_pct"] == pytest.approx(33.3, abs=0.1)


def test_kpi_noop_continues_running() -> None:
    # START, dann NOOP — Miner läuft weiter, keine Verluste
    rows = _rows(pv_w=3000.0, export_w=200.0)
    replay = (
        [_make_replay_result("START", "START_R1_SURPLUS_OK")] * 10
        + [_make_replay_result("NOOP", "NOOP_R5_MIN_RUNTIME_NOT_REACHED")] * 10
        + [_make_replay_result("STOP")] * 124
    )
    kpis = compute_kpis(rows, replay, surplus_min_kw=1.5)
    assert kpis["mining_in_window_blocks"] == 20  # START + NOOP beide laufen
    assert kpis["lost_surplus_kwh"] == pytest.approx(
        124 * 200.0 * 10 / 60_000, rel=0.01
    )


def test_kpi_partial_window() -> None:
    # Nur erste 72 Blöcke haben Überschuss, Rest nicht
    rows = _rows(pv_w=3000.0, n=72) + _rows(pv_w=0.0, n=72, offset_start=720)
    replay = [_make_replay_result("START", "START_R1_SURPLUS_OK")] * 72 + [
        _make_replay_result("STOP")
    ] * 72
    kpis = compute_kpis(rows, replay, surplus_min_kw=1.5)
    assert kpis["surplus_window_blocks"] == 72
    assert kpis["mining_in_window_blocks"] == 72
    assert kpis["window_utilization_pct"] == pytest.approx(100.0)
    assert kpis["total_blocks"] == 144


def test_list_scenarios_filter_by_tag(tmp_path: Path) -> None:
    lib = tmp_path / "library.json"
    builder = ScenarioBuilder(scenarios_dir=tmp_path, library_path=lib)

    for date, pv, tags in [
        ("2026-05-01", 8000.0, ["sunny_high"]),
        ("2026-05-02", 0.0, ["night_only"]),
        ("2026-05-03", 5000.0, ["sunny_low"]),
    ]:
        rows = _rows(pv_w=pv)
        meta = compute_meta(rows, date, tags)
        path = builder._write_csv(rows, meta)
        builder._update_library(meta, path)

    sunny = builder.list_scenarios(tag="sunny_high")
    assert len(sunny) == 1
    assert sunny[0]["date"] == "2026-05-01"

    all_entries = builder.list_scenarios()
    assert len(all_entries) == 3
