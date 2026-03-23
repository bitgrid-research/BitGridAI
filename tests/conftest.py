"""
Gemeinsame Fixtures für alle Tests.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.core.models import EnergyState


@pytest.fixture
def nominal_state() -> EnergyState:
    """Normalbetrieb — PV-Überschuss, gute Batterie, normaler Temp."""
    return EnergyState(
        block_id="2024-01-15T10:00:00",
        window_start=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        window_end=datetime(2024, 1, 15, 10, 10, tzinfo=timezone.utc),
        pv_power_w=3200.0,
        house_load_w=800.0,
        grid_import_w=0.0,
        battery_soc_pct=80.0,
        miner_temp_c=42.0,
        miner_heartbeat_age_sec=5.0,
        surplus_kw=2.4,
        quality="ok",
        missing_signals=(),
        energy_price_ct_kwh=8.2,
        pv_forecast_kw=3.1,
    )


@pytest.fixture
def overtemp_state() -> EnergyState:
    """Übertemperatur → R3 muss greifen."""
    return EnergyState(
        block_id="2024-01-15T14:30:00",
        window_start=datetime(2024, 1, 15, 14, 30, tzinfo=timezone.utc),
        window_end=datetime(2024, 1, 15, 14, 40, tzinfo=timezone.utc),
        pv_power_w=3500.0,
        house_load_w=800.0,
        grid_import_w=0.0,
        battery_soc_pct=75.0,
        miner_temp_c=92.0,
        miner_heartbeat_age_sec=5.0,
        surplus_kw=2.7,
        quality="ok",
        missing_signals=(),
    )


@pytest.fixture
def low_soc_state() -> EnergyState:
    """SoC unter Hard-Min → R2 muss greifen."""
    return EnergyState(
        block_id="2024-01-15T20:00:00",
        window_start=datetime(2024, 1, 15, 20, 0, tzinfo=timezone.utc),
        window_end=datetime(2024, 1, 15, 20, 10, tzinfo=timezone.utc),
        pv_power_w=0.0,
        house_load_w=800.0,
        grid_import_w=800.0,
        battery_soc_pct=8.0,
        miner_temp_c=42.0,
        miner_heartbeat_age_sec=5.0,
        surplus_kw=-0.8,
        quality="ok",
        missing_signals=(),
    )


@pytest.fixture
def no_surplus_state() -> EnergyState:
    """Kein PV-Überschuss → R1 NOOP (grid_import unter R2-Schwelle)."""
    return EnergyState(
        block_id="2024-01-15T06:00:00",
        window_start=datetime(2024, 1, 15, 6, 0, tzinfo=timezone.utc),
        window_end=datetime(2024, 1, 15, 6, 10, tzinfo=timezone.utc),
        pv_power_w=400.0,
        house_load_w=700.0,
        grid_import_w=300.0,  # unter R2-Limit (500W)
        battery_soc_pct=60.0,
        miner_temp_c=38.0,
        miner_heartbeat_age_sec=5.0,
        surplus_kw=-0.3,
        quality="ok",
        missing_signals=(),
    )
