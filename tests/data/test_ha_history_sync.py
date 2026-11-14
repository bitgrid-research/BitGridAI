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
    _BATTERY_CHARGE_ENTITY,
    _BATTERY_DISCHARGE_ENTITY,
    _floor_to_block,
    _last_value_in_window,
    apply_battery_power,
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
        inv_map["pv_forecast_kw"]: [(T0, 5.2)],
        inv_map["heizstab_power_w"]: [(T0, 900.0)],
        inv_map["cloud_coverage_pct"]: [(T0, 49.0)],
        inv_map["outdoor_temp_c"]: [(T0, 20.3)],
        inv_map["outdoor_humidity_pct"]: [(T0, 44.0)],
        inv_map["heizung_energy_kwh_today"]: [(T0, 0.1)],
        inv_map["sun_azimuth_deg"]: [(T0, 180.0)],
        inv_map["sun_elevation_deg"]: [(T0, 45.0)],
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


# ---------------------------------------------------------------------------
# apply_battery_power
# ---------------------------------------------------------------------------


def test_apply_battery_power_computes_charge_minus_discharge() -> None:
    entity_readings = _build_entity_readings()
    entity_readings[_BATTERY_CHARGE_ENTITY] = [(T0, 500.0)]
    entity_readings[_BATTERY_DISCHARGE_ENTITY] = [(T0, 0.0)]
    blocks = resample_to_blocks(
        entity_readings, ENTITY_MAP, T0, T0 + timedelta(minutes=10)
    )
    blocks = apply_battery_power(blocks, entity_readings)
    assert blocks[0].battery_power_w == 500.0


def test_apply_battery_power_discharge_is_negative() -> None:
    entity_readings = _build_entity_readings()
    entity_readings[_BATTERY_CHARGE_ENTITY] = [(T0, 0.0)]
    entity_readings[_BATTERY_DISCHARGE_ENTITY] = [(T0, 620.0)]
    blocks = resample_to_blocks(
        entity_readings, ENTITY_MAP, T0, T0 + timedelta(minutes=10)
    )
    blocks = apply_battery_power(blocks, entity_readings)
    assert blocks[0].battery_power_w == -620.0


def test_apply_battery_power_leaves_none_when_no_data() -> None:
    entity_readings = _build_entity_readings()
    blocks = resample_to_blocks(
        entity_readings, ENTITY_MAP, T0, T0 + timedelta(minutes=10)
    )
    blocks = apply_battery_power(blocks, entity_readings)
    assert blocks[0].battery_power_w is None


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


# ---------------------------------------------------------------------------
# Weather/sun/heating fields (bug until 13.11.2026: fetched, never stored)
# ---------------------------------------------------------------------------


def test_resample_passes_weather_fields_to_state() -> None:
    blocks = resample_to_blocks(
        _build_entity_readings(), ENTITY_MAP, T0, T0 + timedelta(minutes=10)
    )
    b = blocks[0]
    assert b.outdoor_temp_c == 20.3
    assert b.outdoor_humidity_pct == 44.0
    assert b.heizung_energy_kwh_today == 0.1
    assert b.sun_azimuth_deg == 180.0
    assert b.sun_elevation_deg == 45.0
    assert b.cloud_coverage_pct is not None


def test_weather_fields_reach_the_database(db_conn) -> None:
    blocks = resample_to_blocks(
        _build_entity_readings(), ENTITY_MAP, T0, T0 + timedelta(minutes=10)
    )
    StateStore(db_conn).write(blocks[0])
    row = db_conn.execute(
        "SELECT outdoor_temp_c, sun_elevation_deg FROM energy_states"
    ).fetchone()
    assert tuple(row) == (20.3, 45.0)


def test_backfill_fills_only_null_cells_of_existing_blocks(
    db_conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.data import ha_history_sync as hs

    readings = _build_entity_readings()
    blocks = resample_to_blocks(readings, ENTITY_MAP, T0, T0 + timedelta(minutes=20))
    store = StateStore(db_conn)
    for b in blocks:  # stored like the buggy sync did: weather NULL
        store.write(hs.dataclasses.replace(b, **{f: None for f in hs.BACKFILL_FIELDS}))
    db_conn.execute(
        "UPDATE energy_states SET outdoor_temp_c = 5.0 WHERE block_id = ?",
        (blocks[0].block_id,),
    )
    db_conn.commit()
    before = db_conn.execute(
        "SELECT block_id, pv_power_w, house_load_w, battery_soc_pct FROM energy_states"
        " ORDER BY block_id"
    ).fetchall()

    monkeypatch.setattr(hs, "fetch_history", lambda *a, **k: readings)
    filled = hs.backfill_columns(
        T0, T0 + timedelta(minutes=30), db_conn, "http://ha", "token"
    )
    # 2 existing blocks; the third (10:20) does not exist and is not created.
    assert filled["sun_elevation_deg"] == 2
    assert filled["outdoor_temp_c"] == 1  # the measured 5.0 is not overwritten
    rows = db_conn.execute(
        "SELECT outdoor_temp_c, sun_elevation_deg FROM energy_states ORDER BY block_id"
    ).fetchall()
    assert [tuple(r) for r in rows] == [(5.0, 45.0), (20.3, 45.0)]
    after = db_conn.execute(
        "SELECT block_id, pv_power_w, house_load_w, battery_soc_pct FROM energy_states"
        " ORDER BY block_id"
    ).fetchall()
    assert [tuple(r) for r in after] == [tuple(r) for r in before]


def test_resample_marks_held_and_zero_house_load_as_warn() -> None:
    # 14.11.2026: a window without readings repeats the last value; when the
    # house load is older than 30 min HA was down, and 0 W is never real.
    from src.data.ha_history_sync import STALE_AFTER

    load = "sensor.house_load_w"
    emap = [
        (load, "house_load_w"),
        ("sensor.pv_power_w", "pv_power_w"),
        ("sensor.battery_soc_pct", "battery_soc_pct"),
    ]
    readings = {
        load: [(T0, 450.0), (T0 + timedelta(minutes=50), 0.0)],
        "sensor.pv_power_w": [(T0, 100.0)],
        "sensor.battery_soc_pct": [(T0, 50.0)],
    }
    states = resample_to_blocks(readings, emap, T0, T0 + timedelta(minutes=60))
    by_id = {s.block_id[11:16]: s for s in states}
    assert STALE_AFTER == timedelta(minutes=30)
    assert by_id["10:00"].quality == "ok"
    assert by_id["10:20"].quality == "ok"  # last reading 30 min old: still fine
    assert by_id["10:30"].quality == "warn"
    assert "house_load_w:held" in by_id["10:30"].missing_signals
    assert by_id["10:50"].quality == "warn"
    assert "house_load_w:zero" in by_id["10:50"].missing_signals


def test_mark_unmeasured_sets_warn_once_and_keeps_values(db_conn) -> None:
    from src.data.ha_history_sync import mark_unmeasured

    for i in range(8):
        b = (T0 + timedelta(minutes=10 * i)).strftime("%Y-%m-%dT%H:%M:%S")
        load = 0.0 if i < 4 else 300.0 + i
        db_conn.execute(
            "INSERT INTO energy_states (block_id, window_start, window_end,"
            " pv_power_w, house_load_w, grid_import_w, battery_soc_pct,"
            " miner_temp_c, miner_heartbeat_age_sec, surplus_kw, quality,"
            " missing_signals_json) VALUES (?, ?, ?, 0, ?, 0, 50, 0, 0, 0, 'ok', '[]')",
            (b, b, b, load),
        )
    db_conn.commit()
    assert mark_unmeasured(db_conn) == {"held": 0, "zero": 4}
    assert mark_unmeasured(db_conn) == {"held": 0, "zero": 0}
    rows = db_conn.execute(
        "SELECT quality, missing_signals_json, house_load_w FROM energy_states"
        " ORDER BY block_id"
    ).fetchall()
    assert [r[0] for r in rows] == ["warn"] * 4 + ["ok"] * 4
    assert rows[0][1] == '["house_load_w:zero"]' and rows[0][2] == 0.0
