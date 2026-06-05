"""
Unit-Tests für die additive SoC-Band-Strategie (Produktiv-Nachbildung).

Invarianten:
- Mapping SoC-Band → Aktion + params["mode"] (Standby/Eco/Standard/Super/Hold)
- Reserve-Stop (SoC < soc_stop) hat Schutzpriorität — NICHT von R5 geblockt
- R3 Safety überstimmt auch unter strategy="soc_band"
- Default strategy="surplus" bleibt unverändert (kein Eingriff ins Frozen-Set)
- Determinismus: gleicher Input → gleicher Output
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.core import rule_engine
from src.core.models import EnergyState
from src.core.rule_engine import RuleEngineConfig

_SB = RuleEngineConfig(strategy="soc_band")


def _state(
    soc: float,
    pv: float = 0.0,
    temp: float = 42.0,
    grid: float = 0.0,
    heartbeat: float = 5.0,
) -> EnergyState:
    """EnergyState mit frei wählbarem SoC/PV; übrige Signale unkritisch."""
    return EnergyState(
        block_id="2026-06-05T12:00:00",
        window_start=datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 5, 12, 10, tzinfo=timezone.utc),
        pv_power_w=pv,
        house_load_w=500.0,
        grid_import_w=grid,
        battery_soc_pct=soc,
        miner_temp_c=temp,
        miner_heartbeat_age_sec=heartbeat,
        surplus_kw=(pv - 500.0) / 1000.0,
        quality="ok",
        missing_signals=(),
        energy_price_ct_kwh=None,
        pv_forecast_kw=None,
    )


# ── Band-Mapping ───────────────────────────────────────────────────────────────


def test_reserve_stop_below_soc_stop() -> None:
    event = rule_engine.evaluate(_state(soc=45.0), _SB)
    assert event.decision.action == "STOP"
    assert event.decision_code == "STOP_R1_SOC_RESERVE_STOP"
    assert event.params["mode"] == "Standby"


def test_hold_band_no_restart() -> None:
    """50 .. 58 %: kein Neustart (NOOP), laufender Miner bliebe unverändert."""
    event = rule_engine.evaluate(_state(soc=55.0), _SB)
    assert event.decision.action == "NOOP"
    assert event.decision_code == "NOOP_R1_SOC_HOLD"


def test_eco_fresh_start_requires_pv() -> None:
    """Eco-Band, Miner aus, PV unter Schwelle → kein Frischstart."""
    event = rule_engine.evaluate(_state(soc=65.0, pv=1000.0), _SB, last_action=None)
    assert event.decision.action == "NOOP"
    assert event.decision_code == "NOOP_R1_SOC_HOLD_PV"


def test_eco_fresh_start_with_pv() -> None:
    """Eco-Band, PV über pv_start_w → THROTTLE (Eco)."""
    event = rule_engine.evaluate(_state(soc=65.0, pv=6500.0), _SB, last_action=None)
    assert event.decision.action == "THROTTLE"
    assert event.decision_code == "THROTTLE_R1_ECO"
    assert event.params["mode"] == "Eco"


def test_eco_keeps_running_without_pv() -> None:
    """Eco-Band, Miner läuft bereits → bleibt im Eco trotz niedriger PV."""
    event = rule_engine.evaluate(
        _state(soc=65.0, pv=500.0),
        _SB,
        last_action="THROTTLE",
        blocks_since_last_change=5,
    )
    assert event.decision.action == "THROTTLE"
    assert event.decision_code == "THROTTLE_R1_ECO"


def test_standard_band() -> None:
    event = rule_engine.evaluate(_state(soc=85.0), _SB)
    assert event.decision.action == "START"
    assert event.decision_code == "START_R1_STANDARD"
    assert event.params["mode"] == "Standard"


def test_super_band() -> None:
    event = rule_engine.evaluate(_state(soc=95.0), _SB)
    assert event.decision.action == "START"
    assert event.decision_code == "START_R1_SUPER"
    assert event.params["mode"] == "Super"


# ── Prioritäten / Invarianten ───────────────────────────────────────────────────


def test_r3_overtemp_beats_soc_band() -> None:
    """R3 Safety überstimmt die SoC-Band-Strategie."""
    event = rule_engine.evaluate(_state(soc=95.0, temp=92.0), _SB)
    assert event.decision.action == "STOP"
    assert "R3" in event.decision_code


def test_reserve_stop_not_blocked_by_r5() -> None:
    """Reserve-Stop feuert auch wenn R5 (Min-Runtime) sonst NOOP erzwingen würde."""
    event = rule_engine.evaluate(
        _state(soc=45.0), _SB, last_action="START", blocks_since_last_change=1
    )
    assert event.decision.action == "STOP"
    assert event.decision_code == "STOP_R1_SOC_RESERVE_STOP"


def test_semi_mode_reserve_stop_becomes_noop() -> None:
    """SEMI: kein selbstständiger Stopp (außer R3) → Reserve-Stop wird NOOP."""
    event = rule_engine.evaluate(_state(soc=45.0), _SB, autonomy_level="SEMI")
    assert event.decision.action == "NOOP"
    assert event.decision_code == "NOOP_R1_SOC_RESERVE_STOP"


def test_determinism() -> None:
    s = _state(soc=85.0)
    e1 = rule_engine.evaluate(s, _SB)
    e2 = rule_engine.evaluate(s, _SB)
    assert e1.decision_code == e2.decision_code
    assert e1.params["mode"] == e2.params["mode"]


# ── Default-Strategie bleibt unangetastet ────────────────────────────────────────


def test_default_strategy_still_surplus() -> None:
    """Ohne strategy-Angabe gilt weiter die Surplus-kW-Logik (R1)."""
    state = _state(soc=80.0, pv=3500.0)  # Überschuss 3,0 kW
    event = rule_engine.evaluate(state)  # Default-Config
    assert event.decision.action == "START"
    assert event.decision_code == "START_R1_SURPLUS_OK"
