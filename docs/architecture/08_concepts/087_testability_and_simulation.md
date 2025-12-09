# 087 – Testbarkeit & Simulation

> **Kurzüberblick:**  
> Deterministische Regeln (**R1–R5**) + **Replay-Runner** ermöglichen reproduzierbare Tests (Unit, Integration, Field-Replay). KPIs messen Wirkung (Flapping↓, Grid-Import↓, Explanation Coverage).

> **TL;DR (EN):**  
> Deterministic rules + replay runner enable reproducible unit/integration/field tests; KPIs track impact.

---

## Test-Arten

- **Unit-Tests**: Regeln R1–R5, Schwellen/Hysterese, Priority (R3>R2>R5>R1/R4).  
- **Integration (MQTT/REST)**: Topics/Endpoints → Decision → Actuation → UI Events.  
- **Replay-Tests**: Parquet/SQLite-Logs in Echtzeit oder beschleunigt abspielen.  
- **A/B-Tuning**: Deadband-Längen, Forecast-Margins, Hodl-Policies gegen Baseline vergleichen.

---

## Werkzeuge & Artefakte

- **bitgrid-replay** CLI (`--state data/parquet/*.parq --config config/rules.yaml --speed 10x`).  
- **KPI-Runner**: Flapping-Rate, Grid-Import, Explanation-Coverage, Trust-Proxy.  
- **Fault-Injection**: Sensor-Stale, Broker-Down, Heat-Events (siehe Runbooks).  
- **Feature-Flags**: `r4_enabled`, `research_mode`, `energy_path_policy`.

---

## Erfolgskriterien (Beispiele)

- Decision Latency < 300 ms nach Block-Tick.  
- Explanation Latency < 2 s nach DecisionEvent.  
- Flapping ↓ ggü. Baseline; Thermal Incidents = 0.  
- Replay ergibt identische Decisions für gleiche Inputs (Determinismus).

> Testability is built-in via deterministic rules, structured logs, and replayable data.
