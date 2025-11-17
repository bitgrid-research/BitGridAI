# 12 – HCI-Perspektive / HCI Perspective

> **Kurzüberblick:**
> 
> HCI ist Kern von BitGridAI: **erklärbar, rücknehmbar, vertrauensbildend**.
> Muster: **Explain → Act → Confirm**, **Warum jetzt?**, **Was-wäre-wenn?**, **Next‑Block Preview**, **Manual Override** (block‑begrenzt), **Timeline & KPIs** — alles **lokal** und **privacy‑by‑default**.

> **TL;DR (EN):**
> 
> HCI is core to BitGridAI: **explainable, reversible, trust‑building**.
> Patterns: **Explain → Act → Confirm**, **Why now?**, **What‑if?**, **Next‑block preview**, **manual override** (block‑scoped), **timeline & KPIs** — all **local** and **privacy‑by‑default**.

---

## Motivation

Die Mensch-Computer-Interaktion (HCI) ist zentral für BitGridAI.
Jede Automatisierung bleibt **verständlich**, **rücknehmbar** und **vertrauenswürdig**; Erklärungen sind Teil der Steuerlogik, nicht ein Add-on.

> HCI is central to BitGridAI.
> Every automation remains **understandable**, **reversible**, and **trustworthy**; explanations are part of the control logic, not an add-on.

---

## Nutzungskontexte & Personas / Usage Contexts & Personas

| Persona | Bedürfnisse | Implikation für UI/HCI |
| --- | --- | --- |
| **P1 Prosumer** | Möchte PV-Überschuss transparent sehen, eingreifen können und Sicherheit spüren. | Schwellen visualisieren, Overrides prominent platzieren, Safety-Hinweise mit Runbooks. |
| **P2 Researcher** | Benötigt Explainability-Daten und Nutzungslogs ohne Cloud. | Timeline-Export, Annotations, Opt-in-Schalter für Forschungsmodus. |
| **P3 Developer** | Testet Module oder Policies, braucht Debug-Ansicht & Replay. | EnergyState-Snapshots, Replay-Buttons, Feature-Flags via UI. |
| **P4 Community Member** | Teilt Best Practices und vergleicht KPIs lokal. | KPI-Widgets, Export anonymisierter Reports, Hinweis auf Datenscope. |

> Personas verknüpfen UI-Entscheidungen mit konkreten Erwartungen und stellen sicher, dass Explainability, Overrides und Privacy jeweils den passenden Schwerpunkt erhalten.

---

## Designziele / Design Goals

* Entscheidungen **verständlich** darstellen (Reason/Trigger/Parameter, Schwellen sichtbar).
* **Manuelle Eingriffe** jederzeit ermöglichen (Overrides mit TTL bis Blockende).
* **Feedback-Loops** schaffen, die Vertrauen fördern (Bestätigung, Undo, Wirkung).
* **Forschung & Evaluation** über lokale, anonymisierte Nutzungsdaten (Opt-in) ermöglichen.
* **Barrierearme Nutzung** sicherstellen (Keyboard-Flows, Kontraste, „Bewegung reduzieren“).

> - Present decisions with **human-readable** reasoning (thresholds visible).
> - Allow **manual overrides** at any time (block-scoped TTL).
> - Create **feedback loops** that foster trust (acknowledge, undo, effects).
> - Support **research** via **local**, **anonymized**, **opt-in** usage data.
> - Keep the UI **accessible** (keyboard, contrast, reduce-motion respect).

---

## Interaktionsprinzipien / Interaction Principles

1. **Explainable by Design** – „**Warum jetzt?**“ inkl. Schwellen/Parameter zu jeder Aktion.
2. **Reversibility** – **Undo** bis Blockende; Deadband erklärt Haltefenster.
3. **Progressive Disclosure** – Kurztext → Details → Rohdaten (**EnergyState** Snapshot).
4. **Predictability** – **Next‑Block Preview** zeigt geplante Aktion & Begründung.
5. **Safety First** – Hinweise zu **R3/R2** priorisieren; **Stop → Safe** klar kommunizieren.
6. **Local‑First & Privacy** – Keine Telemetrie; Forschungsmodus nur Opt‑in.
7. **Consistency** – Einheitliche Texte/Icons/Metriken in der UI.

> 1) **Explainable by design** — “**Why now?**” with thresholds/parameters for each action.
> 2) **Reversibility** — **undo** until end of block; deadband explains holding window.
> 3) **Progressive disclosure** — short text → details → raw data (**EnergyState** snapshot).
> 4) **Predictability** — **next‑block preview** shows planned action & rationale.
> 5) **Safety first** — surface **R3/R2** messages; communicate **stop → safe**.
> 6) **Local‑first & privacy** — no telemetry; research mode is opt‑in.
> 7) **Consistency** — unified copy/icons/metrics in the UI.

---

## UI-Bausteine / UI Building Blocks

| Baustein               | Zweck                                         | Hinweise & Instrumentierung                            |
| ---------------------- | --------------------------------------------- | ------------------------------------------------------- |
| **Decision-Toast**     | Sofortige Erklärung bei Aktion                | 2-Zeiler, Link zu Details/Timeline, Event 	oast_shown |
| **Why-Now? Panel**     | Reason/Trigger/Parameter, Schwellen           | Zeigt R1-R5-Status, Snapshot-Button export_reason     |
| **Next-Block Preview** | Vorschau auf nächsten Block + Confidence      | "gilt bis Block +D", Forecast-Stabilität, Alternativen  |
| **Timeline**           | Verlauf von DecisionEvents & Overrides        | Filter, Annotationen, Export nach JSON/CSV             |
| **Override-Chip**      | Manueller Start/Stop/Level + TTL              | Countdown, Policy-Rücksprung, Logging override_enter  |
| **Health-Banner**      | Störungen (Broker, Drift, Sensor-Stale)       | Severity-Icons, Link zu Runbook, Aggregat für KPIs      |
| **KPI-Widget**         | Trust/Coverage/Flapping-Metriken              | Lokal berechnet, anonymisiert, Export kpi_report      |
| **Research-Toggle**    | Opt-in/out für Forschungsdaten, Privacy-Info  | Zeigt Datenscope, Audit-Log                            |

> | Component              | Purpose                                    | Notes                                         |
> | ---------------------- | ------------------------------------------- | --------------------------------------------- |
> | **Decision toast**     | Immediate explanation on action             | 2-liner; link to details/timeline + event log |
> | **Why-now panel**      | Reason/trigger/parameters, thresholds       | Shows R1-R5 status, allows snapshot export    |
> | **Next-block preview** | Preview of next block incl. confidence      | Highlights forecast stability & alternatives  |
> | **Timeline**           | History of DecisionEvents & overrides       | Filters, annotations, export                  |
> | **Override chip**      | Manual start/stop/level + TTL               | Countdown, reverts to policy, logs enter/exit |
> | **Health banner**      | Broker/drift/sensor issues                  | Runbook link, severity icon                   |
> | **KPI widget**         | Trust/coverage/flapping metrics             | Computed locally, anonymized                  |
> | **Research toggle**    | Opt-in/out for research logging             | Shows scope, audit trail                      |

---

## Mikrotexte / Microcopy (DE → EN)

**Start (R1):**
„**Start**: Überschuss **1.8 kW** ≥ **1.5 kW**, Preis **16 ct** ≤ **18 ct**. **Deadband** bis **+2**.“

> **Start**: Surplus **1.8 kW** ≥ **1.5 kW**, price **16 ct** ≤ **18 ct**. **Deadband** until **+2**.

**Stop (R2/R3):**
„**Stop**: SoC **24 %** ≤ **25 %** (**R2**). Sicherheit geht vor.“

> **Stop**: SoC **24 %** ≤ **25 %** (**R2**). Safety first.

**Hold (R5):**
„**Stabilisierung aktiv** (**R5**): Zustand bleibt bis **Block +1**.“

> **Stabilization active** (**R5**): holding until **block +1**.

**Preview:**
„**Nächster Block**: voraussichtlich **weiterlaufen**; Prognose stabil (**R4**).“

> **Next block**: expected **continue**; forecast stable (**R4**).

---

## Beispiel / Example

*„Mining pausiert – PV‑Leistung unter 1,5 kW.“* Das System erklärt nicht nur **was**, sondern **warum** — inkl. Schwellen und Deadband.

> *“Mining paused – PV input below 1.5 kW.”* The system explains not only **what** but **why** — incl. thresholds and deadband.

---

## Nutzerreisen / User Journeys

**J1 – Warum läuft der Miner jetzt? (R1/R4)**

1. Decision-Toast „Start (R1) – PV > 1.5 kW“.
2. Why-Now-Panel zeigt Reason/Trigger, Schwellen und Forecast-Confidence.
3. Timeline speichert Event + EnergyState Snapshot (Export-Button).
4. Next-Block Preview visualisiert Deadband und Alternativpfade (Hodl/Export).
5. KPI-Widget aktualisiert Explanation Coverage (Hook).

**Erfolg:** Nutzer versteht Reason/Trigger und kann ggf. einen Stop auslösen; Event zählt als „erklärt“.

> **J1 – Why is the miner running now?**
>
> Toast + why-now panel + timeline snapshot + preview + KPI hook = transparency & control.

**J2 – Safety-Stop (R3)**

1. Alarm-Banner „Übertemperatur“ mit Runbook-Link.
2. System führt sofort Stop aus, ignoriert Deadband.
3. Hinweis zeigt Wiederaufnahmebedingung (T_RESUME) + Countdown.
4. Timeline markiert R3 over_temp, KPI-Widget zählt Safety-Hit.

**Erfolg:** Thermal-Incidents = 0; Nutzer erkennt Ursache & nächste Schritte.

> **J2 – Safety stop (R3)**
>
> Banner + forced stop + resume condition + runbook -> zero incidents.

**J3 – Manueller Override**

1. Override-Chip „Start (00:45)“ blendet TTL ein.
2. Countdown läuft, Timeline zeigt manual_override.
3. System protokolliert override_enter/exit (KPI „manual control share“).
4. Automatische Rückkehr zur Policy am Blockende; Next-Block Preview zeigt Normalzustand.

**Erfolg:** Override-Latenz < 300 ms; Ende klar kommuniziert.

> **J3 – Manual override**
>
> Chip + countdown + timeline + rollback = safe temporary control.

**J4 – Was-wäre-wenn? Analyse**

1. Nutzer öffnet Preview-Tab und simuliert geänderte Schwellen (z. B. Surplus 1.2 kW).
2. UI berechnet hypothetische Entscheidung und kennzeichnet sie als „Simulation – nicht aktiv“.
3. Export-Button legt JSON im lokalen 
esearch/-Ordner ab.

**Erfolg:** Prosumer gewinnt Transparenz ohne Policy-Anpassung; Researcher erhält reproduzierbare Artefakte.

> **J4 – What-if analysis**
>
> Preview simulation + export keeps the active policy untouched while producing evidence.

---

## Forschungsfokus / Research Focus

* Vertrauen in erklärbare Systeme (Trust‑Score, Likert).
* Visuelle Erklärmodelle (Energiefluss vs. Entscheidungsbaum).
* Zeitliche Wahrnehmung von Systemreaktionen (Erklärungslatenz, Vorhersagbarkeit).

> - Trust in explainable systems (trust score, Likert).
> - Visual explanation models (energy flow vs. decision tree).
> - Temporal perception of system responses (explanation latency, predictability).

---

## Studienaufbau / Study Design (A–D)

| Phase               | Ziel                      | Methode                      | Artefakte                         |
| ------------------- | ------------------------- | ---------------------------- | --------------------------------- |
| **A – Elicitation** | Mental Models, Begriffe   | Interviews, Card‑Sort        | Glossar, UI‑Mikrotexte            |
| **B – Prototyping** | UI-Flüsse, Erklärbarkeit  | Think-Aloud, Wizard-of-Oz    | Wireframes, Decision-Toast        |
| **C – Feldstudie**  | Reales Nutzungsverhalten  | In-situ Logging (Opt-in)     | Timeline-Logs, KPI-Bericht        |
| **D – Replay Tests**| Reproduzierbarkeit & a11y | Log-Replay, Heuristische Eval| Annotierte Screencasts, Findings  |

> | Phase               | Goal                        | Method                       | Artifacts                        |
> | ------------------- | -------------------------- | ---------------------------- | -------------------------------- |
> | **A – Elicitation** | Mental models, terminology | interviews, card sort        | glossary, UI microcopy           |
> | **B – Prototyping** | UI flows, explainability   | think-aloud, wizard-of-oz    | wireframes, decision toast       |
> | **C – Field Study** | Real usage behaviour       | in-situ logging (opt-in)     | timeline logs, KPI report        |
> | **D – Replay Tests**| Reproducibility & a11y     | log replay, heuristic review  | annotated screen casts, findings |

---

## Messgrößen / Measures

| Kategorie          | Metrik                                 | Ziel      |
| ------------------ | -------------------------------------- | --------- |
| **Explainability** | Coverage = Decisions mit Reason / alle | ≥ **Z %** |
| **Trust**          | Likert‑Mittelwert                      | ≥ **T/5** |
| **Predictability** | Nutzer sagt „Next Block“ korrekt       | ≥ **X %** |
| **Usability**      | SUS‑Score (optional)                   | ≥ **70**  |
| **Flapping**       | Switches/h ggü. Baseline               | ↓ **Y %** |

> | Category           | Metric                                   | Target    |
> | ------------------ | ---------------------------------------- | --------- |
> | **Explainability** | coverage = decisions with reason / total | ≥ **Z %** |
> | **Trust**          | Likert mean                              | ≥ **T/5** |
> | **Predictability** | user predicts “next block” correctly     | ≥ **X %** |
> | **Usability**      | SUS score (optional)                     | ≥ **70**  |
> | **Flapping**       | switches per hour vs. baseline           | ↓ **Y %** |

---

## Accessibility (a11y) – Minimalset / Minimal Set

* Tastaturbedienbarkeit (Fokus-Reihenfolge, sichtbarer Fokus).
* ARIA-Labels für Toasts/Banner/Chips.
* Kontrast ≥ WCAG AA, skalierbare Schrift.
* „Bewegung reduzieren“ respektieren.
* Live-Regionen für Statusmeldungen und Pausier-Option für Auto-Updates.
* Keine reine Farbkommunikation: Icon + Text + Pattern (insb. Health-Banner).

> - Keyboard operability (focus order, visible focus).
> - ARIA labels for toasts/banners/chips.
> - Contrast ≥ WCAG AA, scalable type.
> - Respect “reduce motion”.
> - Live regions + pause auto updates.
> - Never rely on color alone; pair with icon/text/pattern.

---

## Daten & Datenschutz / Data & Privacy

* **Local‑First**: Keine Cloud; Logs & Studydaten bleiben lokal.
* **Pseudonymisierung**: IDs statt PII; Off‑Site‑Export nur manuell.
* **Opt‑in Forschung**: Schalter im UI; klare Infos zu Zweck/Scope.
* **Transparenz**: Nutzer kann alle **DecisionEvents** einsehen/exportieren.

> - **Local‑first**: no cloud; logs & study data remain local.
> - **Pseudonymization**: IDs instead of PII; off‑site exports are manual only.
> - **Opt‑in research**: toggle in the UI; clear purpose/scope info.
> - **Transparency**: users can view/export all **DecisionEvents**.

---

## Zusammenfassung / Summary

HCI macht BitGridAI **erklärbar, vorhersehbar und kontrollierbar**. Klare Muster (Warum jetzt?, Preview, Overrides), konsistente Mikrotexte und lokale Datenhaltung schaffen **Vertrauen** — Basis für Technik **und** Forschung.

> HCI renders BitGridAI **explainable, predictable, and controllable**. Clear patterns (why now?, preview, overrides), consistent microcopy, and local data create **trust** — the basis for technology **and** research.

*Weiter mit **[13 – UI‑Spezifikation / UI Specification](./13_ui_spec.md)**.*
