"""
BtcPowerLaw — zieht Bitcoin-Preishistorie von der self-hosted mempool.space-
Instanz und berechnet einen Power-Law-Fit (Regression im Log-Log-Raum) für
den ₿itsy-Tab (KI-Tab, Markteinordnung, views/ki_powerlaw.yaml).

Kein Steuerpfad: dieses Modul liefert Markt-Kontext für die Erklärschicht
(read-only), es beeinflusst keine Mining-Entscheidung in core/. Genau wie
core/ arbeitet es aber deterministisch: gleiche Rohdaten -> gleiches Ergebnis
(gewoehnliche kleinste Quadrate, kein ML).

Modell (Heuristik, keine Preisprognose):
    log10(price_usd) = a + b * log10(days_since_genesis)
Support/Widerstand = Fit +/- k * Sigma (Standardabweichung der Residuen).
USD statt EUR: mempool liefert EUR erst ab einem spaeteren Datum (fruehe
Eintraege haben EUR=-1), USD ist ueber die volle Historie durchgehend
vorhanden. Das entspricht auch der Achsenbeschriftung gaengiger Power-Law-
Charts (z.B. BitBO).

CLI:
    python -m src.data.btc_power_law
    python -m src.data.btc_power_law --out src/ha/config/www/btc_power_law.json

Env-Vars (aus .env):
    MEMPOOL_HOST — IP der self-hosted mempool.space-Instanz
    MEMPOOL_PORT — Port (default: 3006)
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import urlopen

log = logging.getLogger(__name__)

GENESIS_DATE = date(2009, 1, 3)
_DEFAULT_PORT = "3006"
_DEFAULT_K = 2.0
_DEFAULT_FUTURE_DAYS = 365 * 15


@dataclass(frozen=True)
class PowerLawFit:
    a: float
    b: float
    sigma: float
    k: float


def fetch_historical_prices(
    base_url: str, currency: str = "USD", timeout: int = 30
) -> list[tuple[int, float]]:
    """
    Ruft /api/v1/historical-price ab. Gibt (unix_ts, price) sortiert
    aufsteigend zurueck, Eintraege ohne gueltigen Preis (-1) werden verworfen.
    """
    url = f"{base_url}/api/v1/historical-price?currency={currency}"
    try:
        with urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
    except URLError as exc:
        log.error("Mempool-Instanz nicht erreichbar: %s", exc)
        return []
    except json.JSONDecodeError as exc:
        log.error("Mempool-Antwort kein gueltiges JSON: %s", exc)
        return []

    raw = payload.get("prices", [])
    out: list[tuple[int, float]] = []
    for entry in raw:
        ts = entry.get("time")
        price = entry.get(currency)
        if ts is None or price is None or price <= 0:
            continue
        out.append((int(ts), float(price)))
    return sorted(out, key=lambda x: x[0])


def downsample_daily(prices: list[tuple[int, float]]) -> list[tuple[date, float]]:
    """Ein Preis pro Kalendertag (UTC), erster Eintrag des Tages gewinnt."""
    by_day: dict[date, float] = {}
    for ts, price in prices:
        d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        if d not in by_day:
            by_day[d] = price
    return sorted(by_day.items())


def _days_since_genesis(d: date) -> int:
    return (d - GENESIS_DATE).days


def fit_power_law(
    daily_prices: list[tuple[date, float]], k: float = _DEFAULT_K
) -> PowerLawFit:
    """
    Gewoehnliche kleinste Quadrate im Log-Log-Raum:
        y = log10(price), x = log10(days_since_genesis)
    Sigma = Standardabweichung der Residuen (fuer Support-/Widerstandsband).
    """
    xs: list[float] = []
    ys: list[float] = []
    for d, price in daily_prices:
        days = _days_since_genesis(d)
        if days <= 0 or price <= 0:
            continue
        xs.append(math.log10(days))
        ys.append(math.log10(price))

    if len(xs) < 2:
        raise ValueError("Zu wenige Datenpunkte fuer Power-Law-Fit")

    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    b = cov / var_x
    a = mean_y - b * mean_x

    residuals = [y - (a + b * x) for x, y in zip(xs, ys)]
    sigma = math.sqrt(sum(r * r for r in residuals) / n)

    return PowerLawFit(a=a, b=b, sigma=sigma, k=k)


def build_artifact(
    daily_prices: list[tuple[date, float]],
    fit: PowerLawFit,
    future_days: int = _DEFAULT_FUTURE_DAYS,
) -> dict[str, object]:
    """
    JSON-Artefakt fuer das Dashboard (views/ki_powerlaw.yaml). Enthaelt die
    komprimierte Tages-Preisreihe (als [days_since_genesis, price]-Paare,
    spart die Datums-Strings) und die Fit-Parameter; das Frontend berechnet
    Regressions-/Support-/Widerstandslinien daraus, inkl. Projektion in die
    Zukunft (chart_max_days), ohne selbst Regression rechnen zu muessen.
    """
    last_day = daily_prices[-1][0] if daily_prices else GENESIS_DATE
    chart_max_days = _days_since_genesis(last_day) + future_days
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "genesis_date": GENESIS_DATE.isoformat(),
        "currency": "USD",
        "fit": {"a": fit.a, "b": fit.b, "sigma": fit.sigma, "k": fit.k},
        "chart_max_days": chart_max_days,
        "prices": [
            [_days_since_genesis(d), round(price, 2)] for d, price in daily_prices
        ],
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
        description="Zieht BTC-Preishistorie von mempool.space und schreibt "
        "den Power-Law-Fit als JSON fuer den ₿itsy-Tab."
    )
    parser.add_argument(
        "--out",
        default="src/ha/config/www/btc_power_law.json",
        help="Zielpfad fuer das JSON-Artefakt",
    )
    parser.add_argument(
        "--k",
        type=float,
        default=_DEFAULT_K,
        help="Bandbreite Support/Widerstand in Standardabweichungen (default: 2.0)",
    )
    parser.add_argument(
        "--future-days",
        type=int,
        default=_DEFAULT_FUTURE_DAYS,
        help="Projektion der Fit-Linien in die Zukunft, in Tagen (default: 15 Jahre)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    _load_dotenv()
    args = _parse_args()

    base_url = _mempool_base_url()
    log.info("Hole Preishistorie von %s ...", base_url)
    prices = fetch_historical_prices(base_url)
    if not prices:
        log.error("Keine Preisdaten erhalten - Abbruch.")
        raise SystemExit(1)

    daily = downsample_daily(prices)
    log.info("%d Rohpunkte -> %d Tageswerte", len(prices), len(daily))

    fit = fit_power_law(daily, k=args.k)
    log.info(
        "Fit: log10(price) = %.4f + %.4f * log10(days), sigma=%.4f",
        fit.a,
        fit.b,
        fit.sigma,
    )

    artifact = build_artifact(daily, fit, future_days=args.future_days)

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_path) / 1024
    print(f"Geschrieben: {out_path} ({size_kb:.0f} KB, {len(daily)} Tageswerte)")


if __name__ == "__main__":
    main()
