"""
BtcDifficulty — zieht Difficulty-Adjustment-Status und aktuelle Blockhoehe von
der self-hosted mempool.space-Instanz fuer die Schwierigkeits-/Halbierungs-
Karte im Bitsy-Tab (KI-Tab, Markteinordnung, views/ki_difficulty.yaml).

Kein Steuerpfad: dieses Modul liefert Netzwerkkontext fuer die Erklaerschicht
(read-only), es beeinflusst keine Mining-Entscheidung in core/.

Datenquelle (rein lokal, self-hosted, kein Live-Zugriff vom Wandtablet):
    /api/v1/difficulty-adjustment und /api/blocks/tip/height der self-hosted
    mempool.space-Instanz. Beide Werte kommen aus derselben Quelle wie
    btc_hashrate.py und btc_power_law.py (MEMPOOL_HOST/MEMPOOL_PORT aus .env).

Zwei unterschiedliche Zeithorizonte, zwei unterschiedliche Schaetzmethoden
(bewusst getrennt, kein Overstating durch eine einzige Methode fuer beide):
    - Naechster Retarget (~2 Wochen entfernt): remaining_days kommt direkt aus
      dem von mempool.space gelieferten remainingTime-Feld. mempool errechnet
      das intern aus dem laufenden Difficulty-Epoch (adjustedTimeAvg) - fuer
      einen so kurzen Horizont ist der aktuelle Epochen-Durchschnitt die
      sinnvollste Schaetzbasis.
    - Naechste Halbierung (>1 Jahr entfernt): hierfuer waere derselbe
      kurzfristige Epochen-Durchschnitt irrefuehrend praezise (er schwankt von
      Epoche zu Epoche +/-10-15%, siehe difficulty_change_pct). Verwendet wird
      stattdessen die Bitcoin-Protokollkonstante DESIGN_BLOCK_TIME_SECONDS
      (Ziel-Blockzeit 600s), eine feste Designgroesse, kein empirischer Fit.
      Das ist dieselbe Zurueckhaltung wie bei der Hashrate-Trendlinie
      (btc_hashrate.py, _DEFAULT_FUTURE_DAYS=0): lieber transparent grob als
      falsch praezise.

CLI:
    python -m src.data.btc_difficulty
    python -m src.data.btc_difficulty --out src/ha/config/www/btc_difficulty.json

Env-Vars (aus .env):
    MEMPOOL_HOST — IP der self-hosted mempool.space-Instanz
    MEMPOOL_PORT — Port (default: 3006)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import urlopen

log = logging.getLogger(__name__)

_DEFAULT_PORT = "3006"
HALVING_INTERVAL_BLOCKS = 210_000
DESIGN_BLOCK_TIME_SECONDS = 600.0  # Bitcoin-Protokollkonstante (Ziel-Blockzeit)

_REQUIRED_DIFF_FIELDS = (
    "difficultyChange",
    "remainingBlocks",
    "remainingTime",
    "previousRetarget",
    "nextRetargetHeight",
)


def fetch_difficulty_adjustment(
    base_url: str, timeout: int = 30
) -> dict[str, float] | None:
    """
    Ruft /api/v1/difficulty-adjustment ab. Gibt die fuer die Karte benoetigten
    Felder zurueck, oder None bei Netzwerkfehler, ungueltigem JSON oder falls
    Pflichtfelder in der Antwort fehlen (fail-closed statt mit Luecken
    weiterzurechnen).
    """
    url = f"{base_url}/api/v1/difficulty-adjustment"
    try:
        with urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
    except URLError as exc:
        log.error("Mempool-Instanz nicht erreichbar: %s", exc)
        return None
    except json.JSONDecodeError as exc:
        log.error(
            "Mempool-Antwort (difficulty-adjustment) kein gueltiges JSON: %s", exc
        )
        return None

    if any(payload.get(f) is None for f in _REQUIRED_DIFF_FIELDS):
        log.error("Mempool-Antwort (difficulty-adjustment) unvollstaendig: %s", payload)
        return None

    return {f: float(payload[f]) for f in _REQUIRED_DIFF_FIELDS}


def fetch_tip_height(base_url: str, timeout: int = 30) -> int | None:
    """
    Ruft /api/blocks/tip/height ab (Klartext-Integer, kein JSON). Gibt None
    bei Netzwerkfehler oder nicht-parsbarer Antwort zurueck.
    """
    url = f"{base_url}/api/blocks/tip/height"
    try:
        with urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode().strip()
    except URLError as exc:
        log.error("Mempool-Instanz nicht erreichbar: %s", exc)
        return None
    try:
        return int(body)
    except ValueError:
        log.error("Mempool-Antwort (tip height) keine gueltige Zahl: %r", body)
        return None


def compute_next_halving(
    height: int, interval: int = HALVING_INTERVAL_BLOCKS
) -> tuple[int, int]:
    """
    Gibt (next_halving_height, remaining_blocks) zurueck. Liegt height exakt
    auf einer Halbierungshoehe, zaehlt das als bereits erreicht - es wird die
    naechste, noch ausstehende Halbierung berechnet.
    """
    next_halving_height = (height // interval + 1) * interval
    return next_halving_height, next_halving_height - height


def build_artifact(
    diff: dict[str, float], height: int, now: datetime | None = None
) -> dict[str, object]:
    """
    JSON-Artefakt fuer das Dashboard (views/ki_difficulty.yaml). Siehe
    Modul-Docstring fuer die zwei getrennten Schaetzmethoden (Retarget vs.
    Halbierung).
    """
    now = now or datetime.now(timezone.utc)
    next_halving_height, remaining_halving_blocks = compute_next_halving(height)
    halving_seconds = remaining_halving_blocks * DESIGN_BLOCK_TIME_SECONDS
    halving_date = now + timedelta(seconds=halving_seconds)

    return {
        "generated_at": now.isoformat(),
        "block_height": height,
        "remaining_blocks": int(diff["remainingBlocks"]),
        "remaining_days": diff["remainingTime"] / 1000 / 86400,
        "difficulty_change_pct": diff["difficultyChange"],
        "previous_retarget_pct": diff["previousRetarget"],
        "next_retarget_height": int(diff["nextRetargetHeight"]),
        "next_halving_height": next_halving_height,
        "next_halving_remaining_blocks": remaining_halving_blocks,
        "next_halving_date": halving_date.isoformat(),
        "next_halving_remaining_days": halving_seconds / 86400,
        "halving_block_time_seconds": DESIGN_BLOCK_TIME_SECONDS,
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
        description="Zieht Difficulty-Adjustment-Status und Blockhoehe von "
        "mempool.space und schreibt sie als JSON fuer den Bitsy-Tab."
    )
    parser.add_argument(
        "--out",
        default="src/ha/config/www/btc_difficulty.json",
        help="Zielpfad fuer das JSON-Artefakt",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    _load_dotenv()
    args = _parse_args()

    base_url = _mempool_base_url()
    log.info("Hole Difficulty-Adjustment-Status von %s ...", base_url)
    diff = fetch_difficulty_adjustment(base_url)
    height = fetch_tip_height(base_url)

    if diff is None or height is None:
        log.error("Difficulty-Adjustment oder Blockhoehe nicht verfuegbar - Abbruch.")
        raise SystemExit(1)

    artifact = build_artifact(diff, height)
    log.info(
        "Retarget in %d Bloecken (~%.1f Tage, %.2f%%), Halbierung in %d Bloecken (~%.0f Tage)",
        artifact["remaining_blocks"],
        artifact["remaining_days"],
        artifact["difficulty_change_pct"],
        artifact["next_halving_remaining_blocks"],
        artifact["next_halving_remaining_days"],
    )

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, separators=(",", ":"))

    print(f"Geschrieben: {out_path}")


if __name__ == "__main__":
    main()
