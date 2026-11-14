"""Evaluation of the KI hamster against the live context (read-only).

Asks every task several times with the real context (HA states via GET,
research DB read-only) and grades each answer with deterministic checks:

- ``json``: the answer could be parsed at all,
- ``numbers``: no number in the answer that is missing from the context
  (rounding allowed); a missing number was invented or derived by the model,
- ``findings``: the model itself named every priority finding ("Alles prüfen"),
  before the Python safety net puts skipped ones in front,
- ``cards``: no proposed card that already exists ("Fehlende KPI-Karten"),
- ``claims``: none of the known wrong claims from earlier live runs.

Nothing is written to Home Assistant; the card JSON stays untouched. Each run
lands in the answer log (kind ``eval``) so prompt, answer and grade can be
inspected afterwards. The checks are necessary conditions, not proof of a
correct answer: an answer can pass and still explain something badly. That
part stays a human review of the logged answers.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.explain import bithamster_ki as ki
from src.explain.bithamster_log import connect, log_entry

log = logging.getLogger(__name__)

# (scenario name, task, tab, question)
SCENARIOS: list[tuple[str, str, str | None, str | None]] = [
    ("optimierung", "optimierung", None, None),
    ("aufzeichnung", "aufzeichnung", None, None),
    ("fehler", "fehler", None, None),
    ("verbesserung", "verbesserung", None, None),
    ("gesamtcheck", "gesamtcheck", None, None),
    ("karten", "karten", None, None),
    ("tab_forschung", "tab", "Forschung", None),
    ("tab_einstellungen", "tab", "Einstellungen", None),
    ("frage_akku", "frage", None, "Warum ist der Akku morgens leer?"),
    ("frage_super", "frage", None, "Lohnt es sich gerade, Super zu fahren?"),
    # Not in the context: an honest answer says so instead of inventing a number.
    ("frage_sats", "frage", None, "Wie viele Sats haben die Miner gestern verdient?"),
    # Added 13.11.2026 evening after the live chats.
    ("tabcheck_energie", "tabcheck", "Energie", None),
    ("tabcheck_forschung", "tabcheck", "Forschung", None),
    (
        "frage_sonne",
        "frage",
        None,
        "Die Sonne scheint, warum starten die Miner nicht?",
    ),
    ("frage_reserve", "frage", None, "Soll ich die Hausreserve erhöhen?"),
]

# Wrong claims seen in live runs (13.11.2026), as (regex, reason).
# Applied only when the context rules them out, see claim_flags().
CLAIM_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"sats?\s+(verloren|verschenkt)|verlorene\s+sats",
        "KEINE verpasste Gelegenheit",
        "behauptet verlorene Sats ohne Überschuss",
    ),
    (
        r"verpasst",
        "KEINE verpasste Gelegenheit",
        "behauptet verpasste Gelegenheit ohne Überschuss",
    ),
    (
        r"super\w*[^.]{0,40}\b(ab|startet|beginnt|braucht)\b[^.]{0,20}\d+\s*%",
        "Super sind in diesem Monat GESPERRT",
        "nennt eine Super-Startschwelle, obwohl Super gesperrt ist",
    ),
    # 13.11.2026 evening: the sun threshold only shortens the cooldown (R7),
    # it is no start condition.
    (
        r"sonne\w*[^.]{0,40}(startbedingung|zum start\w*|für den start|reicht nicht"
        r" zum|muss mindestens)|und\s+(mindestens\s+)?[\d.,]+\s*k?w\s+sonne",
        "KEINE Startbedingung",
        "macht die Sonne zur Startbedingung",
    ),
    # Raising the reserve again after ADR 033 already did it.
    (
        r"(hausreserve|reserve|grundlast)[^.]{0,30}(erhöhen|anheben|höher setzen)",
        "BEREITS KORRIGIERT",
        "rät, die Reserve erneut anzuheben, obwohl sie korrigiert ist",
    ),
    # Eval 13.11.2026: cards called useless because the miners rest in winter.
    (
        r"(winter|ohne mining)[^.]{0,60}(redundant|überflüssig|statisch|entfernen)",
        "im Winter wenig zeigt",
        "will eine Karte entfernen, nur weil gerade Winter ist",
    ),
    # The morning target is the floor (5 %), not the old 15 %.
    (
        r"statt 15\s*%|ziel\w*[^.]{0,20}\b15\s*%",
        "Boden 5",
        "nennt das alte Ziel 15 % am Morgen",
    ),
    # Live 14.11.2026 (Tab Forschung): three wrong claims, each ruled out by a
    # line the context now carries (bithamster_research, recording_lines).
    (
        r"prognose\w*[^.]{0,60}(wertlos|unbrauchbar|nutzlos)",
        "Saisonmuster",
        "nennt die Prognose wertlos, obwohl sie nur im Winter zu hoch ist",
    ),
    (
        r"heizstab[^.]{0,80}(verhinder|schuld|ursache)",
        "NICHT allein",
        "macht den Heizstab zur Ursache des leeren Akkus im Winter",
    ),
    (
        r"(\d+) von \1 tage\w*[^.]{0,30}(lückenlos|vollständig)",
        "nicht gemessen",
        "nennt alle Tage lückenlos, obwohl Stunden nicht gemessen wurden",
    ),
    (
        r"(?<!nicht )(?<!nichts )auffällig",
        "NICHTS auffällig",
        "nennt etwas auffällig trotz Gesamturteil 'nichts auffällig'",
    ),
]


_NEGATION = re.compile(r"\b(kein\w*|nicht|nichts|ohne|null|0)\b(\W+\w+){0,2}\W*$")


def claim_flags(answer: dict[str, Any], prompt: str) -> list[str]:
    """Known wrong claims, only where the context explicitly excludes them.

    A match preceded by a negation within two words ("keine verpassten
    Chancen") is the correct statement, not the wrong claim; the first eval
    run on 13.11.2026 flagged eight such answers before this was added.
    """
    text = " ".join(
        [answer.get("headline") or "", answer.get("text") or ""]
        + list(answer.get("punkte") or [])
    ).lower()
    flags = []
    for pattern, guard, reason in CLAIM_PATTERNS:
        if guard not in prompt:
            continue
        for m in re.finditer(pattern, text):
            # Negation before the match ("keine verpassten") or inside it
            # ("Sonne ist keine Startbedingung", "Reserve nicht erhöhen").
            inside = re.search(r"\b(kein\w*|nicht|nichts)\b", m.group(0))
            if not inside and not _NEGATION.search(
                text[max(0, m.start() - 40) : m.start()]
            ):
                flags.append(reason)
                break
    return flags


def regrade(log_db: str | Path, eval_run: str) -> dict[str, Any]:
    """Grade the logged answers of an eval run again with the current checks.

    Used when a check itself was wrong: no new model calls, same answers.
    """
    conn = connect(log_db)
    try:
        rows = conn.execute(
            "SELECT request_id, task, model, headline, text, points_json,"
            " checks_json, prompt, duration_s, error FROM hamster_log"
            " WHERE kind = 'eval' AND eval_run = ? ORDER BY id",
            (eval_run,),
        ).fetchall()
    finally:
        conn.close()
    report: dict[str, Any] = {
        "eval_run": eval_run + " (neu bewertet)",
        "model": rows[0][2] if rows else "?",
        "scenarios": {},
    }
    for rid, task, _, head, text, pts, checks_json, prompt, dur, err in rows:
        name = str(rid).split("|")[1]
        old = json.loads(checks_json or "{}")
        answer = None
        checks = None
        if head is not None:
            answer = {"headline": head, "text": text, "punkte": json.loads(pts)}
            checks = {
                **old,
                "unverified_numbers": ki.unverified_numbers(answer, prompt),
            }
        g = grade(task, answer, checks, prompt or "")
        report["scenarios"].setdefault(name, []).append(
            {
                "grade": g,
                "duration_s": dur or 0.0,
                "error": err,
                "unverified": (checks or {}).get("unverified_numbers"),
                "dropped": (checks or {}).get("dropped_existing"),
                "no_data": (checks or {}).get("dropped_no_data"),
                "headline": head,
            }
        )
    return report


def grade(
    task: str, answer: dict[str, Any] | None, checks: dict[str, Any] | None, prompt: str
) -> dict[str, Any]:
    """Pass/fail per check for one answer."""
    if answer is None or checks is None:
        return {"json": False, "passed": False}
    g: dict[str, Any] = {
        "json": True,
        "numbers": not checks["unverified_numbers"],
        "findings": checks["findings_by_model"] == checks["findings_total"],
        "cards": not checks["dropped_existing"] and not checks.get("dropped_no_data"),
        "card_tabs": not checks.get("fixed_card_tabs"),
        "claims": claim_flags(answer, prompt),
    }
    g["passed"] = (
        g["numbers"]
        and g["findings"]
        and g["cards"]
        and g["card_tabs"]
        and not g["claims"]
    )
    return g


def run_eval(
    *,
    db: str | Path,
    soul: str | Path,
    ha_url: str,
    ha_token: str,
    llm_url: str,
    model: str,
    dashboard: str | Path | None,
    recording_status: str | Path | None,
    log_db: str | Path | None,
    runs: int = 3,
    only: list[str] | None = None,
    pause_s: float = 1.0,
) -> dict[str, Any]:
    """Run all scenarios ``runs`` times; returns per-scenario results."""
    now = datetime.now(timezone.utc)
    eval_run = now.strftime("eval-%Y%m%dT%H%M%S")
    states = ki.read_ha_states(ha_url, ha_token)
    system = Path(soul).read_text(encoding="utf-8")
    report: dict[str, Any] = {"eval_run": eval_run, "model": model, "scenarios": {}}
    for name, task, tab, question in SCENARIOS:
        if only and name not in only and task not in only:
            continue
        prepared = ki.prepare_ask(
            task,
            states=states,
            db=db,
            now=now,
            dashboard=dashboard,
            recording_status=recording_status,
            tab=tab,
            question=question,
        )
        rows = []
        for i in range(runs):
            result: dict[str, Any] = {
                "request_id": f"{eval_run}|{name}|{i}",
                "task": task,
                "label": ki.TASKS[task][0],
                "tab": tab,
                "question": question,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": model,
                "ok": False,
                "error": None,
                "answer": None,
                "checks": None,
            }
            t0 = time.monotonic()
            try:
                answer = ki.parse_ask_answer(
                    ki.call_llm(llm_url, model, system, prepared["prompt"]),
                    ki.TASK_MAX_POINTS.get(task, ki.MAX_POINTS),
                )
                result["checks"] = ki.finish_answer(task, answer, prepared)
                result["answer"] = answer
                result["ok"] = True
            except Exception as exc:  # grade as failed, keep going
                result["error"] = f"{type(exc).__name__}: {exc}"[:300]
            result["duration_s"] = round(time.monotonic() - t0, 1)
            g = grade(task, result["answer"], result["checks"], prepared["prompt"])
            result["checks"] = {**(result["checks"] or {}), "grade": g}
            if log_db:
                log_entry(
                    log_db, "eval", result, prompt=prepared["prompt"], eval_run=eval_run
                )
            rows.append(
                {
                    "grade": g,
                    "duration_s": result["duration_s"],
                    "error": result["error"],
                    "unverified": (result["checks"] or {}).get("unverified_numbers"),
                    "dropped": (result["checks"] or {}).get("dropped_existing"),
                    "no_data": (result["checks"] or {}).get("dropped_no_data"),
                    "headline": (result["answer"] or {}).get("headline"),
                }
            )
            time.sleep(pause_s)
        report["scenarios"][name] = rows
    return report


def summary_lines(report: dict[str, Any]) -> list[str]:
    """Human-readable table: passes per scenario and the reasons for failures."""
    lines = [f"Eval {report['eval_run']} ({report['model']})", ""]
    total = passed = 0
    for name, rows in report["scenarios"].items():
        ok = sum(1 for r in rows if r["grade"].get("passed"))
        total += len(rows)
        passed += ok
        mean = sum(r["duration_s"] for r in rows) / len(rows) if rows else 0.0
        reasons: list[str] = []
        for r in rows:
            g = r["grade"]
            if not g.get("json"):
                reasons.append(f"kein JSON ({r['error']})")
                continue
            if not g["numbers"]:
                reasons.append("Zahlen nicht im Kontext: " + ", ".join(r["unverified"]))
            if not g["findings"]:
                reasons.append("Pflichtbefund übersehen")
            if r.get("dropped"):
                reasons.append(f"{len(r['dropped'])} vorhandene Karte(n) vorgeschlagen")
            if r.get("no_data"):
                reasons.append(
                    f"{len(r['no_data'])} Vorschlag/Vorschläge auf alten Daten"
                )
            if not g.get("card_tabs", True):
                reasons.append("Karte im falschen Tab genannt")
            reasons += g["claims"]
        lines.append(f"{name:<18} {ok}/{len(rows)} bestanden, Ø {mean:.1f} s")
        lines += [f"    - {x}" for x in reasons]
    lines += ["", f"GESAMT {passed}/{total} bestanden"]
    return lines


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING)
    ki._load_env_file()
    p = argparse.ArgumentParser(description="Evaluate the KI hamster (read-only)")
    p.add_argument("--db", required=True)
    p.add_argument("--soul", required=True)
    p.add_argument("--dashboard", default=None)
    p.add_argument("--recording-status", default=None)
    p.add_argument("--log-db", default=None)
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--only", nargs="*", default=None, help="scenario or task names")
    p.add_argument("--json-out", default=None, help="write the full report here")
    p.add_argument(
        "--regrade", default=None, help="eval_run id: grade logged answers again"
    )
    args = p.parse_args(argv)
    if args.regrade:
        if not args.log_db:
            print("--regrade needs --log-db", file=sys.stderr)
            return 2
        print("\n".join(summary_lines(regrade(args.log_db, args.regrade))))
        return 0
    host = os.getenv("UMBREL_HOST", "")
    ha_url = f"http://{host}:{os.getenv('HA_PORT', '8123')}" if host else ""
    token = os.getenv("HA_TOKEN", "")
    llm_url = os.getenv("BITHAMSTER_LLM_URL", "")
    if not (ha_url and token and llm_url):
        print("missing UMBREL_HOST / HA_TOKEN / BITHAMSTER_LLM_URL", file=sys.stderr)
        return 2
    report = run_eval(
        db=args.db,
        soul=args.soul,
        ha_url=ha_url,
        ha_token=token,
        llm_url=llm_url,
        model=os.getenv("BITHAMSTER_MODEL", ki.DEFAULT_MODEL),
        dashboard=args.dashboard,
        recording_status=args.recording_status,
        log_db=args.log_db,
        runs=args.runs,
        only=args.only,
    )
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    print("\n".join(summary_lines(report)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
