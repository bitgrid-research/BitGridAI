# 12 – Glossar

Die gemeinsame Sprache von BitGridAI.

Dieses Dokument liefert die **Endgültige Terminologie** des gesamten Projekts. Die alphabetische Auflistung aller wichtigen Fachbegriffe stellt sicher, dass Entwickler, Forscher und Anwender dasselbe unter Konzepten wie **EnergyState**, **BlockInterval** oder **Deadband** verstehen.

<img src="../../media/architecture/12_glossary/bithamster_12.png" alt="Hamster tech12" width="1000" />

&nbsp;

## Überblick

Das Glossar enthält zentrale Begriffe, Konzepte und Abkürzungen, die in der BitGridAI‑Architektur verwendet werden. Es dient dazu, **Konsistenz, Verständlichkeit und Nachvollziehbarkeit** innerhalb der Dokumentation sicherzustellen.

---

## Fachbegriffe

| Begriff | Definition |
| :--- | :--- |
| **AGPLv3** | Lizenz, die Transparenz und Copyleft bei Netzbetrieb sicherstellt. |
| **BitGridAI** | Lokales, erklärbares Energiesystem zur Nutzung von PV‑Überschuss und zur Steuerung flexibler Lasten. |
| **BlockInterval (10 min)** | Zeitraster für deterministische Entscheidungen: $block\_id = \text{floor}(\text{epoch}/600)$. |
| **BlockScheduler** | Orchestriert Regelbewertung im 10‑Min‑Takt und setzt Deadband‑Fenster. |
| **Deadband** | Anti‑Flapping‑Mechanismus: hält den Zustand für $D$ Blöcke, außer Safety‑Regeln greifen. |
| **DeadbandActivatedEvent** | Event, das die Aktivierung eines Haltefensters signalisiert. |
| **DecisionEvent** | Domain‑Event mit Aktion, Grund (Reason), Triggern, Parametern und Gültigkeit. |
| **Energy-Path Policy** | Protokolliert die Entscheidung über die Opportunitätskosten der Energieverwendung (Export/Heat/Hodl). |
| **EnergyState (SSoT)** | Zentraler, schreibgeschützter Zustand („Single Source of Truth“) für alle Leser (Core, UI, Logger). |
| **EnergyStateChangedEvent** | Domain‑Event bei Aktualisierung des EnergyState. |
| **Erklärschnittstelle (Explainability UI)** | Lokale UI zur Begründung von Entscheidungen und Anzeige der Timeline. |
| **Explain-Agent (On-Device LLM)** | Lokal ausgeführtes Sprachmodell (quantisiert), generiert Microcopy & Was-wäre-wenn-Ausgaben, bleibt read-only zum Regelpfad. |
| **ExplainSession** | Persistenter Datensatz pro Erklärung/Simulation (`decision_id`, `prompt_version`, `result_text_de/_en`, `confidence`, `type`, `valid_until`), verlinkt zu DecisionEvents. |
| **ExportBundle** | Verschlüsseltes Paket (Timeline, KPIs, ExplainSessions, Hash) für Forschung/Sharing. |
| **Flapping** | Häufige Zustandswechsel Start/Stop; zu minimieren via Deadband. |
| **Grid‑Import** | Netzbezug; KPI zur Reduktion durch lokale Optimierung. |
| **Home Assistant (HA)** | Open‑Source‑Plattform für lokale Automatisierung und Geräteintegration. |
| **KPI** | Kennzahlen zur Wirkung (Grid‑Import↓, Flapping↓, Explanation‑Coverage↑, Trust‑Score↑, Thermal‑Incidents=0). |
| **Local‑First** | Prinzip: Berechnung und Datenhaltung ausschließlich auf Nutzerhardware. |
| **Manual Override** | Temporäre manuelle Steuerung (Start/Stop/Level) bis Blockende/TTL. |
| **Mining Node** | Flexible Last (z. B. Bitcoin‑Miner), die Überschussenergie nutzt. |
| **Modbus (TCP)** | Industriestandard‑Protokoll zur Datenabfrage z. B. am Inverter. |
| **Mosquitto** | Lokaler MQTT‑Broker für Topics wie `energy/state/#` oder `explain/events/#`. |
| **MQTT** | Leichtgewichtiges Messaging‑Protokoll für asynchrone Kopplung. |
| **Next‑Block Preview** | Vorschau der erwarteten Aktion im nächsten Block inkl. Schwellen. |
| **R1 Startregel** | Start bei Überschuss + ggf. Preisgrenzen. |
| **R2 Autarkie‑Schutz** | Stop/Block bei niedrigem SoC zum Schutz der Eigenversorgung. |
| **R3 Thermo‑Schutz** | Sofort‑Stop bei Übertemperatur; Wiederaufnahme mit Hysterese. |
| **R4 Prognose‑Veto** | NOOP-Veto bei zu geringer PV-Prognose oder erwartetem Preis-Peak; löst nie selbst einen Start aus. |
| **R5 Deadband / Anti‑Flapping** | Stabilisierung zur Vermeidung häufiger Start/Stop‑Wechsel. |
| **Replay Runner** | Tool, das Parquet/SQLite-Logs deterministisch abspielt (1x–20x) und KPIs vergleicht. |
| **Research Service** | Lokaler Dienst/CLI für `/research/toggle`, `/research/export`, `/replay` inkl. Audit-Logs. |
| **Research Toggle** | Opt-in/Opt-out-Schalter für Forschung, steuert Export/Replay und UI-Hinweise. |
| **REST / WebSocket** | Lokale HTTP‑/WS‑Schnittstellen für State, Timeline, Events. |
| **Rule Engine (R1–R5)** | Deterministische Kernlogik: Start (R1), Autarkie‑Schutz (R2), Thermo‑Schutz (R3), Prognose‑Veto (R4), Deadband (R5). |
| **SoC (State of Charge)** | Ladezustand des Speichers (0…1); Schutz via R2. |
| **SQLite / Parquet** | Lokale Speicherung (Online‑DB / Langzeit‑Logs & Replay). |
| **Stop → Safe** | Der definierte Fail-Safe-Zustand, der bei kritischen Safety-Regeln (R2/R3) oder unbehebbaren Fehlern erzwungen wird. |
| **Surplus** | Überschussleistung: $p\_pv − p\_load − p\_charge\_req + p\_discharge\_avail$. |
| **T_MAX / T_RESUME** | Temperatur‑Schwellen für Stop/Resume des Miners (R3). |
| **Trust‑Score** | Nutzervertrauen (z. B. Likert‑Skala) aus Studien/Feedback. |

&nbsp;

## Abkürzungen

| Kürzel | Bedeutung |
| :--- | :--- |
| **a11y** | Accessibility (Barrierefreiheit). |
| **ADR** | Architecture Decision Record. |
| **API** | Application Programming Interface. |
| **CLI** | Command Line Interface. |
| **CO₂** | Kohlendioxid, Kenngröße für Energieeffizienz. |
| **DB** | Database. |
| **GGML** | Quantisiertes LLM-Format (für CPU/GPU, on-device). |
| **HA** | Home Assistant. |
| **HCI** | Human‑Computer Interaction. |
| **KPI** | Key Performance Indicator. |
| **LAN** | Local Area Network. |
| **LLM** | Large Language Model (z. B. Explain-Agent). |
| **NTP** | Network Time Protocol. |
| **PII** | Personally Identifiable Information. |
| **R1–R5** | Regelwerk (Start, Autarkie, Thermo, Prognose, Deadband). |
| **SoC** | State of Charge (Ladezustand). |
| **SSoT** | Single Source of Truth (EnergyState). |
| **TLS** | Transport Layer Security. |
| **UI** | User Interface. |
| **UX** | User Experience. |
| **VLAN** | Virtual LAN. |
| **WS** | WebSocket. |
| **XAI** | Explainable Artificial Intelligence. |

---
> **🏁 Ziel erreicht! (Level 12 Cleared)**
>
> Wow, du hast es tatsächlich bis hierher geschafft? Respekt! Das ist weiter, als 90 % aller Entwickler jemals lesen werden. 😉
>
> **Danke für deine Geduld und dein Interesse!** ❤️
>
> Der Architektur-Hamster klappt jetzt den Laptop zu, gönnt sich eine handvoll Sonnenblumenkerne und legt sich auf den warmen Raspberry Pi zum Schlafen. 
>
>Bitte nicht wecken, außer der Bitcoin-Kurs explodiert. 🐹💤

🔙 Zurück zur **[Kapitelübersicht](../12_glossary/README.md)**

🏠 Zurück zur **[Hauptübersicht](../../README.md)**
