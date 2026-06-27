"""
Kanonische SoC-Band-Studienszenarien (deterministisch, reproduzierbar).

Code-Spiegel der konstruierten Snapshots aus
``docs/research/.../2024d_scenarios/soc_band_tagesverlauf.md`` — jede Zeile ein
unabhängiger, gegen den Kern verifizierter Zustand (``strategy="soc_band"``).
Damit lassen sich die Szenarien wie das Surplus-Set (``study_scenarios.py``)
durch ``study_freeze`` replayen und gemeinsam mit den Erklärungen einfrieren.

Werte an realen HA-Daten geerdet (Recorder 2026-05-24..06-03, Frühsommer): PV
0..9,3 kW (Ø 2,0), Hauslast Ø ~0,7 kW (max 5,1), Miner Eco ~1,6 kW / Super
~3,2 kW gesamt. Der Speicher erreicht real fast täglich 99..100 % SoC; die
Standard- (≥ 80 %) und Super-Bänder (≥ 90 %) werden im Realbetrieb also
regelmäßig durchlaufen, die SoC-Werte sind real geerdet. Einzig die Chip-
Temperatur 113 °C (SB07) ist konstruiert: real blieb der Miner ≤ 75 °C, ein
Übertemperatur-Stopp lässt sich nicht ohne Hardware-Risiko aus Echtdaten ziehen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.core.models import EnergyState
from src.core.rule_engine import RuleEngineConfig

# Studien-Config: reale SoC-Band-Parameter (Produktivsystem) + reale Temperaturgrenze
# (Kern-Default 85) + Nachtsperre. Diese Config gilt für ALLE Szenarien hier.
SOC_BAND_CONFIG = RuleEngineConfig(
    strategy="soc_band",
    pv_start_w=6000.0,
    max_grid_import_w=300.0,
    max_chip_temp_c=112.0,
    night_block_enabled=True,
)

_DAY = datetime(2026, 6, 15, tzinfo=timezone.utc)


def _state(
    hhmm: str,
    *,
    pv: float,
    load: float,
    soc: float,
    temp: float = 45.0,
    hb: float = 5.0,
    grid: float = 0.0,
) -> EnergyState:
    h, m = int(hhmm[:2]), int(hhmm[2:])
    start = _DAY + timedelta(hours=h, minutes=m)
    return EnergyState(
        block_id=f"2026-06-15T{hhmm}",
        window_start=start,
        window_end=start + timedelta(minutes=10),
        pv_power_w=pv,
        house_load_w=load,
        grid_import_w=grid,
        battery_soc_pct=soc,
        miner_temp_c=temp,
        miner_heartbeat_age_sec=hb,
        surplus_kw=round((pv - load) / 1000.0, 3),
        quality="ok",
        missing_signals=(),
    )


def _now(hhmm: str) -> datetime:
    return _DAY + timedelta(hours=int(hhmm[:2]), minutes=int(hhmm[2:]))


@dataclass(frozen=True)
class SocBandScenario:
    """Ein SoC-Band-Snapshot: State + Engine-Kontext (inkl. ``now``) + erwarteter Code."""

    sid: str
    clock: str
    title: str
    state: EnergyState
    last_action: str | None
    blocks_since_change: int
    now: datetime
    expected_code: str


SOC_BAND_SCENARIOS: tuple[SocBandScenario, ...] = (
    SocBandScenario(
        "SB01",
        "06:00",
        "Morgentief (Akku über Nacht entladen)",
        _state("0600", pv=200, load=400, soc=21),
        None,
        0,
        _now("0600"),
        "STOP_R1_SOC_RESERVE_STOP",
    ),
    SocBandScenario(
        "SB02",
        "09:00",
        "Eco-Band, Sonne schwach",
        _state("0900", pv=3200, load=500, soc=60),
        None,
        0,
        _now("0900"),
        "NOOP_R1_SOC_HOLD_PV",
    ),
    SocBandScenario(
        "SB03",
        "10:30",
        "Frischstart Eco",
        _state("1030", pv=6300, load=500, soc=64),
        None,
        0,
        _now("1030"),
        "THROTTLE_R1_ECO",
    ),
    SocBandScenario(
        "SB04",
        "11:30",
        "Hochschalten Standard",
        _state("1130", pv=6500, load=500, soc=80),
        "START",
        5,
        _now("1130"),
        "START_R1_STANDARD",
    ),
    SocBandScenario(
        "SB05",
        "12:00",
        "Stufe halten (Anti-Flapping)",
        _state("1200", pv=2700, load=500, soc=78),
        "START",
        1,
        _now("1200"),
        "NOOP_R5_MIN_RUNTIME_NOT_REACHED",
    ),
    SocBandScenario(
        "SB06",
        "13:00",
        "Hochschalten Super",
        _state("1300", pv=8000, load=500, soc=91),
        "START",
        5,
        _now("1300"),
        "START_R1_SUPER",
    ),
    SocBandScenario(
        "SB07",
        "13:30",
        "Übertemperatur",
        _state("1330", pv=7800, load=500, soc=80, temp=113),
        "START",
        6,
        _now("1330"),
        "STOP_R3_OVERTEMP",
    ),
    SocBandScenario(
        "SB08",
        "14:30",
        "Wolke, Netzbezug",
        _state("1430", pv=800, load=1500, soc=88, grid=700),
        "START",
        5,
        _now("1430"),
        "STOP_R2_GRID_IMPORT_EXCEEDED",
    ),
    SocBandScenario(
        "SB09",
        "16:00",
        "Nachmittag, Eco auf Akku (laufender Miner)",
        _state("1600", pv=2200, load=500, soc=78),
        "THROTTLE",
        5,
        _now("1600"),
        "THROTTLE_R1_ECO",
    ),
    SocBandScenario(
        "SB10",
        "20:00",
        "Abend, Eco läuft zur Reserve aus",
        _state("2000", pv=0, load=800, soc=55),
        "THROTTLE",
        5,
        _now("2000"),
        "NOOP_R1_SOC_HOLD",
    ),
    SocBandScenario(
        "SB11",
        "21:00",
        "Hausreserve",
        _state("2100", pv=0, load=900, soc=48),
        "THROTTLE",
        5,
        _now("2100"),
        "STOP_R1_SOC_RESERVE_STOP",
    ),
    SocBandScenario(
        "SB12",
        "22:00",
        "Nachtsperre",
        _state("2200", pv=0, load=700, soc=70),
        None,
        0,
        _now("2200"),
        "NOOP_NIGHT_BLOCK",
    ),
)
