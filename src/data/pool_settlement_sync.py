"""
PoolSettlementSync — synchronisiert taegliche F2Pool-Abrechnungen (BTC/Sats)
nach bitcoin_daily_settlement.

Warum ein eigenes Skript statt einer Erweiterung von ha_history_sync.py:
F2Pool-Abrechnungen sind Tages-, kein 10-Minuten-Raster (siehe db.py-
Kommentar zu bitcoin_daily_settlement), und die Quelle ist eine Attribut-
Liste (sensor.pool_settlement_history), keine HA-History-Zeitreihe.

Kein Steuerpfad: dieses Modul fuellt eine reine Rohdaten-Tabelle, liest nie
zurueck in core/ und beeinflusst keine Mining-Entscheidung — gleiche
Zurueckhaltung wie btc_power_law.py/btc_hashrate.py/btc_difficulty.py.

Datenquelle: HAs bereits autorisierte REST-API (kein zweiter F2Pool-Zugriff
mit eigenem Secret/eigener IP-Whitelist-Pflege, siehe packages/pool.yaml,
das genau diesen Ausfall — vier Wochen unbemerkt — schon einmal erlebt hat).
  - Primaer: sensor.pool_settlement_history, Attribut "transactions"
    (F2Pool V2 API, stuendlich aktualisiert). mining_date ist der
    Abrechnungs-Zeitstempel (Unix, UTC); der eigentliche Mining-Tag ist
    mining_date minus 1 Tag (F2Pool rechnet den Vortag erst am naechsten
    Morgen ab, siehe packages/pool.yaml Kommentar zu pool_capture_daily_btc).
    Gleiche Umrechnung wie bereits im Dashboard (views/mining_log.yaml).
  - Fallback (nur fuer Luecken): input_text.pool_btc_daily_log /
    pool_ths_daily_log. Diese Tage sind Berlin-lokal beschriftet (die
    HA-Automation nutzt now(), keine feste UTC-Zeitzone) — anders als der
    Primaerpfad, der ueber den Unix-Zeitstempel exakt UTC ist. Wird in der
    source-Spalte markiert statt stillschweigend gleichgesetzt.

btc_eur_price_approx ist eine reine Kontext-Spalte (der aktuelle Kurs beim
Sync-Lauf, i. d. R. ~04:00 des Folgetags), nicht der exakte Tagesdurchschnitt
oder Eroeffnungskurs. Die eigentliche Kennzahl energy_to_sats (siehe
daily_kpi.py) ist rein BTC-denominiert und haengt nicht von dieser Spalte ab.

CLI:
    python -m src.data.pool_settlement_sync              # letzte 7 Tage
    python -m src.data.pool_settlement_sync --days 30
    python -m src.data.pool_settlement_sync --from 2026-08-01

Env-Vars (aus .env):
    UMBREL_HOST — HA-Host-IP
    HA_PORT     — HA-Port (default: 8123)
    HA_TOKEN    — Long-Lived Access Token
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.data.db import get_connection

log = logging.getLogger(__name__)

_UMBREL_HOST = os.getenv("UMBREL_HOST", "")
_HA_PORT = os.getenv("HA_PORT", "8123")
_HA_TOKEN = os.getenv("HA_TOKEN", "")

_SETTLEMENT_ENTITY = "sensor.pool_settlement_history"
_BTC_LOG_ENTITY = "input_text.pool_btc_daily_log"
_THS_LOG_ENTITY = "input_text.pool_ths_daily_log"
_PRICE_ENTITY = "sensor.btc_eur_price"

_SOURCE_PRIMARY = "ha:pool_settlement_history"
_SOURCE_FALLBACK = "ha:pool_btc_daily_log"


def _ha_url(host: str, port: str) -> str:
    return f"http://{host}:{port}"


def fetch_entity_state(
    entity_id: str, ha_base_url: str, token: str, timeout: int = 30
) -> dict[str, object] | None:
    """
    Ruft den aktuellen Zustand einer einzelnen HA-Entity ab (/api/states/<id>).
    Gibt None bei Netzwerkfehler, ungueltigem JSON oder 4xx/5xx zurueck.
    """
    req = Request(
        f"{ha_base_url}/api/states/{entity_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            result: dict[str, object] = json.loads(resp.read().decode())
            return result
    except URLError as exc:
        log.error("HA-Entity %s nicht abrufbar: %s", entity_id, exc)
        return None
    except json.JSONDecodeError as exc:
        log.error("HA-Antwort fuer %s kein gueltiges JSON: %s", entity_id, exc)
        return None


def _settlement_day(mining_date_unix: float) -> str:
    """
    UTC-Kalendertag des tatsaechlichen Minings, aus dem F2Pool-Abrechnungs-
    Zeitstempel (mining_date, Unix-Sekunden). F2Pool rechnet den Vortag am
    naechsten Morgen ab, deshalb minus 1 Tag — gleiche Umrechnung wie in
    views/mining_log.yaml.
    """
    settled = datetime.fromtimestamp(mining_date_unix, tz=timezone.utc)
    mined = settled - timedelta(days=1)
    return mined.date().isoformat()


def parse_settlement_transactions(
    transactions: list[object],
) -> dict[str, tuple[float, float | None]]:
    """
    Wertet die "transactions"-Liste von sensor.pool_settlement_history aus.
    Gibt {tag: (earned_btc, pool_ths_avg)} zurueck, ein Eintrag pro Tag mit
    positivem Ertrag (Null-/Negativbetraege werden ignoriert — keine
    erfundene Abrechnung fuer einen Tag ohne Zahlung).
    """
    result: dict[str, tuple[float, float | None]] = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        extra = tx.get("mining_extra")
        if not isinstance(extra, dict):
            continue
        hash_rate = extra.get("hash_rate")
        mining_date = extra.get("mining_date")
        if not hash_rate or not mining_date:
            continue
        amount = tx.get("amount", tx.get("changed_balance"))
        try:
            btc = float(amount)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if btc <= 0:
            continue
        try:
            day = _settlement_day(float(mining_date))
            ths = float(hash_rate) / 1e12
        except (TypeError, ValueError):
            continue
        result[day] = (btc, ths)
    return result


def parse_daily_log(raw: str) -> dict[str, float]:
    """
    Parst die Pipe-separierten Fallback-Logs (pool_btc_daily_log /
    pool_ths_daily_log), Format "YYYY-MM-DD,wert|YYYY-MM-DD,wert|...".
    Tage sind Berlin-lokal beschriftet — nur als Luecken-Fallback gedacht,
    siehe Modul-Docstring.
    """
    result: dict[str, float] = {}
    if not raw or raw in ("unknown", "unavailable"):
        return result
    for entry in raw.split("|"):
        day, _, value = entry.partition(",")
        if not day or not value:
            continue
        try:
            result[day] = float(value)
        except ValueError:
            continue
    return result


def sync(
    conn: sqlite3.Connection,
    ha_base_url: str,
    token: str,
    since: date,
) -> tuple[int, int]:
    """
    Synchronisiert F2Pool-Tagesabrechnungen ab `since` (einschliesslich) in
    bitcoin_daily_settlement. Bestehende Eintraege werden nie ueberschrieben
    (INSERT OR IGNORE) — ein Rohfakt, kein rekonstruierbares Aggregat.

    Gibt (neue_tage, uebersprungene_tage) zurueck.
    """
    settlement_state = fetch_entity_state(_SETTLEMENT_ENTITY, ha_base_url, token)
    transactions: list[object] = []
    if settlement_state is not None:
        attrs = settlement_state.get("attributes")
        if isinstance(attrs, dict):
            transactions = attrs.get("transactions") or []
    primary = parse_settlement_transactions(transactions)

    btc_log_state = fetch_entity_state(_BTC_LOG_ENTITY, ha_base_url, token)
    ths_log_state = fetch_entity_state(_THS_LOG_ENTITY, ha_base_url, token)
    fallback_btc = parse_daily_log(
        str(btc_log_state.get("state", "")) if btc_log_state else ""
    )
    fallback_ths = parse_daily_log(
        str(ths_log_state.get("state", "")) if ths_log_state else ""
    )

    price_state = fetch_entity_state(_PRICE_ENTITY, ha_base_url, token)
    price_now: float | None = None
    if price_state is not None:
        try:
            price_now = float(str(price_state.get("state")))
        except (TypeError, ValueError):
            price_now = None

    since_str = since.isoformat()
    days: dict[str, tuple[float, float | None, str]] = {}
    for day, (btc, ths) in primary.items():
        if day >= since_str:
            days[day] = (btc, ths, _SOURCE_PRIMARY)
    for day, btc in fallback_btc.items():
        if day >= since_str and day not in days:
            days[day] = (btc, fallback_ths.get(day), _SOURCE_FALLBACK)

    if not days:
        log.warning("Keine Abrechnungsdaten von HA erhalten — Sync uebersprungen.")
        return 0, 0

    now = datetime.now(timezone.utc).isoformat()
    added = 0
    skipped = 0
    for day, (btc, ths, source) in sorted(days.items()):
        cur = conn.execute(
            "INSERT OR IGNORE INTO bitcoin_daily_settlement"
            " (day, earned_btc, pool_ths_avg, btc_eur_price_approx, source, captured_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (day, btc, ths, price_now, source, now),
        )
        if cur.rowcount:
            added += 1
        else:
            skipped += 1
    conn.commit()

    log.info("Settlement-Sync fertig: %d neu, %d bereits vorhanden", added, skipped)
    return added, skipped


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
        description="Synchronisiert F2Pool-Tagesabrechnungen (BTC/Sats) "
        "nach bitcoin_daily_settlement"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Letzte N Tage synchronisieren (default: 7)",
    )
    parser.add_argument(
        "--from",
        dest="from_date",
        metavar="YYYY-MM-DD",
        help="Startdatum (ueberschreibt --days)",
    )
    parser.add_argument("--db", default="data/bitgrid.db")
    parser.add_argument(
        "--ha-url",
        default=None,
        help="HA Base URL (default: http://UMBREL_HOST:HA_PORT)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    _load_dotenv()

    host = os.getenv("UMBREL_HOST", _UMBREL_HOST)
    port = os.getenv("HA_PORT", _HA_PORT)
    token = os.getenv("HA_TOKEN", _HA_TOKEN)

    if not host:
        log.error("UMBREL_HOST nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)
    if not token:
        log.error("HA_TOKEN nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)

    args = _parse_args()
    ha_url = args.ha_url or _ha_url(host, port)

    if args.from_date:
        since = date.fromisoformat(args.from_date)
    else:
        since = datetime.now(timezone.utc).date() - timedelta(days=args.days)

    conn = get_connection(args.db)
    try:
        added, skipped = sync(conn, ha_url, token, since)
        print(f"Settlement-Sync: +{added} neue Tage, {skipped} uebersprungen")
        if added == 0 and skipped == 0:
            print("Warnung: Keine Daten empfangen — HA erreichbar?")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
