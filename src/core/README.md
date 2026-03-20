# src/core

Deterministischer Entscheidungskern.

Der Core ist das Herzstück von BitGridAI: Er empfängt Messwerte, bewertet Regeln und erzeugt Entscheidungen. Kein Cloud-Call, kein ML-Modell, kein globaler Zustand — nur deterministisches Input-Output.

---

## Verzeichnisstruktur

```
core/
├── models.py              # Domänenobjekte: EnergyState, Decision, DecisionEvent
├── energy_context.py      # EnergyState aufbauen, normalisieren, validieren
├── block_scheduler.py     # 10-Minuten-Takt, block_id, valid_until
├── rule_engine.py         # R1–R5 bewerten, priorisieren, Decision erzeugen
├── override_handler.py    # Manuelle Overrides, Autonomie-Stufen
├── rules/
│   ├── r1_profitability.py    # R1: Surplus >= Schwelle && Preis ok
│   ├── r2_autarky.py          # R2: SoC und Grid-Import Grenzen
│   ├── r3_safety.py           # R3: Temperatur, Timeout → Safety-Stop (nie überstimmbar)
│   ├── r4_forecast.py         # R4: Vorschau auf nächste Blöcke
│   └── r5_stability.py        # R5: Deadband, Mindestlaufzeiten
└── __init__.py
```

---

## Zentrale Datentypen (`models.py`)

```python
@dataclass(frozen=True)
class EnergyState:
    block_id: str                  # "2024-01-15T10:00:00"
    window_start: datetime
    window_end: datetime
    pv_power_w: float
    house_load_w: float
    grid_import_w: float
    battery_soc_pct: float
    miner_temp_c: float
    miner_heartbeat_age_sec: float
    surplus_kw: float              # abgeleitet: (pv - house_load) / 1000
    quality: Literal["ok", "warn", "error"]
    missing_signals: list[str]
    # Optional / Optimierung
    grid_export_w: float | None = None
    energy_price_ct_kwh: float | None = None
    pv_forecast_kw: float | None = None

@dataclass(frozen=True)
class Decision:
    action: Literal["START", "STOP", "THROTTLE", "NOOP"]
    valid_until: datetime
    command_id: str                # UUID, eindeutig je Block

@dataclass(frozen=True)
class DecisionEvent:
    decision: Decision
    reason: str                    # z.B. "R3_OVERTEMP"
    trigger: str                   # "BLOCK_TICK" | "SAFETY_ASYNC" | "OVERRIDE"
    params: dict                   # relevante Schwellen-Werte zum Zeitpunkt
    state_snapshot: EnergyState
    decision_code: str             # z.B. "STOP_R3_OVERTEMP_T92"

class RuleVote(NamedTuple):
    rule: str                      # "R1" .. "R5"
    action: Literal["START", "STOP", "THROTTLE", "NOOP"]
    confidence: float              # 0.0–1.0
    reason: str
```

---

## Datenfluss

```
adapters/ ──► energy_context.py ──► EnergyState
                                         │
                            block_scheduler (Tick)
                                         │
                                    rule_engine
                                    ├── r1 … r5 (RuleVotes)
                                    ├── Priorisierung: R3 > R2 > R4 > R5 > R1
                                    └── Decision + DecisionEvent
                                         │
                          ┌──────────────┼──────────────┐
                       adapters/      data/           explain/
                    (Aktor-Kommando) (Logging)    (Textbausteine)
```

---

## Konventionen

**Deterministisch:** `rule_engine.evaluate(state: EnergyState) -> DecisionEvent` ist eine pure Funktion — kein I/O, kein globaler State. Gleicher Input → gleicher Output. Immer.

**Safety-First:** R3 erzeugt direkt eine `Decision(action="STOP")` und bricht die Evaluierung der anderen Regeln ab. `override_handler` darf R3-Entscheidungen nie aufheben (`allow_unsafe_override` ist hardcoded `False`).

**Immutable State:** `EnergyState` ist `frozen=True`. Niemals nachträglich modifizieren — das bricht Replay-Fähigkeit.

**Timeboxing:** `block_scheduler` setzt ein Timeout für die Regel-Evaluierung (Default: 80 % der Blockdauer). Bei Überschreitung: `Decision(action="STOP", reason="TIMEOUT_SAFE")`.

---

## Einstiegspunkte für Entwickler

| Aufgabe | Datei |
|---|---|
| Neue Regel hinzufügen | `rules/r_new.py` + Eintrag in `rule_engine.py` |
| Schwellen anpassen | Config in `ops/config/rules.yaml`, nicht im Code |
| EnergyState erweitern | `models.py` + `energy_context.py` |
| Block-Takt ändern | `block_scheduler.py` + `ops/config/system.yaml` |
| Override-Logik | `override_handler.py` |

---

## Tests

Jede Regel hat eigene Unit-Tests in `tests/core/rules/test_r*.py`.

Fixture-Format: `tests/core/fixtures/state_*.json` — serialisierte `EnergyState`-Objekte für Replay-Tests.

```bash
pytest tests/core/ -v
```

---

## Nächste Schritte

- [ ] `models.py` implementieren (Basis für alle anderen Module)
- [ ] `energy_context.py`: Normalizer + Completeness Guard
- [ ] `rules/r3_safety.py` zuerst (Safety ist non-negotiable)
- [ ] `block_scheduler.py`: Tick-Loop + `valid_until`-Berechnung
- [ ] `rule_engine.py`: Priorisierung + Conflict Resolver
- [ ] `override_handler.py`: Autonomie-Stufen + R3-Sperre
