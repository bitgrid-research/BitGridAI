"""
study_sosci.py: SoSci-Survey-Rohdaten der BitGridAI-Studie in Auswertungsform bringen.

Stand: SoSci-Variablenansicht base (bitgrid) vom 14.11.2026, Nachtrag 2 (Entwurf
15.11.2026, Punkt 4 und 9) und TiA-Manual (Körber, deutsch, Tabelle 1).

Festgelegt und getestet:

* **Antwortcodes SUS und TiA sind nicht monoton.** Die Bildschirmposition 1..5
  trägt die SoSci-Codes 1, 3, 4, 5, 2. :data:`LIKERT_RECODE` bildet sie auf die
  Position zurück; -1 ("Keine Angabe") und -9 ("nicht beantwortet") werden zu
  fehlenden Werten. Vorkenntnisse VE02/VE03 sind korrekt 1..5 und bleiben.
* **TiA in Originalreihenfolge.** Durchlauf 1: VE14..VE31 = Items 1..18 (Item 19
  fehlt), Durchlauf 2: V212..V230 = Items 1..19. Die Reihenfolge ist laut
  Nachtrag 2 am Wortlaut der Variablenansicht belegt; :func:`check_item_labels`
  prüft sie erneut, sobald die Texte vorliegen.
* **Umpolung** der Items 5, 7, 10, 15, 16 (6 - x) nach dem Recode.
* **Subskalen statt Gesamtwert** (:data:`TIA_SUBSCALES`): Vertrauen in
  Automation (9, 14) ist die primäre AV; Reliabilität/Kompetenz wird im
  Vergleich ohne Item 19 gerechnet, weil es in Durchlauf 1 fehlt.
* **Fehlwertregel** (:data:`MIN_SHARE_ANSWERED`, :data:`SUS_MAX_MISSING`):
  TiA-Subskalenwert nur, wenn mindestens die Hälfte der Items beantwortet ist,
  bei zwei Items beide. Beim SUS wird höchstens ein fehlendes Item mit der
  Skalenmitte 3 besetzt (Brooke 1996), bei mehr entfällt er. Wie viele Werte
  unvollständig, durch die Regel fehlend oder leer sind, steht je Variante in
  :attr:`Prepared.missing` (Häufung bei einer Variante wäre selbst ein Befund).
* **K001** (Reihenfolge): 1 = Umgangssprachlich -> Technisch (AB),
  2 = Technisch -> Umgangssprachlich (BA). A = umgangssprachlich, B = technisch.
* **MODE**: Fälle mit MODE "pretest" werden ausgeschlossen.

Nur synthetische Daten in Tests (:func:`synthetic_export`); echte SoSci-Exporte
liegen nicht im Repo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# SoSci code -> position on the screen (1 = stimme gar nicht zu ... 5 = voll zu).
# -1 "Keine Angabe" and -9 "nicht beantwortet" are missing (not 0).
LIKERT_RECODE: dict[int, int] = {1: 1, 3: 2, 4: 3, 5: 4, 2: 5}
MISSING_CODES: frozenset[int] = frozenset({-1, -9})
CODE_OF_POSITION: dict[int, int] = {pos: code for code, pos in LIKERT_RECODE.items()}


def _vars(prefix: str, start: int, stop: int) -> list[str]:
    return [
        f"{prefix}{i:02d}" if prefix == "VE" else f"{prefix}{i}"
        for i in range(start, stop + 1)
    ]


SUS_BLOCK1: list[str] = _vars("VE", 4, 13)
SUS_BLOCK2: list[str] = _vars("V", 202, 211)
PRIOR_KNOWLEDGE: list[str] = ["VE02", "VE03"]  # 1..5, not recoded
DEMOGRAPHICS: list[str] = ["DE01", "DE02"]  # SoSci codes, labels in the variable view

TIA_ONLY_BLOCK2 = "V230"
TIA_ONLY_BLOCK2_TEXT = "Ich bin überzeugt von den Fähigkeiten des Systems"


@dataclass(frozen=True)
class TiaItem:
    """One TiA item present in both runs (number = Körber item number)."""

    number: int
    block1: str
    block2: str


TIA_ITEMS: list[TiaItem] = [
    TiaItem(n, b1, b2)
    for n, (b1, b2) in enumerate(
        zip(_vars("VE", 14, 31), _vars("V", 212, 229), strict=True), start=1
    )
]
TIA_ITEM19 = 19  # only in run 2 (V230)

# Körber manual, table 1 (Nachtrag 2, Punkt 4): reversed items.
TIA_REVERSED: frozenset[int] = frozenset({5, 7, 10, 15, 16})


@dataclass(frozen=True)
class Subscale:
    key: str
    name: str
    items: tuple[int, ...]
    role: str  # "primär", "explorativ" or "beschreibend"


TIA_SUBSCALES: tuple[Subscale, ...] = (
    Subscale("tia_vertrauen", "TiA Vertrauen in Automation", (9, 14), "primär"),
    Subscale(
        "tia_rk",
        "TiA Reliabilität/Kompetenz (ohne Item 19)",
        (1, 6, 10, 13, 15),
        "explorativ",
    ),
    Subscale(
        "tia_vv",
        "TiA Verständlichkeit/Vorhersagbarkeit",
        (2, 7, 11, 16),
        "explorativ",
    ),
    Subscale("tia_ie", "TiA Intention der Entwickler", (4, 8), "explorativ"),
    Subscale("tia_vt", "TiA Vertrautheit", (3, 17), "beschreibend"),
    Subscale("tia_nv", "TiA Neigung zu vertrauen", (5, 12, 18), "beschreibend"),
)
# Reliabilität/Kompetenz with item 19, run 2 only, descriptive.
TIA_RK19 = Subscale(
    "tia_rk19",
    "TiA Reliabilität/Kompetenz mit Item 19 (nur Durchlauf 2)",
    (1, 6, 10, 13, 15, 19),
    "beschreibend",
)

# Missing items (Artur, 15.11.2026): a TiA subscale value needs at least this
# share of its items answered, a two-item subscale both (mean of the answered
# items). In the SUS at most SUS_MAX_MISSING of the ten items may be missing;
# such an item gets the scale midpoint SUS_MIDPOINT (Brooke 1996: "they should
# mark the centre point of the scale"), with more missing there is no SUS
# value. The midpoint is the recoded position 3 (SoSci code 4); reversing the
# even items keeps it at 3, both item kinds then contribute 2.
MIN_SHARE_ANSWERED = 0.5
SUS_MAX_MISSING = 1
SUS_MIDPOINT = 3.0


def min_answered(n_items: int) -> int:
    """Fewest answered items for a subscale value (see MIN_SHARE_ANSWERED)."""
    if n_items <= 2:
        return n_items
    return math.ceil(n_items * MIN_SHARE_ANSWERED)


# Decisions that must stand in Nachtrag 2 before the data freeze, otherwise
# they are not preregistered. Turn True only when Nachtrag 2 says so.
NACHTRAG2_CONFIRMED = False  # subscales, reversal, primary DV (draft 15.11.2026)
ANALYSIS_RULES_IN_NACHTRAG2 = False  # missing rule, CI methods, power assumptions
SUS_ORDER_CHECKED = False  # VE04-VE13 / V202-V211 in the standard SUS order


def open_decisions() -> list[dict[str, str]]:
    """Analysis decisions still open in this code, for the freeze check.

    Deterministic: read from the constants above, not estimated.
    """
    out: list[dict[str, str]] = []

    def add(text: str) -> None:
        out.append({"text": text, "where": "study_sosci.py"})

    if not NACHTRAG2_CONFIRMED:
        add(
            "Nachtrag 2 bestätigen: TiA-Subskalen, Umpolung 5/7/10/15/16, primäre"
            " AV Vertrauen in Automation"
        )
    if not ANALYSIS_RULES_IN_NACHTRAG2:
        add(
            "In Nachtrag 2 aufnehmen: Fehlwertregel (TiA-Subskala ab der Hälfte"
            " der Items, bei zwei Items beide; SUS: höchstens ein fehlendes Item,"
            " mit der Skalenmitte 3 besetzt; Zählung je Variante), KI per"
            " Bootstrap und"
            " Hodges-Lehmann, Power-Annahmen"
        )
    if not SUS_ORDER_CHECKED:
        add("SUS: Itemreihenfolge in SoSci gegen die Standardreihenfolge prüfen")
    return out


CONDITION_BY_ORDER = {1: ("A", "B"), 2: ("B", "A")}  # K001 -> (run 1, run 2)
ORDER_LABEL = {1: "AB", 2: "BA"}


def recode_likert(values: pd.Series) -> pd.Series:
    """SoSci codes of a SUS/TiA item -> position 1..5, missing as NaN.

    Unknown codes raise: a silent NaN would hide a changed questionnaire.
    """
    num = pd.to_numeric(values, errors="coerce")
    unknown = set(num.dropna().astype(int)) - set(LIKERT_RECODE) - MISSING_CODES
    if unknown:
        raise ValueError(f"{values.name}: unbekannte Antwortcodes {sorted(unknown)}")
    return num.map(
        lambda v: LIKERT_RECODE.get(int(v), np.nan) if pd.notna(v) else np.nan
    )


def check_item_labels(labels: dict[str, str]) -> list[str]:
    """Compare the item texts of both runs (``labels``: variable -> text from
    the SoSci variable view, not from answers). Returns the problems found;
    an empty list means the pairing is confirmed by text."""
    problems: list[str] = []
    for item in TIA_ITEMS:
        t1, t2 = labels.get(item.block1), labels.get(item.block2)
        if t1 is None or t2 is None:
            problems.append(f"{item.block1}/{item.block2}: Text fehlt")
        elif t1.strip() != t2.strip():
            problems.append(f"{item.block1}/{item.block2}: '{t1}' != '{t2}'")
    if (
        labels.get(TIA_ONLY_BLOCK2, TIA_ONLY_BLOCK2_TEXT).strip()
        != TIA_ONLY_BLOCK2_TEXT
    ):
        problems.append(f"{TIA_ONLY_BLOCK2}: nicht '{TIA_ONLY_BLOCK2_TEXT}'")
    return problems


def sus_score(items: pd.DataFrame) -> pd.Series:
    """SUS 0..100 (Brooke 1996) from ten recoded items in questionnaire order.

    Odd items contribute (x - 1), even items (5 - x), sum times 2.5. Assumes
    the SoSci order is the standard SUS order. Up to SUS_MAX_MISSING missing
    items are set to the midpoint SUS_MIDPOINT (recoded scale); with more
    missing items the value is NaN.
    """
    x = items.to_numpy(dtype=float)
    answered = (~np.isnan(x)).sum(axis=1)
    filled = np.where(np.isnan(x), SUS_MIDPOINT, x)
    contrib = np.where(np.arange(10) % 2 == 0, filled - 1, 5 - filled)
    total = contrib.sum(axis=1) * 2.5
    return pd.Series(
        np.where(answered >= 10 - SUS_MAX_MISSING, total, np.nan), index=items.index
    )


def subscale_score(items: pd.DataFrame, scale: Subscale) -> tuple[pd.Series, pd.Series]:
    """Mean of the subscale items (already recoded and reversed) where the
    missing rule allows it; ``items`` has one column per Körber item number.
    Returns the values and the number of answered items per person."""
    part = items[list(scale.items)]
    answered = part.notna().sum(axis=1)
    value = part.mean(axis=1, skipna=True).where(
        answered >= min_answered(len(scale.items))
    )
    return value, answered


def missing_counts(
    name: str,
    run: int,
    answered: pd.Series,
    n_items: int,
    need: int,
    condition: pd.Series,
) -> list[dict[str, object]]:
    """Per variant: values kept with items missing ("teilweise"), lost by the
    rule ("regel") and with nothing answered ("leer")."""
    out: list[dict[str, object]] = []
    for variant in ("A", "B"):
        a = answered[condition == variant]
        out.append(
            {
                "messung": name,
                "durchlauf": run,
                "variante": variant,
                "teilweise": int(((a >= need) & (a < n_items)).sum()),
                "regel": int(((a > 0) & (a < need)).sum()),
                "leer": int((a == 0).sum()),
            }
        )
    return out


@dataclass
class Prepared:
    """Long format (one row per person and run) plus what was dropped."""

    long: pd.DataFrame
    excluded_pretest: int
    other_modes: dict[str, int]
    notes: list[str]
    # run -> recoded, reversed TiA items (columns = Körber item numbers)
    items: dict[int, pd.DataFrame] = field(default_factory=dict)
    # one row per measure and run: values missing by rule / not answered at all
    missing: list[dict[str, object]] = field(default_factory=list)


def prepare(raw: pd.DataFrame) -> Prepared:
    """SoSci wide export -> one row per person and run.

    Columns of ``long``: case, order (AB/BA), run (1/2), condition (A/B), one
    column per TiA subscale (:data:`TIA_SUBSCALES`), tia_rk19 (run 2 only),
    sus, vk_pv, vk_btc, DE01, DE02.
    """
    df = raw.copy()
    mode = df["MODE"].astype(str).str.strip().str.lower() if "MODE" in df else None
    excluded = 0
    other: dict[str, int] = {}
    if mode is not None:
        is_pre = mode.eq("pretest")
        excluded = int(is_pre.sum())
        df = df[~is_pre]
        rest = mode[~is_pre]
        other = {
            m: int(n) for m, n in rest[rest.ne("interview")].value_counts().items()
        }

    order = pd.to_numeric(df["K001"], errors="coerce")
    bad = sorted(set(order.dropna().astype(int)) - set(CONDITION_BY_ORDER))
    if bad or order.isna().any():
        raise ValueError(f"K001 muss 1 oder 2 sein, gefunden: {bad or 'leer'}")
    needed = (
        SUS_BLOCK1
        + SUS_BLOCK2
        + [i.block1 for i in TIA_ITEMS]
        + [i.block2 for i in TIA_ITEMS]
        + [TIA_ONLY_BLOCK2]
    )
    absent = [c for c in needed if c not in df]
    if absent:
        raise ValueError(f"Variablen fehlen im Export: {absent}")

    case = df["CASE"] if "CASE" in df else pd.Series(df.index, index=df.index)
    items: dict[int, pd.DataFrame] = {}
    missing: list[dict[str, object]] = []
    rows = []
    for run, sus_cols, tia_vars in (
        (1, SUS_BLOCK1, {i.number: i.block1 for i in TIA_ITEMS}),
        (
            2,
            SUS_BLOCK2,
            {**{i.number: i.block2 for i in TIA_ITEMS}, TIA_ITEM19: TIA_ONLY_BLOCK2},
        ),
    ):
        tia = pd.DataFrame(
            {n: recode_likert(df[v]) for n, v in tia_vars.items()}, index=df.index
        )
        for n in TIA_REVERSED:
            tia[n] = 6 - tia[n]
        items[run] = tia
        sus_items = pd.DataFrame(
            {c: recode_likert(df[c]) for c in sus_cols}, index=df.index
        )
        sus = sus_score(sus_items)
        part = pd.DataFrame(
            {
                "case": case,
                "order": order.astype(int).map(ORDER_LABEL),
                "run": run,
                "condition": order.astype(int).map(
                    lambda k: CONDITION_BY_ORDER[k][run - 1]
                ),
            }
        )
        scales = TIA_SUBSCALES + ((TIA_RK19,) if run == 2 else ())
        for scale in scales:
            value, answered = subscale_score(tia, scale)
            part[scale.key] = value
            n_items = len(scale.items)
            missing += missing_counts(
                scale.name,
                run,
                answered,
                n_items,
                min_answered(n_items),
                part["condition"],
            )
        if run == 1:
            part[TIA_RK19.key] = np.nan
        part["sus"] = sus
        missing += missing_counts(
            "SUS",
            run,
            sus_items.notna().sum(axis=1),
            10,
            10 - SUS_MAX_MISSING,
            part["condition"],
        )
        for col, name in (
            ("VE02", "vk_pv"),
            ("VE03", "vk_btc"),
            *zip(DEMOGRAPHICS, DEMOGRAPHICS),
        ):
            src = df[col] if col in df else pd.Series(np.nan, index=df.index)
            value = pd.to_numeric(src, errors="coerce")
            part[name] = value.where(~value.isin(list(MISSING_CODES)))
        rows.append(part)
    notes = [
        "SUS-Wert setzt die Standard-Itemreihenfolge voraus.",
        "TiA-Zuordnung der Items über die Originalreihenfolge (Nachtrag 2);"
        " check_item_labels prüft sie am Wortlaut.",
    ]
    return Prepared(
        pd.concat(rows, ignore_index=True), excluded, other, notes, items, missing
    )


def paired_wide(long: pd.DataFrame, col: str) -> pd.DataFrame:
    """case, order, A, B for one measure; only persons with both values."""
    w = long.pivot_table(
        index=["case", "order"], columns="condition", values=col, aggfunc="first"
    )
    w = w.reset_index()
    for c in ("A", "B"):
        if c not in w:
            w[c] = np.nan
    return w.dropna(subset=["A", "B"])


def synthetic_export(seed: int = 20261115, n: int = 16) -> pd.DataFrame:
    """A SoSci-like wide export with invented answers, for tests and --demo.

    Half the persons AB, half BA, one pretest case. Answers are SoSci codes
    (1, 3, 4, 5, 2), reversed items answered reversed, with a few -1 and -9.
    Condition A is set slightly higher on purpose; this says nothing about
    the real study.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for c in range(n + 1):
        order = 1 if c % 2 == 0 else 2
        person = rng.normal(3.0, 0.5)
        level = {"A": person + 0.4, "B": person}
        row: dict[str, object] = {
            "CASE": 100 + c,
            "MODE": "pretest" if c == n else "interview",
            "K001": order,
            "VE02": int(rng.integers(1, 6)),
            "VE03": int(rng.integers(1, 6)),
            "DE01": int(rng.integers(1, 4)),
            "DE02": int(rng.integers(18, 40)),
        }
        for run, cond in enumerate(CONDITION_BY_ORDER[order], start=1):
            mean = level[cond]
            tia_vars = {i.number: i.block1 if run == 1 else i.block2 for i in TIA_ITEMS}
            if run == 2:
                tia_vars[TIA_ITEM19] = TIA_ONLY_BLOCK2
            for number, var in tia_vars.items():
                pos = int(np.clip(round(rng.normal(mean, 0.7)), 1, 5))
                if number in TIA_REVERSED:
                    pos = 6 - pos
                row[var] = CODE_OF_POSITION[pos]
            sus_cols = SUS_BLOCK1 if run == 1 else SUS_BLOCK2
            for k, var in enumerate(sus_cols):
                pos = int(np.clip(round(rng.normal(mean, 0.7)), 1, 5))
                row[var] = CODE_OF_POSITION[pos if k % 2 == 0 else 6 - pos]
        rows.append(row)
    df = pd.DataFrame(rows)
    # Missing answers: "keine Angabe" (-1) and "nicht beantwortet" (-9).
    df.loc[1, "VE22"] = -1  # item 9 run 1: Vertrauen loses its value (2 items)
    df.loc[2, "V215"] = -9  # item 4 run 2: Intention loses its value
    df.loc[3, "VE14"] = -1  # item 1 run 1: R/K keeps its value (4 of 5)
    df.loc[4, "V205"] = -9  # SUS run 2: one item missing, set to the midpoint
    df.loc[6, "VE05"] = -1  # SUS run 1: two items missing, no value
    df.loc[6, "VE06"] = -9
    df.loc[5, "VE02"] = -1  # prior knowledge "keine Angabe": missing, not recoded
    return df
