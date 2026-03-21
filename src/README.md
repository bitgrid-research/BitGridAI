# src/

Quellcode von BitGridAI — geordnet nach fachlicher Verantwortung.

---

## Module

| Ordner | Verantwortung |
|---|---|
| [core/](core/README.md) | Regel-Engine R1–R5, Block-Scheduler, EnergyState, Decision |
| [adapters/](adapters/README.md) | MQTT / ESPHome / Modbus — Sensor-Ingest, Aktor-Steuerung |
| [ha/](ha/README.md) | Home Assistant: Helpers, Templates, Automationen, Dashboards |
| [sim/](sim/README.md) | Simulation (CSV-Feed) und Replay historischer EnergyStates |
| [explain/](explain/README.md) | Entscheidungscodes → menschenlesbare Textbausteine |
| [ops/](ops/README.md) | Config (rules.yaml, feature_flags.yaml), Health, Metriken |
| [data/](data/README.md) | Persistenz: DecisionEvents, EnergyState-Snapshots, KPIs, Export |
| [ui/](ui/README.md) | Optionale REST-API (State / Decision / Override) für eigene UI |

---

## Datenfluss

```
adapters/ ──────────────► core/energy_context ──► EnergyState (frozen)
  (MQTT, ESPHome, Modbus)                               │
                                          block_scheduler (10-min Tick)
                                                         │
                                                    rule_engine
                                                    ├── R1: Profitabilität
                                                    ├── R2: Autarkie
                                                    ├── R3: Safety  ← höchste Priorität
                                                    ├── R4: Forecast
                                                    └── R5: Stabilität / Deadband
                                                         │
                                                    DecisionEvent
                                          ┌──────────────┼──────────────┐
                                       adapters/       data/         explain/
                                    (Relay/Switch)  (Logging)   (Textbausteine)
                                                         │
                                                   ha/ oder ui/
                                                   (Darstellung)
```

---

## Dependency-Richtung

```
adapters → core     Rohdaten werden zu EnergyState normalisiert
ops      → core     Config liefert Schwellen (rules.yaml)
core     → data     DecisionEvents und States werden gespeichert
core     → explain  Decision-Codes werden zu Texten übersetzt
sim      → core     Test-States werden injiziert (kein Live-I/O)
ha / ui  → alle     Visualisierung und Bedienung (nur lesen + Override)
```

Kernregel: **`core/` hat keine Imports aus `adapters/`, `ha/`, `ui/` oder `sim/`.**
Der Core kennt nur seine eigenen Typen und die Config aus `ops/`.

---

## Wo anfangen?

1. **Typen zuerst:** [core/models.py](core/README.md) — `EnergyState`, `Decision`, `DecisionEvent` sind die Basis für alle Module.
2. **Safety zuerst:** [core/rules/r3_safety.py](core/README.md) — R3 ist non-negotiable und muss zuerst stehen.
3. **Dann Adapters:** [adapters/telemetry_ingest.py](adapters/README.md) — damit Messwerte reinkommen.
4. **Dann Simulation:** [sim/scenarios/](sim/README.md) — erstes Szenario (SH-1) zum Testen ohne Hardware.
5. **Dann HA:** [ha/config/](ha/README.md) — Dashboard und Entscheidungsloop in Home Assistant.
