"""
Tests fuer ha_history_sync — Resampling und Gap-Check ohne Netzwerk.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.data.db import get_connection
from src.data.gap_check import find_gaps, gap_count_minutes
from src.data.ha_history_sync import (
    DEVICE_ENTITY_MAP,
    ENTITY_MAP,
    _floor_to_block,
    _last_value_in_window,
    resample_device_blocks,
    resample_to_blocks,
)
from src.data.state_store import StateStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

T0 = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def db_conn(tmp_path: Path):
    conn = get_connection(tmp_path / "test.db")
    yield conn
    conn.close()


def _readings(*pairs: tuple[int, float]) -> list[tuple[datetime, float | None]]:
    """Erstellt (datetime, value)-Paare aus (minute_offset, value)."""
    return [(T0 + timedelta(minutes=m), v) for m, v in pairs]


# ---------------------------------------------------------------------------
# _floor_to_block
# ---------------------------------------------------------------------------


def test_floor_to_block_aligned() -> None:
    ts = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert _floor_to_block(ts) == ts


def test_floor_to_block_rounds_down() -> None:
    ts = datetime(2026, 6, 1, 10, 7, 34, tzinfo=timezone.utc)
    expected = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert _floor_to_block(ts) == expected


def test_floor_to_block_boundary() -> None:
    ts = datetime(2026, 6, 1, 10, 10, 0, tzinfo=timezone.utc)
    assert _floor_to_block(ts) == ts


# ---------------------------------------------------------------------------
# _last_value_in_window
# ---------------------------------------------------------------------------


def test_last_value_uses_last_in_window() -> None:
    readings = _readings((2, 100.0), (5, 200.0), (8, 300.0))
    win_start = T0
    win_end = T0 + timedelta(minutes=10)
    assert _last_value_in_window(readings, win_start, win_end) == 300.0


def test_last_value_forward_fills_when_empty_window() -> None:
    readings = _readings((0, 42.0))  # vor dem Fenster
    win_start = T0 + timedelta(minutes=10)
    win_end = T0 + timedelta(minutes=20)
    assert _last_value_in_window(readings, win_start, win_end) == 42.0


def test_last_value_returns_none_if_no_data() -> None:
    readings: list[tuple[datetime, float | None]] = []
    win_start = T0
    win_end = T0 + timedelta(minutes=10)
    assert _last_value_in_window(readings, win_start, win_end) is None


def test_last_value_skips_none_values() -> None:
    readings = [(T0 + timedelta(minutes=2), 50.0), (T0 + timedelta(minutes=5), None)]
    win_start = T0
    win_end = T0 + timedelta(minutes=10)
    # None im Fenster wird ignoriert, letzter gueltiger Wert = 50.0
    assert _last_value_in_window(readings, win_start, win_end) == 50.0


# ---------------------------------------------------------------------------
# resample_to_blocks
# ---------------------------------------------------------------------------


def _build_entity_readings(
    pv: float = 5000.0,
    load: float = 500.0,
    soc: float = 80.0,
) -> dict[str, list[tuple[datetime, float | None]]]:
    entity_id_map = dict(ENTITY_MAP)
    inv_map = {v: k for k, v in entity_id_map.items()}
    return {
        inv_map["pv_power_w"]: [(T0, pv)],
        inv_map["house_load_w"]: [(T0, load)],
        inv_map["grid_import_w"]: [(T0, 0.0)],
        inv_map["grid_export_w"]: [(T0, 4.5)],
        inv_map["battery_soc_pct"]: [(T0, soc)],
        inv_map["miner_temp_c"]: [(T0, 85.0)],
        inv_map["miner_heartbeat_age_sec"]: [(T0, 5.0)],
        inv_map["miner_power_w"]: [(T0, 1700.0)],
        inv_map["energy_price_ct_kwh"]: [(T0, 18.5)],
        inv_map["pv_forecast_kw"]: [(T0, 5.2)],
    }


def test_resample_produces_correct_block_count() -> None:
    entity_readings = _build_entity_readings()
    start = T0
    end = T0 + timedelta(hours=1)  # 6 Bloecke
    blocks = resample_to_blocks(entity_readings, ENTITY_MAP, start, end)
    assert len(blocks) == 6


def test_resample_block_ids_are_utc_aligned() -> None:
    entity_readings = _build_entity_readings()
    blocks = resample_to_blocks(
        entity_readings, ENTITY_MAP, T0, T0 + timedelta(minutes=30)
    )
    assert blocks[0].block_id == "2026-06-01T10:00:00"
    assert blocks[1].block_id == "2026-06-01T10:10:00"
    assert blocks[2].block_id == "2026-06-01T10:20:00"


def test_resample_surplus_computed_correctly() -> None:
    entity_readings = _build_entity_readings(pv=5000.0, load=500.0)
    blocks = resample_to_blocks(
        entity_readings, ENTITY_MAP, T0, T0 + timedelta(minutes=10)
    )
    assert abs(blocks[0].surplus_kw - 4.5) < 0.001


def test_resample_quality_ok_when_all_present() -> None:
    entity_readings = _build_entity_readings()
    blocks = resample_to_blocks(
        entity_readings, ENTITY_MAP, T0, T0 + timedelta(minutes=10)
    )
    assert blocks[0].quality == "ok"
    assert blocks[0].missing_signals == ()


def test_resample_quality_warn_on_one_critical_missing() -> None:
    entity_readings = _build_entity_readings()
    # SoC entfernen
    entity_readings.pop("sensor.battery_soc_pct", None)
    blocks = resample_to_blocks(
        entity_readings, ENTITY_MAP, T0, T0 + timedelta(minutes=10)
    )
    assert blocks[0].quality == "warn"
    assert "battery_soc_pct" in blocks[0].missing_signals


def test_resample_forward_fills_across_blocks() -> None:
    # SoC nur im ersten Block vorhanden
    entity_id_map = dict(ENTITY_MAP)
    inv_map = {v: k for k, v in entity_id_map.items()}
    entity_readings = _build_entity_readings()
    # SoC nur bei T0, nicht danach
    entity_readings[inv_map["battery_soc_pct"]] = [(T0, 77.0)]

    blocks = resample_to_blocks(
        entity_readings, ENTITY_MAP, T0, T0 + timedelta(minutes=30)
    )
    # Alle Bloecke sollen 77.0 haben (Forward-Fill)
    for b in blocks:
        assert b.battery_soc_pct == 77.0


# ---------------------------------------------------------------------------
# resample_device_blocks / device_states-Upsert
# ---------------------------------------------------------------------------

_FRIDGE = "sensor.shellyplugsg3_9070694abdf4_leistung"
_TV = "sensor.shellyplugsg3_9070694c99d4_leistung"


def test_device_resample_one_row_per_device_and_block() -> None:
    entity_readings = {_FRIDGE: _readings((0, 87.0)), _TV: _readings((0, 0.0))}
    rows = resample_device_blocks(
        entity_readings, DEVICE_ENTITY_MAP, T0, T0 + timedelta(minutes=30)
    )
    # 3 Bloecke x 2 Plugs mit Daten (die 4 anderen Plugs ohne Daten fehlen)
    assert len(rows) == 6
    assert ("2026-06-01T10:00:00", "kuehlschraenke", 87.0) in rows
    assert ("2026-06-01T10:20:00", "tv", 0.0) in rows


def test_device_resample_forward_fills_across_blocks() -> None:
    entity_readings = {_FRIDGE: _readings((2, 90.0))}
    rows = resample_device_blocks(
        entity_readings, DEVICE_ENTITY_MAP, T0, T0 + timedelta(minutes=30)
    )
    # Wert nur im ersten Block, danach Forward-Fill
    assert rows == [
        ("2026-06-01T10:00:00", "kuehlschraenke", 90.0),
        ("2026-06-01T10:10:00", "kuehlschraenke", 90.0),
        ("2026-06-01T10:20:00", "kuehlschraenke", 90.0),
    ]


def test_device_resample_skips_devices_without_any_data() -> None:
    rows = resample_device_blocks({}, DEVICE_ENTITY_MAP, T0, T0 + timedelta(hours=1))
    assert rows == []


def test_device_states_insert_or_ignore(db_conn) -> None:
    row = ("2026-06-01T10:00:00", "kuehlschraenke", 87.0)
    cur = db_conn.execute(
        "INSERT OR IGNORE INTO device_states (block_id, device, power_w)"
        " VALUES (?, ?, ?)",
        row,
    )
    assert cur.rowcount == 1
    # Zweiter Insert mit anderem Wert wird ignoriert (kein Ueberschreiben)
    cur = db_conn.execute(
        "INSERT OR IGNORE INTO device_states (block_id, device, power_w)"
        " VALUES (?, ?, ?)",
        ("2026-06-01T10:00:00", "kuehlschraenke", 999.0),
    )
    assert cur.rowcount == 0
    value = db_conn.execute(
        "SELECT power_w FROM device_states WHERE block_id = ? AND device = ?",
        ("2026-06-01T10:00:00", "kuehlschraenke"),
    ).fetchone()[0]
    assert value == 87.0


# ---------------------------------------------------------------------------
# find_gaps / gap_count_minutes
# ---------------------------------------------------------------------------


def _write_block(store: StateStore, t: datetime) -> None:
    from datetime import timedelta

    store.write(
        __import__("src.core.models", fromlist=["EnergyState"]).EnergyState(
            block_id=t.strftime("%Y-%m-%dT%H:%M:%S"),
            window_start=t,
            window_end=t + timedelta(minutes=10),
            pv_power_w=1000.0,
            house_load_w=300.0,
            grid_import_w=0.0,
            battery_soc_pct=80.0,
            miner_temp_c=85.0,
            miner_heartbeat_age_sec=5.0,
            surplus_kw=0.7,
            quality="ok",
        )
    )


def test_find_gaps_no_gaps(db_conn) -> None:
    store = StateStore(db_conn)
    start = T0
    end = T0 + timedelta(hours=1)
    t = start
    while t < end:
        _write_block(store, t)
        t += timedelta(minutes=10)
    gaps = find_gaps(db_conn, start, end)
    assert gaps == []


def test_find_gaps_detects_inner_gap(db_conn) -> None:
    store = StateStore(db_conn)
    # Schreibe 10:00, 10:10, dann Luecke, dann 11:00
    for offset in [0, 10, 60]:
        _write_block(store, T0 + timedelta(minutes=offset))
    gaps = find_gaps(db_conn, T0, T0 + timedelta(minutes=70))
    assert len(gaps) == 1
    gap_start, gap_end = gaps[0]
    assert gap_start == T0 + timedelta(minutes=20)
    assert gap_end == T0 + timedelta(minutes=60)


def test_gap_count_minutes(db_conn) -> None:
    store = StateStore(db_conn)
    _write_block(store, T0)
    _write_block(store, T0 + timedelta(hours=1))
    gaps = find_gaps(db_conn, T0, T0 + timedelta(minutes=70))
    total = gap_count_minutes(gaps)
    assert total == 50.0  # 10:10 bis 11:00 = 50 min


def test_find_gaps_empty_db_returns_full_range(db_conn) -> None:
    start = T0
    end = T0 + timedelta(hours=2)
    gaps = find_gaps(db_conn, start, end)
    assert len(gaps) == 1
    assert gaps[0] == (start, end)
