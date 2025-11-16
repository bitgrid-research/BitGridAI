# 09 – Architekturentscheidungen / Architectural Decisions

**Kurzüberblick / TL;DR**
Entscheidungen orientieren sich an **Local‑First**, **Erklärbarkeit**, **Nachhaltigkeit** und **Determinismus**.
Kernelemente: **R1–R5**, **10‑Min‑BlockScheduler**, **EnergyState (SSoT)**, **Deadband**, **DecisionEvents**, **AGPLv3**, **kein Cloud‑Backend**.

> **TL;DR (EN)**
> Decisions follow **local‑first**, **explainability**, **sustainability**, and **determinism**.
> Core: **R1–R5**, **10‑min block scheduler**, **EnergyState (SSoT)**, **deadband**, **DecisionEvents**, **AGPLv3**, **no cloud backend**.

---

## ADR‑Format / Decision Record Format

Alle Architekturentscheidungen folgen dem ADR‑Format (Architecture Decision Record):

1. **Kontext / Context** · 2) **Entscheidung / Decision** · 3) **Begründung / Rationale** · 4) **Alternativen / Alternatives** · 5) **Auswirkungen / Consequences**

> All ADRs follow: 1) **Context** · 2) **Decision** · 3) **Rationale** · 4) **Alternatives** · 5) **Consequences**

---

## ADR‑001 – Lokale Architektur (Local‑First)

**Status:** Accepted
**Kontext:** Datenschutz, Resilienz und Energieeffizienz sind zentral.
**Entscheidung:** BitGridAI läuft vollständig **lokal**, kein Cloud‑Backend.
**Begründung:** Datenhoheit, Energieautonomie, Nachvollziehbarkeit; entspricht OneNote 00 (Ziele/Abgrenzung).
**Alternativen:** Hybrid/Cloud.
**Auswirkungen:** Mehr lokale Betriebsverantwortung, volle Kontrolle.

> **Context:** Privacy, resilience, efficiency. **Decision:** fully on‑prem. **Rationale:** sovereignty, autonomy, traceability. **Consequences:** local ops overhead, full control.

---

## ADR‑002 – MQTT als Kommunikationsbus

**Status:** Accepted
**Kontext:** Lose Kopplung und Erweiterbarkeit der Module/Geräte.
**Entscheidung:** **MQTT** als zentraler Bus (Topics für State/Commands/Events).
**Begründung:** Asynchron, leichtgewichtig, Standard im Home/Edge.
**Alternativen:** REST‑only, proprietäre Protokolle.
**Auswirkungen:** Flexible Integration, klare Contracts.

> **Decision:** MQTT is the central bus; REST remains for queries/control.

---

## ADR‑003 – SQLite + Parquet als Persistenz

**Status:** Accepted
**Kontext:** Auditierbare, einfache Speicherung ohne Netzabhängigkeit.
**Entscheidung:** **SQLite** für Betrieb/Abfragen, **Parquet** für Langzeit‑Logs/Replays.
**Begründung:** Portabel, wartungsarm, reproduzierbar.
**Alternativen:** PostgreSQL, Timeseries‑DBs, Cloud‑Speicher.
**Auswirkungen:** Einfache Backups; begrenzte Skalierung (ausreichend für MVP/Feldstudie).

---

## ADR‑004 – Erklärungsschnittstelle (statt „nur“ Dashboard)

**Status:** Accepted
**Kontext:** HCI‑Fokus (Vertrauen, Transparenz) laut OneNote.
**Entscheidung:** **Explainability‑UI** mit Reasons/Trigger/Params + Timeline + „Next‑Block Preview“.
**Begründung:** Verständnis > reine Visualisierung.
**Alternativen:** Performance‑Dashboards ohne Erklärlayer.
**Auswirkungen:** Höherer semantischer Wert; UI‑Komplexität moderat.

---

## ADR‑005 – Nachhaltigkeit als Steuergröße

**Status:** Accepted
**Kontext:** Energieeinsatz an PV‑Ertrag koppeln (MVP‑Ziel).
**Entscheidung:** **Surplus‑basiertes** Schalten; Mining nur bei Überschuss/Preisgrenzen.
**Begründung:** Effizienz, Autarkie, Forschungsevaluierung.
**Alternativen:** Starre Zeitprofile.
**Auswirkungen:** Verbrauch↓, dynamische Anpassung, klare KPIs.

---

## ADR‑006 – 10‑Minuten BlockScheduler (Block‑Aligned Control)

**Status:** Accepted
**Kontext:** Flapping vermeiden, Erklärbarkeit erhöhen.
**Entscheidung:** Entscheidungen im **10‑Min‑Takt**; `block_id=floor(epoch/600)`.
**Begründung:** Stabilität, einfache Audits/Erklärungen („pro Block“).
**Alternativen:** Sekunden‑Granularität, Event‑Only.
**Auswirkungen:** Leichte Reaktionslatenz; **R4 Pre‑start** mildert.

---

## ADR‑007 – Deterministische Regelengine (R1–R5)

**Status:** Accepted
**Kontext:** Vertrauen & Reproduzierbarkeit.
**Entscheidung:** Kernsteuerung über **R1–R5** (Start, Autarkie, Thermo, Prognose, Deadband); **keine Black‑Box‑ML im Regelpfad**.
**Begründung:** Testbar, erklärbar, replizierbar.
**Alternativen:** Rein ML‑basierte Policy.
**Auswirkungen:** Klarer Prioritäten‑Order: **R3 > R2 > R5 > R1/R4**.

---

## ADR‑008 – EnergyState als Single Source of Truth (SSoT)

**Status:** Accepted
**Kontext:** Konsistenz & Nachvollziehbarkeit across modules.
**Entscheidung:** **Energy Context** ist **einziger Schreiber**; alle anderen lesen **EnergyState**.
**Begründung:** Eine Wahrheit, weniger Race‑Conditions.
**Alternativen:** Mehrere schreibende Komponenten.
**Auswirkungen:** Klare Verantwortlichkeit; Adapter vereinheitlichen Messwerte.

---

## ADR‑009 – Deadband & Hysterese (Anti‑Flapping)

**Status:** Accepted
**Kontext:** Grenzbereichsrauschen bei PV/Last.
**Entscheidung:** **Deadband** hält Zustand **D Blöcke**; nur **R2/R3** dürfen brechen.
**Begründung:** Stabilität, Hardware‑Schutz.
**Alternativen:** Keine Stabilisierung.
**Auswirkungen:** Weniger Start/Stop‑Wechsel; bessere UX.

---

## ADR‑010 – Manual Override (Block‑Scoped)

**Status:** Accepted
**Kontext:** Nutzerautonomie (HCI‑Ziel, OneNote).
**Entscheidung:** `override(action, ttl)` bis **Blockende/TTL**; Reason `manual_override`.
**Begründung:** Kontrolle ohne dauerhafte Policy‑Änderung.
**Alternativen:** Permanente manuelle Modi.
**Auswirkungen:** Sicherheit bleibt Vorrang (**R2/R3** können Override brechen).

---

## ADR‑011 – Lokale Forecast‑Nutzung (R4)

**Status:** Accepted
**Kontext:** Frühzeitiger Start bei stabiler Erwartung.
**Entscheidung:** **Lokaler** Forecast (Datei/Dienst) beeinflusst nur **Pre‑start** (**R4**).
**Begründung:** Bessere Starts, kein Cloudzwang.
**Alternativen:** Externe APIs, Cloud‑Forecasts.
**Auswirkungen:** Prognosefehler werden durch **R2/R3** abgefangen.

---

## ADR‑012 – Datenhaltung & Audit (Append‑Only)

**Status:** Accepted
**Kontext:** Forschung/Audit/Reproducibility.
**Entscheidung:** **Append‑only Logs** (SQLite/Parquet), versionierte **YAML‑Configs**.
**Begründung:** Wiederholbarkeit, einfache Vergleiche.
**Alternativen:** Ephemere/undokumentierte Zustände.
**Auswirkungen:** Speicherplanung nötig; einfache Backups.

---

## ADR‑013 – Lizenz & Offenheit

**Status:** Accepted
**Kontext:** Transparenz & Wiederverwendung.
**Entscheidung:** **AGPLv3** + klare Third‑Party‑Lizenzen.
**Begründung:** Offen, aber copyleft‑kompatibel mit Forschungszielen.
**Alternativen:** MIT/Apache, proprietär.
**Auswirkungen:** Ableitungen müssen offen bleiben, was Forschung fördert.

---

## ADR‑014 – Privacy by Default (No Outbound Telemetry)

**Status:** Accepted
**Kontext:** DSGVO, Nutzervertrauen.
**Entscheidung:** **Keine** ausgehende Telemetrie; lokale Auth; Minimal‑Ports.
**Begründung:** Minimale Angriffsfläche, maximale Hoheit.
**Alternativen:** Opt‑in Cloud‑Telemetry.
**Auswirkungen:** Monitoring/Support lokal zu lösen (UI‑Health, Logs).

---

## ADR‑015 – Safety‑First: Stop → Safe

**Status:** Accepted
**Kontext:** Thermik/SoC‑Grenzen, Feldstudie.
**Entscheidung:** Harte Limits (**R3/R2**) stoppen sofort; Deadband wird ignoriert; Wiederanlauf mit Hysterese.
**Begründung:** Hardware‑Schutz, Vertrauen.
**Alternativen:** Weiche Limits.
**Auswirkungen:** Verfügbarkeit < Sicherheit; klar kommuniziert in UI.

---

## ADR‑016 – Schnittstellen‑Vertrag (Topics & REST)

**Status:** Accepted
**Kontext:** Interoperabilität mit HA/Adaptern.
**Entscheidung:** MQTT‑Topics (`energy/state/#`, `miner/cmd/set`, `explain/events/#`) + REST (`/state`, `/timeline`, `/override`).
**Begründung:** Klare, testbare Contracts.
**Alternativen:** Ad‑hoc Endpunkte.
**Auswirkungen:** Leichte Integration, bessere Tests.

---

## ADR‑017 – KPIs als Projektzielgröße

**Status:** Accepted
**Kontext:** MVP/KPIs (Grid‑Import↓, Flapping↓, Coverage↑, Trust↑, Thermal=0).
**Entscheidung:** KPIs werden im Core geloggt und in Studien ausgewertet.
**Begründung:** Messbare Wirkung statt Behauptung.
**Alternativen:** Informelle Bewertung.
**Auswirkungen:** Klare Erfolgsdefinition, fortlaufendes Tracking.

---

## Zusammenfassung / Summary

Diese Architekturentscheidungen verankern **lokale Autonomie, Transparenz, Nachhaltigkeit und Erklärbarkeit** im Systemdesign. Sie bilden das Rückgrat der technischen und forschungspraktischen Ausrichtung von BitGridAI.

> These ADRs embed **local autonomy, transparency, sustainability, and explainability** into the design. They are the backbone for technical execution and research practice.

*Weiter mit **[10 – Qualitätsszenarien / Quality Scenarios](./10_quality_scenarios.md)**.*
