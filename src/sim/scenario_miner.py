"""
ScenarioMiner — findet reale Blöcke je Studien-Szenario (S1–S10).

Statt erfundener EnergyState-Werte werden die 10 Studien-Szenarien aus echten,
augmentierten HA-Tagen belegt: jeder Tag wird durch den deterministischen Kern
gereplayt, und je Ziel-``decision_code`` wird ein repräsentativer realer Block
mit voller Herkunftsangabe (Quelldatei, Tageszeit, Messwerte) ausgewählt.

Energie-getriebene Szenarien (S1, S2, S6, S7, S8, S10) entstehen direkt aus
Realdaten. Die preis-/forecast-abhängigen (S3, S9) setzen ein zuvor
augmentiertes CSV voraus (siehe ``src.sim.augment``). Die Fault-Szenarien
(S4 Übertemperatur, S5 Comm-Timeout) treten in normalen Daten nicht auf und
werden als „Injektion nötig" gemeldet.

Verwendung:
    python -m src.sim.scenario_miner src/sim/scenarios/real_2026-06-21_augmented.csv
    python -m src.sim.scenario_miner src/sim/scenarios/*.csv --window 4 --freeze-dir docs/study_set
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.sim.replay import replay_scenario
from src.sim.scenario_loader import load_csv_scenario

_BLOCK_MIN = 10
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


# ---------------------------------------------------------------------------
# Zuordnung decision_code → Studien-Szenario
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioSpec:
    """Definiert ein Studien-Szenario und wie es im decision_code erkannt wird."""

    scenario_id: str
    label: str
    match: Callable[[str], bool]
    injection_only: bool = False  # tritt in realen Daten nicht natürlich auf


SCENARIO_SPECS: tuple[ScenarioSpec, ...] = (
    ScenarioSpec("S1", "Klarer Start", lambda c: c == "START_R1_SURPLUS_OK"),
    ScenarioSpec(
        "S2", "Kein Überschuss", lambda c: c == "NOOP_R1_INSUFFICIENT_SURPLUS"
    ),
    ScenarioSpec(
        "S3", "Sonne, aber Preis hoch", lambda c: c == "NOOP_R1_PRICE_TOO_HIGH"
    ),
    ScenarioSpec(
        "S4",
        "Übertemperatur",
        lambda c: c.startswith("STOP_R3_OVERTEMP"),
        injection_only=True,
    ),
    ScenarioSpec(
        "S5",
        "Kommunikationsausfall",
        lambda c: c.startswith("STOP_R3_COMM_TIMEOUT"),
        injection_only=True,
    ),
    ScenarioSpec("S6", "Batterie-Schutz (soft)", lambda c: c == "NOOP_R2_SOC_SOFT_MIN"),
    ScenarioSpec(
        "S7", "Batterie-Notstopp (hard)", lambda c: c == "STOP_R2_SOC_HARD_MIN"
    ),
    ScenarioSpec(
        "S8", "Wolke → Netzbezug", lambda c: c == "STOP_R2_GRID_IMPORT_EXCEEDED"
    ),
    ScenarioSpec(
        "S9", "Forecast blockiert", lambda c: c == "NOOP_R4_FORECAST_PV_INSUFFICIENT"
    ),
    ScenarioSpec("S10", "Anti-Flapping", lambda c: c.startswith("NOOP_R5_")),
)


# ---------------------------------------------------------------------------
# Match-Ergebnis
# ---------------------------------------------------------------------------


@dataclass
class ScenarioMatch:
    spec: ScenarioSpec
    count: int = 0
    source_file: str | None = None
    date: str | None = None
    index: int | None = None  # Blockindex in der Quelldatei
    offset_min: int | None = None
    decision_code: str | None = None
    reason: str | None = None
    state: dict[str, Any] = field(default_factory=dict)

    @property
    def found(self) -> bool:
        return self.count > 0

    def time_of_day(self) -> str:
        if self.offset_min is None:
            return "—"
        minute = self.offset_min % 1440
        return f"{minute // 60:02d}:{minute % 60:02d}"


def _date_from(path: Path, comments: dict[str, str]) -> str:
    if "date" in comments:
        return comments["date"]
    m = _DATE_RE.search(path.name)
    return m.group(1) if m else path.stem


def _read_comment_meta(path: str | Path) -> dict[str, str]:
    """Liest '# key: value'-Metadaten aus dem Kommentar-Header."""
    meta: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s.startswith("#"):
                if s:
                    break
                continue
            body = s[1:].strip()
            if ":" in body:
                key, _, value = body.partition(":")
                meta[key.strip()] = value.strip()
    return meta


def mine_files(
    paths: list[Path],
) -> dict[str, ScenarioMatch]:
    """
    Replayt alle Dateien und sucht je Szenario den ersten passenden Realblock.

    Gibt ein Dict scenario_id → ScenarioMatch zurück (auch für nicht gefundene).
    """
    matches: dict[str, ScenarioMatch] = {
        spec.scenario_id: ScenarioMatch(spec) for spec in SCENARIO_SPECS
    }

    for path in paths:
        rows = load_csv_scenario(path)
        events = replay_scenario(path)
        meta = _read_comment_meta(path)
        date = _date_from(path, meta)

        for i, event in enumerate(events):
            code = event["decision_code"]
            for spec in SCENARIO_SPECS:
                if not spec.match(code):
                    continue
                m = matches[spec.scenario_id]
                m.count += 1
                # Ersten Treffer als Repräsentanten festhalten
                if m.source_file is None:
                    row = rows[i]
                    pv = row["pv_power_w"]
                    load = row["house_load_w"]
                    m.source_file = path.name
                    m.date = date
                    m.index = i
                    m.offset_min = int(row["timestamp_offset_min"])
                    m.decision_code = code
                    m.reason = event["reason"]
                    m.state = {
                        "pv_power_w": pv,
                        "house_load_w": load,
                        "surplus_kw": round((pv - load) / 1000.0, 3),
                        "grid_import_w": row["grid_import_w"],
                        "battery_soc_pct": row["battery_soc_pct"],
                        "miner_temp_c": row["miner_temp_c"],
                        "energy_price_ct_kwh": row.get("energy_price_ct_kwh"),
                        "pv_forecast_kw": row.get("pv_forecast_kw"),
                    }
    return matches


def freeze_window(
    match: ScenarioMatch,
    paths: list[Path],
    window: int,
    out_dir: Path,
) -> Path | None:
    """
    Schreibt den Repräsentanten-Block plus ``window`` Vorblöcke als Mini-CSV.

    Der Kontext erhält den realen R5-Verlauf (last_action / blocks_since_change),
    damit der eingefrorene Block beim Replay denselben decision_code liefert.
    """
    if not match.found or match.index is None or match.source_file is None:
        return None
    src = next((p for p in paths if p.name == match.source_file), None)
    if src is None:
        return None

    rows = load_csv_scenario(src)
    start = max(0, match.index - window)
    chunk = rows[start : match.index + 1]
    if not chunk:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{match.spec.scenario_id}_{match.date}.csv"
    from src.sim.augment import write_csv  # lokal: vermeidet Zyklus beim Import

    header = [
        f"# study_scenario: {match.spec.scenario_id} ({match.spec.label})",
        f"# source: {match.source_file}  block_index: {match.index}",
        f"# decision_code: {match.decision_code}",
    ]
    # Offsets neu basieren, damit das Mini-CSV bei 0 startet
    rebased = []
    for k, row in enumerate(chunk):
        new_row = dict(row)
        new_row["timestamp_offset_min"] = k * _BLOCK_MIN
        rebased.append(new_row)
    write_csv(rebased, out_path, header)
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_report(matches: dict[str, ScenarioMatch]) -> None:
    print(f"\n{'ID':4s} {'Szenario':26s} {'Treffer':>8s}  Repräsentant")
    print("-" * 88)
    for spec in SCENARIO_SPECS:
        m = matches[spec.scenario_id]
        if m.found:
            s = m.state
            detail = (
                f"{m.date} {m.time_of_day()}  "
                f"surplus={s['surplus_kw']:.2f}kW soc={s['battery_soc_pct']:.0f}% "
                f"grid={s['grid_import_w']:.0f}W → {m.decision_code}"
            )
            print(f"{spec.scenario_id:4s} {spec.label:26s} {m.count:>8d}  {detail}")
        else:
            note = "INJEKTION NÖTIG" if spec.injection_only else "nicht gefunden"
            print(f"{spec.scenario_id:4s} {spec.label:26s} {m.count:>8d}  — {note}")


def _force_utf8_stdout() -> None:
    """Stellt stdout auf UTF-8 (Windows-Konsole nutzt sonst cp1252 → UnicodeError)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


def main() -> None:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="Findet reale Blöcke je Studien-Szenario (S1–S10) in augmentierten HA-Tagen"
    )
    parser.add_argument("csv", nargs="+", help="Eine oder mehrere Szenario-CSVs")
    parser.add_argument(
        "--window",
        type=int,
        default=0,
        help="Vorblöcke für den eingefrorenen Kontext (0 = nicht einfrieren)",
    )
    parser.add_argument(
        "--freeze-dir", help="Verzeichnis für eingefrorene Studien-CSVs"
    )
    args = parser.parse_args()

    paths = [Path(p) for p in args.csv]
    missing = [p for p in paths if not p.exists()]
    if missing:
        parser.error("Datei(en) nicht gefunden: " + ", ".join(str(p) for p in missing))

    matches = mine_files(paths)
    _print_report(matches)

    if args.freeze_dir and args.window > 0:
        out_dir = Path(args.freeze_dir)
        print(f"\n→ Friere Studien-Set ein ({args.window} Vorblöcke) → {out_dir}")
        for spec in SCENARIO_SPECS:
            frozen = freeze_window(
                matches[spec.scenario_id], paths, args.window, out_dir
            )
            if frozen:
                print(f"   ✓ {spec.scenario_id}: {frozen.name}")


if __name__ == "__main__":
    main()
