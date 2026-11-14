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
    by = _by_key(_data(today), today)
    # Chapter 4 has only a waiting marker left: its prose is done, \prosa and
    # the unticked checkbox are only mentioned.
    prosa = by["prosa"]
    assert prosa["state"] == "erledigt" and prosa["items"] == []
    assert "keine offenen Marker mehr" in prosa["why"]
    assert "15 Stellen mit" in prosa["why"]
    assert "Kap. 4 Zusammenfassung" in prosa["why"]
    assert by["belegen"]["state"] == "wartet"
    # The appendices that need no results are due whatever the week; C is done.
    fh = by["anhang_fh"]
    assert fh["title"] == "Anhang F und H: Prosa schreiben"
    assert {i["where"] for i in fh["items"]} == {"Anh. F", "Anh. H"}
    assert "Anh. C ist erledigt" in fh["why"]
    assert [k for k, s in by.items() if s["state"] == "jetzt"] == ["anhang_fh"]
    # The research on tone starts with the schedule row that names it.
    lit = by["literatur_tonalitaet"]
    assert lit["state"] == "spaeter" and len(lit["items"]) == 3
    assert "Start laut Zeitplan: 16.11." in lit["why"]


def test_plan_later_chapters_wait_for_their_own_week() -> None:
    today = date(2026, 11, 14)
    steps = ts.plan(_data(today), today)
    keys = [s["key"] for s in steps]
    rows = [s for s in steps if s["key"].startswith("prosa_")]
    assert [s["title"] for s in rows] == [
        "Kap. 5: Prosa schreiben",
        "Kap. 2: Prosa schreiben",
        "Kap. 3: Prosa schreiben",
        "Kap. 6: Prosa schreiben",
        "Kap. 7: Prosa schreiben",
        "Kap. 1, 8, Kurzfassung, Abstract, Anhang: Prosa schreiben",
    ]
    assert {s["state"] for s in rows} == {"spaeter"}  # not "wartet": no Termin
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
    # They sit behind "Befunde später übernehmen" and before the deadlines.
    assert keys.index("spaeter_befunde") < keys.index("prosa_2")
    assert keys.index("prosa_7") < keys.index("fristen")


def test_plan_chapter_five_week_runs_the_pipeline_and_the_research() -> None:
    today = date(2026, 11, 16)
    markers = [
        WAITING_04,
        {"file": "kapitel/05_methodik.tex", "line": 3, "kind": "offen", "text": "O5"},
        {"file": "kapitel/05_methodik.tex", "line": 9, "kind": "pruefen", "text": "P5"},
    ]
    by = _by_key(_data(today, markers), today)
    assert by["prosa"]["title"] == "Kap. 5: Prosa schreiben"
    assert by["klaeren"]["state"] == "jetzt"
    # No checkbox of its own: rated alone, the markers sit in the steps before.
    assert by["prosa"]["state"] == "erledigt"
    assert "2 Marker stehen in den Schritten davor" in by["prosa"]["why"]
    assert "12 Stellen mit" in by["prosa"]["why"]
    assert by["literatur_tonalitaet"]["state"] == "jetzt"
    assert by["anhang_fh"]["state"] == "jetzt"
    # The week of chapter 4 is over: only its waiting marker is left, so done.
    assert by["prosa_1"]["state"] == "erledigt"


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
    data = _data(today, markers)
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
        "unpushed": {"origin": 0, "overleaf": 0},
        "log": {"errors": 0, "undefined": 0},
    }
    assert ts.release_check(None, False) == {}
    assert ts.release_check(ok, False) == {"items": [], "state": "erledigt"}
    bad = dict(
        ok,
        check_tex=4,
        uncommitted=[" M a", " M b"],
        unpushed={"origin": 3, "overleaf": 0},
    )
    got = ts.release_check(bad, True)
    assert got["state"] == "offen"
    assert [i["text"] for i in got["items"]] == [
        "check_tex: 4 Befunde",
        "Abgleich: neue Meldung (ersetzte ADR oder geänderte Zahlen)",
        "2 Dateien nicht committet",
        "3 Commits nicht gepusht (origin)",
    ]
    # No main.log: compilation is unchecked and does not block.
    nolog = ts.release_check(dict(ok, log=None), False)
    assert nolog["state"] == "erledigt" and "ungeprüft" in nolog["note"]
    assert (
        ts.release_check(dict(ok, log={"errors": 2, "undefined": 1}), False)["state"]
        == "offen"
    )
