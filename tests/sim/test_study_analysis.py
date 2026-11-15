"""Analysis of the within design on synthetic data only."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from src.sim import study_analysis as sa
from src.sim import study_sosci as ss

FAST = {"n_boot": 200, "power_sims": 400}


def test_signed_rank_null_is_the_exact_distribution() -> None:
    counts = sa.signed_rank_null(16)
    assert counts.sum() == 2**16 and len(counts) == 16 * 17 // 2 + 1
    assert np.array_equal(counts, counts[::-1])
    # Two-sided alpha 0.05, n = 16: critical value 29 (standard tables).
    assert sa._critical(16) == 29
    assert sa._critical(5) == -1  # no two-sided 5 % test possible


def test_z_values_match_scipy_normal_approximation() -> None:
    d = np.array([0.5, 1.0, -0.5, 1.5, 0.0, 1.0, 2.0, -1.0, 0.5, 1.0])
    z, n, _ = sa.signed_rank_z(d)
    ref = stats.wilcoxon(d, zero_method="wilcox", method="approx", correction=False)
    assert n == 9 and z > 0
    assert 2 * stats.norm.sf(abs(z)) == pytest.approx(ref.pvalue, rel=1e-9)
    x = np.array([3.0, 3.5, 4.0, 4.0, 2.5])
    y = np.array([2.0, 3.0, 3.0, 2.5, 3.5, 2.0])
    zm = sa.mann_whitney_z(x, y)
    ref_mw = stats.mannwhitneyu(x, y, method="asymptotic", use_continuity=False)
    assert zm > 0
    assert 2 * stats.norm.sf(abs(zm)) == pytest.approx(ref_mw.pvalue, rel=1e-9)


def test_hodges_lehmann_paired() -> None:
    est, lo, hi = sa.hodges_lehmann_paired(np.full(16, 0.5))
    assert (est, lo, hi) == (0.5, 0.5, 0.5)
    d = np.arange(1.0, 17.0) - 8.0
    est, lo, hi = sa.hodges_lehmann_paired(d)
    assert est == pytest.approx(0.5) and lo < est < hi


def test_all_differences_one_way_is_flagged() -> None:
    rng = np.random.default_rng(1)
    b = np.linspace(2, 4, 16)
    row = sa.wilcoxon_paired("x", "m", "primär", b + 0.5, b, rng, 100)
    assert sa.RIM_NOTE in row.detail and row.r > 0.8


def test_paired_power_keeps_alpha_and_grows_with_dz() -> None:
    res = sa.paired_power(dz_values=(0.0, 0.5, 0.8), sims=2000)
    power = [r["power"] for r in res]
    assert power[0] <= 0.06
    assert power[0] < power[1] < power[2] and power[2] > 0.7


def test_run_within_tests_on_synthetic_data() -> None:
    res = sa.run_within_tests(ss.prepare(ss.synthetic_export()), **FAST)
    rows = res["rows"]
    roles = [r["rolle"] for r in rows]
    assert roles.count("primär") == 1 and roles.count("explorativ") == 3
    assert res["explorative_tests"] == 3
    h1 = rows[0]
    assert h1["analyse"] == sa.LABEL_H1 and h1["test"] == "Wilcoxon gepaart"
    assert h1["n"] == 15  # one person lost Vertrauen in run 1 by the rule
    for key in ("p", "r", "r_ki_unten", "r_ki_oben", "hl", "hl_ki_unten"):
        assert math.isfinite(h1[key]), key
    assert h1["r_ki_unten"] <= h1["r"] <= h1["r_ki_oben"]
    # Synthetic A is set higher: the sign convention is A - B.
    assert h1["hl"] > 0 and h1["r"] > 0
    described = [r for r in rows if r["rolle"] == "beschreibend"]
    assert len(described) == 3 and all(r["test"] == "keiner" for r in described)
    assert [r["analyse"] for r in rows if r["rolle"] == "Kontrolle"] == [
        sa.LABEL_ORDER
    ] * 2
    assert [r["analyse"] for r in rows if r["rolle"] == "Sensitivität"] == [
        sa.LABEL_SENS
    ] * 2
    kinds = {
        (x["messung"], x["durchlauf"]): x["kennwert"] for x in res["reliabilitaet"]
    }
    assert len(kinds) == 12
    assert kinds[("TiA Vertrauen in Automation", 1)] == "Spearman-Brown"
    assert kinds[("TiA Verständlichkeit/Vorhersagbarkeit", 2)] == "Cronbachs Alpha"
    assert res["stichprobe"]["n"] == 16 and res["stichprobe"]["ab"] == 8


def test_same_seed_same_result() -> None:
    prep = ss.prepare(ss.synthetic_export())
    one = sa.run_within_tests(prep, **FAST)
    two = sa.run_within_tests(prep, **FAST)
    assert one["rows"] == two["rows"] and one["power"] == two["power"]


def test_outputs_and_report(tmp_path: Path) -> None:
    res = sa.run_within_tests(ss.prepare(ss.synthetic_export()), **FAST)
    res["synthetisch"] = True
    paths = sa.write_outputs(res, tmp_path)
    assert [p.name for p in paths] == ["kennwerte.csv", "kennwerte.md", "bericht.txt"]
    text = paths[2].read_text(encoding="utf-8")
    assert text.startswith("SYNTHETISCHE DATEN")
    assert "Explorativ (3 Tests, ohne Korrektur" in text
    assert "Durch die Regel" not in text and "durch die Regel fehlend" in text
    assert "p = < " not in text
    md = paths[1].read_text(encoding="utf-8")
    assert "| analyse |" in md and "## Power" in md
    assert paths[0].read_text(encoding="utf-8-sig").startswith("analyse;messung")


def test_cli_refuses_real_data_before_the_freeze(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sa, "FREEZE_RECORD", tmp_path / "datenfreeze.txt")
    export = tmp_path / "export.csv"  # never read: the check comes first
    assert sa.main(["--sosci", str(export)]) == 2
    out = tmp_path / "demo"
    args = ["--demo", "--out-dir", str(out), "--n-boot", "50", "--power-sims", "100"]
    assert sa.main(args) == 0
    assert (out / "bericht.txt").exists()


def test_missing_lines_per_variant_and_imbalance() -> None:
    rows = [
        {
            "messung": "SUS",
            "durchlauf": 1,
            "variante": "A",
            "teilweise": 1,
            "regel": 0,
            "leer": 0,
        },
        {
            "messung": "SUS",
            "durchlauf": 1,
            "variante": "B",
            "teilweise": 0,
            "regel": 2,
            "leer": 1,
        },
    ]
    lines = sa.missing_lines(rows)
    assert "SUS: A: 1 mit fehlenden Items verwendet; B: 2 durch die Regel" in lines[1]
    assert lines[-1].strip().startswith("ACHTUNG")
    rows[1]["regel"], rows[1]["leer"] = 1, 0
    assert not any("ACHTUNG" in x for x in sa.missing_lines(rows))
    none = [dict(r, teilweise=0, regel=0, leer=0) for r in rows]
    assert sa.missing_lines(none)[-1] == "  keine fehlenden Werte."
