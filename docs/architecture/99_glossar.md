# 99 – Glossar / Glossary

## Überblick / Overview

Das Glossar enthält zentrale Begriffe, Konzepte und Abkürzungen, die in der BitGridAI‑Architektur verwendet werden.
Es dient dazu, **Konsistenz, Verständlichkeit und Nachvollziehbarkeit** innerhalb der Dokumentation sicherzustellen.

> The glossary provides key terms, concepts, and abbreviations used in the BitGridAI architecture.
> It ensures **consistency, clarity, and traceability** throughout the documentation.

---

## Fachbegriffe / Technical Terms

| Begriff                                     | Definition                                                                                                            |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **BitGridAI**                               | Lokales, erklärbares Energiesystem zur Nutzung von PV‑Überschuss und zur Steuerung flexibler Lasten.                  |
| **EnergyState (SSoT)**                      | Zentraler, schreibgeschützter Zustand („Single Source of Truth“) für alle Leser (Core, UI, Logger).                   |
| **Surplus**                                 | Überschussleistung: `p_pv − p_load − p_charge_req + p_discharge_avail`.                                               |
| **BlockInterval (10 min)**                  | Zeitraster für deterministische Entscheidungen: `block_id = floor(epoch/600)`.                                        |
| **BlockScheduler**                          | Orchestriert Regelbewertung im 10‑Min‑Takt und setzt Deadband‑Fenster.                                                |
| **Deadband**                                | Anti‑Flapping‑Mechanismus: hält den Zustand für `D` Blöcke, außer Safety‑Regeln greifen.                              |
| **Rule Engine (R1–R5)**                     | Deterministische Kernlogik: Start (R1), Autarkie‑Schutz (R2), Thermo‑Schutz (R3), Prognose‑Start (R4), Deadband (R5). |
| **R1 Startregel**                           | Start bei Überschuss + ggf. Preisgrenzen.                                                                             |
| **R2 Autarkie‑Schutz**                      | Stop/Block bei niedrigem SoC zum Schutz der Eigenversorgung.                                                          |
| **R3 Thermo‑Schutz**                        | Sofort‑Stop bei Übertemperatur; Wiederaufnahme mit Hysterese.                                                         |
| **R4 Prognose‑Start**                       | Frühstart bei stabiler lokaler Überschussprognose.                                                                    |
| **R5 Deadband / Anti‑Flapping**             | Stabilisierung zur Vermeidung häufiger Start/Stop‑Wechsel.                                                            |
| **DecisionEvent**                           | Domain‑Event mit Aktion, Grund (Reason), Triggern, Parametern und Gültigkeit.                                         |
| **EnergyStateChangedEvent**                 | Domain‑Event bei Aktualisierung des EnergyState.                                                                      |
| **DeadbandActivatedEvent**                  | Event, das die Aktivierung eines Haltefensters signalisiert.                                                          |
| **Erklärschnittstelle (Explainability UI)** | Lokale UI zur Begründung von Entscheidungen und Anzeige der Timeline.                                                 |
| **Explain-Agent (On-Device LLM)**           | Lokal ausgeführtes Sprachmodell (quantisiert), generiert Microcopy & Was-wäre-wenn-Ausgaben, bleibt read-only zum Regelpfad. |
| **ExplainSession**                          | Persistenter Datensatz pro Erklärung/Simulation (`decision_id`, `prompt_version`, `result_text_de/_en`, `confidence`, `type`, `valid_until`), verlinkt zu DecisionEvents. |
| **Next‑Block Preview**                      | Vorschau der erwarteten Aktion im nächsten Block inkl. Schwellen.                                                     |
| **Manual Override**                         | Temporäre manuelle Steuerung (Start/Stop/Level) bis Blockende/TTL.                                                    |
| **Research Toggle**                         | Opt-in/Opt-out-Schalter für Forschung, steuert Export/Replay und UI-Hinweise.                                         |
| **Research Service**                        | Lokaler Dienst/CLI für `/research/toggle`, `/research/export`, `/replay` inkl. Audit-Logs.                             |
| **ExportBundle**                            | Verschlüsseltes Paket (Timeline, KPIs, ExplainSessions, Hash) für Forschung/Sharing.                                  |
| **Replay Runner**                           | Tool, das Parquet/SQLite-Logs deterministisch abspielt (1x–20x) und KPIs vergleicht.                                  |
| **KPI**                                     | Kennzahlen zur Wirkung (Grid‑Import↓, Flapping↓, Explanation‑Coverage↑, Trust‑Score↑, Thermal‑Incidents=0).           |
| **Grid‑Import**                             | Netzbezug; KPI zur Reduktion durch lokale Optimierung.                                                                |
| **Flapping**                                | Häufige Zustandswechsel Start/Stop; zu minimieren via Deadband.                                                       |
| **Trust‑Score**                             | Nutzervertrauen (z. B. Likert‑Skala) aus Studien/Feedback.                                                            |
| **SoC (State of Charge)**                   | Ladezustand des Speichers (0…1); Schutz via R2.                                                                       |
| **T_MAX / T_RESUME**                        | Temperatur‑Schwellen für Stop/Resume des Miners (R3).                                                                 |
| **MQTT**                                    | Leichtgewichtiges Messaging‑Protokoll für asynchrone Kopplung.                                                        |
| **Modbus (TCP)**                            | Industriestandard‑Protokoll zur Datenabfrage z. B. am Inverter.                                                       |
| **REST / WebSocket**                        | Lokale HTTP‑/WS‑Schnittstellen für State, Timeline, Events.                                                           |
| **SQLite / Parquet**                        | Lokale Speicherung (Online‑DB / Langzeit‑Logs & Replay).                                                              |
| **Mosquitto**                               | Lokaler MQTT‑Broker für Topics wie `energy/state/#` oder `explain/events/#`.                                          |
| **Home Assistant (HA)**                     | Open‑Source‑Plattform für lokale Automatisierung und Geräteintegration.                                               |
| **Mining Node**                             | Flexible Last (z. B. Bitcoin‑Miner), die Überschussenergie nutzt.                                                     |
| **Local‑First**                             | Prinzip: Berechnung und Datenhaltung ausschließlich auf Nutzerhardware.                                               |
| **AGPLv3**                                  | Lizenz, die Transparenz und Copyleft bei Netzbetrieb sicherstellt.                                                    |

> | Term                            | Definition                                                                                                      |
> | ------------------------------- | --------------------------------------------------------------------------------------------------------------- |
> | **BitGridAI**                   | Local, explainable energy system leveraging PV surplus and controlling flexible loads.                          |
> | **EnergyState (SSoT)**          | Central read‑only state (“Single Source of Truth”) for core, UI, and logger.                                    |
> | **Surplus**                     | Excess power: `p_pv − p_load − p_charge_req + p_discharge_avail`.                                               |
> | **BlockInterval (10 min)**      | Time grid for deterministic control: `block_id = floor(epoch/600)`.                                             |
> | **BlockScheduler**              | Orchestrates rule evaluation every 10 min and sets deadband windows.                                            |
> | **Deadband**                    | Anti‑flapping mechanism: holds state for `D` blocks unless safety rules apply.                                  |
> | **Rule Engine (R1–R5)**         | Deterministic core: Start (R1), Self‑supply guard (R2), Thermal guard (R3), Forecast start (R4), Deadband (R5). |
> | **R1 Start rule**               | Start on surplus and optional price constraints.                                                                |
> | **R2 Self‑supply guard**        | Stop/block on low SoC to preserve autonomy.                                                                     |
> | **R3 Thermal guard**            | Immediate stop on over‑temperature; resume with hysteresis.                                                     |
> | **R4 Forecast start**           | Early start when local surplus forecast is stable.                                                              |
> | **R5 Deadband / Anti‑flapping** | Stabilization to avoid frequent toggling.                                                                       |
> | **DecisionEvent**               | Domain event with action, reason, triggers, parameters, validity.                                               |
> | **EnergyStateChangedEvent**     | Event on EnergyState update.                                                                                    |
> | **DeadbandActivatedEvent**      | Event signalling that a holding window is active.                                                               |
> | **Explainability UI**           | Local UI explaining decisions and showing the timeline.                                                         |
> | **Next‑block preview**          | Preview of the expected action next block incl. thresholds.                                                     |
> | **Manual override**             | Temporary manual control (start/stop/level) until block end/TTL.                                                |
> | **KPI**                         | Metrics (grid import↓, flapping↓, explanation coverage↑, trust score↑, thermal incidents=0).                    |
> | **Grid import**                 | Power drawn from the grid; KPI to reduce via local optimization.                                                |
> | **Flapping**                    | Frequent start/stop toggling; minimized through deadband.                                                       |
> | **Trust score**                 | User trust (e.g., Likert scale) from studies/feedback.                                                          |
> | **SoC (State of Charge)**       | Battery state of charge (0…1); guarded via R2.                                                                  |
> | **T_MAX / T_RESUME**            | Temperature thresholds for stop/resume of the miner (R3).                                                       |
> | **MQTT**                        | Lightweight messaging protocol for asynchronous coupling.                                                       |
> | **Modbus (TCP)**                | Industrial protocol to query devices like inverters.                                                            |
> | **REST / WebSocket**            | Local HTTP/WS endpoints for state, timeline, events.                                                            |
> | **SQLite / Parquet**            | Local storage (operational DB / long‑term logs & replay).                                                       |
> | **Mosquitto**                   | Local MQTT broker for topics like `energy/state/#` or `explain/events/#`.                                       |
> | **Home Assistant (HA)**         | Open‑source platform for local automation and device integration.                                               |
> | **Mining node**                 | Flexible load (e.g., Bitcoin miner) consuming surplus energy.                                                   |
> | **Local‑first**                 | Principle: computation and data remain on user‑owned hardware.                                                  |
> | **AGPLv3**                      | License ensuring transparency and copyleft for network use.                                                     |

---

## Abkürzungen / Abbreviations

| Kürzel    | Bedeutung                                               |
| --------- | ------------------------------------------------------- |
| **ADR**   | Architecture Decision Record                            |
| **API**   | Application Programming Interface                       |
| **CLI**   | Command Line Interface                                  |
| **DB**    | Database                                                |
| **UI**    | User Interface                                          |
| **UX**    | User Experience                                         |
| **a11y**  | Accessibility (Barrierefreiheit)                        |
| **CO₂**   | Kohlendioxid, Kenngröße für Energieeffizienz            |
| **SSoT**  | Single Source of Truth (EnergyState)                    |
| **SoC**   | State of Charge (Ladezustand)                           |
| **KPI**   | Key Performance Indicator                               |
| **NTP**   | Network Time Protocol                                   |
| **TLS**   | Transport Layer Security                                |
| **PII**   | Personally Identifiable Information                     |
| **WS**    | WebSocket                                               |
| **LAN**   | Local Area Network                                      |
| **VLAN**  | Virtual LAN                                             |
| **HA**    | Home Assistant                                          |
| **HCI**   | Human‑Computer Interaction                              |
| **XAI**   | Explainable Artificial Intelligence                     |
| **R1–R5** | Regelwerk (Start, Autarkie, Thermo, Prognose, Deadband) |
| **LLM**   | Large Language Model (z. B. Explain-Agent)              |
| **GGML**  | Quantisiertes LLM-Format (für CPU/GPU, on-device)       |
| **CLI**   | Command Line Interface                                  |

> | Abbr.     | Meaning                                                 |
> | --------- | ------------------------------------------------------- |
> | **ADR**   | Architecture Decision Record                            |
> | **API**   | Application Programming Interface                       |
> | **CLI**   | Command Line Interface                                  |
> | **DB**    | Database                                                |
> | **UI**    | User Interface                                          |
> | **UX**    | User Experience                                         |
> | **a11y**  | Accessibility                                           |
> | **CO₂**   | Carbon dioxide, metric for energy efficiency            |
> | **SSoT**  | Single Source of Truth (EnergyState)                    |
> | **SoC**   | State of Charge                                         |
> | **KPI**   | Key Performance Indicator                               |
> | **NTP**   | Network Time Protocol                                   |
> | **TLS**   | Transport Layer Security                                |
> | **PII**   | Personally Identifiable Information                     |
> | **WS**    | WebSocket                                               |
> | **LAN**   | Local Area Network                                      |
> | **VLAN**  | Virtual LAN                                             |
> | **HA**    | Home Assistant                                          |
> | **HCI**   | Human‑Computer Interaction                              |
> | **XAI**   | Explainable Artificial Intelligence                     |
> | **R1–R5** | Rule set (start, autonomy, thermal, forecast, deadband) |
> | **LLM**   | Large Language Model (e.g., Explain-Agent)              |
> | **GGML**  | Quantised LLM format (CPU/GPU friendly)                 |
> | **CLI**   | Command Line Interface                                  |

---

## Zusammenfassung / Summary

Das Glossar schafft eine **gemeinsame Sprache** zwischen Entwicklung, Forschung und Anwendung.
Es stellt sicher, dass technische und konzeptionelle Elemente von BitGridAI konsistent und nachvollziehbar kommuniziert werden.

> The glossary establishes a **shared vocabulary** between development, research, and application.
> It ensures that BitGridAI’s technical and conceptual elements are communicated consistently and transparently.
