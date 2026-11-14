"""Tests for automation_cards: surplus reasons, switching, safety (no network)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.data import automation_cards as ac
from src.data.db import get_connection

NOW = datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc)


def _energy(conn, block: str, export_w: float, miner_w: float, quality: str = "ok"):
    conn.execute(
        "INSERT INTO energy_states (block_id, window_start, window_end, pv_power_w,"
        " house_load_w, grid_import_w, battery_soc_pct, miner_temp_c,"
        " miner_heartbeat_age_sec, surplus_kw, quality, grid_export_w, miner_power_w)"
        " VALUES (?, ?, ?, 5000, 500, 0, 90, 0, 0, 0, ?, ?, ?)",
        (block, block, block, quality, export_w, miner_w),
    )


def test_count_switches_separates_start_stop_from_level() -> None:
    events = [
        ("2026-09-05T11:38:29+00:00", "miner1", "Standby", "Idle"),  # no switch
        ("2026-09-05T11:38:31+00:00", "miner1", "Idle", "Eco"),  # start
        ("2026-09-05T12:17:38+00:00", "miner1", "Eco", "Standard"),  # level
        ("2026-09-05T17:29:00+00:00", "miner1", "Standard", "Standby"),  # stop
        ("2026-09-05T23:00:00+00:00", "miner1", "Standby", "Off"),  # no switch
        ("2026-09-05T11:00:00+00:00", "miner2", None, "Eco"),  # baseline
    ]
    assert ac.count_switches(events) == {
        ("2026-09-05", "miner1"): {"start_stop": 2, "level": 1, "dropout": 0}
    }


def test_manual_hours_lasts_until_next_row_of_same_miner() -> None:
    diag = [
        ("2026-09-01T10:00:00+00:00", "miner1", "auto_off"),
        ("2026-09-01T11:00:00+00:00", "miner2", "ok"),
        ("2026-09-01T13:30:00+00:00", "miner1", "ok"),
        ("2026-09-09T22:00:00+00:00", "miner2", "auto_off"),  # until NOW
    ]
    assert ac.manual_hours(diag, NOW) == {"2026-09": 5.5}


def test_surplus_idle_books_reason_and_skips_bad_quality(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        _energy(conn, "2026-06-01T10:00:00", 3000, 0)  # before any diagnosis
        _energy(conn, "2026-09-05T10:00:00", 2400, 0)
        _energy(conn, "2026-09-05T10:10:00", 1800, 50)
        _energy(conn, "2026-09-05T10:20:00", 6000, 0, quality="error")
        _energy(conn, "2026-09-05T10:30:00", 2000, 800)  # miners running
        stop = "Ist=Standby | Ziel=Standby | SoC 49.0% < Stop 50.0%, Miner aus"
        for ts, block, code, summary in [
            ("2026-09-05T08:00:00+00:00", "2026-09-05T08:00:00", "ok", stop),
            ("2026-09-05T10:12:00+00:00", "2026-09-05T10:10:00", "cooldown", None),
        ]:
            conn.execute(
                "INSERT INTO ha_diagnose_log (timestamp, block_id, miner, code,"
                " summary) VALUES (?, ?, 'miner1', ?, ?)",
                (ts, block, code, summary),
            )
        conn.commit()
        out = ac.surplus_idle(conn)
        assert out["hours"] == 0.5
        assert out["export_kwh"] == 1.2
        june, sept = out["months"]
        assert june["reasons"] == {"unbekannt": 0.2}
        assert sept["export_kwh"] == 0.7
        assert sept["reasons"] == {
            "Akku unter Stopp-Schwelle": 0.2,
            "Wartezeit nach Schaltung": 0.2,
        }
        assert out["top_days"][0]["day"] == "2026-09-05"
    finally:
        conn.close()


def test_reason_label_reads_threshold_from_summary() -> None:
    assert ac.reason_label("ok", "x | SoC 62.0% < Eco-Start 70.0%, Miner aus") == (
        "Akku unter Eco-Start"
    )
    assert ac.reason_label("ok", None) == "kein Startgrund laut Regeln"
    assert ac.reason_label("auto_off", "egal") == "Handbetrieb"
    assert ac.reason_label("neu", None) == "neu"


def test_switching_judges_day_by_busiest_miner(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        ev = [
            ("2026-09-05T08:00:00+00:00", "miner1", "Standby", "Eco"),
            ("2026-09-05T09:00:00+00:00", "miner1", "Eco", "Standby"),
            ("2026-09-05T10:00:00+00:00", "miner1", "Standby", "Eco"),
            ("2026-09-05T11:00:00+00:00", "miner1", "Eco", "Standby"),
            ("2026-09-05T08:00:00+00:00", "miner2", "Standby", "Eco"),
            ("2026-09-05T18:00:00+00:00", "miner2", "Eco", "Standby"),
            ("2026-09-06T08:00:00+00:00", "miner1", "Standby", "Eco"),
            ("2026-09-06T18:00:00+00:00", "miner1", "Eco", "Standby"),
            ("2026-09-07T03:00:00+00:00", "miner1", "Standby", "Off"),
        ]
        for i, (ts, miner, f, t) in enumerate(ev):
            conn.execute(
                "INSERT INTO ha_decision_log (id, timestamp, block_id, miner, kind,"
                " from_state, to_state) VALUES (?, ?, ?, ?, 'mode', ?, ?)",
                (str(i), ts, ts[:19], miner, f, t),
            )
        conn.commit()
        out = ac.switching(conn, NOW)
        assert out["since"] == "2026-09-05"
        (month,) = out["months"]
        assert month["mining_days"] == 2  # 07.09. had no start/stop
        assert month["days_over"] == 1
        assert month["max_start_stop"] == 4
        assert month["mean_start_stop"] == 3.0
        assert [d["start_stop"] for d in out["recent"]] == [4, 2]
    finally:
        conn.close()


def test_build_on_empty_db_has_all_sections(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        out = ac.build(conn, NOW)
        assert out["surplus"]["months"] == []
        assert out["switching"]["since"] is None
        assert out["safety"]["errors_total"] == 0
        assert out["safety"]["last_error"] is None
    finally:
        conn.close()


def test_count_switches_short_off_between_running_modes_is_a_dropout() -> None:
    events = [
        ("2026-09-06T10:00:00+00:00", "miner1", "Standby", "Eco"),  # start
        ("2026-09-06T11:00:00+00:00", "miner1", "Eco", "Off"),  # dropout ...
        ("2026-09-06T11:00:30+00:00", "miner1", "Off", "Standby"),  # (off->off)
        ("2026-09-06T11:08:00+00:00", "miner1", "Standby", "Eco"),  # ... back
        ("2026-09-06T14:00:00+00:00", "miner1", "Eco", "Standby"),  # real stop
        ("2026-09-06T14:30:00+00:00", "miner1", "Standby", "Eco"),  # real start
        ("2026-09-06T18:00:00+00:00", "miner1", "Eco", "Standby"),  # stop
    ]
    assert ac.count_switches(events) == {
        ("2026-09-06", "miner1"): {"start_stop": 4, "level": 0, "dropout": 1}
    }


def test_threshold_changes_lists_restart_reset_newest_first(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        rows = [
            ("2026-11-14T01:44:33+00:00", "95.0", "snapshot"),
            ("2026-11-14T02:03:49+00:00", "60.0", "history"),
            ("2026-11-14T02:05:37+00:00", "95.0", "history"),
        ]
        for ts, value, source in rows:
            conn.execute(
                "INSERT INTO settings_history VALUES (?, ?, 'state', ?, ?)",
                (ts, "input_number.mvp_soc_stop_pct", value, source),
            )
        conn.execute(
            "INSERT INTO settings_history VALUES (?, ?, 'state', '570', 'history')",
            ("2026-11-14T02:03:49+00:00", "input_number.mvp_night_baseload_w"),
        )
        conn.commit()
        out = ac.threshold_changes(conn)
    finally:
        conn.close()
    assert [(c["label"], c["old"], c["new"]) for c in out] == [
        ("Stopp", "60.0", "95.0"),
        ("Stopp", "95.0", "60.0"),
    ]
