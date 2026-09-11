"""
bitcoin_kpi_sync.py -- taeglicher Wrapper: Settlement-Sync -> daily_kpi
Neuberechnung -> Energy-to-Sats-Export, in dieser Reihenfolge.

Warum ein Wrapper statt drei separate Scheduled Tasks: die drei Schritte
haben eine echte Reihenfolge-Abhaengigkeit. src.data.pool_settlement_sync
fuellt bitcoin_daily_settlement, aber daily_kpi.energy_to_sats fuer den
betroffenen Tag wird nur beim NAECHSTEN daily_kpi-Lauf neu berechnet
(compute_day() liest bitcoin_daily_settlement nur zum Aufrufzeitpunkt). Ohne
diesen Wrapper bliebe energy_to_sats fuer frisch gesyncte Tage bis zum
naechsten regulaeren daily_kpi-Lauf auf NULL haengen — und der laeuft laut
nightly_and_sync.py um 00:20, VOR diesem Sync.

Gedacht fuer einen taeglichen Windows Scheduled Task um ~04:00 lokal, NACH
dem F2Pool-Settlement (verbucht erst gegen 02:00, siehe packages/pool.yaml
Kommentar zu pool_capture_daily_btc). Idempotent (jeder Schritt ist es fuer
sich: INSERT OR IGNORE / INSERT OR REPLACE / reiner Export) — ein verpasster
oder doppelter Lauf richtet keinen Schaden an.

CLI:
    python scripts\\bitcoin_kpi_sync.py

Env-Vars (aus .env):
    UMBREL_HOST, HA_PORT, HA_TOKEN
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.data.daily_kpi import rebuild  # noqa: E402
from src.data.db import get_connection  # noqa: E402
from src.data.energy_to_sats_export import build_artifact, fetch_series  # noqa: E402
from src.data.pool_settlement_sync import _ha_url  # noqa: E402
from src.data.pool_settlement_sync import sync as sync_settlement  # noqa: E402

log = logging.getLogger("bitcoin_kpi_sync")

# Genug Puffer, um Nachtraege (verpasster Lauf, spaeter nachgetragene
# HA-Sensoren) automatisch aufzuholen, ohne bei jedem Lauf die komplette
# Historie neu zu berechnen (das macht schon nightly.py separat um 00:20).
_REBUILD_DAYS = 10
_EXPORT_DAYS = 30


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    load_dotenv(REPO_ROOT / ".env")

    host = os.getenv("UMBREL_HOST", "")
    port = os.getenv("HA_PORT", "8123")
    token = os.getenv("HA_TOKEN", "")
    if not host or not token:
        log.error("UMBREL_HOST/HA_TOKEN nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)

    db_path = REPO_ROOT / "data" / "bitgrid.db"
    conn = get_connection(db_path)
    try:
        since = datetime.now(timezone.utc).date() - timedelta(days=_REBUILD_DAYS)
        added, skipped = sync_settlement(conn, _ha_url(host, port), token, since)
        log.info("Settlement-Sync: +%d neue Tage, %d uebersprungen", added, skipped)

        days = [
            since + timedelta(days=i)
            for i in range((datetime.now(timezone.utc).date() - since).days + 1)
        ]
        written = rebuild(conn, days)
        log.info("daily_kpi: %d Tage neu berechnet", written)

        series = fetch_series(conn, _EXPORT_DAYS)
    finally:
        conn.close()

    artifact = build_artifact(series)
    out_path = REPO_ROOT / "src" / "ha" / "config" / "www" / "energy_to_sats.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, separators=(",", ":"))
    log.info("Energy-to-Sats-Export geschrieben: %s (%d Tage)", out_path, len(series))


if __name__ == "__main__":
    main()
