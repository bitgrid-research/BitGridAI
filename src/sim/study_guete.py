"""
study_guete.py — Güte-Bewertung der Erklärtexte (FF2).

Während ``study_analysis.py`` das *subjektive* Vertrauen der Probanden auswertet
(FF1), bewertet dieses Modul die *objektive Güte* der Ausgaben (FF2). Zwei Schichten:

  1. Objektive Schicht (automatisch, reproduzierbar): Faithfulness-Vorprüfung aus
     ``study_faithfulness.py`` über das eingefrorene Studien-Set. Da der Kern
     deterministisch ist, ist die wahre Aktion bekannt; Gruppe A (Templates) ist
     konstruktionsbedingt treu und dient als Referenz/Decke.
  2. Rubrik-Schicht (zwei verblindete Rater, je Dimension 0–2): Korrektheit,
     Vollständigkeit, Klarheit; zusätzlich ein Halluzinations-Flag (0/1). Inter-Rater
     Übereinstimmung als quadratisch gewichtetes Cohen's κ.

Die Synthese (Kalibrierung) gehört in die Thesis: deckt die Güte ein etwaiges
Vertrauens-Plus von B (FF1) oder erzeugt B nur „schöneren" Text (Über-Vertrauen)?

  python -m src.sim.study_guete                              # nur objektive Schicht
  python -m src.sim.study_guete --ratings ratings.csv        # + Rubrik-Schicht
  python -m src.sim.study_guete --emit-template ratings.csv  # Rater-CSV-Vorlage schreiben

Rater-CSV-Schema (eine Zeile je sid × group × rater):
  sid,group,rater,korrektheit,vollstaendigkeit,klarheit,halluzination
    sid            — S1..S10
    group          — A | B
    rater          — R1 | R2
    korrektheit    — 0–2 (stimmt die Aussage mit der deterministischen Entscheidung?)
    vollstaendigkeit — 0–2 (Auslöser + relevanter Messwert genannt?)
    klarheit       — 0–2 (laienverständlich, ein Satz, keine Fremdwörter?)
    halluzination  — 0/1 (erfundene Zahl/Aussage? 1 = Penalty)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.sim.study_faithfulness import check_dir

_DEFAULT_DIR = Path("src/sim/study_set")
_RUBRIC_DIMS = ("korrektheit", "vollstaendigkeit", "klarheit")
_RATINGS_TEMPLATE_HEADER = (
    "# guete_ratings.csv — verblindetes 2-Rater-Rubrik-Rating der Erklärtexte (FF2)\n"
    "# Eine Zeile je sid × group × rater. Skala je Dimension 0–2; halluzination 0/1.\n"
    "# Rater bewerten verblindet (A/B-Zuordnung verdeckt; Spalte group hier nur zur Auswertung).\n"
    "sid,group,rater,korrektheit,vollstaendigkeit,klarheit,halluzination\n"
)


# ---------------------------------------------------------------------------
# Objektive Schicht (Faithfulness aus dem eingefrorenen Studien-Set)
# ---------------------------------------------------------------------------


def objective_faithfulness(study_dir: Path) -> dict[str, Any]:
    """Aggregiert die automatische Faithfulness-Vorprüfung über A und B."""
    items = check_dir(study_dir)
    a_consistent = sum(1 for r in items if r["group_a"]["action_consistent"])
    a_has_number = sum(1 for r in items if r["group_a"]["has_number"])

    b_items = [r["group_b"] for r in items if r["group_b"] is not None]
    b_total = len(b_items)
    b_consistent = sum(1 for chk in b_items if chk["action_consistent"])
    b_has_number = sum(1 for chk in b_items if chk["has_number"])

    return {
        "n_scenarios": len(items),
        "group_a": {
            "action_consistent": a_consistent,
            "has_number": a_has_number,
        },
        "group_b": {
            "evaluated": b_total,
            "action_consistent": b_consistent,
            "has_number": b_has_number,
        },
    }


# ---------------------------------------------------------------------------
# Rubrik-Schicht (2 Rater) + Inter-Rater-Reliabilität
# ---------------------------------------------------------------------------


def quadratic_weighted_kappa(r1: list[int], r2: list[int]) -> float:
    """Quadratisch gewichtetes Cohen's κ für zwei gepaarte ordinale Bewertungsreihen."""
    cats = sorted(set(r1) | set(r2))
    if len(cats) < 2 or len(r1) == 0:
        return float("nan")
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    observed = np.zeros((k, k), dtype=float)
    for a, b in zip(r1, r2):
        observed[idx[a], idx[b]] += 1.0
    observed /= float(len(r1))
    row = observed.sum(axis=1)
    col = observed.sum(axis=0)
    expected = np.outer(row, col)
    weights = np.zeros((k, k), dtype=float)
    for i in range(k):
        for j in range(k):
            weights[i, j] = ((i - j) ** 2) / ((k - 1) ** 2)
    denom = float((weights * expected).sum())
    if denom == 0.0:
        return float("nan")
    return 1.0 - float((weights * observed).sum()) / denom


def _kappa_for_dim(df: pd.DataFrame, dim: str) -> float:
    """κ je Dimension: paart Rater R1/R2 über (sid, group)."""
    wide = df.pivot_table(index=["sid", "group"], columns="rater", values=dim)
    if "R1" not in wide.columns or "R2" not in wide.columns:
        return float("nan")
    paired = wide[["R1", "R2"]].dropna()
    if paired.empty:
        return float("nan")
    r1 = [int(round(v)) for v in paired["R1"].tolist()]
    r2 = [int(round(v)) for v in paired["R2"].tolist()]
    return round(quadratic_weighted_kappa(r1, r2), 3)


def rubric_summary(ratings: pd.DataFrame) -> dict[str, Any]:
    """Aggregiert das Rubrik-Rating je Gruppe und die Inter-Rater-Reliabilität."""
    out: dict[str, Any] = {"per_group": {}, "kappa": {}}
    for dim in _RUBRIC_DIMS:
        out["kappa"][dim] = _kappa_for_dim(ratings, dim)

    for group in ("A", "B"):
        g = ratings[ratings["group"].astype(str).str.upper() == group]
        if g.empty:
            continue
        dim_means = {dim: round(float(g[dim].mean()), 3) for dim in _RUBRIC_DIMS}
        guete_total = round(sum(dim_means.values()), 3)  # 0–6
        hallu_rate = round(float(g["halluzination"].mean()), 3)
        out["per_group"][group] = {
            "n_ratings": int(len(g)),
            "dimensions": dim_means,
            "guete_total": guete_total,
            "halluzination_rate": hallu_rate,
        }
    return out


def load_ratings(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, comment="#")
    needed = {"sid", "group", "rater", *_RUBRIC_DIMS, "halluzination"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Rater-CSV fehlen Spalten: {missing}")
    for col in (*_RUBRIC_DIMS, "halluzination"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=[*_RUBRIC_DIMS, "halluzination"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _emit_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_RATINGS_TEMPLATE_HEADER, encoding="utf-8")
    print(f"Rater-CSV-Vorlage geschrieben: {path}")


def _print_objective(obj: dict[str, Any]) -> None:
    n = obj["n_scenarios"]
    a = obj["group_a"]
    b = obj["group_b"]
    print("\n=== OBJEKTIV (Faithfulness-Vorprüfung) ===")
    print(f"  Szenarien: {n}")
    print(
        f"  Gruppe A: action_consistent {a['action_consistent']}/{n}, "
        f"has_number {a['has_number']}/{n} (Template-Referenz)"
    )
    if b["evaluated"]:
        print(
            f"  Gruppe B: action_consistent {b['action_consistent']}/{b['evaluated']}, "
            f"has_number {b['has_number']}/{b['evaluated']}"
        )
    else:
        print("  Gruppe B: noch nicht generiert (OLLAMA_HOST setzen + study_freeze).")


def _print_rubric(rub: dict[str, Any]) -> None:
    print("\n=== RUBRIK (2 Rater, je Dimension 0–2) ===")
    for group, s in rub["per_group"].items():
        dims = ", ".join(f"{d}={v}" for d, v in s["dimensions"].items())
        print(
            f"  Gruppe {group}: {dims} | Güte-Summe {s['guete_total']}/6 | "
            f"Halluzination {s['halluzination_rate']} (n={s['n_ratings']})"
        )
    kappa = ", ".join(f"{d}={v}" for d, v in rub["kappa"].items())
    print(f"  Inter-Rater κ (quadratisch gewichtet): {kappa}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Güte-Bewertung der Erklärtexte (FF2)")
    p.add_argument("--dir", default=str(_DEFAULT_DIR), help="Studien-Set-Verzeichnis")
    p.add_argument("--ratings", default=None, help="Rater-CSV (Rubrik-Schicht)")
    p.add_argument("--out", default=None, help="Ausgabedatei JSON (optional)")
    p.add_argument(
        "--emit-template",
        default=None,
        help="Schreibt eine leere Rater-CSV-Vorlage an den Pfad und beendet sich.",
    )
    args = p.parse_args()

    if args.emit_template:
        _emit_template(Path(args.emit_template))
        return

    result: dict[str, Any] = {"objective": objective_faithfulness(Path(args.dir))}
    _print_objective(result["objective"])

    if args.ratings:
        rub = rubric_summary(load_ratings(Path(args.ratings)))
        result["rubric"] = rub
        _print_rubric(rub)
    else:
        print("\n(Keine Rater-CSV angegeben — nur objektive Schicht ausgewertet.)")

    print(
        "\nHinweis: Gruppe A ist konstruktionsbedingt treu (Template-Interpolation). "
        "Die Kalibrierungsfrage (deckt die Güte ein Vertrauens-Plus von B?) verbindet "
        "diese Werte mit FF1 (study_analysis.py)."
    )

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nErgebnisse gespeichert: {out_path}")


if __name__ == "__main__":
    main()
