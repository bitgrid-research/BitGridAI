"""
Tests fuer btc_price_history — DB-Upsert und Fenster-Export, direkt gegen
eine echte (Test-)DB, kein Netzwerk noetig (fetch_historical_prices selbst
ist in btc_power_law.py getestet).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from src.data.btc_price_history import export_artifact, sync_to_db
from src.data.db import get_connection


@pytest.fixture
def db_conn(tmp_path: Path):
    conn = get_connection(tmp_path / "test.db")
    yield conn
    conn.close()


def test_sync_to_db_writes_all_days(db_conn):
    daily = [
        (date(2026, 8, 30), 67000.0),
        (date(2026, 8, 31), 67500.0),
    ]

    written = sync_to_db(db_conn, daily)

    assert written == 2
    rows = db_conn.execute(
        "SELECT day, price_eur FROM btc_price_daily ORDER BY day"
    ).fetchall()
    assert rows == [("2026-08-30", 67000.0), ("2026-08-31", 67500.0)]


def test_sync_to_db_is_idempotent_upsert(db_conn):
    sync_to_db(db_conn, [(date(2026, 8, 30), 67000.0)])
    sync_to_db(db_conn, [(date(2026, 8, 30), 67999.99)])  # erneuter Abruf, neuer Wert

    rows = db_conn.execute("SELECT price_eur FROM btc_price_daily").fetchall()
    assert rows == [(67999.99,)]  # ueberschrieben, kein Duplikat


def test_export_artifact_applies_window_freshly_against_now(db_conn):
    sync_to_db(
        db_conn,
        [
            (date(2013, 10, 3), 100.0),  # weit ausserhalb jedes realistischen Fensters
            (date(2026, 8, 1), 60000.0),
            (date(2026, 8, 31), 67500.0),
        ],
    )
    now = datetime(2026, 8, 31, tzinfo=timezone.utc)

    artifact = export_artifact(db_conn, days=7, now=now)

    assert artifact["currency"] == "EUR"
    assert artifact["generated_at"] == now.isoformat()
    assert artifact["days"] == [["2026-08-31", 67500.0]]  # 2013/08-01 liegen vor dem 7-Tage-Cutoff


def test_export_artifact_cutoff_tracks_now_not_a_stale_timestamp(db_conn):
    # Kernfix vom 01.09.2026: der Cutoff haengt an `now` beim Lauf, nicht an
    # einem alten generated_at im JSON-Artefakt ("steht wieder bei 25.08").
    # Ein Tag, der aus einem 3-Tage-Fenster faellt, sobald "jetzt" weiterrueckt,
    # OHNE dass ein neuer Sync-Lauf noetig war, beweist genau das.
    sync_to_db(db_conn, [(date(2026, 8, 25), 65000.0)])

    artifact_still_in_window = export_artifact(
        db_conn, days=3, now=datetime(2026, 8, 26, tzinfo=timezone.utc)
    )
    artifact_fallen_out_of_window = export_artifact(
        db_conn, days=3, now=datetime(2026, 8, 31, tzinfo=timezone.utc)
    )

    assert artifact_still_in_window["days"] == [["2026-08-25", 65000.0]]
    assert artifact_fallen_out_of_window["days"] == []


def test_export_artifact_empty_window_returns_no_days(db_conn):
    sync_to_db(db_conn, [(date(2020, 1, 1), 10000.0)])

    artifact = export_artifact(
        db_conn, days=7, now=datetime(2026, 8, 31, tzinfo=timezone.utc)
    )

    assert artifact["days"] == []
