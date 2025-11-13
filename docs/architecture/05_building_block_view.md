# 05 – Bausteinsicht / Building Block View

## Überblick / Overview
BitGridAI ist in klar abgegrenzte, lose gekoppelte Bausteine gegliedert.  
Jedes Modul erfüllt eine spezifische Aufgabe innerhalb des Gesamtsystems  
und trägt durch seine Schnittstellen und Logs zur **Erklärbarkeit und Nachvollziehbarkeit** bei.

> BitGridAI is divided into clearly separated, loosely coupled building blocks.  
> Each module fulfills a specific role within the overall system and contributes to **explainability and traceability** through its interfaces and logs.

---

## Hauptbausteine / Core Building Blocks

| Modul / Ordner | Verantwortung | Beschreibung |
|----------------|----------------|---------------|
| `core/` | Energiefluss- und Entscheidungslogik | Verwaltung von Zuständen, Regeln und Prioritäten |
| `modules/` | Integrationsadapter | Anbindung externer Systeme (z. B. Home Assistant, Inverter, Miner) |
| `ui/` | Lokale Erklärschnittstelle | Darstellung von Energiezuständen, Entscheidungen und Begründungen |
| `data/` | Logging & Simulation | Speicherung von Ereignissen, Messdaten und Evaluationsergebnissen |
| `docs/` | Architektur & Forschung | System- und Forschungsdokumentation (arc42, HCI, Evaluation) |

> | Module / Folder | Responsibility | Description |
> |----------------|----------------|--------------|
> | `core/` | Energy flow and decision logic | Manages states, rules, and priorities |
> | `modules/` | Integration adapters | Connects external systems (e.g., Home Assistant, inverter, miner) |
> | `ui/` | Local explanation interface | Displays energy states, decisions, and rationales |
> | `data/` | Logging & simulation | Stores events, measurements, and evaluation data |
> | `docs/` | Architecture & research | System and research documentation (arc42, HCI, evaluation) |

---

## Kommunikationsschnittstellen / Interfaces
- **MQTT** – Austausch von Energie- und Statusdaten  
- **REST API** – Zugriff auf Kontroll- und Visualisierungsfunktionen  
- **Eventbus (lokal)** – interne Kommunikation zwischen Modulen und Kernlogik  
- **Dateibasierte Logs** – Persistente Speicherung von Entscheidungen und Zuständen  

> - **MQTT** – exchange of energy and state data  
> - **REST API** – access to control and visualization endpoints  
> - **Local Event Bus** – internal communication between modules and the core logic  
> - **File-based Logs** – persistent storage of decisions and states

---

## Interne Struktur / Internal Structure
Die Module interagieren über asynchrone Schnittstellen.  
Das System ist so konzipiert, dass es **erweiterbar, testbar und nachvollziehbar** bleibt,  
auch wenn neue Energiequellen, Verbraucher oder Forschungsadapter hinzugefügt werden.

> Modules interact through asynchronous interfaces.  
> The system is designed to remain **extensible, testable, and transparent**, even as new energy sources, loads, or research adapters are added.

---

## Strukturskizze / Structural Overview
[ PV / Speicher / Sensoren ]
↓
[ modules/ ]
↓
[ core/ ]
↙ ↘
[ data/ ] [ ui/ ]
↓
[ docs/ ]


> ```
> [ PV / Storage / Sensors ]
>           ↓
>       [ modules/ ]
>           ↓
>       [ core/ ]
>     ↙          ↘
> [ data/ ]    [ ui/ ]
>       ↓
>     [ docs/ ]
> ```

---

## Qualitätsaspekte / Quality Aspects
| Aspekt | Beschreibung |
|--------|---------------|
| **Modularität** | Ermöglicht isolierte Weiterentwicklung und Tests einzelner Komponenten |
| **Erklärbarkeit** | Jede Systementscheidung wird im Log und UI begründet |
| **Reproduzierbarkeit** | Alle Aktionen sind zeitlich und datenbasiert rekonstruierbar |
| **Erweiterbarkeit** | Neue Energiequellen oder Verbraucher können als Module ergänzt werden |
| **Nachhaltigkeit** | Komponenten arbeiten ressourcenschonend und lokal ohne Cloud-Abhängigkeit |

> | Aspect | Description |
> |--------|--------------|
> | **Modularity** | Enables isolated development and testing of individual components |
> | **Explainability** | Every decision is logged and explained through the UI |
> | **Reproducibility** | All actions are time- and data-traceable |
> | **Extensibility** | New energy sources or loads can be added as modules |
> | **Sustainability** | Components run locally and efficiently without cloud dependencies |

---

## Zusammenfassung / Summary
Die Bausteinsicht zeigt BitGridAI als **offenes, lokales System**,  
in dem Energieverwaltung, Datenverarbeitung und Nutzerinteraktion klar getrennt und nachvollziehbar bleiben.  
Jede Komponente trägt zur erklärbaren Gesamtlogik bei und unterstützt  
eine nachhaltige, vertrauenswürdige und reproduzierbare Energieautomatisierung.

> The building block view presents BitGridAI as an **open, local system**  
> where energy control, data processing, and user interaction remain clearly separated and transparent.  
> Each component contributes to the explainable overall logic and supports  
> sustainable, trustworthy, and reproducible energy automation.

* [06 Laufzeitsicht / Runtime View](./06_runtime_view.md)
