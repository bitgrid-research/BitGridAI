# 013 – Stakeholder

> **Kurzüberblick:**  
> Kern-Stakeholder: Prosumer/Nutzende, BitGrid Core + Explain-Agent, externe Systeme (HA, Inverter, Meter, Miner) sowie Forschung/Entwicklung.

> **TL;DR (EN):**  
> Stakeholders are users/prosumers, BitGrid core + explain agent, external systems, and researchers/developers.

---

## Akteure / Actors

| Rolle | Erwartung |
| --- | --- |
| **Nutzer / Prosumer** | Transparente Energieentscheidungen sehen, Overrides setzen, Sicherheit spüren. |
| **BitGrid Core + Explain-Agent** | Lokale Entscheidungslogik (R1–R5), BlockScheduler, Logging, Explainability & On-Device-LLM. |
| **Externe Systeme** | Home Assistant, Inverter, Smart Meter/Sensorik, Speicher, Mining-Controller – liefern Daten oder erhalten Kommandos. |
| **Forschende / Entwickler** | Analysieren Verhalten, evaluieren Erklärbarkeit, entwickeln/integrieren Module, bauen Replays/KPIs. |

> | Role | Expectation |
> | --- | --- |
> | **User / Prosumer** | See transparent decisions, set overrides, feel safe. |
> | **BitGrid Core + Explain-Agent** | Local rule engine (R1–R5), block scheduler, logging, explainability on-device. |
> | **External Systems** | HA, inverter, meter/sensors, storage, miner controller – provide data or receive commands. |
> | **Researchers / Developers** | Analyse behaviour, evaluate explainability, build modules, run replays/KPIs. |

---

## Personas (HCI-Fokus)

- **P1 Prosumer:** will PV-Überschuss nutzen, Klarheit & Overrides; braucht Safety-Hinweise.  
- **P2 Researcher:** braucht Explainability-Daten, Timeline-Export, Opt-in-Toggle.  
- **P3 Developer:** testet Module/Policies, nutzt Replay & Debug-Ansicht.  
- **P4 Community Member:** vergleicht KPIs und Best Practices lokal.

> Derived from HCI perspective: transparency, control, research opt-in, and local evidence matter to all roles.
