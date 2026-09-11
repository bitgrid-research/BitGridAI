"""
BtcPriceHistory — synct die BTC/EUR-Preishistorie von der self-gehosteten
mempool.space-Instanz nach bitgrid.db und exportiert sie als JSON-Artefakt
fuer den Kurs-Verlaufschart im BitcoinInfo-Tab (views/stats_btc_price.yaml).

Anders als btc_power_law.py (USD, seit Genesis 2009, Log-Log-Power-Law-Fit
fuer den KI-Tab) hier bewusst EUR. Bis 31.08.2026 schrieb dieses Skript
direkt ein JSON mit einem festen Rolling-Fenster (letzte 90 Tage) — blieb das
Skript laenger unausgefuehrt liegen, verschwanden dabei stillschweigend Tage
UND ein erneuter Deploy des dabei veralteten JSON-Artefakts konnte einen auf
dem Server zwischenzeitlich frischer generierten Stand ueberschreiben
("steht wieder bei 25.08", live beobachtet 01.09.2026). Jetzt zweistufig,
gleiches Muster wie energy_to_sats_export.py (DB-Tabelle als Wahrheitsquelle,
JSON nur als Export):
  1. Sync: mempool.space liefert je Abruf die GESAMTE verfuegbare Historie
     (kein Zeitfenster-Parameter in der API), wird komplett in
     btc_price_daily upgesert (INSERT OR REPLACE, siehe db.py-Kommentar).
     Die Tabelle waechst dadurch unbegrenzt (aktuell seit 2013).
  2. Export: liest ein juengeres --days-Fenster (default 90, Kartendesign
     bewusst ein kurzer Trend statt 12-Jahre-Verlauf, Nutzer-Entscheidung
     01.09.2026) aus der Tabelle — der Cutoff wird aber bei JEDEM Lauf frisch
     gegen die aktuelle Uhrzeit berechnet, nicht gegen einen alten JSON-
     Zeitstempel. Genau das war der eigentliche Fehler: blieb das Skript
     laenger unausgefuehrt liegen, rutschte das exportierte Fenster nicht
     einfach nach, sondern das komplette Artefakt blieb auf dem letzten
     Laufdatum eingefroren stehen ("soll immer den neuesten Wert
     beibehalten").

Wiederverwendet fetch_historical_prices()/downsample_daily() aus
btc_power_law.py statt sie zu duplizieren (identische Quelle, identisches
Downsampling-Prinzip: ein Wert pro Kalendertag).

Kein Steuerpfad: reiner Marktkontext, beeinflusst keine Mining-Entscheidung
in core/.

CLI:
    python -m src.data.btc_price_history
    python -m src.data.btc_price_history --db data/bitgrid.db

Env-Vars (aus .env):
    MEMPOOL_HOST — IP der self-hosted mempool.space-Instanz
    MEMPOOL_PORT — Port (default: 3006)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone

from src.data.btc_power_law import downsample_daily, fetch_historical_prices
from src.data.db import get_connection

log = logging.getLogger(__name__)

_DEFAULT_PORT = "3006"


def sync_to_db(
    conn: sqlite3.Connection, daily_prices: list[tuple[date, float]]
) -> int:
    """Upsert aller abgerufenen Tage in btc_price_daily. Gibt die Anzahl
    geschriebener Zeilen zurueck."""
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        "INSERT OR REPLACE INTO btc_price_daily (day, price_eur, fetched_at) "
        "VALUES (?, ?, ?)",
        [(d.isoformat(), round(p, 2), now_iso) for d, p in daily_prices],
    )
    conn.commit()
    return len(daily_prices)


def export_artifact(
    conn: sqlite3.Connection, days: int, now: datetime | None = None
) -> dict[str, object]:
    """Liest ein juengeres Fenster (`days` Tage) aus btc_price_daily fuer die
    Kurztrend-Karte (Nutzer-Entscheidung 01.09.2026: die volle 12-Jahre-
    Historie waere ein anderes, unerwuenschtes Kartenbild). Der Unterschied
    zum fruehen Verhalten: der Cutoff wird bei JEDEM Lauf frisch gegen `now`
    berechnet, gegen eine Tabelle, die immer die volle mempool.space-Historie
    enthaelt — bleibt das Skript liegen, "verschwindet" beim naechsten Lauf
    nichts, es rutscht nur die Fensterkante nach. Fuer die komplette Historie
    einfach `SELECT * FROM btc_price_daily` direkt gegen die DB abfragen.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = (now.date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT day, price_eur FROM btc_price_daily WHERE day >= ? ORDER BY day",
        (cutoff,),
    ).fetchall()
    return {
        "generated_at": now.isoformat(),
        "currency": "EUR",
        "days": [[day, price] for day, price in rows],
    }


def _mempool_base_url() -> str:
    host = os.getenv("MEMPOOL_HOST", "")
    if not host:
        raise RuntimeError("MEMPOOL_HOST nicht gesetzt. In .env eintragen.")
    port = os.getenv("MEMPOOL_PORT", _DEFAULT_PORT)
    return f"http://{host}:{port}"


def _load_dotenv() -> None:
    env_file = ".env"
    if not os.path.exists(env_file):
        return
    with open(env_file) as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key, _, value = stripped.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synct BTC/EUR-Preishistorie von mempool.space nach "
        "bitgrid.db und exportiert sie als JSON fuer den BitcoinInfo-Tab."
    )
    parser.add_argument("--db", default="data/bitgrid.db")
    parser.add_argument(
        "--out",
        default="src/ha/config/www/btc_price_eur.json",
        help="Zielpfad fuer das JSON-Artefakt",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Fenster fuer den EXPORT in Tagen (default: 90). Betrifft nur "
        "das JSON fuer die Karte, nicht die DB — btc_price_daily haelt "
        "immer die volle mempool.space-Historie.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    _load_dotenv()
    args = _parse_args()

    base_url = _mempool_base_url()
    log.info("Hole EUR-Preishistorie von %s ...", base_url)
    prices = fetch_historical_prices(base_url, currency="EUR")
    if not prices:
        log.error("Keine Preisdaten erhalten - Abbruch.")
        raise SystemExit(1)

    daily = downsample_daily(prices)
    if not daily:
        log.error("Kein Tag im Downsampling - Abbruch.")
        raise SystemExit(1)

    conn = get_connection(args.db)
    try:
        written = sync_to_db(conn, daily)
        artifact = export_artifact(conn, args.days)
    finally:
        conn.close()

    artifact_days = artifact["days"]
    assert isinstance(artifact_days, list)
    if not artifact_days:
        log.error(
            "Export-Fenster (%d Tage) enthaelt keine Zeilen - Abbruch.", args.days
        )
        raise SystemExit(1)

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_path) / 1024
    print(
        f"Sync: {written} Tage nach {args.db} (btc_price_daily, volle Historie). "
        f"Export: {out_path} ({size_kb:.0f} KB, {len(artifact_days)} Tage "
        f"im {args.days}-Tage-Fenster, {artifact_days[0][0]}–{artifact_days[-1][0]})"
    )


if __name__ == "__main__":
    main()
