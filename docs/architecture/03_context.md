# 03 – Systemkontext / System Context

## Überblick / Overview
BitGridAI agiert als lokales Bindeglied zwischen Energieerzeugung, Verbrauch und nutzerzentrierter Automatisierung.  
Es verbindet physische Energieflüsse mit digitalen Entscheidungsprozessen,  
um **transparente, erklärbare und reversible Steuerung** zu ermöglichen.

> BitGridAI acts as a local interface between energy generation, consumption, and user-centered automation.  
> It connects physical energy flows with digital decision processes, enabling **transparent, explainable, and reversible control**.

---

## Akteure / Actors
| Rolle | Beschreibung |
|-------|---------------|
| **Nutzer:in / Prosumer** | Betreibt PV-Anlage, speichert und nutzt Energie lokal |
| **BitGrid Core** | Lokale Entscheidungslogik, Steuerung und Datenhaltung |
| **Externe Systeme** | Z. B. Home Assistant, Wechselrichter, Messgeräte, Mining-Controller |
| **Forschende / Entwickler:innen** | Analysieren Verhalten, Evaluieren Erklärbarkeit, entwickeln Module weiter |

> | Role | Description |
> |------|-------------|
> | **User / Prosumer** | Operates PV, stores and consumes energy locally |
> | **BitGrid Core** | Local decision logic, control, and data handling |
> | **External Systems** | e.g., Home Assistant, inverters, sensors, mining controllers |
> | **Researchers / Developers** | Analyze behavior, evaluate explainability, develop modules |

---

## Externe Systeme / External Systems

| System | Schnittstelle | Zweck |
|---------|----------------|--------|
| **Home Assistant** | MQTT / REST API | Austausch von Zuständen und Automatisierungen |
| **PV-Wechselrichter** | Modbus / API | Bereitstellung von Leistungs- und Statusdaten |
| **Energiespeicher** | API / MQTT | Ladezustand, Leistung, Prioritäten |
| **Mining Controller** | Lokales Netzwerk / API | Dynamische Steuerung flexibler Lasten |
| **Erklärschnittstelle** | WebSocket / REST | Darstellung von Energieflüssen und Entscheidungsbegründungen |

> | System | Interface | Purpose |
> |---------|-----------|----------|
> | **Home Assistant** | MQTT / REST API | Exchange of states and automations |
> | **PV Inverter** | Modbus / API | Provides power and status data |
> | **Energy Storage** | API / MQTT | Reports charge state, performance, priorities |
> | **Mining Controller** | Local network / API | Dynamically controls flexible loads |
> | **Explanation Interface** | WebSocket / REST | Displays energy flows and decision rationales |

---

## Kontextdiagramm / Context Diagram
[ Nutzer:in ]
↓
[ Lokale Erklärschnittstelle ]
↓
[ BitGrid Core ]
↙ ↘
[ Energiegeräte ] [ Forschung / Evaluation ]


> ```
> [ User / Prosumer ]
>       ↓
> [ Local Explanation Interface ]
>       ↓
>   [ BitGrid Core ]
>    ↙          ↘
> [ Energy Devices ]   [ Research / Evaluation ]
> ```

---

## Systemgrenzen / System Boundaries
- **Innerhalb von BitGridAI**:  
  - Entscheidungslogik  
  - Modulare Adapter (PV, Speicher, Miner)  
  - Logging und Erklärschnittstelle  

- **Außerhalb von BitGridAI**:  
  - Physische Hardware (PV, Speicher, Miner)  
  - Fremdsoftware wie Home Assistant  
  - Forschungstools (z. B. externe Evaluationsframeworks)

> - **Inside BitGridAI:**  
>   - Decision logic  
>   - Modular adapters (PV, storage, miner)  
>   - Logging and explanation interface  
> - **Outside BitGridAI:**  
>   - Physical hardware (PV, storage, miner)  
>   - Third-party software (e.g., Home Assistant)  
>   - Research tools (e.g., evaluation frameworks)

---

## Kommunikationsflüsse / Communication Flows
1. **Energiefluss** → Physikalisch: PV → Speicher → Last  
2. **Datenfluss** → Digital: Sensoren → Core → UI / Logging  
3. **Entscheidungsfluss** → Logisch: Regelbasis → Aktion → Erklärung  

> 1. **Energy flow** → Physical: PV → Storage → Load  
> 2. **Data flow** → Digital: Sensors → Core → UI / Logging  
> 3. **Decision flow** → Logical: Rule base → Action → Explanation  

---

## Kontextzusammenfassung / Context Summary
BitGridAI positioniert sich **zwischen physikalischer Infrastruktur und menschlicher Entscheidungsautonomie**.  
Es übersetzt komplexe Energiedaten in verständliche Handlungsmodelle  
und fördert damit *Vertrauen, Kontrolle und Transparenz* im Energiesystem.

> BitGridAI positions itself **between physical infrastructure and human decision autonomy**.  
> It translates complex energy data into understandable action models,  
> fostering *trust, control, and transparency* within the energy system.
