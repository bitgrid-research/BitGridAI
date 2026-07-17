"""
Tests fuer btc_power_law — Downsampling, Power-Law-Fit und Artefakt-Bau,
ohne Netzwerk (fetch_historical_prices wird mit einem Fake-Response gemockt).
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone

import pytest

from src.data.btc_power_law import (
    GENESIS_DATE,
    PowerLawFit,
    _days_since_genesis,
    build_artifact,
    downsample_daily,
    fetch_historical_prices,
    fit_power_law,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._raw = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _ts(d: date, hour: int = 0) -> int:
    return int(datetime(d.year, d.month, d.day, hour, tzinfo=timezone.utc).timestamp())


# ---------------------------------------------------------------------------
# fetch_historical_prices
# ---------------------------------------------------------------------------


def test_fetch_historical_prices_filters_invalid_and_sorts(monkeypatch):
    d1, d2 = date(2020, 1, 2), date(2020, 1, 1)
    payload = {
        "prices": [
            {"time": _ts(d1), "USD": 100.0, "EUR": -1},
            {"time": _ts(d2), "USD": 90.0, "EUR": 80.0},
            {"time": _ts(date(2020, 1, 3)), "USD": -1, "EUR": 95.0},  # invalid USD
            {"time": _ts(date(2020, 1, 4))},  # missing price key
        ]
    }
    monkeypatch.setattr(
        "src.data.btc_power_law.urlopen", lambda *a, **k: _FakeResponse(payload)
    )

    result = fetch_historical_prices("http://mempool.local:3006", currency="USD")

    assert result == [(_ts(d2), 90.0), (_ts(d1), 100.0)]


def test_fetch_historical_prices_network_error_returns_empty(monkeypatch):
    from urllib.error import URLError

    def _raise(*a, **k):
        raise URLError("connection refused")

    monkeypatch.setattr("src.data.btc_power_law.urlopen", _raise)

    assert fetch_historical_prices("http://unreachable:3006") == []


# ---------------------------------------------------------------------------
# downsample_daily
# ---------------------------------------------------------------------------


def test_downsample_daily_keeps_first_value_per_day():
    d = date(2020, 5, 1)
    prices = [
        (_ts(d, hour=0), 10.0),
        (_ts(d, hour=12), 20.0),
        (_ts(date(2020, 5, 2), hour=3), 30.0),
    ]
    assert downsample_daily(prices) == [(d, 10.0), (date(2020, 5, 2), 30.0)]


def test_downsample_daily_empty_input():
    assert downsample_daily([]) == []


# ---------------------------------------------------------------------------
# fit_power_law
# ---------------------------------------------------------------------------


def test_fit_power_law_recovers_exact_line():
    # Konstruiere Daten exakt auf log10(price) = a + b*log10(days), sigma muss ~0 sein.
    true_a, true_b = 1.5, 0.9
    daily = []
    for days in range(100, 5000, 137):
        d = GENESIS_DATE.fromordinal(GENESIS_DATE.toordinal() + days)
        price = 10 ** (true_a + true_b * math.log10(days))
        daily.append((d, price))

    fit = fit_power_law(daily)

    assert fit.a == pytest.approx(true_a, abs=1e-6)
    assert fit.b == pytest.approx(true_b, abs=1e-6)
    assert fit.sigma == pytest.approx(0.0, abs=1e-6)


def test_fit_power_law_too_few_points_raises():
    with pytest.raises(ValueError):
        fit_power_law([(date(2020, 1, 1), 100.0)])


def test_fit_power_law_ignores_non_positive_days_and_prices():
    # Ein Punkt vor/am Genesis-Tag (days <= 0) und ein Nullpreis muessen
    # rausgefiltert werden, sonst wuerde log10 fehlschlagen.
    daily = [
        (GENESIS_DATE, 0.01),  # days == 0, verwerfen
        (date(2020, 1, 1), 0.0),  # Preis == 0, verwerfen
        (date(2020, 1, 2), 100.0),
        (date(2020, 6, 1), 200.0),
    ]
    fit = fit_power_law(daily)
    assert isinstance(fit, PowerLawFit)


# ---------------------------------------------------------------------------
# build_artifact
# ---------------------------------------------------------------------------


def test_build_artifact_structure_and_days_encoding():
    daily = [(date(2020, 1, 2), 100.0), (date(2020, 6, 1), 200.0)]
    fit = PowerLawFit(a=1.0, b=0.8, sigma=0.1, k=2.0)

    artifact = build_artifact(daily, fit, future_days=365)

    assert artifact["genesis_date"] == GENESIS_DATE.isoformat()
    assert artifact["currency"] == "USD"
    assert artifact["fit"] == {"a": 1.0, "b": 0.8, "sigma": 0.1, "k": 2.0}
    assert artifact["prices"] == [
        [_days_since_genesis(date(2020, 1, 2)), 100.0],
        [_days_since_genesis(date(2020, 6, 1)), 200.0],
    ]
    assert artifact["chart_max_days"] == _days_since_genesis(date(2020, 6, 1)) + 365
    # generated_at muss ein gueltiger ISO-Zeitstempel sein
    datetime.fromisoformat(str(artifact["generated_at"]))


def test_build_artifact_empty_prices_uses_genesis_as_last_day():
    fit = PowerLawFit(a=1.0, b=0.8, sigma=0.1, k=2.0)
    artifact = build_artifact([], fit, future_days=100)
    assert artifact["prices"] == []
    assert artifact["chart_max_days"] == 100
