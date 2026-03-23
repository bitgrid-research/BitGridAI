"""
Unit-Tests für EnergyContext.

Abgedeckt:
  build_energy_state()  — surplus, quality, safe defaults, optionale Felder
  _derive_house_load()  — Energiebilanz-Fallback
  raw_from_ingest()     — Brücke TelemetryIngest → RawMeasurements
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.adapters.telemetry_ingest import TelemetryIngest
from src.core.energy_context import RawMeasurements, build_energy_state, raw_from_ingest
from src.core.signals import Signal

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _window() -> tuple[datetime, datetime]:
    start = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 15, 10, 10, tzinfo=timezone.utc)
    return start, end


def _full_raw(**overrides) -> RawMeasurements:
    """Vollständige RawMeasurements — einzelne Felder überschreibbar."""
    defaults = dict(
        pv_power_w=3000.0,
        house_load_w=800.0,
        grid_import_w=0.0,
        battery_soc_pct=80.0,
        miner_temp_c=42.0,
        miner_heartbeat_age_sec=5.0,
    )
    defaults.update(overrides)
    return RawMeasurements(**defaults)


def _build(**overrides):
    start, end = _window()
    return build_energy_state("2024-01-15T10:00:00", start, end, _full_raw(**overrides))


def _ingest_with(**signals: float) -> TelemetryIngest:
    ingest = TelemetryIngest(stale_threshold_sec=60.0)
    mapping = {
        "pv_power_w": Signal.PV_POWER_W,
        "house_load_w": Signal.HOUSE_LOAD_W,
        "grid_import_w": Signal.GRID_IMPORT_W,
        "grid_export_w": Signal.GRID_EXPORT_W,
        "battery_soc_pct": Signal.BATTERY_SOC_PCT,
        "miner_temp_c": Signal.MINER_TEMP_C,
        "miner_heartbeat_age_sec": Signal.MINER_HEARTBEAT_AGE_SEC,
        "miner_power_w": Signal.MINER_POWER_W,
        "energy_price_ct_kwh": Signal.ENERGY_PRICE_CT_KWH,
        "pv_forecast_kw": Signal.PV_FORECAST_KW,
    }
    for name, value in signals.items():
        ingest.update(mapping[name], value, source="test")
    return ingest


# ---------------------------------------------------------------------------
# build_energy_state — Surplus
# ---------------------------------------------------------------------------


class TestSurplus:
    def test_surplus_calculated_correctly(self) -> None:
        state = _build(pv_power_w=3000.0, house_load_w=800.0)
        assert state.surplus_kw == pytest.approx(2.2, abs=0.01)

    def test_surplus_negative_when_no_pv(self) -> None:
        state = _build(pv_power_w=0.0, house_load_w=800.0)
        assert state.surplus_kw < 0

    def test_surplus_zero_at_break_even(self) -> None:
        state = _build(pv_power_w=1000.0, house_load_w=1000.0)
        assert state.surplus_kw == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# build_energy_state — Datenqualität
# ---------------------------------------------------------------------------


class TestQuality:
    def test_all_signals_present_quality_ok(self) -> None:
        state = _build()
        assert state.quality == "ok"
        assert state.missing_signals == ()

    def test_one_missing_signal_quality_warn(self) -> None:
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=3000.0,
            house_load_w=800.0,
            grid_import_w=None,  # fehlt
            battery_soc_pct=80.0,
            miner_temp_c=42.0,
            miner_heartbeat_age_sec=5.0,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        assert state.quality == "warn"
        assert "grid_import_w" in state.missing_signals

    def test_many_missing_signals_quality_error(self) -> None:
        start, end = _window()
        state = build_energy_state("2024-01-15T10:00:00", start, end, RawMeasurements())
        assert state.quality == "error"
        assert len(state.missing_signals) > 2


# ---------------------------------------------------------------------------
# build_energy_state — Safe Defaults
# ---------------------------------------------------------------------------


class TestSafeDefaults:
    def test_missing_temp_defaults_to_999(self) -> None:
        """Fehlende Temperatur → 999°C → R3 greift immer."""
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=3000.0,
            house_load_w=800.0,
            grid_import_w=0.0,
            battery_soc_pct=80.0,
            miner_temp_c=None,
            miner_heartbeat_age_sec=5.0,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        assert state.miner_temp_c == 999.0

    def test_missing_heartbeat_defaults_to_9999(self) -> None:
        """Fehlender Heartbeat → 9999s → R3 Comm-Timeout greift."""
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=3000.0,
            house_load_w=800.0,
            grid_import_w=0.0,
            battery_soc_pct=80.0,
            miner_temp_c=42.0,
            miner_heartbeat_age_sec=None,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        assert state.miner_heartbeat_age_sec == 9999.0

    def test_missing_pv_defaults_to_zero(self) -> None:
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=None,
            house_load_w=800.0,
            grid_import_w=0.0,
            battery_soc_pct=80.0,
            miner_temp_c=42.0,
            miner_heartbeat_age_sec=5.0,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        assert state.pv_power_w == 0.0

    def test_optional_fields_passed_through(self) -> None:
        state = _build()
        start, end = _window()
        raw = _full_raw()
        raw.energy_price_ct_kwh = 18.5
        raw.pv_forecast_kw = 3.2
        raw.grid_export_w = 500.0
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        assert state.energy_price_ct_kwh == 18.5
        assert state.pv_forecast_kw == 3.2
        assert state.grid_export_w == 500.0

    def test_optional_fields_none_by_default(self) -> None:
        state = _build()
        assert state.energy_price_ct_kwh is None
        assert state.pv_forecast_kw is None


# ---------------------------------------------------------------------------
# _derive_house_load — Energiebilanz-Fallback
# ---------------------------------------------------------------------------


class TestDeriveHouseLoad:
    def test_derived_from_pv_import_export_miner(self) -> None:
        """house_load = pv + import - export - miner"""
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=5000.0,
            house_load_w=None,  # nicht direkt gemessen
            grid_import_w=0.0,
            grid_export_w=500.0,
            battery_soc_pct=80.0,
            miner_temp_c=42.0,
            miner_heartbeat_age_sec=5.0,
            miner_power_w=1500.0,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        # 5000 + 0 - 500 - 1500 = 3000W
        assert state.house_load_w == pytest.approx(3000.0)
        assert "house_load_w" not in state.missing_signals

    def test_derived_without_miner_power(self) -> None:
        """Ohne miner_power_w → miner_power wird als 0 behandelt."""
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=4000.0,
            house_load_w=None,
            grid_import_w=200.0,
            grid_export_w=0.0,
            battery_soc_pct=80.0,
            miner_temp_c=42.0,
            miner_heartbeat_age_sec=5.0,
            miner_power_w=None,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        # 4000 + 200 - 0 - 0 = 4200W
        assert state.house_load_w == pytest.approx(4200.0)

    def test_derived_house_load_never_negative(self) -> None:
        """Negative Werte werden auf 0 geclampst."""
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=1000.0,
            house_load_w=None,
            grid_import_w=0.0,
            grid_export_w=2000.0,  # mehr Export als PV → würde negativ
            battery_soc_pct=80.0,
            miner_temp_c=42.0,
            miner_heartbeat_age_sec=5.0,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        assert state.house_load_w >= 0.0

    def test_direct_measurement_takes_priority(self) -> None:
        """Direkt gemessenes house_load_w wird nicht überschrieben."""
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=5000.0,
            house_load_w=700.0,  # direkt gemessen
            grid_import_w=0.0,
            grid_export_w=1000.0,
            battery_soc_pct=80.0,
            miner_temp_c=42.0,
            miner_heartbeat_age_sec=5.0,
            miner_power_w=2000.0,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        assert state.house_load_w == pytest.approx(700.0)

    def test_fallback_not_possible_without_pv(self) -> None:
        """Ohne pv_power_w kann house_load_w nicht abgeleitet werden → fehlt."""
        start, end = _window()
        raw = RawMeasurements(
            pv_power_w=None,
            house_load_w=None,
            grid_import_w=500.0,
            battery_soc_pct=80.0,
            miner_temp_c=42.0,
            miner_heartbeat_age_sec=5.0,
        )
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)
        assert "house_load_w" in state.missing_signals


# ---------------------------------------------------------------------------
# raw_from_ingest — Brücke TelemetryIngest → RawMeasurements
# ---------------------------------------------------------------------------


class TestRawFromIngest:
    def test_all_signals_mapped(self) -> None:
        ingest = _ingest_with(
            pv_power_w=3000,
            house_load_w=800,
            grid_import_w=0,
            battery_soc_pct=80,
            miner_temp_c=65,
            miner_heartbeat_age_sec=5,
        )
        raw = raw_from_ingest(ingest)
        assert raw.pv_power_w == pytest.approx(3000.0)
        assert raw.house_load_w == pytest.approx(800.0)
        assert raw.miner_temp_c == pytest.approx(65.0)

    def test_empty_ingest_returns_all_none(self) -> None:
        ingest = TelemetryIngest()
        raw = raw_from_ingest(ingest)
        assert raw.pv_power_w is None
        assert raw.miner_temp_c is None
        assert raw.battery_soc_pct is None

    def test_optional_signals_mapped(self) -> None:
        ingest = _ingest_with(
            pv_power_w=4000,
            grid_import_w=0,
            battery_soc_pct=80,
            miner_temp_c=65,
            miner_heartbeat_age_sec=5,
            energy_price_ct_kwh=22.5,
            pv_forecast_kw=3.8,
            miner_power_w=1674,
            grid_export_w=200,
        )
        raw = raw_from_ingest(ingest)
        assert raw.energy_price_ct_kwh == pytest.approx(22.5)
        assert raw.pv_forecast_kw == pytest.approx(3.8)
        assert raw.miner_power_w == pytest.approx(1674.0)
        assert raw.grid_export_w == pytest.approx(200.0)

    def test_partial_signals_rest_none(self) -> None:
        ingest = _ingest_with(miner_temp_c=68, miner_heartbeat_age_sec=3)
        raw = raw_from_ingest(ingest)
        assert raw.miner_temp_c == pytest.approx(68.0)
        assert raw.pv_power_w is None
        assert raw.battery_soc_pct is None

    def test_ingest_to_state_pipeline(self) -> None:
        """Vollständiger Pfad: Ingest → RawMeasurements → EnergyState."""
        ingest = _ingest_with(
            pv_power_w=4000,
            house_load_w=600,
            grid_import_w=0,
            battery_soc_pct=85,
            miner_temp_c=67,
            miner_heartbeat_age_sec=8,
        )
        raw = raw_from_ingest(ingest)
        start, end = _window()
        state = build_energy_state("2024-01-15T10:00:00", start, end, raw)

        assert state.quality == "ok"
        assert state.surplus_kw == pytest.approx(3.4, abs=0.01)
        assert state.miner_temp_c == pytest.approx(67.0)
