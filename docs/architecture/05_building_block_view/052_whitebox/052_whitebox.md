# 052 – Whitebox-Sicht / White Box View

TODO: Das Hauptdiagramm und die Beschreibung der Top-Level-Architektur. Hier siehst du, welche Module es gibt, wofür sie zuständig sind und mit wem sie Daten austauschen.

> **Kurzüberblick:**  
> Innere Struktur von BitGridAI: Kernkomponenten, Verantwortlichkeiten und interne Flüsse. Alles **lokal-first, deterministisch (R1–R5), erklärbar**.

> **TL;DR (EN):**  
> Internal structure: core components, responsibilities, and flows. Local-first, deterministic (R1–R5), explainable.

---

## Hauptkomponenten / Main Components

- **core/block_scheduler**: 10‑Min-Takt, vergibt `valid_until` (Deadband).
- **core/rule_engine (R1–R5)**: Start/Autarkie/Thermo/Forecast/Deadband; Priorität R3>R2>R5>R1/R4.
- **core/energy_context**: schreibt EnergyState (SSoT), konsolidiert Mess-/Forecast-/Preis-/Thermo-Daten.
- **modules/**: Adapter für PV, Smart Meter, Speicher, Miner (MQTT/REST/Modbus).
- **ui/**: Explainability-UI + WebSocket/REST-Layer; Overrides, Preview, Timeline.
- **explain/**: On-device LLM (Explain-Agent) für Microcopy/Was-wäre-wenn (read-only zum Regelpfad).
- **data/**: Logging (SQLite/Parquet/JSON), Replay, KPIs.
- **research/**: Export/Replay-Tools, Opt-in-Governance.

---

## Interne Flüsse / Internal Flows

1) Adapter → EnergyState  
2) BlockScheduler → Rule Engine (R1–R5)  
3) Decision → Actuation (Miner/Relay) + DecisionEvent → UI/Logs  
4) Explain-Agent → ExplainSession → UI/Research (keine Steuerung)  
5) Overrides/Research-Toggle → Rule Engine → UI Feedback

---

## Datenmodelle (Kurz)

- **EnergyState**: `ts, block_id, p_pv_kw, p_load_kw, surplus_kw, soc_pct, t_miner_c, price_ct_kwh, forecast_surplus_kw[], grid_import_kw, grid_export_kw`
- **DecisionEvent**: `action, reason, trigger, params, valid_until, override_ttl, preferred_path`
- **ExplainSession**: `prompt_version, result_text_de/en, confidence, type (live|what_if)`

---

## Querschnittliche Konzepte im Whitebox-Kontext

- **Explainability by Design**: Reason/Trigger/Params in jedem DecisionEvent; Timeline/Preview im UI.
- **Safety First**: R3/R2 können Deadband/Overrides brechen; Stop → Safe.
- **Determinismus & Replay**: Append-only Logs, identische Decisions bei gleichem Input (Tests/Replay).
- **Privacy-by-Default**: keine ausgehende Telemetrie; Research-Exports nur Opt-in.

> Whitebox: zeigt, wie die Bausteine zusammenspielen, ohne Cloud-Abhängigkeiten und mit klaren Verantwortlichkeiten.
