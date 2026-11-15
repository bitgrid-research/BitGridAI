"""Prose per chapter in the thesis plan: splitting, weeks, done rule, tracks."""

from __future__ import annotations

from datetime import date
from typing import Any

from src.data import thesis_sync as ts

ITEMS = [
    "Kap. 1 Aufbau, Kap. 2 Synthese, Kap. 3 Forschungslücke mit Vergleichstabelle,"
    " Kap. 4 Zusammenfassung, Kap. 8",
    r"Kurzfassung (drei sachliche Punkte stehen als \pruefen dort), Abstract",
    "Anh. C Texttabelle aus der tatsächlich gezeigten Fassung, Anh. F Volltext der"
    " Präregistrierung, Anh. H Codierleitfaden",
]
# (week, start, end, write, parallel) as in the schedule of the thesis.
SCHEDULE = [
    ("02.-08.11.", "2026-11-02", "2026-11-08", "Stichpunkte prüfen", "Export"),
    ("09.-15.11.", "2026-11-09", "2026-11-15", "Kap. 4 System (Prosa)", "Erhebung"),
    (
        "16.-22.11.",
        "2026-11-16",
        "2026-11-22",
        "Kap. 5 Methodik",
        "Kap. 4 an Wallach; Literaturrecherche zu Tonalität starten",
    ),
    ("23.-29.11.", "2026-11-23", "2026-11-29", "Kap. 2 Theorie", "Datenfreeze"),
    ("30.11.-06.12.", "2026-11-30", "2026-12-06", "Kap. 3 Forschungsstand", "x"),
    ("07.-13.12.", "2026-12-07", "2026-12-13", "Kap. 6 Ergebnisse", "x"),
    ("14.-20.12.", "2026-12-14", "2026-12-20", "Kap. 7 Diskussion", "x"),
    (
        "21.12.-03.01.",
        "2026-12-21",
        "2027-01-03",
        "Kap. 1, 8, Kurzfassung/Abstract, Anhang",
        "x",
    ),
]
WAITING_04 = {
    "file": "kapitel/04_system.tex",
    "line": 462,
    "kind": "pruefen",
    "text": "Teilbeleg",
    "termin": "2026-11-17",
}


def _data(today: date, markers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    iso = today.isoformat()
    return {
        "schedule": [
            {
                "week": w,
                "start": s,
                "end": e,
                "write": wr,
                "parallel": p,
                "now": s <= iso <= e,
            }
            for w, s, e, wr, p in SCHEDULE
        ],
        "sections": [
            {"section": "Schreiben (Artur, nach der Zuordnung)", "items": ITEMS}
        ],
        "marker_items": [WAITING_04] if markers is None else markers,
        "markers": [
            {"file": "kapitel/04_system.tex", "prosa": 15},
            {"file": "kapitel/05_methodik.tex", "prosa": 12},
        ],
        "literatur_fragen": ["Formalität", "Erklärungen", "Fachsprache"],
        "sync": {},
    }


def _no_drafts(data: dict[str, Any]) -> dict[str, Any]:
    r"""Same data without \prosa drafts in any chapter."""
    data["markers"] = [dict(m, prosa=0) for m in data["markers"]]
    return data


def _by_key(data: dict[str, Any], today: date) -> dict[str, dict[str, Any]]:
    return {s["key"]: s for s in ts.plan(data, today)}


def test_split_pieces_per_chapter_outside_brackets() -> None:
    assert ts.split_pieces(ITEMS[0]) == [
        "Kap. 1 Aufbau",
        "Kap. 2 Synthese",
        "Kap. 3 Forschungslücke mit Vergleichstabelle",
        "Kap. 4 Zusammenfassung",
        "Kap. 8",
    ]
    assert ts.split_pieces(ITEMS[1]) == [
        r"Kurzfassung (drei sachliche Punkte stehen als \pruefen dort)",
        "Abstract",
    ]
    assert len(ts.split_pieces(ITEMS[2])) == 3
    # A comma inside brackets or before a non-unit does not split.
    assert len(ts.split_pieces("Kap. 1 Aufbau (siehe Kap. 2, Kap. 3), Kap. 4")) == 2
    assert ts.split_pieces("Kap. 1 Aufbau, dann Feinschliff") == [
        "Kap. 1 Aufbau, dann Feinschliff"
    ]


def test_piece_unit_names_key_label_and_rest() -> None:
    assert ts.piece_unit("Kap. 3 Forschungslücke") == (
        "kap:3",
        "Kap. 3",
        "Forschungslücke",
    )
    assert ts.piece_unit("Anh. F Volltext") == ("anh:F", "Anh. F", "Volltext")
    assert ts.piece_unit("Anhang H") == ("anh:H", "Anh. H", "")
    assert ts.piece_unit("Kap. 8") == ("kap:8", "Kap. 8", "")
    assert ts.piece_unit("Abstract") == ("abstract", "Abstract", "")
    assert ts.piece_unit("Irgendwas") is None
    assert ts.piece_unit("Kap. 12 zu lang") is None


def test_search_questions_reads_the_numbered_items_of_the_section() -> None:
    md = (
        "# T\n\n## Andere\n\n1. nicht diese\n\n"
        "## Nächste Suchfragen (noch keine Quellen)\n\n"
        "1. Erste `Frage`.\n2. **Zweite** Frage.\n3. Dritte.\n4. Vierte.\n\n"
        "## Ende\n1. auch nicht\n"
    )
    assert ts.search_questions(md) == ["Erste Frage.", "Zweite Frage.", "Dritte."]
    assert ts.search_questions(md, limit=1) == ["Erste Frage."]
    assert ts.search_questions("") == []


def test_plan_today_chapter_four_is_done_and_the_appendices_are_due() -> None:
    today = date(2026, 11, 14)
    # With 15 drafts by Claude left, chapter 4 is "revise the draft", now.
    drafted = _by_key(_data(today), today)["prosa"]
    assert drafted["title"] == "Kap. 4: Entwurf überarbeiten"
    assert drafted["state"] == "jetzt" and drafted["prosa"] == 15
    by = _by_key(_no_drafts(_data(today)), today)
    # Chapter 4 has only a waiting marker left and no draft: its prose is done,
    # the unticked checkbox is only mentioned.
    prosa = by["prosa"]
    assert prosa["state"] == "erledigt" and prosa["items"] == []
    assert "keine offenen Marker mehr" in prosa["why"]
    assert "Kap. 4 Zusammenfassung" in prosa["why"]
    assert by["belegen"]["state"] == "wartet"
    # The appendices that need no results are due whatever the week; C is done.
    fh = by["anhang_fh"]
    assert fh["title"] == "Anhang F und H: Prosa schreiben"
    assert {i["where"] for i in fh["items"]} == {"Anh. F", "Anh. H"}
    assert "Anh. C ist erledigt" in fh["why"]
    assert [k for k, s in by.items() if s["state"] == "jetzt"] == [
        "wallach",
        "anhang_fh",
    ]
    # The research on tone starts with the schedule row that names it.
    lit = by["literatur_tonalitaet"]
    assert lit["state"] == "bereit" and len(lit["items"]) == 3
    # The research on tone is done (14.11.2026): no "biggest risk" any more.
    assert "Größtes Risiko" not in lit["why"]


def test_plan_later_chapters_wait_for_their_own_week() -> None:
    today = date(2026, 11, 14)
    steps = ts.plan(_data(today), today)
    keys = [s["key"] for s in steps]
    rows = [s for s in steps if s["key"].startswith("prosa_")]
    assert [s["title"] for s in rows] == [
        "Kap. 5: Entwurf überarbeiten",
        "Kap. 2: Prosa schreiben",
        "Kap. 3: Prosa schreiben",
        "Kap. 6: Prosa schreiben",
        "Kap. 7: Prosa schreiben",
        "Kap. 1, 8, Kurzfassung, Abstract, Anhang: Prosa schreiben",
    ]
    # Target week, not a lock (Artur, 15.11.2026); results wait for the freeze.
    assert [s["state"] for s in rows] == [
        "bereit",
        "bereit",
        "bereit",
        "gesperrt",
        "bereit",
        "bereit",
    ]
    texts = [[i["text"] for i in s["items"]] for s in rows]
    assert texts[:5] == [
        [],
        ["Synthese"],
        ["Forschungslücke mit Vergleichstabelle"],
        [],
        [],
    ]
    assert {i["where"] for i in rows[5]["items"]} == {
        "Kap. 1",
        "Kap. 8",
        "Kurzfassung",
        "Abstract",
    }
    # Right behind this week's loop, before research and the deadlines
    # (Artur, 15.11.2026: prose stood too far back).
    assert keys.index("prosa_2") < keys.index("spaeter_befunde")
    assert keys.index("prosa_7") < keys.index("literatur")
    assert keys.index("prosa_7") < keys.index("fristen")


def test_plan_chapter_five_week_runs_the_pipeline_and_the_research() -> None:
    today = date(2026, 11, 16)
    markers = [
        WAITING_04,
        {"file": "kapitel/05_methodik.tex", "line": 3, "kind": "offen", "text": "O5"},
        {"file": "kapitel/05_methodik.tex", "line": 9, "kind": "pruefen", "text": "P5"},
    ]
    by = _by_key(_data(today, markers), today)
    assert by["prosa"]["title"] == "Kap. 5: Entwurf überarbeiten"
    assert by["klaeren"]["state"] == "jetzt"
    # 12 drafts to revise: not done; behind "klaeren" in the pipeline.
    assert by["prosa"]["state"] == "offen" and by["prosa"]["prosa"] == 12
    assert "12 Stellen mit" in by["prosa"]["why"]
    # Open questions: the research can start any time.
    assert by["literatur_tonalitaet"]["state"] == "bereit"
    assert by["literatur_tonalitaet"]["title"] == "Literaturrecherche"
    assert by["anhang_fh"]["state"] == "jetzt"
    # The week of chapter 4 is over, but its 15 drafts are left: still due.
    assert by["prosa_1"]["state"] == "jetzt"
    no = _by_key(_no_drafts(_data(today, markers)), today)
    assert no["prosa"]["state"] == "erledigt"
    assert "2 Marker stehen in den Schritten davor" in no["prosa"]["why"]
    assert no["prosa_1"]["state"] == "erledigt"


def test_plan_overdue_chapter_returns_when_its_termin_has_passed() -> None:
    today = date(2026, 11, 18)
    by = _by_key(_data(today), today)
    row = by["prosa_1"]  # chapter 4, week over, marker no longer waiting
    assert row["state"] == "jetzt"
    assert [i["where"] for i in row["items"]] == ["04_system.tex:462"]
    assert "wartet_bis" not in row["items"][0]


def test_plan_prosa_unit_without_a_schedule_row_goes_to_sonstiges() -> None:
    today = date(2026, 11, 14)
    data = _data(today)
    data["sections"] = [
        {"section": "Schreiben", "items": ["Kap. 9 Anhang X, ohne Ziel"]}
    ]
    by = _by_key(data, today)
    # No schedule row names chapter 9: the point is kept, not dropped.
    assert by["sonstiges"]["items"] == [
        {"text": "Anhang X, ohne Ziel", "where": "Kap. 9"}
    ]


def test_plain_cleans_latex_leftovers() -> None:
    raw = (
        r"Cohens $\kappa$ z.\ B.\ Stufe in \cref{fig:x}, \texttt{a\_b},"
        r" $$ a~b \rightarrow c"
    )
    assert ts._plain(raw) == "Cohens Kappa z. B. Stufe in (Verweis), a_b, a b -> c"


def test_plan_current_prose_without_own_points_is_done_despite_open_markers() -> None:
    today = date(2026, 11, 14)
    markers = [
        {"file": "kapitel/04_system.tex", "line": 5, "kind": "offen", "text": "O"},
        {"file": "kapitel/04_system.tex", "line": 9, "kind": "pruefen", "text": "P"},
    ]
    data = _no_drafts(_data(today, markers))
    data["sections"] = []  # the checkbox for chapter 4 is ticked
    by = _by_key(data, today)
    assert by["prosa"]["state"] == "erledigt"
    assert "2 Marker stehen in den Schritten davor" in by["prosa"]["why"]
    assert by["klaeren"]["state"] == "jetzt"


def test_plan_appendix_with_only_decisions_waits_for_artur() -> None:
    today = date(2026, 11, 14)
    markers = [
        {"file": "anhang/h_x.tex", "line": 3, "kind": "offen", "text": "Rater"},
    ]
    data = _data(today, markers)
    data["sections"] = [
        {"section": "Schreiben", "items": ["Anh. H Entwurf steht seit gestern"]}
    ]
    fh = _by_key(data, today)["anhang_fh"]
    assert fh["state"] == "wartet" and fh["wait_who"] == "Artur"
    assert {i["am_zug"] for i in fh["items"]} == {"Artur"}
    # A point still open for Claude keeps the step "jetzt".
    markers.append(
        {"file": "anhang/h_x.tex", "line": 4, "kind": "pruefen", "text": "Q"}
    )
    fh = _by_key(_data(today, markers), today)["anhang_fh"]
    assert fh["state"] == "jetzt"


def test_release_check_needs_all_four_conditions() -> None:
    ok = {
        "check_tex": 0,
        "uncommitted": [],
        "unpushed": 0,
        "log": {"errors": 0, "undefined": 0},
    }
    assert ts.release_check(None, False) == {}
    assert ts.release_check(ok, False) == {"items": [], "state": "erledigt"}
    bad = dict(
        ok,
        check_tex=4,
        uncommitted=[" M a", " M b"],
        unpushed=3,
        github_differs=True,
    )
    got = ts.release_check(bad, True)
    assert got["state"] == "offen"
    assert [i["text"] for i in got["items"]] == [
        "check_tex: 4 Befunde",
        "Abgleich: neue Meldung (ersetzte ADR oder geänderte Zahlen)",
        "2 Dateien nicht committet",
        "3 Commits nicht gepusht",
        "GitHub-Stand weicht ab",
    ]
    # No main.log: compilation is unchecked and does not block.
    nolog = ts.release_check(dict(ok, log=None), False)
    assert nolog["state"] == "erledigt" and "ungeprüft" in nolog["note"]
    assert (
        ts.release_check(dict(ok, log={"errors": 2, "undefined": 1}), False)["state"]
        == "offen"
    )


def test_release_check_hints_do_not_block() -> None:
    ok = {
        "check_tex": 0,
        "uncommitted": [],
        "unpushed": 0,
        "log": {"errors": 0, "undefined": 0},
    }
    got = ts.release_check(ok, False, ["8 zitierte Dateien seit dem Stand geändert"])
    assert got["state"] == "erledigt"
    assert "8 zitierte Dateien" in got["note"]


def test_plan_wallach_meeting_is_now_with_agenda_and_questions() -> None:
    today = date(2026, 11, 14)
    data = _data(today)
    data["sections"] = [
        {"section": "Prof. Wallach (mit Gliederung)", "items": ["Titel klären"]},
        {
            "section": "Prüfungsamt und Hochschule",
            "items": ["Pflichtumfang mit Wallach", "Anmeldung (Termin 20.11.)"],
        },
    ]
    steps = ts.plan(data, today)
    by = {s["key"]: s for s in steps}
    w = by["wallach"]
    assert w["phase"] == ts.PHASE_WEEK
    assert w["state"] == "jetzt" and w["who"] == "Artur mit Prof. Wallach"
    # Saturday 14.11.: the agenda for Wednesday 18.11. is the first point.
    assert w["items"][0]["frist"] == "2026-11-18"
    assert w["items"][0]["text"].startswith("Agenda vorbereiten")
    assert [i["text"] for i in w["items"][1:]] == [
        "Titel klären",
        "Pflichtumfang mit Wallach (siehe auch Hochschule)",
    ]
    assert [bool(i.get("siehe_auch")) for i in w["items"]] == [False, False, True]
    # Not in "Vorbereiten", and still counted once under Hochschule.
    assert all("Titel" not in i["text"] for i in by["naechste"]["items"])
    assert len(by["fristen"]["items"]) == 2


def test_plan_shows_the_prosa_note_for_every_chapter_and_the_appendices() -> None:
    today = date(2026, 11, 14)
    data = _data(today)
    data["markers"] += [{"file": "anhang/h_codierleitfaden.tex", "prosa": 3}]
    by = _by_key(data, today)
    # Later chapter, week not started: the note is there, state unaffected.
    assert (
        r"12 Stellen mit \prosa (Entwurf, von dir anzupassen)" in by["prosa_2"]["why"]
    )
    assert by["prosa_2"]["state"] == "bereit"
    assert (
        r"3 Stellen mit \prosa (Entwurf, von dir anzupassen)" in by["anhang_fh"]["why"]
    )
    assert r"15 Stellen mit \prosa (Entwurf" in by["prosa"]["why"]


def test_wait_reason_reads_the_marker_text() -> None:
    assert ts.wait_reason("Nachtrag schließen") == "Wallach"
    assert ts.wait_reason("mit Prof. Wallach klären") == "Wallach"
    assert ts.wait_reason("Ankerbeispiele aus den Transkripten") == "Daten"
    assert ts.wait_reason("Wer codiert? Zweite Person") == "Person"
    assert ts.wait_reason("Rater benennen (zwei)") == "Person"
    assert ts.wait_reason("Maß festlegen") is None


def test_plain_resolves_known_chapter_labels() -> None:
    labels = ts.label_units(
        {
            "kapitel/06_ergebnisse.tex": r"\chapter{E}\label{chap:ergebnisse}",
            "anhang/h_codierleitfaden.tex": r"\label{anhang:codierleitfaden}",
        }
    )
    assert labels == {
        "chap:ergebnisse": "Kap. 6",
        "anhang:codierleitfaden": "Anhang H",
    }
    raw = r"Ergebnis in \cref{chap:ergebnisse} und \cref{fig:x}, \cref{anhang:codierleitfaden}"
    assert ts._plain(raw, labels) == "Ergebnis in Kap. 6 und (Verweis), Anhang H"


def test_plan_appendix_waiting_on_outside_inputs_hands_on_jetzt() -> None:
    today = date(2026, 11, 14)
    h = "anhang/h_codierleitfaden.tex"
    markers = [
        {
            "file": "anhang/f_p.tex",
            "line": 1,
            "kind": "offen",
            "text": "Nachtrag schließen",
        },
        {"file": h, "line": 2, "kind": "offen", "text": "Wer codiert?"},
        {"file": h, "line": 3, "kind": "offen", "text": "Rater benennen"},
        {
            "file": h,
            "line": 4,
            "kind": "offen",
            "text": "Ankerbeispiele aus Transkripten",
        },
    ]
    data = _data(today, markers)
    data["sections"] = [
        {"section": "Schreiben", "items": ["Anh. H Codierleitfaden: Entwurf steht"]},
        {"section": "Prof. Wallach", "items": ["Titel klären"]},
    ]
    by = _by_key(data, today)
    fh = by["anhang_fh"]
    assert fh["title"] == "Anhang F und H: offene Entscheidungen"
    assert fh["state"] == "wartet" and fh["wait_who"] == "Wallach, Person, Daten"
    # The summary line of offene_punkte.md is a subtitle, not a point.
    assert len(fh["items"]) == 4 and "Sammelzeile Anh. H" in fh["why"]
    # The Nachtrag point also shows in the Wallach list, not counted there.
    w = [i for i in by["wallach"]["items"] if i.get("siehe_auch")]
    assert [i["text"] for i in w] == ["Nachtrag schließen (siehe auch Schritt 7)"]
    assert "jetzt" not in fh["state"]


def test_parse_frist_and_due_window() -> None:
    today = date(2026, 11, 14)
    text = "Annika erinnern (Woche 16.–20.11., Frist 19.11.): verlängern"
    assert ts.parse_frist(text, today) == date(2026, 11, 19)
    assert ts.parse_frist("ohne", today) is None
    assert ts.parse_frist("Frist 31.02.", today) is None
    item = {"frist": "2026-11-19"}
    assert not ts.frist_due(item, date(2026, 11, 15))  # 4 days before
    assert ts.frist_due(item, date(2026, 11, 16))  # 3 days before
    assert ts.frist_due(item, date(2026, 11, 20))  # overdue


def _erhebung(today: date) -> dict[str, Any]:
    data = _no_drafts(_data(today, []))
    data["sections"] = [
        {
            "section": "Sitzungsprotokoll-Export (nur aus dem Labornetz)",
            "items": [
                "Screenshots der Erklärkarte A und B (Termin 16./17.11.2026)",
                "Eigenes Foto eines Avalon-Q-Miners",
                "Sitzungsexport VP01–VP10: Mo/Di 16./17.11.2026",
            ],
        },
        {
            "section": "Sitzungsprotokoll-Export (Fragen)",
            "items": ["Reihenfolge A/B je Person", "Sitzungsdauer"],
        },
        {
            "section": "SoSci-Export und Annika Dietrich",
            "items": [
                "Antwortcodes SUS und TiA in SoSci: umcodieren",
                "Annika erinnern (Woche 16.–20.11., Frist 19.11.): verlängern",
                "Datum der Korrektur von Aufgabe 1 in SoSci",
                "Finale Fragebogen-PDF (Anh. B)",
                "Rekrutierungsweg (Kap. 7)",
                "Wer codiert Teach-Back? Wer sind die zwei Rater für FF2?",
            ],
        },
        {
            "section": "Auswertung (nach dem Datenfreeze)",
            "items": [
                "`src/sim/study_analysis.py` auf within umstellen",
                "Kap. 6 vollständig; Kap. 7 Einordnung",
            ],
        },
    ]
    return data


def test_plan_groups_the_survey_and_routes_the_analysis() -> None:
    today = date(2026, 11, 14)
    by = _by_key(_erhebung(today), today)
    par = by["parallel"]["items"]
    groups = [i["group"] for i in par]
    assert groups == sorted(
        groups, key=[ts.GROUP_LAB, ts.GROUP_SOSCI, ts.GROUP_MEDIA].index
    )
    lab = [i for i in par if i["group"] == ts.GROUP_LAB]
    # The questions of the export inherit its Termin.
    assert {i["text"] for i in lab} == {
        "Sitzungsexport VP01–VP10: Mo/Di 16./17.11.2026",
        "Reihenfolge A/B je Person",
        "Sitzungsdauer",
    }
    assert {i.get("wartet_bis") for i in lab} == {"2026-11-17"}
    sosci = {i["text"]: i for i in par if i["group"] == ts.GROUP_SOSCI}
    assert sosci["Datum der Korrektur von Aufgabe 1 in SoSci"]["am_zug"] == "Annika"
    assert sosci["Finale Fragebogen-PDF (Anh. B)"]["am_zug"] == "Annika"
    assert "am_zug" not in sosci["Rekrutierungsweg (Kap. 7)"]
    coder = [i for i in par if i["text"].startswith("Wer codiert")]
    assert coder[0]["siehe_auch"] and "Schritt 7" in coder[0]["text"]
    media = [i["text"] for i in par if i["group"] == ts.GROUP_MEDIA]
    assert len(media) == 2
    # The analysis is prepared now; only Kap. 6/7 wait for the freeze.
    prep = by["auswertung_vorb"]
    assert prep["state"] == "bereit" and prep["who"] == "Dev"
    assert len(prep["items"]) == 2
    assert [i["text"] for i in by["freeze"]["items"]] == [
        "Kap. 6 vollständig; Kap. 7 Einordnung"
    ]
    # The Frist is 5 days away: not due yet, the step stays parallel.
    assert by["parallel"]["state"] == "parallel"


def test_plan_due_frist_makes_the_step_jetzt() -> None:
    today = date(2026, 11, 17)
    by = _by_key(_erhebung(today), today)
    assert by["parallel"]["state"] == "jetzt"
    reminder = [i for i in by["parallel"]["items"] if i.get("frist")]
    assert reminder[0]["frist"] == "2026-11-19"


def test_next_meeting_is_the_coming_wednesday() -> None:
    assert ts.next_meeting(date(2026, 11, 14)) == date(2026, 11, 18)  # Sa
    assert ts.next_meeting(date(2026, 11, 18)) == date(2026, 11, 18)  # Mi
    assert ts.next_meeting(date(2026, 11, 19)) == date(2026, 11, 25)  # Do


def test_freeze_check_lists_what_is_due_before_the_freeze() -> None:
    today = date(2026, 11, 14)
    data = _data(
        today,
        [
            {
                "file": "anhang/f_praeregistrierung.tex",
                "line": 278,
                "kind": "offen",
                "text": "Offene Punkte des Nachtrags schließen",
            },
            {
                "file": "kapitel/05_methodik.tex",
                "line": 9,
                "kind": "offen",
                "text": "X",
            },
        ],
    )
    data["sections"] = [
        {"section": "SoSci-Export", "items": ["Antwortcodes umcodieren, Nachtrag 2"]},
        {"section": "Prof. Wallach (Gliederung)", "items": ["H2 streichen, Nachtrag"]},
        {"section": "Artur", "items": ["ohne Bezug"]},
    ]
    code = [{"text": "TiA: Umpolung festlegen", "where": "study_sosci.py"}]
    fc = ts.freeze_check(data, today, code)
    # Freeze = end of the row whose parallel column names it; Wednesdays up to it.
    assert fc["freeze"] == "2026-11-29" and fc["days_left"] == 15
    assert fc["meetings"] == ["2026-11-18", "2026-11-25"]
    got = [(i["quelle"], i["am_zug"], i["text"]) for i in fc["items"]]
    assert got == [
        ("Präregistrierung", "Wallach", "Offene Punkte des Nachtrags schließen"),
        ("offene Punkte", "Artur", "Antwortcodes umcodieren, Nachtrag 2"),
        ("offene Punkte", "Wallach", "H2 streichen, Nachtrag"),
        ("Auswertungscode", "Artur", "TiA: Umpolung festlegen"),
    ]
    # After the last meeting before the freeze none is left.
    assert ts.freeze_check(data, date(2026, 11, 26))["meetings"] == []
