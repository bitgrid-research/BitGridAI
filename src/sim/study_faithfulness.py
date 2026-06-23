"""
Faithfulness-Vorprüfung — automatischer Konsistenz-Check der Erklärungen.

Da das System **deterministisch** ist, kennen wir die wahre Entscheidung. Eine
Erklärung ist *nicht treu*, wenn sie der Aktion widerspricht (z. B. „Miner läuft"
bei einem STOP). Diese Prüfung ist eine **automatisierte Vorstufe**, kein Ersatz
für die manuelle Bewertung. Sie prüft:
- **Aktions-Konsistenz** (kein Widerspruch zur START/STOP/THROTTLE/NOOP-Aktion),
- **Erdung** (konkreter Zahlenwert, wie im LLM-Prompt gefordert),
- **Informations-Parität A↔B** (trägt B die Änderungsbedingung aus A, also
  mindestens einen Schwellenwert aus dem A-`options`-Feld; nur die Stimme darf
  variieren, nicht der Informationsgehalt, Prereg 2024a/2024e).

  python -m src.sim.study_faithfulness            # prüft src/sim/study_set/*.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_RUN_TERMS = ("läuft", "startet", "gestartet", "angeschaltet", "eco", "gedrosselt")
_STOP_TERMS = ("gestoppt", "stoppt", "stopp", "abgeschaltet", "ausgeschaltet")
_DEFAULT_DIR = Path("src/sim/study_set")
_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")


def change_thresholds(options_text: str) -> list[str]:
    """Schwellenwerte aus dem A-`options`-Text (z. B. ['58'], ['6,0'], ['500'])."""
    return _NUM_RE.findall(options_text or "")


def covers_change_condition(b_text: str, options_text: str) -> bool | None:
    """Trägt B die Änderungsbedingung aus A (mindestens einen Schwellenwert)?

    Gibt ``None`` zurück, wenn A keine numerische Änderungsbedingung nennt
    (z. B. ``START_R1_SURPLUS_OK`` mit leerem ``options``) — dann nicht prüfbar.
    """
    nums = change_thresholds(options_text)
    if not nums:
        return None
    return any(n in (b_text or "") for n in nums)


def check_text(text: str, action: str) -> dict[str, bool]:
    """Prüft eine Erklärung gegen die Aktion (START/STOP/THROTTLE/NOOP)."""
    t = text.lower()
    run = any(w in t for w in _RUN_TERMS)
    stop = any(w in t for w in _STOP_TERMS)
    if action == "STOP":
        consistent = stop and not run
    elif action in ("START", "THROTTLE"):
        consistent = run and not stop
    else:  # NOOP — Aktion mehrdeutig (läuft weiter / bleibt aus); nur Doppel-Widerspruch flaggen
        consistent = not (run and stop)
    return {
        "action_consistent": consistent,
        "has_number": bool(re.search(r"\d", text)),
    }


def check_item(item: dict[str, Any]) -> dict[str, Any]:
    action = item["decision"]["action"]
    expl = item["explanation"]
    a_short = expl["group_a"]["short"]
    a_options = expl["group_a"].get("options", "")
    b_text = expl["group_b"]
    return {
        "sid": item["sid"],
        "action": action,
        "group_a": check_text(a_short, action),
        "group_b": None if b_text is None else check_text(b_text, action),
        "b_covers_change": (
            None if b_text is None else covers_change_condition(b_text, a_options)
        ),
    }


def check_dir(study_dir: Path) -> list[dict[str, Any]]:
    files = sorted(p for p in study_dir.glob("S*.json"))
    return [check_item(json.loads(p.read_text(encoding="utf-8"))) for p in files]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Faithfulness-Vorprüfung der Erklärungen")
    p.add_argument("--dir", default=str(_DEFAULT_DIR))
    args = p.parse_args()

    results = check_dir(Path(args.dir))
    if not results:
        print(f"Keine S*.json in {args.dir} — erst `study_freeze` ausführen.")
        return

    print(
        f"{'SID':5s} {'Aktion':9s} {'A-konsist':10s} {'A-Zahl':7s} "
        f"{'B-konsist':13s} B-Änderung"
    )
    print("-" * 78)
    a_ok = 0
    b_total = 0
    b_ok = 0
    b_change_total = 0
    b_change_ok = 0
    for r in results:
        ga = r["group_a"]
        a_ok += 1 if ga["action_consistent"] else 0
        chk = r["group_b"]
        if chk is None:
            gb_str = "–"
        else:
            b_total += 1
            b_ok += 1 if chk["action_consistent"] else 0
            gb_str = "✓" if chk["action_consistent"] else "✗ WIDERSPRUCH"
        cov = r["b_covers_change"]
        if cov is None:
            cov_str = "–"
        else:
            b_change_total += 1
            b_change_ok += 1 if cov else 0
            cov_str = "✓" if cov else "✗ FEHLT"
        print(
            f"  {r['sid']:4s} {r['action']:9s} "
            f"{'✓' if ga['action_consistent'] else '✗ WIDERSPRUCH':10s} "
            f"{'✓' if ga['has_number'] else '–':7s} "
            f"{gb_str:13s} {cov_str}"
        )
    print("-" * 78)
    print(f"Gruppe A konsistent: {a_ok}/{len(results)}")
    if b_total:
        print(f"Gruppe B konsistent: {b_ok}/{b_total}")
        if b_change_total:
            print(f"Gruppe B trägt Änderungsbedingung: {b_change_ok}/{b_change_total}")
    else:
        print("Gruppe B: noch nicht generiert (OLLAMA_HOST setzen + study_freeze).")
    print("\nHinweis: automatische Vorstufe — manuelle Bewertung bleibt nötig.")


if __name__ == "__main__":
    main()
