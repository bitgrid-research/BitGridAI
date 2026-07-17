"""Unit-Tests für die neuen Verlaufs-/Cooldown-Helfer in bitsy_status.py.

Reine Parsing-Logik (keine HTTP-/MQTT-Mocks noetig) — genau der Teil, der bei
kaputten Zeitstempeln oder leeren HA-States am ehesten stillschweigend falsche
Tipps produzieren wuerde, statt sauber None zurueckzugeben.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.explain.bitsy_status import (
    _lockout_minutes_remaining,
    _soc_trend,
    classify_state,
)

# ── _soc_trend ───────────────────────────────────────────────────────────────


def test_soc_trend_happy_path() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    states = {"input_text.batt_soc_trace": f"{today}|[[8.5, 45.0], [12.0, 82.0]]"}
    assert _soc_trend(states) == "08:30 Uhr 45.0% -> jetzt 82.0%"


def test_soc_trend_none_when_empty() -> None:
    assert _soc_trend({}) is None
    assert _soc_trend({"input_text.batt_soc_trace": ""}) is None


def test_soc_trend_none_when_stale_date() -> None:
    states = {"input_text.batt_soc_trace": "2020-01-01|[[8.0, 40.0], [9.0, 50.0]]"}
    assert _soc_trend(states) is None


def test_soc_trend_none_when_only_one_point() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    states = {"input_text.batt_soc_trace": f"{today}|[[8.5, 45.0]]"}
    assert _soc_trend(states) is None


def test_soc_trend_none_on_malformed_json() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    states = {"input_text.batt_soc_trace": f"{today}|not-json"}
    assert _soc_trend(states) is None


# ── _lockout_minutes_remaining ───────────────────────────────────────────────


def test_lockout_minutes_remaining_future_timestamp() -> None:
    until = datetime.now() + timedelta(minutes=42)
    states = {"input_datetime.lockout": until.strftime("%Y-%m-%d %H:%M:%S")}
    minutes = _lockout_minutes_remaining(states, "input_datetime.lockout")
    assert minutes is not None
    assert 40 <= minutes <= 42


def test_lockout_minutes_remaining_none_for_epoch_default() -> None:
    states = {"input_datetime.lockout": "1970-01-01 00:00:00"}
    assert _lockout_minutes_remaining(states, "input_datetime.lockout") is None


def test_lockout_minutes_remaining_none_for_missing_or_unavailable() -> None:
    assert _lockout_minutes_remaining({}, "input_datetime.lockout") is None
    states = {"input_datetime.lockout": "unavailable"}
    assert _lockout_minutes_remaining(states, "input_datetime.lockout") is None


# ── classify_state: neue Felder landen in numbers ──────────────────────────


def test_classify_state_cooldown_text_none_for_dash() -> None:
    states = {
        "sensor.miner1_workmode_status": "Standard",
        "sensor.miner_1_cooldown_status": "—",
    }
    cls = classify_state(states)
    assert cls.numbers["cooldown_text"] is None


def test_classify_state_cooldown_text_passed_through() -> None:
    states = {
        "sensor.miner1_workmode_status": "Standard",
        "sensor.miner_1_cooldown_status": "↓ 12 min",
    }
    cls = classify_state(states)
    assert cls.numbers["cooldown_text"] == "↓ 12 min"
