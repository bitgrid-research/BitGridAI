"""
Tests fuer btc_price_history — DB-Upsert und Fenster-Export, direkt gegen
eine echte (Test-)DB, kein Netzwerk noetig (fetch_historical_prices selbst
ist in btc_power_law.py getestet).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from src.data.btc_price_history import (
    export_artifact,
    export_full_artifact,
    drop_isolated_outliers,
    normalize_stale_eur,
    sync_raw_to_db,
    sync_to_db,
)
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
    assert artifact["days"] == [
        ["2026-08-31", 67500.0]
    ]  # 2013/08-01 liegen vor dem 7-Tage-Cutoff


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


def test_sync_raw_to_db_writes_eur_and_usd(db_conn):
    written = sync_raw_to_db(
        db_conn,
        [
            (1790000000, 73000.0, 83000.0),
            (1790003600, 73100.0, 83200.0),
        ],
    )

    assert written == 2
    rows = db_conn.execute(
        "SELECT ts, price_eur, price_usd FROM btc_price_raw ORDER BY ts"
    ).fetchall()
    assert rows == [
        (1790000000, 73000.0, 83000.0),
        (1790003600, 73100.0, 83200.0),
    ]


def test_sync_raw_to_db_keeps_none_for_missing_currency(db_conn):
    # Fruehe mempool.space-Jahre kennen keinen EUR-Kurs (Rohwert -1), USD
    # liegt seit Genesis durchgehend vor — clean() in
    # fetch_historical_prices_dual() liefert dafuer bereits None, nicht -1.
    sync_raw_to_db(db_conn, [(1279497600, None, 0.09)])

    row = db_conn.execute(
        "SELECT price_eur, price_usd FROM btc_price_raw WHERE ts = 1279497600"
    ).fetchone()
    assert row == (None, 0.09)


def test_sync_raw_to_db_is_idempotent_upsert(db_conn):
    sync_raw_to_db(db_conn, [(1790000000, 73000.0, 83000.0)])
    sync_raw_to_db(db_conn, [(1790000000, 73999.0, 84000.0)])  # erneuter Abruf

    rows = db_conn.execute("SELECT price_eur, price_usd FROM btc_price_raw").fetchall()
    assert rows == [(73999.0, 84000.0)]  # ueberschrieben, kein Duplikat


def test_export_full_artifact_returns_full_resolution_no_window(db_conn):
    sync_raw_to_db(
        db_conn,
        [
            (1279497600, None, 0.09),  # weit ausserhalb jedes 90-Tage-Fensters
            (1790000000, 73000.0, 83000.0),
            (1790003600, 73100.0, 83200.0),
        ],
    )
    now = datetime(2026, 9, 25, tzinfo=timezone.utc)

    artifact = export_full_artifact(db_conn, now=now)

    assert artifact["generated_at"] == now.isoformat()
    # Kein Cutoff wie export_artifact(): der 2010er-Punkt bleibt drin, die
    # Zeitraum-Buttons im Chart filtern client-seitig aus dieser vollen Reihe.
    assert artifact["points"] == [
        [1279497600, None, 0.09],
        [1790000000, 73000.0, 83000.0],
        [1790003600, 73100.0, 83200.0],
    ]


# Tagesanker 2026-06-18 00:00 UTC (durch 86400 teilbar).
MIDNIGHT = 1781740800


def test_normalize_stale_eur_recomputes_frozen_hourly_eur():
    # Befund 15.10.2026: stuendlicher EUR-Wert tagelang eingefroren (56748),
    # USD laeuft weiter; nur der 00:00-Punkt traegt den richtigen Tageskurs.
    points = [
        (MIDNIGHT, 53720.2, 60980.8),  # Anker: 1.1352 USD je EUR
        (MIDNIGHT + 3600, 56748.0, 61200.0),  # 1.0785 -> > 1 % daneben
    ]

    out, fixed = normalize_stale_eur(points)

    assert fixed == 1
    assert out[0] == [MIDNIGHT, 53720.2, 60980.8]  # Anker unveraendert
    assert out[1] == [MIDNIGHT + 3600, round(61200.0 / (60980.8 / 53720.2), 2), 61200.0]


def test_normalize_stale_eur_keeps_plausible_values():
    points = [
        (MIDNIGHT, 53720.2, 60980.8),
        (MIDNIGHT + 3600, 53900.0, 61250.0),  # 1.1364, innerhalb 1 %
    ]

    out, fixed = normalize_stale_eur(points)

    assert fixed == 0
    assert out[1] == [MIDNIGHT + 3600, 53900.0, 61250.0]


def test_normalize_stale_eur_never_invents_missing_eur():
    out, fixed = normalize_stale_eur(
        [(MIDNIGHT, 53720.2, 60980.8), (MIDNIGHT + 3600, None, 61200.0)]
    )

    assert fixed == 0
    assert out[1] == [MIDNIGHT + 3600, None, 61200.0]


def test_normalize_stale_eur_ignores_outdated_anchor():
    # Anker aelter als 2 Tage: lieber Rohwert behalten als mit altem Kurs rechnen.
    late = MIDNIGHT + 3 * 86400 + 3600
    out, fixed = normalize_stale_eur(
        [(MIDNIGHT, 53720.2, 60980.8), (late, 56748.0, 61200.0)]
    )

    assert fixed == 0
    assert out[1] == [late, 56748.0, 61200.0]


def test_export_full_artifact_applies_eur_normalization(db_conn):
    sync_raw_to_db(
        db_conn,
        [(MIDNIGHT, 53720.2, 60980.8), (MIDNIGHT + 3600, 56748.0, 61200.0)],
    )

    artifact = export_full_artifact(
        db_conn, now=datetime(2026, 9, 25, tzinfo=timezone.utc)
    )

    assert artifact["points"][1][1] == round(61200.0 / (60980.8 / 53720.2), 2)
    # Rohdaten in der DB bleiben unangetastet.
    raw = db_conn.execute(
        "SELECT price_eur FROM btc_price_raw WHERE ts = ?", (MIDNIGHT + 3600,)
    ).fetchone()
    assert raw == (56748.0,)


def test_drop_isolated_outliers_removes_midnight_spike():
    # Befund 15.10.2026: Tageswert einer anderen Quelle zwischen Stundenwerten,
    # in beiden Waehrungen ~4 % daneben.
    points = [
        [MIDNIGHT - 3600, 54500.0, 62239.0],
        [MIDNIGHT, 56437.5, 64733.0],
        [MIDNIGHT + 3600, 54480.0, 62200.0],
    ]

    out, dropped = drop_isolated_outliers(points)

    assert dropped == 1
    assert [p[0] for p in out] == [MIDNIGHT - 3600, MIDNIGHT + 3600]


def test_drop_isolated_outliers_keeps_daily_resolution():
    # Tagesaufloesung (Nachbarn 24 h entfernt): echte Tagesbewegungen bleiben.
    points = [
        [MIDNIGHT - 86400, 61307.0, 71360.0],
        [MIDNIGHT, 57445.0, 66694.0],
        [MIDNIGHT + 86400, 55238.0, 64021.0],
    ]

    out, dropped = drop_isolated_outliers(points)

    assert dropped == 0
    assert out == points


def test_drop_isolated_outliers_keeps_real_step_change():
    # Nachbarn uneinig = echter Sprung, kein Einzelausreisser.
    points = [
        [MIDNIGHT - 3600, 54500.0, 62239.0],
        [MIDNIGHT, 57000.0, 65100.0],
        [MIDNIGHT + 3600, 57100.0, 65200.0],
    ]

    out, dropped = drop_isolated_outliers(points)

    assert dropped == 0
    assert out == points
