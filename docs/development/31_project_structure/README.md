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
├── src/                         # Quellcode
│   ├── core/                    # Regelwerk, Scheduler, EnergyState
│   ├── adapters/                # Protokoll-Anbindungen (MQTT, Modbus, REST)
│   ├── explain/                 # Erklärungslogik, Textbausteine
│   ├── ui/                      # Web-UI (optional, falls kein HA-Dashboard)
│   ├── data/                    # Export, Logs, KPI-Reporting
│   ├── sim/                     # Simulation, Replay, Szenarien
│   ├── ops/                     # Health-Check, Config-Reload, Monitoring
│   └── ha/                      # Home Assistant YAML, docker-compose
│
├── tests/                       # Tests (gespiegelte src/-Struktur)
│   ├── core/
│   ├── adapters/
│   └── ...
│
├── config/                      # Laufzeit-Konfiguration (Regeln, Flags, Tokens)
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

## Module im Detail

### `src/core/` — Entscheidungskern

Das Herzstück. Hier läuft alles, was **deterministisch** sein muss:
Rule Engine, Block-Scheduler und EnergyState.

| Modul | Zweck |
|-------|-------|
| Rule Engine | Bewertet Regeln R1–R5, erzeugt `DecisionEvent` |
| Block-Scheduler | Plant Zeitblöcke auf Basis von Prognose und Regeln |
| EnergyState | Aktuelles Systemabbild (PV, Batterie, Verbrauch, Grid) |
| Override-Handler | Verwaltet manuelle Eingriffe mit Timeout |

> Keine direkten Datenbankzugriffe. Kein Netzwerk. Kein I/O.
> `core/` spricht ausschließlich über definierte Schnittstellen.

&nbsp;

### `src/adapters/` — Protokoll-Anbindungen

Alles, was mit der Außenwelt kommuniziert: Geräte lesen, Kommandos schreiben.

| Adapter | Protokoll | Zweck |
|---------|-----------|-------|
| `telemetry_ingest` | MQTT, Modbus TCP, REST | Sensordaten hereinholen |
| `actuation_writer` | MQTT, REST | Kommandos an Geräte senden |
| `health_monitor` | intern | Adapter-Verfügbarkeit überwachen |
| `device_profiles` | YAML/Config | Gerätekonfigurationen |

> Adapter **schreiben nie direkt** in die Datenbank.
> Sie liefern Daten an `core/` und empfangen Kommandos zurück.

&nbsp;

### `src/explain/` — Erklärungslogik

Übersetzt interne Entscheidungen in menschenlesbare Erklärungen.
Mapping: Regeln R1–R5 → Textbausteine → UI-Ausgabe.

&nbsp;

### `src/data/` — Datenhaltung

Persistenz und Auswertung:
- **SQLite** (Hot-Daten, operative Zustände)
- **Parquet** (Cold-Daten, Logs, Zeitreihen – append-only)
- KPI-Reporting, Export für Research-Node

&nbsp;

### `src/sim/` — Simulation & Replay

Szenarien durchspielen, ohne echte Hardware zu brauchen.
Replay-Prüfung vor Updates (siehe [Kapitel 35 – CI/CD](../35_cicd/README.md)).

&nbsp;

### `src/ops/` — Betrieb & Observability

Health-Checks, Config-Reload zur Laufzeit, Logging-Konfiguration.

&nbsp;

### `src/ha/` — Home Assistant

YAML-Konfiguration, Dashboards und `docker-compose.yml` für den HA-Stack.
Home Assistant ist ein **Peer im LAN**, kein Kontrollzentrum.

&nbsp;

### `src/ui/` — Web-UI (optional)

Eigene Visualisierung & Kontrolloberfläche, falls kein HA-Dashboard genutzt wird.

&nbsp;

## Schichtregeln — was darf mit wem reden?

Die Schichtenarchitektur ist **bindend** (Konvention `C-Architektur`):

```
      UI / Explain
           ↓
         Core          ← einzige Entscheidungsinstanz
        ↙    ↘
  Adapters   Data
        ↘    ↙
          Ops
```

| Erlaubt | Verboten |
|---------|---------|
| `adapters/` liefert Daten an `core/` | `adapters/` schreibt direkt in DB |
| `core/` gibt Kommandos an `adapters/` | `core/` importiert aus `ui/` |
| `explain/` liest aus `core/` | `explain/` steuert Geräte |
| `data/` speichert Events von `core/` | `data/` trifft Regelentscheidungen |

&nbsp;

## Namenskonventionen

Alle Details stehen in [02.3 – Konventionen](../../architecture/02_archtecture_constraints/023_conventions.md). Die wichtigsten auf einen Blick:

| Was | Konvention | Beispiel |
|-----|-----------|---------|
| **Dateien & Ordner** | `snake_case` | `rule_engine.py`, `telemetry_ingest/` |
| **Klassen** | `PascalCase` | `EnergyState`, `BlockScheduler` |
| **Funktionen & Variablen** | `snake_case` | `calculate_surplus_power()` |
| **Konstanten** | `UPPER_SNAKE_CASE` | `MAX_BATTERY_CHARGE_W` |
| **MQTT Topics** | `bitgridai/<location>/<type>/<id>/<measure>` | `bitgridai/home/inverter/sma1/active_power_w` |
| **Code-Sprache** | Englisch | Variablen, Kommentare, Docstrings |
| **Doku-Sprache** | Deutsch | Alle Markdown-Dateien in `docs/` |

&nbsp;

## `tests/` — Teststruktur

Die Teststruktur **spiegelt** `src/` wider:

```
tests/
├── core/
│   ├── test_rule_engine.py
│   ├── test_block_scheduler.py
│   └── test_energy_state.py
├── adapters/
│   └── test_telemetry_ingest.py
└── ...
```

Mehr dazu in [34 – Tests & Qualitätssicherung](../34_testing/README.md).

---

> **Nächster Schritt:** Struktur verstanden.
> Jetzt geht's darum, wie wir mit Git arbeiten und Änderungen koordinieren.
>
> 👉 Weiter zu **[32 – Workflow & Branching](../32_workflow/README.md)**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
