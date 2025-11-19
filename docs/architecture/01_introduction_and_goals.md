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

![Venn-Diagramm](../media/venn_diagramm.svg)

Die Regelengine (R1–R5) ist das operative Gewissen von BitGridAI: 
- **R1 Startregel** sorgt dafür, dass Mining nur bei ausreichendem PV‑Überschuss und sinnvollem Strompreis startet. 
- **R2 Energie & Autarkie-Schutz** schützt Energiehaushalt und Autarkie, indem der Speicher genügend Reserve für Haushalt behält.
- **R3 Thermo- & Hardware-Schutz** überwacht Thermik und Hardware und bremst oder stoppt die Last bei Übertemperaturen. 
- **R4 Prognose-Start** koppelt Schaltentscheidungen an robuste Kurzfrist‑Prognosen, bevor der nächste Block geplant wird.
- **R5 Stabilität / Anti-Flapping** sichert Stabilität durch Deadband/Anti‑Flapping, damit das System nicht nervös an‑ und ausschaltet.

> The rule engine (R1–R5) is the operational conscience of BitGridAI:
> - **R1 Start Rule** ensures mining only begins when PV surplus is sufficient and the electricity price is reasonable.
> - **R2 Energy & Self-Sufficiency Protection** safeguards the household energy budget and self-sufficiency by keeping enough battery reserve for the home.
> - **R3 Thermal & Hardware Protection monitors** thermals and hardware, throttling or stopping the load if temperatures exceed limits.
> - **R4 Forecast Start links switching decisions** to robust short-term forecasts before the next block is scheduled.
> - **R5 Stability / Anti-Flapping** enforces stability via a deadband/anti-flapping window so the system doesn’t nervously switch on and off.

Das System folgt Bitcoin-nahen Leitmotiven: *Bitcoin ist Zeit* (Blocktakt als Automatisierungsrhythmus), *Proof-of-Work* als klare Energieschnittstelle und flexible Last, die Überschussenergie gezielt in einen durch Arbeit erzeugten Wert konserviert, statt gestrandete PV-Leistung ungenutzt zu lassen. Durch dieses System lassen sich im Privathaushalt PV-Spitzen gezielt abfangen, das Verteilnetz entlasten, Eigenverbrauch und Autarkie erhöhen und netzschädliche Rückspeisespitzen vermeiden. Entscheidungen bleiben lokal, deterministisch und erklärbar (R1–R5), sodass Stabilität, Dezentralisierung und Sicherheit vor globaler Skalierung priorisiert werden.

> The system follows Bitcoin-aligned principles: *Bitcoin is time* (block cadence as the automation rhythm), and *proof-of-work* serves as a clear energy interface and flexible load that conserves surplus energy as work-derived value rather than leaving stranded PV output unused. With this approach, PV peaks in residential homes can be actively absorbed, relieving the distribution grid, increasing self-consumption and autonomy, and avoiding grid-harmful feed-in spikes. Decisions remain local, deterministic, and explainable (R1–R5), thereby prioritizing stability, decentralization, and security over global scaling.

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
  - **R1 Startregel** – Mining läuft nur, wenn genug PV-Überschuss vorhanden ist und der Strompreis stimmt.  
  - **R2 Autarkie-Schutz** – der Speicher bleibt so gefüllt, dass Haushalt/Essentials weiterlaufen können.  
  - **R3 Thermo-Schutz** – zu hohe Geräte- oder Raumtemperaturen bremsen oder stoppen das System automatisch.  
  - **R4 Prognose-Start** – erst wenn die Kurzfrist-Prognose stabil genug aussieht, wird der nächste Block geplant.  
  - **R5 Deadband / Anti-Flapping** – Entscheidungen bleiben für ein Zeitfenster gültig, damit nichts hektisch an/aus springt.  
- vollständig **lokal** läuft (Home Assistant oder als Docker-Container innerhalb von umbrelOS, Rule-Engine, On-device-LLM).  
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

## Zusammenfassung / Summary

BitGridAI definiert einen **lokalen, erklärbaren Energie-MVP**: klare Ziele, Qualitätskriterien und KPIs sichern Transparenz, Sicherheit und Nachhaltigkeit; R1–R5 geben jedem Entscheidungszyklus einen nachvollziehbaren Rahmen.  
Das Kapitel verankert damit, warum BitGridAI existiert, welche Resultate erwartet werden und wie Erfolg messbar bleibt – die Basis für alle folgenden arc42-Abschnitte.

> BitGridAI’s vision is a **local-first, explainable energy automation MVP** with explicit goals, guardrails, and KPIs that keep transparency, safety, and sustainability measurable.  
> This chapter grounds every later decision by spelling out the mission, rule set (R1–R5), and success metrics.

---

*Weiter mit **[02 Rahmenbedingungen / Constraints](./02_constraints.md)**.*
