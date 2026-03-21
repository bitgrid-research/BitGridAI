"""
EnergyContext — baut EnergyState aus Rohmesswerten auf.

Normalisiert Einheiten, berechnet surplus_kw, bewertet Datenqualität
und markiert fehlende Signale.

house_load_w-Fallback:
  Wenn house_load_w nicht direkt gemessen, wird es aus der Energiebilanz
  berechnet: pv + grid_import - grid_export - miner_power
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from src.adapters.telemetry_ingest import TelemetryIngest
from src.core.models import EnergyState
from src.core.signals import REQUIRED_SIGNALS, Signal


@dataclass
class RawMeasurements:
    """Rohdaten aus Adaptern — None bedeutet Signal fehlt oder noch nicht empfangen."""

    pv_power_w: float | None = None
    house_load_w: float | None = None
    grid_import_w: float | None = None
    grid_export_w: float | None = None
    battery_soc_pct: float | None = None
    miner_temp_c: float | None = None
    miner_heartbeat_age_sec: float | None = None

    # Optionale Felder für EnergyState
    energy_price_ct_kwh: float | None = None
    pv_forecast_kw: float | None = None

    # Hilfsgröße für house_load_w-Berechnung (nicht in EnergyState required)
    miner_power_w: float | None = None


def _derive_house_load(raw: RawMeasurements) -> float | None:
    """
    Berechnet house_load_w aus der Energiebilanz falls nicht direkt gemessen.

    Formel: pv + grid_import - grid_export - miner_power
    Miner-Leistung wird subtrahiert, da house_load_w nur die Basislast enthält
    (Miner ist flexible Last, wird von BitGridAI separat gesteuert).

    Gibt None zurück wenn Pflicht-Eingangssignale fehlen.
    """
    if raw.pv_power_w is None or raw.grid_import_w is None:
        return None

    export = raw.grid_export_w or 0.0
    miner = raw.miner_power_w or 0.0

    computed = raw.pv_power_w + raw.grid_import_w - export - miner
    return max(0.0, computed)  # Basislast kann nicht negativ sein


def raw_from_ingest(ingest: TelemetryIngest) -> RawMeasurements:
    """
    Liest alle Signal-Werte aus TelemetryIngest → RawMeasurements.

    Verbindet Infrastruktur (TelemetryIngest) mit Domain (RawMeasurements).
    Stale oder fehlende Signale landen als None — build_energy_state()
    füllt sie mit sicheren Defaults auf.
    """
    return RawMeasurements(
        pv_power_w=ingest.get_value(Signal.PV_POWER_W),
        house_load_w=ingest.get_value(Signal.HOUSE_LOAD_W),
        grid_import_w=ingest.get_value(Signal.GRID_IMPORT_W),
        grid_export_w=ingest.get_value(Signal.GRID_EXPORT_W),
        battery_soc_pct=ingest.get_value(Signal.BATTERY_SOC_PCT),
        miner_temp_c=ingest.get_value(Signal.MINER_TEMP_C),
        miner_heartbeat_age_sec=ingest.get_value(Signal.MINER_HEARTBEAT_AGE_SEC),
        energy_price_ct_kwh=ingest.get_value(Signal.ENERGY_PRICE_CT_KWH),
        pv_forecast_kw=ingest.get_value(Signal.PV_FORECAST_KW),
        miner_power_w=ingest.get_value(Signal.MINER_POWER_W),
    )


def build_energy_state(
    block_id: str,
    window_start: datetime,
    window_end: datetime,
    raw: RawMeasurements,
) -> EnergyState:
    """
    Baut einen unveränderlichen EnergyState aus Rohmesswerten.

    1. Versucht house_load_w aus Energiebilanz zu berechnen falls fehlend.
    2. Identifiziert fehlende Pflichtfelder.
    3. Füllt fehlende Werte mit sicheren Defaults (hohe Temp → R3 greift).
    4. Bewertet Datenqualität: ok / warn / error.
    """
    # house_load_w ableiten wenn nicht direkt gemessen
    if raw.house_load_w is None:
        raw.house_load_w = _derive_house_load(raw)

    # Fehlende Pflichtfelder bestimmen (via Signal-Enum, keine Magic Strings)
    missing: list[str] = [
        sig.value
        for sig in REQUIRED_SIGNALS
        if getattr(raw, sig.value, None) is None
    ]

    if missing:
        quality: Literal["ok", "warn", "error"] = (
            "error" if len(missing) > 2 else "warn"
        )
        pv = raw.pv_power_w or 0.0
        load = raw.house_load_w or 0.0
        grid = raw.grid_import_w or 0.0
        soc = raw.battery_soc_pct or 0.0
        temp = raw.miner_temp_c or 999.0        # hohe Temp → R3 greift sicher
        age = raw.miner_heartbeat_age_sec or 9999.0  # alter Heartbeat → R3 greift
    else:
        quality = "ok"
        pv = raw.pv_power_w      # type: ignore[assignment]
        load = raw.house_load_w  # type: ignore[assignment]
        grid = raw.grid_import_w  # type: ignore[assignment]
        soc = raw.battery_soc_pct  # type: ignore[assignment]
        temp = raw.miner_temp_c  # type: ignore[assignment]
        age = raw.miner_heartbeat_age_sec  # type: ignore[assignment]

    surplus_kw = (pv - load) / 1000.0

    return EnergyState(
        block_id=block_id,
        window_start=window_start,
        window_end=window_end,
        pv_power_w=pv,
        house_load_w=load,
        grid_import_w=grid,
        battery_soc_pct=soc,
        miner_temp_c=temp,
        miner_heartbeat_age_sec=age,
        surplus_kw=surplus_kw,
        quality=quality,
        missing_signals=tuple(missing),
        grid_export_w=raw.grid_export_w,
        energy_price_ct_kwh=raw.energy_price_ct_kwh,
        pv_forecast_kw=raw.pv_forecast_kw,
    )
