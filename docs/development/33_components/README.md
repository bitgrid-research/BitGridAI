# 33 – Komponenten & Module

Hier schauen wir hinter die Kulissen: wie die einzelnen Module aufgebaut sind,
was sie tun – und was sie ausdrücklich **nicht** tun.

Dieses Kapitel ist der Einstieg für alle, die **aktiv am Code arbeiten**.
Die vollständige Architekturperspektive steckt in [Kapitel 5 – Bausteinsicht](../../architecture/05_building_block_view/README.md).

&nbsp;

## Modulübersicht

```
src/
├── core/        ← Entscheidungskern         deterministisch, kein I/O
├── adapters/    ← Protokoll-Anbindungen      liest & schreibt Hardware
├── explain/     ← Erklärungslogik            read-only, kein Aktorzugriff
├── ui/          ← Web-Frontend               konsumiert API, zeigt an
├── data/        ← Persistenz & Reporting     speichert, aggregiert
├── sim/         ← Simulation & Replay        Sandbox, kein Live-Zugriff
├── ops/         ← Betrieb & Querschnitt      Security, Config, Monitoring
└── ha/          ← Home Assistant             YAML, Docker, Peer im LAN
```

&nbsp;

---

## `src/core/` — Entscheidungskern

> **Architektur-Referenz:** [05.2.1 – Whitebox Core](../../architecture/05_building_block_view/052_whitebox/0521_core_whitebox/README.md)

Das Herzstück. Läuft im **10-Minuten-Takt**, bewertet die Regeln **R1–R5**
und hält den `EnergyState` als Single Source of Truth.

**Enthaltene Bausteine:**

| Baustein | Datei (geplant) | Zweck |
|----------|----------------|-------|
| `Block-Scheduler` | `scheduler.py` | 10-Min-Takt, `valid_until`-Deadbands |
| `Energy Context` | `energy_context.py` | Messwerte + Forecasts → `EnergyState` |
| `Rule Engine` | `rule_engine.py` | R1–R5 bewerten → `Decision`, `DecisionEvent` |
| `Override Handler` | `override_handler.py` | Manuelle Eingriffe mit TTL + Scope |

**Priorität der Regeln:**
```
R1 Safety  >  R2 Autarkie  >  R3 Stabilität  >  R4 Optimierung  >  R5 Sonstiges
```

**Was `core/` darf:**
- `EnergyState` lesen und schreiben
- `DecisionEvent` erzeugen
- Schnittstellen zu `adapters/` und `data/` aufrufen

**Was `core/` nicht darf:**
- Direkte Datenbankzugriffe
- Netzwerkkommunikation
- Imports aus `ui/` oder `explain/`

&nbsp;

---

## `src/adapters/` — Protokoll-Anbindungen

> **Architektur-Referenz:** [05.2.2 – Whitebox Adapters](../../architecture/05_building_block_view/052_whitebox/0522_adapters_whitebox/README.md)

Die Brücke zur Hardware. Spricht **MQTT, Modbus TCP und REST** –
und übersetzt alles in interne Events, die der Core versteht.

**Enthaltene Bausteine:**

| Baustein | Datei (geplant) | Zweck |
|----------|----------------|-------|
| `Telemetry Ingest` | `telemetry_ingest.py` | Gerätedaten lesen, normalisieren |
| `Actuation Writer` | `actuation_writer.py` | Core-Kommandos auf Geräte schreiben |
| `Health Monitor` | `health_monitor.py` | Heartbeats pro Gerät überwachen |
| `Device Profiles` | `config/*.yaml` | Gerätespezifische Skalierung & Limits |

**Einheiten-Regel:** Nach innen ausschließlich SI-Einheiten (W, Wh, °C).
Das Mapping übernehmen die Device Profiles.

**MQTT Topic-Schema:**
```
bitgridai/<location>/<device_type>/<device_id>/<measurement>

Beispiel:
bitgridai/home/inverter/sma1/active_power_w
bitgridai/home/battery/pylontech1/soc_pct
bitgridai/home/miner/antminer1/power_w
```

**Was `adapters/` nicht darf:**
- Direkt in die Datenbank schreiben
- Entscheidungslogik enthalten
- `core/`-Interna importieren

&nbsp;

---

## `src/explain/` & `src/ui/` — Erklärung & Darstellung

> **Architektur-Referenz:** [05.2.3 – Whitebox UI & Explainability](../../architecture/05_building_block_view/052_whitebox/0523_ui_explain_whitebox/README.md)

Das Gesicht des Systems. Zeigt an, erklärt – steuert aber **nichts**.

**Enthaltene Bausteine:**

| Baustein | Ort | Zweck |
|----------|-----|-------|
| `API-Layer` | `ui/api/` | REST/WS: `/state`, `/timeline`, `/override`, `/preview` |
| `Web-UI` | `ui/frontend/` | Live-State, Timeline, Overrides, Opt-in |
| `Explain-Agent` | `explain/` | `DecisionEvent` → menschenlesbare Erklärung |
| `Preview / What-if` | `ui/preview/` | Sandbox-Simulation, kein Geräteschreibzugriff |

**Strikte Grenze:**
`explain/` und `ui/` sind **read-only** gegenüber Geräten.
Overrides laufen über den API-Layer → `core/` → `adapters/`.
Direktzugriff auf Hardware: nicht erlaubt.

&nbsp;

---

## `src/data/` — Persistenz & Reporting

> **Architektur-Referenz:** [05.2.4 – Whitebox Data & Research](../../architecture/05_building_block_view/052_whitebox/0524_data_research_whitebox/README.md)

Das Gedächtnis des Systems. Alles, was entschieden wurde, bleibt nachvollziehbar.

**Enthaltene Bausteine:**

| Baustein | Datei / Pfad | Zweck |
|----------|-------------|-------|
| `Operational DB` | `data/bitgrid.sqlite` | Aktuelle Zustände, TTLs, Konfigurationen |
| `Event / Log Store` | `data/logs/*.parquet` | Append-only Audit-Trail: Events + States |
| `KPI / Reporting` | `data/kpi/` | Aggregierte Kennzahlen (kWh, Verfügbarkeit) |
| `Export / Replay` | `data/exports/` | Signierte Bundles für Forschung (nur Opt-in) |

**Persistenz-Schema:**

| Daten | Format | Ort | Retention |
|-------|--------|-----|-----------|
| Operative Zustände | SQLite | `data/bitgrid.sqlite` | laufend |
| DecisionEvents | Parquet (append-only) | `data/logs/` | rotierend |
| KPIs | Parquet / JSON | `data/kpi/` | langfristig |
| Exporte | ZIP + Manifest + Hash | `data/exports/` | explizit |

**Append-only-Regel:** Log- und Event-Daten werden **nie** überschrieben.
Nur kontrollierte Rotation über Config.

&nbsp;

---

## `src/sim/` — Simulation & Replay

Szenarien durchspielen, ohne echte Hardware zu brauchen.
Wird auch für **Replay-Prüfung vor Updates** eingesetzt (→ [Kapitel 35 – CI/CD](../35_cicd/README.md)).

| Funktion | Beschreibung |
|----------|-------------|
| Szenarien | Vordefinierte Lastprofile und Wetterdaten |
| Replay | Historische Events erneut durch Core laufen lassen |
| Fixtures | Statische Testzustände für Unit-Tests |

`sim/` hat **keinen Zugriff** auf das Live-System.
Es ist eine vollständige Sandbox.

&nbsp;

---

## `src/ops/` — Betrieb & Querschnitt

> **Architektur-Referenz:** [05.2.5 – Whitebox Operations](../../architecture/05_building_block_view/052_whitebox/0525_operations_whitebox/README.md)

Alles, was man erst bemerkt, wenn es fehlt: Security, Konfiguration, Monitoring.

**Enthaltene Bausteine:**

| Baustein | Datei (geplant) | Zweck |
|----------|----------------|-------|
| `Security & Auth` | `ops/auth.py` | Lokale Rollen (Operator / Observer), Policies |
| `Config & Feature Flags` | `ops/config_loader.py` | YAML-Profile laden, validieren, Reload |
| `Observability` | `ops/monitoring.py` | Metriken, Health-Endpunkte, Alerts |

**Konfigurationsformat:** `config/*.yaml`, Schema-validiert, Reload zur Laufzeit ohne Neustart.

&nbsp;

---

## `src/ha/` — Home Assistant

Home Assistant ist ein **Peer im LAN**, kein Kontrollzentrum.

| Datei | Inhalt |
|-------|--------|
| `docker-compose.yml` | HA-Stack lokal starten |
| `config/configuration.yaml` | HA-Hauptkonfiguration |
| `config/ui-lovelace.yaml` | Dashboard-Definition |

HA kommuniziert ausschließlich über **MQTT** (lesen) und **REST** (begrenzte Schreibzugriffe auf `/override`).

&nbsp;

---

## Zusammenspiel auf einen Blick

```
Feldgeräte
    │  MQTT / Modbus / REST
    ▼
adapters/               ← normalisiert, leitet weiter
    │  EnergyState-Update
    ▼
core/                   ← entscheidet (R1–R5, 10-Min-Takt)
  ├──▶ adapters/        ← Kommandos an Geräte
  ├──▶ data/            ← Events + States persistieren
  └──▶ explain/ + ui/   ← State-Feed, DecisionEvents

ops/                    ← begleitet alles (Auth, Config, Monitoring)
sim/                    ← Sandbox, kein Live-Zugriff
ha/                     ← Peer im LAN, liest MQTT
```

&nbsp;

## Wo finde ich mehr?

| Thema | Wo |
|-------|----|
| Vollständige Bausteinsicht (Level 1–3) | [Kapitel 05 – Bausteinsicht](../../architecture/05_building_block_view/README.md) |
| Laufzeitverhalten & Szenarien | [Kapitel 06 – Laufzeitsicht](../../architecture/06_runtime_view/README.md) |
| Schnittstellen & Protokolle | [Kapitel 08 – Konzepte](../../architecture/08_concepts/README.md) |
| Namenskonventionen & Code-Style | [02.3 – Konventionen](../../architecture/02_archtecture_constraints/023_conventions.md) |

---

> **Nächster Schritt:** Module verstanden.
> Jetzt schauen wir, wie wir Qualität sichern: Tests, Qualitätsgates, Teststrategie.
>
> 👉 Weiter zu **[34 – Tests & Qualitätssicherung](../34_testing/README.md)**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
