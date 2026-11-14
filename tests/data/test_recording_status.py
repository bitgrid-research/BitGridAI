"""
Tests for recording_status — the read-only health report of the research DB.

All dates are relative to an injected ``NOW``. Fixed calendar dates would drift
out of the evaluated window and turn the tests red without any code change.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from src.data.db import get_connection
from src.data.recording_status import (
    BLOCKS_PER_DAY,
    HISTORY_DAYS,
    MAX_AGE_HOURS,
    apply_sync,
    build_status,
    open_readonly,
    parse_sync_log,
    read_sync_log,
    run,
    write_atomic,
)

# 03:55 UTC, shortly after a nightly sync.
NOW = datetime(2026, 3, 10, 3, 55, 0, tzinfo=timezone.utc)
TODAY = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
FIRST_DAY = TODAY - timedelta(days=HISTORY_DAYS)
STEP = timedelta(minutes=10)


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = get_connection(tmp_path / "test.db")
    yield connection
    connection.close()


def _block_id(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%S")


def _add_energy(
    conn: sqlite3.Connection,
    ts: datetime,
    quality: str = "ok",
    missing: str = "[]",
) -> None:
    conn.execute(
        "INSERT INTO energy_states (block_id, window_start, window_end, quality,"
        " missing_signals_json) VALUES (?, ?, ?, ?, ?)",
        (_block_id(ts), ts.isoformat(), (ts + STEP).isoformat(), quality, missing),
    )


def _add_side_tables(conn: sqlite3.Connection, ts: datetime) -> None:
    conn.execute(
        "INSERT INTO device_states (block_id, device, power_w) VALUES (?, 'x', 1.0)",
        (_block_id(ts),),
    )
    conn.execute(
        "INSERT INTO miner_states (block_id, miner) VALUES (?, 'miner1')",
        (_block_id(ts),),
    )


def _fill(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
    skip_day: datetime | None = None,
) -> None:
    """Write one energy block per 10 minutes in [start, end)."""
    ts = start
    while ts < end:
        if skip_day is None or not (skip_day <= ts < skip_day + timedelta(days=1)):
            _add_energy(conn, ts)
        ts += STEP


def _healthy(conn: sqlite3.Connection, end: datetime | None = None) -> None:
    last = end or NOW.replace(minute=30)
    _fill(conn, FIRST_DAY, last)
    _add_side_tables(conn, last - STEP)
    conn.commit()


def test_healthy_database_is_ok(conn: sqlite3.Connection) -> None:
    _healthy(conn)
    status = build_status(conn, NOW)

    assert status["level"] == "ok"
    assert status["reasons"] == []
    assert status["generated_at"] == "2026-03-10T03:55:00Z"
    assert status["max_age_hours"] == MAX_AGE_HOURS
    assert status["tables"]["energy_states"]["latest_block"] == "2026-03-10T03:20:00Z"

    days = status["days"]
    assert len(days) == HISTORY_DAYS + 1
    assert [d["complete"] for d in days] == [True] * HISTORY_DAYS + [False]
    assert all(d["blocks"] == BLOCKS_PER_DAY for d in days[:-1])
    # The running day is partial by nature and must not degrade the level.
    assert 0 < days[-1]["blocks"] < BLOCKS_PER_DAY


def test_same_input_gives_same_report(conn: sqlite3.Connection) -> None:
    _healthy(conn)
    assert build_status(conn, NOW) == build_status(conn, NOW)


def test_stale_database_is_error(conn: sqlite3.Connection) -> None:
    last = NOW - timedelta(hours=MAX_AGE_HOURS + 1)
    _fill(conn, FIRST_DAY, last)
    _add_side_tables(conn, NOW - STEP)
    conn.commit()

    status = build_status(conn, NOW)

    assert status["level"] == "error"
    assert any("Sync läuft nicht" in r for r in status["reasons"])


def test_age_exactly_at_limit_is_not_stale(conn: sqlite3.Connection) -> None:
    # NOW is not on the 10-minute grid, so the boundary block is written
    # explicitly instead of relying on the fill loop to hit it.
    last_block = NOW - timedelta(hours=MAX_AGE_HOURS)
    _fill(conn, FIRST_DAY, last_block - timedelta(hours=1))
    _add_energy(conn, last_block)
    _add_side_tables(conn, NOW - STEP)
    conn.commit()

    status = build_status(conn, NOW)

    assert status["tables"]["energy_states"]["age_hours"] == MAX_AGE_HOURS
    assert not any("Sync läuft nicht" in r for r in status["reasons"])


def test_short_day_is_warn(conn: sqlite3.Connection) -> None:
    _healthy(conn)
    day = TODAY - timedelta(days=3)
    conn.execute(
        "DELETE FROM energy_states WHERE block_id >= ? AND block_id < ?",
        (_block_id(day), _block_id(day + 44 * STEP)),
    )
    conn.commit()

    status = build_status(conn, NOW)

    assert status["level"] == "warn"
    assert any(f"{day:%Y-%m-%d} (100/144)" in r for r in status["reasons"])


def test_empty_day_is_error(conn: sqlite3.Connection) -> None:
    day = TODAY - timedelta(days=2)
    _fill(conn, FIRST_DAY, NOW.replace(minute=30), skip_day=day)
    _add_side_tables(conn, NOW - STEP)
    conn.commit()

    status = build_status(conn, NOW)

    assert status["level"] == "error"
    assert any(
        "ganz ohne Daten" in r and f"{day:%Y-%m-%d}" in r for r in status["reasons"]
    )


def test_quality_warn_and_missing_signals_are_counted(
    conn: sqlite3.Connection,
) -> None:
    _healthy(conn)
    day = TODAY - timedelta(days=1)
    conn.execute(
        "UPDATE energy_states SET quality = 'warn',"
        " missing_signals_json = '[\"pv_power_w\"]' WHERE block_id = ?",
        (_block_id(day),),
    )
    conn.commit()

    status = build_status(conn, NOW)
    row = next(d for d in status["days"] if d["date"] == f"{day:%Y-%m-%d}")

    assert status["level"] == "warn"
    assert row["quality_warn"] == 1
    assert row["missing_signals"] == 1
    assert row["quality_error"] == 0


def test_quality_error_beats_warn(conn: sqlite3.Connection) -> None:
    _healthy(conn)
    day = TODAY - timedelta(days=1)
    conn.execute(
        "UPDATE energy_states SET quality = 'warn' WHERE block_id = ?",
        (_block_id(day),),
    )
    conn.execute(
        "UPDATE energy_states SET quality = 'error' WHERE block_id = ?",
        (_block_id(day + STEP),),
    )
    conn.commit()

    status = build_status(conn, NOW)

    assert status["level"] == "error"
    assert any("quality=error" in r for r in status["reasons"])
    assert any("quality=warn" in r for r in status["reasons"])


def test_lagging_side_table_is_warn(conn: sqlite3.Connection) -> None:
    _fill(conn, FIRST_DAY, NOW.replace(minute=30))
    _add_side_tables(conn, NOW - timedelta(hours=MAX_AGE_HOURS + 4))
    conn.commit()

    status = build_status(conn, NOW)

    assert status["level"] == "warn"
    assert any("device_states hängt" in r for r in status["reasons"])
    assert any("miner_states hängt" in r for r in status["reasons"])


def test_history_without_gaps(conn: sqlite3.Connection) -> None:
    _healthy(conn)
    history = build_status(conn, NOW)["history"]

    assert history["first_day"] == f"{FIRST_DAY:%Y-%m-%d}"
    assert history["evaluated_from"] == f"{FIRST_DAY:%Y-%m-%d}"
    assert history["evaluated_to"] == f"{TODAY - timedelta(days=1):%Y-%m-%d}"
    assert history["days_total"] == HISTORY_DAYS
    assert history["days_complete"] == HISTORY_DAYS
    assert history["missing_ranges"] == []
    assert history["partial"] == []


def test_history_merges_old_missing_days_without_changing_level(
    conn: sqlite3.Connection,
) -> None:
    # Recording started 40 days ago at 16:20, then ran with three holes that
    # all lie outside the 7-day window evaluated for the level.
    start = TODAY - timedelta(days=40) + timedelta(hours=16, minutes=20)
    _fill(conn, start, NOW.replace(minute=30))
    _add_side_tables(conn, NOW - STEP)

    def day(offset: int) -> datetime:
        return TODAY - timedelta(days=offset)

    def drop(first: datetime, last_exclusive: datetime) -> None:
        conn.execute(
            "DELETE FROM energy_states WHERE block_id >= ? AND block_id < ?",
            (_block_id(first), _block_id(last_exclusive)),
        )

    drop(day(30), day(27))  # three consecutive days
    drop(day(20), day(19))  # a single day
    drop(day(15), day(15) + 44 * STEP)  # partial day, 100 blocks left
    conn.commit()

    status = build_status(conn, NOW)
    history = status["history"]

    assert status["level"] == "ok"
    assert history["first_day"] == f"{day(40):%Y-%m-%d}"
    assert history["first_day_blocks"] == 46
    # The start day is partial by nature and not part of the evaluation.
    assert history["evaluated_from"] == f"{day(39):%Y-%m-%d}"
    assert history["days_total"] == 39
    assert history["days_missing"] == 4
    assert history["days_partial"] == 1
    assert history["days_complete"] == 34
    assert history["missing_ranges"] == [
        {"from": f"{day(30):%Y-%m-%d}", "to": f"{day(28):%Y-%m-%d}", "days": 3},
        {"from": f"{day(20):%Y-%m-%d}", "to": f"{day(20):%Y-%m-%d}", "days": 1},
    ]
    assert history["partial"] == [{"date": f"{day(15):%Y-%m-%d}", "blocks": 100}]

    by_day = history["blocks_by_day"]
    assert by_day[f"{day(40):%Y-%m-%d}"] == 46
    assert by_day[f"{day(15):%Y-%m-%d}"] == 100
    assert by_day[f"{day(1):%Y-%m-%d}"] == BLOCKS_PER_DAY
    # Missing days are absent, the running day is not part of the history.
    assert f"{day(29):%Y-%m-%d}" not in by_day
    assert f"{TODAY:%Y-%m-%d}" not in by_day
    assert list(by_day) == sorted(by_day)


def test_history_counts_quality_blocks_of_the_whole_period(
    conn: sqlite3.Connection,
) -> None:
    start = TODAY - timedelta(days=30)
    _fill(conn, start, NOW.replace(minute=30))
    _add_side_tables(conn, NOW - STEP)
    conn.execute(
        "UPDATE energy_states SET quality = 'error' WHERE block_id = ?",
        (_block_id(start + STEP),),
    )
    conn.commit()

    status = build_status(conn, NOW)

    # Outside the 7-day window: visible in the history, no effect on level.
    assert status["level"] == "ok"
    assert status["history"]["quality_error_blocks"] == 1


def test_history_is_none_when_only_today_has_data(conn: sqlite3.Connection) -> None:
    _fill(conn, TODAY, NOW.replace(minute=30))
    conn.commit()

    assert build_status(conn, NOW)["history"] is None


def test_empty_database_is_error(conn: sqlite3.Connection) -> None:
    status = build_status(conn, NOW)

    assert status["level"] == "error"
    assert status["history"] is None
    assert status["days"] == []
    assert any("energy_states ist leer" in r for r in status["reasons"])


def test_missing_table_is_error(tmp_path: Path) -> None:
    bare = sqlite3.connect(tmp_path / "bare.db")
    try:
        status = build_status(bare, NOW)
    finally:
        bare.close()

    assert status["level"] == "error"
    assert status["tables"]["energy_states"]["exists"] is False


def test_naive_now_is_rejected(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError):
        build_status(conn, NOW.replace(tzinfo=None))


def test_readonly_connection_cannot_write(tmp_path: Path) -> None:
    db_path = tmp_path / "ro.db"
    get_connection(db_path).close()

    ro = open_readonly(db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            ro.execute("DELETE FROM energy_states")
    finally:
        ro.close()


def test_write_atomic_replaces_and_leaves_no_temp_file(tmp_path: Path) -> None:
    target = tmp_path / "www" / "recording_status.json"

    write_atomic({"level": "ok", "note": "erste"}, target)
    write_atomic({"level": "warn", "note": "zweite, mit Umlaut ü"}, target)

    assert json.loads(target.read_text(encoding="utf-8")) == {
        "level": "warn",
        "note": "zweite, mit Umlaut ü",
    }
    assert [p.name for p in target.parent.iterdir()] == ["recording_status.json"]


def test_run_writes_error_report_for_missing_database(tmp_path: Path) -> None:
    out = tmp_path / "status.json"

    status = run(tmp_path / "gibt_es_nicht.db", out, NOW)

    written = json.loads(out.read_text(encoding="utf-8"))
    assert status["db_readable"] is False
    assert written["level"] == "error"
    assert "nicht lesbar" in written["reasons"][0]
    # sqlite must not have created the file as a side effect.
    assert not (tmp_path / "gibt_es_nicht.db").exists()


def test_run_writes_report_for_healthy_database(tmp_path: Path) -> None:
    db_path = tmp_path / "ok.db"
    connection = get_connection(db_path)
    _healthy(connection)
    connection.close()
    out = tmp_path / "status.json"

    status = run(db_path, out, NOW)

    assert status["db_readable"] is True
    assert json.loads(out.read_text(encoding="utf-8"))["level"] == "ok"


# ---------------------------------------------------------------------------
# Sync log
# ---------------------------------------------------------------------------

_GOOD_RUN = """\
2026-03-09 03:45:01,156 INFO Hole HA History 2026-03-06 02:45 bis 2026-03-09 02:45 (18 Entitaeten)...
2026-03-09 03:45:06,687 INFO Sync fertig: 144 neu, 288 bereits vorhanden
2026-03-09 03:45:08,550 INFO Miner-Sync fertig: 288 neu, 576 bereits vorhanden
Sync: +144 neue Bloecke, 288 uebersprungen
2026-03-10 03:45:01,807 INFO Hole HA History 2026-03-07 02:45 bis 2026-03-10 02:45 (18 Entitaeten)...
2026-03-10 03:45:12,684 INFO 432 Bloecke resamplet
2026-03-10 03:45:12,916 INFO Sync fertig: 143 neu, 289 bereits vorhanden
2026-03-10 03:45:14,459 INFO Device-Sync fertig: 864 neu, 1728 bereits vorhanden
2026-03-10 03:45:14,508 INFO Miner-Sync fertig: 288 neu, 576 bereits vorhanden
Sync: +143 neue Bloecke, 289 uebersprungen
"""

_CET = timezone(timedelta(hours=1))


def test_parse_sync_log_reads_the_most_recent_run() -> None:
    parsed = parse_sync_log(_GOOD_RUN, _CET)

    assert parsed == {
        "last_start": "2026-03-10T02:45:01Z",
        "last_end": "2026-03-10T02:45:14Z",
        "ok": True,
        "blocks_added": 143,
    }


def test_parse_sync_log_flags_a_run_that_crashed() -> None:
    crashed = _GOOD_RUN + (
        "2026-03-11 03:45:01,100 INFO Hole HA History 2026-03-08 02:45 bis"
        " 2026-03-11 02:45 (18 Entitaeten)...\n"
        "Traceback (most recent call last):\n"
        '  File "ha_history_sync.py", line 1, in <module>\n'
        "ConnectionError: HA nicht erreichbar\n"
    )

    parsed = parse_sync_log(crashed, _CET)

    assert parsed is not None
    assert parsed["last_start"] == "2026-03-11T02:45:01Z"
    assert parsed["ok"] is False
    assert parsed["last_end"] is None
    assert parsed["blocks_added"] is None


def test_parse_sync_log_flags_an_error_line_in_a_finished_run() -> None:
    with_error = _GOOD_RUN.replace(
        "2026-03-10 03:45:12,684 INFO 432 Bloecke resamplet",
        "2026-03-10 03:45:12,684 ERROR Quell-Entity existiert nicht in HA: sensor.x",
    )

    parsed = parse_sync_log(with_error, _CET)

    assert parsed is not None
    assert parsed["last_end"] == "2026-03-10T02:45:14Z"
    assert parsed["ok"] is False


def test_parse_sync_log_without_any_run() -> None:
    assert parse_sync_log("irgendein anderer Text\n", _CET) is None


def test_read_sync_log_missing_file_is_reported_not_raised(tmp_path: Path) -> None:
    sync = read_sync_log(tmp_path / "fehlt.log", "03:45", _CET)

    assert sync["log_readable"] is False
    assert sync["schedule"] == "03:45"
    assert sync["ok"] is None


def test_apply_sync_failed_run_makes_the_report_red(tmp_path: Path) -> None:
    status: dict[str, Any] = {"level": "ok", "reasons": []}
    apply_sync(
        status,
        {"log_readable": True, "last_start": "2026-03-10T02:45:01Z", "ok": False},
    )

    assert status["level"] == "error"
    assert "Fehler abgebrochen" in status["reasons"][0]


def test_apply_sync_unreadable_log_is_only_a_warning() -> None:
    status: dict[str, Any] = {"level": "ok", "reasons": []}
    apply_sync(status, {"log_readable": False, "last_start": None, "ok": None})

    assert status["level"] == "warn"


def test_apply_sync_never_lowers_an_existing_error() -> None:
    status: dict[str, Any] = {"level": "error", "reasons": ["vorher"]}
    apply_sync(status, {"log_readable": False, "last_start": None, "ok": None})

    assert status["level"] == "error"


def test_run_includes_sync_section_when_log_is_given(tmp_path: Path) -> None:
    db_path = tmp_path / "ok.db"
    connection = get_connection(db_path)
    _healthy(connection)
    connection.close()
    log_path = tmp_path / "ha_history_sync.log"
    log_path.write_text(_GOOD_RUN, encoding="utf-8")
    out = tmp_path / "status.json"

    status = run(db_path, out, NOW, sync_log=log_path, sync_schedule="03:45")

    written = json.loads(out.read_text(encoding="utf-8"))
    assert status["level"] == "ok"
    assert written["sync"]["schedule"] == "03:45"
    assert written["sync"]["ok"] is True
    assert written["sync"]["blocks_added"] == 143


def test_run_without_sync_log_has_empty_sync_section(tmp_path: Path) -> None:
    db_path = tmp_path / "ok.db"
    connection = get_connection(db_path)
    _healthy(connection)
    connection.close()

    status = run(db_path, tmp_path / "status.json", NOW)

    assert status["sync"] is None


def _core(
    block: str, load: float, soc: float = 50.0
) -> tuple[str, float, float, float, float]:
    return (block, load, soc, 0.0, 0.0)


def test_suspect_runs_finds_held_values_and_zero_house_load() -> None:
    from src.data.recording_status import suspect_by_day, suspect_runs

    blocks = [
        f"2026-08-07T{h:02d}:{m:02d}:00"
        for h in range(22, 24)
        for m in range(0, 60, 10)
    ]
    blocks += [
        f"2026-08-08T{h:02d}:{m:02d}:00" for h in range(0, 2) for m in range(0, 60, 10)
    ]
    rows = [_core(b, 400.0 + i) for i, b in enumerate(blocks[:4])]
    # 20 blocks with exactly the same core values across midnight: held
    rows += [_core(b, 512.0) for b in blocks[4:]]
    runs = suspect_runs(rows)
    assert runs == [{"from": blocks[4], "to": blocks[-1], "blocks": 20, "kind": "held"}]
    days = suspect_by_day(runs)
    assert sum(days.values()) == runs[0]["blocks"]
    assert set(days) == {"2026-08-07", "2026-08-08"}


def test_suspect_runs_zero_load_needs_three_blocks_and_breaks_on_gaps() -> None:
    from src.data.recording_status import suspect_runs

    rows = [
        _core("2026-05-27T05:00:00", 0.0, 18.0),
        _core("2026-05-27T05:10:00", 0.0, 19.0),
        _core("2026-05-27T05:20:00", 0.0, 20.0),
        _core("2026-05-27T05:30:00", 300.0),
        _core("2026-05-27T06:00:00", 0.0),  # single zero block: not counted
        _core("2026-05-27T06:10:00", 250.0),
        # a gap of 40 min splits two zero blocks: no run of three
        _core("2026-05-27T07:00:00", 0.0),
        _core("2026-05-27T07:40:00", 0.0),
        _core("2026-05-27T07:50:00", 280.0),
    ]
    assert suspect_runs(rows) == [
        {
            "from": "2026-05-27T05:00:00",
            "to": "2026-05-27T05:20:00",
            "blocks": 3,
            "kind": "zero",
        }
    ]
