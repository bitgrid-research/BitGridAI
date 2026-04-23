"""
Domänenobjekte von BitGridAI.

EnergyState  — unveränderlicher Snapshot aller Messwerte eines Blocks
Decision     — Aktion + Gültigkeitsfenster
DecisionEvent — vollständiges Audit-Objekt (State + Decision + Kontext)
RuleVote     — Stimmabgabe einer einzelnen Regel
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, NamedTuple

# ---------------------------------------------------------------------------
# EnergyState
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EnergyState:
    """Unveränderlicher Snapshot aller Messwerte für einen 10-Minuten-Block."""

    block_id: str
    window_start: datetime
    window_end: datetime

    # Pflichtfelder — Messwerte in SI-Einheiten
    pv_power_w: float
    house_load_w: float
    grid_import_w: float
    battery_soc_pct: float
    miner_temp_c: float
    miner_heartbeat_age_sec: float

    # Abgeleiteter Wert — wird von energy_context berechnet
    surplus_kw: float  # (pv_power_w - house_load_w) / 1000

    # Datenqualität
    quality: Literal["ok", "warn", "error"]
    missing_signals: tuple[str, ...] = field(default_factory=tuple)

    # Optionale Felder
    grid_export_w: float | None = None
    miner_power_w: float | None = None
    heizstab_power_w: float | None = None
    energy_price_ct_kwh: float | None = None
    pv_forecast_kw: float | None = None


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    """Aktion des Core für einen Block, gültig bis valid_until."""

    action: Literal["START", "STOP", "THROTTLE", "NOOP"]
    valid_until: datetime
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# DecisionEvent — vollständiges Audit-Objekt
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionEvent:
    """Vollständiges Audit-Objekt: Decision + Kontext + State-Snapshot."""

    decision: Decision
    reason: str  # maschinenlesbarer Code, z.B. "R3_OVERTEMP"
    trigger: Literal["BLOCK_TICK", "SAFETY_ASYNC", "OVERRIDE"]
    params: dict[str, Any]  # verwendete Schwellenwerte zum Zeitpunkt der Entscheidung
    state_snapshot: EnergyState
    decision_code: str  # z.B. "STOP_R3_OVERTEMP_T92"


# ---------------------------------------------------------------------------
# RuleVote — Stimmabgabe einer Regel
# ---------------------------------------------------------------------------


class RuleVote(NamedTuple):
    """Stimmabgabe einer einzelnen Regel R1–R5."""

    rule: Literal["R1", "R2", "R3", "R4", "R5"]
    action: Literal["START", "STOP", "THROTTLE", "NOOP"]
    confidence: float  # 0.0 – 1.0
    reason: str  # maschinenlesbar, z.B. "SURPLUS_OK"
