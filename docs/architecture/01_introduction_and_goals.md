# 01 – Einführung und Ziele / Introduction and Goals

> **Kurzüberblick:**
>
> BitGridAI erforscht lokale, erklärbare Energieautomatisierung ohne Cloud.  
> PV-Überschuss wird als flexible Last (u. a. Bitcoin-Mining) genutzt.  
> Fokus: Transparenz, Vertrauen, Sicherheit und Wiederholbarkeit.

> **TL;DR (EN):**
>
> BitGridAI researches local, explainable energy automation with no cloud.  
> PV surplus is used as a flexible load (incl. Bitcoin mining).  
> Focus: transparency, trust, safety, and reproducibility.

---

## Zweck / Purpose
BitGridAI untersucht, wie lokale Energieautomatisierung **erklärbar, vertrauenswürdig und nutzerzentriert** gestaltet werden kann. Das Projekt verbindet Human-Computer Interaction (HCI), erneuerbare Energien und **transparente, lokal laufende KI** zu einem einheitlichen Systemansatz.

> BitGridAI explores how **local** energy automation can become **explainable, trustworthy, and user-centered**.  
> It combines Human-Computer Interaction (HCI), renewables, and **transparent on-device AI** into one cohesive approach.

Das System folgt dabei Bitcoin-nahen Leitmotiven: *Bitcoin ist Zeit* (Blocktakt als Automatisierungsrhythmus), *Proof-of-Work* als klare Energieschnittstelle und der Option, Überschussenergie bewusst zu **hodln** statt sofort zu verbrauchen. Entscheidungen balancieren das **Blockchain-Trilemma**, indem sie Dezentralisierung und Sicherheit vor globale Skalierung stellen.

> Bitcoin-aligned principles guide the system: *Bitcoin is time* (block cadence drives automation), *proof-of-work* provides a clear energy interface, and surplus energy can deliberately be **hodled** instead of consumed. Decisions balance the blockchain trilemma by prioritizing decentralization and security over global scale.

---

## Ziele / Goals
1. **Erklärbare Automatisierung** (XAI) in Energiesystemen ermöglichen.  
2. **Nutzervertrauen & Kontrolle** durch klare Oberflächen und Begründungen stärken.  
3. **Lokal & transparent** arbeiten – ohne Cloud-Abhängigkeit (Local-First).  
4. **PV-Überschuss** für flexible Berechnungen nutzen (z. B. Bitcoin-Mining).  
5. **Offene Forschung & Zusammenarbeit** fördern (Daten, Tools, Templates).

> 1. Enable **explainable automation** (XAI) in energy systems.  
> 2. Foster **user trust & control** via clear UIs and rationales.  
> 3. Operate **locally and transparently**—no cloud lock-in.  
> 4. Utilize **PV surplus** for flexible computation (e.g., Bitcoin mining).  
> 5. Encourage **open collaboration** (data, tools, templates).

---

## Qualitätsziele / Quality Goals
| Qualität | Beschreibung |
|---|---|
| **Transparenz** | Jede Entscheidung ist nachvollziehbar (Reason, Trigger, Parameter). |
| **Autonomie** | Vollständig lokaler Betrieb; keine externen Abhängigkeiten. |
| **Nachhaltigkeit** | Effiziente Nutzung erneuerbarer Energie & Lastverschiebung. |
| **Vorhersagbarkeit** | Deterministische Regeln, Deadband/Anti-Flapping. |
| **Sicherheit** | Thermo-Schutz und Fail-States (Stop → Safe). |
| **Reproduzierbarkeit** | Offene Daten, modulare Architektur, klare KPIs. |

> | Quality | Description |
> |---|---|
> | **Transparency** | Every decision is explainable (reason, trigger, parameters). |
> | **Autonomy** | Fully local stack; no external dependencies. |
> | **Sustainability** | Efficient use of renewables and load shifting. |
> | **Predictability** | Deterministic rules, deadband/anti-flapping. |
> | **Safety** | Thermal protection and fail states (stop → safe). |
> | **Reproducibility** | Open data, modular architecture, clear KPIs. |

---

## MVP – Definition / MVP – Definition
Ein **lokales, KI-gestütztes System**, das …
- PV-Überschuss erkennt und **Mining als flexible Last** ansteuert.  
- Entscheidungen **erklärt** (Explainability-Layer in der UI).  
- **R1–R5** konsequent anwendet:  
  - **R1 Startregel** (Überschuss + Preis),  
  - **R2 Autarkie-Schutz** (SoC),  
  - **R3 Thermo-Schutz** (Temperatur),  
  - **R4 Prognose-Start** (Forecast-Stabilität),  
  - **R5 Deadband / Anti-Flapping** (zeitbasierte Stabilität).  
- vollständig **lokal** läuft (Home Assistant, Rule-Engine, On-device-LLM).  
- **Block-aligned** denkt (10-Min-Takt) für robuste Schaltentscheidungen.

> A **local, AI-assisted system** that …  
> • detects PV surplus and **drives mining as a flexible load**;  
> • **explains** its decisions (UI explainability layer);  
> • applies **R1–R5** (start, autonomy, thermal, forecast, deadband);  
> • runs **entirely on-prem** (Home Assistant, rule engine, on-device LLM);  
> • uses a **10-minute block rhythm** for stable scheduling.

---

## KPIs / Success Metrics
| KPI | Zielwert | Messmethode/Quelle |
| --- | --- | --- |
| **Netzbezug-Reduktion** | ≥ 25 % weniger Import in Testzeitraum (30 Tage) | Vergleich `grid_import_kwh` gegen Baseline-Log |
| **Flapping-Rate** | ≤ 2 Start/Stop-Wechsel pro Tag (≥ 60 % Reduktion ggü. Baseline) | `DecisionEvent`-Analyse (`start`/`stop`) |
| **Erklärungs-Abdeckung** | ≥ 98 % der Decisions mit `reason/trigger/params` | Timeline-Export (`explain_coverage`) |
| **Vertrauens-Score** | ≥ 4/5 Likert in Prosumer-Studien (n=10) | Research-Panel Survey |
| **Thermal-Safety-Events** | 0 ungeplante Übertemperaturen `t_miner > 85 °C` | Health-Log + Sensorwerte |
| **Energy-to-Sats-Effizienz** | ≥ 45 sats/kWh (rolling 7 Tage) | `energy_to_value`-Dataset |
| **Hodl/Export-Traceability** | 100 % Blockfenster loggen `preferred_path` + Rationale | Append-only Hodl-Log |
| **PoW-Sicherheitsverletzungen** | 0 ungeklärte Hashrate-/Effizienzabweichungen | `miner_state` + KPI-Alerts |

> | KPI | Target | Measurement |
> | --- | --- | --- |
> | **Grid import reduction** | ≥ 25 % less import during a 30-day trial | Compare `grid_import_kwh` vs. baseline |
> | **Flapping rate** | ≤ 2 start/stop switches per day (≥ 60 % drop) | `DecisionEvent` start/stop analysis |
> | **Explanation coverage** | ≥ 98 % of decisions emit `reason/trigger/params` | Timeline export (`explain_coverage`) |
> | **Trust score** | ≥ 4/5 Likert in prosumer study (n=10) | Research panel survey |
> | **Thermal safety events** | 0 unplanned `t_miner > 85 °C` | Health log + sensors |
> | **Energy-to-sats efficiency** | ≥ 45 sats/kWh (rolling 7 days) | `energy_to_value` dataset |
> | **Hodl/export traceability** | 100 % of block windows log `preferred_path` plus rationale | Append-only hodl log |
> | **PoW safety violations** | 0 unexplained hashrate deviations | `miner_state` + KPI alerts |

---

*Weiter mit **[02 Rahmenbedingungen / Constraints](./02_constraints.md)**.*
