"""
ScenarioGenerator — synthetische Testszenarien für BitGridAI.

Generiert CSV-Dateien im Format von src/sim/scenario_loader.py:
  offset_min, pv_power_w, house_load_w, grid_import_w, battery_soc_pct,
  miner_temp_c, miner_heartbeat_age_sec [, price_ct] [, forecast_kw]

Vorhandene Szenario-Typen:
  sunny_day      — klarer Sonnentag, stabiler Überschuss mittags
  cloudy_day     — bedeckt mit zufälligen Wolkendurchgängen
  price_spike    — Preis-Spike erzwingt R4-Blockierung
  battery_drain  — Batterie entlädt sich → R2 greift
  overtemp       — Miner überhitzt → R3 greift
  full_day       — 24h mit allen Ereignissen kombiniert

Verwendung:
  python -m src.sim.scenario_generator --type sunny_day --blocks 36
  python -m src.sim.scenario_generator --type full_day --out my_scenario.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import os
import random
from pathlib import Path
from typing import Any, Callable


def _pv_curve(
    offset_min: int,
    peak_kw: float = 10.0,
    sunrise_h: float = 6.5,
    sunset_h: float = 20.5,
) -> float:
    """Sinusförmige PV-Kurve basierend auf Tageszeit."""
    hour = (offset_min / 60) % 24
    if hour < sunrise_h or hour > sunset_h:
        return 0.0
    day_fraction = (hour - sunrise_h) / (sunset_h - sunrise_h)
    return peak_kw * 1000 * math.sin(math.pi * day_fraction)


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


# ---------------------------------------------------------------------------
# Szenario-Generatoren
# ---------------------------------------------------------------------------


def sunny_day(blocks: int = 36, peak_kw: float = 10.0) -> list[dict[str, Any]]:
    """Klarer Sonnentag — stabiler Surplus am Mittag."""
    rows = []
    soc = 85.0
    for i in range(blocks):
        offset = i * 10
        pv = _pv_curve(offset, peak_kw=peak_kw)
        house = 600 + random.gauss(0, 50)
        surplus = pv - house
        grid = _clamp(-surplus, 0, 2000)
        soc = _clamp(soc + surplus / 10000, 20.0, 100.0)
        rows.append(
            {
                "offset_min": offset,
                "pv_power_w": round(pv, 1),
                "house_load_w": round(house, 1),
                "grid_import_w": round(grid, 1),
                "battery_soc_pct": round(soc, 1),
                "miner_temp_c": round(65 + random.gauss(0, 2), 1),
                "miner_heartbeat_age_sec": 5,
                "energy_price_ct_kwh": round(18 + random.gauss(0, 2), 2),
                "pv_forecast_kw": round(pv / 1000 * 0.9, 2),
            }
        )
    return rows


def cloudy_day(blocks: int = 36, peak_kw: float = 10.0) -> list[dict[str, Any]]:
    """Bedeckter Tag mit Wolkendurchgängen (PV bricht kurz ein)."""
    rows = []
    soc = 70.0
    cloud_factor = 1.0
    for i in range(blocks):
        offset = i * 10
        # Wolken-Events: zufällige Einbrüche
        if random.random() < 0.15:
            cloud_factor = random.uniform(0.1, 0.4)
        elif random.random() < 0.3:
            cloud_factor = _clamp(cloud_factor + 0.2, 0.0, 1.0)

        pv = _pv_curve(offset, peak_kw=peak_kw) * cloud_factor
        house = 800 + random.gauss(0, 80)
        surplus = pv - house
        grid = _clamp(-surplus, 0, 5000)
        soc = _clamp(soc + surplus / 12000, 15.0, 100.0)
        rows.append(
            {
                "offset_min": offset,
                "pv_power_w": round(pv, 1),
                "house_load_w": round(house, 1),
                "grid_import_w": round(grid, 1),
                "battery_soc_pct": round(soc, 1),
                "miner_temp_c": round(67 + random.gauss(0, 3), 1),
                "miner_heartbeat_age_sec": 5,
                "energy_price_ct_kwh": round(22 + random.gauss(0, 3), 2),
                "pv_forecast_kw": round(pv / 1000 * cloud_factor, 2),
            }
        )
    return rows


def price_spike(blocks: int = 24) -> list[dict[str, Any]]:
    """Preis-Spike in der Mitte → R1/R4 blockieren Mining."""
    rows = []
    soc = 90.0
    for i in range(blocks):
        offset = i * 10
        pv = 4000 + random.gauss(0, 200)  # Stabil viel PV
        house = 600.0
        surplus = pv - house
        soc = _clamp(soc + 0.1, 80.0, 100.0)

        # Blocks 8–16: Preis-Spike auf 35 Ct/kWh
        if 8 <= i <= 16:
            price = round(35 + random.gauss(0, 2), 2)
        else:
            price = round(18 + random.gauss(0, 1), 2)

        rows.append(
            {
                "offset_min": offset,
                "pv_power_w": round(pv, 1),
                "house_load_w": round(house, 1),
                "grid_import_w": 0.0,
                "battery_soc_pct": round(soc, 1),
                "miner_temp_c": 66.0,
                "miner_heartbeat_age_sec": 5,
                "energy_price_ct_kwh": price,
                "pv_forecast_kw": round(pv / 1000, 2),
            }
        )
    return rows


def battery_drain(blocks: int = 30) -> list[dict[str, Any]]:
    """Batterie entlädt sich durch Nachtbetrieb → R2 greift bei SoC ≤ 20%."""
    rows = []
    soc = 45.0
    for i in range(blocks):
        offset = i * 10
        pv = 0.0  # Nacht
        house = 700 + random.gauss(0, 50)
        grid = _clamp(house, 0, 5000)

        # Batterie entlädt sich um ~1% pro Block
        soc = _clamp(soc - 1.5 + random.gauss(0, 0.3), 0.0, 100.0)
        rows.append(
            {
                "offset_min": offset,
                "pv_power_w": 0.0,
                "house_load_w": round(house, 1),
                "grid_import_w": round(grid, 1),
                "battery_soc_pct": round(soc, 1),
                "miner_temp_c": 62.0,
                "miner_heartbeat_age_sec": 5,
                "energy_price_ct_kwh": 20.0,
                "pv_forecast_kw": 0.0,
            }
        )
    return rows


def overtemp(blocks: int = 20) -> list[dict[str, Any]]:
    """Miner-Temperatur steigt auf >85°C → R3 Safety-Stop."""
    rows = []
    soc = 80.0
    for i in range(blocks):
        offset = i * 10
        pv = 5000.0
        house = 600.0

        # Temp steigt ab Block 8 auf 90°C
        if i < 8:
            temp = 65 + i * 0.5
        else:
            temp = _clamp(65 + (i - 8) * 4, 65, 92)

        rows.append(
            {
                "offset_min": offset,
                "pv_power_w": pv,
                "house_load_w": house,
                "grid_import_w": 0.0,
                "battery_soc_pct": round(soc, 1),
                "miner_temp_c": round(temp, 1),
                "miner_heartbeat_age_sec": 5,
                "energy_price_ct_kwh": 18.0,
                "pv_forecast_kw": 5.0,
            }
        )
    return rows


def full_day(peak_kw: float = 10.0) -> list[dict[str, Any]]:
    """24h-Szenario mit allen Ereignissen: PV-Kurve + Batterie + Preis-Spike + kurze Überhitzung."""
    blocks_per_hour = 6
    total_blocks = 24 * blocks_per_hour  # 144 Blöcke
    rows = []
    soc = 60.0
    base_price = 18.0

    for i in range(total_blocks):
        offset = i * 10
        hour = (offset / 60) % 24

        pv = _pv_curve(offset, peak_kw=peak_kw)
        # Wolken-Event von 11:00–12:30
        if 66 <= i <= 75:
            pv *= 0.2

        house = 600 + 200 * math.sin(math.pi * hour / 12) + random.gauss(0, 60)

        surplus = pv - house
        soc = _clamp(soc + surplus / 15000, 5.0, 100.0)
        grid = _clamp(-surplus, 0, 8000)

        # Preis-Spike 17:00–19:00 (Abendspitze)
        if 17 <= hour < 19:
            price = round(32 + random.gauss(0, 3), 2)
        else:
            price = round(base_price + random.gauss(0, 2), 2)

        # Kurze Überhitzung 13:30–14:00
        if 81 <= i <= 84:
            temp = round(86 + random.gauss(0, 1), 1)
        else:
            temp = round(65 + random.gauss(0, 2), 1)

        rows.append(
            {
                "offset_min": offset,
                "pv_power_w": round(pv, 1),
                "house_load_w": round(house, 1),
                "grid_import_w": round(grid, 1),
                "battery_soc_pct": round(soc, 1),
                "miner_temp_c": temp,
                "miner_heartbeat_age_sec": 5,
                "energy_price_ct_kwh": price,
                "pv_forecast_kw": round(pv / 1000 * 0.85, 2),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# CSV-Export
# ---------------------------------------------------------------------------

_SCENARIO_MAP: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "sunny_day": sunny_day,
    "cloudy_day": cloudy_day,
    "price_spike": price_spike,
    "battery_drain": battery_drain,
    "overtemp": overtemp,
    "full_day": full_day,
}

_HEADER = (
    "# offset_min, pv_power_w, house_load_w, grid_import_w, battery_soc_pct, "
    "miner_temp_c, miner_heartbeat_age_sec, energy_price_ct_kwh, pv_forecast_kw\n"
)


def generate_csv(scenario_type: str, **kwargs: Any) -> str:
    """Generiert ein Szenario als CSV-String."""
    fn = _SCENARIO_MAP.get(scenario_type)
    if fn is None:
        raise ValueError(
            f"Unbekanntes Szenario: {scenario_type!r}. Verfügbar: {list(_SCENARIO_MAP)}"
        )

    rows = fn(**kwargs)

    buf = io.StringIO()
    buf.write(_HEADER)
    for row in rows:
        buf.write(
            f"{row['offset_min']}, "
            f"{row['pv_power_w']}, "
            f"{row['house_load_w']}, "
            f"{row['grid_import_w']}, "
            f"{row['battery_soc_pct']}, "
            f"{row['miner_temp_c']}, "
            f"{row['miner_heartbeat_age_sec']}, "
            f"{row.get('energy_price_ct_kwh', '')}, "
            f"{row.get('pv_forecast_kw', '')}\n"
        )
    return buf.getvalue()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="BitGridAI Scenario Generator")
    parser.add_argument(
        "--type",
        default="sunny_day",
        choices=list(_SCENARIO_MAP),
        help="Szenario-Typ",
    )
    parser.add_argument(
        "--blocks", type=int, default=None, help="Anzahl Blöcke (10 min)"
    )
    parser.add_argument(
        "--peak-kw", type=float, default=10.0, help="PV-Peakleistung (kW)"
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Ausgabedatei (default: scenarios/{type}.csv)",
    )
    args = parser.parse_args()

    kwargs = {"peak_kw": args.peak_kw}
    if args.blocks is not None:
        kwargs["blocks"] = args.blocks

    csv_content = generate_csv(args.type, **kwargs)

    out_path = args.out or f"src/sim/scenarios/gen_{args.type}.csv"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(csv_content, encoding="utf-8")
    print(f"Szenario geschrieben: {out_path}")
    print(f"Blöcke: {csv_content.count(chr(10)) - 1}")


if __name__ == "__main__":
    main()
