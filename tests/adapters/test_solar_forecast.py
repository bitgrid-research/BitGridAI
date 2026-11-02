"""
Unit-Tests für die lokale, deterministische Sonnenstand-Prognose (Option A).

Invarianten:
- Elevation positiv um den Sonnenhöchststand, negativ nachts (Sonne unter Horizont)
- Klarhimmel-PV: 0 unter dem Horizont, monoton in der Elevation, <= kWp*PR
- Determinismus: gleicher (Ort, Zeit, kWp) → gleicher Wert (replay-fähig)
- Abend < Mittag (der für R4 relevante Flap-Fall)
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.solar_forecast import (
    clear_sky_pv_kw,
    forecast_pv_kw,
    solar_elevation_deg,
)

# München, Sommersonnenwende — Referenzort/-tag mit hohem Sonnenstand.
_LAT, _LON = 48.1, 11.6
_NOON = datetime(2026, 6, 21, 11, 30, tzinfo=timezone.utc)  # nahe Sonnenhöchststand
_MIDNIGHT = datetime(2026, 6, 21, 0, 0, tzinfo=timezone.utc)
_EVENING = datetime(2026, 6, 21, 18, 0, tzinfo=timezone.utc)


def test_elevation_high_at_solar_noon_summer() -> None:
    """Zur Sonnenwende erreicht München mittags ~65° Elevation."""
    elev = solar_elevation_deg(_LAT, _LON, _NOON)
    assert elev > 60.0


def test_elevation_negative_at_midnight() -> None:
    """Mitternacht: Sonne deutlich unter dem Horizont."""
    assert solar_elevation_deg(_LAT, _LON, _MIDNIGHT) < 0.0


def test_clear_sky_zero_below_horizon() -> None:
    assert clear_sky_pv_kw(-5.0, 10.0) == 0.0
    assert clear_sky_pv_kw(0.0, 10.0) == 0.0


def test_clear_sky_monotonic_and_capped() -> None:
    low = clear_sky_pv_kw(10.0, 10.0)
    high = clear_sky_pv_kw(60.0, 10.0)
    assert 0.0 < low < high <= 10.0 * 0.75


def test_forecast_deterministic() -> None:
    a = forecast_pv_kw(_LAT, _LON, _NOON, 10.0)
    b = forecast_pv_kw(_LAT, _LON, _NOON, 10.0)
    assert a == b


def test_forecast_evening_below_noon() -> None:
    """Abend-PV-Obergrenze liegt unter der Mittags-Obergrenze (Flap-Fall)."""
    noon = forecast_pv_kw(_LAT, _LON, _NOON, 10.0)
    evening = forecast_pv_kw(_LAT, _LON, _EVENING, 10.0)
    assert evening < noon


def test_naive_datetime_treated_as_utc() -> None:
    """Naiver Zeitstempel wird als UTC interpretiert (kein Crash, gleiches Ergebnis)."""
    naive = datetime(2026, 6, 21, 11, 30)
    aware = datetime(2026, 6, 21, 11, 30, tzinfo=timezone.utc)
    assert forecast_pv_kw(_LAT, _LON, naive, 10.0) == forecast_pv_kw(
        _LAT, _LON, aware, 10.0
    )
