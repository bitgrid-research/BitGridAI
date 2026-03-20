src/

  core/           # Regel-Engine (R1–R5), Block-Scheduler, EnergyState, Decision

  adapters/       # MQTT / ESPHome / Modbus — Sensor-Ingest, Aktor-Steuerung

  ha/             # Home-Assistant YAML: Helpers, Templates, Automationen, Dashboards

  sim/            # Simulation (CSV-Feed) und Replay (historische EnergyStates)

  explain/        # Entscheidungscodes → menschenlesbare Textbausteine

  ops/            # Config (rules.yaml, feature_flags.yaml), Health, Metriken

  data/           # Persistenz: DecisionEvents, EnergyState-Snapshots, KPIs, Export

  ui/             # Optionale REST-API (State / Decision / Override) für eigene UI


Datenfluss:

  adapters → core/energy_context → EnergyState
                                       │
                          block_scheduler (10-min Tick)
                                       │
                                  rule_engine (R1–R5)
                                       │
                     ┌─────────────────┼──────────────────┐
                  adapters/         data/              explain/
              (Aktor-Kommando)   (Logging)          (Textbausteine)
                                       │
                                 ha/ oder ui/
                               (Darstellung)

Dependency-Richtung:
  core ← adapters (liefert Daten)
  core → data     (speichert Events)
  core → explain  (erzeugt Codes)
  ops  → core     (liefert Config/Schwellen)
  sim  → core     (injiziert Test-States)
  ha   → alle     (visualisiert, bedient)
