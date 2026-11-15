"""Tests for the research cards (night balance, forecast vs. actual)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.data import research_cards as rc


def _db(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path) if path else ":memory:")
    conn.execute(
        "CREATE TABLE energy_states (block_id TEXT PRIMARY KEY, pv_power_w REAL,"
        " battery_soc_pct REAL, house_load_w REAL, miner_power_w REAL,"
        " grid_import_w REAL, pv_forecast_kw REAL)"
    )
    return conn


def _fill(
    conn: sqlite3.Connection,
    *,
    start: str,
    days: int,
    stop: float = 75,
    morning: float = 2,
    forecast_factor: float | None = 1.0,
    grid_w: float = 0.0,
) -> None:
    """Sun 08:00-15:50 UTC at 1200 W, miners 10-14 h, SoC falls to ``morning``.

    ``pv_forecast_kw`` holds the power of the current block, scaled by
    ``forecast_factor`` (None: no forecast at all).
    """
    first = datetime.fromisoformat(start)
    for d in range(days):
        for i in range(144):
            ts = first + timedelta(days=d, minutes=10 * i)
            h = ts.hour + ts.minute / 60
            pv = 1200.0 if 8 <= h < 16 else 0.0
            # stored forecast describes the current block (see FORECAST_LEAD_BLOCKS)
            pv_ahead = pv / 1000
            miner = 1500.0 if 10 <= h < 14 else 0.0
            if h < 8:
                soc = morning + (stop - morning) * (8 - h) / 18
            elif h < 10:
                soc = morning
            elif h < 14:
                soc = stop
            else:
                soc = stop - (stop - morning) * (h - 14) / 18
            fc = None if forecast_factor is None else pv_ahead * forecast_factor
            conn.execute(
                "INSERT INTO energy_states VALUES (?,?,?,?,?,?,?)",
                (
                    ts.strftime("%Y-%m-%dT%H:%M:%S"),
                    pv,
                    soc,
                    600.0 + miner,
                    miner,
                    grid_w if (h >= 16 or h < 8) else 0.0,
                    fc,
                ),
            )


NOW = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)


def test_perfect_forecast_has_no_error() -> None:
    conn = _db()
    _fill(conn, start="2026-10-01", days=20)
    days = rc.forecast_days(conn, NOW)
    assert days, "expected complete days"
    assert all(d["error_pct"] == 0.0 for d in days)
    assert days[-1]["day"] == "2026-10-19"  # running day excluded
    assert len(days) <= rc.CARD_FORECAST_DAYS


def test_forecast_overestimate_shows_as_positive_bias() -> None:
    conn = _db()
    _fill(conn, start="2026-10-01", days=20, forecast_factor=1.5)
    summary = rc.forecast_summary(rc.forecast_days(conn, NOW))
    assert summary["bias_pct"] == pytest.approx(50.0, abs=0.5)
    assert summary["mae_pct"] == pytest.approx(50.0, abs=0.5)


def test_days_without_forecast_are_skipped() -> None:
    conn = _db()
    _fill(conn, start="2026-10-01", days=20, forecast_factor=None)
    assert rc.forecast_days(conn, NOW) == []
    assert rc.forecast_summary([]) == {
        "days_used": 0,
        "bias_pct": None,
        "mae_pct": None,
    }


def test_build_cards_nights_and_verdict() -> None:
    conn = _db()
    _fill(conn, start="2026-10-01", days=19, grid_w=300.0)
    cards = rc.build_cards(
        conn,
        NOW,
        {
            "baseload_w": 535.0,
            "capacity_kwh": 12.5,
            "gap_h": 0.0,
            "efficiency": 1.0,
            "floor_pct": 15.0,
        },
    )
    months = {m["month"]: m for m in cards["nights"]["months"]}
    oct_ = months[10]
    assert oct_["verdict"] == "zu_niedrig"
    assert oct_["at_stop"] == oct_["mined_nights"]
    # October ran before ADR 033: today's rule is not judged on it, the
    # measured stop is shown instead.
    assert oct_["before_formula_v2"] is True and oct_["rule_holds"] is None
    assert oct_["stop_measured"] == oct_["stop_target"]
    assert all(r["before_formula_v2"] for r in cards["nights"]["recent"])
    assert oct_["grid_kwh_after_mining"] == oct_["grid_kwh"] > 0
    recent = cards["nights"]["recent"]
    assert len(recent) == rc.CARD_NIGHTS
    assert recent[-1]["mined"] and recent[-1]["stop_target"] == 75
    assert recent[-1]["morning_soc"] == pytest.approx(2.0)
    json.dumps(cards)  # serialisable for the card


def test_build_cards_on_empty_db() -> None:
    cards = rc.build_cards(sqlite3.connect(":memory:"), NOW)
    assert cards["nights"]["months"] == [] and cards["nights"]["recent"] == []
    assert cards["forecast"]["days"] == []


def test_main_writes_json_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "bitgrid.db"
    conn = _db(db)
    _fill(conn, start="2026-10-01", days=8)
    conn.commit()
    conn.close()
    monkeypatch.chdir(tmp_path)  # no .env here: defaults, no HA call
    monkeypatch.delenv("UMBREL_HOST", raising=False)
    out = tmp_path / "www" / "research_cards.json"
    out.parent.mkdir()
    assert rc.main(["--db", str(db), "--out", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["settings"]["source"] == "default"
    assert data["nights"]["recent"]


def test_forecast_by_hour_shows_where_it_is_off() -> None:
    conn = _db()
    _fill(conn, start="2026-10-01", days=20, forecast_factor=2.0)
    days = rc.forecast_days(conn, NOW)
    hours = rc.forecast_by_hour(conn, days)
    assert hours, "expected an hourly profile"
    sunny = [h for h in hours if h["actual_kw"] > 0 and h["forecast_kw"] > 0]
    assert sunny and all(
        h["forecast_kw"] == pytest.approx(2 * h["actual_kw"]) for h in sunny
    )
    assert rc.forecast_by_hour(conn, []) == []


def test_settings_from_states_converts_and_falls_back() -> None:
    st = rc.settings_from_states(
        {
            "input_number.mvp_battery_efficiency_pct": {"state": "85"},
            "input_number.mvp_night_baseload_w": {"state": "unavailable"},
        }
    )
    assert st["efficiency"] == pytest.approx(0.85)
    assert st["baseload_w"] == rc.BASELOAD_DEFAULT_W
    assert st["floor_pct"] == rc.RESERVE_FLOOR_PCT == 5.0


def _miner_kpi(
    conn: sqlite3.Connection, rows: list[tuple[str, str, float, float, float]]
) -> None:
    conn.execute(
        "CREATE TABLE daily_miner_kpi (day TEXT, miner TEXT, h_eco REAL,"
        " h_standard REAL, h_super REAL, w_per_th REAL)"
    )
    conn.executemany(
        "INSERT INTO daily_miner_kpi VALUES (?, 'miner1', ?, ?, 0, ?)", rows
    )


def test_efficiency_ignores_mixed_mode_days() -> None:
    # A Standard day raises W/TH without any wear; it must not count.
    conn = _db()
    rows = [(f"2026-08-{d:02d}", 6.0, 0.0, 16.0) for d in range(1, 5)]
    rows += [(f"2026-10-{d:02d}", 6.0, 0.0, 16.2) for d in range(1, 5)]
    rows += [("2026-10-20", 3.0, 4.0, 18.0)]
    _miner_kpi(conn, [(r[0], r[1], r[2], r[3]) for r in rows])
    m = rc.efficiency_trend(conn)["miners"][0]
    assert [x["days"] for x in m["months"]] == [4, 4]
    assert m["change_pct"] == pytest.approx(1.2, abs=0.05)
    assert m["verdict"] == "stabil"


def test_efficiency_flags_drift_and_needs_enough_days() -> None:
    conn = _db()
    rows = [(f"2026-08-{d:02d}", 6.0, 0.0, 16.0) for d in range(1, 5)]
    rows += [(f"2026-10-{d:02d}", 6.0, 0.0, 17.2) for d in range(1, 5)]
    rows += [("2026-11-01", 6.0, 0.0, 20.0)]  # one day only, no verdict weight
    _miner_kpi(conn, rows)
    m = rc.efficiency_trend(conn)["miners"][0]
    assert m["verdict"] == "schlechter" and m["change_pct"] == pytest.approx(7.5)


def test_efficiency_skips_days_with_unmeasured_blocks() -> None:
    conn = _db()
    conn.execute("ALTER TABLE energy_states ADD COLUMN quality TEXT")
    conn.executemany(
        "INSERT INTO energy_states (block_id, quality) VALUES (?, 'warn')",
        [(f"2026-10-01T0{h}:00:00",) for h in range(rc.UNMEASURED_MIN_BLOCKS)],
    )
    rows = [(f"2026-10-{d:02d}", 6.0, 0.0, 16.0) for d in range(1, 5)]
    _miner_kpi(conn, rows)
    m = rc.efficiency_trend(conn)["miners"][0]
    assert [x["days"] for x in m["months"]] == [3]


def test_efficiency_without_table_is_empty() -> None:
    assert rc.efficiency_trend(sqlite3.connect(":memory:"))["miners"] == []


def _peak_db(day: str, soc_pv: list[tuple[float, float]]) -> sqlite3.Connection:
    conn = _db()
    for i in range(144):
        soc, pv = soc_pv[i % len(soc_pv)]
        conn.execute(
            "INSERT INTO energy_states (block_id, battery_soc_pct, pv_power_w)"
            " VALUES (?, ?, ?)",
            (f"{day}T{i // 6:02d}:{i % 6 * 10:02d}:00", soc, pv),
        )
    return conn


def test_peak_days_names_what_was_missing() -> None:
    table = {r["month"]: r for r in rc.season_table(570, 12.5)}
    now = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
    # November: Eco start capped at 100 %. Battery peaks at 80 %, sun is enough.
    conn = _peak_db("2026-11-12", [(80.0, 7000.0)])
    day = rc.peak_days(conn, now, table, 6000)[0]
    assert day["eco_start"] == 100 and day["missing"] == "akku"
    # The sun is no start condition (R7): a full battery without sun counts.
    conn = _peak_db("2026-11-12", [(100.0, 0.0), (50.0, 0.0)])
    day = rc.peak_days(conn, now, table, 6000)[0]
    assert day["missing"] is None and day["start_blocks"] == 72
    conn = _peak_db("2026-11-12", [(100.0, 7000.0)])
    day = rc.peak_days(conn, now, table, 6000)[0]
    assert day["missing"] is None and day["start_blocks"] == 144


def test_peak_days_skips_today_and_incomplete_days() -> None:
    table = {r["month"]: r for r in rc.season_table(570, 12.5)}
    now = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
    conn = _peak_db("2026-11-13", [(80.0, 7000.0)])
    assert rc.peak_days(conn, now, table, 6000) == []


def test_heizstab_vs_battery_counts_only_while_not_full() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE energy_states (block_id TEXT, heizstab_power_w REAL,"
        " battery_soc_pct REAL)"
    )
    for i in range(144):
        block = f"2026-11-12T{i // 6:02d}:{i % 6 * 10:02d}:00"
        soc = 0.0 if i < 72 else 100.0  # empty morning, full afternoon
        conn.execute("INSERT INTO energy_states VALUES (?, 600, ?)", (block, soc))
    now = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
    h = rc.heizstab_vs_battery(conn, now)
    assert h["days"] == 1 and h["empty_mornings"] == 1
    assert h["heizstab_kwh"] == pytest.approx(14.4)
    assert h["heizstab_kwh_not_full"] == pytest.approx(7.2)


def test_forecast_months_shows_season_and_skips_days_without_forecast(
    tmp_path: Path,
) -> None:
    from datetime import datetime as _dt
    from datetime import timedelta as _td

    from src.data import research_cards as rc
    from src.data.db import get_connection

    conn = get_connection(tmp_path / "fc.db")
    try:

        def day(
            d: str, pv_w: float, fc_kw: float | None, night_fc: float = 0.0
        ) -> None:
            # Sun and forecast 06-18 UTC (72 blocks), night forecast night_fc.
            t0 = _dt.fromisoformat(d + "T00:00:00")
            for i in range(144):
                b = (t0 + _td(minutes=10 * i)).strftime("%Y-%m-%dT%H:%M:%S")
                sun = 36 <= i < 108
                conn.execute(
                    "INSERT INTO energy_states (block_id, window_start, window_end,"
                    " pv_power_w, house_load_w, grid_import_w, battery_soc_pct,"
                    " miner_temp_c, miner_heartbeat_age_sec, surplus_kw, quality,"
                    " pv_forecast_kw) VALUES (?, ?, ?, ?, 0, 0, 50, 0, 0, 0, 'ok', ?)",
                    (
                        b,
                        b,
                        b,
                        pv_w if sun else 0.0,
                        None if fc_kw is None else (fc_kw if sun else night_fc),
                    ),
                )

        day("2026-07-10", 1000.0, 0.9)  # 12 kWh measured, 10.8 forecast
        day("2026-11-10", 100.0, 0.175)  # 1.2 kWh measured, 2.1 forecast
        day("2026-11-11", 100.0, None)  # no forecast: not counted
        # frozen forecast, 6.87 kW day and night (27.-31.05.2026): not counted
        day("2026-11-12", 100.0, 6.87, night_fc=6.87)
        conn.commit()
        assert rc.frozen_forecast_days(conn) == {"2026-11-12"}
        months = {m["month"]: m for m in rc.forecast_months(conn)}
    finally:
        conn.close()
    assert months["2026-07"]["bias_pct"] == -10.0
    assert months["2026-11"]["bias_pct"] == 75.0
    assert (months["2026-11"]["days"], months["2026-11"]["days_total"]) == (1, 3)


def test_unmeasured_days_need_one_hour_of_non_ok_blocks(tmp_path: Path) -> None:
    from src.data import research_cards as rc
    from src.data.db import get_connection

    conn = get_connection(tmp_path / "u.db")
    try:
        for day, warn in (("2026-08-07", 6), ("2026-08-09", 5)):
            for i in range(warn):
                b = f"{day}T10:{i}0:00"
                conn.execute(
                    "INSERT INTO energy_states (block_id, window_start, window_end,"
                    " pv_power_w, house_load_w, grid_import_w, battery_soc_pct,"
                    " miner_temp_c, miner_heartbeat_age_sec, surplus_kw, quality)"
                    " VALUES (?, ?, ?, 0, 0, 0, 50, 0, 0, 0, 'warn')",
                    (b, b, b),
                )
        conn.commit()
        assert rc.unmeasured_days(conn) == {"2026-08-07"}
    finally:
        conn.close()
