# 12 – Glossar / Glossary (Auszug)

> **Kurzüberblick:**  
> Gemeinsame Sprache für BitGridAI: zentrale Begriffe (**EnergyState, DecisionEvent, R1–R5, BlockInterval**) und Abkürzungen. Vollständiges Glossar siehe `docs/architecture/99_glossar.md`.

> **TL;DR (EN):**  
> Shared vocabulary for BitGridAI (EnergyState, DecisionEvent, R1–R5, block interval). Full list in `99_glossar.md`.

---

## Fachbegriffe / Technical Terms

| Begriff | Definition |
| --- | --- |
| **EnergyState (SSoT)** | Zentraler, schreibgeschützter Zustand für Messwerte/Forecast/Preis/SoC/Temperatur. |
| **Surplus** | Überschussleistung: `p_pv - p_load - p_charge_req + p_discharge_avail`. |
| **BlockInterval (10 min)** | Zeitscheibe für deterministische Entscheidungen: `block_id = floor(epoch/600)`. |
| **Rule Engine (R1–R5)** | Start, Autarkie-Schutz, Thermo-Schutz, Prognose-Start, Deadband/Anti-Flapping. |
| **DecisionEvent** | Aktion + Reason/Trigger/Params + `valid_until`; treibt UI/Logs/KPIs. |
| **Deadband** | Haltefenster `D` Blöcke zur Flapping-Reduktion. |
| **Explain-Agent** | On-Device-LLM für Microcopy & Was-wäre-wenn; nicht im Regelpfad. |
| **ExplainSession** | Persistenter Datensatz pro Erklärung/Simulation (Prompt-Version, Text DE/EN, Confidence). |
| **Manual Override** | Block-begrenzter Start/Stop/Level mit TTL; Reason `manual_override`. |
| **Research Toggle** | Opt-in/Opt-out für Forschung/Exports/Replay. |
| **Energy-Path Policy** | Wahl von *Export/Heat/Hodl* je Block; protokolliert `energy_path_decision`. |
| **Stop → Safe** | Fail-Safe-Zustand bei Safety-Regeln (R2/R3) oder Fehlern. |

---

## Abkürzungen / Abbreviations

| Kürzel | Bedeutung |
| --- | --- |
| **ADR** | Architecture Decision Record |
| **SSoT** | Single Source of Truth |
| **SoC** | State of Charge |
| **KPI** | Key Performance Indicator |
| **HA** | Home Assistant |
| **HCI / XAI** | Human-Computer Interaction / Explainable AI |
| **LLM / GGML** | Large Language Model / quantisiertes Format |
| **MQTT / REST / WS** | Messaging/HTTP/WebSocket-Protokolle |
| **VLAN/LAN** | (Virtual) Local Area Network |
| **a11y** | Accessibility |

---

## Hinweis

Für detaillierte Definitionen und zweisprachige Tabellen bitte `docs/architecture/99_glossar.md` nutzen.
