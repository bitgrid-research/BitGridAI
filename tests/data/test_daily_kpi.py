"""
Tests fuer daily_kpi — energy_to_sats-Berechnung in compute_day().

daily_kpi.py hatte bisher keine Tests. Dieser Umfang deckt bewusst nur den
neuen energy_to_sats-Zweig ab (die einzige bis dahin ungetestete Arithmetik
im Modul), keine vollstaendige Abdeckung des restlichen Moduls.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from src.data.daily_kpi import compute_day
from src.data.db import get_connection


@pytest.fixture
def db_conn(tmp_path: Path):
    conn = get_connection(tmp_path / "test.db")
    yield conn
    conn.close()


def _insert_energy_block(conn, block_id: str, miner_power_w: float) -> None:
    conn.execute(
        "INSERT INTO energy_states (block_id, window_start, window_end,"
        " pv_power_w, house_load_w, grid_import_w, grid_export_w,"
        " miner_power_w, heizstab_power_w, battery_soc_pct, quality,"
        " missing_signals_json) VALUES (?, ?, ?, 3000, 500, 0, 2000, ?, 0, 80,"
        " 'ok', '[]')",
        (block_id, block_id, block_id, miner_power_w),
    )
    conn.commit()


def test_compute_day_without_settlement_leaves_energy_to_sats_null(db_conn):
    _insert_energy_block(db_conn, "2026-08-20T10:00:00", 1500)

    assert compute_day(db_conn, date(2026, 8, 20)) is True

    row = db_conn.execute(
        "SELECT mining_kwh, energy_to_sats FROM daily_kpi WHERE day = '2026-08-20'"
    ).fetchone()
    assert row[0] == pytest.approx(0.25)  # 1500 W * 10 min = 0.25 kWh
    assert row[1] is None


def test_compute_day_with_settlement_computes_sats_per_kwh(db_conn):
    _insert_energy_block(db_conn, "2026-08-20T10:00:00", 1500)
    db_conn.execute(
        "INSERT INTO bitcoin_daily_settlement (day, earned_btc, pool_ths_avg,"
        " btc_eur_price_approx, source, captured_at) VALUES"
        " ('2026-08-20', 0.0000005, 55.0, 60000.0,"
        " 'ha:pool_settlement_history', '2026-08-21T04:00:00')"
    )
    db_conn.commit()

    assert compute_day(db_conn, date(2026, 8, 20)) is True

    row = db_conn.execute(
        "SELECT mining_kwh, energy_to_sats FROM daily_kpi WHERE day = '2026-08-20'"
    ).fetchone()
    mining_kwh, energy_to_sats = row
    expected = round(0.0000005 * 1e8 / mining_kwh, 2)
    assert energy_to_sats == expected


def test_compute_day_zero_mining_kwh_leaves_energy_to_sats_null(db_conn):
    # Miner lief nicht (miner_power_w = 0), aber Abrechnung liegt vor.
    _insert_energy_block(db_conn, "2026-08-20T10:00:00", 0)
    db_conn.execute(
        "INSERT INTO bitcoin_daily_settlement (day, earned_btc, pool_ths_avg,"
        " btc_eur_price_approx, source, captured_at) VALUES"
        " ('2026-08-20', 0.0000005, 55.0, 60000.0,"
        " 'ha:pool_settlement_history', '2026-08-21T04:00:00')"
    )
    db_conn.commit()

    assert compute_day(db_conn, date(2026, 8, 20)) is True

    row = db_conn.execute(
        "SELECT mining_kwh, energy_to_sats FROM daily_kpi WHERE day = '2026-08-20'"
    ).fetchone()
    assert row[0] == 0.0
    assert row[1] is None


def test_compute_day_no_blocks_returns_false_and_writes_nothing(db_conn):
    assert compute_day(db_conn, date(2026, 8, 20)) is False
    row = db_conn.execute("SELECT * FROM daily_kpi WHERE day = '2026-08-20'").fetchone()
    assert row is None
