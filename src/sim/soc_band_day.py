"""
SoC-Band-Tagessimulation mit **geschlossenem Regelkreis**.

Treibt eine exogene PV- und Hauslast-Kurve (aus ``synth_seasons``) Block fuer Block
durch den Kern mit ``strategy="soc_band"`` und schliesst die SoC-Rueckkopplung:
der vom Kern gewaehlte Miner-Modus zieht Leistung, und genau diese Leistung
bestimmt den SoC des naechsten Blocks. Dadurch sind SoC-Verlauf und
Entscheidungscodes in sich konsistent (anders als ``synth_seasons``, das den Miner
nicht modelliert).

Ergebnis: je ``decision_code`` der **erste** Block, in dem er auftritt, mit echten
(simulierten) Werten. Das ersetzt die handgesetzten SoC/PV-Zahlen der
Studienszenarien durch einen reproduzierbaren Replay.

Grenzen (bewusst, nicht versteckt):
- ``MINER_MODE_POWER_W`` ist eine **Annahme** (2x Avalon Q). Gegen den realen
  ``sensor.miner_power_w`` kalibrieren; der SoC-Verlauf haengt direkt daran.
- ``NOOP_NIGHT_BLOCK`` und die Modus-Rueckfall-Hysterese (75/85 %) sind noch
  **nicht** im Kern, entstehen hier also nicht. Bis sie im Kern sind, bleiben die
  22:00-Zeile und die "Rueckfall"-Optionen ausserhalb dieses Replays.
- Uebertemperatur / Comm-Timeout / Netzbezug-Stop sind Ereignis-Injektionen
  (kein Wetter): ``STOP_R3_OVERTEMP`` etc. werden hier nicht erzeugt, sondern
  ueber die handgesetzten Studienszenarien abgedeckt.

  python -m src.sim.soc_band_day --season sommer --start-soc 21
  python -m src.sim.soc_band_day --season sommer --start-soc 21 --out trace.csv
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.core import rule_engine
from src.core.models import DecisionEvent, EnergyState
from src.core.rule_engine import RuleEngineConfig
from src.sim.synth_seasons import SEASONS, SeasonProfile, _load_at, _pv_at

_BLOCK_MIN = 10
_BLOCKS = 144
_BASE_DAY = datetime(2026, 6, 15, tzinfo=timezone.utc)

# Miner-Leistung je realisiertem Betriebsmodus (2x Avalon Q).
# Eco/Super aus HA-Recorder belegt (miner1_mode_power_output 800 W/Miner Eco,
# 1600 W/Miner Super; miner_total_power_w-Max ~3395 W). Standard wurde im
# Recorder nie gesetzt → geschätzt (2x ~1200 W), bei Messung nachziehen.
MINER_MODE_POWER_W: dict[str, float] = {
    "Standby": 0.0,
    "Hold": 0.0,
    "Eco": 1600.0,
    "Standard": 2400.0,  # geschätzt: Standard-Modus real noch nicht beobachtet
    "Super": 3200.0,
}

# Zielcodes der SoC-Band-Studie, die aus dem Tagesverlauf emergieren koennen.
_SOC_BAND_TARGET_CODES = (
    "STOP_R1_SOC_RESERVE_STOP",
    "NOOP_R1_SOC_HOLD",
    "NOOP_R1_SOC_HOLD_PV",
    "THROTTLE_R1_ECO",
    "START_R1_STANDARD",
    "START_R1_SUPER",
    "NOOP_R5_MIN_RUNTIME_NOT_REACHED",
)


@dataclass(frozen=True)
class BlockRecord:
    """Ein simulierter Block: Eingangs-State, Entscheidung und Energiefluss."""

    index: int
    clock: str
    pv_w: float
    load_w: float
    miner_w: float
    grid_import_w: float
    grid_export_w: float
    soc_pct: float
    mode: str
    action: str
    decision_code: str


def _mode_from_code(decision_code: str) -> str:
    """Faellt der Modus nicht in params, leite ihn aus dem Code-Suffix ab."""
    if "SUPER" in decision_code:
        return "Super"
    if "STANDARD" in decision_code:
        return "Standard"
    if "ECO" in decision_code:
        return "Eco"
    return "Standby"


def _running_mode_after(event: DecisionEvent, previous_mode: str) -> str:
    """Realisierter Miner-Modus nach diesem Block (START/THROTTLE schalten,
    STOP schaltet ab, NOOP laesst den Zustand unveraendert)."""
    action = event.decision.action
    if action in ("START", "THROTTLE"):
        mode = event.params.get("mode")
        if not isinstance(mode, str) or mode not in MINER_MODE_POWER_W:
            mode = _mode_from_code(event.decision_code)
        return mode
    if action == "STOP":
        return "Standby"
    return previous_mode  # NOOP: unveraendert


def simulate_day(
    profile: SeasonProfile,
    start_soc_pct: float,
    battery_kwh: float,
    config: RuleEngineConfig,
) -> list[BlockRecord]:
    """Geschlossener Regelkreis ueber 144 Bloecke. Reine Funktion, deterministisch."""
    cap_wh = battery_kwh * 1000.0
    soc_wh = start_soc_pct / 100.0 * cap_wh
    dt_h = _BLOCK_MIN / 60.0

    running_mode = "Standby"
    blocks_since_change = 0
    grid_import_prev = 0.0  # Netzbezug des Vorblocks (1-Block-Lag fuer R2)

    records: list[BlockRecord] = []
    for i in range(_BLOCKS):
        minute = i * _BLOCK_MIN
        pv = _pv_at(minute, profile)
        load = _load_at(minute, profile)
        soc_pct = soc_wh / cap_wh * 100.0
        start = _BASE_DAY + timedelta(minutes=minute)

        # last_action spiegelt den realisierten Miner-Status (wie der reale
        # Status-Sensor), nicht die rohe Vorblock-Entscheidung — sonst haelt
        # r1_soc_band einen laufenden Miner nach einem R5-NOOP faelschlich fuer aus.
        running = running_mode != "Standby"
        if running_mode == "Eco":
            last_action: str | None = "THROTTLE"
        elif running:
            last_action = "START"
        else:
            last_action = None

        state = EnergyState(
            block_id=start.strftime("%Y-%m-%dT%H:%M"),
            window_start=start,
            window_end=start + timedelta(minutes=_BLOCK_MIN),
            pv_power_w=pv,
            house_load_w=load,
            grid_import_w=grid_import_prev,
            battery_soc_pct=round(soc_pct, 2),
            miner_temp_c=45.0,
            miner_heartbeat_age_sec=5.0,
            surplus_kw=round((pv - load) / 1000.0, 3),
            quality="ok",
            missing_signals=(),
        )

        event = rule_engine.evaluate(
            state,
            config,
            last_action=last_action,
            blocks_since_last_change=blocks_since_change,
            now=start,
        )

        running_mode = _running_mode_after(event, running_mode)
        miner_w = MINER_MODE_POWER_W[running_mode]

        # blocks_since_change = Bloecke seit dem letzten An/Aus-Wechsel des Miners.
        if (running_mode != "Standby") != running:
            blocks_since_change = 0
        else:
            blocks_since_change += 1

        # Batterie-Update: PV deckt Last + Miner, Rest laedt/entlaedt den Akku.
        net_w = pv - load - miner_w
        new_soc_wh = soc_wh + net_w * dt_h
        grid_export = 0.0
        grid_import = 0.0
        if new_soc_wh > cap_wh:
            grid_export = (new_soc_wh - cap_wh) / dt_h
            new_soc_wh = cap_wh
        elif new_soc_wh < 0.0:
            grid_import = -new_soc_wh / dt_h
            new_soc_wh = 0.0
        soc_wh = new_soc_wh
        grid_import_prev = grid_import

        records.append(
            BlockRecord(
                index=i,
                clock=start.strftime("%H:%M"),
                pv_w=round(pv, 1),
                load_w=round(load, 1),
                miner_w=miner_w,
                grid_import_w=round(grid_import, 1),
                grid_export_w=round(grid_export, 1),
                soc_pct=round(soc_pct, 1),
                mode=str(event.params.get("mode", running_mode)),
                action=event.decision.action,
                decision_code=event.decision_code,
            )
        )

    return records


def first_occurrences(records: list[BlockRecord]) -> dict[str, BlockRecord]:
    """Erster Block je decision_code (Reihenfolge des Tagesverlaufs)."""
    out: dict[str, BlockRecord] = {}
    for r in records:
        out.setdefault(r.decision_code, r)
    return out


def _print_timeline(records: list[BlockRecord]) -> None:
    """Kompakte Timeline: nur Bloecke, in denen sich der Code aendert."""
    print("\nTages-Timeline (nur Code-Wechsel):")
    print(f"  {'Zeit':5} {'PV kW':>6} {'Last':>5} {'Miner':>6} {'SoC':>5}  Code")
    prev = ""
    for r in records:
        if r.decision_code == prev:
            continue
        prev = r.decision_code
        print(
            f"  {r.clock:5} {r.pv_w/1000:6.1f} {r.load_w/1000:5.1f} "
            f"{r.miner_w/1000:6.1f} {r.soc_pct:4.0f}%  {r.decision_code}"
        )


def _print_instants(records: list[BlockRecord]) -> None:
    """Szenario-Instants: erster Block je Zielcode mit echten Werten."""
    seen = first_occurrences(records)
    print("\nSzenario-Instants (erstes Auftreten je Zielcode):")
    for code in _SOC_BAND_TARGET_CODES:
        r = seen.get(code)
        if r is None:
            print(f"  [ ] {code:34} — kommt im Tagesverlauf NICHT vor")
            continue
        print(
            f"  [x] {code:34} {r.clock}  SoC {r.soc_pct:4.0f}%  "
            f"PV {r.pv_w/1000:.1f} kW  Last {r.load_w/1000:.1f} kW  "
            f"Miner {r.miner_w/1000:.1f} kW  Modus {r.mode}"
        )


def _write_csv(records: list[BlockRecord], out: Path) -> None:
    cols = (
        "index,clock,pv_w,load_w,miner_w,grid_import_w,grid_export_w,"
        "soc_pct,mode,action,decision_code"
    )
    lines = ["# SoC-Band-Tagessimulation (geschlossener Regelkreis) — simuliert", cols]
    for r in records:
        lines.append(
            f"{r.index},{r.clock},{r.pv_w},{r.load_w},{r.miner_w},"
            f"{r.grid_import_w},{r.grid_export_w},{r.soc_pct},{r.mode},"
            f"{r.action},{r.decision_code}"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(description="SoC-Band-Tagessimulation (Regelkreis)")
    p.add_argument("--season", default="sommer", choices=sorted(SEASONS))
    p.add_argument("--start-soc", type=float, default=21.0, help="Start-SoC in %%")
    p.add_argument("--battery-kwh", type=float, default=10.0)
    p.add_argument("--pv-start-w", type=float, default=6000.0, help="Eco-Frischstart")
    p.add_argument("--out", help="optional: CSV-Trace schreiben")
    args = p.parse_args()

    profile = replace(
        SEASONS[args.season],
        start_soc_pct=args.start_soc,
        battery_kwh=args.battery_kwh,
    )
    config = RuleEngineConfig(
        strategy="soc_band",
        pv_start_w=args.pv_start_w,
        max_chip_temp_c=112.0,  # reale Avalon-Q-Grenze (Kern-Default 85)
        night_block_enabled=True,  # realer Betrieb hat Nachtsperre 22:00–06:00
    )

    records = simulate_day(profile, args.start_soc, args.battery_kwh, config)

    print(
        f"Saison={args.season}  Start-SoC={args.start_soc:.0f}%  "
        f"Akku={args.battery_kwh:.0f} kWh  Eco-Start-PV={args.pv_start_w/1000:.1f} kW"
    )
    socs = [r.soc_pct for r in records]
    print(f"SoC-Spanne {min(socs):.0f}–{max(socs):.0f} %")
    _print_timeline(records)
    _print_instants(records)

    if args.out:
        out = Path(args.out)
        _write_csv(records, out)
        print(f"\nTrace geschrieben: {out}")


if __name__ == "__main__":
    main()
