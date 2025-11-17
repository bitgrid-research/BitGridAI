# 05 – Bausteinsicht / Building Block View

> **Kurzüberblick:**
> 
> Sauber getrennte **Bausteine**: `core/`, `modules/`, `ui/`, `data/`, `docs/`.  
> **EnergyState (SSoT)**, **MQTT/REST**-Adapter, **Explainability-UI**, **append-only Logs & KPIs**.  
> Ziel: **erweiterbar**, **testbar**, **nachvollziehbar** – ohne Cloud.

> **TL;DR (EN):**
> 
> Clear **building blocks**: `core/`, `modules/`, `ui/`, `data/`, `docs/`.  
> **EnergyState (SSoT)**, **MQTT/REST** adapters, **explainability UI**, **append-only logs & KPIs**.  
> Goal: **extensible**, **testable**, **traceable** — no cloud.

---

## Überblick / Overview

BitGridAI ist in klar abgegrenzte, lose gekoppelte Bausteine gegliedert.
Jedes Modul erfüllt eine spezifische Aufgabe innerhalb des Gesamtsystems
und trägt durch seine Schnittstellen und Logs zur **Erklärbarkeit und Nachvollziehbarkeit** bei.

> BitGridAI is divided into clearly separated, loosely coupled building blocks.
> Each module fulfills a specific role within the overall system and contributes to **explainability and traceability** through its interfaces and logs.

---

## Hauptbausteine / Core Building Blocks

| Modul / Ordner | Verantwortung                        | Beschreibung                                                       |
| -------------- | ------------------------------------ | ------------------------------------------------------------------ |
| `core/`        | Energiefluss- und Entscheidungslogik | Verwaltung von Zuständen, Regeln und Prioritäten                   |
| `modules/`     | Integrationsadapter                  | Anbindung externer Systeme (z. B. Home Assistant, Inverter, Miner) |
| `ui/`          | Lokale Erklärschnittstelle           | Darstellung von Energiezuständen, Entscheidungen und Begründungen  |
| `data/`        | Logging & Simulation                 | Speicherung von Ereignissen, Messdaten und Evaluationsergebnissen  |
| `docs/`        | Architektur & Forschung              | System- und Forschungsdokumentation (arc42, HCI, Evaluation)       |

### Bitcoin-Leitplanken in den Bausteinen

| Komponente                 | Beitrag zu *Bitcoin ist Zeit / Hodl / PoW*                                                                 |
| -------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `core/block_scheduler`     | Erzwingt 10-Minuten-Blockfenster, vergibt `valid_until`-Deadbands und synchronisiert Explainability-Logs. |
| `modules/miner_controller` | Liefert Proof-of-Work-Telemetrie (Hashrate, J/TH, Temperatur) und koppelt Safety-Signale (R2/R3).         |
| `core/hodl_policy`         | Bewertet Energiepfade (*Export*, *Heat*, *Hodl*) und schreibt Energy-to-Value-Korrelationen in `data/`.   |
| `ui/research_panels`       | Visualisiert Blockzeit, Energy→Sats-Effizienz und Trilemma-Trade-offs für Forschung & Betrieb.            |
| `data/energy_to_value`     | Append-only Nachweis gehodlter kWh/Sats; liefert Input für KPIs und Risiko-Reviews.                       |

> | Component                  | Contribution to *Bitcoin is Time / Hodl / PoW*                                                             |
> | -------------------------- | ---------------------------------------------------------------------------------------------------------- |
> | `core/block_scheduler`     | Enforces 10-minute windows, assigns `valid_until` deadbands, syncs explainability logs by block time.      |
> | `modules/miner_controller` | Streams proof-of-work telemetry (hashrate, J/TH, temperature) and wires in safety signals (R2/R3).         |
> | `core/hodl_policy`         | Evaluates energy paths (*export*, *heat*, *hodl*) and writes energy-to-value correlations into `data/`.    |
> | `ui/research_panels`       | Displays block time, energy→sats efficiency, and trilemma trade-offs for research & operations.            |
> | `data/energy_to_value`     | Append-only record of hodled kWh/sats; feeds KPIs and risk reviews.                                        |

> | Module / Folder | Responsibility                 | Description                                                       |
> | --------------- | ------------------------------ | ----------------------------------------------------------------- |
> | `core/`         | Energy flow and decision logic | Manages states, rules, and priorities                             |
> | `modules/`      | Integration adapters           | Connects external systems (e.g., Home Assistant, inverter, miner) |
> | `ui/`           | Local explanation interface    | Displays energy states, decisions, and rationales                 |
> | `data/`         | Logging & simulation           | Stores events, measurements, and evaluation data                  |
> | `docs/`         | Architecture & research        | System and research documentation (arc42, HCI, evaluation)        |

---

## Kommunikationsschnittstellen / Interfaces

* **MQTT** – Austausch von Energie- und Statusdaten
* **REST API** – Zugriff auf Kontroll- und Visualisierungsfunktionen
* **Eventbus (lokal)** – interne Kommunikation zwischen Modulen und Kernlogik
* **Dateibasierte Logs** – Persistente Speicherung von Entscheidungen und Zuständen

> - **MQTT** – exchange of energy and state data
> - **REST API** – access to control and visualization endpoints
> - **Local Event Bus** – internal communication between modules and the core logic
> - **File-based Logs** – persistent storage of decisions and states

### Adapter- & Payload-Katalog

| Integration | Transport | Topic/Endpoint | Payload-Ausschnitt |
| --- | --- | --- | --- |
| PV/Inverter Adapter | MQTT (`sensor/pv_power`, `sensor/pv_voltage`) | `{"p_pv_kw": 3.2, "u_dc_v": 425}` | Werte werden in SI-Einheiten publiziert, `retain=true` |
| Smart-Meter Adapter | MQTT (`meter/grid`) | `{"p_import_kw": 0.8, "p_export_kw": 0.0, "phase": {"l1":0.3,"l2":0.3,"l3":0.2}}` | 1 Hz Updates, Clock synchronisiert über NTP |
| Speicher Adapter | REST `GET /storage/state` + MQTT Kommandos | Response `{"soc_pct":54,"p_charge_kw":0.5,"p_discharge_kw":0}` | Adapter schreibt nur bei lokalem Token |
| Miner Controller | REST `POST /miner/cmd` + MQTT `miner/state` | Command `{"action":"set_power","value_kw":2.0}`; State `{"hashrate_ths":92,"t_miner_c":72}` | Alle Kommandos haben `command_id` zur Korrelation |
| Explainability UI | WebSocket `ws://ui/events` | Stream `{"type":"decision","payload": DecisionEvent}` | Direktes Mapping auf Datenmodell |
| Research Exporter | REST `POST /research/export` | Request `{"scope":["timeline","kpi"],"since_block":812345}` | Antwort enthält signiertes ZIP (`hash_sha256`) |

#### REST-Beispiele

`GET /state`  
```json
{
  "ts": "2025-01-17T10:20:00Z",
  "block_id": 812345,
  "p_pv_kw": 4.1,
  "p_load_kw": 2.3,
  "surplus_kw": 1.8,
  "soc_pct": 58,
  "t_miner_c": 71,
  "price_ct_kwh": 17.2
}
```

`POST /override`
```json
{
  "action": "stop",
  "ttl_blocks": 2,
  "note": "PV forecast drop due to clouds"
}
```

Antwort: `{"accepted": true, "valid_until_block": 812347, "command_id": "ovr-2025-01-17T10:20:05Z"}`.

---

## Interne Struktur / Internal Structure

Die Module interagieren über asynchrone Schnittstellen.
Das System ist so konzipiert, dass es **erweiterbar, testbar und nachvollziehbar** bleibt,
auch wenn neue Energiequellen, Verbraucher oder Forschungsadapter hinzugefügt werden.

> Modules interact through asynchronous interfaces.
> The system is designed to remain **extensible, testable, and transparent**, even as new energy sources, loads, or research adapters are added.

---

## Strukturskizze / Structural Overview

```
[ PV / Speicher / Sensoren ]
            ↓
        [ modules/ ]
            ↓
        [ core/ ]
      ↙          ↘
  [ data/ ]    [ ui/ ]
        ↓
     [ docs/ ]
```

> ```
> [ PV / Storage / Sensors ]
>           ↓
>       [ modules/ ]
>           ↓
>       [ core/ ]
>     ↙          ↘
> [ data/ ]    [ ui/ ]
>       ↓
>     [ docs/ ]
> ```

---

## Qualitätsaspekte / Quality Aspects

| Aspekt                 | Beschreibung                                                              |
| ---------------------- | ------------------------------------------------------------------------- |
| **Modularität**        | Ermöglicht isolierte Weiterentwicklung und Tests einzelner Komponenten    |
| **Erklärbarkeit**      | Jede Systementscheidung wird im Log und UI begründet                      |
| **Reproduzierbarkeit** | Alle Aktionen sind zeitlich und datenbasiert rekonstruierbar              |
| **Erweiterbarkeit**    | Neue Energiequellen oder Verbraucher können als Module ergänzt werden     |
| **Nachhaltigkeit**     | Komponenten arbeiten ressourcenschonend und lokal ohne Cloud-Abhängigkeit |

> | Aspect              | Description                                                       |
> | ------------------- | ----------------------------------------------------------------- |
> | **Modularity**      | Enables isolated development and testing of individual components |
> | **Explainability**  | Every decision is logged and explained through the UI             |
> | **Reproducibility** | All actions are time- and data-traceable                          |
> | **Extensibility**   | New energy sources or loads can be added as modules               |
> | **Sustainability**  | Components run locally and efficiently without cloud dependencies |

---

## Zusammenfassung / Summary

Die Bausteinsicht zeigt BitGridAI als **offenes, lokales System**,
indem Energieverwaltung, Datenverarbeitung und Nutzerinteraktion klar getrennt und nachvollziehbar bleiben.
Jede Komponente trägt zur erklärbaren Gesamtlogik bei und unterstützt
eine nachhaltige, vertrauenswürdige und reproduzierbare Energieautomatisierung.

> The building block view presents BitGridAI as an **open, local system**
> where energy control, data processing, and user interaction remain clearly separated and transparent.
> Each component contributes to the explainable overall logic and supports
> sustainable, trustworthy, and reproducible energy automation.

*Weiter mit **[06 Laufzeitsicht / Runtime View](./06_runtime_view.md)**.*
