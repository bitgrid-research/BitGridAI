"""Tests for the deterministic seasonal check of the KI hamster."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from src.explain import bithamster_ki as ki
from src.explain.bithamster_season import (
    night_check,
    season_findings,
    season_lines,
    season_table,
)

# Formula before ADR 033 (13.11.2026): no evening gap, no losses, 15 % floor.
OLD = {
    "baseload_w": 535.0,
    "capacity_kwh": 12.5,
    "gap_h": 0.0,
    "efficiency": 1.0,
    "floor_pct": 15.0,
}


def _old_table() -> list[dict]:  # type: ignore[type-arg]
    return season_table(535, 12.5, 0.0, 1.0, 15.0)


def _old_check(conn: sqlite3.Connection) -> dict:  # type: ignore[type-arg]
    return night_check(conn, 12.5, efficiency=1.0, floor_pct=15.0)


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE energy_states (block_id TEXT PRIMARY KEY, pv_power_w REAL,"
        " battery_soc_pct REAL, house_load_w REAL, miner_power_w REAL,"
        " grid_import_w REAL, grid_export_w REAL, battery_power_w REAL,"
        " heizstab_power_w REAL, pv_forecast_kw REAL, energy_price_ct_kwh REAL,"
        " outdoor_temp_c REAL, cloud_coverage_pct REAL, sun_elevation_deg REAL,"
        " heizung_energy_kwh_today REAL)"
    )
    return conn


def _fill(
    conn: sqlite3.Connection,
    *,
    days: int,
    stop: float,
    morning: float,
    mine: bool = True,
    start: str = "2026-10-01",
) -> None:
    """Synthetic October days: sun 08:00-15:50 UTC, miners until 14:00.

    The SoC sits at ``stop`` when the miners stop and falls linearly to
    ``morning`` at the first light of the next day.
    """
    first = datetime.fromisoformat(start)
    for d in range(days):
        day = first + timedelta(days=d)
        for i in range(144):
            ts = day + timedelta(minutes=10 * i)
            hour = ts.hour + ts.minute / 60
            pv = 300.0 if 8 <= hour < 16 else 0.0
            miner = 1500.0 if mine and 10 <= hour < 14 else 0.0
            if hour < 8:  # end of the previous night
                soc = morning + (stop - morning) * (8 - hour) / 18
            elif hour < 10:  # first light, before the miners start
                soc = morning
            elif hour < 14:
                soc = stop
            else:  # 14:00 -> next morning 08:00 = 18 h
                soc = stop - (stop - morning) * (hour - 14) / 18
            conn.execute(
                "INSERT INTO energy_states (block_id, pv_power_w, battery_soc_pct,"
                " house_load_w, miner_power_w, grid_import_w) VALUES (?,?,?,?,?,?)",
                (
                    ts.strftime("%Y-%m-%dT%H:%M:%S"),
                    pv,
                    soc,
                    600.0 + miner,
                    miner,
                    0.0,
                ),
            )


# ---------------------------------------------------------------------------
# season_table: same numbers as the "Saisonale Schwellwerte" card
# ---------------------------------------------------------------------------


def test_season_table_matches_dashboard_values() -> None:
    rows = {r["month"]: r for r in _old_table()}
    nov = rows[11]
    assert nov["stop"] == 81 and nov["eco"] == 91
    assert nov["std"] is None and nov["std_off"] is None and nov["super"] is None
    assert nov["tier"] == "Nur Eco"
    jun = rows[6]
    assert (jun["stop"], jun["std"], jun["super"]) == (49, 74, 89)
    assert jun["tier"] == "Voll (Eco/Standard/Super)"
    assert rows[9]["tier"] == "Eco + Standard" and rows[9]["super"] is None


def test_adr029_formula_with_measured_terms() -> None:
    rows = {r["month"]: r for r in season_table(570, 12.5, 0.75, 0.80, 5.0)}
    # 570 W x (8 h + 0,75 h) / (12,5 kWh x 0,8) + 5 % = 54,9 % -> Voll in June
    assert rows[6]["stop"] == 55 and rows[6]["tier"] == "Voll (Eco/Standard/Super)"
    assert rows[8]["stop"] == 69 and rows[8]["tier"] == "Eco + Standard"
    assert rows[9]["tier"] == "Nur Eco" and rows[11]["stop"] == 95
    assert rows[6]["night_kwh"] == pytest.approx(570 * 8.75 / 1000)


def test_season_table_caps_reserve_at_95() -> None:
    rows = season_table(5000, 12.5)
    assert all(r["stop"] == 95 for r in rows)
    assert all(r["tier"] == "Nur Eco" for r in rows)


# ---------------------------------------------------------------------------
# night_check + verdict
# ---------------------------------------------------------------------------


def test_night_check_empty_battery_after_mining_is_too_low() -> None:
    conn = _db()
    _fill(conn, days=7, stop=75, morning=2)
    checks = _old_check(conn)
    oct_ = checks[10]
    assert oct_["nights"] == 6
    assert oct_["mined_nights"] == 6
    assert oct_["morning_after_mining"] == pytest.approx(2.0, abs=0.5)
    text = "\n".join(season_lines(_old_table(), checks, OLD, 10))
    # Nights before ADR 033: no rule check against today's table value
    # (that compared old nights with the new threshold), only the measured
    # shutdown SoC.
    assert (
        "REGEL HÄLT" not in text
        and "alte Formel, abgeschaltet im Mittel bei 75 %" in text
    )
    assert "HAUSRESERVE ZU NIEDRIG" in text
    # Nights after ADR 033 are checked against the threshold again.
    oct_after = dict(oct_, last_day="2026-11-20")
    text = "\n".join(season_lines(_old_table(), {10: oct_after}, OLD, 10))
    assert "REGEL HÄLT" in text


def test_night_check_full_battery_in_morning_is_too_high() -> None:
    conn = _db()
    _fill(conn, days=7, stop=75, morning=40)
    text = "\n".join(season_lines(_old_table(), _old_check(conn), OLD, 10))
    assert "HAUSRESERVE ZU HOCH" in text


def test_nights_without_mining_are_not_blamed_on_miners() -> None:
    conn = _db()
    _fill(conn, days=7, stop=40, morning=1, mine=False)
    checks = _old_check(conn)
    assert checks[10]["mined_nights"] == 0
    text = "\n".join(season_lines(_old_table(), checks, OLD, 10))
    assert "NICHT an den Minern" in text
    assert "HAUSRESERVE" not in text  # no verdict without mining days


def test_night_check_skips_data_before_formula_and_incomplete_days() -> None:
    conn = _db()
    _fill(conn, days=4, stop=75, morning=2, start="2026-08-01")
    assert _old_check(conn) == {}
    conn.execute("DELETE FROM energy_states")
    _fill(conn, days=3, stop=75, morning=2)
    conn.execute("DELETE FROM energy_states WHERE block_id LIKE '2026-10-02T1%'")
    assert _old_check(conn) == {}


def test_too_few_nights_gives_no_measured_claim() -> None:
    conn = _db()
    _fill(conn, days=3, stop=75, morning=2)
    text = "\n".join(season_lines(_old_table(), _old_check(conn), OLD, 10))
    assert "zu wenige vollständige Nächte" in text
    assert "HAUSRESERVE" not in text


def test_night_check_without_table_is_empty() -> None:
    assert night_check(sqlite3.connect(":memory:"), 12.5) == {}


# ---------------------------------------------------------------------------
# Integration in the ask prompt
# ---------------------------------------------------------------------------


def test_inventory_flags_empty_columns_and_tables() -> None:
    conn = _db()
    _fill(conn, days=2, stop=75, morning=2, start="2026-11-10")
    now = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
    text = "\n".join(ki.inventory_lines(ki.data_inventory(conn, now)))
    assert "Solarleistung 100 %" in text
    assert "LEER oder lückenhaft" in text and "Außentemperatur 0 %" in text
    assert "Poolertrag je Tag: LEER" in text


def test_overview_prompt_has_tabs_season_and_inventory() -> None:
    live = {
        "live": {"soc_pct": 30.0, "miner1_mode": "Standby", "miner2_mode": "Standby"},
        "thresholds": [],
        "night_block": {"enabled": False, "start": "", "end": ""},
        "diagnose": [],
    }
    research = {"window_days": 14, "days_used": 0}
    prompt = ki.build_ask_prompt(
        "gesamtcheck",
        live=live,
        research=research,
        now=datetime(2026, 11, 13, 12, tzinfo=timezone.utc),
        states={},
        recording=None,
        tabs={"Einstellungen": ["Saisonale Schwellwerte"]},
        tab=None,
        question=None,
        season=["SAISONALE AUTOMATIK x"],
        inventory=["DATENBESTAND y"],
    )
    assert "ALLE TABS UND IHRE KARTEN" in prompt
    assert "- Einstellungen: Saisonale Schwellwerte" in prompt
    assert "SAISONALE AUTOMATIK x" in prompt and "DATENBESTAND y" in prompt
    assert "0 bis 6 kurze Punkte" in prompt


def test_overview_answers_keep_six_points() -> None:
    raw = '{"headline": "h", "text": "t", "punkte": ["1","2","3","4","5","6","7"]}'
    assert len(ki.parse_ask_answer(raw, 6)["punkte"]) == 6
    assert len(ki.parse_ask_answer(raw)["punkte"]) == ki.MAX_POINTS


def test_inventory_marks_stale_tables_and_drops_cards_on_them() -> None:
    # Live 13.11.2026: decision_events had 259 rows, all from 02.07.; the
    # model proposed a "Regel-Log" card with "the data is all there".
    conn = _db()
    conn.execute("CREATE TABLE decision_events (id TEXT, block_id TEXT)")
    conn.execute("INSERT INTO decision_events VALUES ('a', '2026-07-02T18:50:00')")
    now = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
    inv = ki.data_inventory(conn, now)
    text = "\n".join(ki.inventory_lines(inv))
    assert (
        "NICHT die Produktion; in keiner Karte gezeigt, auch nicht in Datenaufzeichnung): VERALTET"
        in text
    )
    assert "2026-07-02" in text
    # Since 14.11.2026 the production log lives in ha_decision_log: a card on
    # "why was it switched" is supported now, one on the Python core is not.
    keep, dropped = ki.drop_unsupported_cards(
        [
            "Tab Forschung: 'Kern-Replay'. Daten aus dem Python-Kern.",
            "Tab Einstellungen: 'Regel-Log'. Frage: Warum wurde geschaltet?",
        ],
        inv,
    )
    assert len(dropped) == 1 and "Kern-Replay" in dropped[0]
    assert keep[0].startswith("Tab Einstellungen")


def test_findings_mark_months_fixed_by_adr033() -> None:
    # Nights before 13.11.2026 ran with the old formula; their verdict is
    # already acted on and must not read as an open task.
    table = season_table(570, 12.5)
    check = {
        "nights": 30,
        "mined_nights": 10,
        "morning_after_mining": 1.0,
        "floor_pct": 5.0,
        "grid_kwh_after_mining": 15.0,
        "stop_socs": [74.0, 75.0, 76.0],
        "last_day": "2026-10-31",
    }
    text = season_findings(table, {10: check})[0]
    assert text.startswith("Saisonale Automatik Oktober: BEREITS KORRIGIERT")
    assert "bei 75 % ab" in text and len(text) <= 260
    open_check = dict(check, last_day="2026-11-20")
    assert "BEREITS" not in season_findings(table, {10: open_check})[0]


def test_unmeasured_hours_are_a_priority_finding() -> None:
    from src.explain import bithamster_ki as ki

    rec = {"history": {"suspect_runs": [{"blocks": 12, "kind": "held"}, {"blocks": 3}]}}
    found = ki.priority_findings([], None, {}, rec)
    assert len(found) == 1
    assert "2 Stunden gespeichert, aber nicht gemessen" in found[0]["text"]
    answer = {"text": "Alles vollständig.", "punkte": ["keine Datenlücken"]}
    assert not ki.finding_mentioned(found[0], answer)
