"""
study_analysis.py — Statistische Auswertung der BitGridAI-Nutzerstudie.

Eingabe:
  events.parquet   — Parquet aus /research/export (ZIP entpackt)
  participants.csv — Fragebogen-Daten je Proband; Schema:
    participant_id,group,sus_pre,sus_post,trust_pre,trust_post,
    tlx_pre,tlx_mid,tlx_post,vignette_pre,vignette_post

Ausgabe:
  Konsole: alle Tests im Format  U=..., p=..., r=... (N=...)
  Datei:   study_results.json   (maschinenlesbar für Thesis)

Verwendung:
  python -m src.sim.study_analysis \\
    --events data/study/events.parquet \\
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
# Effektgröße-Berechnung
# ---------------------------------------------------------------------------

@dataclass
class MWResult:
    """Ergebnis eines Mann-Whitney-U-Tests mit Effektgröße."""
    label: str
    U: float
    p: float
    r: float
    N: int

    def format(self) -> str:
        return f"{self.label}: U={self.U:.1f}, p={self.p:.3f}, r={self.r:.2f} (N={self.N})"


@dataclass
class WilcoxResult:
    """Ergebnis eines Wilcoxon-Vorzeichen-Rangtests mit Effektgröße."""
    label: str
    W: float
    p: float
    r: float
    N_pairs: int

    def format(self) -> str:
        return f"{self.label}: W={self.W:.1f}, p={self.p:.3f}, r={self.r:.2f} (N={self.N_pairs} Paare)"


def _mann_whitney(label: str, x: np.ndarray, y: np.ndarray) -> MWResult:
    """Mann-Whitney-U mit r = Z / sqrt(N_total) nach Field 2018."""
    n1, n2 = len(x), len(y)
    N = n1 + n2
    result = stats.mannwhitneyu(x, y, alternative="two-sided", method="auto")
    U = float(result.statistic)
    p = float(result.pvalue)

    # Z via Normalapproximation der U-Verteilung
    mu_u = n1 * n2 / 2.0
    sigma_u = math.sqrt(n1 * n2 * (N + 1) / 12.0)
    z = abs(U - mu_u) / sigma_u if sigma_u > 0 else 0.0
    r = z / math.sqrt(N)
    return MWResult(label=label, U=U, p=p, r=round(r, 3), N=N)


def _wilcoxon(label: str, pre: np.ndarray, post: np.ndarray) -> WilcoxResult:
    """Wilcoxon-Vorzeichen-Rangtest mit r = Z / sqrt(2 * n_paare) nach Field 2018."""
    diff = post - pre
    n_pairs = int(np.sum(diff != 0))  # Nulldifferenzen werden verworfen

    if n_pairs < 2:
        return WilcoxResult(label=label, W=float("nan"), p=float("nan"), r=float("nan"), N_pairs=n_pairs)

    result = stats.wilcoxon(post - pre, alternative="two-sided", method="auto")
    W = float(result.statistic)
    p = float(result.pvalue)

    # Z-Approximation für den W-Statistikwert
    mu_w = n_pairs * (n_pairs + 1) / 4.0
    sigma_w = math.sqrt(n_pairs * (n_pairs + 1) * (2 * n_pairs + 1) / 24.0)
    z = abs(W - mu_w) / sigma_w if sigma_w > 0 else 0.0
    # N_total für abhängige Stichproben = 2 * n_paare (Field 2018 §7.5)
    r = z / math.sqrt(2 * n_pairs)
    return WilcoxResult(label=label, W=W, p=p, r=round(r, 3), N_pairs=n_pairs)


# ---------------------------------------------------------------------------
# Override-Rate aus Parquet ableiten
# ---------------------------------------------------------------------------

def compute_override_rates(events: pd.DataFrame, participants: pd.DataFrame) -> pd.DataFrame:
    """Berechnet Override-Rate (Anteil OVERRIDE-Trigger) pro Proband.

    Erfordert Spalte 'participant_id' in events. Wenn nicht vorhanden,
    wird ein leerer DataFrame zurückgegeben (kein Fehler, nur Warnung).
    """
    if "participant_id" not in events.columns:
        print("WARNUNG: events.parquet enthält keine participant_id-Spalte — "
              "Override-Rate kann nicht berechnet werden.")
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
# Statistische Tests
# ---------------------------------------------------------------------------

def run_all_tests(df: pd.DataFrame) -> dict[str, Any]:
    """Führt alle vordefinierten Hypothesentests durch.

    df muss Spalten enthalten: group (B/E), sus_pre, sus_post,
    trust_pre, trust_post, tlx_pre, tlx_post, vignette_pre, vignette_post.
    Override-Spalten (override_rate, r3_override_attempts) optional.
    """
    b = df[df["group"] == "B"]
    e = df[df["group"] == "E"]

    results: dict[str, Any] = {"between_groups": [], "within_group_B": [], "within_group_E": []}

    # ------------------------------------------------------------------
    # Zwischen-Gruppen: Mann-Whitney-U (H1 / H2 / H3)
    # ------------------------------------------------------------------
    between: list[MWResult] = []

    between.append(_mann_whitney(
        "H1: Vignetten-Score post (Gruppe E > B)",
        b["vignette_post"].to_numpy(dtype=float),
        e["vignette_post"].to_numpy(dtype=float),
    ))
    between.append(_mann_whitney(
        "H3: SUS post (Gruppe E > B)",
        b["sus_post"].to_numpy(dtype=float),
        e["sus_post"].to_numpy(dtype=float),
    ))
    between.append(_mann_whitney(
        "H3: Trust post (Gruppe E > B)",
        b["trust_post"].to_numpy(dtype=float),
        e["trust_post"].to_numpy(dtype=float),
    ))
    between.append(_mann_whitney(
        "H3: NASA-TLX post (Gruppe B > E — niedrigere Belastung in E erwartet)",
        e["tlx_post"].to_numpy(dtype=float),
        b["tlx_post"].to_numpy(dtype=float),
    ))

    if "override_rate" in df.columns:
        between.append(_mann_whitney(
            "H2: Override-Rate (Gruppe E ≠ B)",
            b["override_rate"].to_numpy(dtype=float),
            e["override_rate"].to_numpy(dtype=float),
        ))
    if "r3_override_attempts" in df.columns:
        between.append(_mann_whitney(
            "H2: R3-Override-Versuche (Gruppe B > E erwartet)",
            e["r3_override_attempts"].to_numpy(dtype=float),
            b["r3_override_attempts"].to_numpy(dtype=float),
        ))

    results["between_groups"] = [asdict(r) for r in between]

    # ------------------------------------------------------------------
    # Innerhalb Gruppe B: Wilcoxon Prä-Post
    # ------------------------------------------------------------------
    within_b: list[WilcoxResult] = [
        _wilcoxon("SUS prä→post (B)", b["sus_pre"].to_numpy(float), b["sus_post"].to_numpy(float)),
        _wilcoxon("Trust prä→post (B)", b["trust_pre"].to_numpy(float), b["trust_post"].to_numpy(float)),
        _wilcoxon("TLX prä→post (B)", b["tlx_pre"].to_numpy(float), b["tlx_post"].to_numpy(float)),
        _wilcoxon("Vignette prä→post (B)", b["vignette_pre"].to_numpy(float), b["vignette_post"].to_numpy(float)),
    ]
    results["within_group_B"] = [asdict(r) for r in within_b]

    # ------------------------------------------------------------------
    # Innerhalb Gruppe E: Wilcoxon Prä-Post
    # ------------------------------------------------------------------
    within_e: list[WilcoxResult] = [
        _wilcoxon("SUS prä→post (E)", e["sus_pre"].to_numpy(float), e["sus_post"].to_numpy(float)),
        _wilcoxon("Trust prä→post (E)", e["trust_pre"].to_numpy(float), e["trust_post"].to_numpy(float)),
        _wilcoxon("TLX prä→post (E)", e["tlx_pre"].to_numpy(float), e["tlx_post"].to_numpy(float)),
        _wilcoxon("Vignette prä→post (E)", e["vignette_pre"].to_numpy(float), e["vignette_post"].to_numpy(float)),
    ]
    results["within_group_E"] = [asdict(r) for r in within_e]

    return results


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

_EFFECT_LABELS = {(0.0, 0.1): "trivial", (0.1, 0.3): "klein", (0.3, 0.5): "mittel", (0.5, 1.0): "groß"}


def _effect_label(r: float) -> str:
    for (lo, hi), label in _EFFECT_LABELS.items():
        if lo <= abs(r) < hi:
            return label
    return "groß"


def print_results(results: dict[str, Any]) -> None:
    def _row(d: dict[str, Any]) -> str:
        r = d.get("r", float("nan"))
        label = d.get("label", "")
        if "U" in d:
            return (f"  {label}\n"
                    f"    → U={d['U']:.1f}, p={d['p']:.3f}, r={r:.2f} [{_effect_label(r)}] "
                    f"(N={d['N']})")
        else:
            return (f"  {label}\n"
                    f"    → W={d['W']:.1f}, p={d['p']:.3f}, r={r:.2f} [{_effect_label(r)}] "
                    f"(N={d['N_pairs']} Paare)")

    print("\n=== ZWISCHEN-GRUPPEN (Mann-Whitney-U) ===")
    for r in results["between_groups"]:
        print(_row(r))

    print("\n=== INNERHALB GRUPPE B (Wilcoxon Prä→Post) ===")
    for r in results["within_group_B"]:
        print(_row(r))

    print("\n=== INNERHALB GRUPPE E (Wilcoxon Prä→Post) ===")
    for r in results["within_group_E"]:
        print(_row(r))

    print("\nHinweis: Power bei n=5 je Gruppe ≈ 20 % für r=0.3. "
          "Nicht-signifikante Befunde schließen mittlere Effekte nicht aus.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="BitGridAI Studie — Statistische Auswertung")
    p.add_argument("--events", required=True, help="Pfad zur events.parquet (aus /research/export ZIP)")
    p.add_argument("--participants", required=True, help="Pfad zur participants.csv")
    p.add_argument("--out", default=None, help="Ausgabedatei JSON (optional)")
    return p.parse_args()


def main() -> None:
    args = _parse()

    events = pd.read_parquet(args.events)
    participants = pd.read_csv(args.participants, comment="#")

    required = {"participant_id", "group", "sus_pre", "sus_post", "trust_pre", "trust_post",
                "tlx_pre", "tlx_post", "vignette_pre", "vignette_post"}
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
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nErgebnisse gespeichert: {out_path}")


if __name__ == "__main__":
    main()
