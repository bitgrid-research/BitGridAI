"""
Augment — ergänzt fehlende Signale in realen HA-Szenario-CSVs.

Home Assistant speichert drei für die Regeln relevante Signale **nicht**
historisch. Dieses Modul füllt sie deterministisch und dokumentiert auf:

  - ``energy_price_ct_kwh`` — über ein dokumentiertes Tarifmodell (Tageszeit-Bänder)
  - ``pv_forecast_kw``      — über Perfect-Foresight aus den tatsächlich
                              gemessenen Folgeblöcken

Beide Verfahren sind reine Funktionen der vorhandenen Realdaten → der Replay
bleibt deterministisch und reproduzierbar. Was real gemessen und was augmentiert
ist, bleibt durch die Tarif-/Forecast-Herkunft klar getrennt.

Verwendung:
    python -m src.sim.augment src/sim/scenarios/real_2026-06-21.csv
    python -m src.sim.augment <in.csv> --out <out.csv> --horizon 6
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from src.sim.scenario_loader import load_csv_scenario

# ---------------------------------------------------------------------------
# Dokumentiertes Tarifmodell
# ---------------------------------------------------------------------------
#
# Vereinfachte dynamische Prosumer-Tarifkurve (ct/kWh) nach Tageszeit-Bändern.
# Bildet das typische Profil eines dynamischen Tarifs nach: günstige PV-reiche
# Mittagsstunden, teure Abend-Spitze. Jedes Band ist (start_h, end_h, ct/kWh),
# end_h exklusiv. Die Bänder decken 0–24 h lückenlos ab.
#
# Caveat: Die Tageszeit wird aus ``timestamp_offset_min`` abgeleitet (Uhrzeit
# relativ zum Export-Start, i.d.R. UTC-Mitternacht). Für die Studie ist nur die
# deterministische, reproduzierbare Zuordnung relevant, nicht die exakte
# Lokalzeit-Korrektur.
_TARIFF_BANDS: tuple[tuple[int, int, float], ...] = (
    (0, 6, 18.0),  # Nacht
    (6, 10, 24.0),  # Morgen (Last hoch, wenig PV)
    (10, 16, 13.0),  # PV-Mittag (günstig)
    (16, 17, 22.0),  # Übergang
    (17, 21, 29.0),  # Abend-Spitze (teuer)
    (21, 24, 21.0),  # später Abend
)

_MINUTES_PER_DAY = 1440
_BLOCK_MIN = 10


def tariff_ct_kwh(minute_of_day: int) -> float:
    """Gibt den Tarif (ct/kWh) für eine Minute-im-Tag nach dem Tarifmodell zurück."""
    hour = (minute_of_day % _MINUTES_PER_DAY) // 60
    for start_h, end_h, price in _TARIFF_BANDS:
        if start_h <= hour < end_h:
            return price
    # Bänder decken 0–24 ab; dieser Pfad ist unerreichbar, dient nur der Typsicherheit.
    return _TARIFF_BANDS[-1][2]


def apply_tariff(rows: list[dict[str, Any]], *, overwrite: bool = False) -> int:
    """
    Füllt ``energy_price_ct_kwh`` je Block aus dem Tarifmodell.

    Füllt standardmäßig nur leere Felder; mit ``overwrite=True`` werden auch
    vorhandene Werte ersetzt. Gibt die Anzahl gesetzter Felder zurück.
    """
    filled = 0
    for row in rows:
        if not overwrite and row.get("energy_price_ct_kwh") is not None:
            continue
        minute_of_day = int(row["timestamp_offset_min"]) % _MINUTES_PER_DAY
        row["energy_price_ct_kwh"] = tariff_ct_kwh(minute_of_day)
        filled += 1
    return filled


def apply_perfect_forecast(
    rows: list[dict[str, Any]],
    *,
    horizon_blocks: int = 6,
    overwrite: bool = False,
) -> int:
    """
    Füllt ``pv_forecast_kw`` als Perfect-Foresight aus den Folgeblöcken.

    Für Block i ist der Forecast der Mittelwert der tatsächlich gemessenen
    PV-Leistung der nächsten ``horizon_blocks`` Blöcke (Standard 6 = 1 h), in kW.
    Am Zeitreihenende (keine Folgeblöcke mehr) wird die aktuelle PV-Leistung als
    Fallback verwendet. Gibt die Anzahl gesetzter Felder zurück.
    """
    if horizon_blocks < 1:
        raise ValueError("horizon_blocks muss >= 1 sein")

    n = len(rows)
    filled = 0
    for i, row in enumerate(rows):
        if not overwrite and row.get("pv_forecast_kw") is not None:
            continue
        window = [
            rows[j]["pv_power_w"] for j in range(i + 1, min(i + 1 + horizon_blocks, n))
        ]
        if window:
            forecast_w = sum(window) / len(window)
        else:
            forecast_w = float(row["pv_power_w"])  # Fallback: aktueller Wert
        row["pv_forecast_kw"] = round(forecast_w / 1000.0, 3)
        filled += 1
    return filled


# ---------------------------------------------------------------------------
# CSV-I/O (Kommentar-Header bleibt erhalten)
# ---------------------------------------------------------------------------

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


def _read_comments(path: str | Path) -> list[str]:
    """Liest die führenden #-Kommentarzeilen (Metadaten) einer Szenario-CSV."""
    comments: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#"):
                comments.append(stripped)
            elif stripped:
                break  # erste Datenzeile → Header ist zu Ende
    return comments


def _format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def write_csv(
    rows: list[dict[str, Any]],
    out_path: str | Path,
    comments: list[str],
) -> None:
    """Schreibt Rows im 12-Spalten-Szenarioformat samt erhaltenem Kommentar-Header."""
    lines: list[str] = list(comments)
    lines.append("# augment: tariff+forecast")
    lines.append("# " + ", ".join(_CSV_COLUMNS))
    for row in rows:
        lines.append(",".join(_format_cell(row.get(col)) for col in _CSV_COLUMNS))
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def augment_file(
    in_path: str | Path,
    out_path: str | Path,
    *,
    horizon_blocks: int = 6,
    overwrite: bool = False,
) -> tuple[int, int]:
    """Augmentiert eine Szenario-CSV (Tarif + Forecast) und schreibt sie."""
    rows = load_csv_scenario(in_path)
    comments = _read_comments(in_path)
    n_price = apply_tariff(rows, overwrite=overwrite)
    n_forecast = apply_perfect_forecast(
        rows, horizon_blocks=horizon_blocks, overwrite=overwrite
    )
    write_csv(rows, out_path, comments)
    return n_price, n_forecast


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(
        description="Ergänzt Tarif (energy_price) und Perfect-Foresight (pv_forecast) in einer Szenario-CSV"
    )
    parser.add_argument("csv", help="Eingabe-Szenario-CSV")
    parser.add_argument("--out", help="Ausgabedatei (Standard: <in>_augmented.csv)")
    parser.add_argument(
        "--horizon",
        type=int,
        default=6,
        help="Forecast-Horizont in Blöcken (Standard: 6 = 1 h)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Vorhandene Preis-/Forecast-Werte überschreiben",
    )
    args = parser.parse_args()

    in_path = Path(args.csv)
    out_path = (
        Path(args.out)
        if args.out
        else in_path.with_name(f"{in_path.stem}_augmented.csv")
    )
    n_price, n_forecast = augment_file(
        in_path, out_path, horizon_blocks=args.horizon, overwrite=args.overwrite
    )
    print(f"→ Eingabe:  {in_path}")
    print(f"→ Ausgabe:  {out_path}")
    print(f"✓ Tarif gesetzt:    {n_price} Blöcke")
    print(f"✓ Forecast gesetzt: {n_forecast} Blöcke (Horizont {args.horizon} Blöcke)")


if __name__ == "__main__":
    main()
