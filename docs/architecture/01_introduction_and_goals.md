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
- **Netzbezug**: >= X% Reduktion während der Versuchsphase.  
- **Flapping** (Start/Stop-Wechsel): >= Y% Reduktion dank Deadband.  
- **Erklärungs-Abdeckung**: >= Z% (alle Decisions liefern Reason/Trigger/Parameter).  
- **Vertrauens-Score**: >= T/5 (Likert) in Nutzerstudien.  
- **Thermal-Safety-Events**: 0 ungeplante Übertemperaturen.  
- **Energy-to-Sats-Effizienz**: >= E sats/kWh bei aktivem Mining/Hodl.  
- **Hodl/Export-Traceability**: 100% der Blockfenster loggen `preferred_path` inkl. Begründung.  
- **PoW-Sicherheitsverletzungen**: 0 ungeklärte Hashrate-/Effizienzabweichungen (durch R2/R3 abgefangen).

> - **Grid import** reduced by >= X% during trials.  
> - **Flapping** reduced by >= Y% via deadband.  
> - **Explanation coverage** >= Z%.  
> - **Trust score** >= T/5.  
> - **Thermal safety**: 0 unexpected over-temperature events.  
> - **Energy-to-sats efficiency** >= E sats/kWh whenever mining/hodl is active.  
> - **Hodl/export traceability**: 100% of block windows log `preferred_path` plus rationale.  
> - **PoW safety violations**: 0 unexplained hashrate/efficiency deviations (caught by R2/R3).

---

