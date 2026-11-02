"""
Tests fuer btc_difficulty — Fetch-Parsing (Difficulty-Adjustment, Tip-Height),
Halbierungsberechnung und Artefakt-Bau, ohne Netzwerk (urlopen wird mit einem
Fake-Response gemockt).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from src.data.btc_difficulty import (
    DESIGN_BLOCK_TIME_SECONDS,
    HALVING_INTERVAL_BLOCKS,
    build_artifact,
    compute_next_halving,
    fetch_difficulty_adjustment,
    fetch_tip_height,
)


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._raw = body

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _json_response(payload: dict[str, object]) -> _FakeResponse:
    return _FakeResponse(json.dumps(payload).encode())


# ---------------------------------------------------------------------------
# fetch_difficulty_adjustment
# ---------------------------------------------------------------------------


def test_fetch_difficulty_adjustment_parses_required_fields(monkeypatch):
    payload = {
        "progressPercent": 4.81,
        "difficultyChange": -4.87,
        "estimatedRetargetDate": 1785069074486,
        "remainingBlocks": 1919,
        "remainingTime": 1212796486,
        "previousRetarget": -5.00,
        "previousTime": 1783800551,
        "nextRetargetHeight": 959616,
        "timeAvg": 574505,
        "adjustedTimeAvg": 631994,
        "timeOffset": 0,
    }
    monkeypatch.setattr(
        "src.data.btc_difficulty.urlopen", lambda *a, **k: _json_response(payload)
    )

    result = fetch_difficulty_adjustment("http://mempool.local:3006")

    assert result == {
        "difficultyChange": -4.87,
        "remainingBlocks": 1919.0,
        "remainingTime": 1212796486.0,
        "previousRetarget": -5.00,
        "nextRetargetHeight": 959616.0,
    }


def test_fetch_difficulty_adjustment_missing_field_returns_none(monkeypatch):
    payload = {
        "difficultyChange": -4.87,
        "remainingBlocks": 1919,
        # remainingTime fehlt
        "previousRetarget": -5.00,
        "nextRetargetHeight": 959616,
    }
    monkeypatch.setattr(
        "src.data.btc_difficulty.urlopen", lambda *a, **k: _json_response(payload)
    )

    assert fetch_difficulty_adjustment("http://mempool.local:3006") is None


def test_fetch_difficulty_adjustment_network_error_returns_none(monkeypatch):
    from urllib.error import URLError

    def _raise(*a, **k):
        raise URLError("connection refused")

    monkeypatch.setattr("src.data.btc_difficulty.urlopen", _raise)

    assert fetch_difficulty_adjustment("http://unreachable:3006") is None


def test_fetch_difficulty_adjustment_bad_json_returns_none(monkeypatch):
    monkeypatch.setattr(
        "src.data.btc_difficulty.urlopen", lambda *a, **k: _FakeResponse(b"not json")
    )

    assert fetch_difficulty_adjustment("http://mempool.local:3006") is None


# ---------------------------------------------------------------------------
# fetch_tip_height
# ---------------------------------------------------------------------------


def test_fetch_tip_height_parses_plain_integer(monkeypatch):
    monkeypatch.setattr(
        "src.data.btc_difficulty.urlopen", lambda *a, **k: _FakeResponse(b"957697")
    )

    assert fetch_tip_height("http://mempool.local:3006") == 957697


def test_fetch_tip_height_network_error_returns_none(monkeypatch):
    from urllib.error import URLError

    def _raise(*a, **k):
        raise URLError("connection refused")

    monkeypatch.setattr("src.data.btc_difficulty.urlopen", _raise)

    assert fetch_tip_height("http://unreachable:3006") is None


def test_fetch_tip_height_non_numeric_returns_none(monkeypatch):
    monkeypatch.setattr(
        "src.data.btc_difficulty.urlopen",
        lambda *a, **k: _FakeResponse(b"not-a-number"),
    )

    assert fetch_tip_height("http://mempool.local:3006") is None


# ---------------------------------------------------------------------------
# compute_next_halving
# ---------------------------------------------------------------------------


def test_compute_next_halving_mid_epoch():
    next_height, remaining = compute_next_halving(957697)
    assert next_height == 1_050_000
    assert remaining == 92_303


def test_compute_next_halving_exact_halving_height_rolls_to_next():
    next_height, remaining = compute_next_halving(840_000)
    assert next_height == 1_050_000
    assert remaining == HALVING_INTERVAL_BLOCKS


def test_compute_next_halving_height_zero():
    next_height, remaining = compute_next_halving(0)
    assert next_height == HALVING_INTERVAL_BLOCKS
    assert remaining == HALVING_INTERVAL_BLOCKS


# ---------------------------------------------------------------------------
# build_artifact
# ---------------------------------------------------------------------------


def test_build_artifact_structure_and_values():
    diff = {
        "difficultyChange": -4.87,
        "remainingBlocks": 1919.0,
        "remainingTime": 1212796486.0,
        "previousRetarget": -5.00,
        "nextRetargetHeight": 959616.0,
    }
    now = datetime(2026, 7, 12, tzinfo=timezone.utc)

    artifact = build_artifact(diff, 957697, now=now)

    assert artifact["block_height"] == 957697
    assert artifact["remaining_blocks"] == 1919
    assert artifact["remaining_days"] == 1212796486.0 / 1000 / 86400
    assert artifact["difficulty_change_pct"] == -4.87
    assert artifact["previous_retarget_pct"] == -5.00
    assert artifact["next_retarget_height"] == 959616
    assert artifact["next_halving_height"] == 1_050_000
    assert artifact["next_halving_remaining_blocks"] == 92_303
    assert artifact["halving_block_time_seconds"] == DESIGN_BLOCK_TIME_SECONDS

    expected_days = 92_303 * DESIGN_BLOCK_TIME_SECONDS / 86400
    assert artifact["next_halving_remaining_days"] == expected_days
    assert datetime.fromisoformat(str(artifact["next_halving_date"])) > now
    assert datetime.fromisoformat(str(artifact["generated_at"])) == now
