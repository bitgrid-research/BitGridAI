"""
study_analysis.py: Statistische Auswertung der BitGridAI-Nutzerstudie (Within-Design).

Design (Nachtrag 2, Kap. 5.7): N = 16, jede Person sieht A (umgangssprachlich) und
B (technisch) in zwei Durchläufen, Reihenfolge je Person aus SoSci K001 (AB/BA).
Aufbereitung (Umcodierung, Umpolung, Subskalen, Fehlwertregel) in study_sosci.py.

Analysen, alle zweiseitig; je Kennwert N, Median und IQR, Effektgröße mit
95-%-KI, p nie allein:

1. H1 (primär): Wilcoxon gepaart A gegen B auf TiA Vertrauen in Automation.
   r = Z / sqrt(N ohne Nulldifferenzen), KI per Bootstrap über Personen;
   Hodges-Lehmann-Schätzer der Differenz A - B mit verteilungsfreiem KI.
2. SUS gepaart, gleich.
3. Explorativ, ohne Korrektur (Anzahl im Bericht): Reliabilität/Kompetenz
   (ohne Item 19), Verständlichkeit/Vorhersagbarkeit, Intention der Entwickler.
   Vertrautheit, Neigung zu vertrauen und R/K mit Item 19 nur beschreibend.
4. Reihenfolge: Differenzen A - B der AB- gegen die BA-Personen, Mann-Whitney.
5. Sensitivität: nur 1. Durchlauf, A gegen B unabhängig (8 gegen 8).
6. Reliabilität je Durchlauf: Spearman-Brown (2 Items), Cronbachs Alpha (sonst).
7. Power: Monte-Carlo für den gepaarten Wilcoxon bei N = 16.

Das Between-Design bis zum Nachtrag vom 17.10.2026 (Mann-Whitney über Gruppen,
Jian-Skala, participants.csv, Power 39,5 %) ist entfernt.

Verwendung:
  python -m src.sim.study_analysis --demo        (synthetische Daten)
  python -m src.sim.study_analysis --sosci data/study/sosci/<export>.csv
Echte Daten nur nach dem Datenfreeze: --sosci verlangt data/study/datenfreeze.txt.
Ausgabe: kennwerte.csv, kennwerte.md, bericht.txt in --out-dir.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from src.sim import study_sosci

REPO = Path(__file__).resolve().parents[2]
FREEZE_RECORD = REPO / "data" / "study" / "datenfreeze.txt"
OUT_REAL = REPO / "data" / "study" / "auswertung"
OUT_DEMO = REPO / "data" / "study" / "auswertung_demo"

SEED = 20261115
N_BOOT = 10_000
ALPHA = 0.05
POWER_N = 16
POWER_DZ: tuple[float, ...] = (0.3, 0.5, 0.8)
POWER_RHO = 0.5
POWER_SIMS = 10_000

LABEL_H1 = "H1: TiA Vertrauen in Automation, A gegen B (Wilcoxon gepaart)"
LABEL_ORDER = "Reihenfolge: Differenz A - B, AB- gegen BA-Personen (Mann-Whitney)"
LABEL_SENS = "Sensitivität: nur 1. Durchlauf, A gegen B unabhängig (Mann-Whitney)"
RIM_NOTE = (
    "vollständig getrennt (alle Differenzen bzw. Ränge auf einer Seite): r liegt am"
    " Rand, das Bootstrap-KI für r ist nicht aussagekräftig"
)


# ---------------------------------------------------------------------------
# Kennwerte
# ---------------------------------------------------------------------------


@dataclass
class Row:
    """One line of the result table. Group 1/2 = A/B, or AB/BA for the order."""

    analyse: str
    messung: str
    rolle: str
    test: str
    vergleich: str
    n: int
    detail: str
    mdn_1: float
    q1_1: float
    q3_1: float
    mdn_2: float
    q1_2: float
    q3_2: float
    statistik: float = math.nan
    p: float = math.nan
    r: float = math.nan
    r_ki_unten: float = math.nan
    r_ki_oben: float = math.nan
    hl: float = math.nan
    hl_ki_unten: float = math.nan
    hl_ki_oben: float = math.nan
    bootstrap_ungueltig: int = 0


def _mdn_iqr(x: np.ndarray) -> tuple[float, float, float]:
    if len(x) == 0:
        return math.nan, math.nan, math.nan
    q1, mdn, q3 = np.percentile(x, [25, 50, 75])
    return float(mdn), float(q1), float(q3)


def _ties(values: np.ndarray) -> float:
    """Sum of t^3 - t over groups of equal values (tie correction)."""
    _, t = np.unique(np.round(values, 9), return_counts=True)
    return float((t.astype(float) ** 3 - t).sum())


def signed_rank_z(d: np.ndarray) -> tuple[float, int, float]:
    """Z of the Wilcoxon signed-rank statistic, positive = A higher.

    Zero differences are dropped (Wilcoxon's method), ties corrected.
    Returns (z, pairs used, W+).
    """
    nz = d[d != 0]
    n = len(nz)
    if n == 0:
        return math.nan, 0, 0.0
    ranks = stats.rankdata(np.abs(nz))
    w_plus = float(ranks[nz > 0].sum())
    var = n * (n + 1) * (2 * n + 1) / 24 - _ties(np.abs(nz)) / 48
    z = (w_plus - n * (n + 1) / 4) / math.sqrt(var) if var > 0 else 0.0
    return z, n, w_plus


def _r_paired(d: np.ndarray) -> float:
    z, n, _ = signed_rank_z(d)
    return z / math.sqrt(n) if n else math.nan


def mann_whitney_z(x: np.ndarray, y: np.ndarray) -> float:
    """Z of the Mann-Whitney U of x, positive = x higher, ties corrected."""
    n1, n2 = len(x), len(y)
    big_n = n1 + n2
    both = np.concatenate([x, y])
    ranks = stats.rankdata(both)
    u1 = float(ranks[:n1].sum()) - n1 * (n1 + 1) / 2
    var = n1 * n2 / 12 * ((big_n + 1) - _ties(both) / (big_n * (big_n - 1)))
    return (u1 - n1 * n2 / 2) / math.sqrt(var) if var > 0 else 0.0


def _r_mw(x: np.ndarray, y: np.ndarray) -> float:
    return mann_whitney_z(x, y) / math.sqrt(len(x) + len(y))


def _percentile_ci(values: list[float]) -> tuple[float, float, int]:
    arr = np.asarray(values, dtype=float)
    ok = arr[np.isfinite(arr)]
    if len(ok) == 0:
        return math.nan, math.nan, len(arr)
    lo, hi = np.percentile(ok, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])
    return float(lo), float(hi), int(len(arr) - len(ok))


def signed_rank_null(n: int) -> np.ndarray:
    """Exact null distribution of W+ for n pairs without ties (counts)."""
    m = n * (n + 1) // 2
    counts = np.zeros(m + 1)
    counts[0] = 1.0
    for rank in range(1, n + 1):
        nxt = counts.copy()
        nxt[rank:] += counts[: m + 1 - rank]
        counts = nxt
    return counts


def _critical(n: int) -> int:
    """Largest w with P(W+ <= w) <= alpha/2 (exact); -1 if none exists."""
    cdf = np.cumsum(signed_rank_null(n)) / 2.0**n
    below = np.nonzero(cdf <= ALPHA / 2)[0]
    return int(below[-1]) if len(below) else -1


def hodges_lehmann_paired(d: np.ndarray) -> tuple[float, float, float]:
    """Median of the Walsh averages of d with the distribution-free CI
    (Hollander and Wolfe; exact without ties, approximate with ties)."""
    n = len(d)
    if n == 0:
        return math.nan, math.nan, math.nan
    i, j = np.triu_indices(n)
    walsh = np.sort((d[i] + d[j]) / 2)
    est = float(np.median(walsh))
    k = _critical(n) + 1  # 1-based rank of the lower bound
    if k < 1:
        return est, math.nan, math.nan
    return est, float(walsh[k - 1]), float(walsh[len(walsh) - k])


def wilcoxon_paired(
    analyse: str,
    messung: str,
    rolle: str,
    a: np.ndarray,
    b: np.ndarray,
    rng: np.random.Generator,
    n_boot: int,
) -> Row:
    """Paired A against B: medians, Wilcoxon p, r with bootstrap CI, HL."""
    d = a - b
    _, n_used, _ = signed_rank_z(d)
    zeros = int((d == 0).sum())
    ma, a1, a3 = _mdn_iqr(a)
    mb, b1, b3 = _mdn_iqr(b)
    row = Row(
        analyse,
        messung,
        rolle,
        "Wilcoxon gepaart",
        "A gegen B",
        len(d),
        f"{zeros} Nulldifferenzen ausgeschlossen, {n_used} Paare im Test",
        ma,
        a1,
        a3,
        mb,
        b1,
        b3,
    )
    if n_used == 0:
        return row
    res = stats.wilcoxon(d, zero_method="wilcox", alternative="two-sided")
    row.statistik = float(res.statistic)
    row.p = float(res.pvalue)
    row.r = _r_paired(d)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    row.r_ki_unten, row.r_ki_oben, row.bootstrap_ungueltig = _percentile_ci(
        [_r_paired(d[k]) for k in idx]
    )
    row.hl, row.hl_ki_unten, row.hl_ki_oben = hodges_lehmann_paired(d)
    nz = d[d != 0]
    if (nz > 0).all() or (nz < 0).all():
        # Every resample then sits at the bound of r: the percentile CI
        # collapses and would look precise. Say so instead.
        row.detail += f"; {RIM_NOTE}"
    return row


def mann_whitney(
    analyse: str,
    messung: str,
    rolle: str,
    vergleich: str,
    x: np.ndarray,
    y: np.ndarray,
    detail: str,
    rng: np.random.Generator,
    n_boot: int,
) -> Row:
    """Independent groups x against y: medians, U, p, r with bootstrap CI
    (resampled within each group)."""
    m1, x1, x3 = _mdn_iqr(x)
    m2, y1, y3 = _mdn_iqr(y)
    row = Row(
        analyse,
        messung,
        rolle,
        "Mann-Whitney-U",
        vergleich,
        len(x) + len(y),
        detail,
        m1,
        x1,
        x3,
        m2,
        y1,
        y3,
    )
    if len(x) == 0 or len(y) == 0:
        return row
    res = stats.mannwhitneyu(x, y, alternative="two-sided", method="auto")
    row.statistik = float(res.statistic)
    row.p = float(res.pvalue)
    row.r = _r_mw(x, y)
    ix = rng.integers(0, len(x), size=(n_boot, len(x)))
    iy = rng.integers(0, len(y), size=(n_boot, len(y)))
    row.r_ki_unten, row.r_ki_oben, row.bootstrap_ungueltig = _percentile_ci(
        [_r_mw(x[i], y[j]) for i, j in zip(ix, iy, strict=True)]
    )
    if x.max() < y.min() or x.min() > y.max():
        row.detail += f"; {RIM_NOTE}"
    return row


def descriptive(
    analyse: str, messung: str, a: np.ndarray, b: np.ndarray, detail: str
) -> Row:
    """Medians and IQR only, no test."""
    ma, a1, a3 = _mdn_iqr(a)
    mb, b1, b3 = _mdn_iqr(b)
    return Row(
        analyse,
        messung,
        "beschreibend",
        "keiner",
        "A gegen B",
        len(a) + len(b) if detail.startswith("unabhängig") else len(a),
        detail,
        ma,
        a1,
        a3,
        mb,
        b1,
        b3,
    )


# ---------------------------------------------------------------------------
# Reliabilität und Power
# ---------------------------------------------------------------------------


def cronbach_alpha(items: pd.DataFrame) -> tuple[float, int]:
    """Alpha over complete cases; (alpha, n)."""
    x = items.dropna().to_numpy(dtype=float)
    n, k = x.shape
    if n < 2 or k < 2:
        return math.nan, n
    total = x.sum(axis=1).var(ddof=1)
    if total == 0:
        return math.nan, n
    return float(k / (k - 1) * (1 - x.var(axis=0, ddof=1).sum() / total)), n


def spearman_brown(items: pd.DataFrame) -> tuple[float, int]:
    """Spearman-Brown of a two-item scale (Eisinga et al. 2013); (rho, n)."""
    x = items.dropna().to_numpy(dtype=float)
    n = len(x)
    if n < 3 or x[:, 0].std() == 0 or x[:, 1].std() == 0:
        return math.nan, n
    r = float(np.corrcoef(x[:, 0], x[:, 1])[0, 1])
    return 2 * r / (1 + r), n


def reliability(prep: study_sosci.Prepared) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for run, items in sorted(prep.items.items()):
        for scale in study_sosci.TIA_SUBSCALES:
            part = items[list(scale.items)]
            if len(scale.items) == 2:
                value, n = spearman_brown(part)
                kind = "Spearman-Brown"
            else:
                value, n = cronbach_alpha(part)
                kind = "Cronbachs Alpha"
            out.append(
                {
                    "messung": scale.name,
                    "durchlauf": run,
                    "kennwert": kind,
                    "wert": value,
                    "n": n,
                    "items": len(scale.items),
                }
            )
    return out


def paired_power(
    n: int = POWER_N,
    dz_values: tuple[float, ...] = POWER_DZ,
    rho: float = POWER_RHO,
    sims: int = POWER_SIMS,
    seed: int = SEED,
) -> list[dict[str, float]]:
    """Monte-Carlo power of the two-sided paired Wilcoxon (exact critical value).

    Both measurements normal with correlation rho; the mean difference is set
    so that the standardized difference is dz. With dz given, rho only shapes
    the raw values, the power depends on dz alone.
    """
    rng = np.random.default_rng(seed)
    crit = _critical(n)
    m = n * (n + 1) // 2
    cov = [[1.0, rho], [rho, 1.0]]
    out = []
    for dz in dz_values:
        delta = dz * math.sqrt(2 * (1 - rho))
        xy = rng.multivariate_normal([delta, 0.0], cov, size=(sims, n))
        d = xy[..., 0] - xy[..., 1]
        ranks = np.abs(d).argsort(axis=1).argsort(axis=1) + 1
        w_plus = (ranks * (d > 0)).sum(axis=1)
        reject = (w_plus <= crit) | (w_plus >= m - crit)
        out.append(
            {
                "dz": dz,
                "power": float(reject.mean()),
                "n": n,
                "rho": rho,
                "simulationen": sims,
                "alpha": ALPHA,
            }
        )
    return out


# ---------------------------------------------------------------------------
# Auswertung
# ---------------------------------------------------------------------------


def run_within_tests(
    prep: study_sosci.Prepared,
    n_boot: int = N_BOOT,
    seed: int = SEED,
    power_sims: int = POWER_SIMS,
) -> dict[str, Any]:
    """All analyses of the within design (see module docstring)."""
    rng = np.random.default_rng(seed)
    long = prep.long
    rows: list[Row] = []
    primary = study_sosci.TIA_SUBSCALES[0]

    def paired(key: str) -> pd.DataFrame:
        return study_sosci.paired_wide(long, key)

    def arrays(w: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        return w["A"].to_numpy(dtype=float), w["B"].to_numpy(dtype=float)

    # 1 and 2: H1 and SUS
    w = paired(primary.key)
    rows.append(
        wilcoxon_paired(LABEL_H1, primary.name, "primär", *arrays(w), rng, n_boot)
    )
    rows.append(
        wilcoxon_paired(
            "SUS, A gegen B (Wilcoxon gepaart)",
            "SUS (0-100)",
            "sekundär",
            *arrays(paired("sus")),
            rng,
            n_boot,
        )
    )
    # 3: exploratory and descriptive subscales
    explorative = 0
    for scale in study_sosci.TIA_SUBSCALES[1:]:
        a, b = arrays(paired(scale.key))
        if scale.role == "explorativ":
            explorative += 1
            rows.append(
                wilcoxon_paired(
                    f"Explorativ: {scale.name} (Wilcoxon gepaart)",
                    scale.name,
                    "explorativ",
                    a,
                    b,
                    rng,
                    n_boot,
                )
            )
        else:
            rows.append(
                descriptive(f"Beschreibend: {scale.name}", scale.name, a, b, "gepaart")
            )
    run2 = long[long["run"] == 2]
    rk19 = study_sosci.TIA_RK19
    rows.append(
        descriptive(
            f"Beschreibend: {rk19.name}",
            rk19.name,
            run2.loc[run2["condition"] == "A", rk19.key].dropna().to_numpy(dtype=float),
            run2.loc[run2["condition"] == "B", rk19.key].dropna().to_numpy(dtype=float),
            "unabhängig (nur Durchlauf 2, je Person eine Variante)",
        )
    )
    # 4 and 5: order effect and sensitivity, for the primary DV and the SUS
    first = long[long["run"] == 1]
    for key, name in ((primary.key, primary.name), ("sus", "SUS (0-100)")):
        wk = paired(key)
        diff = (wk["A"] - wk["B"]).to_numpy(dtype=float)
        orders = wk["order"].to_numpy()
        ab, ba = diff[orders == "AB"], diff[orders == "BA"]
        rows.append(
            mann_whitney(
                LABEL_ORDER,
                name,
                "Kontrolle",
                "AB gegen BA (Differenz A - B)",
                ab,
                ba,
                f"{len(ab)} AB, {len(ba)} BA",
                rng,
                n_boot,
            )
        )
        xa = first.loc[first["condition"] == "A", key].dropna().to_numpy(dtype=float)
        xb = first.loc[first["condition"] == "B", key].dropna().to_numpy(dtype=float)
        rows.append(
            mann_whitney(
                LABEL_SENS,
                name,
                "Sensitivität",
                "A gegen B",
                xa,
                xb,
                f"{len(xa)} A, {len(xb)} B",
                rng,
                n_boot,
            )
        )

    persons = long[long["run"] == 1]
    sample: dict[str, Any] = {
        "n": int(len(persons)),
        "ab": int((persons["order"] == "AB").sum()),
        "ba": int((persons["order"] == "BA").sum()),
        "pretest_ausgeschlossen": prep.excluded_pretest,
        "andere_modi": prep.other_modes,
    }
    for col, name in (
        ("vk_pv", "Vorkenntnisse PV"),
        ("vk_btc", "Vorkenntnisse Bitcoin"),
    ):
        vals = persons[col].dropna().to_numpy(dtype=float)
        mdn, q1, q3 = _mdn_iqr(vals)
        sample[name] = {"n": int(len(vals)), "mdn": mdn, "q1": q1, "q3": q3}
    for col in study_sosci.DEMOGRAPHICS:
        counts = persons[col].dropna().astype(int).value_counts().sort_index()
        sample[col] = {str(k): int(v) for k, v in counts.items()}

    return {
        "rows": [asdict(r) for r in rows],
        "reliabilitaet": reliability(prep),
        "power": paired_power(sims=power_sims, seed=seed),
        "fehlwerte": prep.missing,
        "stichprobe": sample,
        "explorative_tests": explorative,
        "n_boot": n_boot,
        "seed": seed,
        "notes": list(prep.notes),
        "synthetisch": False,
    }


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------


def _effect_label(r: float) -> str:
    """Conventions for r (Cohen 1988): .1 small, .3 medium, .5 large."""
    a = abs(r)
    if a < 0.1:
        return "trivial"
    if a < 0.3:
        return "klein"
    if a < 0.5:
        return "mittel"
    return "groß"


def _de(v: float, digits: int = 2) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    return f"{v:.{digits}f}".replace(".", ",")


def _p(v: float) -> str:
    if math.isnan(v):
        return "–"
    return "< 0,001" if v < 0.001 else _de(v, 3)


def _row_text(r: dict[str, Any]) -> str:
    g1, g2 = r["vergleich"].split(" gegen ")[0], r["vergleich"].split(" gegen ")[1]
    g2 = g2.split(" (")[0]
    text = (
        f"{r['messung']}: {g1} Mdn {_de(r['mdn_1'])} (IQR {_de(r['q1_1'])} bis"
        f" {_de(r['q3_1'])}), {g2} Mdn {_de(r['mdn_2'])} (IQR {_de(r['q1_2'])} bis"
        f" {_de(r['q3_2'])})"
    )
    if r["test"] == "keiner":
        return text + f"; {r['detail']}, N = {r['n']}."
    text += (
        f"; {r['test']}: Statistik = {_de(r['statistik'], 1)},"
        f" p {'< 0,001' if r['p'] < 0.001 else '= ' + _p(r['p'])},"
        f" r = {_de(r['r'])} [95-%-KI {_de(r['r_ki_unten'])}; {_de(r['r_ki_oben'])}]"
        f" ({_effect_label(r['r']) if not math.isnan(r['r']) else 'nicht berechenbar'}),"
        f" N = {r['n']} ({r['detail']})"
    )
    if not math.isnan(r["hl"]):
        text += (
            f"; Differenz A - B nach Hodges-Lehmann {_de(r['hl'])}"
            f" [95-%-KI {_de(r['hl_ki_unten'])}; {_de(r['hl_ki_oben'])}]"
        )
    if r["bootstrap_ungueltig"]:
        text += f"; {r['bootstrap_ungueltig']} Bootstrap-Ziehungen ohne Wert"
    return text + "."


KINDS = (
    ("teilweise", "mit fehlenden Items verwendet"),
    ("regel", "durch die Regel fehlend"),
    ("leer", "ganz unbeantwortet"),
)


def missing_lines(fehlwerte: list[dict[str, Any]]) -> list[str]:
    """Missing values per measure and variant (both runs together), and a
    note when one variant has clearly more: that would be a finding itself
    (items not understood): then they are not missing at random, and the
    midpoint for a missing SUS item is less harmless than it looks."""
    lines = [
        "Fehlwerte je Variante (beide Durchläufe): TiA-Subskala ab der Hälfte der"
        " Items (bei zwei Items beide), SUS bei höchstens einem fehlenden Item"
        " mit der Skalenmitte 3 besetzt (Brooke 1996)."
    ]
    totals = {"A": 0, "B": 0}
    by_measure: dict[str, dict[str, dict[str, int]]] = {}
    for m in fehlwerte:
        per = by_measure.setdefault(str(m["messung"]), {})
        cell = per.setdefault(str(m["variante"]), {k: 0 for k, _ in KINDS})
        for k, _ in KINDS:
            cell[k] += int(m[k])
            totals[str(m["variante"])] += int(m[k])
    for measure, per in by_measure.items():
        parts = []
        for variant in ("A", "B"):
            cell = per.get(variant, {})
            found = [f"{cell[k]} {label}" for k, label in KINDS if cell.get(k)]
            if found:
                parts.append(f"{variant}: " + ", ".join(found))
        if parts:
            lines.append(f"  {measure}: " + "; ".join(parts) + ".")
    if totals["A"] + totals["B"] == 0:
        lines.append("  keine fehlenden Werte.")
    elif abs(totals["A"] - totals["B"]) >= 2:
        lines.append(
            f"  ACHTUNG: Fehlwerte ungleich verteilt (A {totals['A']}, B"
            f" {totals['B']}). Möglicherweise wurden Items einer Variante nicht"
            " verstanden; dann fehlen sie nicht zufällig. In Kap. 7 berichten."
        )
    return lines


def report(results: dict[str, Any]) -> str:
    rows = results["rows"]
    s = results["stichprobe"]
    lines: list[str] = []
    if results.get("synthetisch"):
        lines += [
            "SYNTHETISCHE DATEN (--demo): nichts davon ist ein Studienergebnis.",
            "",
        ]
    lines += [
        "Auswertung BitGridAI-Studie, Within-Design (alle Tests zweiseitig, alpha = 0,05)",
        f"Stichprobe: N = {s['n']} ({s['ab']} AB, {s['ba']} BA); Pretest ausgeschlossen:"
        f" {s['pretest_ausgeschlossen']}.",
    ]
    if s["andere_modi"]:
        lines.append(f"WARNUNG: MODE-Werte außer interview: {s['andere_modi']}")
    for name in ("Vorkenntnisse PV", "Vorkenntnisse Bitcoin"):
        v = s[name]
        lines.append(
            f"{name} (1 bis 5): Mdn {_de(v['mdn'], 1)} (IQR {_de(v['q1'], 1)} bis"
            f" {_de(v['q3'], 1)}), n = {v['n']}."
        )
    for col in study_sosci.DEMOGRAPHICS:
        lines.append(f"{col} (SoSci-Codes, Bedeutung laut Variablenansicht): {s[col]}")
    lines.append("")
    lines += missing_lines(results["fehlwerte"])
    sections = (
        ("primär", "Primär (H1)"),
        ("sekundär", "Sekundär"),
        (
            "explorativ",
            f"Explorativ ({results['explorative_tests']} Tests, ohne Korrektur für"
            " multiples Testen)",
        ),
        ("beschreibend", "Nur beschreibend"),
        ("Kontrolle", "Reihenfolgeeffekt"),
        ("Sensitivität", "Sensitivität (nur 1. Durchlauf)"),
    )
    for role, title in sections:
        lines += ["", title + ":"]
        lines += [f"  {_row_text(r)}" for r in rows if r["rolle"] == role]
    lines += ["", "Reliabilität (je Durchlauf, vollständige Fälle):"]
    for rel in results["reliabilitaet"]:
        lines.append(
            f"  {rel['messung']}, Durchlauf {rel['durchlauf']}: {rel['kennwert']}"
            f" {_de(rel['wert'])} ({rel['items']} Items, n = {rel['n']})"
        )
    lines += [
        "",
        "Power des gepaarten Wilcoxon (Monte-Carlo, zweiseitig, exakter kritischer"
        " Wert, Seed fest):",
    ]
    for pw in results["power"]:
        lines.append(
            f"  dz = {_de(pw['dz'], 1)}: {_de(100 * pw['power'], 1)} %"
            f" (N = {pw['n']}, Korrelation {_de(pw['rho'], 1)},"
            f" {pw['simulationen']} Simulationen)"
        )
    lines += [
        "",
        f"KI für r: Perzentil-Bootstrap über Personen, {results['n_boot']} Ziehungen,"
        f" Seed {results['seed']}. KI für Hodges-Lehmann: verteilungsfrei über die"
        " Walsh-Mittel (exakt ohne Bindungen, mit Bindungen angenähert).",
        "p nie allein lesen: immer mit Effektgröße, KI und N. Ein nicht signifikantes"
        " Ergebnis schließt mittlere Effekte bei N = 16 nicht aus.",
    ]
    lines += [f"Hinweis: {n}" for n in results["notes"]]
    return "\n".join(lines) + "\n"


_TABLE_COLS = (
    "analyse",
    "messung",
    "rolle",
    "test",
    "vergleich",
    "n",
    "detail",
    "mdn_1",
    "q1_1",
    "q3_1",
    "mdn_2",
    "q1_2",
    "q3_2",
    "statistik",
    "p",
    "r",
    "r_ki_unten",
    "r_ki_oben",
    "hl",
    "hl_ki_unten",
    "hl_ki_oben",
)


def markdown(results: dict[str, Any]) -> str:
    head = "| " + " | ".join(_TABLE_COLS) + " |"
    sep = "|" + "---|" * len(_TABLE_COLS)
    body = []
    for r in results["rows"]:
        cells = []
        for c in _TABLE_COLS:
            v = r[c]
            if c == "p":
                cells.append(_p(v))
            elif isinstance(v, float):
                cells.append(_de(v))
            else:
                cells.append(str(v))
        body.append("| " + " | ".join(cells) + " |")
    lines = []
    if results.get("synthetisch"):
        lines += ["**SYNTHETISCHE DATEN, kein Studienergebnis.**", ""]
    lines += ["## Kennwerte", "", head, sep, *body, "", "## Reliabilität", ""]
    lines += [
        "| Messung | Durchlauf | Kennwert | Wert | Items | n |",
        "|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {x['messung']} | {x['durchlauf']} | {x['kennwert']} | {_de(x['wert'])}"
        f" | {x['items']} | {x['n']} |"
        for x in results["reliabilitaet"]
    ]
    lines += [
        "",
        "## Power (gepaarter Wilcoxon)",
        "",
        "| dz | Power | N | Korrelation |",
    ]
    lines += ["|---|---|---|---|"]
    lines += [
        f"| {_de(x['dz'], 1)} | {_de(100 * x['power'], 1)} % | {x['n']} | {_de(x['rho'], 1)} |"
        for x in results["power"]
    ]
    return "\n".join(lines) + "\n"


def write_outputs(results: dict[str, Any], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(results["rows"])
    paths = [
        out_dir / "kennwerte.csv",
        out_dir / "kennwerte.md",
        out_dir / "bericht.txt",
    ]
    table.to_csv(paths[0], sep=";", decimal=",", index=False, encoding="utf-8-sig")
    paths[1].write_text(markdown(results), encoding="utf-8")
    paths[2].write_text(report(results), encoding="utf-8")
    return paths


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="BitGridAI Studie, Auswertung (within)")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--sosci", help="SoSci-Rohexport (CSV), nur nach dem Datenfreeze")
    src.add_argument("--demo", action="store_true", help="synthetische Daten")
    p.add_argument("--out-dir", default=None, help="Ausgabeordner")
    p.add_argument("--n-boot", type=int, default=N_BOOT)
    p.add_argument("--power-sims", type=int, default=POWER_SIMS)
    args = p.parse_args(argv)

    if args.sosci:
        if not FREEZE_RECORD.exists():
            print(
                f"Abbruch: {FREEZE_RECORD} fehlt. Echte Daten erst nach dem"
                " Datenfreeze auswerten (zum Testen: --demo).",
                file=sys.stderr,
            )
            return 2
        raw = pd.read_csv(args.sosci, sep=None, engine="python", encoding="utf-8-sig")
        out_dir = Path(args.out_dir) if args.out_dir else OUT_REAL
    else:
        raw = study_sosci.synthetic_export()
        out_dir = Path(args.out_dir) if args.out_dir else OUT_DEMO
    results = run_within_tests(
        study_sosci.prepare(raw), n_boot=args.n_boot, power_sims=args.power_sims
    )
    results["synthetisch"] = bool(args.demo)
    paths = write_outputs(results, out_dir)
    print(report(results))
    for path in paths:
        print(f"geschrieben: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
