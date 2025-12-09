# 084 – Plausibilitäts- & Validitätsprüfungen

> **Kurzüberblick:**  
> Mess- und Prognosedaten werden **lokal geprüft**: Schwellen, Hysterese, Confidence, Stale-Erkennung. Nur valide Frames fließen in **EnergyState** und damit in **R1–R5** ein.

> **TL;DR (EN):**  
> Local validation of measurements/forecasts: thresholds, hysteresis, confidence, stale detection; only valid frames enter EnergyState.

---

## Checks (Auswahl)

- **Sensor-Stale & Lücken**: fehlende Frames markieren State als unsicher → **hold** statt **start**; Health-Banner.  
- **Range-Prüfungen**: `p_pv_kw`, `p_load_kw`, `soc_pct`, `t_miner_c` gegen plausible Min/Max.  
- **Hysterese**: `t_stop_c / t_resume_c`, `soc_stop_pct / soc_resume_pct` vermeiden Ping-Pong.  
- **Forecast-Qualität (R4)**: `forecast_confidence ≥ 0.7`, Konsistenz über n Blöcke, Margin (z. B. +0.3 kW).  
- **Deadband (R5)**: validiert Stabilität um Schwellen, reduziert Flapping.  
- **Adapter-Heartbeat**: MQTT/REST-Adapter melden Liveness; Circuit-Breaker bei Fehlern.  
- **Config-Schema**: YAML-Validierung für Schwellen/Policies; Hash/Version in UI sichtbar.

> Validation keeps the deterministic rule path clean and predictable, prevents bad data from triggering actions.
