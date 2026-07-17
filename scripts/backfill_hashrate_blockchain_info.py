"""
backfill_hashrate_blockchain_info.py — EINMALIGES, manuell auszuführendes
Backfill-Skript für die Hashrate-Vorgeschichte (2009 bis kurz vor dem lokal
indizierten Zeitraum der self-hosted mempool.space-Instanz).

Bewusste Ausnahme von ADR-001/011 (Local-First, keine externen Cloud-APIs):
die self-hosted mempool-Instanz indiziert Hashrate nur für den Zeitraum, den
sie selbst mit ihrem konfigurierten INDEXING_BLOCKS_AMOUNT abgedeckt hat
(aktuell ~1 Jahr) — kein Backfill seit Genesis wie bei der Preishistorie.
Um trotzdem einen echten Log-Log-Chart über die volle Historie zu zeigen
(views/ki_hashrate.yaml), wird EINMALIG blockchain.info/charts (öffentliche,
unauthentifizierte Chart-API, keine Kontoanmeldung) als Fremdquelle für die
Vorgeschichte gezogen. Siehe ADR-024 (docs/architecture/09_design_decisions/
091_adr_de.md).

WICHTIG — Abgrenzung zum laufenden Betrieb:
- Dieses Skript ist NICHT Teil von src/data/ (Laufzeit-Datenschicht) und wird
  NICHT von btc_hashrate.py aufgerufen. Es läuft nur, wenn ein Mensch es
  manuell startet.
- Es schreibt eine STATISCHE Seed-Datei (src/data/btc_hashrate_seed.json),
  die danach ins Repo eingecheckt wird. Der reguläre Betrieb (btc_hashrate.py)
  liest diese Datei nur noch lokal von der Festplatte, ohne erneuten
  Netzwerkzugriff auf blockchain.info.
- Bei Bedarf (z. B. genauere Quelle, Lizenzbedenken) kann die Seed-Datei
  jederzeit ersetzt oder entfernt werden, ohne dass der reguläre Betrieb
  bricht (btc_hashrate.py funktioniert auch ganz ohne Seed-Datei, dann nur
  mit dem vom lokalen Node abgedeckten Zeitraum).

CLI:
    python -m scripts.backfill_hashrate_blockchain_info
    python -m scripts.backfill_hashrate_blockchain_info --out src/data/btc_hashrate_seed.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import urlopen

log = logging.getLogger(__name__)

_SOURCE_URL = "https://api.blockchain.info/charts/hash-rate?timespan=all&format=json"
_TH = 1e12  # 1 TH/s = 1e12 H/s
_EH = 1e18  # 1 EH/s = 1e18 H/s


def fetch_blockchain_info_hashrate(
    url: str = _SOURCE_URL, timeout: int = 30
) -> list[tuple[int, float]]:
    """
    Ruft die öffentliche blockchain.info-Chart-API ab. Gibt (unix_ts,
    hashrate_ehs) sortiert aufsteigend zurück. Die API liefert Werte in
    TH/s (siehe unit-Feld der Antwort), umgerechnet auf EH/s zur
    Konsistenz mit btc_hashrate.py.
    """
    try:
        with urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
    except URLError as exc:
        log.error("blockchain.info nicht erreichbar: %s", exc)
        return []
    except json.JSONDecodeError as exc:
        log.error("blockchain.info-Antwort kein gültiges JSON: %s", exc)
        return []

    raw = payload.get("values", [])
    out: list[tuple[int, float]] = []
    for entry in raw:
        ts = entry.get("x")
        th = entry.get("y")
        if ts is None or th is None or th <= 0:
            continue
        out.append((int(ts), float(th) * _TH / _EH))
    return sorted(out, key=lambda x: x[0])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EINMALIGES Backfill der Hashrate-Vorgeschichte von "
        "blockchain.info als Seed-Datei für btc_hashrate.py (siehe ADR-024)."
    )
    parser.add_argument(
        "--out",
        default="src/data/btc_hashrate_seed.json",
        help="Zielpfad für die Seed-Datei",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    args = _parse_args()

    log.info("Hole Hashrate-Vorgeschichte von %s ...", _SOURCE_URL)
    points = fetch_blockchain_info_hashrate()
    if not points:
        log.error("Keine Daten von blockchain.info erhalten - Abbruch.")
        raise SystemExit(1)

    seed = {
        "source": "blockchain.info charts API (Hash Rate, TH/s -> EH/s umgerechnet)",
        "source_url": _SOURCE_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "note": "Einmaliges manuelles Backfill (ADR-024), kein Live-Zugriff im "
        "regulären Betrieb. btc_hashrate.py bevorzugt bei Überschneidung "
        "immer die lokal von mempool.space gemessenen Werte.",
        "unit": "EH/s",
        # Kein fixes round(v, n): die Reihe reicht von ~1e-13 EH/s (2009)
        # bis ~900 EH/s (heute) - eine feste Nachkommastellenzahl würde die
        # frühen Werte auf 0.0 abschneiden. Volle Float-Praezision behalten.
        "points": [[ts, v] for ts, v in points],
    }

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(seed, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_path) / 1024
    print(f"Geschrieben: {out_path} ({size_kb:.0f} KB, {len(points)} Datenpunkte)")


if __name__ == "__main__":
    main()
