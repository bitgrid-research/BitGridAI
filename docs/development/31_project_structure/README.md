# 31 – Projektstruktur

Bevor du anfängst Code zu schreiben, lohnt sich ein kurzer Überblick:
**Wo liegt was – und warum?**

Das Repository folgt einer klaren Trennung zwischen Dokumentation, Quellcode und Konfiguration.
Diese Struktur ist kein Zufall, sondern direkte Konsequenz der Schichtenarchitektur aus [Kapitel 5](../../architecture/05_building_block_view/README.md).

&nbsp;

## Verzeichnisübersicht

```
BitGridAI/
│
├── docs/                        # Gesamte Projektdokumentation
│   ├── architecture/            # arc42 – Kapitel 01–12
│   ├── research/                # Forschung – Kapitel 20–29
│   ├── development/             # Entwicklung – Kapitel 30–37  ← du bist hier
│   └── media/                   # Bilder, Grafiken, Screenshots
│
├── src/                         # Quellcode (je Modul ein README)
│   ├── core/                    # Regel-Engine R1–R5, Block-Scheduler, EnergyState
│   ├── adapters/                # MQTT / ESPHome / Modbus — Sensor-Ingest, Aktor-Steuerung
│   ├── ha/                      # Home Assistant YAML, Automationen, Dashboards
│   ├── sim/                     # Simulation (CSV-Feed) und Replay
│   ├── explain/                 # Entscheidungscodes → Textbausteine
│   ├── ops/                     # Config (rules.yaml, feature_flags.yaml), Health, Metriken
│   ├── data/                    # Persistenz: DecisionEvents, EnergyState-Snapshots, KPIs
│   └── ui/                      # Optionale REST-API (State / Decision / Override)
│
├── tests/                       # Tests – spiegelt src/-Struktur
│   ├── core/
│   │   ├── rules/               # test_r1.py … test_r5.py
│   │   └── fixtures/            # state_*.json für Replay-Tests
│   ├── adapters/
│   ├── sim/
│   └── ...
│
├── data/                        # Laufzeitdaten (SQLite, Parquet) – nicht eingecheckt
├── logs/                        # Laufzeit-Logs – nicht eingecheckt
│
├── .venv/                       # Virtuelle Python-Umgebung – nicht eingecheckt
├── .env                         # Lokale Umgebungsvariablen – nicht eingecheckt
├── .env.example                 # Vorlage für .env – eingecheckt
├── docker-compose.yml           # Stack-Definition (mqtt + core + ui)
├── .gitignore
└── README.md
```

&nbsp;

## Datenfluss auf einen Blick

```
adapters/ ──────────────► core/energy_context ──► EnergyState (frozen)
  (MQTT, ESPHome, Modbus)                               │
                                          block_scheduler (10-min Tick)
                                                         │
                                                    rule_engine
                                                    ├── R1: Profitabilität
                                                    ├── R2: Autarkie
                                                    ├── R3: Safety  ← Priorität
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

&nbsp;

## Module im Detail

### `src/core/` — Entscheidungskern

Das Herzstück. Kein I/O, kein Netzwerk, kein globaler State — nur deterministisches Input-Output.

```
core/
├── models.py              # EnergyState, Decision, DecisionEvent, RuleVote
├── energy_context.py      # Normalizer, State Builder, Completeness Guard
├── block_scheduler.py     # 10-min Takt, block_id, valid_until
├── rule_engine.py         # R1–R5 bewerten, priorisieren, Decision erzeugen
├── override_handler.py    # Manuelle Overrides, Autonomie-Stufen
└── rules/
    ├── r1_profitability.py
    ├── r2_autarky.py
    ├── r3_safety.py        # Höchste Priorität, nie überstimmbar
    ├── r4_forecast.py
    └── r5_stability.py
```

Kernregel: **`core/` importiert nichts aus `adapters/`, `ha/`, `ui/` oder `sim/`.**
Der Core kennt nur seine eigenen Typen und die Config aus `ops/`.

→ Details: [src/core/README.md](../../../src/core/README.md)

&nbsp;

### `src/adapters/` — Protokoll-Anbindungen

Übersetzt externe Signale in Domänenobjekte und Aktor-Kommandos in Protokoll-Nachrichten.

```
adapters/
├── telemetry_ingest.py    # Rohdaten → normalisierte TelemetryFrames
├── actuation_writer.py    # Decision → Relay/Switch-Kommando
├── health_monitor.py      # Verbindungs-Health, Timeout-Detection
├── mqtt_client.py
├── esphome_adapter.py
├── modbus_adapter.py
└── profiles/
    ├── device_profiles.yaml   # Gerätekonfigurationen (Einheiten, Topics, Timeouts)
    └── topic_schema.yaml      # MQTT-Topic-Konvention
```

Alle Werte intern in SI-Einheiten (W, °C, %, s). Einheiten-Konversion passiert im Adapter, nie im Core.

→ Details: [src/adapters/README.md](../../../src/adapters/README.md)

&nbsp;

### `src/ha/` — Home Assistant

Primäre UI und Simulationsumgebung. Bildet R1–R5 als HA-Template-Sensoren ab.

```
ha/
├── procedure.md               # Arbeitsplan + vollständiges Entity-Listing
├── docker-compose.yml         # HA + Mosquitto für lokale Entwicklung
└── config/
    ├── helpers.yaml           # input_number, input_boolean, input_select, ...
    ├── template_sensors.yaml  # binary_sensor.r1_* bis r5_*, sensor.surplus_kw
    ├── automations/
    │   ├── decision_loop.yaml     # 10-min-Takt, R1–R5-Priorität
    │   └── safety_async.yaml      # R3 asynchron (sofort)
    └── dashboards/
        ├── energy_flow.yaml
        ├── decision_card.yaml
        └── control_panel.yaml
```

→ Details: [src/ha/README.md](../../../src/ha/README.md)

&nbsp;

### `src/sim/` — Simulation & Replay

Szenarien durchspielen ohne echte Hardware. Replay-Tests vor jedem Update.

```
sim/
├── runner.py              # CLI: CSV-Feed mit konfigurierbarer Geschwindigkeit
├── replay.py              # Historische EnergyStates re-evaluieren
├── scenarios/
│   ├── sh1_stable_surplus.csv      # Stabiler Überschuss → START + Laufphase
│   ├── sh2_variable_pv.csv         # Wechselhafte PV → NOOP + Ruhezeiten
│   ├── sh3_soc_critical.csv        # SoC kritisch → R2-STOP
│   └── sh4_safety_overtemp.csv     # Übertemperatur → R3-STOP
└── fixtures/
    ├── state_nominal.json
    ├── state_degraded.json
    └── state_safety_triggered.json
```

→ Details: [src/sim/README.md](../../../src/sim/README.md)

&nbsp;

### `src/explain/` — Erklärungslogik

Übersetzt Decision-Codes in strukturierte, konsistente Texte für UI und Logging.

```
explain/
├── explain_agent.py       # DecisionEvent → ExplainResult
├── decision_codes.py      # Alle Codes als Konstanten (stabil über Releases)
├── code_generator.py      # EnergyState + Decision → Code ableiten
└── mappings/
    ├── rule_map.yaml      # Regel → Code-Bedingungen
    └── text_blocks.yaml   # Textbausteine DE + EN mit Template-Interpolation
```

Keine freien Strings im Core. Alle Erklärtexte kommen aus `text_blocks.yaml`.

→ Details: [src/explain/README.md](../../../src/explain/README.md)

&nbsp;

### `src/ops/` — Betrieb & Observability

Config, Health-Checks und Metriken. Keine Entscheidungslogik.

```
ops/
├── health_check.py        # SystemHealth aggregieren + MQTT-Publish
├── config_loader.py       # Laden, Validieren, Hot-Reload (atomar)
├── metrics.py             # KPIs je Block berechnen
├── events.py              # Health- und System-Event-Typen
└── config/
    ├── rules.yaml         # Schwellen R1–R5 (hot-reload, kein Neustart)
    ├── adapters.yaml      # Adapter-Timeouts, Topics
    ├── system.yaml        # Block-Dauer, Logging, Retention
    └── feature_flags.yaml # Preview, Simulation, Research-Export, Auth
```

→ Details: [src/ops/README.md](../../../src/ops/README.md)

&nbsp;

### `src/data/` — Datenhaltung

Persistenz und Auswertung. Append-only für Events und States.

```
data/
├── db.py                  # SQLite (WAL-Mode), Interface austauschbar
├── models.py              # Tabellen-Schema
├── event_store.py         # DecisionEvents schreiben und lesen
├── state_store.py         # EnergyState-Snapshots für Replay
├── kpi.py                 # KPI-Aggregation je Block
└── export.py              # CSV-Export, Anonymisierung, Manifest
```

→ Details: [src/data/README.md](../../../src/data/README.md)

&nbsp;

### `src/ui/` — Web-UI (optional)

REST-API für eigene Visualisierung, falls kein HA-Dashboard genutzt wird.
Drei Endpunkte: `GET /state`, `GET /decision`, `POST /override`.

→ Details: [src/ui/README.md](../../../src/ui/README.md)

&nbsp;

## Schichtregeln — was darf mit wem reden?

Die Schichtenarchitektur ist **bindend** (Konvention `C-Architektur`):

```
      ha / ui / explain
             ↓
           core          ← einzige Entscheidungsinstanz
          ↙    ↘
    adapters   data
          ↘    ↙
            ops
             ↑
            sim          (nur in Tests, nie im Live-Pfad)
```

| Erlaubt | Verboten |
|---------|---------|
| `adapters/` liefert Daten an `core/` | `adapters/` schreibt direkt in DB |
| `core/` gibt Kommandos an `adapters/` | `core/` importiert aus `ui/` oder `ha/` |
| `explain/` liest DecisionEvents | `explain/` steuert Geräte |
| `data/` speichert Events von `core/` | `data/` trifft Regelentscheidungen |
| `sim/` injiziert Test-States in `core/` | `sim/` läuft im Live-Betriebspfad |

&nbsp;

## Namenskonventionen

Alle Details stehen in [02.3 – Konventionen](../../architecture/02_architecture_constraints/023_conventions.md). Die wichtigsten auf einen Blick:

| Was | Konvention | Beispiel |
|-----|-----------|---------|
| **Dateien & Ordner** | `snake_case` | `rule_engine.py`, `telemetry_ingest/` |
| **Klassen** | `PascalCase` | `EnergyState`, `BlockScheduler` |
| **Funktionen & Variablen** | `snake_case` | `calculate_surplus_power()` |
| **Konstanten** | `UPPER_SNAKE_CASE` | `MAX_BATTERY_CHARGE_W` |
| **MQTT Topics** | `bitgrid/<location>/<device>/<signal>` | `bitgrid/home/pv_inverter/power_w` |
| **Decision-Codes** | `ACTION_REGEL_KONTEXT` | `STOP_R3_OVERTEMP`, `NOOP_R5_DEADBAND_ACTIVE` |
| **Code-Sprache** | Englisch | Variablen, Kommentare, Docstrings |
| **Doku-Sprache** | Deutsch | Alle Markdown-Dateien in `docs/` |

&nbsp;

## `tests/` — Teststruktur

Die Teststruktur **spiegelt** `src/` wider:

```
tests/
├── core/
│   ├── rules/
│   │   ├── test_r1_profitability.py
│   │   ├── test_r2_autarky.py
│   │   ├── test_r3_safety.py       # Kritisch — immer zuerst
│   │   ├── test_r4_forecast.py
│   │   └── test_r5_stability.py
│   ├── test_rule_engine.py         # Priorisierung + Conflict Resolver
│   ├── test_block_scheduler.py
│   ├── test_energy_context.py
│   └── fixtures/
│       ├── state_nominal.json
│       ├── state_degraded.json
│       └── state_safety_triggered.json
├── adapters/
│   ├── test_telemetry_ingest.py
│   └── test_actuation_writer.py
├── sim/
│   └── test_scenarios.py           # SH-1 bis SH-4 parametrisiert
└── explain/
    └── test_explain_agent.py
```

Mehr dazu in [34 – Tests & Qualitätssicherung](../34_testing/README.md).

&nbsp;

## Wo anfangen?

1. **Typen zuerst:** `src/core/models.py` — `EnergyState`, `Decision`, `DecisionEvent` sind die Basis für alle Module.
2. **Safety zuerst:** `src/core/rules/r3_safety.py` — R3 ist non-negotiable und muss vor allen anderen Regeln stehen.
3. **Dann Adapters:** `src/adapters/telemetry_ingest.py` — damit Messwerte reinkommen.
4. **Dann Simulation:** `src/sim/scenarios/sh1_stable_surplus.csv` — erstes Szenario ohne Hardware.
5. **Dann HA:** `src/ha/config/` — Dashboard und Entscheidungsloop in Home Assistant.

---

> **Nächster Schritt:** Struktur verstanden.
> Jetzt geht's darum, wie wir mit Git arbeiten und Änderungen koordinieren.
>
> 👉 Weiter zu **[32 – Workflow & Branching](../32_workflow/README.md)**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
