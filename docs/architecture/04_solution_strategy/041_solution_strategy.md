# 041 – Lösungsstrategie / Solution Strategy

> **Kurzüberblick:**  
> **Modular, local-first, erklärbar**: deterministische **R1–R5** im **10-Min-Blocktakt**, Explainability-UI + on-device Explain-Agent, MQTT/REST-Adapter, SQLite/Parquet-Logging & Replay, Research-Toggle. Keine Cloud.

> **TL;DR (EN):**  
> Modular, local-first, explainable: **R1–R5** on a 10-min cadence, explainability UI + on-device agent, MQTT/REST adapters, SQLite/Parquet logging & replay, research toggle; no cloud.

---

## Ansatz / Approach

BitGridAI kombiniert Energieoptimierung mit **Erklärbarkeit** und **Nachhaltigkeit**.  
Klar getrennte Bausteine (core/modules/ui/data/docs) erlauben Erweiterung ohne Kernbrüche; jede Entscheidung bleibt nachvollziehbar und reproduzierbar.

---

## Architekturprinzipien

1. **Trennung von Verantwortlichkeiten**: Logik, Module, Erklärungsschicht klar getrennt.  
2. **Transparenz zuerst**: Reason/Trigger/Parameter für jede Aktion; Timeline & Preview.  
3. **Lokal statt Cloud**: Daten und Modelle bleiben auf Nutzerhardware.  
4. **Echtzeit-Erklärbarkeit**: Explain-Agent on-device.  
5. **Nachhaltigkeit als Steuergröße**: Surplus/Preis steuern Last, Deadband glättet.  
6. **Forschungs- & Replay-Fähigkeit**: Research-Toggle, KPIs, Replays sind first-class.

---

## Technologische Strategie (Kurzfassung)

- **Kernlogik:** Python-Rule-Engine (R1–R5), BlockScheduler, Hodl-Policy.  
- **Kommunikation:** MQTT/REST für asynchrone Kopplung zu Geräten & UI.  
- **Explainability:** Lokale UI + on-device LLM für Microcopy & Was-wäre-wenn.  
- **Speicherung:** SQLite/Parquet/JSON, append-only, versionierte YAML-Configs.  
- **Research Services:** CLI/Tools für KPIs, Opt-in-Export, anonymisierte Reports.

---

## Begründung / Rationale

Lokal-first erhöht Datenschutz & Resilienz; deterministische Regeln sind testbar und erklärbar; Modularität erleichtert neue Adapter; Nachhaltigkeit und HCI werden als Kernparameter in der Steuerlogik geführt; Replays sichern wissenschaftliche Evidenz.

> Local-first privacy, deterministic/testable rules, modular adapters, sustainability & HCI as first-class, replayable evidence.
