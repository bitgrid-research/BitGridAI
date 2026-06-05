"""
Synthetische 4-Jahreszeiten-Tagesprofile gegen den Saison-Bias.

Die Realdaten decken nur Spätfrühling ab. Dieser Generator erzeugt deterministische
Tageskurven (Winter/Frühling/Sommer/Herbst) im Pipeline-CSV-Format, damit
`augment` → `replay` → `scenario_miner` darauf laufen — klar als **synthetisch**
markiert (kein Ersatz für reale saisonale Aufzeichnung, nur Überbrückung).

Modell:
- PV: Glockenkurve (sin) zwischen Sonnenauf-/-untergang × Saison-Peak, optional Wolken-Dip.
- Last: Grundlast + Morgen-/Abendspitze.
- Batterie: lädt mit Überschuss, entlädt bei Defizit (Kapazität, Start-SoC) — Miner
  NICHT modelliert (das entscheidet der Replay-Kern).

  python -m src.sim.synth_seasons --all      # alle 4 → src/sim/scenarios/synth_<saison>.csv
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_BLOCK_MIN = 10
_BLOCKS = 144
_DEFAULT_DIR = Path("src/sim/scenarios")

_CSV_COLUMNS = [
    "timestamp_offset_min",
    "pv_power_w",
    "house_load_w",
    "grid_import_w",
    "battery_soc_pct",
    "miner_temp_c",
    "miner_heartbeat_age_sec",
    "energy_price_ct_kwh",
    "pv_forecast_kw",
    "grid_export_w",
    "miner_power_w",
    "heizstab_power_w",
]


@dataclass(frozen=True)
class SeasonProfile:
    name: str
    pv_peak_w: float
    sunrise_min: int
    sunset_min: int
    load_base_w: float
    morning_peak_w: float
    evening_peak_w: float
    start_soc_pct: float
    battery_kwh: float = 10.0
    cloud_start_min: int = -1
    cloud_end_min: int = -1
    cloud_factor: float = 1.0


SEASONS: dict[str, SeasonProfile] = {
    "winter": SeasonProfile(
        "winter",
        pv_peak_w=2500,
        sunrise_min=480,
        sunset_min=990,
        load_base_w=700,
        morning_peak_w=900,
        evening_peak_w=1400,
        start_soc_pct=35,
        cloud_start_min=660,
        cloud_end_min=840,
        cloud_factor=0.4,
    ),
    "fruehling": SeasonProfile(
        "fruehling",
        pv_peak_w=6000,
        sunrise_min=390,
        sunset_min=1170,
        load_base_w=550,
        morning_peak_w=700,
        evening_peak_w=1000,
        start_soc_pct=30,
    ),
    "sommer": SeasonProfile(
        "sommer",
        pv_peak_w=9000,
        sunrise_min=330,
        sunset_min=1260,
        load_base_w=500,
        morning_peak_w=600,
        evening_peak_w=900,
        start_soc_pct=25,
    ),
    "herbst": SeasonProfile(
        "herbst",
        pv_peak_w=4500,
        sunrise_min=450,
        sunset_min=1080,
        load_base_w=650,
        morning_peak_w=800,
        evening_peak_w=1200,
        start_soc_pct=40,
        cloud_start_min=720,
        cloud_end_min=900,
        cloud_factor=0.5,
    ),
}


def _pv_at(minute: int, p: SeasonProfile) -> float:
    if minute < p.sunrise_min or minute > p.sunset_min:
        return 0.0
    x = (minute - p.sunrise_min) / (p.sunset_min - p.sunrise_min)
    pv = p.pv_peak_w * math.sin(math.pi * x) ** 1.3
    if p.cloud_start_min <= minute <= p.cloud_end_min:
        pv *= p.cloud_factor
    return float(max(0.0, pv))


def _load_at(minute: int, p: SeasonProfile) -> float:
    load = p.load_base_w
    if 420 <= minute <= 540:
        load += p.morning_peak_w
    if 1080 <= minute <= 1320:
        load += p.evening_peak_w
    return load


def generate_day(p: SeasonProfile) -> list[dict[str, Any]]:
    """Erzeugt 144 10-Min-Blöcke mit einfachem Batteriemodell."""
    cap_wh = p.battery_kwh * 1000.0
    soc_wh = p.start_soc_pct / 100.0 * cap_wh
    rows: list[dict[str, Any]] = []
    for i in range(_BLOCKS):
        minute = i * _BLOCK_MIN
        pv = _pv_at(minute, p)
        load = _load_at(minute, p)
        surplus_w = pv - load
        energy_wh = surplus_w * (_BLOCK_MIN / 60.0)

        grid_import = 0.0
        grid_export = 0.0
        new_soc = soc_wh + energy_wh
        if new_soc > cap_wh:  # Batterie voll → Rest einspeisen
            grid_export = (new_soc - cap_wh) / (_BLOCK_MIN / 60.0)
            new_soc = cap_wh
        elif new_soc < 0:  # Batterie leer → Rest aus Netz
            grid_import = (-new_soc) / (_BLOCK_MIN / 60.0)
            new_soc = 0.0
        soc_wh = new_soc

        rows.append(
            {
                "timestamp_offset_min": minute,
                "pv_power_w": round(pv, 1),
                "house_load_w": round(load, 1),
                "grid_import_w": round(grid_import, 1),
                "battery_soc_pct": round(soc_wh / cap_wh * 100, 1),
                "miner_temp_c": 45.0,
                "miner_heartbeat_age_sec": 5.0,
                "energy_price_ct_kwh": "",
                "pv_forecast_kw": "",
                "grid_export_w": round(grid_export, 1),
                "miner_power_w": "",
                "heizstab_power_w": "",
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]], out: Path, season: str) -> None:
    lines = [
        "# SYNTHETISCH — deterministisches Saison-Profil (kein Realmesswert)",
        f"# season: {season}",
        "# " + ", ".join(_CSV_COLUMNS),
    ]
    for r in rows:
        lines.append(",".join(str(r[c]) for c in _CSV_COLUMNS))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Synthetische Saison-Tagesprofile")
    p.add_argument("--season", choices=sorted(SEASONS), help="einzelne Saison")
    p.add_argument("--all", action="store_true", help="alle 4 Saisons")
    p.add_argument("--out-dir", default=str(_DEFAULT_DIR))
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seasons = list(SEASONS) if args.all else ([args.season] if args.season else [])
    if not seasons:
        p.error("--season <name> oder --all angeben")

    for s in seasons:
        prof = SEASONS[s]
        rows = generate_day(prof)
        out = out_dir / f"synth_{s}.csv"
        write_csv(rows, out, s)
        pv_peak = max(float(r["pv_power_w"]) for r in rows)
        soc = [float(r["battery_soc_pct"]) for r in rows]
        print(
            f"  ✓ {s:10s} PV-Peak {pv_peak/1000:.1f} kW · SoC {min(soc):.0f}–{max(soc):.0f} % → {out.name}"
        )


if __name__ == "__main__":
    main()
