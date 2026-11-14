"""Tests for the deterministic grading of the hamster eval."""

from __future__ import annotations

from src.explain import bithamster_eval as ev


def test_claim_flags_only_where_context_excludes_them() -> None:
    answer = {"headline": "Sats verloren", "text": "Etwas ist auffällig.", "punkte": []}
    ctx = "Es gab also KEINE verpasste Gelegenheit. GESAMTURTEIL: NICHTS auffällig."
    assert len(ev.claim_flags(answer, ctx)) == 2
    assert ev.claim_flags(answer, "kein Hinweis im Kontext") == []
    calm = {
        "headline": "Ruhig",
        "text": "Nichts auffällig, nicht auffällig.",
        "punkte": [],
    }
    assert ev.claim_flags(calm, ctx) == []


def test_grade_and_summary() -> None:
    checks = {
        "unverified_numbers": ["340"],
        "findings_by_model": 1,
        "findings_total": 2,
        "dropped_existing": [],
    }
    g = ev.grade(
        "gesamtcheck", {"headline": "h", "text": "t", "punkte": []}, checks, ""
    )
    assert g["json"] and not g["numbers"] and not g["findings"] and g["cards"]
    assert not g["passed"]
    assert ev.grade("frage", None, None, "") == {"json": False, "passed": False}
    report = {
        "eval_run": "eval-x",
        "model": "m",
        "scenarios": {
            "gesamtcheck": [
                {
                    "grade": g,
                    "duration_s": 10.0,
                    "error": None,
                    "unverified": ["340"],
                    "dropped": [],
                    "headline": "h",
                }
            ]
        },
    }
    text = "\n".join(ev.summary_lines(report))
    assert "0/1 bestanden" in text and "340" in text and "Pflichtbefund" in text
    assert "GESAMT 0/1" in text


def test_negated_claims_are_not_flagged() -> None:
    ctx = "Es gab also KEINE verpasste Gelegenheit zum Minen."
    for ok_text in (
        "Es gibt keine verpassten Chancen.",
        "Keine verpasste Chance zum Minen.",
        "Kein Fehler, nichts verpasst.",
    ):
        assert (
            ev.claim_flags({"headline": "", "text": ok_text, "punkte": []}, ctx) == []
        )
    bad = {"headline": "", "text": "Gestern wurde Sonne verpasst.", "punkte": []}
    assert ev.claim_flags(bad, ctx) == [
        "behauptet verpasste Gelegenheit ohne Überschuss"
    ]


def test_rounded_big_numbers_are_verified() -> None:
    from src.explain import bithamster_ki as ki

    answer = {"headline": "", "text": "Auf 580 W anheben, nicht 700 W.", "punkte": []}
    assert ki.unverified_numbers(answer, "gemessen 579 W, eingestellt 535 W") == ["700"]


def test_regrade_uses_current_checks(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from src.explain import bithamster_log as hl

    path = tmp_path / "log.db"
    result = {
        "request_id": "eval-x|fehler|0",
        "task": "fehler",
        "model": "m",
        "ok": True,
        "generated_at": "t",
        "answer": {
            "headline": "Ruhig",
            "text": "Keine verpassten Chancen.",
            "punkte": [],
        },
        "checks": {
            "unverified_numbers": [],
            "findings_by_model": 0,
            "findings_total": 0,
            "dropped_existing": [],
            "grade": {"passed": False},
        },
        "duration_s": 4.0,
    }
    hl.log_entry(
        path, "eval", result, prompt="KEINE verpasste Gelegenheit", eval_run="eval-x"
    )
    report = ev.regrade(path, "eval-x")
    assert report["scenarios"]["fehler"][0]["grade"]["passed"] is True


def test_super_threshold_flagged_only_when_blocked() -> None:
    ctx = "- Standard und Super sind in diesem Monat GESPERRT (Saison: Nur Eco)"
    bad = {"headline": "", "text": "Super startet erst bei 100 % Akku.", "punkte": []}
    good = {"headline": "", "text": "Super ist im November gesperrt.", "punkte": []}
    assert ev.claim_flags(bad, ctx) == [
        "nennt eine Super-Startschwelle, obwohl Super gesperrt ist"
    ]
    assert ev.claim_flags(good, ctx) == []
    assert ev.claim_flags(bad, "Super ab 95 % Akku.") == []


def test_zero_counts_as_negation() -> None:
    ctx = "Es gab also KEINE verpasste Gelegenheit zum Minen."
    ans = {"headline": "", "text": "0 verpasste Überschüsse.", "punkte": []}
    assert ev.claim_flags(ans, ctx) == []


def test_sum_and_difference_of_named_numbers_are_verified() -> None:
    from src.explain import bithamster_ki as ki

    ctx = "Sonne 10,8 kWh, Haus 17,2 kWh, 212 Sats pro kWh, Minen 0,6 kWh."
    diff = {
        "headline": "",
        "text": "17,2 minus 10,8 gibt 6,4 kWh Defizit.",
        "punkte": [],
    }
    assert ki.unverified_numbers(diff, ctx) == []
    # 6,4 without both operands in the answer stays flagged
    alone = {"headline": "", "text": "Defizit 6,4 kWh.", "punkte": []}
    assert ki.unverified_numbers(alone, ctx) == ["6,4"]
    prod = {"headline": "", "text": "212 mal 0,6 sind 127 Sats.", "punkte": []}
    assert ki.unverified_numbers(prod, ctx) == ["127"]


def test_claims_from_the_evening_chats() -> None:
    from src.explain.bithamster_eval import claim_flags

    prompt = "Die Sonne ist KEINE Startbedingung. BEREITS KORRIGIERT. Boden 5 %."
    wrong = {
        "headline": "x",
        "text": "Aufwachen ab 100 % Akku und mindestens 6.000 W Sonne.",
        "punkte": [
            "Hausreserve für den Winter erhöhen.",
            "Morgens 2 % statt 15 % Akku.",
        ],
    }
    assert len(claim_flags(wrong, prompt)) == 3
    right = {
        "headline": "x",
        "text": "Die Sonne ist keine Startbedingung, nur der Akku zählt.",
        "punkte": ["Die Hausreserve nicht erhöhen, sie ist schon korrigiert."],
    }
    assert claim_flags(right, prompt) == []


def test_claims_from_the_research_tab_14_11() -> None:
    from src.explain.bithamster_eval import claim_flags

    prompt = "Saisonmuster. es erklärt NICHT allein. nicht gemessen."
    wrong = {
        "headline": "x",
        "text": "Die Prognose ist mit 74 % Abweichung wertlos.",
        "punkte": [
            "Der Heizstab verhindert das Erreichen der 100 %-Startschwelle.",
            "173 von 173 Tagen lückenlos erfasst.",
        ],
    }
    assert len(claim_flags(wrong, prompt)) == 3
    right = {
        "headline": "x",
        "text": "Die Prognose ist im Winter zu hoch, im Sommer brauchbar.",
        "punkte": ["172 von 173 Tagen vollständig übertragen, 117 h nicht gemessen."],
    }
    assert claim_flags(right, prompt) == []
