# 02 – Rahmenbedingungen / Constraints

> **Kurzüberblick:**
>   
> BitGridAI ist **local-first**, **open-source** und **erklärbar**.  
> Keine Cloud, keine proprietären Abhängigkeiten, deterministische Regeln (**R1–R5**), 10-Min-Blocktakt, Safety & Logging als Pflicht.

> **TL;DR (EN):**
> 
> BitGridAI is **local-first**, **open-source**, and **explainable**.  
> No cloud, no proprietary dependencies; deterministic rules (**R1–R5**), 10-minute block cadence; safety & logging are mandatory.

---

## Überblick / Overview
Dieses Kapitel beschreibt die zentralen **technischen, organisatorischen und rechtlichen Rahmenbedingungen**, die die Architektur von BitGridAI prägen.  
Ziel ist ein Gleichgewicht zwischen **lokaler Kontrolle, Nachhaltigkeit und Interoperabilität**.

> This chapter defines the **technical, organizational, and legal constraints** shaping the BitGridAI architecture.  
> The goal is to maintain a balance between **local control, sustainability, and interoperability**.

---

## Technische Rahmenbedingungen / Technical Constraints

| Bereich                         | Beschreibung |
| --- | --- |
| **Lokale Ausführung** | Alle Datenverarbeitung erfolgt lokal auf Nutzerhardware (z. B. Raspberry Pi, NUC, ThinClient). |
| **Open-Source-Stack** | Ausschließlich quelloffene Komponenten (Python, MQTT, Home Assistant, SQLite/Parquet). |
| **Modularität** | Erweiterbar über **lokale Adapter** (MQTT/REST/Modbus), ohne Kernlogik zu verändern. |
| **Offline-Fähigkeit** | Grundfunktionen bleiben ohne Internet verfügbar (Steuerung, Logging, UI). |
| **Hardwareunabhängigkeit** | Keine Bindung an proprietäre Smart-Home-Hubs oder Cloud-APIs. |
| **Single Source of Truth** | **EnergyState** als zentraler Zustand (Messwerte, Prognosen, Preis/SoC, Temperaturen). |
| **Deterministische Regelengine** | **R1–R5** (Start, Autarkie-Schutz, Thermo-Schutz, Prognose-Start, Deadband) sind deterministisch; kein Black-Box-ML im Regelpfad. |
| **Block-Scheduler** | Entscheidungen im **10-Min-Takt** (BlockInterval) zur Stabilität und Anti-Flapping. |
| **Explainability by Design** | Jede Aktion liefert **Reason/Trigger/Parameter** und erzeugt ein DecisionEvent. |
| **Safety & Fail States** | Klare Grenzwerte (SoC/Temperatur) → **Stop → Safe**; kein OC/UV von Mining-HW. |
| **Logging & KPIs** | Append-only Log lokal; Reproduzierbarkeit über versionierte Konfiguration (YAML). |
| **Security/Privacy** | Keine Telemetrie nach außen; minimale offenen Ports; lokale Auth (z. B. HA-User). |

> | Area | Description |
> | --- | --- |
> | **Local Execution** | All processing runs on user hardware (e.g., Raspberry Pi, NUC, thin client). |
> | **Open-Source Stack** | Only FOSS components (Python, MQTT, Home Assistant, SQLite/Parquet). |
> | **Modularity** | Extensible via **local adapters** (MQTT/REST/Modbus) without touching core logic. |
> | **Offline Capability** | Core functions (control, logging, UI) work without internet. |
> | **Hardware Independence** | No reliance on proprietary hubs or cloud APIs. |
> | **Single Source of Truth** | **EnergyState** centralizes metering, forecasts, prices/SoC, temperatures. |
> | **Deterministic Rule Engine** | **R1–R5** are deterministic; no black-box ML in the control loop. |
> | **Block Scheduler** | Decisions align to a **10-minute rhythm** for stability and anti-flapping. |
> | **Explainability by Design** | Every action includes **reason/trigger/parameters** and emits a DecisionEvent. |
> | **Safety & Fail States** | Hard limits (SoC/temperature) → **stop → safe**; no OC/UV of mining HW. |
> | **Logging & KPIs** | Append-only local log; reproducible, versioned YAML configuration. |
> | **Security/Privacy** | No outbound telemetry; minimal open ports; local auth (e.g., HA users). |

---

## Organisatorische Rahmenbedingungen / Organizational Constraints

| Bereich | Beschreibung |
| --- | --- |
| **Forschungskontext** | Universitäres Projekt (HCI & Energieinformatik) mit Feldstudien im Haushalt. |
| **Nachvollziehbarkeit** | Architektur- & Entscheidungsdoku obligatorisch (ADR in `09_design_decisions.md`). |
| **Kooperationen** | Offene Schnittstellen für Partner (Messgeräte, Zähler, Prosumer-Communities). |
| **Ressourcenbegrenzung** | Budget/Zeitrahmen limitiert → Fokus auf MVP + Kernfunktionen. |
| **Konfigurationsdisziplin** | Änderungen nur über versionierte YAMLs; reproducible builds. |

> | Area | Description |
> | --- | --- |
> | **Research Context** | Academic project (HCI & energy informatics) with in-home field trials. |
> | **Traceability** | Architecture & decision documentation mandatory (ADRs in `09_design_decisions.md`). |
> | **Collaboration** | Open interfaces for partners (meters, sensors, prosumer groups). |
> | **Resource Constraints** | Limited budget/time → focus on MVP and core features. |
> | **Config Discipline** | Changes via versioned YAML; reproducible builds. |

---

## Rechtliche & Ethische Rahmenbedingungen / Legal & Ethical Constraints

| Bereich | Beschreibung |
| --- | --- |
| **Datenschutz (DSGVO)** | Keine Cloud-Verarbeitung personenbezogener Daten; **Datenminimierung** & lokale Aufbewahrung. |
| **Einwilligung & Anonymisierung** | Für Nutzerstudien: informierte Einwilligung, Pseudonymisierung der Logs. |
| **Transparenzpflicht** | Entscheidungen müssen erklärbar & nachvollziehbar sein (UI-Erklärungen, Timeline). |
| **Open-Source-Lizenz** | Veröffentlichung unter **AGPLv3**; Third-Party-Lizenzen beachten. |
| **Sicherheitsnormen** | Einsatz **zertifizierter** Schaltkomponenten; keine Arbeiten an Netzspannung im Projektumfang. |
| **Keine Zentralabhängigkeit** | Keine Drittanbieter-Clouds oder API-Keys als Voraussetzung für Grundfunktionen. |

> | Area | Description |
> | --- | --- |
> | **Data Protection (GDPR)** | No cloud processing of personal data; **data minimization** and local retention. |
> | **Consent & Anonymization** | For user studies: informed consent; pseudonymized logs. |
> | **Transparency Obligation** | Decisions must be explainable (UI rationales, timeline). |
> | **Open-Source Licensing** | **AGPLv3**; respect third-party licenses. |
> | **Safety Standards** | Use **certified** switching gear; no mains work within project scope. |
> | **No Central Dependencies** | No third-party cloud/API keys required for core functions. |

---

## Umwelt- & Nachhaltigkeitsaspekte / Environmental & Sustainability Constraints

| Bereich | Beschreibung |
| --- | --- |
| **Energieverbrauch** | Minimierung von Dauerlasten durch Deadband, Blocktakt und Leistungsstufen. |
| **Hardwarelebensdauer** | Schonende Lastprofile (Temperatur- und Lüfterpolitik) verlängern Lebensdauer. |
| **Materialeinsatz** | Bevorzugt reparierbare, wiederverwendbare Hardware (Refurb/Thin Clients). |
| **PV-Überschussnutzung** | Vorrang für lokal erzeugte Energie; optionale **Wärmenutzung** der Abwärme. |

> | Area | Description |
> | --- | --- |
> | **Energy Consumption** | Reduce steady loads via deadband, block rhythm and power levels. |
> | **Hardware Lifetime** | Gentle duty cycles (temperature/fan policy) extend component health. |
> | **Material Efficiency** | Prefer repairable/reusable hardware (refurb/thin clients). |
> | **PV Surplus Usage** | Prioritize local generation; optional **heat reuse** from mining. |

---

## HCI & Explainability-Constraints

| Bereich | Beschreibung |
| --- | --- |
| **User Autonomy** | Manuelle Override-Möglichkeiten mit klarer Rücknahme-Logik (Timeout/Next-Block). |
| **Erklärungspflicht** | Jede Entscheidung erzeugt eine **lesbare Begründung** (Reason, Trigger, Parameter). |
| **Vorhersage-Feedback** | UI zeigt „**Was passiert im nächsten Block?**“ inkl. Start/Stop-Schwellen. |
| **Audit-Trail** | Zeitachse mit DecisionEvents, EnergyState-Snapshots und KPI-Hinweisen. |

> | Area | Description |
> | --- | --- |
> | **User Autonomy** | Manual overrides with clear rollback logic (timeout/next block). |
> | **Explanation Duty** | Each decision includes **human-readable rationale**. |
> | **Predictive Feedback** | UI previews “**what happens next block**” incl. thresholds. |
> | **Audit Trail** | Timeline of DecisionEvents, EnergyState snapshots, KPI hints. |

---

## Zusammenfassung / Summary
Die definierten Rahmenbedingungen gewährleisten, dass BitGridAI **unabhängig, erklärbar und nachhaltig** betrieben werden kann.  
Sie bilden das Fundament für eine Architektur, die technologische Offenheit mit ethischer Verantwortung verbindet.

> The defined constraints ensure that BitGridAI operates **independently, transparently, and sustainably**.  
> They form the foundation for an architecture that combines technological openness with ethical responsibility.

*Weiter mit **[03 – Systemkontext / System Context](./03_context.md)**.*



