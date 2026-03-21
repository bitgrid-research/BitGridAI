"""Unit-Tests für R2 Autarkie."""

from __future__ import annotations

from src.core.models import EnergyState
from src.core.rules import r2_autarky


def test_hard_min_soc_triggers_stop(low_soc_state: EnergyState) -> None:
    vote = r2_autarky.evaluate(low_soc_state, soc_hard_min_pct=10.0)
    assert vote is not None
    assert vote.action == "STOP"
    assert "SOC_HARD_MIN" in vote.reason


def test_soft_min_soc_triggers_noop(nominal_state: EnergyState) -> None:
    from src.core.models import EnergyState as ES
    soft_state = EnergyState(
        **{**nominal_state.__dict__, "battery_soc_pct": 15.0}  # type: ignore[arg-type]
    )
    vote = r2_autarky.evaluate(soft_state, soc_soft_min_pct=20.0, soc_hard_min_pct=10.0)
    assert vote is not None
    assert vote.action == "NOOP"
    assert "SOC_SOFT_MIN" in vote.reason


def test_grid_import_exceeded_triggers_stop(nominal_state: EnergyState) -> None:
    import_state = EnergyState(
        **{**nominal_state.__dict__, "grid_import_w": 800.0}  # type: ignore[arg-type]
    )
    vote = r2_autarky.evaluate(import_state, max_grid_import_w=500.0)
    assert vote is not None
    assert vote.action == "STOP"


def test_healthy_battery_returns_none(nominal_state: EnergyState) -> None:
    vote = r2_autarky.evaluate(nominal_state)
    assert vote is None
