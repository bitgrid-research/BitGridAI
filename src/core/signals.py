"""
Signal — kanonische Signal-Namen als typsicheres Enum.

Alle Adapter, TelemetryIngest und EnergyContext verwenden ausschließlich
diese Konstanten — keine Magic Strings mehr.

Da Signal(str, Enum), sind Instanzen direkt als dict-Keys und
als Argumente für TelemetryIngest.update() verwendbar.
"""

from __future__ import annotations

from enum import Enum


class Signal(str, Enum):
    """Kanonische Signal-Namen der BitGridAI-Domain."""

    # Energie — Pflichtfelder in EnergyState
    PV_POWER_W = "pv_power_w"
    HOUSE_LOAD_W = "house_load_w"
    GRID_IMPORT_W = "grid_import_w"
    GRID_EXPORT_W = "grid_export_w"
    BATTERY_SOC_PCT = "battery_soc_pct"

    # Miner — Pflichtfelder in EnergyState
    MINER_TEMP_C = "miner_temp_c"
    MINER_HEARTBEAT_AGE_SEC = "miner_heartbeat_age_sec"

    # Miner — optionale Metriken (nicht in EnergyState required)
    MINER_POWER_W = "miner_power_w"
    MINER_HASHRATE_TH = "miner_hashrate_th"
    MINER_HASHRATE_GH = "miner_hashrate_gh"

    # Markt — optionale Felder in EnergyState
    ENERGY_PRICE_CT_KWH = "energy_price_ct_kwh"
    PV_FORECAST_KW = "pv_forecast_kw"


# Pflichtfelder für EnergyState — als geordnetes Tuple für Validierung
REQUIRED_SIGNALS: tuple[Signal, ...] = (
    Signal.PV_POWER_W,
    Signal.HOUSE_LOAD_W,
    Signal.GRID_IMPORT_W,
    Signal.BATTERY_SOC_PCT,
    Signal.MINER_TEMP_C,
    Signal.MINER_HEARTBEAT_AGE_SEC,
)
