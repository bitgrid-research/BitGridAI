"""Tests for ha_decision_sync: parsers and idempotent storage, no network."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.data import ha_decision_sync as ds
from src.data.db import get_connection

START = datetime(2026, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 11, 7, 0, 0, 0, tzinfo=timezone.utc)


def _log_row(ts: str, state: str, rule: str, values: str) -> dict[str, Any]:
    return {
        "entity_id": "sensor.miner_1_log",
        "state": state,
        "last_updated": ts,
        "attributes": {
            "entries": [
                {"time": "x", "miner": "M1", "rule": "old", "values": "old"},
                {"time": ts[11:16], "miner": "M1", "rule": rule, "values": values},
            ]
        },
    }


LOG = [
    # carried over to the window start: not an event of this window
    _log_row("2026-11-05T00:00:00+00:00", "R1 Stopp", "Off → Standby", "alt"),
    _log_row(
        "2026-11-05T14:06:42.152704+00:00",
        "Regulär",
        "Regulär",
        "Standby — regulär (SoC 81%)",
    ),
    _log_row(
        "2026-11-05T14:57:13.161108+00:00",
        "R1 Stopp",
        "R1 Stopp",
        "Standby — R1 Sicherheitsstopp: SoC 80% < Stop 81%",
    ),
    _log_row(
        "2026-11-06T09:31:00+00:00",
        "Regulär",
        "Standby → Eco",
        "Eco — regulär (SoC 92%)",
    ),
]


def test_block_id_of_floors_to_ten_minutes_utc() -> None:
    ts = datetime(2026, 11, 5, 14, 57, 13, tzinfo=timezone.utc)
    assert ds.block_id_of(ts) == "2026-11-05T14:50:00"


def test_decision_rows_parse_rule_and_mode_events() -> None:
    rows = ds.decision_rows("miner1", LOG, START)
    # carried-over row and the log sensor's mode entry are skipped
    assert len(rows) == 2
    rule = rows[1]
    assert rule[2] == "2026-11-05T14:50:00"
    assert rule[4:8] == ("rule", None, "R1 Stopp", "R1 Stopp")
    assert rule[8] == "Standby — R1 Sicherheitsstopp: SoC 80% < Stop 81%"
    assert rule[9] == 80.0


def _mode(ts: str, state: str) -> dict[str, Any]:
    return {"state": state, "last_updated": ts}


MODES = [
    _mode("2026-11-05T00:00:00+00:00", "Standby"),
    _mode("2026-11-05T09:00:00+00:00", "unavailable"),
    _mode("2026-11-05T09:01:00+00:00", "Standby"),
    _mode("2026-11-05T14:30:00+00:00", "Eco"),
    _mode("2026-11-05T15:00:00+00:00", "Standby"),
]


def test_mode_rows_ignore_dropouts_and_use_baseline() -> None:
    rows = ds.mode_rows("miner1", MODES, START, None)
    assert [(r[2], r[3]) for r in rows] == [("Standby", "Eco"), ("Eco", "Standby")]
    assert rows[0][0] == "miner1|mode|2026-11-05T14:30:00+00:00"
    # a known previous mode wins over the carried-over row
    rows = ds.mode_rows("miner1", MODES, START, "Eco")
    assert (rows[0][2], rows[0][3]) == ("Eco", "Standby")


def test_decision_rows_skip_empty_log_and_repeated_entry() -> None:
    reset = {
        "state": "Regulär",
        "last_updated": "2026-11-05T10:00:00+00:00",
        "attributes": {"entries": []},
    }
    repeat = dict(LOG[1], last_updated="2026-11-05T14:10:00+00:00")
    rows = ds.decision_rows("miner1", [reset, LOG[1], repeat], START)
    assert len(rows) == 1


def _diag(
    ts: str, code: str, actual: str, target: str, soc: str, why: str = "< Stop 50%"
) -> dict[str, Any]:
    return {
        "state": code,
        "last_updated": ts,
        "attributes": {
            "summary": f"Ist={actual} | Ziel={target} | SoC {soc}% {why}",
            "actual_mode": actual,
            "night_block": False,
        },
    }


def test_diagnose_rows_only_on_verdict_change() -> None:
    hist = [
        _diag("2026-11-05T00:00:00+00:00", "ok", "Standby", "Standby", "1"),
        _diag("2026-11-05T08:00:00+00:00", "ok", "Standby", "Standby", "5"),
        # same verdict, other kind of reason: a new row
        _diag("2026-11-05T10:00:00+00:00", "ok", "Standby", "Standby", "60", "wartet"),
        _diag("2026-11-05T12:35:36+00:00", "anomaly", "Super", "Standard", "90"),
        {"state": "unavailable", "last_updated": "2026-11-05T12:36:00+00:00"},
        _diag("2026-11-05T12:37:14+00:00", "auto_off", "Super", "Super", "90"),
    ]
    rows = ds.diagnose_rows("miner1", hist, START)
    assert [(r[3], r[4], r[5]) for r in rows] == [
        ("ok", "Standby", "Standby"),
        ("ok", "Standby", "Standby"),
        ("anomaly", "Super", "Standard"),
        ("auto_off", "Super", "Super"),
    ]
    assert rows[2][1] == "2026-11-05T12:30:00"
    assert rows[0][7] == 0
    assert ds.reason_kind(rows[1][6]) == "SoC N% wartet"


def test_setting_changes_store_only_changes() -> None:
    hist = [
        {
            "state": "Nur Eco",
            "last_updated": "2026-11-05T00:00:00+00:00",
            "attributes": {"eco_ab_pct": 85.5, "hausreserve_pct": 75.5},
        },
        {
            "state": "Nur Eco",
            "last_updated": "2026-11-06T00:00:10+00:00",
            "attributes": {"eco_ab_pct": 86.0, "hausreserve_pct": 75.5},
        },
    ]
    known: dict[str, str] = {"state": "Nur Eco"}
    rows = ds.setting_changes(
        ds.SEASON_ENTITY, hist, ("state", "eco_ab_pct", "hausreserve_pct"), known, START
    )
    assert [(r[2], r[3]) for r in rows] == [
        ("eco_ab_pct", "85.5"),
        ("hausreserve_pct", "75.5"),
        ("eco_ab_pct", "86.0"),
    ]
    assert known["eco_ab_pct"] == "86.0"


def test_setting_changes_skip_carried_drops_stale_start_row() -> None:
    hist = [
        {"state": "70.0", "last_updated": "2026-11-05T00:00:00+00:00"},
        {"state": "81.0", "last_updated": "2026-11-05T09:00:00+00:00"},
    ]
    rows = ds.setting_changes("input_number.x", hist, ("state",), {}, START, True)
    assert [(r[0][:13], r[3]) for r in rows] == [("2026-11-05T09", "81.0")]


def test_sync_window_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hist = {
        "sensor.miner_1_log": LOG,
        "sensor.miner1_workmode_status": MODES,
        "sensor.miner_1_auto_diagnose": [
            _diag("2026-11-05T00:00:00+00:00", "ok", "Standby", "Standby", "1"),
            _diag("2026-11-05T12:35:36+00:00", "anomaly", "Super", "Standard", "90"),
        ],
        ds.SEASON_ENTITY: [
            {
                "state": "Nur Eco",
                "last_updated": "2026-11-05T00:00:00+00:00",
                "attributes": {"eco_ab_pct": 85.5},
            }
        ],
    }
    monkeypatch.setattr(ds, "fetch_full_history", lambda *a, **k: hist)
    conn = get_connection(tmp_path / "t.db")
    try:
        first = ds.sync_window(START, END, conn, "http://x", "t")
        second = ds.sync_window(START, END, conn, "http://x", "t")
        assert first == {"decisions": 4, "diagnose": 2, "settings": 2}
        assert second == {"decisions": 0, "diagnose": 0, "settings": 0}
        # the stop at 15:00 carries the rule the watchdog wrote at 14:57
        stop = conn.execute(
            "SELECT from_state, to_state, rule_active, soc_pct FROM ha_decision_log"
            " WHERE kind = 'mode' ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        assert stop == ("Eco", "Standby", "R1 Stopp", 80.0)
    finally:
        conn.close()


def test_sync_window_overlapping_rerun_adds_no_setting_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def season(ts: str, eco: float) -> dict[str, Any]:
        return {
            "state": "Nur Eco",
            "last_updated": ts,
            "attributes": {"eco_ab_pct": eco},
        }

    full = {
        ds.SEASON_ENTITY: [
            season("2026-11-05T00:00:00+00:00", 85.5),
            season("2026-11-06T12:00:00+00:00", 86.0),
        ]
    }
    # nightly rerun starting one day later: HA carries the old value over
    later = datetime(2026, 11, 6, 0, 0, 0, tzinfo=timezone.utc)
    rerun = {
        ds.SEASON_ENTITY: [
            season("2026-11-06T00:00:00+00:00", 85.5),
            season("2026-11-06T12:00:00+00:00", 86.0),
        ]
    }
    conn = get_connection(tmp_path / "t.db")
    try:
        monkeypatch.setattr(ds, "fetch_full_history", lambda *a, **k: full)
        assert ds.sync_window(START, END, conn, "http://x", "t")["settings"] == 3
        monkeypatch.setattr(ds, "fetch_full_history", lambda *a, **k: rerun)
        assert ds.sync_window(later, END, conn, "http://x", "t")["settings"] == 0
    finally:
        conn.close()


def test_snapshot_settings_only_when_value_differs(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        states = {"input_number.mvp_soc_stop_pct": "81.0"}
        assert ds.snapshot_settings(conn, states, START) == 1
        assert ds.snapshot_settings(conn, states, END) == 0
        states["input_number.mvp_soc_stop_pct"] = "75.0"
        assert ds.snapshot_settings(conn, states, END) == 1
        rows = conn.execute(
            "SELECT value, source FROM settings_history ORDER BY timestamp"
        ).fetchall()
        assert rows == [("81.0", "snapshot"), ("75.0", "snapshot")]
    finally:
        conn.close()
