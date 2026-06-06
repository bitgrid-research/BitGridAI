"""
Studien-Freeze — friert die 10 Szenarien gemeinsam mit ihren Erklärungen ein.

Pro Szenario: Replay durch den deterministischen Kern → DecisionEvent, dann
Gruppe-A-Erklärung (statische Bausteine) und Gruppe-B-Slots je Persona
(energie/waerme/tech). Gruppe B wird nur gefüllt, wenn OLLAMA_HOST gesetzt ist
(externer Ollama-Rechner) — sonst bleiben Platzhalter (None).

So entsteht ein **reproduzierbares, ausfallsicheres Studien-Paket**: Stimuli +
Erklärungen sind eingefroren, unabhängig von der Live-Verfügbarkeit des LLM.

  python -m src.sim.study_freeze                 # Gruppe A + B-Platzhalter
  OLLAMA_HOST=http://host:11434 python -m src.sim.study_freeze   # + Gruppe B
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from src.core import rule_engine
from src.core.rule_engine import RuleEngineConfig
from src.explain.decision_codes import ALL_CODES
from src.explain.explain_agent import (
    ExplainAgent,
    load_hamster_states,
    load_persona_examples,
)
from src.sim.study_scenarios import STUDY_SCENARIOS, StudyScenario

_PERSONAS = ("energie", "waerme", "tech")
_DEFAULT_OUT = Path("src/sim/study_set")

# Few-Shot-Gold-Referenzen je Persona + Hamster-Anzeige je Aktion (einmalig geladen).
_PERSONA_EXAMPLES = load_persona_examples()
_HAMSTER_STATES = load_hamster_states()


def base_code(code: str) -> str:
    """Normalisiert einen decision_code auf den Basis-Code (für Text-Lookup)."""
    for base in sorted(ALL_CODES, key=len, reverse=True):
        if code == base or code.startswith(base + "_"):
            return base
    return code


def _state_dict(sc: StudyScenario) -> dict[str, Any]:
    s = sc.state
    return {
        "block_id": s.block_id,
        "pv_power_w": s.pv_power_w,
        "house_load_w": s.house_load_w,
        "surplus_kw": s.surplus_kw,
        "grid_import_w": s.grid_import_w,
        "grid_export_w": s.grid_export_w,
        "battery_soc_pct": s.battery_soc_pct,
        "miner_temp_c": s.miner_temp_c,
        "miner_heartbeat_age_sec": s.miner_heartbeat_age_sec,
        "energy_price_ct_kwh": s.energy_price_ct_kwh,
        "pv_forecast_kw": s.pv_forecast_kw,
        "quality": s.quality,
    }


def _group_a(agent: ExplainAgent, code: str, params: dict[str, Any]) -> dict[str, str]:
    r = agent.explain(base_code(code), params)
    return {
        "short": r.short,
        "long": r.long,
        "trigger": r.trigger,
        "data_basis": r.data_basis,
        "effect": r.effect,
        "options": r.options,
    }


def _group_b(
    code: str, params: dict[str, Any], ollama_host: str
) -> dict[str, str | None]:
    """Generiert Gruppe-B-Texte je Persona (wenn Ollama erreichbar), sonst Platzhalter."""
    out: dict[str, str | None] = {}
    if not ollama_host:
        return {p: None for p in _PERSONAS}
    saved = os.environ.get("OLLAMA_PERSONA")
    try:
        for persona in _PERSONAS:
            os.environ["OLLAMA_PERSONA"] = persona
            agent = ExplainAgent()  # liest OLLAMA_HOST + OLLAMA_PERSONA
            out[persona] = agent.explain(base_code(code), params).short
    finally:
        if saved is None:
            os.environ.pop("OLLAMA_PERSONA", None)
        else:
            os.environ["OLLAMA_PERSONA"] = saved
    return out


def freeze_one(
    sc: StudyScenario, agent_a: ExplainAgent, ollama_host: str
) -> dict[str, Any]:
    event = rule_engine.evaluate(
        sc.state,
        config=RuleEngineConfig(),
        last_action=sc.last_action,
        blocks_since_last_change=sc.blocks_since_change,
    )
    code = event.decision_code
    action = event.decision.action
    ref = _PERSONA_EXAMPLES.get(base_code(code), {})
    return {
        "sid": sc.sid,
        "title": sc.title,
        "expected_code": sc.expected_code,
        "actual_code": code,
        "verified": code == sc.expected_code,
        "decision": {
            "action": action,
            "code": code,
            "base_code": base_code(code),
            "reason": event.reason,
        },
        "hamster": _HAMSTER_STATES.get(action, {}),
        "engine_input": {
            "last_action": sc.last_action,
            "blocks_since_change": sc.blocks_since_change,
        },
        "state": _state_dict(sc),
        "params": event.params,
        "explanation": {
            "group_a": _group_a(agent_a, code, event.params),
            # Gold-Referenz je Persona (Few-Shot-Anker; Vergleichsziel für group_b).
            "group_b_reference": {p: ref.get(p) for p in _PERSONAS},
            # Echter LLM-Output je Persona (None bis Ollama verkabelt).
            "group_b": _group_b(code, event.params, ollama_host),
        },
    }


def freeze_all(out_dir: Path, ollama_host: str) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Gruppe A immer ohne LLM (reine Templates) — OLLAMA_HOST temporär leeren.
    saved_host = os.environ.get("OLLAMA_HOST")
    os.environ["OLLAMA_HOST"] = ""
    try:
        agent_a = ExplainAgent()
    finally:
        if saved_host is None:
            os.environ.pop("OLLAMA_HOST", None)
        else:
            os.environ["OLLAMA_HOST"] = saved_host

    items: list[dict[str, Any]] = []
    for sc in STUDY_SCENARIOS:
        item = freeze_one(sc, agent_a, ollama_host)
        (out_dir / f"{sc.sid}.json").write_text(
            json.dumps(item, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        items.append(item)

    index = [
        {
            "sid": it["sid"],
            "title": it["title"],
            "code": it["actual_code"],
            "verified": it["verified"],
            "group_b_filled": all(
                v is not None for v in it["explanation"]["group_b"].values()
            ),
        }
        for it in items
    ]
    (out_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return items


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(
        description="Studien-Szenarien + Erklärungen einfrieren"
    )
    p.add_argument("--out", default=str(_DEFAULT_OUT))
    args = p.parse_args()

    ollama_host = os.environ.get("OLLAMA_HOST", "").rstrip("/")
    items = freeze_all(Path(args.out), ollama_host)

    print(
        f"→ Ausgabe: {args.out}   Gruppe B: {'AKTIV' if ollama_host else 'Platzhalter (kein OLLAMA_HOST)'}"
    )
    print("-" * 70)
    ok = 0
    for it in items:
        v = "✓" if it["verified"] else "✗ MISMATCH"
        gb = (
            "B✓"
            if all(x is not None for x in it["explanation"]["group_b"].values())
            else "B–"
        )
        print(f"  {it['sid']:4s} {v:10s} {gb}  {it['actual_code']}")
        ok += 1 if it["verified"] else 0
    print("-" * 70)
    print(f"{ok}/{len(items)} verifiziert (Kern-Output == erwarteter Code)")


if __name__ == "__main__":
    main()
