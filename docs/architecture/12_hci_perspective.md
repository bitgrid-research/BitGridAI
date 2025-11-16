# 12 – HCI-Perspektive / HCI Perspective

> **Kurzüberblick / TL;DR**
> HCI ist Kern von BitGridAI: **erklärbar, rücknehmbar, vertrauensbildend**.
> Muster: **Explain → Act → Confirm**, **Warum jetzt?**, **Was-wäre-wenn?**, **Next‑Block Preview**, **Manual Override** (block‑begrenzt), **Timeline & KPIs** — alles **lokal** und **privacy‑by‑default**.

> **TL;DR (EN)**
> HCI is core to BitGridAI: **explainable, reversible, trust‑building**.
> Patterns: **Explain → Act → Confirm**, **Why now?**, **What‑if?**, **Next‑block preview**, **manual override** (block‑scoped), **timeline & KPIs** — all **local** and **privacy‑by‑default**.

---

## Motivation

Die Mensch‑Computer‑Interaktion (HCI) ist zentral für BitGridAI.
Jede Automatisierung bleibt **verständlich**, **rücknehmbar** und **vertrauenswürdig**; Erklärungen sind Teil der Steuerlogik, nicht ein Add‑on.

> HCI is central to BitGridAI.
> Every automation remains **understandable**, **reversible**, and **trustworthy**; explanations are part of the control logic, not an add‑on.

---

## Designziele / Design Goals

* Entscheidungen **verständlich** darstellen (Reason/Trigger/Parameter, Schwellen sichtbar).
* **Manuelle Eingriffe** jederzeit ermöglichen (Overrides mit TTL bis Blockende).
* **Feedback‑Loops** schaffen, die Vertrauen fördern (Bestätigung, Undo, Wirkung).
* **Forschung** durch **lokale**, **anonymisierte** Nutzungsdaten (Opt‑in) unterstützen.

> - Present decisions with **human‑readable** reasoning (thresholds visible).
> - Allow **manual overrides** at any time (block‑scoped TTL).
> - Create **feedback loops** that foster trust (acknowledge, undo, effects).
> - Support **research** via **local**, **anonymized**, **opt‑in** usage data.

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

## UI‑Bausteine / UI Building Blocks

| Baustein               | Zweck                                   | Hinweise                           |
| ---------------------- | --------------------------------------- | ---------------------------------- |
| **Decision‑Toast**     | Sofortige Erklärung bei Aktion          | 2‑Zeiler; Link zu Details/Timeline |
| **Why‑Now? Panel**     | Reason/Trigger/Parameter, Schwellen     | zeigt R1–R5‑Status (ok/block)      |
| **Next‑Block Preview** | Vorschau auf nächsten Block             | „gilt bis Block +D“ (Deadband)     |
| **Timeline**           | Verlauf von DecisionEvents              | Filter: Regel, Gerät, Zeitraum     |
| **Override‑Chip**      | Manueller Start/Stop/Level + TTL        | Countdown, Rücksprung zur Policy   |
| **Health‑Banner**      | Störungen (Broker, Drift, Sensor‑Stale) | Link zu Runbook/Abhilfe            |
| **KPI‑Widget**         | Trust/Coverage/Flapping‑Metriken        | lokal berechnet, anonymisiert      |

> | Component              | Purpose                                 | Notes                             |
> | ---------------------- | --------------------------------------- | --------------------------------- |
> | **Decision toast**     | Immediate explanation on action         | 2‑liner; link to details/timeline |
> | **Why‑now panel**      | Reason/trigger/parameters, thresholds   | shows R1–R5 status (ok/blocked)   |
> | **Next‑block preview** | Preview of next block                   | “valid until block +D” (deadband) |
> | **Timeline**           | History of DecisionEvents               | filters: rule, device, time range |
> | **Override chip**      | Manual start/stop/level + TTL           | countdown, return to policy       |
> | **Health banner**      | Incidents (broker, drift, sensor‑stale) | link to runbook/remedy            |
> | **KPI widget**         | Trust/coverage/flapping metrics         | computed locally, anonymized      |

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

**J1 – Normaler Start (R1)**

1. Toast „Start (R1) …“, 2) Why‑Now‑Panel mit Schwellen, 3) Timeline‑Eintrag, 4) Preview für nächsten Block.
   **Erfolg:** Explanation‑Latency < 2 s; Nutzer versteht Aktion.

> **J1 – Normal start (R1)**
>
> 1. toast “Start (R1) …”, 2) why‑now panel with thresholds, 3) timeline entry, 4) next‑block preview.
>    **Success:** explanation latency < 2 s; user understands the action.

**J2 – Safety‑Stop (R3)**

1. Alarm‑Banner „Übertemperatur“, 2) Stop, 3) Hinweis auf Wiederaufnahmebedingung (T_RESUME), 4) Link zu Runbook.
   **Erfolg:** Thermal‑Incidents = 0.

> **J2 – Safety stop (R3)**
>
> 1. alarm banner “over temperature”, 2) stop, 3) show resume condition (T_RESUME), 4) link to runbook.
>    **Success:** thermal incidents = 0.

**J3 – Manueller Override**

1. Override‑Chip „Start (00:45)“, 2) Countdown, 3) Timeline „manual_override“, 4) automatische Rückkehr zur Policy.
   **Erfolg:** Override‑Latency < 300 ms; klares Ende am Block.

> **J3 – Manual override**
>
> 1. override chip “Start (00:45)”, 2) countdown, 3) timeline “manual_override”, 4) automatic return to policy.
>    **Success:** override latency < 300 ms; clear end at block boundary.

---

## Forschungsfokus / Research Focus

* Vertrauen in erklärbare Systeme (Trust‑Score, Likert).
* Visuelle Erklärmodelle (Energiefluss vs. Entscheidungsbaum).
* Zeitliche Wahrnehmung von Systemreaktionen (Erklärungslatenz, Vorhersagbarkeit).

> - Trust in explainable systems (trust score, Likert).
> - Visual explanation models (energy flow vs. decision tree).
> - Temporal perception of system responses (explanation latency, predictability).

---

## Studienaufbau / Study Design (A–C)

| Phase               | Ziel                     | Methode                   | Artefakte                  |
| ------------------- | ------------------------ | ------------------------- | -------------------------- |
| **A – Elicitation** | Mental Models, Begriffe  | Interviews, Card‑Sort     | Glossar, UI‑Mikrotexte     |
| **B – Prototyping** | UI‑Flüsse, Erklärbarkeit | Think‑Aloud, Wizard‑of‑Oz | Wireframes, Decision‑Toast |
| **C – Feldstudie**  | Reales Nutzungsverhalten | In‑situ Logging (Opt‑in)  | Timeline‑Logs, KPI‑Bericht |

> | Phase               | Goal                       | Method                    | Artifacts                  |
> | ------------------- | -------------------------- | ------------------------- | -------------------------- |
> | **A – Elicitation** | Mental models, terminology | interviews, card sort     | glossary, UI microcopy     |
> | **B – Prototyping** | UI flows, explainability   | think‑aloud, wizard‑of‑oz | wireframes, decision toast |
> | **C – Field Study** | Real usage behaviour       | in‑situ logging (opt‑in)  | timeline logs, KPI report  |

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

* Tastaturbedienbarkeit (Fokus‑Reihenfolge, sichtbarer Fokus).
* ARIA‑Labels für Toasts/Banner/Chips.
* Kontrast ≥ WCAG AA, skalierbare Schrift.
* „Bewegung reduzieren“ respektieren.

> - Keyboard operability (focus order, visible focus).
> - ARIA labels for toasts/banners/chips.
> - Contrast ≥ WCAG AA, scalable type.
> - Respect “reduce motion”.

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
