"""
study_analysis.py — Statistische Auswertung der BitGridAI-Nutzerstudie.

Design: Mixed, Einzelsitzung (N = 16). Between-Faktor Gruppe A (statischer
Regeltext, n = 8) vs. Gruppe B (LLM-Erklärung, n = 8; keine Personas). Primäre AV
ist das Nutzervertrauen (Automation-Trust-Skala, Jian 2000, Summe 12–84). Am Ende
sieht jede Person beide Varianten und gibt ein Within-Vergleichsrating ab
(Forced-Choice + 7-stufiges Vergleichsrating). Es gibt keine Prä/Post-Messung.

Forschungsfragen:
  FF1 (Vertrauen): Erhöhen LLM-Erklärungen (B) das Vertrauen gegenüber A?
  FF2 (Güte):      objektiv/separat in study_guete.py (Faithfulness + Rubrik).

Eingabe:
  events.parquet   — Parquet aus /research/export (ZIP entpackt)
  participants.csv — Fragebogen-/Score-Daten je Proband; Schema:
    participant_id,group,trust,sus,tlx,fc_pref,trust_compare,
    technikaffinitaet,btc_vorwissen

Ausgabe:
  Konsole: alle Tests im Format  stat=..., p=..., effect=... (N=...)
  Datei:   study_results.json   (maschinenlesbar für die Thesis)

Verwendung:
  python -m src.sim.study_analysis \\
    --events data/study/events_merged.parquet \\
    --participants data/study/participants.csv \\
    [--out data/study/study_results.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Einheitliches Test-Ergebnis (Mann-Whitney / Wilcoxon / Binomial)
# ---------------------------------------------------------------------------


@dataclass
class StatResult:
    """Ergebnis eines Tests mit Effektgröße.

    ``effect_name`` ist "r" (rangbiseriale/­z-basierte Effektgröße nach Field 2018)
    bei Mann-Whitney und Wilcoxon, "p_hat" (Anteil B-Präferenz) beim Binomialtest.
    """

    label: str
    test: str
    statistic: float
    p: float
    effect: float
    effect_name: str
    N: int


def _mann_whitney(
    label: str, x: np.ndarray, y: np.ndarray, alternative: str = "two-sided"
) -> StatResult:
    """Mann-Whitney-U mit r = Z / sqrt(N_total) nach Field 2018.

    ``alternative`` wird an scipy weitergereicht: "greater" testet die gerichtete
    Hypothese x > y (z.B. H1: Gruppe B > Gruppe A), sonst "two-sided".
    """
    n1, n2 = len(x), len(y)
    N = n1 + n2
    result = stats.mannwhitneyu(x, y, alternative=alternative, method="auto")
    U = float(result.statistic)
    p = float(result.pvalue)

    # Z via Normalapproximation der U-Verteilung
    mu_u = n1 * n2 / 2.0
    sigma_u = math.sqrt(n1 * n2 * (N + 1) / 12.0)
    z = abs(U - mu_u) / sigma_u if sigma_u > 0 else 0.0
    r = z / math.sqrt(N) if N > 0 else 0.0
    return StatResult(label, "mann_whitney", round(U, 1), p, round(r, 3), "r", N)


def _wilcoxon_vs_const(
    label: str, x: np.ndarray, const: float, alternative: str = "two-sided"
) -> StatResult:
    """Wilcoxon-Vorzeichen-Rang-Test der Differenzen (x - const) gegen 0.

    Für das Within-Vergleichsrating (z.B. 1..7, Mitte 4 = "gleiches Vertrauen"):
    testet, ob die Bewertungen systematisch über der neutralen Mitte liegen.
    Effektgröße r = Z / sqrt(n_eff) (Nullen ausgeschlossen).
    """
    diffs = x - const
    n = int(np.count_nonzero(diffs))
    if n == 0:
        return StatResult(label, "wilcoxon", 0.0, 1.0, 0.0, "r", 0)
    result = stats.wilcoxon(diffs, alternative=alternative, zero_method="wilcox")
    W = float(result.statistic)
    p = float(result.pvalue)

    # Z via Normalapproximation der Vorzeichen-Rang-Verteilung
    mu_w = n * (n + 1) / 4.0
    sigma_w = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    z = abs(W - mu_w) / sigma_w if sigma_w > 0 else 0.0
    r = z / math.sqrt(n)
    return StatResult(label, "wilcoxon", round(W, 1), p, round(r, 3), "r", n)


def _binomial(label: str, k: int, n: int, alternative: str = "greater") -> StatResult:
    """Exakter Binomial-/Vorzeichentest: k von n Probanden präferieren B (H0: p=0,5).

    Effektmaß ist der beobachtete Anteil p_hat = k / n.
    """
    if n == 0:
        return StatResult(label, "binomial", 0.0, 1.0, 0.0, "p_hat", 0)
    result = stats.binomtest(k, n, 0.5, alternative=alternative)
    p = float(result.pvalue)
    return StatResult(label, "binomial", float(k), p, round(k / n, 3), "p_hat", n)


def _col(df: pd.DataFrame, col: str) -> np.ndarray:
    """Numerische Spalte als NaN-bereinigtes float-Array (leer, wenn Spalte fehlt)."""
    if col not in df.columns:
        return np.array([], dtype=float)
    return pd.to_numeric(df[col], errors="coerce").dropna().to_numpy(dtype=float)


# ---------------------------------------------------------------------------
# Override-Kennzahlen aus Parquet ableiten (behaviorale Verlässlichkeit)
# ---------------------------------------------------------------------------


def compute_override_rates(
    events: pd.DataFrame, participants: pd.DataFrame
) -> pd.DataFrame:
    """Berechnet Override-Rate (Anteil OVERRIDE-Trigger) pro Proband.

    Erfordert Spalte 'participant_id' in events. Wenn nicht vorhanden,
    wird participants unverändert zurückgegeben (kein Fehler, nur Warnung).
    """
    if "participant_id" not in events.columns:
        print(
            "WARNUNG: events.parquet enthält keine participant_id-Spalte — "
            "Override-Rate kann nicht berechnet werden."
        )
        return participants.copy()

    totals = events.groupby("participant_id").size().rename("events_total")
    overrides = (
        events[events["trigger"] == "OVERRIDE"]
        .groupby("participant_id")
        .size()
        .rename("override_count")
    )
    rates = pd.concat([totals, overrides], axis=1).fillna(0)
    rates["override_rate"] = rates["override_count"] / rates["events_total"]

    r3_attempts = (
        events[
            (events["trigger"] == "OVERRIDE")
            & (events["decision_code"].str.startswith("STOP_R3"))
        ]
        .groupby("participant_id")
        .size()
        .rename("r3_override_attempts")
        .reindex(rates.index, fill_value=0)
    )
    rates = rates.join(r3_attempts)

    return participants.merge(rates.reset_index(), on="participant_id", how="left")


# ---------------------------------------------------------------------------
# Statistische Tests (Single-Session, Gruppe A vs. B)
# ---------------------------------------------------------------------------


def run_all_tests(df: pd.DataFrame) -> dict[str, Any]:
    """Führt die vordefinierten Tests durch.

    Pflichtspalten: group (A/B), trust (12–84). Within: fc_pref (A/B/tie),
    trust_compare (1–7, Mitte 4). Optional: sus, tlx sowie Override-Spalten
    (override_rate, r3_override_attempts) aus :func:`compute_override_rates`.
    """
    a = df[df["group"] == "A"]
    b = df[df["group"] == "B"]

    results: dict[str, Any] = {
        "primary": [],
        "within": [],
        "secondary": [],
    }

    # ------------------------------------------------------------------
    # H1 (primär, gerichtet, between): Vertrauen Gruppe B > Gruppe A
    # ------------------------------------------------------------------
    results["primary"].append(
        asdict(
            _mann_whitney(
                "H1: Vertrauen Jian-Summe (Gruppe B > A, einseitig, between)",
                _col(b, "trust"),
                _col(a, "trust"),
                alternative="greater",
            )
        )
    )

    # ------------------------------------------------------------------
    # H2 (within, gerichtet): Direktvergleich beider Varianten (N=16)
    # ------------------------------------------------------------------
    if "fc_pref" in df.columns:
        fc = df["fc_pref"].astype(str).str.strip().str.upper()
        fc = fc[fc.isin(["A", "B"])]  # Unentschieden (tie) ausgeschlossen
        if len(fc) > 0:
            k = int((fc == "B").sum())
            results["within"].append(
                asdict(
                    _binomial(
                        "H2a: Forced-Choice B vs. A (Vorzeichentest, B > Zufall)",
                        k,
                        int(len(fc)),
                        alternative="greater",
                    )
                )
            )

    tc = _col(df, "trust_compare")
    if len(tc) > 0:
        results["within"].append(
            asdict(
                _wilcoxon_vs_const(
                    "H2b: Vergleichsrating vs. Mitte 4 (Wilcoxon, B-Seite > Mitte)",
                    tc,
                    4.0,
                    alternative="greater",
                )
            )
        )

    # ------------------------------------------------------------------
    # Sekundär (deskriptiv, zweiseitig): optionale Skalen + Override (A vs. B)
    # ------------------------------------------------------------------
    secondary: list[StatResult] = []
    for col, lbl in (("sus", "SUS"), ("tlx", "NASA-TLX")):
        xa, xb = _col(a, col), _col(b, col)
        if len(xa) > 0 and len(xb) > 0:
            secondary.append(_mann_whitney(f"{lbl} (A vs. B, zweiseitig)", xb, xa))

    for col, lbl in (
        ("override_rate", "Override-Rate"),
        ("r3_override_attempts", "R3-Override-Versuche"),
    ):
        xa, xb = _col(a, col), _col(b, col)
        if len(xa) > 0 and len(xb) > 0:
            secondary.append(_mann_whitney(f"{lbl} (A vs. B, zweiseitig)", xb, xa))

    results["secondary"] = [asdict(r) for r in secondary]

    return results


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

_EFFECT_LABELS = {
    (0.0, 0.1): "trivial",
    (0.1, 0.3): "klein",
    (0.3, 0.5): "mittel",
    (0.5, 1.0): "groß",
}


def _effect_label(r: float) -> str:
    for (lo, hi), label in _EFFECT_LABELS.items():
        if lo <= abs(r) < hi:
            return label
    return "groß"


def _row(d: dict[str, Any]) -> str:
    eff = d.get("effect", float("nan"))
    band = f" [{_effect_label(eff)}]" if d.get("effect_name") == "r" else ""
    return (
        f"  {d.get('label', '')}\n"
        f"    → {d['test']}: stat={d['statistic']:.1f}, p={d['p']:.3f}, "
        f"{d['effect_name']}={eff:.2f}{band} (N={d['N']})"
    )


def print_results(results: dict[str, Any]) -> None:
    print("\n=== PRIMÄR (H1, Vertrauen, Mann-Whitney-U, einseitig) ===")
    for r in results["primary"]:
        print(_row(r))

    print("\n=== WITHIN (H2, Direktvergleich A vs. B) ===")
    if results["within"]:
        for r in results["within"]:
            print(_row(r))
    else:
        print("  (kein Within-Vergleich erhoben)")

    print("\n=== SEKUNDÄR (deskriptiv, A vs. B) ===")
    if results["secondary"]:
        for r in results["secondary"]:
            print(_row(r))
    else:
        print("  (keine sekundären Maße erhoben)")

    print(
        "\nHinweis: N=16; der between-Vergleich (n=8 je Gruppe) ist unterpowert, "
        "nur große Effekte sind zuverlässig detektierbar. Der Within-Vergleich (N=16) "
        "trägt mehr Power. p-Werte nie isoliert: stets mit Effektgröße und N lesen. "
        "Nicht-signifikante Befunde schließen mittlere Effekte nicht aus."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="BitGridAI Studie — Statistische Auswertung (Single-Session, A vs. B)"
    )
    p.add_argument(
        "--events",
        required=True,
        help="Pfad zur events.parquet (aus /research/export ZIP)",
    )
    p.add_argument("--participants", required=True, help="Pfad zur participants.csv")
    p.add_argument("--out", default=None, help="Ausgabedatei JSON (optional)")
    return p.parse_args()


def main() -> None:
    args = _parse()

    events = pd.read_parquet(args.events)
    participants = pd.read_csv(args.participants, comment="#")

    required = {"participant_id", "group", "trust"}
    missing = required - set(participants.columns)
    if missing:
        print(f"FEHLER: participants.csv fehlen Spalten: {missing}", file=sys.stderr)
        sys.exit(1)

    df = compute_override_rates(events, participants)
    results = run_all_tests(df)
    print_results(results)

    out_path = Path(args.out) if args.out else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nErgebnisse gespeichert: {out_path}")


if __name__ == "__main__":
    main()
