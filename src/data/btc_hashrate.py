"""
BtcHashrate — zieht die Netzwerk-Hashrate-Historie von der self-hosted
mempool.space-Instanz für den Hashrate-Chart im ₿itsy-Tab (KI-Tab,
Markteinordnung, views/ki_hashrate.yaml).

Kein Steuerpfad: dieses Modul liefert Netzwerkkontext für die Erklärschicht
(read-only), es beeinflusst keine Mining-Entscheidung in core/.

Datenquelle (regulärer Betrieb, rein lokal):
    /api/v1/mining/hashrate/{interval} der self-hosted mempool.space-Instanz.
    Deckt nur den Zeitraum ab, den der lokale Node bereits indiziert hat
    (aktuell ca. 1 Jahr) — kein Backfill seit Genesis wie bei der
    Preishistorie (btc_power_law.py, externer Marktdaten-Feed seit 2010).

Vorgeschichte (einmalig, siehe ADR-024):
    Für die Zeit VOR dem lokal indizierten Zeitraum wird optional eine
    einmalig erzeugte Seed-Datei (btc_hashrate_seed.json, siehe
    scripts/backfill_hashrate_blockchain_info.py) mitgeladen. Dieses Modul
    selbst greift dafür NIE live auf blockchain.info zu — es liest nur die
    lokal abgelegte, bereits gezogene Seed-Datei. Bei Überschneidung haben
    die live von mempool.space gemessenen Werte immer Vorrang (siehe
    merge_with_seed).

    Ohne Seed-Datei funktioniert dieses Modul unverändert, dann eben nur
    mit dem vom lokalen Node abgedeckten Zeitraum (kein Fehler, kein
    Netzwerkzugriff auf eine Fremdquelle).

Fit: log10(hashrate_ehs) = a + b * log10(days_since_genesis), dieselbe
Log-Log-OLS-Regression wie beim Preis (btc_power_law.fit_power_law,
wiederverwendet statt dupliziert). Rein deskriptiver Trend, KEIN etabliertes
Modell wie die BTC-Preis-Power-Law-Heuristik — die Karte weist das explizit
aus (wissenschaftliche Sauberkeit: kein Overstating).

CLI:
    python -m src.data.btc_hashrate
    python -m src.data.btc_hashrate --out src/ha/config/www/btc_hashrate.json

Env-Vars (aus .env):
    MEMPOOL_HOST — IP der self-hosted mempool.space-Instanz
    MEMPOOL_PORT — Port (default: 3006)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import date, datetime, timezone
from urllib.error import URLError
from urllib.request import urlopen

from src.data.btc_power_law import (
    GENESIS_DATE,
    PowerLawFit,
    downsample_daily,
    fit_power_law,
)

log = logging.getLogger(__name__)

_DEFAULT_PORT = "3006"
_DEFAULT_INTERVAL = "all"
_DEFAULT_K = 2.0
# Bewusst 0 (kein Vorschau-Fenster wie beim Preis-Chart): bei b~9-10 würde
# schon eine Projektion von wenigen Jahren auf absurde EH/s-Werte führen
# (Extrapolation eines rein deskriptiven Fits ohne etablierte Theorie
# dahinter, anders als beim Preis) - Overstating-Risiko. Die Trendlinie wird
# daher nur über den tatsächlichen Datenbereich gezeichnet, nicht darüber
# hinaus projiziert.
_DEFAULT_FUTURE_DAYS = 0
_EH = 1e18  # 1 EH/s = 1e18 H/s


def fetch_hashrate_history(
    base_url: str, interval: str = _DEFAULT_INTERVAL, timeout: int = 30
) -> list[tuple[int, float]]:
    """
    Ruft /api/v1/mining/hashrate/{interval} ab. Gibt (unix_ts, avg_hashrate_hs)
    sortiert aufsteigend zurück. interval="all" liefert den maximal vom
    lokalen Node bereits indizierten Zeitraum (wächst mit der Zeit, kein
    Backfill seit Genesis wie bei der Preishistorie).
    """
    url = f"{base_url}/api/v1/mining/hashrate/{interval}"
    try:
        with urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
    except URLError as exc:
        log.error("Mempool-Instanz nicht erreichbar: %s", exc)
        return []
    except json.JSONDecodeError as exc:
        log.error("Mempool-Antwort kein gültiges JSON: %s", exc)
        return []

    raw = payload.get("hashrates", [])
    out: list[tuple[int, float]] = []
    for entry in raw:
        ts = entry.get("timestamp")
        hr = entry.get("avgHashrate")
        if ts is None or hr is None or hr <= 0:
            continue
        out.append((int(ts), float(hr)))
    return sorted(out, key=lambda x: x[0])


def load_seed(path: str) -> list[tuple[int, float]]:
    """
    Lädt die einmalig erzeugte blockchain.info-Seed-Datei (siehe
    scripts/backfill_hashrate_blockchain_info.py), falls vorhanden. Gibt
    (unix_ts, hashrate_ehs) zurück. Kein Netzwerkzugriff, reine Datei-I/O.
    Fehlt die Datei, wird eine leere Liste zurückgegeben (kein Fehler).
    """
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    points = payload.get("points", [])
    return [(int(ts), float(v)) for ts, v in points]


def merge_with_seed(
    live: list[tuple[int, float]], seed: list[tuple[int, float]]
) -> list[tuple[int, float]]:
    """
    Kombiniert die live von mempool.space gemessenen Tageswerte (EH/s) mit
    der einmalig geladenen blockchain.info-Vorgeschichte (Seed). Der Seed
    wird nur für Zeitstempel VOR dem frühesten Live-Zeitstempel
    berücksichtigt — die lokal gemessenen Werte haben bei Überschneidung
    immer Vorrang vor der Drittanbieter-Backfill-Quelle.
    """
    if not live:
        return sorted(seed, key=lambda x: x[0])
    cutoff = live[0][0]
    filtered_seed = [p for p in seed if p[0] < cutoff]
    return sorted(filtered_seed + live, key=lambda x: x[0])


def _round_sig(v: float, digits: int = 6) -> float:
    """
    Rundet auf signifikante Stellen statt Nachkommastellen. Die Hashrate-
    Reihe spannt >16 Zehnerpotenzen (2009: ~1e-13 EH/s, heute: ~900 EH/s);
    festes round(v, n) würde die frühen Werte auf 0.0 abschneiden und
    log10(0) im Frontend brechen.
    """
    if v == 0:
        return 0.0
    return float(f"{v:.{digits}g}")


def build_artifact(
    daily: list[tuple[date, float]],
    fit: PowerLawFit,
    own_measurement_since: date | None,
    future_days: int = _DEFAULT_FUTURE_DAYS,
) -> dict[str, object]:
    """
    JSON-Artefakt für das Dashboard (views/ki_hashrate.yaml). Hashrate in
    EH/s. own_measurement_since markiert, ab welchem Tag die Werte von der
    eigenen mempool-Instanz stammen (statt aus dem blockchain.info-Backfill)
    — die Karte zeigt diese Grenze an, damit die Datenherkunft transparent
    bleibt (kein Overstating der eigenen Messreihe).
    """
    last_day = daily[-1][0] if daily else GENESIS_DATE
    chart_max_days = (last_day - GENESIS_DATE).days + future_days
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "genesis_date": GENESIS_DATE.isoformat(),
        "unit": "EH/s",
        "fit": {"a": fit.a, "b": fit.b, "sigma": fit.sigma, "k": fit.k},
        "chart_max_days": chart_max_days,
        "own_measurement_since_days": (
            (own_measurement_since - GENESIS_DATE).days
            if own_measurement_since
            else None
        ),
        "hashrates": [[(d - GENESIS_DATE).days, _round_sig(v)] for d, v in daily],
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
        description="Zieht die Netzwerk-Hashrate-Historie von mempool.space, "
        "kombiniert sie optional mit dem einmaligen blockchain.info-Backfill "
        "(siehe ADR-024) und schreibt sie als JSON für den ₿itsy-Tab."
    )
    parser.add_argument(
        "--out",
        default="src/ha/config/www/btc_hashrate.json",
        help="Zielpfad für das JSON-Artefakt",
    )
    parser.add_argument(
        "--seed",
        default="src/data/btc_hashrate_seed.json",
        help="Pfad zur einmaligen blockchain.info-Seed-Datei (optional, "
        "siehe scripts/backfill_hashrate_blockchain_info.py)",
    )
    parser.add_argument(
        "--interval",
        default=_DEFAULT_INTERVAL,
        help="mempool-Zeitfenster (24h, 3d, 1w, 1m, 3m, 6m, 1y, 2y, 3y, all)",
    )
    parser.add_argument(
        "--k",
        type=float,
        default=_DEFAULT_K,
        help="Bandbreite in Standardabweichungen fürs Fit-Objekt (default: 2.0)",
    )
    parser.add_argument(
        "--future-days",
        type=int,
        default=_DEFAULT_FUTURE_DAYS,
        help="Projektion der Trendlinie in die Zukunft, in Tagen (default: 0, "
        "keine Projektion - siehe Kommentar bei _DEFAULT_FUTURE_DAYS)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    _load_dotenv()
    args = _parse_args()

    base_url = _mempool_base_url()
    log.info("Hole Hashrate-Historie von %s (interval=%s) ...", base_url, args.interval)
    live_hs = fetch_hashrate_history(base_url, interval=args.interval)
    live_eh = [(ts, hr / _EH) for ts, hr in live_hs]

    seed_eh = load_seed(args.seed)
    if seed_eh:
        log.info(
            "%d Seed-Punkte aus %s geladen (blockchain.info-Backfill)",
            len(seed_eh),
            args.seed,
        )

    combined = merge_with_seed(live_eh, seed_eh)
    if not combined:
        log.error("Keine Hashrate-Daten (weder live noch Seed) - Abbruch.")
        raise SystemExit(1)

    daily = downsample_daily(combined)
    log.info(
        "%d Tageswerte, Zeitraum %s bis %s",
        len(daily),
        daily[0][0],
        daily[-1][0],
    )

    fit = fit_power_law(daily, k=args.k)
    log.info(
        "Trend: log10(EH/s) = %.4f + %.4f * log10(days), sigma=%.4f",
        fit.a,
        fit.b,
        fit.sigma,
    )

    own_since = (
        datetime.fromtimestamp(live_eh[0][0], tz=timezone.utc).date()
        if live_eh
        else None
    )

    artifact = build_artifact(daily, fit, own_since, future_days=args.future_days)

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_path) / 1024
    print(f"Geschrieben: {out_path} ({size_kb:.0f} KB, {len(daily)} Tageswerte)")


if __name__ == "__main__":
    main()
