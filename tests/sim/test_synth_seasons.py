"""Tests für die synthetischen Saison-Profile (Determinismus + Saison-Gradient)."""

from __future__ import annotations

from src.sim.synth_seasons import SEASONS, generate_day


def test_deterministic() -> None:
    a = generate_day(SEASONS["sommer"])
    b = generate_day(SEASONS["sommer"])
    assert a == b
    assert len(a) == 144


def test_season_gradient_pv() -> None:
    peak = {
        s: max(float(r["pv_power_w"]) for r in generate_day(p))
        for s, p in SEASONS.items()
    }
    assert peak["sommer"] > peak["fruehling"] > peak["herbst"] > peak["winter"]


def test_soc_stays_in_bounds() -> None:
    for p in SEASONS.values():
        soc = [float(r["battery_soc_pct"]) for r in generate_day(p)]
        assert min(soc) >= 0.0
        assert max(soc) <= 100.0


def test_grid_import_only_when_battery_empty() -> None:
    rows = generate_day(SEASONS["winter"])
    for r in rows:
        if float(r["grid_import_w"]) > 0:
            assert float(r["battery_soc_pct"]) == 0.0
