"""Befund markers "ohne Zahlen" and duplicates in one block (synthetic text)."""

from __future__ import annotations

from datetime import date

from src.data import thesis_sync as ts

TEX = r"""
\chapter{System}
\section{Daten}
% Quelle: thesis_notes.py
% Stand: 14.11.2026
% Befund: protokoll (Stichtag 14.11.2026, ohne Zahlen)
% Befund: datenbasis (Stichtag 14.11.2026)
Text.
\section{Zweimal}
% Befund: protokoll (Stichtag 13.11.2026)
% Befund: protokoll (Stichtag 14.11.2026)
Text.
\section{Gemischt}
% Befund: protokoll (Stichtag 14.11.2026, ohne Zahlen)
% Befund: protokoll (Stichtag 14.11.2026)
Text.
"""

GROUP = ts.TEXT_GROUPS[0]


def _notes(protokoll: str, datenbasis: str) -> list[dict[str, str]]:
    return [
        {"id": "protokoll", "group": GROUP, "title": "P", "text": protokoll},
        {"id": "datenbasis", "group": GROUP, "title": "D", "text": datenbasis},
    ]


SNAP = {
    "2026-11-14": _notes(
        "1.204 Moduswechsel seit 14.11.2026 protokolliert, 23 % Regelwechsel.",
        "174 Tage, 6 fehlerhaft.",
    ),
    "2026-11-13": _notes("1.180 Moduswechsel.", "173 Tage."),
}


def test_parse_reads_the_ohne_zahlen_suffix() -> None:
    first = ts.parse_tex(TEX, "kapitel/04.tex")[0]
    assert first.befunde == [("protokoll", "2026-11-14"), ("datenbasis", "2026-11-14")]
    assert first.ohne_zahlen == {"protokoll"}


def test_ohne_zahlen_ignores_counters_but_not_the_statement() -> None:
    entries = ts.parse_tex(TEX, "kapitel/04.tex")[:1]
    # Counters and dates moved on, the statement is the same.
    today = _notes(
        "1.317 Moduswechsel seit 15.11.2026 protokolliert, 24 % Regelwechsel.",
        "175 Tage, 6 fehlerhaft.",
    )
    rows = {r["id"]: r for r in ts.befunde(entries, today, SNAP)["notes"]}
    assert rows["protokoll"]["places"][0]["state"] == "aktuell"
    assert rows["protokoll"]["places"][0]["ohne_zahlen"] is True
    # Without the suffix the same kind of change still counts.
    assert rows["datenbasis"]["places"][0]["state"] == "geaendert"
    # A changed statement counts even "ohne Zahlen".
    reworded = _notes(
        "1.317 Moduswechsel seit 15.11.2026 protokolliert, Regelwechsel fehlen.",
        "174 Tage, 6 fehlerhaft.",
    )
    rows = {r["id"]: r for r in ts.befunde(entries, reworded, SNAP)["notes"]}
    assert rows["protokoll"]["places"][0]["state"] == "geaendert"


def test_same_finding_twice_in_one_block_is_one_place() -> None:
    entries = ts.parse_tex(TEX, "kapitel/04.tex")
    assert entries[1].befunde == [("protokoll", "2026-11-14")]  # newest Stichtag
    # Mixed: one marker with numbers, so the numbers count.
    assert entries[2].befunde == [("protokoll", "2026-11-14")]
    assert entries[2].ohne_zahlen == set()
    rows = {r["id"]: r for r in ts.befunde(entries, _notes("x", "y"), SNAP)["notes"]}
    assert [p["line"] for p in rows["protokoll"]["places"]] == [4, 10, 14]


def test_plan_says_aussage_for_a_changed_statement() -> None:
    entries = ts.parse_tex(TEX, "kapitel/04.tex")[:1]
    reworded = _notes("Regelwechsel fehlen.", "174 Tage, 6 fehlerhaft.")
    data = {
        "schedule": [],
        "sync": {"befunde": ts.befunde(entries, reworded, SNAP)},
    }
    stale = {s["key"]: s for s in ts.plan(data, date(2026, 11, 15))}["veraltet"]
    assert [i["text"] for i in stale["items"]] == [
        "Befund P: Aussage seit Stichtag 14.11.2026 geändert"
    ]


def test_without_numbers_masks_dates_and_decimals() -> None:
    assert ts.without_numbers("1.234,5 kWh am 14.11.2026 um 03:50, 23 %") == (
        "# kWh am # um #, # %"
    )
