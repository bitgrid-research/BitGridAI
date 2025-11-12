# 11 – Risiken und Technische Schulden / Risks and Technical Debt

## Überblick / Overview

Dieses Kapitel beschreibt die identifizierten Risiken und bestehenden technischen Schulden innerhalb von BitGridAI.
Ziel ist es, potenzielle Schwachstellen frühzeitig zu erkennen, deren Auswirkungen zu bewerten und Maßnahmen zur Reduzierung abzuleiten.

> This chapter outlines the identified risks and existing technical debt within BitGridAI.
> The goal is to detect potential weaknesses early, assess their impact, and define strategies for mitigation.

---

## Hauptrisiken / Key Risks

| Risiko                              | Beschreibung                                          | Wahrscheinlichkeit | Auswirkung | Gegenmaßnahme                                      |
| ----------------------------------- | ----------------------------------------------------- | ------------------ | ---------- | -------------------------------------------------- |
| **Hardwareausfall**                 | Defekte Sensoren oder Instabilität auf Raspberry Pi   | Mittel             | Hoch       | Redundante Sensoren, automatisches Recovery-Skript |
| **MQTT-Broker-Ausfall**             | Kommunikationsunterbrechung zwischen Modulen          | Hoch               | Mittel     | Fallback-Mechanismus, lokale Zwischenspeicherung   |
| **Fehlerhafte Regeldefinitionen**   | Nutzer konfigurieren inkonsistente Regeln       | Mittel             | Mittel     | Validierung und Simulation vor Aktivierung         |
| **Speicherüberlauf / Logwachstum**  | Dauerhafte Protokollierung führt zu Speicherknappheit | Niedrig            | Hoch       | Periodische Bereinigung, Archivierung alter Logs   |
| **Nachhaltigkeitsmetriken ungenau** | Unpräzise Erfassung der PV- oder Verbrauchsdaten      | Mittel             | Mittel     | Kalibrierung, Plausibilitätsprüfungen              |
| **UI-Verständlichkeit**             | Nutzer interpretieren Erklärungen falsch        | Niedrig            | Mittel     | Usability-Tests, iteratives HCI-Feedback           |

> | Risk                                  | Description                                   | Probability | Impact | Mitigation                                  |
> | ------------------------------------- | --------------------------------------------- | ----------- | ------ | ------------------------------------------- |
> | **Hardware Failure**                  | Defective sensors or Raspberry Pi instability | Medium      | High   | Redundant sensors, auto-recovery script     |
> | **MQTT Broker Failure**               | Loss of communication between modules         | High        | Medium | Fallback mechanism, local buffering         |
> | **Invalid Rule Definitions**          | Users configure inconsistent rules            | Medium      | Medium | Validation and simulation before activation |
> | **Storage Overflow / Log Growth**     | Continuous logging causes storage shortage    | Low         | High   | Periodic cleanup, archiving of old logs     |
> | **Inaccurate Sustainability Metrics** | Imprecise PV or consumption measurements      | Medium      | Medium | Calibration and plausibility checks         |
> | **UI Misinterpretation**              | Users misunderstand explanations              | Low         | Medium | Usability testing, iterative HCI feedback   |

---

## Technische Schulden / Technical Debt

| Bereich            | Beschreibung                                     | Risiko                                   | Gegenmaßnahme                                    |
| ------------------ | ------------------------------------------------ | ---------------------------------------- | ------------------------------------------------ |
| **Modularität**    | Einige Adapter fest in Logik eingebunden         | Erweiterungsaufwand                      | Refactoring zu Plugin-System                     |
| **Logging-System** | Keine einheitliche Log-Struktur zwischen Modulen | Inkonsistente Analysen                   | Einführung eines zentralen Logging-Schemas       |
| **Testing**        | Fehlende automatisierte Tests für MQTT-Events    | Risiko von Regressionsfehlern            | Aufbau einer Testumgebung mit simulierten Topics |
| **Dokumentation**  | Fehlende API-Dokumentation                       | Verständnisbarrieren für neue Entwickler | Generierung via docstrings und Sphinx            |
| **UI-Komponenten** | Fehlende Barrierefreiheit (Accessibility)        | Eingeschränkte Nutzbarkeit               | Implementierung von a11y-Konzepten               |

> | Area               | Description                                    | Risk                                | Mitigation                                   |
> | ------------------ | ---------------------------------------------- | ----------------------------------- | -------------------------------------------- |
> | **Modularity**     | Some adapters still tightly coupled with logic | Higher extension effort             | Refactor into plugin system                  |
> | **Logging System** | Inconsistent log structures across modules     | Analysis inconsistency              | Introduce unified logging schema             |
> | **Testing**        | Missing automated MQTT event tests             | Risk of regression                  | Build test environment with simulated topics |
> | **Documentation**  | Missing API documentation                      | Onboarding barrier for contributors | Generate via docstrings and Sphinx           |
> | **UI Components**  | Lack of accessibility features                 | Reduced usability                   | Implement accessibility (a11y) concepts      |

---

## Risikoanalyse / Risk Analysis

| Kategorie             | Beschreibung                                        | Priorität |
| --------------------- | --------------------------------------------------- | --------- |
| **Betrieblich**       | Hardwarestabilität, Netzwerkunterbrechungen         | Hoch      |
| **Technisch**         | Modularität, fehlende Tests                         | Hoch      |
| **Organisatorisch**   | Fehlende Dokumentation, geringe Entwicklerkapazität | Mittel    |
| **Forschungsbezogen** | Validierung der Nachhaltigkeitsmetriken             | Mittel    |

> | Category             | Description                                    | Priority |
> | -------------------- | ---------------------------------------------- | -------- |
> | **Operational**      | Hardware stability, network interruptions      | High     |
> | **Technical**        | Modularity, missing tests                      | High     |
> | **Organizational**   | Documentation gaps, limited developer capacity | Medium   |
> | **Research-related** | Validation of sustainability metrics           | Medium   |

---

## Maßnahmenplan / Mitigation Plan

1. **Automatisierte Tests** für Regel-Engine und MQTT-Kommunikation einführen.
2. **Modularisierung refaktorieren** (Plugin-basierte Module).
3. **Speicher- und Logging-Management** regelmäßig prüfen.
4. **Forschungspartnerschaften** für Metrikvalidierung und HCI-Tests ausbauen.
5. **Monitoring-Dashboard** für Systemgesundheit und Energieeffizienz entwickeln.

> 1) Implement **automated tests** for rule engine and MQTT communication.
> 2) **Refactor modularization** (plugin-based architecture).
> 3) Regularly review **storage and logging management**.
> 4) Strengthen **research partnerships** for metric validation and HCI testing.
> 5) Develop a **monitoring dashboard** for system health and energy efficiency.

---

## Zusammenfassung / Summary

Das Risikomanagement stellt sicher, dass BitGridAI langfristig stabil, nachvollziehbar und erweiterbar bleibt.
Durch die bewusste Dokumentation technischer Schulden kann das Projekt gezielt verbessert werden,
ohne seine Grundwerte – **Lokalität, Transparenz und Nachhaltigkeit** – zu gefährden.

> The risk management ensures that BitGridAI remains stable, transparent, and extensible in the long term.
> By documenting technical debt consciously, the project can evolve strategically without compromising its core principles – **locality, transparency, and sustainability**.
