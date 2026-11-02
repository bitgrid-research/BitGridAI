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

Seit 25.09.2026 zusaetzlich ein zweiter, rohaufgeloester Pfad (btc_price_raw
-> www/btc_price_full.json) fuer den dynamischen BitcoinInfo-Kurschart
(views/btc_kurs_chart.yaml): EUR+USD aus einem gemeinsamen Abruf
(fetch_historical_prices_dual()), ungekuerzt in mempool.space-eigener
Aufloesung (stuendlich fuer die juengsten ~100 Tage, danach taeglich/
woechentlich). Die Zeitraum-Buttons (1 Tag/5 Tage/1 Monat/1 Jahr/5 Jahre/Max)
filtern client-seitig aus dieser einen Reihe, kein zweiter Datenpfad noetig.

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

from src.data.btc_power_law import (
    downsample_daily,
    fetch_historical_prices,
    fetch_historical_prices_dual,
)
from src.data.db import get_connection

log = logging.getLogger(__name__)

_DEFAULT_PORT = "3006"


def sync_to_db(conn: sqlite3.Connection, daily_prices: list[tuple[date, float]]) -> int:
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


def sync_raw_to_db(
    conn: sqlite3.Connection,
    raw_prices: list[tuple[int, float | None, float | None]],
) -> int:
    """Upsert der Rohpunkte (mempool-Aufloesung, EUR+USD) in btc_price_raw.
    Gibt die Anzahl geschriebener Zeilen zurueck."""
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        "INSERT OR REPLACE INTO btc_price_raw (ts, price_eur, price_usd, fetched_at) "
        "VALUES (?, ?, ?, ?)",
        [
            (
                ts,
                round(eur, 2) if eur is not None else None,
                round(usd, 2) if usd is not None else None,
                now_iso,
            )
            for ts, eur, usd in raw_prices
        ],
    )
    conn.commit()
    return len(raw_prices)


# Groesste plausible Abweichung eines Punkts vom EUR/USD-Kurs seines
# Tagesankers. Wechselkurse bewegen sich innerhalb eines Tages im
# Promillebereich; 1 % trennt sauber von den fortgeschriebenen EUR-Werten
# (gemessen 15.10.2026: 3-5 % Abweichung, Juni/Juli 2026).
_EUR_FX_TOLERANCE = 0.01
# Ein Tagesanker gilt hoechstens so lange; danach bleibt EUR unangetastet,
# statt mit einem veralteten Wechselkurs umzurechnen.
_EUR_ANCHOR_MAX_AGE_S = 2 * 86400


def normalize_stale_eur(
    points: list[tuple[int, float | None, float | None]],
) -> tuple[list[list[int | float | None]], int]:
    """Korrigiert fortgeschriebene EUR-Werte in der Rohaufloesung.

    Befund 15.10.2026: mempool.space liefert in der Stunden-Aufloesung fuer
    einzelne Zeitraeume (u. a. Juni/Juli 2026) einen tagelang eingefrorenen
    EUR-Wert, waehrend USD stuendlich weiterlaeuft; nur die Punkte um 00:00
    UTC tragen den richtigen Tageskurs. Im Kurschart (Zeitraum "1 Monat")
    erschien das als Zacke an jeder Mitternacht. Korrektur: die Punkte um
    00:00 UTC sind Anker fuer den EUR/USD-Kurs des Tages. Weicht ein anderer
    Punkt um mehr als _EUR_FX_TOLERANCE davon ab, wird sein EUR-Wert aus
    seinem echten USD-Wert und dem Ankerkurs berechnet. Plausible Werte,
    fehlende Werte (None) und Punkte ohne frischen Anker bleiben unveraendert;
    die DB-Tabelle btc_price_raw behaelt immer die Rohdaten.

    Erwartet nach ts aufsteigend sortierte Punkte. Gibt die Punkte und die
    Anzahl korrigierter EUR-Werte zurueck.
    """
    out: list[list[int | float | None]] = []
    fixed = 0
    anchor: float | None = None  # USD je EUR am juengsten Tagesanker
    anchor_ts = 0
    for ts, eur, usd in points:
        if ts % 86400 == 0 and eur and usd:
            anchor, anchor_ts = usd / eur, ts
        elif (
            anchor is not None
            and eur
            and usd
            and ts - anchor_ts <= _EUR_ANCHOR_MAX_AGE_S
            and abs(usd / eur / anchor - 1) > _EUR_FX_TOLERANCE
        ):
            eur = round(usd / anchor, 2)
            fixed += 1
        out.append([ts, eur, usd])
    return out, fixed


# Einzelpunkt-Ausreisser in der Stundenaufloesung: weicht ein Punkt von BEIDEN
# Nachbarn (je hoechstens 1 h entfernt, untereinander einig) um mehr als das
# ab, faellt er aus dem Export.
_OUTLIER_TOLERANCE = 0.02
_OUTLIER_NEIGHBOUR_S = 3600


def drop_isolated_outliers(
    points: list[list[int | float | None]],
) -> tuple[list[list[int | float | None]], int]:
    """Entfernt einzelne Ausreisser-Punkte innerhalb der Stundenaufloesung.

    Befund 15.10.2026: mempool.space mischt an manchen Mitternachten einen
    Tageswert aus einer anderen Quelle in die Stundenreihe, der in BEIDEN
    Waehrungen 3-5 % neben den Stundenwerten davor und danach liegt (Zacke im
    Kurschart). Ein Punkt faellt nur weg, wenn beide Nachbarn hoechstens
    _OUTLIER_NEIGHBOUR_S entfernt sind, sich untereinander auf
    _OUTLIER_TOLERANCE einig sind und der Punkt von beiden um mehr als das
    abweicht (je Waehrung geprueft, eine genuegt). Tages-/Wochenaufloesung
    (Nachbarn weiter weg) bleibt unberuehrt, echte Kursspruenge ueber mehrere
    Stunden ebenfalls. Es wird nichts interpoliert, nur weggelassen; die
    DB-Tabelle btc_price_raw behaelt den Punkt.
    """

    def off(a: float | None, b: float | None) -> bool:
        return bool(a and b and abs(a - b) / b > _OUTLIER_TOLERANCE)

    keep: list[list[int | float | None]] = []
    dropped = 0
    for i, p in enumerate(points):
        if 0 < i < len(points) - 1:
            prev, nxt = points[i - 1], points[i + 1]
            close = (
                int(p[0] or 0) - int(prev[0] or 0) <= _OUTLIER_NEIGHBOUR_S
                and int(nxt[0] or 0) - int(p[0] or 0) <= _OUTLIER_NEIGHBOUR_S
            )
            if close and any(
                off(p[k], prev[k]) and off(p[k], nxt[k]) and not off(prev[k], nxt[k])
                for k in (1, 2)
            ):
                dropped += 1
                continue
        keep.append(p)
    return keep, dropped


def export_full_artifact(
    conn: sqlite3.Connection, now: datetime | None = None
) -> dict[str, object]:
    """Exportiert die GESAMTE Rohaufloesung (btc_price_raw) als JSON fuer den
    dynamischen BitcoinInfo-Kurschart (views/btc_kurs_chart.yaml). Anders als
    export_artifact() (90-Tage-EUR-Trend) kein Zeitfenster: die
    Zeitraum-Buttons (1 Tag ... Max) filtern client-seitig aus derselben
    vollen Reihe, mempool.space liefert ohnehin schon eine mit dem Alter
    coarser werdende Aufloesung (stuendlich -> taeglich -> woechentlich), ein
    serverseitiger Cutoff wuerde nur Punkte wegwerfen, die die kurzen
    Zeitraeume brauchen."""
    now = now or datetime.now(timezone.utc)
    rows = conn.execute(
        "SELECT ts, price_eur, price_usd FROM btc_price_raw ORDER BY ts"
    ).fetchall()
    points, fixed = normalize_stale_eur(rows)
    points, dropped = drop_isolated_outliers(points)
    if fixed or dropped:
        log.info(
            "Export: %d fortgeschriebene EUR-Werte korrigiert, %d Ausreisser entfernt",
            fixed,
            dropped,
        )
    return {
        "generated_at": now.isoformat(),
        "points": points,
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
    parser.add_argument(
        "--full-out",
        default="src/ha/config/www/btc_price_full.json",
        help="Zielpfad fuer das rohaufgeloeste EUR+USD-Artefakt "
        "(views/btc_kurs_chart.yaml, Zeitraum-Buttons 1 Tag ... Max).",
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

    log.info("Hole EUR+USD-Rohaufloesung von %s ...", base_url)
    raw_prices = fetch_historical_prices_dual(base_url)
    if not raw_prices:
        log.error("Keine Rohpreisdaten erhalten - Abbruch.")
        raise SystemExit(1)

    conn = get_connection(args.db)
    try:
        written = sync_to_db(conn, daily)
        artifact = export_artifact(conn, args.days)
        written_raw = sync_raw_to_db(conn, raw_prices)
        full_artifact = export_full_artifact(conn)
    finally:
        conn.close()

    artifact_days = artifact["days"]
    assert isinstance(artifact_days, list)
    if not artifact_days:
        log.error(
            "Export-Fenster (%d Tage) enthaelt keine Zeilen - Abbruch.", args.days
        )
        raise SystemExit(1)

    full_points = full_artifact["points"]
    assert isinstance(full_points, list)
    if not full_points:
        log.error("Rohaufloesungs-Export enthaelt keine Zeilen - Abbruch.")
        raise SystemExit(1)

    full_out_path = args.full_out
    os.makedirs(os.path.dirname(full_out_path) or ".", exist_ok=True)
    with open(full_out_path, "w", encoding="utf-8") as f:
        json.dump(full_artifact, f, separators=(",", ":"))
    full_size_kb = os.path.getsize(full_out_path) / 1024
    print(
        f"Sync: {written_raw} Rohpunkte nach {args.db} (btc_price_raw). "
        f"Export: {full_out_path} ({full_size_kb:.0f} KB, {len(full_points)} Punkte)"
    )

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
