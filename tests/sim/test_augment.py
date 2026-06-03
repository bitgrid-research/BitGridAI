"""
Tests für augment — Tarifmodell + Perfect-Foresight-Forecast.

Reine Funktionen auf Row-Dicts; CSV-Roundtrip via tmp_path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.sim.augment import (
    apply_perfect_forecast,
    apply_tariff,
    augment_file,
    tariff_ct_kwh,
)
from src.sim.scenario_loader import load_csv_scenario


def _row(offset: int, pv: float = 0.0, load: float = 1000.0) -> dict[str, Any]:
    return {
        "timestamp_offset_min": offset,
        "pv_power_w": pv,
        "house_load_w": load,
        "grid_import_w": 0.0,
        "battery_soc_pct": 50.0,
        "miner_temp_c": 45.0,
        "miner_heartbeat_age_sec": 5.0,
        "energy_price_ct_kwh": None,
        "pv_forecast_kw": None,
        "grid_export_w": None,
        "miner_power_w": None,
        "heizstab_power_w": None,
    }


# ---------------------------------------------------------------------------
# tariff_ct_kwh — Tageszeit-Bänder
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "minute_of_day, expected",
    [
        (3 * 60, 18.0),  # 03:00 Nacht
        (8 * 60, 24.0),  # 08:00 Morgen
        (10 * 60 + 30, 13.0),  # 10:30 PV-Mittag
        (16 * 60 + 30, 22.0),  # 16:30 Übergang
        (17 * 60 + 30, 29.0),  # 17:30 Abend-Spitze
        (22 * 60, 21.0),  # 22:00 später Abend
    ],
)
def test_tariff_bands(minute_of_day: int, expected: float) -> None:
    assert tariff_ct_kwh(minute_of_day) == expected


def test_tariff_wraps_over_midnight() -> None:
    # 1500 min = 25:00 → 01:00 nach Modulo → Nachtband
    assert tariff_ct_kwh(25 * 60) == 18.0


# ---------------------------------------------------------------------------
# apply_tariff
# ---------------------------------------------------------------------------


def test_apply_tariff_fills_empty() -> None:
    rows = [_row(10 * 60 + 30), _row(17 * 60 + 30)]
    n = apply_tariff(rows)
    assert n == 2
    assert rows[0]["energy_price_ct_kwh"] == 13.0
    assert rows[1]["energy_price_ct_kwh"] == 29.0


def test_apply_tariff_respects_existing() -> None:
    rows = [_row(10 * 60 + 30)]
    rows[0]["energy_price_ct_kwh"] = 99.0
    n = apply_tariff(rows)
    assert n == 0
    assert rows[0]["energy_price_ct_kwh"] == 99.0


def test_apply_tariff_overwrite() -> None:
    rows = [_row(10 * 60 + 30)]
    rows[0]["energy_price_ct_kwh"] = 99.0
    n = apply_tariff(rows, overwrite=True)
    assert n == 1
    assert rows[0]["energy_price_ct_kwh"] == 13.0


# ---------------------------------------------------------------------------
# apply_perfect_forecast
# ---------------------------------------------------------------------------


def test_perfect_forecast_mean_of_next_blocks() -> None:
    rows = [_row(i * 10, pv=p) for i, p in enumerate([1000, 2000, 3000, 4000])]
    apply_perfect_forecast(rows, horizon_blocks=2)
    # Block 0 sieht Folgeblöcke 2000, 3000 → Mittel 2500 W = 2.5 kW
    assert rows[0]["pv_forecast_kw"] == 2.5
    # Block 1 sieht 3000, 4000 → 3.5 kW
    assert rows[1]["pv_forecast_kw"] == 3.5


def test_perfect_forecast_end_fallback_to_current() -> None:
    rows = [_row(0, pv=1000), _row(10, pv=2000)]
    apply_perfect_forecast(rows, horizon_blocks=3)
    # Letzter Block hat keine Folgeblöcke → Fallback auf aktuelle PV (2.0 kW)
    assert rows[1]["pv_forecast_kw"] == 2.0


def test_perfect_forecast_horizon_validation() -> None:
    with pytest.raises(ValueError):
        apply_perfect_forecast([_row(0)], horizon_blocks=0)


def test_perfect_forecast_detects_incoming_crash() -> None:
    # Hohe PV jetzt, Einbruch in den Folgeblöcken → Forecast < R4-Schwelle (2.0)
    rows = [_row(0, pv=4000), _row(10, pv=500), _row(20, pv=400), _row(30, pv=300)]
    apply_perfect_forecast(rows, horizon_blocks=3)
    assert rows[0]["pv_forecast_kw"] < 2.0


# ---------------------------------------------------------------------------
# augment_file — CSV-Roundtrip
# ---------------------------------------------------------------------------


def test_augment_file_roundtrip(tmp_path: Path) -> None:
    src = tmp_path / "real.csv"
    src.write_text(
        "# date: 2026-06-21\n"
        "# timestamp_offset_min, pv_power_w, house_load_w, ...\n"
        "630,4500.00,1500.00,0.00,80.00,45.00,5.0,,,,,\n"  # 10:30
        "1050,4000.00,1500.00,0.00,70.00,45.00,5.0,,,,,\n"  # 17:30
        "1060,200.00,1500.00,0.00,70.00,45.00,5.0,,,,,\n",  # 17:40
        encoding="utf-8",
    )
    out = tmp_path / "aug.csv"
    n_price, n_forecast = augment_file(src, out, horizon_blocks=6)

    assert n_price == 3
    assert n_forecast == 3
    rows = load_csv_scenario(out)
    assert (
        rows[0]["energy_price_ct_kwh"] == 13.0
    )  # 10:30 → günstig → würde Start erlauben
    assert rows[1]["energy_price_ct_kwh"] == 29.0  # 17:30 → teuer → R1 PRICE_TOO_HIGH
    # Kommentar-Header bleibt erhalten
    assert out.read_text(encoding="utf-8").startswith("# date: 2026-06-21")
