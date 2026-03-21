"""
Replay — führt historische EnergyStates durch den Core und vergleicht Decisions.

Verwendung:
    python -m sim.replay --fixture fixtures/state_nominal.json
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.core import rule_engine
from src.core.models import EnergyState
from src.sim.scenario_loader import load_fixture, load_csv_scenario, rows_to_energy_states


def replay_fixture(fixture_path: str | Path) -> dict:
    """Replayed ein einzelnes JSON-Fixture und gibt das DecisionEvent als Dict zurück."""
    data = load_fixture(fixture_path)
    state = _dict_to_energy_state(data)
    event = rule_engine.evaluate(state)
    return {
        "fixture": str(fixture_path),
        "action": event.decision.action,
        "decision_code": event.decision_code,
        "reason": event.reason,
    }


def replay_scenario(csv_path: str | Path) -> list[dict]:
    """Replayed ein CSV-Szenario und gibt alle DecisionEvents als Liste zurück."""
    rows = load_csv_scenario(csv_path)
    states = rows_to_energy_states(rows)
    results = []
    last_action = None
    blocks_since_change = 0

    for state in states:
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

        results.append({
            "block_id": state.block_id,
            "action": event.decision.action,
            "decision_code": event.decision_code,
            "reason": event.reason,
        })
    return results


def _dict_to_energy_state(data: dict) -> EnergyState:
    from datetime import datetime
    return EnergyState(
        block_id=data["block_id"],
        window_start=datetime.fromisoformat(data["window_start"]),
        window_end=datetime.fromisoformat(data["window_end"]),
        pv_power_w=data["pv_power_w"],
        house_load_w=data["house_load_w"],
        grid_import_w=data["grid_import_w"],
        battery_soc_pct=data["battery_soc_pct"],
        miner_temp_c=data["miner_temp_c"],
        miner_heartbeat_age_sec=data["miner_heartbeat_age_sec"],
        surplus_kw=data["surplus_kw"],
        quality=data["quality"],
        missing_signals=tuple(data.get("missing_signals", [])),
        grid_export_w=data.get("grid_export_w"),
        energy_price_ct_kwh=data.get("energy_price_ct_kwh"),
        pv_forecast_kw=data.get("pv_forecast_kw"),
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BitGridAI Replay")
    parser.add_argument("--fixture", help="Pfad zu einem JSON-Fixture")
    parser.add_argument("--scenario", help="Pfad zu einem CSV-Szenario")
    args = parser.parse_args()

    if args.fixture:
        result = replay_fixture(args.fixture)
        print(json.dumps(result, indent=2, default=str))
    elif args.scenario:
        results = replay_scenario(args.scenario)
        print(json.dumps(results, indent=2, default=str))
    else:
        parser.print_help()
