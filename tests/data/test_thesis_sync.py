"""Tests for thesis_sync: comment parsing, ADR replacement, file drift, Befunde."""

from __future__ import annotations

from typing import Any

from src.data import thesis_sync as ts

ADRS = """
## ADR 027 — Saisonale Schwellen (Detail)

**Kontext.** ADR 020 bleibt, Text erwähnt ersetzt ADR 025 nur im Fließtext.

## ADR 028 — Live-Formel (Detail)

**Kontext.** irgendwas

## ADR 033 — Hausreserve-Formel

**Datum:** 13.11.2026 · **Status:** umgesetzt · **Ersetzt teilweise:** ADR 028 (Formel)
"""

TEX = r"""% Kopf
%   % Stand: 02.11.2026 neu   = Beispiel, wird übersprungen
\chapter{System}
\section{Hausreserve}
\begin{itemize}
  \item Formel mit 535 W.
        % Quelle: mvp_auto.yaml Z. 734-802; ADR 027/028
        % Stand: bis 02.11.2026; 03.11.2026 geändert
        % Befund: hausreserve (Stichtag 14.11.2026)
  \item Neue Formel.
        % Quellen: ADR 028 und 033, src/ha/config/packages/mvp_auto.yaml
        % Stand: 14.11.2026 geprüft
  \item Ohne Stand.
        % Quelle: README.md, 091_adr_de.md Z. 3;
        % Fortsetzung nennt scripts/build_sim_day.py
\end{itemize}
\section{Befunde}
Text.
% Befund: schaltwechsel, unbekannt_x
"""


def test_parse_adrs_reads_only_head_metadata() -> None:
    adrs = ts.parse_adrs(ADRS)
    assert adrs[33]["replaces"] == [28]
    assert adrs[33]["date"] == "2026-11-13"
    # "ersetzt ADR 025" in running text is no replacement.
    assert adrs[27]["replaces"] == []
    assert adrs[28]["title"] == "Live-Formel"


def test_refs_handle_lists_and_paths() -> None:
    assert ts.adr_refs("ADR 027/028; ADRs 030 und 031, ADR 033") == [27, 28, 30, 31, 33]
    assert ts.file_refs(r"docs\x\a.md Z. 3; mvp_auto.yaml; docs/01_* ; a.md") == [
        "docs/x/a.md",
        "mvp_auto.yaml",
        "a.md",
    ]


def test_parse_tex_blocks_stand_and_continuation() -> None:
    entries = ts.parse_tex(TEX, "kapitel/04.tex")
    assert len(entries) == 4  # the head example before \chapter is skipped
    first, second, third, fourth = entries
    assert first.section == "Hausreserve"
    assert first.stand == "2026-11-03"
    assert first.befunde == [("hausreserve", "2026-11-14")]
    assert second.stand == "2026-11-14"
    assert "033" in second.sources
    assert third.stand is None
    assert "build_sim_day.py" in third.sources
    assert fourth.section == "Befunde"
    assert [b for b, _ in fourth.befunde] == ["schaltwechsel", "unbekannt_x"]


def _check() -> dict[str, Any]:
    entries = ts.parse_tex(TEX, "kapitel/04.tex")
    paths = {
        "mvp_auto.yaml": "src/ha/config/packages/mvp_auto.yaml",
        "src/ha/config/packages/mvp_auto.yaml": "src/ha/config/packages/mvp_auto.yaml",
        "091_adr_de.md": "docs/091_adr_de.md",
        "scripts/build_sim_day.py": "scripts/build_sim_day.py",
    }
    dates = {
        "src/ha/config/packages/mvp_auto.yaml": "2026-11-14",
        "scripts/build_sim_day.py": "2026-11-10",
    }
    return ts.check(entries, ts.parse_adrs(ADRS), paths.get, dates.get)


def test_check_flags_replaced_adr_unless_replacement_is_cited() -> None:
    out = _check()
    replaced = out["replaced"]
    assert isinstance(replaced, list)
    # Entry 1 cites 028 without 033 -> flagged; entry 2 cites both -> not.
    assert [(r["line"], r["adr"], r["by"]) for r in replaced] == [(7, 28, 33)]


def test_check_file_drift_needs_a_stand_date() -> None:
    out = _check()
    changed = out["changed"]
    assert isinstance(changed, list)
    assert [c["path"] for c in changed] == ["src/ha/config/packages/mvp_auto.yaml"]
    # Only the 03.11. entry; the 14.11. one is checked, the third has no Stand.
    assert [e["line"] for e in changed[0]["entries"]] == [7]
    assert out["unresolved"] == ["README.md"]
    assert [n["line"] for n in out["no_stand"]] == [14]


def test_befunde_states_against_snapshot() -> None:
    entries = ts.parse_tex(TEX, "kapitel/04.tex")
    notes = [
        {"id": "hausreserve", "group": ts.TEXT_GROUPS[0], "title": "H", "text": "neu"},
        {"id": "schaltwechsel", "group": ts.TEXT_GROUPS[0], "title": "S", "text": "x"},
        {"id": "ueberschuss", "group": ts.TEXT_GROUPS[0], "title": "U", "text": "y"},
        {"id": "einordnung", "group": "Einordnung", "title": "E", "text": "z"},
    ]
    snaps = {"2026-11-14": [{"id": "hausreserve", "text": "alt"}]}
    out = ts.befunde(entries, notes, snaps)
    rows = {r["id"]: r for r in out["notes"]}
    assert rows["hausreserve"]["places"][0]["state"] == "geaendert"
    # Cited without a Stichtag and without a Stand in that block.
    assert rows["schaltwechsel"]["places"][0]["state"] == "ohne_abzug"
    assert out["missing"] == ["ueberschuss"]  # Einordnung needs no text
    assert [u["id"] for u in out["unknown"]] == ["unbekannt_x"]


def test_render_markdown_names_every_part() -> None:
    sync = _check()
    entries = ts.parse_tex(TEX, "kapitel/04.tex")
    sync["befunde"] = ts.befunde(
        entries,
        [{"id": "ueberschuss", "group": ts.TEXT_GROUPS[0], "title": "U", "text": "y"}],
        {},
    )
    md = ts.render_markdown(sync, "2026-11-14T09:00:00+00:00")
    assert "ersetzt durch ADR 033" in md
    assert "**fehlt im Text**" in md
    assert "mvp_auto.yaml" in md
    assert "Quelle ohne Stand-Datum (1)" in md
    assert " — " not in md


def test_marker_items_balance_braces_and_skip_comments() -> None:
    tex = "\n".join(
        [
            "a",
            r"  \pruefen{Nur noch {\em belegen}: siehe~\cref{sec:x}",
            "  weiter}",
            r"% \offen{auskommentiert}",
            r"\item \offen{Freigabe \textbf{Autor}}",
            "",
        ]
    )
    items = ts.marker_items(tex, "kapitel/04_system.tex")
    assert [(i["kind"], i["line"]) for i in items] == [("pruefen", 2), ("offen", 5)]
    assert items[0]["text"] == "Nur noch belegen: siehe (Verweis) weiter"
    assert items[1]["text"] == "Freigabe Autor"


def _plan_data(today_week_end: str) -> dict[str, Any]:
    return {
        "schedule": [
            {
                "week": "09.-15.11.",
                "start": "2026-11-09",
                "end": "2026-11-15",
                "write": "Kap. 4 System (Prosa)",
                "parallel": "Erhebung",
                "now": True,
            },
            {
                "week": "16.-22.11.",
                "start": "2026-11-16",
                "end": "2026-11-22",
                "write": "Kap. 5 Methodik",
                "parallel": "x",
                "now": False,
            },
            {
                "week": "23.-29.11.",
                "start": "2026-11-23",
                "end": today_week_end,
                "write": "Kap. 2",
                "parallel": "Ende der Erhebung, Datenfreeze",
                "now": False,
            },
            {
                "week": "07.-13.12.",
                "start": "2026-12-07",
                "end": "2026-12-13",
                "write": "Kap. 6 Ergebnisse",
                "parallel": "",
                "now": False,
            },
            {
                "week": "14.-20.12.",
                "start": "2026-12-14",
                "end": "2026-12-20",
                "write": "Kap. 7 Diskussion",
                "parallel": "",
                "now": False,
            },
        ],
        "sections": [
            {"section": "Artur (eigenes Wissen)", "items": ["Frage A"]},
            {"section": "Literatur", "items": ["Paper X"]},
            {"section": "Prüfungsamt und Hochschule", "items": ["Titel"]},
            {"section": "Auswertung (nach dem Datenfreeze)", "items": ["rechnen"]},
            {"section": "Neu und unbekannt", "items": ["z"]},
        ],
        "marker_items": [
            {
                "file": "kapitel/04_system.tex",
                "line": 9,
                "kind": "pruefen",
                "text": "P4",
            },
            {
                "file": "kapitel/05_methodik.tex",
                "line": 3,
                "kind": "offen",
                "text": "O5",
            },
        ],
        "sync": {
            "replaced": [],
            "befunde": {
                "notes": [
                    {"id": "a", "title": "A", "group": ts.TEXT_GROUPS[3], "places": []},
                    {"id": "l", "title": "L", "group": ts.TEXT_GROUPS[2], "places": []},
                    {"id": "p", "title": "P", "group": ts.TEXT_GROUPS[0], "places": []},
                    {"id": "m", "title": "M", "group": ts.TEXT_GROUPS[1], "places": []},
                ],
                "missing": ["a", "l", "p", "m"],
            },
        },
    }


def test_plan_orders_work_and_scopes_to_the_week_chapter() -> None:
    from datetime import date

    steps = ts.plan(_plan_data("2026-11-29"), date(2026, 11, 14))
    keys = [s["key"] for s in steps]
    assert keys[:6] == ["veraltet", "klaeren", "belegen", "befunde", "prosa", "pruefen"]
    by = {s["key"]: s for s in steps}
    assert by["veraltet"]["state"] == "erledigt"  # nothing stale
    assert by["klaeren"]["state"] == "jetzt"  # first step with work
    # Only chapter 4 markers this week; chapter 5 marker is not listed.
    assert [i["text"] for i in by["belegen"]["items"]] == ["P4"]
    assert [i["text"] for i in by["klaeren"]["items"]] == ["Frage A"]
    # Rule of Artur (14.11.2026): production figures are not chapter 4. Only
    # the explanation layer is Kap. 4 now; methods, results and limitations
    # wait under their own chapter.
    assert [i["where"] for i in by["befunde"]["items"]] == ["Kap. 4"]
    # Next week (Kap. 5) stays under "Vorbereiten"; Kap. 6 and 7 wait in their
    # own step, each with the week in which the chapter is written.
    prep = {i["text"].split(" (")[0]: i["where"] for i in by["naechste"]["items"]}
    assert prep["M"] == "Kap. 5 · 16.-22.11." and "P" not in prep and "L" not in prep
    far = {i["text"].split(" (")[0]: i["where"] for i in by["spaeter_befunde"]["items"]}
    # Production findings belong to Kap. 7 (variant b, Artur 15.11.2026).
    assert far == {"P": "Kap. 7 · 14.-20.12.", "L": "Kap. 7 · 14.-20.12."}
    assert by["spaeter_befunde"]["state"] == "bereit"
    # Order (Artur, 15.11.2026): the chapter block ("Vorbereiten", the
    # other chapters, their findings) before what runs alongside (literature)
    # and before the Hochschule.
    order = [s["key"] for s in steps]
    assert order.index("naechste") < order.index("spaeter_befunde")
    assert order.index("spaeter_befunde") < order.index("literatur")
    assert order.index("literatur") < order.index("fristen")
    assert [i["text"] for i in by["literatur"]["items"]] == ["Paper X"]
    assert [i["text"] for i in by["fristen"]["items"]] == ["Titel"]
    assert by["literatur"]["who"] == "Artur mit Claude"
    assert "nachweislich existiert" in by["literatur"]["why"]
    assert by["literatur"]["state"] == "bereit"
    assert by["freeze"]["state"] == "gesperrt"
    assert by["sonstiges"]["items"][0]["text"] == "z"
    after = ts.plan(_plan_data("2026-11-29"), date(2026, 12, 1))
    assert {s["key"]: s for s in after}["freeze"]["state"] != "gesperrt"


def test_week_chapters_reads_lists() -> None:
    assert ts.week_chapters("Kap. 1, 8, Kurzfassung") == [1, 8]
    assert ts.week_chapters("Kap. 7 Diskussion") == [7]
    assert ts.week_chapters("Puffer") == []


def test_parse_termin_reads_the_last_day_in_all_forms() -> None:
    from datetime import date

    today = date(2026, 11, 14)
    for text, want in [
        ("x (Termin 17.11.) y", date(2026, 11, 17)),
        ("x (Termin 16./17.11.)", date(2026, 11, 17)),
        ("x (Termin 16.–17.11.)", date(2026, 11, 17)),
        ("x (Termin 16.-17.11.)", date(2026, 11, 17)),
        ("x (Termin~16./17.11.2026)", date(2026, 11, 17)),
        ("x (Termin\n17.11.)", date(2026, 11, 17)),
        ("x (Termin 30.11.–02.12.)", date(2026, 12, 2)),
        # No year: a date long past is next year's.
        ("x (Termin 05.01.)", date(2027, 1, 5)),
        # A date a few days back stays this year (it has simply passed).
        ("x (Termin 10.11.)", date(2026, 11, 10)),
    ]:
        assert ts.parse_termin(text, today) == want, text
    for text in [
        "",
        "ohne Termin",
        "Termin 17.11.",
        "(Termin bald)",
        "(Termin 31.02.)",
    ]:
        assert ts.parse_termin(text, today) is None, text


def test_marker_items_keep_a_termin_that_the_preview_cuts_off() -> None:
    from datetime import date

    body = "Nachweis " + "wichtig " * 40 + "(Termin 16./17.11.)."
    tex = "\n".join([r"\pruefen{" + body + "}", r"\offen{ohne Datum}", ""])
    items = ts.marker_items(tex, "kapitel/04_system.tex", date(2026, 11, 14))
    assert "Termin" not in items[0]["text"]  # preview is cut at MARKER_MAX
    assert items[0]["termin"] == "2026-11-17"
    assert items[1]["termin"] is None


def _wait_data(*termine: str | None) -> dict[str, Any]:
    data = _plan_data("2026-11-29")
    data["marker_items"] = [
        {
            "file": "kapitel/04_system.tex",
            "line": 10 + n,
            "kind": "pruefen",
            "text": f"P{n}",
            "termin": t,
        }
        for n, t in enumerate(termine)
    ]
    return data


def test_plan_step_waits_when_every_point_waits_for_a_termin() -> None:
    from datetime import date

    steps = ts.plan(_wait_data("2026-11-17", "2026-11-17"), date(2026, 11, 14))
    by = {s["key"]: s for s in steps}
    assert by["belegen"]["state"] == "wartet"
    assert by["belegen"]["wait_until"] == "2026-11-17"
    assert [i["wartet_bis"] for i in by["belegen"]["items"]] == ["2026-11-17"] * 2
    # "jetzt" moves on to the next step with real work.
    assert by["klaeren"]["state"] == "jetzt"
    # The Wallach meeting is always "jetzt" (Artur, 15.11.2026).
    assert [s["key"] for s in steps if s["state"] == "jetzt"] == ["klaeren", "wallach"]


def test_plan_wait_ends_after_the_termin_day() -> None:
    from datetime import date

    data = _wait_data("2026-11-17")
    # The day of the Termin still waits (the result is not there before it is over).
    day = {s["key"]: s for s in ts.plan(data, date(2026, 11, 17))}["belegen"]
    assert day["state"] == "wartet"
    # Afterwards the point counts like any other and carries no flag.
    after = {s["key"]: s for s in ts.plan(data, date(2026, 11, 18))}["belegen"]
    assert after["state"] != "wartet"
    assert "wartet_bis" not in after["items"][0]


def test_plan_mixed_step_keeps_working_state_and_flags_only_the_waiting_point() -> None:
    from datetime import date

    steps = ts.plan(_wait_data("2026-11-17", None), date(2026, 11, 14))
    belegen = {s["key"]: s for s in steps}["belegen"]
    assert belegen["state"] in ("jetzt", "offen")
    assert [bool(i.get("wartet_bis")) for i in belegen["items"]] == [True, False]
    assert "wait_until" not in belegen


def test_plan_checkbox_point_with_termin_makes_a_later_step_wait() -> None:
    from datetime import date

    data = _plan_data("2026-11-29")
    data["sections"] = [
        {
            "section": "Sitzungsprotokoll-Export",
            "items": ["Export holen (Termin 16.–17.11.)"],
        }
    ]
    steps = {s["key"]: s for s in ts.plan(data, date(2026, 11, 14))}
    assert steps["parallel"]["state"] == "wartet"
    assert steps["parallel"]["wait_until"] == "2026-11-17"
