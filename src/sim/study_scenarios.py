"""
Kanonische Studien-Szenarien S1–S10 (deterministisch, reproduzierbar).

Spiegelt die Spezifikationen aus
docs/.../2024_study_design_context/2024d_scenarios/ — als Code, damit der
Studien-Freeze (`study_freeze.py`) sie durch den Kern replayen und gemeinsam mit
den Erklärungen einfrieren kann.

`expected_code` dient der Verifikation (Test): Kern-Output == erwarteter Code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.core.models import EnergyState

_BASE_DAY = datetime(2026, 6, 15, tzinfo=timezone.utc)


def _state(
    hhmm: str,
    *,
    pv: float,
    load: float,
    soc: float,
    temp: float,
    hb: float,
    grid_in: float = 0.0,
    grid_ex: float | None = None,
    price: float | None = None,
    forecast: float | None = None,
    quality: str = "ok",
    missing: tuple[str, ...] = (),
) -> EnergyState:
    h, m = int(hhmm[:2]), int(hhmm[2:])
    start = _BASE_DAY + timedelta(hours=h, minutes=m)
    return EnergyState(
        block_id=f"2026-06-15T{hhmm}",
        window_start=start,
        window_end=start + timedelta(minutes=10),
        pv_power_w=pv,
        house_load_w=load,
        grid_import_w=grid_in,
        battery_soc_pct=soc,
        miner_temp_c=temp,
        miner_heartbeat_age_sec=hb,
        surplus_kw=round((pv - load) / 1000.0, 3),
        quality=quality,  # type: ignore[arg-type]
        missing_signals=missing,
        grid_export_w=grid_ex,
        energy_price_ct_kwh=price,
        pv_forecast_kw=forecast,
    )


@dataclass(frozen=True)
class StudyScenario:
    """Ein Studien-Szenario: Eingangs-State + Engine-Kontext + erwarteter Code."""

    sid: str
    title: str
    state: EnergyState
    last_action: str | None
    blocks_since_change: int
    expected_code: str


STUDY_SCENARIOS: tuple[StudyScenario, ...] = (
    StudyScenario(
        "S1",
        "Klarer Start",
        _state(
            "1030", pv=4500, load=1500, soc=80, temp=45, hb=5, price=12, forecast=4.0
        ),
        last_action="STOP",
        blocks_since_change=5,
        expected_code="START_R1_SURPLUS_OK",
    ),
    StudyScenario(
        "S2",
        "Kein Überschuss",
        _state(
            "0700", pv=1700, load=1300, soc=70, temp=30, hb=5, price=18, forecast=3.0
        ),
        last_action=None,
        blocks_since_change=0,
        expected_code="NOOP_R1_INSUFFICIENT_SURPLUS",
    ),
    StudyScenario(
        "S3",
        "Sonne, aber Preis zu hoch",
        _state(
            "1730", pv=4000, load=1500, soc=70, temp=40, hb=5, price=28, forecast=2.5
        ),
        last_action="STOP",
        blocks_since_change=5,
        expected_code="NOOP_R1_PRICE_TOO_HIGH",
    ),
    StudyScenario(
        "S4",
        "Übertemperatur",
        _state(
            "1430", pv=4500, load=1500, soc=75, temp=90, hb=5, price=12, forecast=4.0
        ),
        last_action="START",
        blocks_since_change=6,
        expected_code="STOP_R3_OVERTEMP",
    ),
    StudyScenario(
        "S5",
        "Kommunikationsausfall",
        _state(
            "1500",
            pv=4200,
            load=1500,
            soc=72,
            temp=50,
            hb=75,
            price=13,
            forecast=3.5,
            quality="warn",
            missing=("miner_heartbeat",),
        ),
        last_action="START",
        blocks_since_change=2,
        expected_code="STOP_R3_COMM_TIMEOUT",
    ),
    StudyScenario(
        "S6",
        "Batterie-Schutz (soft)",
        _state(
            "0900", pv=3800, load=1300, soc=55, temp=30, hb=5, price=14, forecast=3.5
        ),
        last_action=None,
        blocks_since_change=0,
        expected_code="NOOP_R2_SOC_SOFT_MIN",
    ),
    StudyScenario(
        "S7",
        "Batterie-Notstopp (hard)",
        _state(
            "1630",
            pv=1200,
            load=1400,
            soc=45,
            temp=55,
            hb=5,
            grid_in=200,
            price=20,
            forecast=1.5,
        ),
        last_action="START",
        blocks_since_change=6,
        expected_code="STOP_R2_SOC_HARD_MIN",
    ),
    StudyScenario(
        "S8",
        "Wolke → Netzbezug",
        _state(
            "1230",
            pv=800,
            load=1500,
            soc=65,
            temp=50,
            hb=5,
            grid_in=700,
            price=15,
            forecast=3.0,
        ),
        last_action="START",
        blocks_since_change=5,
        expected_code="STOP_R2_GRID_IMPORT_EXCEEDED",
    ),
    StudyScenario(
        "S9",
        "Forecast blockiert",
        _state(
            "1330", pv=3700, load=1500, soc=60, temp=45, hb=5, price=16, forecast=1.2
        ),
        last_action="STOP",
        blocks_since_change=4,
        expected_code="NOOP_R4_FORECAST_PV_INSUFFICIENT",
    ),
    StudyScenario(
        "S10",
        "Anti-Flapping",
        _state(
            "1100", pv=2700, load=1500, soc=78, temp=48, hb=5, price=12, forecast=3.0
        ),
        last_action="START",
        blocks_since_change=1,
        expected_code="NOOP_R5_MIN_RUNTIME_NOT_REACHED",
    ),
)
