"""Tests for thesis_notes: numbers come from the cards, groups stay ordered."""

from __future__ import annotations

from pathlib import Path

from src.data import thesis_notes as tn
from src.data.db import get_connection

CARDS = {
    "settings": {
        "floor_pct": 5.0,
        "baseload_w": 570.0,
        "gap_h": 0.75,
        "efficiency": 0.8,
    },
    "automation": {
        "switching": {
            "target": 2,
            "since": "2026-05-07",
            "months": [
                {
                    "month": "2026-06",
                    "mining_days": 30,
                    "days_over": 15,
                    "max_start_stop": 38,
                },
                {
                    "month": "2026-09",
                    "mining_days": 20,
                    "days_over": 5,
                    "max_start_stop": 12,
                },
                {
                    "month": "2026-11",
                    "mining_days": 0,
                    "days_over": 0,
                    "max_start_stop": 0,
                },
            ],
        },
        "surplus": {
            "hours": 41.8,
            "export_kwh": 121.6,
            "months": [
                {"reasons": {"unbekannt": 13.2}},
                {"reasons": {"Akku unter Stopp-Schwelle": 23.0, "Handbetrieb": 0.7}},
            ],
        },
        "safety": {
            "tmax_limit_c": 110,
            "errors_total": 94,
            "hot_blocks_total": 39,
            "rows": [
                {"month": "2026-07", "miner": "miner2", "hot_blocks": 33},
                {"month": "2026-06", "miner": "miner1", "hot_blocks": 1},
            ],
        },
    },
    "heizstab": {"days": 13, "heizstab_kwh_not_full": 10.3, "empty_mornings": 12},
    "forecast": {"days_used": 13, "mae_pct": 82.4, "bias_pct": 73.1},
}


def test_de_formats_german_numbers() -> None:
    assert tn.de(1234.5, 1) == "1.234,5"
    assert tn.de(6693) == "6.693"
    assert tn.de(None) == "—"
    assert tn.de_day("2026-05-25") == "25.05.2026"


def test_notes_quote_card_numbers_and_keep_group_order(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        notes = tn.build(conn, CARDS)
    finally:
        conn.close()
    by_title = {n["title"]: n["text"] for n in notes}
    switch = by_title["Qualitätsziel Schaltwechsel wird verfehlt"]
    assert "An 20 von 50 Tagen mit Mining (40 %)" in switch
    assert "Höchstwert 38 im Juni" in switch
    surplus = by_title["Ungenutzter Solarüberschuss"]
    assert "41,8 Stunden" in surplus and "121,6 kWh" in surplus
    # the unknown share is not presented as a reason
    assert "Für 23,7 Stunden" in surplus
    assert "Akku unter Stopp-Schwelle (23,0 Stunden)" in surplus
    assert "33 davon bei miner2 im Juli" in by_title["Übertemperatur"]
    assert "10,3 kWh" in by_title["Heizstab konkurriert mit dem Akku"]
    order = [tn.GROUP_ORDER.index(n["group"]) for n in notes]
    assert order == sorted(order)
    assert notes[0]["group"] == tn.G_FRAME
    # no spaced dash in prose (project style)
    assert not any(" — " in n["text"] or " – " in n["text"] for n in notes)


def test_build_on_empty_input_still_gives_fixed_notes(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        notes = tn.build(conn, {})
    finally:
        conn.close()
    assert [n["title"] for n in notes] == [
        n["title"]
        for n in sorted(tn.FIXED_NOTES, key=lambda n: tn.GROUP_ORDER.index(n["group"]))
    ]


def test_every_note_has_a_unique_stable_id(tmp_path: Path) -> None:
    """The thesis cites notes as "% Befund: <id>": ids must exist and differ."""
    conn = get_connection(tmp_path / "t.db")
    try:
        notes = tn.build(conn, CARDS)
    finally:
        conn.close()
    ids = [n["id"] for n in notes]
    assert all(ids) and len(ids) == len(set(ids))
    assert "schaltwechsel" in ids and "einordnung" in ids


def test_reserve_derivation_quotes_values_in_force(tmp_path: Path) -> None:
    """hausreserve_herleitung (Kap. 4) follows the HA values, not the ADR text."""
    conn = get_connection(tmp_path / "t.db")
    try:
        notes = tn.build(conn, CARDS)
        later = tn.build(
            conn, {**CARDS, "settings": {**CARDS["settings"], "gap_h": 1.0}}
        )
    finally:
        conn.close()
    note = next(n for n in notes if n["id"] == "hausreserve_herleitung")
    assert note["group"] == tn.G_SYSTEM
    assert "570 W" in note["text"] and "0,75 h" in note["text"]
    assert "80 %" in note["text"] and "Boden 5 %" in note["text"]
    changed = next(n for n in later if n["id"] == "hausreserve_herleitung")
    assert "1,00 h" in changed["text"]


def test_system_group_maps_to_chapter_4() -> None:
    from src.data.thesis_sync import GROUP_CHAPTER

    assert GROUP_CHAPTER[tn.G_SYSTEM] == 4


def _kpi(conn: object, day: str, sats: float | None, kwh: float, warn: int = 0) -> None:
    conn.execute(  # type: ignore[attr-defined]
        "INSERT INTO daily_kpi (day, blocks, coverage_pct, quality_warn,"
        " quality_error, energy_to_sats, mining_kwh, computed_at)"
        " VALUES (?, 144, 100, ?, 0, ?, ?, 'x')",
        (day, warn, sats, kwh),
    )


def test_energy_to_sats_counts_only_real_mining_days(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "t.db")
    try:
        _kpi(conn, "2026-08-01", 120.0, 10.0)
        _kpi(conn, "2026-08-02", 130.0, 30.0)  # weighted: (1200+3900)/40
        _kpi(conn, "2026-08-03", 999.0, 10.0, warn=6)  # not measured
        _kpi(conn, "2026-08-04", None, 10.0)  # no settlement
        _kpi(conn, "2026-08-05", 0.0, 12.0)  # stored zero = missing settlement
        _kpi(conn, "2026-11-01", 120.0, 0.44)  # standby residual payout
        _kpi(conn, "2026-09-01", 110.0, 5.0)
        conn.commit()
        notes = tn.build(conn, {})
    finally:
        conn.close()
    text = next(n for n in notes if n["id"] == "energy_to_sats")["text"]
    assert "3 gemessene Mining-Tage" in text
    assert "August 127,5 (2 Tage, 40 kWh)" in text
    assert "September 110,0 (1 Tag, 5 kWh)" in text
    assert "1 Mining-Tage mit gespeicherter 0" in text
    assert "November" not in text and "999" not in text


def test_saisonsperre_bug_is_a_fixed_limitation() -> None:
    note = next(n for n in tn.FIXED_NOTES if n["id"] == "saisonsperre_bug")
    assert note["group"] == tn.G_LIMIT
    assert "ADR 030" in note["title"]
