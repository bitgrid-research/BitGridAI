# 086 – Logging & Tracing

> **Kurzüberblick:**  
> **Append-only** Logging (SQLite/Parquet/JSON), Events nach **DecisionEvent/EnergyState/ExplainSession**, lokale KPIs & Replay; keine Telemetrie nach außen.

> **TL;DR (EN):**  
> Append-only logs, structured events, local KPIs/replay; zero outbound telemetry.

---

## Prinzipien

- **Lokal & offline**: keine Cloud-Backhauls, Ports minimal.  
- **Strukturiert**: einheitliches Schema für `DecisionEvent`, `EnergyStateChangedEvent`, `DeadbandActivatedEvent`, `ExplainSession`.  
- **Append-only**: Auditierbarkeit, Reproduzierbarkeit, Hashes für Exporte.  
- **Versioniert**: YAML-Configs, Prompt-Versionen, UI-Microcopy.  
- **Privacy-by-Default**: Research-Exports nur mit Toggle (Opt-in); Pseudonymisierung.

---

## Ablage

- `data/bitgrid.sqlite` (Timeline, States, KPIs)  
- `data/parquet/*.parq` (Langzeit-Logs & Replay)  
- `config/*.yaml` (Rules, Flags, Policies)  
- `explain/*.json` (ExplainSessions, Prompt-Versionen)

---

## Tracing Hooks

- MQTT Topics: `energy/state/#`, `miner/state/#`, `explain/events/#`.  
- REST: `GET /state`, `/timeline`, `/preview`, `POST /override`, `/decisions`.  
- UI Events: `toast_shown`, `override_enter/exit`, `export_reason`.

> Structured, local traces keep decisions auditable and research-ready.
