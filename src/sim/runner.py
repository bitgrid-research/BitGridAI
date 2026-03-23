"""
SimRunner — CSV-Feed mit konfigurierbarer Geschwindigkeit.

Verwendung:
    python -m sim.runner --scenario scenarios/sh1_stable_surplus.csv --speed 10
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.core import rule_engine
from src.sim.scenario_loader import load_csv_scenario, rows_to_energy_states

BLOCK_DURATION_SEC = 600  # 10 Minuten


def run(scenario_path: str | Path, speed: float = 1.0) -> None:
    """
    Führt ein Szenario aus und gibt Decisions auf stdout aus.

    speed: Faktor für die Simulation (10 = 10x Echtzeit, jeder Block in 60s)
    """
    rows = load_csv_scenario(scenario_path)
    states = rows_to_energy_states(rows)
    sleep_sec = BLOCK_DURATION_SEC / speed

    last_action = None
    blocks_since_change = 0

    print(f"[SIM] Starte Szenario: {scenario_path} (speed={speed}x)")

    for i, state in enumerate(states):
        event = rule_engine.evaluate(
            state,
            last_action=last_action,
            blocks_since_last_change=blocks_since_change,
        )

        if event.decision.action != last_action:
            blocks_since_change = 0
            last_action = event.decision.action
        else:
            blocks_since_change += 1

        output = {
            "block": i + 1,
            "block_id": state.block_id,
            "pv_kw": round(state.pv_power_w / 1000, 2),
            "surplus_kw": round(state.surplus_kw, 2),
            "soc_pct": state.battery_soc_pct,
            "temp_c": state.miner_temp_c,
            "action": event.decision.action,
            "code": event.decision_code,
        }
        print(json.dumps(output))

        if i < len(states) - 1:
            time.sleep(sleep_sec)

    print("[SIM] Szenario abgeschlossen.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BitGridAI Simulation Runner")
    parser.add_argument("--scenario", required=True, help="Pfad zum CSV-Szenario")
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Simulationsgeschwindigkeit (Default: 1.0)",
    )
    args = parser.parse_args()

    run(args.scenario, speed=args.speed)
