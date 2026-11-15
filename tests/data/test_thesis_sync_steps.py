"""Plan steps added on 15.11.2026 (synthetic data only, no thesis text)."""

from __future__ import annotations

from datetime import date
from typing import Any

from src.data import thesis_sync as ts
from tests.data.test_thesis_sync_prosa import _by_key, _data

TODAY = date(2026, 11, 15)  # Sunday; next meeting Wednesday 18.11.

SUMMARY = r"""
\section{Introduction}
% Wortbudget ca. 600; entspricht \cref{chap:einleitung}
One two three four five.
\section{Theory}
% Wortbudget ca. 550; entspricht \cref{chap:theorie}
\section{Related}
% Wortbudget ca. 400; entspricht \cref{chap:forschungsstand}
\section{System}
% Wortbudget ca. 900; entspricht \cref{chap:system}
\section{Method}
% Wortbudget ca. 900; entspricht \cref{chap:methodik}
\section{Results}
% Wortbudget ca. 900; entspricht \cref{chap:ergebnisse}
\section{Discussion}
% Wortbudget ca. 850; entspricht \cref{chap:diskussion}
\section{Conclusion}
% Wortbudget ca. 300; entspricht \cref{chap:fazit}
"""
LABELS = {
    "chap:einleitung": 1,
    "chap:theorie": 2,
    "chap:forschungsstand": 3,
    "chap:system": 4,
    "chap:methodik": 5,
    "chap:ergebnisse": 6,
    "chap:diskussion": 7,
    "chap:fazit": 8,
}


def _with(**extra: Any) -> dict[str, Any]:
    data = _data(TODAY)
    data.update(extra)
    return data


def test_summary_parts_read_budget_chapter_and_words() -> None:
    parts = ts.summary_parts(SUMMARY, LABELS)
    assert [p["chapter"] for p in parts] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert sum(p["budget"] for p in parts if p["chapter"] in (2, 3, 4, 5)) == 2750
    assert sum(p["budget"] for p in parts if p["chapter"] in (1, 6, 7, 8)) == 2650
    assert parts[0]["words"] == 5  # comment line not counted
    assert ts.summary_parts(SUMMARY, LABELS, lambda t: 7)[1]["words"] == 7


def test_chapter_labels_from_chapter_files() -> None:
    texts = {"kapitel/05_methodik.tex": r"\chapter{M}\label{chap:methodik}"}
    assert ts.chapter_labels(texts) == {"chap:methodik": 5}


def test_summary_step_waits_for_chapter_prose_and_groups_halves() -> None:
    parts = ts.summary_parts(SUMMARY, LABELS)
    by = _by_key(_with(summary_parts=parts), TODAY)
    s = by["summary"]
    assert s["title"] == "Extended Summary (Anhang A): 5 von 5.000 Wörtern"
    # No chapter prose is done in the synthetic data: nothing to write yet.
    assert s["state"] == "wartet" and s["wait_who"] == "Kapitelprosa"
    assert s["offen"] == 8 and "prosa" not in s
    groups = list(dict.fromkeys(i["group"] for i in s["items"]))
    assert groups == [
        "Teil zu Kap. 2–5 (Soll 2.750 Wörter)",
        "Teil zu Kap. 1 und 6–8 (Soll 2.650 Wörter)",
    ]


def test_summary_part_is_ready_once_its_chapter_is_done() -> None:
    parts = ts.summary_parts(SUMMARY, LABELS)
    data = _with(summary_parts=parts, marker_items=[])
    data["markers"] = [dict(m, prosa=0) for m in data["markers"]]
    by = _by_key(data, TODAY)
    s = by["summary"]
    ready = [i["where"] for i in s["items"] if i.get("bereit")]
    assert ready == ["Kap. 4"] and s["state"] == "bereit"


def test_literature_gaps_need_a_bib_cite_and_no_literature_offen() -> None:
    texts = {
        "kapitel/02_theorie.tex": "\\section{Vertrauen}\\cite{A}\n"
        "\\section{Sprachstil, Ton}\n\\item \\offen{Literaturlücke: keine Quellen}\n"
        "% \\cite{B}\n\\section{Usability}\\cite{B}\n",
        "kapitel/03_forschungsstand.tex": "\\cite{B} \\offen{Tabelle bauen}",
    }
    gaps = ts.literature_gaps(texts, {"A", "B"})
    assert gaps == [
        {
            "text": "zitiert noch keine Quelle aus references.bib",
            "where": "Kap. 2, Sprachstil",
        },
        {"text": "Literaturlücke: keine Quellen", "where": "Kap. 2, Sprachstil"},
    ]


def test_literature_is_not_done_while_the_text_has_gaps() -> None:
    gap = {"text": "Literaturlücke", "where": "Kap. 2, Sprachstil"}
    by = _by_key(_with(literatur_fragen=[], literatur_luecken=[gap]), TODAY)
    assert by["literatur_tonalitaet"]["state"] == "bereit"
    assert by["literatur"]["state"] == "bereit"
    assert by["literatur"]["items"][0]["siehe_auch"]
    by = _by_key(_with(literatur_fragen=[], literatur_luecken=[]), TODAY)
    assert by["literatur_tonalitaet"]["state"] == "erledigt"
    assert by["literatur"]["state"] == "erledigt"


def test_hochschule_points_move_to_their_own_steps() -> None:
    sections = [
        {
            "section": "Prof. Wallach (Gliederung)",
            "items": ["Extended Summary (Anhang A): Gewichtung abstimmen"],
        },
        {
            "section": "Prüfungsamt und Hochschule",
            "items": [
                "Extended Summary (Anhang A, Pflicht)",
                "Kolloquium (20 Min. Vortrag)",
                "Anlagen zur elektronischen Abgabe",
                "Anhang J „Einsatz von KI-Werkzeugen“ vervollständigen",
                "Titel festlegen",
                "Deckblatt (Frist 10.12.)",
            ],
        },
    ]
    by = _by_key(_with(sections=sections), TODAY)
    assert [i["text"] for i in by["fristen"]["items"]] == [
        "Deckblatt (Frist 10.12.)",
        "Titel festlegen",
    ]
    assert by["fristen"]["state"] == "bereit"
    assert "Sammelpunkt" in by["summary"]["why"]
    assert by["kolloquium"]["state"] == "bereit"
    assert by["kolloquium"]["items"][-1]["text"] == "Kolloquium (20 Min. Vortrag)"
    assert by["anlagen"]["state"] == "bereit"
    assert {i["frist"] for i in by["anlagen"]["items"]} == {"2027-01-10"}
    assert by["anhang_j"]["items"][-1]["text"].startswith("Anhang J")
    # The Wallach question about the summary stays a Wallach question.
    assert any("Gewichtung" in i["text"] for i in by["wallach"]["items"])


def test_anlagen_are_due_three_days_before_the_frist() -> None:
    sections = [{"section": "Prüfungsamt und Hochschule", "items": ["Anlagen planen"]}]
    day = date(2027, 1, 7)
    data = _data(day)
    data["sections"] = sections
    assert _by_key(data, day)["anlagen"]["state"] == "jetzt"


def test_kolloquium_and_anlagen_done_without_their_checkbox() -> None:
    by = _by_key(_with(sections=[]), TODAY)
    assert by["kolloquium"]["state"] == "erledigt" and not by["kolloquium"]["items"]
    assert by["anlagen"]["state"] == "erledigt"


def test_anhang_j_runs_along_with_its_markers() -> None:
    marker = {
        "file": "anhang/j_ki_werkzeuge.tex",
        "line": 32,
        "kind": "pruefen",
        "text": "Zeitraum und Umfang angeben.",
    }
    by = _by_key(_with(marker_items=[marker]), TODAY)
    j = by["anhang_j"]
    assert j["state"] == "parallel" and j["items"][0]["am_zug"] == "Claude"
    assert "nach jeder Sitzung" in j["why"]


def test_changed_text_sources_and_lab_deploy_are_work_for_now() -> None:
    sync = {
        "changed": [
            {
                "path": "src/ha/config/packages/mvp_auto.yaml",
                "changed": "2026-11-15",
                "entries": [{}, {}],
            },
            {"path": "scripts/other.py", "changed": "2026-11-15", "entries": [{}]},
        ]
    }
    lab = {"last_deploy": "2026-11-02T10:00:00+00:00", "locked": False}
    by = _by_key(_with(sync=sync, lab_guard=lab), TODAY)
    e = by["erklaertexte"]
    assert e["state"] == "jetzt" and e["phase"] == ts.PHASE_WEEK
    texts = [i["text"] for i in e["items"]]
    assert texts[0].startswith("geändert am 15.11.2026") and "(2 Stellen)" in texts[0]
    assert "Lab-Deploy am 02.11.2026" in texts[1]
    assert "Lab-Sperre" in texts[2] and len(texts) == 3
    quiet = {"last_deploy": "2026-09-11T22:48:24+02:00", "locked": True}
    assert _by_key(_with(lab_guard=quiet), TODAY)["erklaertexte"]["state"] == "erledigt"


def test_analysis_parts_are_ticked_by_their_code() -> None:
    sources = {
        "src/sim/study_analysis.py": "def run_within_tests\nReihenfolge: Differenz",
        "src/sim/study_sosci.py": "LIKERT_RECODE = {}",
    }
    parts = ts.auswertung_status(sources)
    assert [p["done"] for p in parts] == [True, True, False, False, True]
    sections = [
        {
            "section": "SoSci-Export und Annika Dietrich",
            "items": ["Antwortcodes SUS und TiA in SoSci: umcodieren"],
        },
        {
            "section": "Auswertung (nach dem Datenfreeze)",
            "items": ["study_analysis.py auf within umstellen; Power neu rechnen"],
        },
    ]
    by = _by_key(_with(sections=sections, auswertung_teile=parts), TODAY)
    a = by["auswertung_vorb"]
    # Both open points are covered by a part, none is listed twice.
    assert len(a["items"]) == 5 and a["offen"] == 2 and a["state"] == "bereit"
    assert "Antwortcodes SUS und TiA" in a["why"]


def test_wallach_after_the_meeting_asks_for_the_answers() -> None:
    day = date(2026, 11, 19)  # Thursday after the meeting
    w = _by_key(_data(day), day)["wallach"]
    assert w["items"][0]["text"].startswith("Antworten aus dem Gespräch")
    assert w["items"][0]["where"] == "Gespräch Mi 18.11."
    assert w["title"] == "Gespräch mit Prof. Wallach (Mi 25.11.)"


def test_every_step_has_a_phase_in_card_order() -> None:
    steps = ts.plan(_data(TODAY), TODAY)
    order = [ts.PHASE_WEEK, ts.PHASE_CHAPTERS, ts.PHASE_SIDE, ts.PHASE_SUBMIT]
    phases = [s["phase"] for s in steps]
    assert phases == sorted(phases, key=order.index)
    assert "spaeter" not in {s["state"] for s in steps}


def test_figure_points_read_boxes_and_open_table_rows() -> None:
    md = (
        "| `fig:a` | 4 | Bild A | x.png | Artur | **fertig** |\n"
        "| (optional) | 2 | Prinzip | Excalidraw | Claude | offen |\n"
        "| `fig:b` | B | Fragebogen | pdf | Artur | offen |\n"
        "- [x] erledigt\n- [ ] Exponat gesamt\n"
    )
    assert ts.figure_points(md) == [
        {"text": "Prinzip (optional)", "where": "Kap. 2"},
        {"text": "Fragebogen (fig:b)", "where": "Anh. B"},
        {"text": "Exponat gesamt", "where": "Fotoliste"},
    ]


def test_markers_outside_the_week_appear_in_their_steps() -> None:
    def mk(file: str, kind: str = "pruefen") -> dict[str, Any]:
        return {"file": file, "line": 1, "kind": kind, "text": f"Punkt {file}"}

    markers = [
        mk("kapitel/05_methodik.tex"),
        mk("vorspann/kurzfassung.tex", "offen"),
        mk("anhang/g_systemdetails.tex"),
        mk("vorspann/titelseite.tex", "offen"),
        mk("anhang/c_erklaertexte.tex", "offen"),
    ]
    by = _by_key(
        _with(
            marker_items=markers, abbildungen=[{"text": "Foto", "where": "Fotoliste"}]
        ),
        TODAY,
    )
    assert "Punkt kapitel/05_methodik.tex" in [
        i["text"] for i in by["prosa_2"]["items"]
    ]
    assert "Punkt vorspann/kurzfassung.tex" in [
        i["text"] for i in by["prosa_7"]["items"]
    ]
    other = [i["where"] for i in by["anhaenge"]["items"]]
    assert other == [
        "g_systemdetails.tex:1",
        "titelseite.tex:1",
        "c_erklaertexte.tex:1",
    ]
    assert "Anhang C gilt laut Liste als fertig" in by["anhaenge"]["why"]
    assert (
        by["abbildungen"]["state"] == "bereit"
        and by["abbildungen"]["phase"] == ts.PHASE_SIDE
    )


def test_list_gaps_show_in_their_step_until_the_line_is_listed() -> None:
    data = _with(sections=[])
    data["list_gaps"] = ts.list_gaps(data)
    assert len(data["list_gaps"]) == len(ts.LIST_GAPS)
    by = _by_key(data, TODAY)
    freeze = [i for i in by["freeze"]["items"] if i.get("fehlt_in_liste")]
    assert len(freeze) == 3 and all(i["tip"] for i in freeze)
    # The freeze check lists a gap that names the Nachtrag (synthetic line).
    data["list_gaps"] = data["list_gaps"] + [
        {"step": "anhang_fh", "text": "Im Nachtrag festlegen", "where": "w", "tip": "t"}
    ]
    check = ts.freeze_check(data, TODAY)
    assert any(i["quelle"] == "fehlt in offene_punkte.md" for i in check["items"])
    # Once the line is in the list, the gap disappears.
    line = ts.LIST_GAPS[0][2]
    listed = _with(
        sections=[{"section": "Auswertung (nach dem Datenfreeze)", "items": [line]}]
    )
    assert len(ts.list_gaps(listed)) == len(ts.LIST_GAPS) - 1


def test_no_gap_line_is_rerouted_by_item_route() -> None:
    for _, _, line, _ in ts.LIST_GAPS:
        assert not any(w in line for w, _ in ts.ITEM_ROUTE), line


def test_every_step_has_a_tip() -> None:
    data = _with(sections=[])
    data["list_gaps"] = ts.list_gaps(data)
    steps = ts.plan(data, TODAY)
    assert [s["key"] for s in steps if not s.get("tip")] == []


def test_datenfreeze_step_waits_for_its_week_then_is_due() -> None:
    by = _by_key(_with(), TODAY)
    df = by["datenfreeze"]
    assert df["state"] == "wartet" and df["phase"] == ts.PHASE_SIDE
    assert len(df["items"]) == len(ts.DATENFREEZE_PLAN)
    assert {i["frist"] for i in df["items"]} == {"2026-11-29"}
    assert df["items"][1]["am_zug"] == "Annika"
    day = date(2026, 11, 27)
    assert _by_key(_data(day), day)["datenfreeze"]["state"] == "jetzt"
    done = _with(datenfreeze_done=True)
    assert _by_key(done, TODAY)["datenfreeze"]["state"] == "erledigt"


def test_item_tip_takes_the_first_keyword_in_the_text() -> None:
    tip = ts.item_tip(
        "x", {"text": "Lärm luftgekühlter Miner, Foto Avalon", "where": ""}
    )
    assert tip is not None and tip.startswith("Drei Wege aus dem Marker")


def test_item_tip_rules_per_kind_of_point() -> None:
    offen = {"text": "Ein Fakt", "where": "05_methodik.tex:3", "kind": "offen"}
    assert "Stichwort" in str(ts.item_tip("prosa_2", offen))
    write = {"text": "Antwort auf H1", "where": "07_diskussion.tex:9", "kind": "offen"}
    assert "Prosa schreibst du" in str(ts.item_tip("prosa_6", write))
    result = {"text": "SUS A gegen B", "where": "06_ergebnisse.tex:9", "kind": "offen"}
    assert "Datenfreeze" in str(ts.item_tip("prosa_5", result))
    check = {"text": "Zahl unsicher", "where": "04_system.tex:5", "kind": "pruefen"}
    assert "belegen" in str(ts.item_tip("prosa", check))
    befund = {"text": "Winter ohne Mining (% Befund: winter)", "where": "Kap. 7"}
    assert "Befund winter übernehmen" in str(ts.item_tip("spaeter_befunde", befund))
    part = {"text": "Method: 0 von 900 Wörtern", "where": "Kap. 5"}
    assert "Budget 900" in str(ts.item_tip("summary", part))
    waiting = {
        "text": "Ein Fakt",
        "where": "05_methodik.tex:3",
        "kind": "offen",
        "wartet_bis": "2026-11-17",
    }
    assert str(ts.item_tip("prosa_2", waiting)).startswith("Termin 17.11.:")


def test_every_open_point_of_the_plan_has_a_solution() -> None:
    data = _with(sections=[])
    data["list_gaps"] = ts.list_gaps(data)
    for step in ts.plan(data, TODAY):
        for item in step["items"]:
            if not (item.get("siehe_auch") or item.get("erledigt")):
                assert item.get("tip"), (step["key"], item["text"])


def test_item_tips_for_the_index_and_tia_item_19() -> None:
    index = {
        "text": "Index für das Textverständnis („ sucht Dieter raus“)",
        "where": "",
    }
    tip = str(ts.item_tip("prosa_2", index))
    assert "Name des Index" in tip and "Wallach-Agenda" in tip
    item19 = {
        "text": "Variablenansicht vom 14.11.2026: Der erste TiA-Block",
        "where": "",
    }
    tip = str(ts.item_tip("prosa_2", item19))
    assert "keinen Gesamtwert" in tip and "18 gemeinsame" not in tip


def test_offen_after_the_freeze_waits_for_the_freeze() -> None:
    assert ts.wait_reason("N und Alter nach dem Datenfreeze eintragen") == "Datenfreeze"
    assert ts.wait_reason("Nach dem Datenfreeze rechnen") == "Datenfreeze"
    assert ts.wait_reason("vor dem Datenfreeze klären") is None
    point = {
        "text": "Wert nach dem Datenfreeze",
        "where": "05_methodik.tex:9",
        "kind": "offen",
        "am_zug": "Datenfreeze",
    }
    assert "SoSci-Export eintragen (Claude)" in str(ts.item_tip("prosa_2", point))
