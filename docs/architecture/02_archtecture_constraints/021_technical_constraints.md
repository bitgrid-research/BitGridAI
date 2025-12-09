# 021 – Technische Rahmenbedingungen / Technical Constraints

> **Kurzüberblick:**  
> **Local-first**, **Open-Source-Stack**, deterministische **R1–R5**, **10-Min-Blocktakt**, Explainability & Logging als Pflicht, keine Cloud-Abhängigkeiten.

> **TL;DR (EN):**  
> Local-first, open-source, deterministic rules (R1–R5) on a 10-minute cadence; explainability + logging mandatory; no cloud dependencies.

---

| Bereich | Beschreibung |
| --- | --- |
| **Lokale Ausführung** | Alle Verarbeitung auf Nutzerhardware (Pi/NUC/ThinClient); offline-fähig. |
| **Open-Source-Stack** | Python, MQTT, Home Assistant, SQLite/Parquet; keine proprietären Services. |
| **Modularität** | Erweiterbar über lokale Adapter (MQTT/REST/Modbus) ohne Kernlogik zu ändern. |
| **Single Source of Truth** | **EnergyState** als einziger Schreiber für Messwerte, Prognosen, Preise, SoC, Temperaturen. |
| **Deterministische Regelengine** | **R1–R5** ohne Black-Box-ML im Regelpfad; Priorität R3>R2>R5>R1/R4. |
| **Block-Scheduler** | Entscheidungen im **10-Minuten-Takt**; `valid_until`-Deadbands für Stabilität. |
| **Explain-Agent (On-Device LLM)** | Microcopy & What-if lokal; keine Cloud-Abfragen. |
| **Safety & Fail States** | Harte Limits (SoC/Temperatur) → **Stop → Safe**; kein OC/UV am Miner. |
| **Logging & KPIs** | Append-only (SQLite/Parquet/JSON); Research-Toggle steuert Export/Replay. |
| **Security/Privacy** | Keine Telemetrie nach außen; minimale Ports; lokale Auth (z. B. HA-User). |

> Local execution, FOSS stack, modular adapters, EnergyState as SSoT, deterministic R1–R5, 10-min scheduler, on-device explain agent, safety-first, append-only logging, privacy-by-default.
