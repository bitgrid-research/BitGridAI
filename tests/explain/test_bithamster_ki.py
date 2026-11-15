"""Tests for src/explain/bithamster_ki.py (read-only dashboard explainer)."""

from __future__ import annotations

import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.explain import bithamster_ki as bk

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)

KPI_COLS = (
    "day TEXT PRIMARY KEY, blocks INT, coverage_pct REAL, pv_kwh REAL, house_kwh REAL,"
    " grid_import_kwh REAL, grid_export_kwh REAL, mining_kwh REAL, soc_min_pct REAL,"
    " soc_max_pct REAL, soc_h_locked REAL, soc_h_hold REAL, soc_h_eco REAL,"
    " soc_h_standard REAL, soc_h_super REAL, blocks_surplus_idle INT,"
    " blocks_switch_mismatch INT, blocks_temp_ge_110 INT, energy_to_sats REAL"
)
MINER_COLS = (
    "day TEXT, miner TEXT, h_eco REAL, h_standard REAL, h_super REAL, h_standby REAL,"
    " w_per_th REAL, tmax_max_c REAL, blocks_ge_110 INT, switch_mismatches INT"
)


def _kpi_row(
    day: str,
    coverage: float = 100.0,
    surplus: int = 0,
    mismatch: int = 0,
    pv: float = 5.0,
) -> tuple[Any, ...]:
    return (
        day,
        144,
        coverage,
        pv,
        15.0,
        10.0,
        0.5,
        1.0,
        60.0,
        90.0,
        2.0,
        20.0,
        1.0,
        0.5,
        0.5,
        surplus,
        mismatch,
        0,
        900.0,
    )


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "bitgrid.db"
    conn = sqlite3.connect(path)
    conn.execute(f"CREATE TABLE daily_kpi ({KPI_COLS})")
    conn.execute(f"CREATE TABLE daily_miner_kpi ({MINER_COLS})")
    conn.execute(
        "CREATE TABLE miner_states (block_id TEXT, miner TEXT, workmode_set TEXT,"
        " workmode_status TEXT)"
    )
    conn.executemany(
        "INSERT INTO miner_states VALUES (?,?,?,?)",
        [
            ("2026-11-10T21:00:00", "miner1", "Standby", "Off"),
            ("2026-11-10T21:00:00", "miner2", "Standby", "Off"),
            ("2026-11-11T02:30:00", "miner1", "Standby", "Off"),
            ("2026-11-11T10:00:00", "miner1", "Eco", "Off"),  # real mismatch
            ("2026-11-11T10:10:00", "miner1", "Eco", "Eco"),  # no mismatch
            ("2026-10-01T10:00:00", "miner1", "Super", "Standby"),  # outside window
        ],
    )
    rows = [
        _kpi_row("2026-11-10", surplus=12, pv=14.0),  # 2 h surplus, sunny
        _kpi_row("2026-11-11", mismatch=3),
        _kpi_row("2026-11-12", coverage=50.0, surplus=99),  # incomplete -> skipped
        _kpi_row("2026-11-13", surplus=60),  # running day -> excluded
        _kpi_row("2026-10-01", surplus=60),  # outside window
    ]
    conn.executemany(f"INSERT INTO daily_kpi VALUES ({','.join('?' * 19)})", rows)
    conn.executemany(
        f"INSERT INTO daily_miner_kpi VALUES ({','.join('?' * 10)})",
        [
            ("2026-11-10", "miner1", 2.0, 1.0, 0.0, 21.0, 18.5, 95.0, 0, 1),
            ("2026-11-11", "miner1", 1.0, 0.0, 0.0, 23.0, 19.5, 101.0, 2, 0),
        ],
    )
    conn.commit()
    conn.close()
    return path


def _states() -> dict[str, dict[str, Any]]:
    def s(entity: str, state: str, **attrs: Any) -> dict[str, Any]:
        return {"entity_id": entity, "state": state, "attributes": attrs}

    items = [
        s("sensor.sma_storage_battery_soc_total", "67"),
        s("sensor.sma_tripower_pv_power", "2100"),
        s("sensor.grid_import_w", "0"),
        s("sensor.miner_total_power_w", "unavailable"),
        s("sensor.miner1_workmode_status", "Standby"),
        s("input_number.mvp_soc_stop_pct", "81.0"),
        s("input_number.mvp_soc_eco_start_pct", "91.0"),
        s("input_boolean.mvp_night_block_enabled", "on"),
        s("input_datetime.mvp_night_block_start", "22:00:00"),
        s("input_datetime.mvp_night_block_end", "06:00:00"),
        s(
            "sensor.miner_1_auto_diagnose",
            "ok",
            summary="Ist=Standby | Ziel=Standby | SoC 67% < Stop 81%",
        ),
    ]
    return {i["entity_id"]: i for i in items}


GOOD_ANSWER = json.dumps(
    {
        "lage": {
            "headline": "Ich lade erst den Akku",
            "text": "Dein Akku steht bei 67 %.",
        },
        "optimierungen": [
            {
                "titel": "Sonne bleibt liegen",
                "befund": "2 Stunden Überschuss.",
                "vorschlag": "Probier mal X.",
                "pruefen": "Weniger Stunden.",
            }
        ],
    }
)


# ── formatting ────────────────────────────────────────────────────────────────


def test_de_num_uses_decimal_comma_and_thousands_dot() -> None:
    assert bk.de_num(1234.56) == "1.234,6"
    assert bk.de_num(3.0, 0) == "3"
    assert bk.de_num(None) == "unbekannt"


# ── research facts ────────────────────────────────────────────────────────────


def test_research_facts_skips_incomplete_and_running_days(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        facts = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    assert facts["days_used"] == 2
    assert facts["days_skipped_incomplete"] == 1
    assert (facts["first_day"], facts["last_day"]) == ("2026-11-10", "2026-11-11")
    assert facts["surplus_idle_hours"] == pytest.approx(2.0)
    assert facts["surplus_idle_days"] == 1
    assert facts["switch_mismatch_blocks"] == 3
    assert facts["sunny_days"] == 1
    assert facts["soc_h_mean"]["hold"] == pytest.approx(20.0)


def test_research_facts_aggregates_miners(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        m = bk.research_facts(conn, NOW)["miners"][0]
    finally:
        conn.close()
    assert m["miner"] == "miner1"
    assert m["h_eco"] == pytest.approx(3.0)
    assert m["w_per_th"] == pytest.approx(19.0)
    assert m["tmax_max_c"] == pytest.approx(101.0)
    assert m["blocks_ge_110"] == 2


def test_research_facts_empty_window(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        facts = bk.research_facts(conn, datetime(2027, 6, 1, tzinfo=timezone.utc))
    finally:
        conn.close()
    assert facts["days_used"] == 0
    assert facts["miners"] == []


# ── live facts and context ────────────────────────────────────────────────────


def test_live_facts_maps_unavailable_to_none() -> None:
    live = bk.live_facts(_states())
    assert live["live"]["soc_pct"] == 67.0
    assert live["live"]["miner_total_w"] is None
    assert live["live"]["miner1_mode"] == "Standby"
    assert live["night_block"] == {"enabled": True, "start": "22:00", "end": "06:00"}
    stop = next(t for t in live["thresholds"] if "Stop" in t["label"])
    assert stop["value"] == 81.0


def test_build_context_contains_the_numbers(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        research = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    text = bk.build_context(bk.live_facts(_states()), research, NOW)
    assert "Akku-Ladestand: 67 %" in text
    assert "Solarleistung gerade: 2,1 kW" in text
    assert "Stop-Schwelle Akku (Hausreserve): 81 %" in text
    assert "2,0 Stunden an 1 Tagen" in text
    assert "miner1" in text


def test_build_context_without_complete_days_says_so() -> None:
    research = {"window_days": 14, "days_used": 0}
    text = bk.build_context(bk.live_facts(_states()), research, NOW)
    assert "reichen die Daten nicht" in text


# ── model answer ──────────────────────────────────────────────────────────────


def test_parse_answer_accepts_fenced_json_with_think_block() -> None:
    raw = "<think>hmm</think>\n```json\n" + GOOD_ANSWER + "\n```"
    out = bk.parse_answer(raw)
    assert out["lage"]["headline"] == "Ich lade erst den Akku"
    assert len(out["optimierungen"]) == 1


def test_parse_answer_clips_and_limits() -> None:
    opts = [
        {"titel": f"T{i}", "befund": "b", "vorschlag": "v", "pruefen": "p"}
        for i in range(5)
    ]
    opts.append({"titel": "", "befund": "b", "vorschlag": "v"})  # incomplete -> dropped
    raw = json.dumps(
        {"lage": {"headline": "H", "text": "wort " * 200}, "optimierungen": opts}
    )
    out = bk.parse_answer(raw)
    assert len(out["optimierungen"]) == bk.MAX_OPTIMIZATIONS
    assert len(out["lage"]["text"]) <= bk.LIMITS["text"]
    assert out["lage"]["text"].endswith("…")


@pytest.mark.parametrize(
    "raw", ["kein json", json.dumps({"lage": {"headline": "H"}}), "[1, 2]"]
)
def test_parse_answer_rejects_unusable_output(raw: str) -> None:
    with pytest.raises(ValueError):
        bk.parse_answer(raw)


# ── HTTP: GET towards HA, POST only towards the LLM ───────────────────────────


class _Resp(io.BytesIO):
    def __enter__(self) -> "_Resp":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def test_read_ha_states_uses_get_only(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[Any] = []

    def fake_urlopen(req: Any, timeout: int) -> _Resp:
        seen.append(req)
        return _Resp(json.dumps(list(_states().values())).encode())

    monkeypatch.setattr(bk, "urlopen", fake_urlopen)
    states = bk.read_ha_states("http://ha:8123", "tok")
    assert "sensor.grid_import_w" in states
    assert [r.get_method() for r in seen] == ["GET"]
    assert seen[0].full_url == "http://ha:8123/api/states"
    assert seen[0].data is None


def test_call_llm_disables_thinking_and_asks_for_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[Any] = []

    def fake_urlopen(req: Any, timeout: int) -> _Resp:
        seen.append(req)
        return _Resp(
            json.dumps({"choices": [{"message": {"content": GOOD_ANSWER}}]}).encode()
        )

    monkeypatch.setattr(bk, "urlopen", fake_urlopen)
    assert bk.call_llm("http://gx10:8000", "m", "sys", "user") == GOOD_ANSWER
    body = json.loads(seen[0].data)
    assert seen[0].full_url == "http://gx10:8000/v1/chat/completions"
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["response_format"] == {"type": "json_object"}
    assert body["messages"][0] == {"role": "system", "content": "sys"}


# ── full run ──────────────────────────────────────────────────────────────────


def _soul(tmp_path: Path) -> Path:
    p = tmp_path / "SOUL.md"
    p.write_text("Du bist BitHamster.", encoding="utf-8")
    return p


def test_run_writes_ok_json_with_facts(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompts: list[tuple[str, str]] = []
    monkeypatch.setattr(bk, "read_ha_states", lambda url, token: _states())

    def fake_llm(url: str, model: str, system: str, user: str) -> str:
        prompts.append((system, user))
        return GOOD_ANSWER

    monkeypatch.setattr(bk, "call_llm", fake_llm)
    out = tmp_path / "www" / "bithamster_ki.json"
    result = bk.run(
        db=db_path,
        out=out,
        soul=_soul(tmp_path),
        ha_url="u",
        ha_token="t",
        llm_url="l",
        model="m",
        now=NOW,
    )
    assert result["ok"] is True
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["lage"]["headline"] == "Ich lade erst den Akku"
    assert data["facts"]["research"]["days_used"] == 2
    assert prompts[0][0] == "Du bist BitHamster."
    assert "LIVE-WERTE" in prompts[0][1]


def test_run_keeps_facts_and_reports_error_when_llm_fails(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bk, "read_ha_states", lambda url, token: _states())

    def broken(url: str, model: str, system: str, user: str) -> str:
        raise TimeoutError("vLLM busy")

    monkeypatch.setattr(bk, "call_llm", broken)
    out = tmp_path / "bithamster_ki.json"
    result = bk.run(
        db=db_path,
        out=out,
        soul=_soul(tmp_path),
        ha_url="u",
        ha_token="t",
        llm_url="l",
        model="m",
        now=NOW,
    )
    assert result["ok"] is False
    assert "TimeoutError" in result["error"]
    assert result["lage"] is None
    assert (
        json.loads(out.read_text(encoding="utf-8"))["facts"]["research"]["days_used"]
        == 2
    )


def test_run_missing_database_still_writes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bk, "read_ha_states", lambda url, token: _states())
    out = tmp_path / "bithamster_ki.json"
    result = bk.run(
        db=tmp_path / "nope.db",
        out=out,
        soul=_soul(tmp_path),
        ha_url="u",
        ha_token="t",
        llm_url="l",
        model="m",
        now=NOW,
    )
    assert result["ok"] is False
    assert out.exists()


def test_context_spells_out_wakeup_rule_and_season(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        research = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    text = bk.build_context(bk.live_facts(_states()), research, NOW)
    assert "Fällt der Akku unter 81 %" in text
    assert "mindestens 91 % hat" in text and "KEINE Startbedingung" in text
    assert "Winter, sonnenarm" in text
    # per-day means, not only totals (house 15 kWh/day in the fixture)
    assert "Hausverbrauch: im Schnitt 15,0 kWh pro Tag" in text


def test_season_text_covers_all_months() -> None:
    assert all(bk.season_text(m) for m in range(1, 13))
    assert "Sommer" in bk.season_text(6)


def test_next_step_names_the_wakeup_threshold() -> None:
    live = bk.live_facts(_states())
    live["thresholds"].append(
        {"label": "Sonne für Schnellstart", "value": 6000.0, "unit": "W"}
    )
    step = bk.next_step(live)
    assert step is not None and "Aufwachen erst ab 91 %" in step


def test_next_step_when_mining() -> None:
    live = bk.live_facts(_states())
    live["live"]["miner1_mode"] = "Eco"
    assert "unter 81 %" in (bk.next_step(live) or "")


# ── Auftraege (buttons and chat) ──────────────────────────────────────────────

DASHBOARD = """views:
  - title: Übersicht
    cards:
      - type: custom:button-card
        template: group_header
        icon: mdi:flash
        name: Energiefluss
  - title: Abfall
    cards:
      - type: custom:button-card
        template: group_header
        icon: mdi:calendar
        name: Kalender
"""

ASK_ANSWER = json.dumps(
    {
        "headline": "Alles im Lot",
        "text": "Die Aufzeichnung läuft.",
        "punkte": ["a", "", 3],
    }
)


@pytest.mark.parametrize(
    ("state", "task"),
    [
        ("fehler|2026-11-13T14:00:00", "fehler"),
        ("", None),
        ("fehler", None),
        ("hack|x", None),
    ],
)
def test_parse_request(state: str, task: str | None) -> None:
    assert bk.parse_request(state) == task


def test_dashboard_tabs_reads_group_headers_and_notes(tmp_path: Path) -> None:
    p = tmp_path / "dash.yaml"
    p.write_text(DASHBOARD, encoding="utf-8")
    tabs = bk.dashboard_tabs(p)
    assert tabs["Abfall"] == ["Kalender"]  # fixture YAML, not the live title
    assert tabs["Übersicht"][0].startswith("BitGridAI")  # hand-written note first
    assert tabs["Übersicht"][-1] == "Energiefluss"


def test_ask_prompt_per_task(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        research = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    states = _states()
    live = bk.live_facts(states)
    common: dict[str, Any] = dict(
        live=live,
        research=research,
        now=NOW,
        states=states,
        recording={"level": "ok", "reasons": [], "history": {"days_missing": 2}},
        tabs={"Abfall": ["Termine", "Kalender"]},
    )
    tab = bk.build_ask_prompt("tab", tab="Abfall", question=None, **common)
    assert "Karten in diesem Tab: Termine; Kalender." in tab
    assert '"punkte"' in tab
    err = bk.build_ask_prompt("fehler", tab=None, question=None, **common)
    assert "AUFZEICHNUNGSSTATUS" in err and "Nicht verfügbar:" in err
    assert "sensor.miner_total_power_w" in err
    q = bk.build_ask_prompt("frage", tab=None, question="Warum schläfst du?", **common)
    assert "FRAGE DES NUTZERS: Warum schläfst du?" in q


def test_parse_ask_answer_drops_bad_points() -> None:
    out = bk.parse_ask_answer(ASK_ANSWER)
    assert out == {
        "headline": "Alles im Lot",
        "text": "Die Aufzeichnung läuft.",
        "punkte": ["a"],
    }
    with pytest.raises(ValueError):
        bk.parse_ask_answer(json.dumps({"headline": "nur"}))


def test_run_ask_answers_once_per_request(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = {"state": "aufzeichnung|2026-11-13T14:00:00"}
    calls: list[str] = []
    monkeypatch.setattr(bk, "read_ha_state", lambda url, token, entity: request)
    monkeypatch.setattr(bk, "read_ha_states", lambda url, token: _states())

    def fake_llm(url: str, model: str, system: str, user: str) -> str:
        calls.append(user)
        return ASK_ANSWER

    monkeypatch.setattr(bk, "call_llm", fake_llm)
    out = tmp_path / "ask.json"
    kwargs: dict[str, Any] = dict(
        db=db_path,
        out=out,
        soul=_soul(tmp_path),
        ha_url="u",
        ha_token="t",
        llm_url="l",
        model="m",
        now=NOW,
    )
    first = bk.run_ask(**kwargs)
    assert (
        first is not None
        and first["ok"]
        and first["label"] == "Datenaufzeichnung prüfen"
    )
    assert "AUFZEICHNUNGSSTATUS" in calls[0]
    assert bk.run_ask(**kwargs) is None  # same request id: nothing to do
    request["state"] = "frage|2026-11-13T14:05:00"
    second = bk.run_ask(**kwargs)
    assert second is not None and second["task"] == "frage"
    assert len(calls) == 2


def test_run_ask_without_request_does_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bk, "read_ha_state", lambda url, token, entity: None)
    out = tmp_path / "ask.json"
    assert (
        bk.run_ask(
            db="x", out=out, soul="s", ha_url="u", ha_token="t", llm_url="l", model="m"
        )
        is None
    )
    assert not out.exists()


def test_read_ha_state_is_get_and_404_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    from urllib.error import HTTPError

    seen: list[Any] = []

    def fake_urlopen(req: Any, timeout: int) -> _Resp:
        seen.append(req)
        raise HTTPError(req.full_url, 404, "nf", None, None)  # type: ignore[arg-type]

    monkeypatch.setattr(bk, "urlopen", fake_urlopen)
    assert bk.read_ha_state("http://ha", "t", "input_text.x") is None
    assert seen[0].get_method() == "GET"


def test_recording_lines_use_local_time(monkeypatch: pytest.MonkeyPatch) -> None:
    lines = bk.recording_lines(
        {
            "level": "ok",
            "generated_at": "2026-11-13T02:55:00+00:00",
            "sync": {
                "last_start": "2026-11-13T02:45:00+00:00",
                "ok": True,
                "blocks_added": 144,
                "schedule": "03:45",
            },
        }
    )
    expected = (
        datetime(2026, 11, 13, 2, 45, tzinfo=timezone.utc)
        .astimezone()
        .strftime("%d.%m. %H:%M")
    )
    assert any(f"Letzter Sync: {expected} Uhr" in line for line in lines)
    assert bk.local_ts("kaputt") == "unbekannt"


def test_mismatch_breakdown_separates_rest_from_real(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        facts = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    b = facts["switch_mismatch_breakdown"]
    assert (b["rest"], b["real"]) == (3, 1)
    assert (b["rest_first"], b["rest_last"]) == (
        "2026-11-10T21:00:00",
        "2026-11-11T02:30:00",
    )
    text = " ".join(bk.mismatch_lines(facts))
    assert "KEIN Fehler, nur Hinweis: 3 Einträge" in text
    assert (
        "Echte Schaltfehler (Modus befohlen, Miner hat ihn nicht übernommen): 1 Einträge"
        in text
    )
    assert "je Miner" in text


def test_mismatch_breakdown_without_table() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        b = bk.mismatch_breakdown(conn, "2026-01-01", "2026-02-01")
    finally:
        conn.close()
    assert b["real"] == 0 and b["rest"] == 0


def test_context_wording_for_soc_and_zero_surplus(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        research = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    research["surplus_idle_hours"] = 0.0
    text = bk.build_context(bk.live_facts(_states()), research, NOW)
    assert "der HÖCHSTE Stand eines Tages lag im Mittel bei 90 %" in text
    assert "KEINE verpasste Gelegenheit" in text


def test_baseline_compares_with_previous_window(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        # 2026-10-01 lies in the 30 days before the 14-day window ending 13.11.
        research = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    b = research["baseline"]
    assert b["days"] == 1 and b["first_day"] == "2026-10-01"
    text = " ".join(bk.baseline_lines(research))
    assert "VERGLEICH mit den 1 vollständigen Tagen davor" in text
    assert "Sonne jetzt 9,5 kWh, vorher 5,0 kWh" in text
    assert "EINORDNUNG" in text


def test_baseline_missing_says_so() -> None:
    lines = bk.baseline_lines({"baseline": {"days": 0}, "days_used": 3})
    assert "Kein Vergleichszeitraum" in lines[0]


def test_assessment_low_battery_is_expected_when_sun_below_house() -> None:
    research = {
        "days_used": 14,
        "pv_kwh_mean": 10.8,
        "house_kwh_total": 17.2 * 14,
        "soc_max_mean": 32.4,
        "grid_import_kwh_total": 7.6 * 14,
        "grid_export_kwh_total": 0.09 * 14,
        "surplus_idle_hours": 0.0,
    }
    baseline = {"pv_kwh": 18.7, "grid_import_kwh": 6.3, "soc_max_pct": 54.5}
    text = " ".join(bk.assessment_lines(research, baseline))
    assert "Akku-Höchststand 32 %: ERWARTBAR" in text
    assert "Netzbezug 7,6 kWh/Tag, höher als vorher: ERWARTBAR" in text
    assert "praktisch nichts verschenkt, GUT" in text
    assert "GESAMTURTEIL: In diesem Zeitraum ist NICHTS auffällig" in text


def test_assessment_flags_battery_when_sun_is_enough() -> None:
    research = {
        "days_used": 7,
        "pv_kwh_mean": 30.0,
        "house_kwh_total": 15.0 * 7,
        "soc_max_mean": 40.0,
        "grid_import_kwh_total": 2.0 * 7,
        "grid_export_kwh_total": 5.0 * 7,
        "surplus_idle_hours": 3.0,
    }
    text = " ".join(
        bk.assessment_lines(
            research, {"pv_kwh": 25.0, "grid_import_kwh": 3.0, "soc_max_pct": 80.0}
        )
    )
    assert "Akku-Höchststand 40 %: AUFFÄLLIG" in text
    assert "GESAMTURTEIL" not in text
    assert "3,0 Stunden Überschuss" in text


def test_watch_answers_new_requests_and_survives_errors(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    states = iter(
        [
            {"state": "fehler|2026-11-13T14:00:00"},  # new -> answered
            {"state": "fehler|2026-11-13T14:00:00"},  # same -> nothing
            ConnectionError("HA restarting"),  # error -> back-off, keep going
            {"state": "tab|2026-11-13T14:01:00"},  # new -> answered
        ]
    )

    def fake_state(url: str, token: str, entity: str) -> Any:
        item = next(states)
        if isinstance(item, Exception):
            raise item
        return item

    sleeps: list[float] = []
    monkeypatch.setattr(bk, "read_ha_state", fake_state)
    monkeypatch.setattr(bk, "read_ha_states", lambda url, token: _states())
    monkeypatch.setattr(bk, "call_llm", lambda url, model, system, user: ASK_ANSWER)
    answered = bk.watch(
        poll_s=3.0,
        max_rounds=4,
        sleep=sleeps.append,
        db=db_path,
        out=tmp_path / "ask.json",
        soul=_soul(tmp_path),
        ha_url="u",
        ha_token="t",
        llm_url="l",
        model="m",
    )
    assert answered == 2
    assert sleeps == [3.0, 3.0, bk.WATCH_ERROR_BACKOFF_S, 3.0]


def test_history_is_newest_first_and_capped() -> None:
    prev: dict[str, Any] = {
        "request_id": "a|1",
        "task": "fehler",
        "answer": {"headline": "alt"},
    }
    hist = bk.append_history(prev, {"request_id": "b|2", "task": "tab", "ok": True})
    assert [h["request_id"] for h in hist] == ["b|2", "a|1"]  # old single answer kept
    prev = {"history": [{"request_id": f"x|{i}"} for i in range(bk.ASK_HISTORY_MAX)]}
    hist = bk.append_history(prev, {"request_id": "new|0"})
    assert len(hist) == bk.ASK_HISTORY_MAX
    assert hist[0]["request_id"] == "new|0"
    assert hist[-1]["request_id"] == f"x|{bk.ASK_HISTORY_MAX - 2}"


def test_run_ask_writes_history(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = {"state": "fehler|2026-11-13T14:00:00"}
    monkeypatch.setattr(bk, "read_ha_state", lambda url, token, entity: request)
    monkeypatch.setattr(bk, "read_ha_states", lambda url, token: _states())
    monkeypatch.setattr(bk, "call_llm", lambda url, model, system, user: ASK_ANSWER)
    out = tmp_path / "ask.json"
    kwargs: dict[str, Any] = dict(
        db=db_path,
        out=out,
        soul=_soul(tmp_path),
        ha_url="u",
        ha_token="t",
        llm_url="l",
        model="m",
        now=NOW,
    )
    bk.run_ask(**kwargs)
    request["state"] = "tab|2026-11-13T14:01:00"
    bk.run_ask(**kwargs)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert [h["task"] for h in data["history"]] == ["tab", "fehler"]
    assert data["history"][1]["answer"]["headline"] == "Alles im Lot"
    assert "history" not in data["history"][0]  # no nesting


# ---------------------------------------------------------------------------
# Deterministic post-checks and answer log (13.11.2026)
# ---------------------------------------------------------------------------


def test_drop_existing_cards_removes_known_titles() -> None:
    tabs = {
        "Einstellungen": ["Saisonale Schwellwerte"],
        "Forschung": ["Lücken", "Aufzeichnung je Tag"],
        "Übersicht": ["Miner"],
    }
    points = [
        "Akku über Nacht (Forschung): Grundlast je Nacht.",
        "Aufzeichnungs-Lücken (Forschung): fehlende Tage.",
        "Saisonale Schwellwerte (Einstellungen): Grenzen.",
        "Miner-Verfügbarkeit (Forschung): Zeiten ohne Meldung.",
    ]
    keep, dropped = bk.drop_existing_cards(points, tabs)
    assert [p.split(" (")[0] for p in keep] == [
        "Akku über Nacht",
        "Miner-Verfügbarkeit",
    ]
    assert len(dropped) == 2


def test_unverified_numbers_flags_invented_values() -> None:
    context = "Akku 75 %, Netzbezug 124,7 kWh, Sonne 6.000 W, 14 Tage."
    answer = {
        "headline": "Akku 75 %",
        "text": "Rund 125 kWh aus dem Netz, ab 6.000 W Sonne.",
        "punkte": ["In 14 Tagen 2 Mal", "Spart 340 Euro im Jahr"],
    }
    assert bk.unverified_numbers(answer, context) == ["340"]


def test_ensure_findings_adds_skipped_finding_in_front() -> None:
    findings = [
        {
            "text": "Saisonale Automatik Oktober: Hausreserve 75 % ist zu niedrig.",
            "keys": ["Oktober", "Hausreserve"],
        },
        {
            "text": "Datenaufzeichnung: Außentemperatur leer.",
            "keys": ["Außentemperatur"],
        },
    ]
    answer = {"text": "Alles gut.", "punkte": ["Außentemperatur fehlt seit August."]}
    added = bk.ensure_findings(answer, findings, 6)
    assert len(added) == 1 and added[0].startswith("Fest berechnet: Saisonale")
    assert answer["punkte"][0] == added[0]
    assert answer["punkte"][1] == "Außentemperatur fehlt seit August."


def test_priority_findings_collects_season_data_and_gaps() -> None:
    inv = {
        "blocks": 100,
        "columns": [("Solarleistung", 100.0), ("Bewölkung", 0.0)],
        "tables": [],
    }
    out = bk.priority_findings(
        ["Saisonale Automatik Oktober: Hausreserve 75 % ist zu niedrig."],
        inv,
        {"surplus_idle_hours": 0, "window_days": 14},
        {"history": {"days_missing": 50}},
    )
    texts = [f["text"] for f in out]
    assert texts[0].startswith("Saisonale Automatik Oktober")
    assert out[0]["keys"] == ["Oktober"]
    assert any("Bewölkung" in t for t in texts)
    assert any("50 Tage fehlen" in t for t in texts)
    assert not any("Überschuss" in t for t in texts)


def test_run_ask_logs_answer_with_prompt(
    db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.explain import bithamster_log as hl

    request = {"state": "gesamtcheck|2026-11-13T14:00:00"}
    monkeypatch.setattr(bk, "read_ha_state", lambda url, token, entity: request)
    monkeypatch.setattr(bk, "read_ha_states", lambda url, token: _states())
    monkeypatch.setattr(bk, "call_llm", lambda url, model, system, user: ASK_ANSWER)
    log_db = tmp_path / "log" / "bithamster_log.db"
    result = bk.run_ask(
        db=db_path,
        out=tmp_path / "ask.json",
        soul=_soul(tmp_path),
        ha_url="u",
        ha_token="t",
        llm_url="l",
        model="m",
        log_db=log_db,
        now=NOW,
    )
    assert result is not None and result["ok"] and result["checks"] is not None
    conn = hl.connect(log_db)
    row = conn.execute(
        "SELECT kind, task, ok, headline, prompt, checks_json FROM hamster_log"
    ).fetchone()
    conn.close()
    assert row[:4] == ("ask", "gesamtcheck", 1, "Alles im Lot")
    assert "AUFTRAG: Alles prüfen" in row[4]
    assert "unverified_numbers" in json.loads(row[5])


def test_log_never_raises_and_import_is_idempotent(tmp_path: Path) -> None:
    from src.explain import bithamster_log as hl

    assert hl.log_entry(tmp_path, "ask", {"ok": True}) is False  # path is a dir
    ask = {
        "history": [
            {
                "request_id": "b|2",
                "task": "fehler",
                "ok": True,
                "generated_at": "t2",
                "answer": {"headline": "h2", "text": "x", "punkte": []},
            },
            {
                "request_id": "a|1",
                "task": "tab",
                "ok": True,
                "generated_at": "t1",
                "answer": {"headline": "h1", "text": "y", "punkte": ["p"]},
            },
        ]
    }
    path = tmp_path / "l.db"
    assert hl.import_history(path, ask) == 2
    assert hl.import_history(path, ask) == 0
    conn = hl.connect(path)
    order = [
        r[0] for r in conn.execute("SELECT request_id FROM hamster_log ORDER BY id")
    ]
    conn.close()
    assert order == ["a|1", "b|2"]  # oldest first


def test_rules_in_words_marks_blocked_stages() -> None:
    th = [
        {"label": "Standard-Start Akku", "value": 100.0, "unit": "%"},
        {"label": "Super-Start Akku", "value": 100.0, "unit": "%"},
    ]
    text = "\n".join(bk.rules_in_words(th, "Nur Eco"))
    assert "Standard und Super sind in diesem Monat GESPERRT" in text
    assert "Super ab" not in text
    text = "\n".join(bk.rules_in_words(th, "Eco + Standard"))
    assert "Standard ab 100 %" in text and "Super ist in" in text
    assert "Super ab 100 %" in "\n".join(bk.rules_in_words(th, None))


def test_build_context_shows_blocked_thresholds_as_blocked(db_path: Path) -> None:
    states = _states()
    states["sensor.mvp_saison_status"] = {
        "entity_id": "sensor.mvp_saison_status",
        "state": "Nur Eco",
        "attributes": {},
    }
    states["input_number.mvp_soc_super_pct"] = {
        "entity_id": "input_number.mvp_soc_super_pct",
        "state": "100",
        "attributes": {},
    }
    live = bk.live_facts(states)
    ctx = bk.build_context(live, {"window_days": 14, "days_used": 0}, NOW)
    assert "Saison diesen Monat: Nur Eco" in ctx
    assert "- Super-Start Akku: GESPERRT in diesem Monat" in ctx
    assert "Super-Start Akku: 100" not in ctx


def test_yesterday_lines_use_real_pool_revenue(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE bitcoin_daily_settlement (day TEXT PRIMARY KEY, earned_btc REAL)"
    )
    conn.execute("INSERT INTO bitcoin_daily_settlement VALUES ('2026-11-12', 5.6e-07)")
    conn.commit()
    text = "\n".join(bk.yesterday_lines(conn, NOW))
    assert "GESTERN (12.11." in text
    assert "Poolertrag laut F2Pool-Abrechnung: 56 Sats" in text
    conn.execute("DELETE FROM bitcoin_daily_settlement")
    text = "\n".join(bk.yesterday_lines(conn, NOW))
    assert "Rechne KEINEN Ertrag hoch" in text
    conn.close()


def test_drop_existing_cards_by_quoted_name_and_by_content() -> None:
    # Live 13.11.2026: "Akku über Nacht-Historie" with the very question of the
    # existing card Akku über Nacht passed the name-only filter.
    tabs = {
        "Forschung": ["Akku über Nacht", "Solarprognose", "Hardware-Zustand (W/TH)"]
    }
    points = [
        "Tab Einstellungen: 'Akku über Nacht-Historie'. Frage: Reicht die"
        " Hausreserve? Daten: Morgendlicher Akkustand vs. Netzbezug nachts.",
        "Tab Bitcoin: 'Effizienz-Trend'. Frage: Werden die Miner schlechter?"
        " Daten: W pro TH im Zeitverlauf.",
        "Tab Energie: 'Akku-Verlauf'. Frage: Wie schnell lädt der Akku?",
    ]
    keep, dropped = bk.drop_existing_cards(points, tabs)
    assert len(dropped) == 2
    assert keep == [points[2]]


def test_drop_existing_cards_season_status_is_saisonsteuerung() -> None:
    tabs = {"Einstellungen": ["Saisonsteuerung"]}
    point = (
        "Karte 'Saison-Status' im Tab Einstellungen: Zeigt live, welche Stufen"
        " gesperrt sind und warum (z. B. 'Nur Eco' wegen Winter)."
    )
    assert bk.drop_existing_cards([point], tabs) == ([], [point])


def test_drop_existing_cards_second_live_run() -> None:
    tabs = {"Forschung": ["Akku über Nacht"], "Bitcoin": ["Mining-Effizienz"]}
    points = [
        "Tab Forschung: 'Akku-Höchststand und Start'. Zeigt täglich den Abstand"
        " zur Hausreserve.",
        "Tab Energie: 'Nacht-Grundlast-Check'. Vergleicht die gemessenen 579 W"
        " mit der eingestellten 570 W.",
        "Tab Bitcoin: 'Sats pro kWh Trend'. Zeigt den Schnitt im Zeitverlauf.",
    ]
    keep, dropped = bk.drop_existing_cards(points, tabs)
    assert keep == [points[0]] and len(dropped) == 2


def test_tab_value_lines_reads_tab_and_included_views(tmp_path: Path) -> None:
    (tmp_path / "views").mkdir()
    (tmp_path / "views" / "x.yaml").write_text(
        "entity: sensor.included_one\nnested: !include y.yaml\n", encoding="utf-8"
    )
    (tmp_path / "views" / "y.yaml").write_text(
        "entity: sensor.nested_one\n", encoding="utf-8"
    )
    dash = tmp_path / "dash.yaml"
    dash.write_text(
        "views:\n"
        "  - title: Energie\n"
        "    cards:\n"
        "      - entity: sensor.pv_power\n"
        "      - !include views/x.yaml\n"
        "      - entity: sensor.not_in_ha\n"
        "  - title: Bitcoin\n"
        "    cards:\n"
        "      - entity: sensor.btc_price\n",
        encoding="utf-8",
    )
    states = {
        "sensor.pv_power": {
            "state": "1200",
            "attributes": {"friendly_name": "PV", "unit_of_measurement": "W"},
        },
        "sensor.included_one": {"state": "unavailable", "attributes": {}},
        "sensor.nested_one": {"state": "3", "attributes": {}},
        "sensor.btc_price": {"state": "90000", "attributes": {}},
    }
    lines = bk.tab_value_lines(dash, "Energie", states)
    assert lines == [
        "Karte ohne Titel:",
        "- PV (sensor.pv_power): 1200 W",
        "- sensor.included_one (sensor.included_one): UNAVAILABLE",
        "- sensor.nested_one (sensor.nested_one): 3",
    ]


def test_tabcheck_prompt_has_values_other_tabs_and_inventory(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        research = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    prompt = bk.build_ask_prompt(
        "tabcheck",
        live=bk.live_facts(_states()),
        research=research,
        now=NOW,
        states=_states(),
        recording=None,
        tabs={"Energie": ["Verbrauchsverlauf"], "Bitcoin": ["Poolerträge"]},
        tab="Energie",
        question=None,
        inventory=["DATENBESTAND x"],
        tab_values=["- PV (sensor.pv_power): 1200 W"],
    )
    assert "AUFTRAG: Tab verbessern" in prompt
    assert "TAB: Energie" in prompt and "Verbrauchsverlauf" in prompt
    assert "- PV (sensor.pv_power): 1200 W" in prompt
    assert "- Bitcoin: Poolerträge" in prompt and "- Energie:" not in prompt
    assert "DATENBESTAND x" in prompt


def test_parse_request_knows_tabcheck() -> None:
    assert bk.parse_request("tabcheck|2026-11-13T17:00:00") == "tabcheck"


def test_tabcheck_drops_only_cards_of_other_tabs() -> None:
    prepared = {
        "tabs": {"Energie": ["Verbrauchsverlauf"], "Übersicht": ["Tagesverlauf"]},
        "tab": "Energie",
        "findings": [],
        "inventory": None,
        "prompt": "",
    }
    own = "Karte 'Verbrauchsverlauf': Liste kürzen, nur Top-Verbraucher."
    dup = (
        "Karte 'Verbrauchsverlauf': Gegenüberstellung von Solarproduktion und"
        " Hausverbrauch im Zeitverlauf fehlt."
    )
    answer = {"headline": "x", "text": "y", "punkte": [own, dup]}
    checks = bk.finish_answer("tabcheck", answer, prepared)
    assert answer["punkte"] == [own]
    assert checks["dropped_existing"] == [dup]


def test_tab_value_lines_groups_by_card_and_skips_controls(tmp_path: Path) -> None:
    dash = tmp_path / "dash.yaml"
    dash.write_text(
        "views:\n"
        "  - title: Energie\n"
        "    cards:\n"
        "      - type: custom:button-card\n"
        "        template: group_header\n"
        "        name: Aktueller Verbrauch\n"
        "      - entity: sensor.load\n"
        "      - type: custom:button-card\n"
        "        template: group_header\n"
        "        name: Verlauf\n"
        "      - entity: sensor.counter\n"
        "      - entity: input_select.historie_raum\n",
        encoding="utf-8",
    )
    states = {
        "sensor.load": {"state": "600", "attributes": {}},
        "sensor.counter": {"state": "12", "attributes": {}},
        "input_select.historie_raum": {"state": "Bad", "attributes": {}},
    }
    assert bk.tab_value_lines(dash, "Energie", states) == [
        "Karte Aktueller Verbrauch:",
        "- sensor.load (sensor.load): 600",
        "Karte Verlauf:",
        "- sensor.counter (sensor.counter): 12",
    ]


def test_fix_card_tabs_moves_card_to_its_real_tab() -> None:
    tabs = {
        "Übersicht": ["Tagesbilanz", "Miner"],
        "Steuerung": ["Miner"],
        "Energie": ["Verbrauchsverlauf"],
    }
    answer = {
        "text": "Siehe (Tab Energie, Karte Tagesbilanz).",
        "punkte": [
            "Netzbezug 7,6 kWh (Tab Energie, Karte Tagesbilanz).",
            "Miner im Standby (Tab Energie, Karte Miner).",  # two homes: keep
            "Liste kürzen (Tab Energie, Karte Verbrauchsverlauf).",
        ],
    }
    fixes = bk.fix_card_tabs(answer, tabs)
    assert answer["text"] == "Siehe (Tab Übersicht, Karte Tagesbilanz)."
    assert answer["punkte"][0].endswith("(Tab Übersicht, Karte Tagesbilanz).")
    assert answer["punkte"][1].endswith("(Tab Energie, Karte Miner).")
    assert answer["punkte"][2].endswith("(Tab Energie, Karte Verbrauchsverlauf).")
    assert fixes == ["Tagesbilanz: Tab Energie -> Übersicht"] * 2


def test_live_soc_template_replaces_only_the_live_soc() -> None:
    live = {
        "live": {"soc_pct": 64.0},
        "thresholds": [{"value": 95.0}, {"value": 100.0}],
    }
    text = "Dein Akku steht bei 64 %, unter der Hausreserve von 95 %. 164 % nie."
    assert bk.live_soc_template(text, live) == (
        "Dein Akku steht bei {akku} %, unter der Hausreserve von 95 %. 164 % nie."
    )
    # Same number as a threshold: ambiguous, leave it.
    live["live"]["soc_pct"] = 95.0
    assert bk.live_soc_template("Akku 95 %, Stop 95 %.", live) is None
    live["live"]["soc_pct"] = 50.0
    assert bk.live_soc_template("Kein Akkustand im Text.", live) is None


def test_research_card_lines_describe_json_cards(tmp_path: Path) -> None:
    data = {
        "nights": {
            "months": [
                {
                    "month": 10,
                    "nights": 30,
                    "mined_nights": 10,
                    "verdict": "zu_niedrig",
                    "morning_after_mining": 2.0,
                    "grid_kwh_after_mining": 15.0,
                }
            ],
            "recent": [{}] * 14,
        },
        "forecast": {"days_used": 14, "bias_pct": 74.0, "mae_pct": 80.0},
        "efficiency": {
            "miners": [{"miner": "miner1", "verdict": "stabil", "change_pct": -0.7}]
        },
        "peak": [{"soc_max": 85.0, "missing": "akku", "eco_start": 100}],
    }
    path = tmp_path / "research_cards.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    text = "\n".join(bk.research_card_lines(path, "Forschung"))
    assert "Karte Solarprognose:" in text and "74 % daneben" in text
    assert "Karte Akku über Nacht" in text and "Monat 10: 30 Nächte" in text
    assert "zu_niedrig" in text
    assert "miner1: stabil" in text
    assert "an 0 von 1 Tagen Start möglich, bester Tag 85 %" in text
    assert bk.research_card_lines(path, "Energie") == []


def test_drop_existing_cards_eval_wordings() -> None:
    tabs = {"Forschung": ["Akku-Höchststand und Start"], "Übersicht": ["Tagesverlauf"]}
    points = [
        "Tab Forschung: 'Akku-Start-Check'. Zeigt, wie oft der Akku die 100 %"
        " für den Start erreicht hat.",
        "Fehlende Karte: Ein direkter Vergleich von Solarerzeugung und"
        " Hausverbrauch fehlt.",
    ]
    keep, dropped = bk.drop_existing_cards(points, tabs)
    assert keep == [] and len(dropped) == 2


def test_unverified_numbers_ignores_dates() -> None:
    answer = {
        "headline": "",
        "text": "Letzte Zeile 02.07.2026, Stand 13.11.",
        "punkte": [],
    }
    assert bk.unverified_numbers(answer, "nichts") == []


def test_karten_all_dropped_gets_an_honest_text() -> None:
    prepared = {
        "tabs": {"Forschung": ["Akku über Nacht"]},
        "findings": [],
        "inventory": None,
        "prompt": "",
    }
    answer = {
        "headline": "Akku über Nacht fehlt",
        "text": "Die Akku über Nacht fehlt im Dashboard.",
        "punkte": ["Akku über Nacht (Tab Forschung): Akku morgens."],
    }
    bk.finish_answer("karten", answer, prepared)
    assert answer["punkte"] == [] and answer["headline"] == "Keine neue Karte gefunden"


def test_yesterday_names_the_bitaxe_when_the_pool_rate_is_small() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE bitcoin_daily_settlement (day TEXT, earned_btc REAL,"
        " pool_ths_avg REAL)"
    )
    conn.execute(
        "INSERT INTO bitcoin_daily_settlement VALUES ('2026-11-12', 5.6e-7, 1.38)"
    )
    now = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
    text = "\n".join(bk.yesterday_lines(conn, now))
    assert "56 Sats" in text and "1,4 TH/s" in text and "Bitaxe" in text
    conn.execute("UPDATE bitcoin_daily_settlement SET pool_ths_avg = 120")
    assert "Bitaxe" not in "\n".join(bk.yesterday_lines(conn, now))


def test_entity_label_spells_out_groups_and_rooms() -> None:
    assert "NICHT die Miner" in bk.entity_label("sensor.typ_computer_power_w", None)
    assert (
        bk.entity_label("sensor.raum_schlafzimmer1_power_w", None)
        == "Raum Schlafzimmer1"
    )
    assert bk.entity_label("sensor.pv", "PV") == "PV"


def test_winter_lines_only_in_winter_and_name_the_heizstab() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE energy_states (block_id TEXT, heizstab_power_w REAL,"
        " battery_soc_pct REAL)"
    )
    for i in range(144):
        block = f"2026-11-12T{i // 6:02d}:{i % 6 * 10:02d}:00"
        conn.execute("INSERT INTO energy_states VALUES (?, 600, 20)", (block,))
    winter = bk.winter_lines(conn, datetime(2026, 11, 13, 12, tzinfo=timezone.utc))
    assert winter is not None
    text = "\n".join(winter)
    assert text.startswith("- PRIORITÄT im Winter: 1. Der Akku")
    assert "BEFUND HEIZSTAB" in text and "14,4 kWh" in text
    assert bk.winter_lines(conn, datetime(2026, 7, 1, 12, tzinfo=timezone.utc)) is None


def test_fit_to_card_state_no_sleeping_outside_the_night_block() -> None:
    live = {
        "live": {"soc_pct": 54.0, "miner1_mode": "Standby", "miner2_mode": "Standby"},
        "thresholds": [
            {"label": "Stop-Schwelle Akku (Hausreserve)", "value": 95.0},
            {"label": "Eco-Start Akku", "value": 100.0},
        ],
        "night_active": False,
    }
    assert bk.card_state(live) == "charge"
    lage = {
        "headline": "Akku leer, ich schlafe",
        "text": "Ich schlafe, bis er voll ist.",
    }
    assert bk.fit_to_card_state(lage, live) is True
    assert lage == {
        "headline": "Akku lädt zuerst",
        "text": "Ich ruhe, bis er voll ist.",
    }
    live["night_active"] = True
    lage = {"headline": "Ich schlafe", "text": "Nachtsperre."}
    assert bk.fit_to_card_state(lage, live) is False


def test_drop_shown_claims_removes_points_against_the_card_content() -> None:
    answer = {
        "text": "Der Tab ist ruhig. Die Hardware-Abzahlung zeigt 400 Euro, aber keine Sats.",
        "punkte": [
            "Karte Hardware-Abzahlung: Zeigt nur 400 Euro Investition.",
            "Karte Langzeitbilanz: Fehlt der Monatsertrag in Sats.",
            "Karte Mining Verlauf: 0 Stunden Laufzeit, obwohl der Bitaxe läuft.",
        ],
    }
    dropped = bk.drop_shown_claims(answer)
    assert answer["punkte"] == [
        "Karte Mining Verlauf: 0 Stunden Laufzeit, obwohl der Bitaxe läuft."
    ]
    assert answer["text"] == "Der Tab ist ruhig."
    assert len(dropped) == 3


def test_drop_existing_cards_heizstab_and_night_discharge_live_14_11() -> None:
    tabs = {"Forschung": ["Akku über Nacht", "Akku-Höchststand und Start"]}
    points = [
        "Tab Forschung: 'Heizstab vs. Akku'. Zeigt, wann der Heizstab Strom zog,"
        " obwohl der Akku unter 95 % war.",
        "Tab Forschung: 'Akku-Entleerung nachts'. Zeigt die Entladeleistung in"
        " der Nacht.",
    ]
    assert bk.drop_existing_cards(points, tabs) == ([], points)


def test_tab_value_lines_climate_shows_room_temperature(tmp_path: Path) -> None:
    dash = tmp_path / "d.yaml"
    dash.write_text(
        "views:\n  - title: Grundriss\n    cards:\n"
        "      - name: Räume\n        entity: climate.bad\n",
        encoding="utf-8",
    )
    states = {
        "climate.bad": {
            "state": "heat",
            "attributes": {"friendly_name": "Bad", "current_temperature": 21.0},
        }
    }
    text = "\n".join(bk.tab_value_lines(dash, "Grundriss", states))
    assert "heat, Raum 21,0 °C" in text


def test_recording_lines_report_stored_but_not_measured_hours() -> None:
    # Live 14.11.2026: "173 of 173 days complete, no problems".
    status = {
        "level": "ok",
        "generated_at": "2026-11-14T07:00:00+00:00",
        "history": {
            "first_day": "2026-05-25",
            "days_complete": 173,
            "days_total": 173,
            "days_missing": 0,
            "days_partial": 0,
            "suspect_runs": [
                {"from": "2026-08-07T15:40:00", "blocks": 139, "kind": "held"},
                {"from": "2026-05-27T06:20:00", "blocks": 69, "kind": "zero"},
                {"from": "2026-06-06T10:00:00", "blocks": 3, "kind": "zero"},
            ],
        },
    }
    text = "\n".join(bk.recording_lines(status))
    assert "ACHTUNG" in text and "35 Stunden in 2 Zeiträumen" in text
    assert "23,2 h, Werte eingefroren" in text
    assert "11,5 h, Hausverbrauch 0 W" in text


# ── per-card requests from the header buttons (15.11.2026) ──────────────


def test_parse_request_accepts_card_tasks_only_for_known_cards() -> None:
    assert (
        bk.parse_request("karte_daten@nights|2026-11-15T10:00:00")
        == "karte_daten@nights"
    )
    assert bk.parse_request("karte_daten@unbekannt|2026-11-15T10:00:00") is None
    assert bk.parse_request("karte_foo@nights|2026-11-15T10:00:00") is None
    assert bk.parse_request("karte_daten@nights") is None


def test_task_label_names_mode_and_card() -> None:
    assert bk.task_label("karte_verbessern@switching") == (
        "Karte verbessern: Schaltwechsel"
    )
    assert bk.task_label("fehler") == "Fehler finden"


def test_card_context_only_holds_the_requested_card(tmp_path: Path) -> None:
    dash = tmp_path / "dash.yaml"
    dash.write_text(
        "views:\n"
        "  - title: Forschung\n"
        "    cards:\n"
        "      - type: custom:button-card\n"
        "        template: group_header_ki\n"
        "        icon: mdi:x\n"
        "        name: Schaltwechsel\n"
        "      - entity: sensor.wechsel_heute\n"
        "      - type: custom:button-card\n"
        "        template: group_header\n"
        "        icon: mdi:y\n"
        "        name: Solarprognose\n"
        "      - entity: sensor.prognose\n",
        encoding="utf-8",
    )
    states = {
        "sensor.wechsel_heute": {"state": "3", "attributes": {"friendly_name": "W"}},
        "sensor.prognose": {"state": "9", "attributes": {"friendly_name": "P"}},
    }
    cards = {
        "automation": {
            "switching": {
                "target": 2,
                "months": [{"mining_days": 10, "days_over": 2, "dropouts": 1}],
            },
            "surplus": {"hours": 4.0, "export_kwh": 9.0, "months": []},
        }
    }
    lines = bk.card_context_lines(
        "switching", dashboard=dash, states=states, cards=cards, recording=None
    )
    text = "\n".join(lines)
    assert "KARTE: Schaltwechsel" in text
    assert "sensor.wechsel_heute" in text
    assert "sensor.prognose" not in text
    assert "Schaltwechsel: an 2 von 10" in text
    assert "Ungenutzter Solarüberschuss" not in text
    # The new header template still counts as a card title.
    assert bk.dashboard_tabs(dash)["Forschung"] == ["Schaltwechsel", "Solarprognose"]


def test_card_prompt_uses_card_instruction_and_inventory(db_path: Path) -> None:
    conn = bk.open_readonly(db_path)
    try:
        research = bk.research_facts(conn, NOW)
    finally:
        conn.close()
    prompt = bk.build_ask_prompt(
        "karte_daten@nights",
        live=bk.live_facts(_states()),
        research=research,
        now=NOW,
        states=_states(),
        recording=None,
        tabs={},
        tab=None,
        question=None,
        inventory=["DATENBESTAND: test"],
        research_lines=["KARTE: Akku über Nacht (Tab Forschung)"],
    )
    assert "AUFTRAG: Daten prüfen: Akku über Nacht." in prompt
    assert "Bleib bei dieser Karte" in prompt
    assert "DATENBESTAND: test" in prompt


def test_card_context_fixes_terms() -> None:
    lines = bk.card_context_lines(
        "switching", dashboard=None, states={}, cards=None, recording=None
    )
    text = "\n".join(lines)
    assert "Obergrenze" in text


def test_card_task_drops_claim_that_the_card_shows_nothing() -> None:
    answer = {
        "headline": "x",
        "text": "Die Karte zeigt keine Werte für W pro TH. Im Sommer wieder.",
        "punkte": ["Karte zeigt keine Werte je Monat", "Im Sommer prüfen"],
    }
    dropped = bk.drop_shown_claims(answer, "Hardware-Zustand (W/TH)")
    assert answer["punkte"] == ["Im Sommer prüfen"]
    assert "keine Werte" not in answer["text"]
    assert len(dropped) == 2
