# 032 – Technischer Kontext / Technical Context

TODO: Die Sicht unter der Haube. Mit welchen konkreten APIs, Protokollen, Datenbanken oder Hardware-Komponenten kommuniziert BitGridAI auf technischer Ebene?


> **Kurzüberblick:**  
> Lokale Kopplung von PV, Speicher, Smart Meter, Miner – orchestriert durch **EnergyState (SSoT)**, **BlockScheduler (10 Min)** und **Rule Engine R1–R5**. Kommunikation über **MQTT/REST/WS**, alles im **geschlossenen LAN**.

> **TL;DR (EN):**  
> Local coupling of PV/storage/meter/miner via **EnergyState**, **10-min block scheduler**, **R1–R5**; MQTT/REST/WS inside a closed LAN.

---

## Externe Systeme / External Systems

| System | Schnittstelle | Zweck |
| --- | --- | --- |
| **Home Assistant** | MQTT / REST | State/Command-Austausch, UI-Einbindung. |
| **PV-Wechselrichter** | Modbus/TCP / API | Erzeugungs-, Spannungs- und Statusdaten. |
| **Smart Meter / Sensorik** | MQTT / SML / API | Import/Export, Phasenleistung, Momentanwerte. |
| **Energiespeicher** | API / MQTT | SoC, Lade-/Entladeleistung, Prioritäten. |
| **Mining-Controller** | LAN / API | Leistungsstufen, Start/Stop, Temperatur-/Lüfterdaten. |
| **Preis/Forecast (optional)** | Datei / lokaler Dienst | Tarife, PV-/Lastprognosen für R1/R4 (lokal verarbeitet). |
| **Erklär-UI** | WebSocket / REST | Visualisierung von Energieflüssen & Entscheidungsgründen. |
| **Research/Replay Node** | Datei / CLI | Auslesen von Logs, KPI-Berechnung, Was-wäre-wenn-Replay. |

> HA, inverter, meter, storage, miner controller, optional price/forecast svc, explanation UI, research node.

---

## Grenzen & Flüsse / Boundaries & Flows

- **Inside BitGridAI:** Decision & Rule Engine (R1–R5), BlockScheduler, EnergyState, Explain-Agent, KPI/Logging, lokale Adapter.  
- **Outside:** Physische Hardware (PV/Speicher/Miner), externe UIs, Home Assistant Core, optionale lokale Forecast-Dienste.

**Kommunikationsflüsse:**  
1) Sensoren → **EnergyState** (SSoT) → UI/Logs/Research.  
2) Regeln → **DecisionEvent** + Erklärung → Actuation → Miner/Loads.  
3) Overrides/Research-Toggle → Rule Engine → UI Feedback.

---

## Domain-Events (Auszug)

- `EnergyStateChangedEvent`, `DecisionEvent`, `DeadbandActivatedEvent`, `ResearchToggleChanged`, `ExplainSessionCreated`.

> Domain events keep integrations and research aligned with EnergyState and decisions.
