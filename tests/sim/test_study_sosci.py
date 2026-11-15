"""SoSci preparation of the study: recoding, reversal, subscales, missing rule.

Only synthetic rows; no real SoSci export is read.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.sim import study_sosci as ss


def test_recode_table_is_the_fixed_mapping() -> None:
    assert ss.LIKERT_RECODE == {1: 1, 3: 2, 4: 3, 5: 4, 2: 5}
    assert ss.MISSING_CODES == {-1, -9}
    assert ss.CODE_OF_POSITION == {1: 1, 2: 3, 3: 4, 4: 5, 5: 2}


def test_recode_raw_row_with_all_codes() -> None:
    raw = pd.Series([1, 2, 3, 4, 5, -1, -9, None], name="VE14")
    got = ss.recode_likert(raw)
    assert got.tolist()[:5] == [1, 5, 2, 3, 4]
    assert all(math.isnan(v) for v in got.tolist()[5:])


def test_recode_rejects_unknown_codes() -> None:
    with pytest.raises(ValueError, match="unbekannte Antwortcodes"):
        ss.recode_likert(pd.Series([1, 6], name="V212"))


def test_tia_items_follow_the_original_numbering() -> None:
    assert len(ss.TIA_ITEMS) == 18
    first, last = ss.TIA_ITEMS[0], ss.TIA_ITEMS[-1]
    assert (first.number, first.block1, first.block2) == (1, "VE14", "V212")
    assert (last.number, last.block1, last.block2) == (18, "VE31", "V229")
    assert ss.TIA_ONLY_BLOCK2 == "V230" and ss.TIA_ITEM19 == 19
    assert ss.SUS_BLOCK1 == [f"VE{i:02d}" for i in range(4, 14)]
    assert ss.SUS_BLOCK2 == [f"V{i}" for i in range(202, 212)]


def test_subscales_follow_the_koerber_manual() -> None:
    by_key = {s.key: s for s in ss.TIA_SUBSCALES}
    assert by_key["tia_vertrauen"].items == (9, 14)
    assert by_key["tia_vertrauen"].role == "primär"
    assert by_key["tia_rk"].items == (1, 6, 10, 13, 15)
    assert by_key["tia_vv"].items == (2, 7, 11, 16)
    assert by_key["tia_ie"].items == (4, 8)
    assert by_key["tia_vt"].items == (3, 17) and by_key["tia_vt"].role == "beschreibend"
    assert by_key["tia_nv"].items == (5, 12, 18)
    # Items 1..18 each in exactly one subscale; 19 only in R/K of run 2.
    used = sorted(i for s in ss.TIA_SUBSCALES for i in s.items)
    assert used == list(range(1, 19))
    assert ss.TIA_RK19.items == (1, 6, 10, 13, 15, 19)
    assert ss.TIA_REVERSED == {5, 7, 10, 15, 16}
    roles = [s.role for s in ss.TIA_SUBSCALES]
    assert roles.count("explorativ") == 3


def test_missing_rule_half_of_the_items_two_items_both() -> None:
    assert [ss.min_answered(k) for k in (2, 3, 4, 5, 6)] == [2, 2, 2, 3, 3]


def test_check_item_labels_finds_a_mismatch() -> None:
    labels = {i.block1: f"Text {i.number}" for i in ss.TIA_ITEMS}
    labels.update({i.block2: f"Text {i.number}" for i in ss.TIA_ITEMS})
    labels[ss.TIA_ONLY_BLOCK2] = ss.TIA_ONLY_BLOCK2_TEXT
    assert ss.check_item_labels(labels) == []
    labels["V229"] = "anders"
    assert ss.check_item_labels(labels) == ["VE31/V229: 'Text 18' != 'anders'"]


def test_sus_score_standard_formula_and_midpoint() -> None:
    items = pd.DataFrame(
        [
            [5, 1] * 5,
            [3] * 10,
            [5, 1] * 4 + [5, np.nan],  # even item missing: 9 x 4 + 2
            [4, 2] * 4 + [np.nan, 2],  # odd item missing: 9 x 3 + 2
            [5, 1] * 4 + [np.nan, np.nan],  # two missing: no value
        ]
    )
    got = ss.sus_score(items).tolist()
    assert got[:4] == [100.0, 50.0, 95.0, 72.5] and math.isnan(got[4])
    assert ss.SUS_MAX_MISSING == 1 and ss.SUS_MIDPOINT == 3.0
    # The midpoint is position 3 after recoding, i.e. SoSci code 4.
    assert ss.CODE_OF_POSITION[3] == 4


def test_missing_sus_item_from_sosci_codes() -> None:
    raw = pd.DataFrame([_row(1, 1, 3, 3), _row(2, 2, 3, 3)])
    # Best answers in run 1 of case 1: odd items position 5 (code 2), even 1.
    raw.loc[0, ss.SUS_BLOCK1] = [2, 1] * 5
    raw.loc[0, "VE05"] = -1  # item 2 missing: midpoint 3 contributes 2, not 4
    raw.loc[1, "V202"] = -9
    raw.loc[1, "V203"] = -1  # two items missing in run 2: no value
    long = ss.prepare(raw).long.set_index(["case", "run"])
    assert long.loc[(1, 1), "sus"] == 95.0  # prorating would give 100
    assert math.isnan(long.loc[(2, 2), "sus"])
    assert long.loc[(2, 1), "sus"] == 50.0


def _counts(prep: ss.Prepared) -> dict[tuple[str, int, str], dict[str, object]]:
    return {(m["messung"], m["durchlauf"], m["variante"]): m for m in prep.missing}


def _row(case: int, order: int, pos_a: int, pos_b: int) -> dict[str, Any]:
    """A respondent who means pos_a for A and pos_b for B on every TiA item:
    reversed items are answered reversed, everything written as SoSci codes."""
    first, second = (pos_a, pos_b) if order == 1 else (pos_b, pos_a)
    row: dict[str, Any] = {"CASE": case, "MODE": "interview", "K001": order}
    row.update({"VE02": 3, "VE03": 2, "DE01": 1, "DE02": 25})

    def code(n: int, pos: int) -> int:
        return ss.CODE_OF_POSITION[6 - pos if n in ss.TIA_REVERSED else pos]

    for i in ss.TIA_ITEMS:
        row[i.block1] = code(i.number, first)
        row[i.block2] = code(i.number, second)
    row[ss.TIA_ONLY_BLOCK2] = code(19, second)
    row.update({c: ss.CODE_OF_POSITION[3] for c in ss.SUS_BLOCK1 + ss.SUS_BLOCK2})
    return row


def test_prepare_reverses_and_scores_every_subscale() -> None:
    raw = pd.DataFrame([_row(1, 1, pos_a=2, pos_b=4), _row(2, 2, pos_a=5, pos_b=1)])
    long = ss.prepare(raw).long.set_index(["case", "run"])
    # K001 = 1: run 1 is A (umgangssprachlich), K001 = 2: run 1 is B.
    assert long.loc[(1, 1), "condition"] == "A" and long.loc[(1, 1), "order"] == "AB"
    assert long.loc[(2, 1), "condition"] == "B" and long.loc[(2, 1), "order"] == "BA"
    for s in ss.TIA_SUBSCALES:
        assert long.loc[(1, 1), s.key] == 2.0 and long.loc[(1, 2), s.key] == 4.0
        assert long.loc[(2, 1), s.key] == 1.0 and long.loc[(2, 2), s.key] == 5.0
    assert long.loc[(1, 2), "tia_rk19"] == 4.0
    assert math.isnan(long.loc[(1, 1), "tia_rk19"])
    assert long.loc[(1, 1), "sus"] == 50.0
    assert long.loc[(1, 1), "vk_pv"] == 3  # prior knowledge is not recoded


def test_prepare_applies_the_missing_rule_and_counts_it() -> None:
    raw = pd.DataFrame([_row(1, 1, 3, 3), _row(2, 2, 3, 3)])
    raw.loc[0, "VE22"] = -1  # item 9, run 1: Vertrauen (2 items) has no value
    raw.loc[0, "VE14"] = -9  # item 1, run 1: R/K keeps 4 of 5 items
    raw.loc[1, "VE14"] = -1
    raw.loc[1, "VE19"] = -1
    raw.loc[1, "VE23"] = -1  # items 1, 6, 10 run 1: 2 of 5 left, below 3
    raw.loc[0, "VE02"] = -1  # "keine Angabe" in prior knowledge is missing
    prep = ss.prepare(raw)
    long = prep.long.set_index(["case", "run"])
    assert math.isnan(long.loc[(1, 1), "tia_vertrauen"])
    assert long.loc[(1, 1), "tia_rk"] == 3.0
    assert math.isnan(long.loc[(2, 1), "tia_rk"])
    assert math.isnan(long.loc[(1, 1), "vk_pv"])
    miss = _counts(prep)
    # Case 1 is AB (run 1 = A), case 2 is BA (run 1 = B).
    assert miss[("TiA Vertrauen in Automation", 1, "A")]["regel"] == 1
    assert miss[("TiA Vertrauen in Automation", 1, "B")]["regel"] == 0
    rk = "TiA Reliabilität/Kompetenz (ohne Item 19)"
    assert miss[(rk, 1, "A")]["teilweise"] == 1 and miss[(rk, 1, "A")]["regel"] == 0
    assert miss[(rk, 1, "B")]["regel"] == 1
    assert miss[("SUS", 2, "A")]["regel"] == 0


def test_prepare_on_the_synthetic_export() -> None:
    prep = ss.prepare(ss.synthetic_export())
    assert prep.excluded_pretest == 1 and prep.other_modes == {}
    first = prep.long[prep.long["run"] == 1]
    assert len(first) == 16
    assert (first["order"] == "AB").sum() == 8 and (first["order"] == "BA").sum() == 8
    total: dict[tuple[str, int], dict[str, int]] = {}
    for m in prep.missing:
        t = total.setdefault((str(m["messung"]), int(m["durchlauf"])), {})
        for k in ("teilweise", "regel", "leer"):
            t[k] = t.get(k, 0) + int(m[k])
    assert total[("TiA Vertrauen in Automation", 1)]["regel"] == 1
    assert total[("TiA Intention der Entwickler", 2)]["regel"] == 1
    assert total[("TiA Reliabilität/Kompetenz (ohne Item 19)", 1)]["teilweise"] == 1
    assert total[("SUS", 2)] == {"teilweise": 1, "regel": 0, "leer": 0}
    assert total[("SUS", 1)]["regel"] == 1
    assert sorted(prep.items) == [1, 2] and 19 in prep.items[2]


def test_prepare_rejects_missing_order_and_variables() -> None:
    raw = pd.DataFrame([_row(1, 1, 2, 4)])
    raw.loc[0, "K001"] = 3
    with pytest.raises(ValueError, match="K001"):
        ss.prepare(raw)
    with pytest.raises(ValueError, match="V230"):
        ss.prepare(pd.DataFrame([_row(1, 1, 2, 4)]).drop(columns="V230"))


def test_open_decisions_follow_the_constants(monkeypatch: pytest.MonkeyPatch) -> None:
    texts = [d["text"] for d in ss.open_decisions()]
    assert len(texts) == 3 and texts[0].startswith("Nachtrag 2 bestätigen")
    monkeypatch.setattr(ss, "NACHTRAG2_CONFIRMED", True)
    monkeypatch.setattr(ss, "ANALYSIS_RULES_IN_NACHTRAG2", True)
    assert [d["text"][:4] for d in ss.open_decisions()] == ["SUS:"]
