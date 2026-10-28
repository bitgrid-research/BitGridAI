"""
Tests fuer auto_repair - die Leitplanken sind hier das Wichtigste.

Die Reparatur darf Luecken schliessen, aber niemals echte Messwerte
ueberschreiben oder bei einem Programmierfehler die halbe Datenbank
umschreiben. Genau das pruefen diese Tests.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from src.adapters.sma_webconnect_log import resample_to_blocks
from src.data.auto_repair import (
    MAX_BLOCKS_PER_RUN,
    RECONSTRUCTED_MARKER,
    find_pv_zero_blocks,
    reconstruct_pv_from_meter,
    remove_future_blocks,
    report_day_deviation,
)
from src.data.db import get_connection

BASE = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def conn(tmp_path: Path) -> Any:
    connection = get_connection(tmp_path / "test.db")
    yield connection
    connection.close()


def _insert_block(
    connection: sqlite3.Connection,
    ts: datetime,
    pv: float,
    house: float = 500.0,
    grid: float = 0.0,
    quality: str = "ok",
) -> None:
    stamp = ts.strftime("%Y-%m-%dT%H:%M")
    connection.execute(
        "INSERT INTO energy_states (block_id, window_start, window_end,"
        " pv_power_w, house_load_w, grid_import_w, quality)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (stamp, stamp, stamp, pv, house, grid, quality),
    )
    connection.commit()


# --- Stufe 1: Zukunftsbloecke ---------------------------------------------


def test_removes_blocks_that_lie_in_the_future(conn: sqlite3.Connection) -> None:
    now = BASE
    _insert_block(conn, now - timedelta(minutes=10), 3000.0)
    _insert_block(conn, now + timedelta(minutes=10), 3000.0)
    _insert_block(conn, now + timedelta(hours=5), 3000.0)

    action = remove_future_blocks(conn, now, apply=True)

    assert action.applied
    assert action.blocks == 2
    remaining = conn.execute("SELECT COUNT(*) FROM energy_states").fetchone()[0]
    assert remaining == 1


def test_dry_run_keeps_future_blocks(conn: sqlite3.Connection) -> None:
    _insert_block(conn, BASE + timedelta(hours=1), 3000.0)

    action = remove_future_blocks(conn, BASE, apply=False)

    assert action.blocks == 1
    assert not action.applied
    assert conn.execute("SELECT COUNT(*) FROM energy_states").fetchone()[0] == 1


def test_future_cleanup_stops_above_limit(conn: sqlite3.Connection) -> None:
    for i in range(MAX_BLOCKS_PER_RUN + 1):
        _insert_block(conn, BASE + timedelta(minutes=10 * (i + 1)), 1.0)

    action = remove_future_blocks(conn, BASE, apply=True)

    assert action.blocked
    assert not action.applied
    # Nichts angefasst: das Limit ist eine Notbremse, keine Teilausfuehrung.
    count = conn.execute("SELECT COUNT(*) FROM energy_states").fetchone()[0]
    assert count == MAX_BLOCKS_PER_RUN + 1


# --- Stufe 2: PV-Rekonstruktion -------------------------------------------


def test_reconstructs_only_zeros_the_meter_contradicts(
    conn: sqlite3.Connection,
) -> None:
    zero_with_sun = BASE
    zero_at_night = BASE + timedelta(minutes=10)
    _insert_block(conn, zero_with_sun, 0.0)
    _insert_block(conn, zero_at_night, 0.0)

    device = {zero_with_sun: 4200.0, zero_at_night: 0.0}
    action = reconstruct_pv_from_meter(
        conn, BASE - timedelta(days=1), BASE + timedelta(days=1), device, apply=True
    )

    assert action.applied
    assert action.blocks == 1
    rows = dict(
        conn.execute("SELECT window_start, pv_power_w FROM energy_states").fetchall()
    )
    assert rows[zero_with_sun.strftime("%Y-%m-%dT%H:%M")] == 4200.0
    # Die Nacht-Null bleibt eine Null: ihr widerspricht kein Zaehlerzuwachs.
    assert rows[zero_at_night.strftime("%Y-%m-%dT%H:%M")] == 0.0


def test_never_overwrites_an_existing_measurement(conn: sqlite3.Connection) -> None:
    _insert_block(conn, BASE, 1500.0)

    action = reconstruct_pv_from_meter(
        conn,
        BASE - timedelta(days=1),
        BASE + timedelta(days=1),
        {BASE: 9999.0},
        apply=True,
    )

    assert action.blocks == 0
    value = conn.execute("SELECT pv_power_w FROM energy_states").fetchone()[0]
    assert value == 1500.0


def test_reconstruction_is_marked_and_idempotent(conn: sqlite3.Connection) -> None:
    _insert_block(conn, BASE, 0.0)
    device = {BASE: 3000.0}
    window = (BASE - timedelta(days=1), BASE + timedelta(days=1))

    first = reconstruct_pv_from_meter(conn, *window, device, apply=True)
    assert first.blocks == 1

    quality, missing = conn.execute(
        "SELECT quality, missing_signals_json FROM energy_states"
    ).fetchone()
    assert quality == "warn"
    assert RECONSTRUCTED_MARKER in json.loads(missing)

    # Zweiter Lauf darf denselben Block nicht erneut anfassen.
    second = reconstruct_pv_from_meter(conn, *window, device, apply=True)
    assert second.blocks == 0


def test_surplus_is_recomputed_from_the_new_pv_value(
    conn: sqlite3.Connection,
) -> None:
    _insert_block(conn, BASE, 0.0, house=1000.0, grid=200.0)

    reconstruct_pv_from_meter(
        conn,
        BASE - timedelta(days=1),
        BASE + timedelta(days=1),
        {BASE: 3000.0},
        apply=True,
    )

    surplus = conn.execute("SELECT surplus_kw FROM energy_states").fetchone()[0]
    assert surplus == pytest.approx((3000.0 - 1000.0 - 200.0) / 1000)


def test_noise_below_threshold_is_left_alone(conn: sqlite3.Connection) -> None:
    _insert_block(conn, BASE, 0.0)

    action = reconstruct_pv_from_meter(
        conn,
        BASE - timedelta(days=1),
        BASE + timedelta(days=1),
        {BASE: 5.0},
        apply=True,
    )

    assert action.blocks == 0


def test_zero_blocks_query_skips_already_reconstructed(
    conn: sqlite3.Connection,
) -> None:
    _insert_block(conn, BASE, 0.0)
    conn.execute(
        "UPDATE energy_states SET missing_signals_json = ?",
        (json.dumps([RECONSTRUCTED_MARKER]),),
    )
    conn.commit()

    found = find_pv_zero_blocks(
        conn, BASE - timedelta(days=1), BASE + timedelta(days=1)
    )

    assert found == []


# --- Stufe 3: nur melden ---------------------------------------------------


def test_day_deviation_reports_but_changes_nothing(conn: sqlite3.Connection) -> None:
    # Sechs Bloecke à 1000 W = 1,0 kWh in der Datenbank
    for i in range(6):
        _insert_block(conn, BASE + timedelta(minutes=10 * i), 1000.0)

    action = report_day_deviation(conn, {"2026-09-23": 10.0})

    assert action.blocks == 1
    assert not action.applied
    assert "2026-09-23" in action.detail
    value = conn.execute("SELECT pv_power_w FROM energy_states LIMIT 1").fetchone()[0]
    assert value == 1000.0


def test_day_deviation_silent_within_tolerance(conn: sqlite3.Connection) -> None:
    for i in range(6):
        _insert_block(conn, BASE + timedelta(minutes=10 * i), 1000.0)

    action = report_day_deviation(conn, {"2026-09-23": 1.0})

    assert action.blocks == 0


# --- Resampling ------------------------------------------------------------


def test_resample_converts_meter_readings_to_average_power() -> None:
    start = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)
    # 500 Wh Zuwachs je fuenf Minuten entspricht 6000 W
    series = [
        (start, 1000),
        (start + timedelta(minutes=5), 1500),
        (start + timedelta(minutes=10), 2000),
    ]

    blocks = resample_to_blocks(series, block_minutes=10)

    assert blocks[start] == pytest.approx(6000.0)


def test_resample_skips_blocks_without_both_edges() -> None:
    start = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)
    series = [(start, 1000), (start + timedelta(minutes=5), 1500)]

    blocks = resample_to_blocks(series, block_minutes=10)

    # Der Block braucht einen Randwert bei +10 min, den es nicht gibt.
    assert blocks == {}


def test_resample_needs_at_least_two_points() -> None:
    start = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)
    assert resample_to_blocks([(start, 1000)]) == {}
    assert resample_to_blocks([]) == {}
