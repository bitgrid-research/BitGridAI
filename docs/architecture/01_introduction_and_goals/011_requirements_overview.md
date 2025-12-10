# 011 – Requirements Overview / Anforderungen

TODO: Kurzbeschreibung: Was genau bauen wir hier? Ein Überblick über die wesentlichen Features und Use-Cases.

> **Kurzüberblick:**  
> BitGridAI ist **local-first**, erklärbar (R1–R5, 10-Min-Blocktakt), priorisiert **Sicherheit, Autarkie und Transparenz** und muss komplett ohne Cloud laufen.

> **TL;DR (EN):**  
> Local-first, explainable control with **R1–R5** on a **10-minute cadence**, safety/autonomy first, no cloud.

---

## Zweck & Rahmen / Purpose & Scope

BitGridAI steuert PV-Überschuss **lokal** in flexible Lasten (v. a. Mining) und erklärt jede Entscheidung.  
Alle Kernfunktionen (Messung, Regeln, Explainability, Logging, Research) laufen **on-prem** und sind reproduzierbar.

> Local control of PV surplus into flexible loads with **full explanations**, entirely on-prem and reproducible.

---

## Kernanforderungen / Core Requirements

- **R1–R5 deterministisch**: Start, Autarkie-Schutz, Thermo-Schutz, Prognose-Start, Deadband/Anti-Flapping.  
- **Block-Scheduler**: Entscheidungen an den 10-Minuten-Block gebunden; Deadbands vergeben `valid_until`.  
- **EnergyState (SSoT)**: eine wahrheitsführende Quelle für Messwerte, Prognosen, Preise, SoC, Temperaturen.  
- **Explainability by Design**: Jede Aktion liefert `reason/trigger/params`, Timeline + Next-Block-Preview.  
- **Safety first**: Stop → Safe bei SoC- oder Temperaturverletzung; Hysterese für Resume.  
- **Local-first / No Cloud**: Keine externen Abhängigkeiten; Offline-Fähigkeit ist Pflicht.  
- **Auditierbares Logging**: Append-only (SQLite/Parquet), versionierte YAML-Configs, Research-Toggle (Opt-in).

> Deterministic rules, 10-min cadence, single source of truth, explainability, safety-first, local-only, auditable logs.

---

## MVP-Scope

- **PV-Überschusserkennung** + Mining-Steuerung als flexible Last.  
- **Explainability-Layer** (UI + on-device Explain-Agent) mit Timeline, Preview, Overrides (Block-TTL).  
- **Lokale Adapter**: MQTT/REST/Modbus für PV, Speicher, Smart Meter, Miner.  
- **KPI-Tracking**: Grid-Import↓, Flapping↓, Explanation Coverage, Trust-Score, Thermal Incidents = 0.  
- **Replay & Forschung**: Log-Replay, Was-wäre-wenn-Simulation, Export-Bundles bei aktivem Research-Mode.

> PV surplus control, explainability UI, local adapters, KPI tracking, replay for research.
