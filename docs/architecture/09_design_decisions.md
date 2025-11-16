# 09 – Architekturentscheidungen / Architectural Decisions

> **Kurzüberblick / TL;DR:**
> Entscheidungen orientieren sich an **Local‑First**, **Erklärbarkeit**, **Nachhaltigkeit** und **Determinismus**.
> Kernelemente: **R1–R5**, **10‑Min‑BlockScheduler**, **EnergyState (SSoT)**, **Deadband**, **DecisionEvents**, **AGPLv3**, **kein Cloud‑Backend**.

> **TL;DR (EN):**
> Decisions follow **local‑first**, **explainability**, **sustainability**, and **determinism**.
> Core: **R1–R5**, **10‑min block scheduler**, **EnergyState (SSoT)**, **deadband**, **DecisionEvents**, **AGPLv3**, **no cloud backend**.

---

## ADR‑Format / Decision Record Format

Alle ADRs enthalten: **Kontext → Entscheidung → Begründung → Alternativen → Auswirkungen**.

> All ADRs include: **Context → Decision → Rationale → Alternatives → Consequences**.

---

## Tabellarische Übersicht (DE) / Tabular Overview (DE)

|     ADR | Titel                                         | Status   | Kontext                                | Entscheidung                                                                                          | Begründung                                 | Alternativen                       | Auswirkungen                                          |
| ------: | --------------------------------------------- | -------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------ | ---------------------------------- | ----------------------------------------------------- |
| **001** | Lokale Architektur (Local‑First)              | Accepted | Datenschutz, Resilienz, Effizienz      | Vollständig **lokal**, kein Cloud‑Backend                                                             | Datenhoheit, Autarkie, Nachvollziehbarkeit | Hybrid/Cloud                       | Mehr lokale Ops, volle Kontrolle                      |
| **002** | MQTT als Kommunikationsbus                    | Accepted | Lose Kopplung/Erweiterbarkeit          | **MQTT** als Bus (State/Commands/Events); REST optional                                               | Asynchron, leichtgewichtig, Standard       | REST‑only, proprietär              | Flexible Integration, klare Contracts                 |
| **003** | Persistenz: SQLite + Parquet                  | Accepted | Audit ohne Netzabhängigkeit            | **SQLite** (Betrieb/Abfrage) + **Parquet** (Langzeit/Replay)                                          | Portabel, wartungsarm, reproduzierbar      | PostgreSQL, Time‑Series‑DBs, Cloud | Einfache Backups, Skalierung begrenzt (ok für MVP)    |
| **004** | Erklärungsschnittstelle statt „nur“ Dashboard | Accepted | HCI‑Fokus Vertrauen/Transparenz        | **Explainability‑UI** (Reasons/Trigger/Params, Timeline, Preview)                                     | Verständnis > reine Visualisierung         | Performance‑Dashboards             | Höherer semantischer Wert, moderate UI‑Komplexität    |
| **005** | Nachhaltigkeit als Steuergröße                | Accepted | PV‑Kopplung, Effizienz                 | **Surplus‑basiertes** Schalten; Preisgrenzen                                                          | Effizienz, Autarkie, Forschung             | Starre Zeitprofile                 | Verbrauch↓, dynamische Anpassung, klare KPIs          |
| **006** | 10‑Minuten BlockScheduler                     | Accepted | Flapping vermeiden, Audit vereinfachen | Entscheidungen im **10‑Min‑Takt** (`block=floor(epoch/600)`)                                          | Stabilität, Erklärbarkeit „pro Block“      | Sekunden‑Granularität, Event‑Only  | Kleine Latenz; **R4** mildert (Pre‑start)             |
| **007** | Deterministische Regelengine (R1–R5)          | Accepted | Vertrauen & Reproduzierbarkeit         | **R1–R5** im Kern; **keine Black‑Box‑ML** im Regelpfad                                                | Testbar, erklärbar, replizierbar           | Rein ML‑basierte Policy            | Priorität: **R3 > R2 > R5 > R1/R4**                   |
| **008** | EnergyState als SSoT                          | Accepted | Konsistenz über Module                 | **Energy Context** ist **einziger Schreiber**; alle anderen lesen                                     | Eine Wahrheit, weniger Race‑Conditions     | Mehrere Writer                     | Klare Verantwortlichkeit; Adapter harmonisieren Werte |
| **009** | Deadband & Hysterese                          | Accepted | Grenzbereichsrauschen                  | **Deadband** hält Zustand **D Blöcke**; nur **R2/R3** brechen                                         | Stabilität, Hardware‑Schutz                | Keine Stabilisierung               | Weniger Start/Stop, bessere UX                        |
| **010** | Manual Override (Block‑Scoped)                | Accepted | Nutzerautonomie                        | `override(action, ttl)` bis **Blockende/TTL**; Reason `manual_override`                               | Kontrolle ohne Policy‑Änderung             | Permanente manuelle Modi           | Sicherheit hat Vorrang (R2/R3 können brechen)         |
| **011** | Lokale Forecast‑Nutzung (R4)                  | Accepted | Frühstart bei stabiler Erwartung       | **Lokaler** Forecast (Datei/Dienst) beeinflusst nur **R4**                                            | Bessere Starts, kein Cloud‑Zwang           | Externe APIs/Cloud                 | Fehler werden durch **R2/R3** abgefangen              |
| **012** | Datenhaltung & Audit (Append‑Only)            | Accepted | Forschung/Audit                        | **Append‑only Logs**, versionierte **YAML‑Configs**                                                   | Wiederholbarkeit, Vergleichbarkeit         | Ephemere Zustände                  | Speicherplanung nötig; einfache Backups               |
| **013** | Lizenz & Offenheit                            | Accepted | Transparenz/Wiederverwendung           | **AGPLv3** + klare 3rd‑Party‑Lizenzen                                                                 | Offen, copyleft‑kompatibel                 | MIT/Apache, proprietär             | Ableitungen bleiben offen, Forschung fördert          |
| **014** | Privacy by Default (No Telemetry)             | Accepted | DSGVO, Vertrauen                       | **Keine** ausgehende Telemetrie; lokale Auth; Minimal‑Ports                                           | Minimale Angriffsfläche, Hoheit            | Opt‑in Telemetrie                  | Monitoring/Support lokal (Health, Logs)               |
| **015** | Safety‑First: Stop → Safe                     | Accepted | Thermik/SoC‑Grenzen                    | Harte Limits (**R3/R2**) stoppen sofort; Deadband ignoriert; Hysterese für Resume                     | Hardware‑Schutz, Vertrauen                 | Weiche Limits                      | Verfügbarkeit < Sicherheit; klar in UI                |
| **016** | Schnittstellen‑Vertrag (MQTT & REST)          | Accepted | Interoperabilität                      | MQTT: `energy/state/#`, `miner/cmd/set`, `explain/events/#`; REST: `/state`, `/timeline`, `/override` | Klare, testbare Contracts                  | Ad‑hoc Endpunkte                   | Leichte Integration, bessere Tests                    |
| **017** | KPIs als Zielgröße                            | Accepted | Wirkung messbar machen                 | KPIs im Core loggen, in Studien auswerten                                                             | Messbare Wirkung statt Behauptung          | Informell                          | Klare Erfolgsdefinition, kontinuierliches Tracking    |

---

## English Summary Table (EN)

| ADR | Title                           | Status   | Context                         | Decision                                               | Rationale                           | Alternatives            | Consequences                         |
| --: | ------------------------------- | -------- | ------------------------------- | ------------------------------------------------------ | ----------------------------------- | ----------------------- | ------------------------------------ |
| 001 | Local‑first architecture        | Accepted | Privacy, resilience, efficiency | Fully on‑prem; no cloud backend                        | Sovereignty, autonomy, traceability | Hybrid/cloud            | Local ops; full control              |
| 002 | MQTT as message bus             | Accepted | Loose coupling                  | MQTT for state/cmd/events; REST optional               | Async, lightweight, common          | REST‑only, proprietary  | Flexible integration                 |
| 003 | SQLite + Parquet                | Accepted | Auditable storage               | SQLite runtime; Parquet long‑term/replay               | Portable, low‑maintenance           | Postgres, TS‑DBs, cloud | Easy backups; limited scale (OK MVP) |
| 004 | Explanation UI                  | Accepted | HCI focus                       | Explainability UI with reasons, timeline, preview      | Understanding > visuals             | Perf dashboards         | Higher semantic value                |
| 005 | Sustainability as control       | Accepted | PV‑coupling                     | Surplus‑/price‑based switching                         | Efficiency, autonomy                | Fixed schedules         | Lower consumption; clear KPIs        |
| 006 | 10‑min block scheduler          | Accepted | Anti‑flapping, audit            | Decisions per 10‑min block                             | Stability, explainability           | Per‑second, event‑only  | Small latency; R4 mitigates          |
| 007 | Deterministic R1–R5             | Accepted | Trust & reproducibility         | No black‑box ML on control path                        | Testable, explainable               | ML‑only policy          | Priority: R3>R2>R5>R1/R4             |
| 008 | EnergyState as SSoT             | Accepted | Consistency                     | Single writer: Energy Context                          | One truth                           | Multi writers           | Clear responsibility                 |
| 009 | Deadband & hysteresis           | Accepted | Threshold noise                 | Hold D blocks; only R2/R3 may break                    | Stability, HW protection            | No stabilization        | Fewer toggles                        |
| 010 | Manual override                 | Accepted | User autonomy                   | Override action+ttl; block‑scoped                      | Control without policy change       | Permanent manual modes  | Safety overrides                     |
| 011 | Local forecast (R4)             | Accepted | Early start                     | Local forecast only affects R4                         | Better starts; no cloud             | External APIs           | Safety catches errors                |
| 012 | Append‑only + versioned configs | Accepted | Audit/replay                    | Append‑only logs; YAML configs                         | Reproducibility                     | Ephemeral states        | Storage planning                     |
| 013 | License (AGPLv3)                | Accepted | Openness                        | AGPLv3 + 3rd‑party clarity                             | Copyleft aligns with research       | MIT/Apache, proprietary | Derivatives stay open                |
| 014 | Privacy by default              | Accepted | GDPR, trust                     | No outbound telemetry; local auth                      | Minimal attack surface              | Opt‑in telemetry        | Local monitoring                     |
| 015 | Safety first                    | Accepted | Thermal/SoC                     | Hard stops (R3/R2); ignore deadband; hysteresis resume | HW protection, trust                | Soft limits             | Availability < safety                |
| 016 | Interface contract              | Accepted | Interop                         | MQTT topics + REST endpoints                           | Clear, testable                     | Ad‑hoc endpoints        | Easier integration, tests            |
| 017 | KPIs as objectives              | Accepted | Measurable impact               | Log in core; evaluate in studies                       | Evidence‑driven                     | Informal                | Clear success tracking               |

---

## Zusammenfassung / Summary

Diese Architekturentscheidungen verankern **lokale Autonomie, Transparenz, Nachhaltigkeit und Erklärbarkeit** im Systemdesign. Sie bilden das Rückgrat der technischen und forschungspraktischen Ausrichtung von BitGridAI.

> These ADRs embed **local autonomy, transparency, sustainability, and explainability** into the design. They are the backbone for technical execution and research practice.

*Weiter mit **[10 – Qualitätsszenarien / Quality Scenarios](./10_quality_scenarios.md)**.*
