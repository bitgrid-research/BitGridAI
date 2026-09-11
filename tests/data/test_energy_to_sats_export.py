"""
Tests fuer energy_to_sats_export — Serienabfrage und Artefakt-Bau, direkt
gegen eine echte (Test-)DB, kein Netzwerk noetig (reiner DB-Export).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.data.db import get_connection
from src.data.energy_to_sats_export import (
    build_artifact,
    fetch_series,
    target_for_month,
)


@pytest.fixture
def db_conn(tmp_path: Path):
    conn = get_connection(tmp_path / "test.db")
    yield conn
    conn.close()


def _insert_daily_kpi(conn, day: str, energy_to_sats: float | None) -> None:
    conn.execute(
        "INSERT INTO daily_kpi (day, blocks, coverage_pct, quality_warn,"
        " quality_error, mining_kwh, energy_to_sats, computed_at) VALUES"
        " (?, 144, 100.0, 0, 0, 1.0, ?, '2026-08-21T00:00:00')",
        (day, energy_to_sats),
    )
    conn.commit()


def test_fetch_series_returns_rolling_average(db_conn):
    _insert_daily_kpi(db_conn, "2026-08-18", 30.0)
    _insert_daily_kpi(db_conn, "2026-08-19", 50.0)
    _insert_daily_kpi(db_conn, "2026-08-20", 60.0)

    series = fetch_series(db_conn, 30)

    assert [p["day"] for p in series] == ["2026-08-18", "2026-08-19", "2026-08-20"]
    assert series[0]["avg_7d"] == 30.0
    assert series[1]["avg_7d"] == 40.0
    assert series[2]["avg_7d"] == pytest.approx(46.67, abs=0.01)


def test_fetch_series_excludes_days_without_settlement(db_conn):
    _insert_daily_kpi(db_conn, "2026-08-18", 30.0)
    _insert_daily_kpi(db_conn, "2026-08-19", None)  # keine Abrechnung
    _insert_daily_kpi(db_conn, "2026-08-20", 60.0)

    series = fetch_series(db_conn, 30)

    assert [p["day"] for p in series] == ["2026-08-18", "2026-08-20"]


def test_fetch_series_respects_days_window(db_conn):
    old_day = (datetime.now(timezone.utc).date() - timedelta(days=90)).isoformat()
    _insert_daily_kpi(db_conn, old_day, 30.0)

    series = fetch_series(db_conn, 30)
    assert series == []


def test_fetch_series_empty_db_returns_empty_list(db_conn):
    assert fetch_series(db_conn, 30) == []


def test_build_artifact_uses_latest_available_avg_7d():
    series = [
        {"day": "2026-08-18", "energy_to_sats": 30.0, "avg_7d": 30.0},
        {"day": "2026-08-19", "energy_to_sats": 50.0, "avg_7d": 40.0},
    ]
    now = datetime(2026, 8, 21, tzinfo=timezone.utc)

    artifact = build_artifact(series, now=now)

    assert artifact["target_sats_per_kwh"] == target_for_month(8)  # now = August
    assert artifact["latest_avg_7d"] == 40.0
    assert artifact["days"] == series
    assert artifact["generated_at"] == now.isoformat()


def test_build_artifact_empty_series_has_no_latest_avg():
    artifact = build_artifact([])
    assert artifact["latest_avg_7d"] is None
    assert artifact["days"] == []


def test_build_artifact_skips_trailing_none_avg():
    # Letzter Tag hat noch keinen 7-Tage-Schnitt (z.B. gerade erst gesynct
    # ohne genug Vorlauf) -> das Artefakt zeigt den letzten VORHANDENEN Wert,
    # keine erfundene Null.
    series = [
        {"day": "2026-08-18", "energy_to_sats": 30.0, "avg_7d": 30.0},
        {"day": "2026-08-19", "energy_to_sats": 50.0, "avg_7d": None},
    ]
    artifact = build_artifact(series)
    assert artifact["latest_avg_7d"] == 30.0


@pytest.mark.parametrize(
    "month,expected",
    [
        (1, 135.0),
        (2, 135.0),
        (3, 130.0),
        (4, 130.0),
        (5, 125.0),
        (6, 125.0),
        (7, 125.0),
        (8, 125.0),
        (9, 130.0),
        (10, 135.0),
        (11, 135.0),
        (12, 135.0),
    ],
)
def test_target_for_month_matches_saison_tiers(month, expected):
    # Tier-Grenzen aus ADR 029 (091_adr_de.md): Voll = Mai-Aug, Eco+Standard =
    # Maer/Apr/Sep, Nur Eco = Okt-Feb (sensor.mvp_saison_status, ADR 028).
    assert target_for_month(month) == expected
