"""
Nightly — die Nachtkette: Daten holen, verdichten, Faktenbericht schreiben.

Laeuft auf der Umbrel, wenn das Haus ruht. Vier Schritte, streng nacheinander,
weil Ollama pro Modell nur eine Anfrage gleichzeitig bedient und der Agent
danach ungestoert arbeiten soll:

    1. HA-History nachziehen (energy_states, device_states, miner_states)
    2. Luecken pruefen und melden
    3. Tagesaggregate neu berechnen (daily_kpi, daily_miner_kpi)
    4. Faktenbericht des Vortags in den Obsidian-Vault schreiben

Bewusst **ohne Sprachmodell**. Jede Zahl hier ist gezaehlt oder gerechnet, das
Ergebnis ist bei erneutem Lauf identisch. Die Deutung passiert getrennt davon
durch den Nachtforscher, der diesen Bericht liest.

Schlaegt ein Schritt fehl, laufen die folgenden trotzdem: ein fehlender Sync
soll nicht verhindern, dass aus den vorhandenen Daten ein Bericht entsteht. Der
Fehler steht dann im Log und im Bericht.

CLI:
    python -m src.data.nightly                  # gestern
    python -m src.data.nightly --date 2026-07-20
    python -m src.data.nightly --days 3         # letzte 3 Tage nachziehen

Env:
    UMBREL_HOST, HA_PORT, HA_TOKEN   HA-Zugang
    BITGRID_DB                        DB-Pfad (default: data/bitgrid.db)
    VAULT_DIR                         Zielordner fuer den Faktenbericht
"""

from __future__ import annotations

import argparse
import logging
import os
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from src.data.daily_kpi import days_in_db, rebuild
from src.data.daily_report import build_report, _fetch_sun
from src.data.db import get_connection
from src.data.gap_check import find_gaps
from src.data.ha_history_sync import _ha_url, sync, sync_devices, sync_miners

log = logging.getLogger("nightly")


def _schritt(name: str, fn: object) -> str:
    """Fuehrt einen Schritt aus und faengt Fehler ab, damit die Kette weiterlaeuft."""
    try:
        ergebnis = fn()  # type: ignore[operator]
        log.info("%s: %s", name, ergebnis)
        return f"{name}: {ergebnis}"
    except Exception as exc:  # noqa: BLE001 - ein Schritt darf die Nacht nicht kippen
        log.error("%s FEHLGESCHLAGEN: %s", name, exc)
        log.debug(traceback.format_exc())
        return f"{name}: FEHLER {exc}"


def run(tag: date, tage_zurueck: int, db_pfad: str, vault: Path) -> list[str]:
    host = os.getenv("UMBREL_HOST", "")
    token = os.getenv("HA_TOKEN", "")
    ha_url = _ha_url(host, os.getenv("HA_PORT", "8123"))
    ende = datetime.now(timezone.utc)
    start = ende - timedelta(days=tage_zurueck)

    conn = get_connection(db_pfad)
    protokoll: list[str] = []
    try:
        if host and token:
            protokoll.append(
                _schritt(
                    "1 Sync Bloecke",
                    lambda: "%d neu, %d vorhanden"
                    % sync(start, ende, conn, ha_url, token),
                )
            )
            protokoll.append(
                _schritt(
                    "1 Sync Geraete",
                    lambda: "%d neu, %d vorhanden"
                    % sync_devices(start, ende, conn, ha_url, token),
                )
            )
            protokoll.append(
                _schritt(
                    "1 Sync Miner",
                    lambda: "%d neu, %d vorhanden"
                    % sync_miners(start, ende, conn, ha_url, token),
                )
            )
        else:
            protokoll.append("1 Sync: uebersprungen (UMBREL_HOST/HA_TOKEN fehlen)")

        def _luecken() -> str:
            luecken = find_gaps(conn, start, ende)
            if not luecken:
                return "keine"
            minuten = sum(int((b - a).total_seconds() // 60) for a, b in luecken)
            return f"{len(luecken)} Intervalle, {minuten} min"

        protokoll.append(_schritt("2 Luecken", _luecken))

        protokoll.append(
            _schritt(
                "3 Tagesaggregate",
                lambda: f"{rebuild(conn, days_in_db(conn))} Tage berechnet",
            )
        )

        def _bericht() -> str:
            text = build_report(conn, tag, _fetch_sun(tag))
            ziel = vault / f"{tag:%Y}" / f"{tag:%m}" / f"{tag.isoformat()}_fakten.md"
            ziel.parent.mkdir(parents=True, exist_ok=True)
            ziel.write_text(text, encoding="utf-8")
            return f"{ziel} ({len(text)} Zeichen)"

        protokoll.append(_schritt("4 Faktenbericht", _bericht))
    finally:
        conn.close()
    return protokoll


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Nachtkette: Sync, Verdichtung, Bericht")
    p.add_argument("--date", default=None, help="Berichtstag (default: gestern)")
    p.add_argument(
        "--days", type=int, default=2, help="Tage rueckwaerts synchronisieren"
    )
    p.add_argument("--db", default=os.getenv("BITGRID_DB", "data/bitgrid.db"))
    p.add_argument("--vault", default=os.getenv("VAULT_DIR", "vault"))
    return p.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = _parse_args()
    tag = (
        date.fromisoformat(args.date)
        if args.date
        else (datetime.now(timezone.utc) - timedelta(days=1)).date()
    )
    log.info("=== Nachtkette fuer %s ===", tag.isoformat())
    protokoll = run(tag, args.days, args.db, Path(args.vault))
    log.info("=== fertig ===")
    for zeile in protokoll:
        print(zeile)


if __name__ == "__main__":
    main()
