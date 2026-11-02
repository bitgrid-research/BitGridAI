"""
Tests für btc_hashrate — Fetch-Parsing, Seed-Merge und Artefakt-Bau, ohne
Netzwerk (fetch_hashrate_history wird mit einem Fake-Response gemockt, der
Seed wird über eine Temp-Datei geladen).
"""

from __future__ import annotations

import json
from datetime import date, datetime

from src.data.btc_power_law import GENESIS_DATE, PowerLawFit
from src.data.btc_hashrate import (
    build_artifact,
    fetch_hashrate_history,
    load_seed,
    merge_with_seed,
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


# ---------------------------------------------------------------------------
# fetch_hashrate_history
# ---------------------------------------------------------------------------


def test_fetch_hashrate_history_filters_invalid_and_sorts(monkeypatch):
    payload = {
        "hashrates": [
            {"timestamp": 200, "avgHashrate": 5e20},
            {"timestamp": 100, "avgHashrate": 4e20},
            {"timestamp": 300, "avgHashrate": -1},  # invalid, verwerfen
            {"timestamp": 400},  # fehlender Wert, verwerfen
        ],
        "difficulty": [],
        "currentHashrate": 5e20,
        "currentDifficulty": 1,
    }
    monkeypatch.setattr(
        "src.data.btc_hashrate.urlopen", lambda *a, **k: _FakeResponse(payload)
    )

    result = fetch_hashrate_history("http://mempool.local:3006")

    assert result == [(100, 4e20), (200, 5e20)]


def test_fetch_hashrate_history_network_error_returns_empty(monkeypatch):
    from urllib.error import URLError

    def _raise(*a, **k):
        raise URLError("connection refused")

    monkeypatch.setattr("src.data.btc_hashrate.urlopen", _raise)

    assert fetch_hashrate_history("http://unreachable:3006") == []


def test_fetch_hashrate_history_bad_json_returns_empty(monkeypatch):
    class _BadJson:
        def read(self) -> bytes:
            return b"not json"

        def __enter__(self) -> "_BadJson":
            return self

        def __exit__(self, *exc: object) -> None:
            return None

    monkeypatch.setattr("src.data.btc_hashrate.urlopen", lambda *a, **k: _BadJson())

    assert fetch_hashrate_history("http://mempool.local:3006") == []


# ---------------------------------------------------------------------------
# load_seed
# ---------------------------------------------------------------------------


def test_load_seed_missing_file_returns_empty(tmp_path):
    assert load_seed(str(tmp_path / "nope.json")) == []


def test_load_seed_reads_points(tmp_path):
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps({"points": [[100, 0.5], [200, 0.6]]}), encoding="utf-8"
    )
    assert load_seed(str(seed_path)) == [(100, 0.5), (200, 0.6)]


# ---------------------------------------------------------------------------
# merge_with_seed
# ---------------------------------------------------------------------------


def test_merge_with_seed_live_wins_on_overlap():
    live = [(300, 10.0), (400, 11.0)]
    seed = [(100, 1.0), (200, 2.0), (300, 999.0), (350, 999.0)]

    result = merge_with_seed(live, seed)

    # Seed-Punkte ab dem ersten Live-Zeitstempel (300) werden verworfen,
    # auch wenn sie zwischen zwei Live-Punkten liegen (350).
    assert result == [(100, 1.0), (200, 2.0), (300, 10.0), (400, 11.0)]


def test_merge_with_seed_empty_live_keeps_all_seed_sorted():
    seed = [(200, 2.0), (100, 1.0)]
    assert merge_with_seed([], seed) == [(100, 1.0), (200, 2.0)]


def test_merge_with_seed_empty_seed_returns_live():
    live = [(100, 1.0)]
    assert merge_with_seed(live, []) == live


# ---------------------------------------------------------------------------
# build_artifact
# ---------------------------------------------------------------------------


def test_build_artifact_structure_and_days_encoding():
    daily = [(date(2020, 1, 2), 100.0), (date(2020, 6, 1), 200.0)]
    fit = PowerLawFit(a=1.0, b=0.8, sigma=0.1, k=2.0)
    own_since = date(2020, 6, 1)

    artifact = build_artifact(daily, fit, own_since, future_days=365)

    assert artifact["genesis_date"] == GENESIS_DATE.isoformat()
    assert artifact["unit"] == "EH/s"
    assert artifact["fit"] == {"a": 1.0, "b": 0.8, "sigma": 0.1, "k": 2.0}
    assert artifact["hashrates"] == [
        [(date(2020, 1, 2) - GENESIS_DATE).days, 100.0],
        [(date(2020, 6, 1) - GENESIS_DATE).days, 200.0],
    ]
    assert artifact["own_measurement_since_days"] == (own_since - GENESIS_DATE).days
    assert artifact["chart_max_days"] == (date(2020, 6, 1) - GENESIS_DATE).days + 365
    datetime.fromisoformat(str(artifact["generated_at"]))


def test_build_artifact_own_measurement_none_when_no_live_data():
    daily = [(date(2020, 1, 2), 100.0)]
    fit = PowerLawFit(a=1.0, b=0.8, sigma=0.1, k=2.0)

    artifact = build_artifact(daily, fit, None, future_days=100)

    assert artifact["own_measurement_since_days"] is None


def test_build_artifact_empty_daily_uses_genesis_as_last_day():
    fit = PowerLawFit(a=1.0, b=0.8, sigma=0.1, k=2.0)
    artifact = build_artifact([], fit, None, future_days=100)
    assert artifact["hashrates"] == []
    assert artifact["chart_max_days"] == 100
