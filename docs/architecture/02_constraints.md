# 02 – Rahmenbedingungen / Constraints

## Überblick / Overview

Dieses Kapitel beschreibt die zentralen **technischen, organisatorischen und rechtlichen Rahmenbedingungen**, die die Architektur von BitGridAI prägen.
Das Ziel ist, ein Gleichgewicht zwischen **lokaler Kontrolle, Nachhaltigkeit und Interoperabilität** zu schaffen.

> This chapter defines the **technical, organizational, and legal constraints** shaping the BitGridAI architecture.
> The goal is to maintain a balance between **local control, sustainability, and interoperability**.

---

## Technische Rahmenbedingungen / Technical Constraints

| Bereich                    | Beschreibung                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------- |
| **Lokale Ausführung**      | Alle Datenverarbeitung erfolgt lokal auf Nutzerhardware (z. B. Raspberry Pi, NUC). |
| **Open-Source-Stack**      | Nutzung ausschließlich quelloffener Softwarekomponenten (Python, MQTT, SQLite).    |
| **Modularität**            | System muss erweiterbar bleiben, ohne Kernlogik zu verändern.                      |
| **Offline-Fähigkeit**      | Grundfunktionen bleiben auch ohne Internetanbindung verfügbar.                     |
| **Hardwareunabhängigkeit** | Keine Bindung an proprietäre Smart-Home- oder Cloud-APIs.                          |

> | Area                      | Description                                                                  |
> | ------------------------- | ---------------------------------------------------------------------------- |
> | **Local Execution**       | All data processing occurs on user-owned hardware (e.g., Raspberry Pi, NUC). |
> | **Open-Source Stack**     | Only open-source components are used (Python, MQTT, SQLite).                 |
> | **Modularity**            | The system must remain extensible without modifying core logic.              |
> | **Offline Capability**    | Core functions remain operational without internet connectivity.             |
> | **Hardware Independence** | No dependency on proprietary Smart Home or cloud APIs.                       |

---

## Organisatorische Rahmenbedingungen / Organizational Constraints

| Bereich                  | Beschreibung                                                                              |
| ------------------------ | ----------------------------------------------------------------------------------------- |
| **Forschungskontext**    | Projekt im Rahmen universitärer Forschung mit Fokus auf HCI und Energieoptimierung.       |
| **Nachvollziehbarkeit**  | Alle Architekturentscheidungen müssen dokumentiert und reproduzierbar sein.               |
| **Kooperationen**        | Offene Schnittstellen für mögliche Forschungspartner (z. B. Energiemanagement-Institute). |
| **Ressourcenbegrenzung** | Entwicklung unter begrenztem Budget und Zeitrahmen.                                       |

> | Area                     | Description                                                                             |
> | ------------------------ | --------------------------------------------------------------------------------------- |
> | **Research Context**     | Conducted within an academic setting focusing on HCI and energy optimization.           |
> | **Traceability**         | All architectural decisions must be documented and reproducible.                        |
> | **Collaboration**        | Open interfaces to enable research partnerships (e.g., energy management institutions). |
> | **Resource Constraints** | Limited budget and time available for development.                                      |

---

## Rechtliche & Ethische Rahmenbedingungen / Legal & Ethical Constraints

| Bereich                         | Beschreibung                                                       |
| ------------------------------- | ------------------------------------------------------------------ |
| **Datenschutz (DSGVO)**         | Keine Cloud-Verarbeitung personenbezogener Daten.                  |
| **Transparenzpflicht**          | Systementscheidungen müssen erklärbar und nachvollziehbar sein.    |
| **Open-Source-Lizenzierung**    | Veröffentlichung unter AGPLv3 zur Wahrung der Transparenz.         |
| **Nachhaltigkeitspflicht**      | Energieeffizienz als entwerfendes Prinzip, nicht als Nebenprodukt. |
| **Keine zentrale Abhängigkeit** | Keine Drittanbieter-Clouds oder API-Keys notwendig.                |

> | Area                           | Description                                               |
> | ------------------------------ | --------------------------------------------------------- |
> | **Data Protection (GDPR)**     | No cloud processing of personal data.                     |
> | **Transparency Obligation**    | All system decisions must be explainable and traceable.   |
> | **Open-Source Licensing**      | Released under AGPLv3 to ensure transparency.             |
> | **Sustainability Requirement** | Energy efficiency is a design parameter, not a byproduct. |
> | **No Central Dependencies**    | No third-party cloud or API keys required.                |

---

## Umwelt- und Nachhaltigkeitsaspekte / Environmental & Sustainability Constraints

| Bereich                  | Beschreibung                                             |
| ------------------------ | -------------------------------------------------------- |
| **Energieverbrauch**     | Minimierung von Dauerlasten durch adaptive Steuerung.    |
| **Hardwarelebensdauer**  | Optimierung der Lastzyklen zur Schonung von Komponenten. |
| **Materialeinsatz**      | Fokus auf reparierbare, wiederverwendbare Hardware.      |
| **PV-Überschussnutzung** | Priorisierte Nutzung lokal erzeugter Energie.            |

> | Area                    | Description                                         |
> | ----------------------- | --------------------------------------------------- |
> | **Energy Consumption**  | Minimize continuous loads through adaptive control. |
> | **Hardware Lifetime**   | Optimize duty cycles to preserve component health.  |
> | **Material Efficiency** | Prioritize repairable and reusable hardware.        |
> | **PV Surplus Usage**    | Prefer local renewable energy utilization.          |

---

## Zusammenfassung / Summary

Die definierten Rahmenbedingungen gewährleisten, dass BitGridAI **unabhängig, erklärbar und nachhaltig** betrieben werden kann.
Sie bilden das Fundament für eine Architektur, die technologische Offenheit mit ethischer Verantwortung verbindet.

> The defined constraints ensure that BitGridAI operates **independently, transparently, and sustainably**.
> They form the foundation for an architecture that combines technological openness with ethical responsibility.
