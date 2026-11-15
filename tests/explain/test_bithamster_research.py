"""Tests for bithamster_research: findings, decision window/log, reviewed list."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.data.db import get_connection
from src.explain import bithamster_research as br

UTC = timezone.utc
CET = timezone(timedelta(hours=1))
NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)

CARDS = {
    "automation": {
        "surplus": {
            "hours": 41.8,
            "export_kwh": 121.6,
            "months": [
                {"reasons": {"Akku unter Stopp-Schwelle": 20.0, "unbekannt": 13.2}},
                {"reasons": {"Akku unter Stopp-Schwelle": 5.1, "Handbetrieb": 0.7}},
            ],
        },
        "switching": {
            "target": 2,
            "dropout_max_min": 15,
            "months": [
                {"month": "2026-07", "mining_days": 31, "days_over": 6, "dropouts": 38},
                {"month": "2026-11", "mining_days": 0, "days_over": 0, "dropouts": 0},
            ],
            "threshold_changes": [
                {
                    "timestamp": "2026-11-14T02:05:37+00:00",
                    "label": "Stopp",
                    "old": "60.0",
                    "new": "95.0",
                    "source": "history",
                }
            ],
        },
        "safety": {"hot_blocks_total": 39, "tmax_limit_c": 110, "errors_total": 94},
    },
    "forecast": {
        "months": [
            {"month": "2026-07", "days": 30, "bias_pct": -14.6},
            {"month": "2026-11", "days": 13, "bias_pct": 74.8},
            {"month": "2026-05", "days": 0, "bias_pct": None},
        ]
    },
    "heizstab": {"days": 14, "heizstab_kwh_not_full": 11.3},
}


def test_findings_give_size_and_limits() -> None:
    text = "\n".join(br.research_findings_lines(CARDS))
    assert "Akku unter Stopp-Schwelle 25,1 h" in text
    assert "an 6 von 31 Mining-Tagen" in text and "38 kurze Abbrüche" in text
    assert "Stopp 60 → 95 %" in text
    assert "Juli -15 %" in text and "November +75 %" in text
    assert "Mai" not in text  # month without usable days
    # 11.3 kWh over 14 days: the size the model needs to judge the heating rod
    assert "0,8 kWh am Tag" in text and "NICHT allein" in text
    assert br.research_findings_lines({}) == []


def test_question_window_by_date_time_and_words() -> None:
    w = br.question_window(
        "Warum hat Miner 1 am 05.09. um 14:17 hochgeschaltet?", NOW, CET
    )
    assert w is not None
    assert w[0] == datetime(2026, 9, 5, 11, 17, tzinfo=UTC)  # 14:17 CET - 2 h
    assert w[2] == "05.09.2026 14:17 ±2 h"
    day = br.question_window("Was war am 5.9.2026 los?", NOW, CET)
    assert day is not None and day[1] - day[0] == timedelta(days=1)
    # a date in the future of this year means last year
    dec = br.question_window("Warum am 24.12.?", NOW, CET)
    assert dec is not None and dec[2] == "24.12.2025"
    last = br.question_window("Warum laufen die Miner nicht?", NOW, CET)
    assert last is not None and last[2] == "letzte 24 Stunden"
    assert br.question_window("Wie hoch ist der Akku?", NOW, CET) is None


def test_decision_lines_explain_from_log_only(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        conn.execute(
            "INSERT INTO ha_decision_log (id, timestamp, block_id, miner, kind,"
            " from_state, to_state, rule_active, reason, soc_pct) VALUES"
            " ('a', '2026-09-05T15:29:00+00:00', '2026-09-05T15:20:00', 'miner1',"
            " 'mode', 'Standard', 'Eco', 'Regulär', 'Standard — regulär (SoC 99%)', 99)"
        )
        conn.execute(
            "INSERT INTO settings_history VALUES ('2026-09-01T00:00:00+00:00',"
            " 'sensor.mvp_saison_status', 'eco_ab_pct', '88.0', 'history')"
        )
        conn.commit()
        window = br.question_window("Warum am 05.09.?", NOW, CET)
        assert window is not None
        text = "\n".join(br.decision_lines(conn, window, CET))
        empty = br.decision_lines(
            conn,
            (NOW - timedelta(hours=24), NOW, "letzte 24 Stunden"),
            CET,
        )
    finally:
        conn.close()
    assert "05.09. 16:29 Miner 1: Standard → Eco; Regel: Regulär" in text
    assert "Ruhezustand" not in text
    assert "Eco ab 88 %" in text
    assert "Keine Moduswechsel in diesem Zeitraum." in "\n".join(empty)


def test_drop_reviewed_removes_known_repeats_only() -> None:
    points = [
        "Heizstab verhindert, dass der Akku 100 % erreicht.",
        "Neue Karte 'Halteband-Dauer' im Tab Forschung.",
        "Eco-Schwelle im Juni um 5 Punkte senken.",
    ]
    keep, dropped = br.drop_reviewed(points)
    assert keep == [points[2]]
    assert dropped == points[:2]
    assert "SCHON GEPRÜFT" in br.reviewed_lines()[0]


def test_decision_lines_skip_rest_jumps_and_date_the_reason(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        rows = [
            ("r", "2026-11-13T15:52:47+00:00", "rule", None, "R1 Stopp"),
            ("m1", "2026-11-13T21:30:56.01+00:00", "mode", "Standby", "Off"),
            ("m2", "2026-11-13T21:30:56.18+00:00", "mode", "Off", "Standby"),
            ("m3", "2026-11-13T22:00:00+00:00", "mode", "Standby", "Eco"),
        ]
        for rid, ts, kind, frm, to in rows:
            conn.execute(
                "INSERT INTO ha_decision_log (id, timestamp, block_id, miner, kind,"
                " from_state, to_state, rule_active, reason) VALUES"
                " (?, ?, ?, 'miner1', ?, ?, ?, 'R1 Stopp', 'SoC 69% < Stop 95%')",
                (rid, ts, ts[:19], kind, frm, to),
            )
        conn.commit()
        window = (
            datetime(2026, 11, 13, 12, tzinfo=UTC),
            datetime(2026, 11, 14, 0, tzinfo=UTC),
            "x",
        )
        text = "\n".join(br.decision_lines(conn, window, CET))
    finally:
        conn.close()
    assert "2 Sprünge nur zwischen Standby, Off und Idle" in text
    assert "Standby → Off" not in text
    assert "13.11. 23:00 Miner 1: Standby → Eco" in text
    assert "Watchdog, geschrieben 13.11. 16:52" in text


def test_local_time_follows_daylight_saving_without_fixed_zone() -> None:
    # Without a zone the system zone is used per date. Only the conversion
    # path is checked here: the result must equal datetime.astimezone().
    t = datetime(2026, 9, 5, 17, 29, tzinfo=UTC)
    assert br._local(t.isoformat(), None) == t.astimezone().strftime("%d.%m. %H:%M")


def test_thesis_lines_plan_and_findings_without_plant_data() -> None:
    open_points = {
        "deadline": "2027-01-15",
        "exported_at": "2026-11-14T08:00:00+00:00",
        "list_stand": "04.11.2026",
        "open_total": 2,
        "markers_offen": 3,
        "markers_pruefen": 1,
        "schedule": [
            {
                "week": "09.–15.11.",
                "write": "Kap. 4 System",
                "parallel": "Erhebung",
                "now": True,
            },
            {
                "week": "16.–22.11.",
                "write": "Kap. 5 Methodik",
                "parallel": "",
                "now": False,
            },
        ],
        "sections": [{"section": "Literatur", "items": ["x" * 300, "Körber (2019)"]}],
        "markers": [
            {"file": "kapitel/04_system.tex", "offen": 2, "pruefen": 9, "words": 6687},
            {"file": "anhang/b.tex", "offen": 0, "pruefen": 0, "words": 10},
        ],
    }
    cards = {
        "thesis": [{"group": "Limitationen", "title": "Winter", "text": "kein Mining"}]
    }
    text = "\n".join(br.thesis_lines(cards, open_points, NOW))
    assert "Abgabe 15.01.2027, noch 62 Tage" in text
    assert "DIESE WOCHE: Kap. 4 System (parallel: Erhebung)" in text
    assert "Kap. 5 Methodik" in text and "parallel: )" not in text
    assert "x" * 219 + "…" in text and "x" * 221 not in text
    assert "04_system 2/9/6687" in text and "b 0/0" not in text
    assert "[Limitationen] Winter: kein Mining" in text
    assert br.thesis_lines(None, None, NOW) == []


def test_thesis_lines_carry_the_sync_check_as_facts() -> None:
    sync = {
        "replaced": [
            {
                "file": "kapitel/04_system.tex",
                "line": 343,
                "section": "Saisonale Hausreserve",
                "adr": 28,
                "by": 33,
                "by_title": "Hausreserve-Formel",
            }
        ],
        "changed": [{"path": "mvp_auto.yaml", "entries": [{}, {}]}],
        "adr_uncited": [{"adr": 34, "title": "Protokoll", "date": "2026-11-14"}],
        "befunde": {
            "notes": [
                {
                    "id": "schaltwechsel",
                    "places": [
                        {
                            "file": "kapitel/04.tex",
                            "line": 9,
                            "state": "geaendert",
                            "stichtag": "2026-11-14",
                        }
                    ],
                }
            ],
            "missing": ["ueberschuss"],
        },
    }
    plan = [
        {
            "state": "jetzt",
            "title": "Veraltete Stellen",
            "items": [{}],
            "who": "Claude",
        },
        {
            "state": "wartet",
            "wait_until": "2026-11-17",
            "title": "Stellen belegen",
            "items": [{}],
            "who": "Claude",
        },
    ]
    open_points = {"deadline": "2027-01-15", "sync": sync, "plan": plan}
    text = "\n".join(br.thesis_lines(None, open_points, NOW))
    assert "- 1. [jetzt] Veraltete Stellen (1 offen; Claude)" in text
    # A waiting step names its date, so the model does not read it as work now.
    assert "- 2. [wartet bis 17.11.] Stellen belegen (1 offen; Claude)" in text
    assert "VERALTET 04_system:343 (Saisonale Hausreserve): zitiert ADR 028" in text
    assert "ZAHLEN GEÄNDERT: Befund schaltwechsel in 04.tex:9" in text
    assert "noch nicht im Text: ueberschuss" in text
    assert "mvp_auto.yaml (2 Einträge)" in text
    assert "ADR 034 Protokoll" in text
    # No sync block -> no heading without content.
    assert "STAND-ABGLEICH" not in "\n".join(
        br.thesis_lines(None, {"deadline": "2027-01-15", "sync": {}}, NOW)
    )


def test_thesis_lines_name_the_next_meeting_and_list_detail_steps() -> None:
    open_points = {
        "deadline": "2027-01-15",
        "sync": {},
        "plan": [
            {
                "key": "wallach",
                "title": "Fragen an Prof. Wallach",
                "who": "Artur mit Prof. Wallach",
                "state": "parallel",
                "items": [
                    {"text": "Ethikvotum nötig?", "where": "Prof. Wallach"},
                    {"text": "Titel", "where": "Hochschule", "siehe_auch": "1"},
                    {"text": "H2 streichen", "where": "f.tex:1", "am_zug": "Wallach"},
                ],
            }
        ],
    }
    # NOW is a Saturday or any day: the meeting is the next Wednesday.
    plain = "\n".join(br.thesis_lines(None, open_points, NOW))
    assert "Nächstes Gespräch mit Prof. Wallach: Mi" in plain
    assert "Ethikvotum" not in plain  # points only when asked for
    detail = "\n".join(br.thesis_lines(None, open_points, NOW, ("wallach",)))
    assert "    - Prof. Wallach: Ethikvotum nötig?" in detail
    assert "    - f.tex:1: H2 streichen [wartet auf Wallach]" in detail
    assert "Titel" not in detail  # counted elsewhere, not repeated


def test_freeze_lines_number_the_fixed_list() -> None:
    check = {
        "freeze": "2026-11-29",
        "days_left": 15,
        "meetings": ["2026-11-18", "2026-11-25"],
        "items": [
            {
                "text": "H2 streichen",
                "where": "f.tex:1",
                "am_zug": "Wallach",
                "quelle": "Präregistrierung",
            },
        ],
    }
    lines = br.freeze_lines(check)
    assert "Datenfreeze am 29.11.2026, noch 15 Tage" in lines[0]
    assert "Mi 18.11., Mi 25.11." in lines[0]
    assert (
        lines[1]
        == "  1. [am Zug: Wallach; Quelle: Präregistrierung; Ort: f.tex:1] H2 streichen"
    )
    assert "freeze_check fehlt" in br.freeze_lines(None)[0]
    # Only the freeze task gets the list.
    op = {"deadline": "2027-01-15", "sync": {}, "freeze_check": check}
    assert "VOR DEM DATENFREEZE" not in "\n".join(br.thesis_lines(None, op, NOW))
    assert "VOR DEM DATENFREEZE" in "\n".join(
        br.thesis_lines(None, op, NOW, with_freeze=True)
    )
