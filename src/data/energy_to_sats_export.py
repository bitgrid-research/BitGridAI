"""
EnergyToSatsExport — exportiert die energy_to_sats-Tagesreihe aus bitgrid.db
als JSON-Artefakt fuer den Statistik-Tab (views/stats_energy_to_sats.yaml).

Anders als btc_power_law.py/btc_hashrate.py/btc_difficulty.py kein Netzwerk-
zugriff: die Quelle ist ausschliesslich die lokale bitgrid.db (daily_kpi +
die View v_energy_to_sats_7d, siehe db.py). Gleiches Ausgabemuster trotzdem
uebernommen (JSON-Datei nach src/ha/config/www/, Karte liest sie per
fetch('/local/...')) — Konsistenz mit den bestehenden Analyse-Karten.

Kein Steuerpfad: reiner Export fuer die Anzeige, beeinflusst keine
Mining-Entscheidung in core/. Zeigt das offizielle KPI-Ziel aus
docs/architecture/01_introduction_and_goals/012_quality_goals.md
("Energy-to-Sats-Effizienz >= 45 sats/kWh, 7-Tage-Schnitt") zum ersten Mal
ueberhaupt an, siehe ADR 026.

CLI:
    python -m src.data.energy_to_sats_export
    python -m src.data.energy_to_sats_export --days 21 --db data/bitgrid.db
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

from src.data.db import get_connection

# Saisonal gestaffelt seit 01.09.2026 (ADR 029, docs/architecture/09_design_
# decisions/091_adr_de.md) statt fest 45 sats/kWh (ADR 026) — der feste Wert
# war seit Wochen um Faktor ~2,8 unterboten und damit kein Ziel mehr. Nur der
# "Voll"-Tarif (Mai-Aug) ist an 17 echte Tagesmessungen kalibriert, die beiden
# anderen sind Modellschaetzungen (Eco ist pro kWh effizienter als Super,
# siehe ADR 029), ausdruecklich vorlaeufig bis echte Daten aus den jeweiligen
# Monaten vorliegen. Tier-Zuordnung folgt sensor.mvp_saison_status (ADR 028).
_SEASONAL_TARGETS: dict[int, float] = {
    1: 135.0,
    2: 135.0,  # Nur Eco (Jan/Feb)
    3: 130.0,
    4: 130.0,  # Eco + Standard (Maer/Apr)
    5: 125.0,
    6: 125.0,
    7: 125.0,
    8: 125.0,  # Voll — gemessen, 15.-31.08.2026, n=17
    9: 130.0,  # Eco + Standard (Sep)
    10: 135.0,
    11: 135.0,
    12: 135.0,  # Nur Eco (Okt-Dez)
}


def target_for_month(month: int) -> float:
    """Saisonales Energy-to-Sats-Ziel fuer den gegebenen Kalendermonat (1-12)."""
    return _SEASONAL_TARGETS[month]


def fetch_series(conn: sqlite3.Connection, days: int) -> list[dict[str, object]]:
    """
    Liest die letzten `days` Tage aus v_energy_to_sats_7d (Tage ohne
    Abrechnung sind darin nicht enthalten — keine erfundenen Luecken-Punkte
    im Chart, siehe compute_day() in daily_kpi.py).
    """
    since = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT day, energy_to_sats, energy_to_sats_7d_avg"
        " FROM v_energy_to_sats_7d WHERE day >= ? ORDER BY day",
        (since,),
    ).fetchall()
    return [
        {
            "day": day,
            "energy_to_sats": round(sats, 2),
            "avg_7d": round(avg7, 2) if avg7 is not None else None,
        }
        for day, sats, avg7 in rows
    ]


def build_artifact(
    series: list[dict[str, object]], now: datetime | None = None
) -> dict[str, object]:
    now = now or datetime.now(timezone.utc)
    latest_avg = None
    for point in reversed(series):
        if point["avg_7d"] is not None:
            latest_avg = point["avg_7d"]
            break
    return {
        "generated_at": now.isoformat(),
        "target_sats_per_kwh": target_for_month(now.month),
        "latest_avg_7d": latest_avg,
        "days": series,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exportiert energy_to_sats aus bitgrid.db als JSON fuer den Statistik-Tab"
    )
    parser.add_argument(
        "--days", type=int, default=30, help="Zeitfenster in Tagen (default: 30)"
    )
    parser.add_argument("--db", default="data/bitgrid.db")
    parser.add_argument(
        "--out",
        default="src/ha/config/www/energy_to_sats.json",
        help="Zielpfad fuer das JSON-Artefakt",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    conn = get_connection(args.db)
    try:
        series = fetch_series(conn, args.days)
    finally:
        conn.close()

    artifact = build_artifact(series)

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, separators=(",", ":"))

    avg_txt = (
        f"{artifact['latest_avg_7d']:.1f}"
        if artifact["latest_avg_7d"] is not None
        else "—"
    )
    print(
        f"Geschrieben: {out_path} ({len(series)} Tage, "
        f"7-Tage-Schnitt aktuell: {avg_txt} sats/kWh, "
        f"Ziel: {artifact['target_sats_per_kwh']})"
    )


if __name__ == "__main__":
    main()
