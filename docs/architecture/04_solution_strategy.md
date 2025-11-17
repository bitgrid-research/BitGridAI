# 04 – Lösungsstrategie / Solution Strategy

> **Kurzüberblick:**
> 
> Lokale, modulare und erklärbare Architektur: deterministische R1–R5 auf 10‑Min‑Blocktakt, Explainability‑UI + Explain-Agent ("Warum jetzt?"/Was‑wäre‑wenn), MQTT/REST‑Adapter, SQLite/Parquet‑Logging & Replay, Research-Toggle. Keine Cloud, klare Schnittstellen, Nachhaltigkeit als Steuergröße.

> **TL;DR (EN):**
> 
> Modular, local‑first, and explainable architecture: deterministic R1–R5 on a 10‑minute block cadence, explainability UI + on-device explain agent ("Why now?"/what-if), MQTT/REST adapters, SQLite/Parquet logging & replay, research toggle. No cloud, clear contracts, sustainability as a control parameter.

---

## Ansatz / Approach
BitGridAI verfolgt eine **modulare, lokale und erklärbare Systemarchitektur**,  
die Energieoptimierung, Entscheidungsnachvollziehbarkeit und Nutzervertrauen vereint.  
Das System zielt darauf ab, Energieflüsse nicht nur zu steuern, sondern sie **verstehbar zu machen** –  
durch transparente Prozesse, klare Schnittstellen und nachvollziehbare Entscheidungen.

> BitGridAI follows a **modular, local-first, and explainable system architecture**  
> that combines energy optimization, decision transparency, and user trust.  
> The system not only manages energy but seeks to make it *understandable* — through transparency, structure, and clear interfaces.

---

## Architekturprinzipien / Design Principles
1. **Trennung von Verantwortlichkeiten** – Logik, Module und Erklärschnittstelle sind klar abgegrenzt  
2. **Transparenz zuerst** – Jede Entscheidung ist nachvollziehbar und überprüfbar  
3. **Lokal statt Cloud** – Datenverarbeitung erfolgt ausschließlich unter Nutzerkontrolle  
4. **Erklärbarkeit im Echtzeitkontext** – Entscheidungen werden unmittelbar begründet und kommuniziert (Explain-Agent on-device)  
5. **Nachhaltigkeit als Systemparameter** – Energiesteuerung orientiert sich an Verfügbarkeit und Qualität erneuerbarer Ressourcen  
6. **Forschungs- & Replay-Fähigkeit** – Research-Toggle, KPIs und lokale Replays sind first-class.

> 1. **Separation of concerns** – logic, modules, and the explanation interface are clearly decoupled  
> 2. **Transparency first** – every decision is traceable and verifiable  
> 3. **Local over cloud** – all data processing remains under user control  
> 4. **Real-time explainability** – decisions are communicated and justified via an on-device explain agent  
> 5. **Sustainability as a design goal** – control logic adapts to the availability and quality of renewable resources  
> 6. **Research & replay readiness** – research toggle, KPIs, and local replays are first-class.

---

## Technologische Strategie / Technological Strategy

| Ebene | Technologie | Ziel |
|-------|--------------|------|
| **Kernlogik** | Python | Regel- und Entscheidungs-Engine für Energieflüsse |
| **Kommunikation** | MQTT / REST | Asynchrone Kopplung zwischen Modulen und Geräten |
| **Erklärschnittstelle & Explain-Agent** | Lokale UI + On-Device-LLM | Transparente Darstellung, Microcopy, Was-wäre-wenn-Simulationen |
| **Speicherung & Replay** | SQLite / Parquet / JSON | Reproduzierbare Datenpersistenz, KPI-Berechnung, Log-Replay |
| **Research Services** | CLI / Python tooling | KPI-Runner, Opt-in-Export, anonymisierte Reports |

> | Layer | Technology | Purpose |
> |-------|-------------|----------|
> | **Core Logic** | Python | Rule and decision engine for energy flow management |
> | **Communication** | MQTT / REST | Asynchronous coupling between modules and devices |
> | **Explanation Interface & Explain Agent** | Local UI + on-device LLM | Transparent visualization, microcopy, what-if simulations |
> | **Storage & Replay** | SQLite / Parquet / JSON | Reproducible data persistence, KPI computation, log replay |
> | **Research Services** | CLI / Python tooling | KPI runner, opt-in export, anonymized reports |

---

## Architekturdiagramm / Conceptual Flow
PV → Energiespeicher → BitGrid Core + Explain-Agent → Flexibler Verbraucher (z. B. Mining Node) → Lokale Erklär-/Research-Schnittstelle → KPI/Replay


> ```
> PV → Energy Buffer → BitGrid Core + Explain Agent → Flexible Load (e.g., Mining Node) → Local Explanation/Research Interface → KPI/Replay
> ```

---

## Begründung / Rationale
- **Lokale Architektur** stärkt Datenschutz, Vertrauen und Autonomie  
- **Modularität** ermöglicht Wiederverwendung, Erweiterbarkeit und klare Verantwortlichkeiten  
- **Erklärbarkeit** (Explain-Agent + UI) schafft Akzeptanz der Nutzer und unterstützt wissenschaftliche Evaluation  
- **Nachhaltigkeit** wird als Steuergröße integriert, nicht als nachgelagerter Effekt behandelt  
- **Forschungsfähigkeit** (Research-Toggle, Replay) stellt belastbare Studien sicher  

> - **Local-first architecture** reinforces privacy, trust, and user autonomy  
> - **Modularity** ensures reusability, extensibility, and clear responsibilities  
> - **Explainability** (explain agent + UI) increases user acceptance and supports scientific evaluation  
> - **Sustainability** is treated as an integrated control parameter, not a secondary outcome  
> - **Research readiness** (toggle + replay) secures evidence-based results

---

## Zusammenfassung / Summary

Die Lösungsstrategie fasst BitGridAI als **lokales, deterministisches und erklärbares System** zusammen: Module bleiben klar getrennt, Entscheidungen laufen block-synchron über R1–R5, und sämtliche Schnittstellen (UI, Explain-Agent, Research-Services) sind lokal auditierbar.  
Damit bildet das Kapitel den Fahrplan für alle folgenden Sichten – von Bausteinen bis Deployment – und stellt sicher, dass Transparenz, Nachhaltigkeit und Forschungstauglichkeit durchgängig berücksichtigt werden.

> The solution strategy distills BitGridAI into a **local-first, deterministic, explainable architecture**: separated modules, block-aligned decisions (R1–R5), and local contracts for UI, explain agent, and research services.  
> It acts as the blueprint for the remaining arc42 chapters, ensuring transparency, sustainability, and research readiness stay embedded throughout.

* [05 Bausteinsicht / Building Block View](./05_building_block_view.md)
