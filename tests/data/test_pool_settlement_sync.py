"""
Tests fuer pool_settlement_sync — Tag-Ableitung, Transaktions-/Log-Parsing und
Sync-Idempotenz, ohne Netzwerk (urlopen wird mit einem Fake-Response gemockt).
"""

from __future__ import annotations

import json
from datetime import date, timezone
from pathlib import Path

import pytest

from src.data.db import get_connection
from src.data.pool_settlement_sync import (
    _settlement_day,
    parse_daily_log,
    parse_settlement_transactions,
    sync,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_conn(tmp_path: Path):
    conn = get_connection(tmp_path / "test.db")
    yield conn
    conn.close()


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._raw = body

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _json_response(payload: object) -> _FakeResponse:
    return _FakeResponse(json.dumps(payload).encode())


def _state_payload(state: str, attributes: dict[str, object] | None = None) -> dict:
    return {"state": state, "attributes": attributes or {}}


# ---------------------------------------------------------------------------
# _settlement_day
# ---------------------------------------------------------------------------


def test_settlement_day_subtracts_one_utc_day():
    # 2026-08-21T02:00:00Z Abrechnung -> Mining-Tag 2026-08-20
    ts = date(2026, 8, 21).toordinal()
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    assert _settlement_day(settled.timestamp()) == "2026-08-20"


def test_settlement_day_midnight_boundary():
    import datetime as dt

    settled = dt.datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    assert _settlement_day(settled.timestamp()) == "2025-12-31"


# ---------------------------------------------------------------------------
# parse_settlement_transactions
# ---------------------------------------------------------------------------


def test_parse_settlement_transactions_happy_path():
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    transactions = [
        {
            "amount": "0.00012345",
            "mining_extra": {
                "hash_rate": 55_000_000_000_000,  # 55 TH/s in H/s
                "mining_date": settled.timestamp(),
            },
        }
    ]
    result = parse_settlement_transactions(transactions)
    assert result == {"2026-08-20": (0.00012345, 55.0)}


def test_parse_settlement_transactions_falls_back_to_changed_balance():
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    transactions = [
        {
            "changed_balance": "0.0001",
            "mining_extra": {
                "hash_rate": 1e12,
                "mining_date": settled.timestamp(),
            },
        }
    ]
    result = parse_settlement_transactions(transactions)
    assert result["2026-08-20"][0] == 0.0001


def test_parse_settlement_transactions_skips_zero_and_negative():
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    transactions = [
        {
            "amount": "0",
            "mining_extra": {"hash_rate": 1e12, "mining_date": settled.timestamp()},
        },
        {
            "amount": "-0.0001",
            "mining_extra": {"hash_rate": 1e12, "mining_date": settled.timestamp()},
        },
    ]
    assert parse_settlement_transactions(transactions) == {}


def test_parse_settlement_transactions_skips_missing_fields():
    transactions = [
        {"amount": "0.0001", "mining_extra": {"hash_rate": None, "mining_date": 123}},
        {"amount": "0.0001", "mining_extra": {}},
        {"amount": "0.0001"},  # kein mining_extra
        {},
        "not-a-dict",
    ]
    assert parse_settlement_transactions(transactions) == {}


def test_parse_settlement_transactions_ignores_malformed_amount():
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    transactions = [
        {
            "amount": "not-a-number",
            "mining_extra": {"hash_rate": 1e12, "mining_date": settled.timestamp()},
        }
    ]
    assert parse_settlement_transactions(transactions) == {}


# ---------------------------------------------------------------------------
# parse_daily_log
# ---------------------------------------------------------------------------


def test_parse_daily_log_multiple_entries():
    raw = "2026-08-20,0.0001|2026-08-19,0.00012|2026-08-18,0.00009"
    result = parse_daily_log(raw)
    assert result == {
        "2026-08-20": 0.0001,
        "2026-08-19": 0.00012,
        "2026-08-18": 0.00009,
    }


def test_parse_daily_log_empty_and_unknown():
    assert parse_daily_log("") == {}
    assert parse_daily_log("unknown") == {}
    assert parse_daily_log("unavailable") == {}


def test_parse_daily_log_skips_malformed_entries():
    raw = "2026-08-20,0.0001|malformed|2026-08-18,not-a-number|,0.0002"
    assert parse_daily_log(raw) == {"2026-08-20": 0.0001}


# ---------------------------------------------------------------------------
# sync — Netzwerk gemockt, echte DB (tmp_path)
# ---------------------------------------------------------------------------


def _mock_urlopen(monkeypatch, responses: dict[str, dict[str, object]]) -> None:
    """
    responses: {entity_id: state_payload}. Ein GET auf /api/states/<id>
    liefert responses[id], alles andere 404 (URLError).
    """

    def _fake_urlopen(req, timeout=30):
        from urllib.error import URLError

        url = req.full_url if hasattr(req, "full_url") else req
        for entity_id, payload in responses.items():
            if url.endswith(f"/api/states/{entity_id}"):
                return _json_response(payload)
        raise URLError(f"not mocked: {url}")

    monkeypatch.setattr("src.data.pool_settlement_sync.urlopen", _fake_urlopen)


def test_sync_writes_rows_from_settlement_history(db_conn, monkeypatch):
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    _mock_urlopen(
        monkeypatch,
        {
            "sensor.pool_settlement_history": _state_payload(
                "1",
                {
                    "transactions": [
                        {
                            "amount": "0.0001",
                            "mining_extra": {
                                "hash_rate": 55e12,
                                "mining_date": settled.timestamp(),
                            },
                        }
                    ]
                },
            ),
            "input_text.pool_btc_daily_log": _state_payload(""),
            "input_text.pool_ths_daily_log": _state_payload(""),
            "sensor.btc_eur_price": _state_payload("60000"),
        },
    )

    added, skipped = sync(db_conn, "http://ha.local:8123", "tok", date(2026, 8, 1))
    assert (added, skipped) == (1, 0)

    row = db_conn.execute(
        "SELECT earned_btc, pool_ths_avg, btc_eur_price_approx, source"
        " FROM bitcoin_daily_settlement WHERE day = '2026-08-20'"
    ).fetchone()
    assert row == (0.0001, 55.0, 60000.0, "ha:pool_settlement_history")


def test_sync_is_idempotent(db_conn, monkeypatch):
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    _mock_urlopen(
        monkeypatch,
        {
            "sensor.pool_settlement_history": _state_payload(
                "1",
                {
                    "transactions": [
                        {
                            "amount": "0.0001",
                            "mining_extra": {
                                "hash_rate": 55e12,
                                "mining_date": settled.timestamp(),
                            },
                        }
                    ]
                },
            ),
            "input_text.pool_btc_daily_log": _state_payload(""),
            "input_text.pool_ths_daily_log": _state_payload(""),
            "sensor.btc_eur_price": _state_payload("60000"),
        },
    )

    added1, _ = sync(db_conn, "http://ha.local:8123", "tok", date(2026, 8, 1))
    added2, skipped2 = sync(db_conn, "http://ha.local:8123", "tok", date(2026, 8, 1))
    assert added1 == 1
    assert added2 == 0
    assert skipped2 == 1

    count = db_conn.execute("SELECT COUNT(*) FROM bitcoin_daily_settlement").fetchone()[
        0
    ]
    assert count == 1


def test_sync_uses_fallback_log_for_gaps_not_in_settlement_history(
    db_conn, monkeypatch
):
    _mock_urlopen(
        monkeypatch,
        {
            "sensor.pool_settlement_history": _state_payload("1", {"transactions": []}),
            "input_text.pool_btc_daily_log": _state_payload("2026-08-19,0.00008"),
            "input_text.pool_ths_daily_log": _state_payload("2026-08-19,50.0"),
            "sensor.btc_eur_price": _state_payload("60000"),
        },
    )

    added, _ = sync(db_conn, "http://ha.local:8123", "tok", date(2026, 8, 1))
    assert added == 1

    row = db_conn.execute(
        "SELECT earned_btc, pool_ths_avg, source FROM bitcoin_daily_settlement"
        " WHERE day = '2026-08-19'"
    ).fetchone()
    assert row == (0.00008, 50.0, "ha:pool_btc_daily_log")


def test_sync_primary_source_wins_over_fallback_for_same_day(db_conn, monkeypatch):
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    _mock_urlopen(
        monkeypatch,
        {
            "sensor.pool_settlement_history": _state_payload(
                "1",
                {
                    "transactions": [
                        {
                            "amount": "0.0001",
                            "mining_extra": {
                                "hash_rate": 55e12,
                                "mining_date": settled.timestamp(),
                            },
                        }
                    ]
                },
            ),
            # gleicher Tag, abweichender Fallback-Wert -> darf NICHT gewinnen
            "input_text.pool_btc_daily_log": _state_payload("2026-08-20,0.00099"),
            "input_text.pool_ths_daily_log": _state_payload(""),
            "sensor.btc_eur_price": _state_payload("60000"),
        },
    )

    sync(db_conn, "http://ha.local:8123", "tok", date(2026, 8, 1))

    row = db_conn.execute(
        "SELECT earned_btc, source FROM bitcoin_daily_settlement WHERE day = '2026-08-20'"
    ).fetchone()
    assert row == (0.0001, "ha:pool_settlement_history")


def test_sync_respects_since_cutoff(db_conn, monkeypatch):
    import datetime as dt

    settled = dt.datetime(2026, 8, 21, 2, 0, 0, tzinfo=timezone.utc)
    _mock_urlopen(
        monkeypatch,
        {
            "sensor.pool_settlement_history": _state_payload(
                "1",
                {
                    "transactions": [
                        {
                            "amount": "0.0001",
                            "mining_extra": {
                                "hash_rate": 55e12,
                                "mining_date": settled.timestamp(),  # -> Tag 2026-08-20
                            },
                        }
                    ]
                },
            ),
            "input_text.pool_btc_daily_log": _state_payload(""),
            "input_text.pool_ths_daily_log": _state_payload(""),
            "sensor.btc_eur_price": _state_payload("60000"),
        },
    )

    added, _ = sync(db_conn, "http://ha.local:8123", "tok", date(2026, 8, 21))
    assert added == 0
    count = db_conn.execute("SELECT COUNT(*) FROM bitcoin_daily_settlement").fetchone()[
        0
    ]
    assert count == 0


def test_sync_no_data_returns_zero(db_conn, monkeypatch):
    _mock_urlopen(
        monkeypatch,
        {
            "sensor.pool_settlement_history": _state_payload("0", {"transactions": []}),
            "input_text.pool_btc_daily_log": _state_payload(""),
            "input_text.pool_ths_daily_log": _state_payload(""),
            "sensor.btc_eur_price": _state_payload("60000"),
        },
    )

    added, skipped = sync(db_conn, "http://ha.local:8123", "tok", date(2026, 8, 1))
    assert (added, skipped) == (0, 0)
