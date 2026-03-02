# Home Assistant Simulation - Ablauf (Template)

Kurz und pragmatisch: Dieses Dokument dient als Arbeitsplan und Checkliste, um die
regelbasierte BitGridAI-Logik in Home Assistant als Simulation aufzubauen.

## Ziele

- Regelwerk R1-R5 in Home Assistant abbilden.
- Entscheidungsgruende als erklaerbare Texte ausgeben.
- Relais/LED als physisches Feedback integrieren.
- Reproduzierbare Simulation (manuell oder Replay).

## Annahmen und Scope

- Entscheidungslogik ist deterministisch und blockbasiert (z. B. 10-Minuten-Takt).
- R3 (Safety) darf asynchron uebersteuern.
- Es gibt keine Cloud-Abhaengigkeit fuer die Kernlogik.

## Datenmodell (Entitaeten)

### Sensoren (Pflichtsignale)

- `sensor.pv_power_w`
- `sensor.house_load_w`
- `sensor.grid_import_w`
- `sensor.battery_soc_pct`
- `sensor.miner_temp_c`
- `sensor.miner_heartbeat_age_sec`
- `sensor.miner_status`

### Sensoren (Optional / Optimierung)

- `sensor.grid_export_w` (optional)
- `sensor.battery_charge_w` (optional)
- `sensor.battery_discharge_w` (optional)
- `sensor.energy_price_ct_kwh` (optional)
- `sensor.price_forecast_max_ct_kwh` (optional)
- `sensor.pv_forecast_kw` (optional)
- `sensor.forecast_updated_at` (optional)

### Abgeleitete Werte / EnergyState

- `sensor.surplus_kw`
- `sensor.block_id`
- `sensor.block_start_ts` (optional)
- `sensor.block_window_start` (optional)
- `sensor.block_window_end` (optional)
- `sensor.energy_state_timestamp`
- `sensor.energy_state_quality` (ok/warn/error)
- `binary_sensor.telemetry_complete`
- `binary_sensor.energy_state_degraded`
- `sensor.missing_telemetry` (optional, text)
- `input_number.max_input_drift_sec` (optional)

### Parameter R1 (Start)

- `input_number.r1_surplus_min_kw`
- `input_number.r1_price_max_ct_kwh` (optional)

### Parameter R2 (Autarkie)

- `input_number.r2_soc_soft_min_pct`
- `input_number.r2_soc_hard_min_pct`
- `input_number.r2_max_grid_import_w`

### Parameter R3 (Safety)

- `input_number.r3_max_chip_temp_c`
- `input_number.r3_t_resume_c` (optional)
- `input_number.r3_comm_timeout_sec`
- `input_number.r3_safety_lockout_min`
- `input_boolean.r3_emergency_stop` (optional)

### Parameter R4 (Forecast)

- `input_number.r4_forecast_lookahead_min`
- `input_number.r4_min_predicted_surplus_kw`
- `input_number.r4_price_spike_threshold_ct`

### Parameter R5 (Deadband/Stabilitaet)

- `input_number.r5_deadband_hold_blocks`
- `input_number.r5_min_runtime_blocks`
- `input_number.r5_min_pause_blocks`
- `input_number.r5_max_grid_import_deadband_w` (optional)
- `input_select.r5_force_unlock_rules` (R2, R3)

### Override / Autonomie

- `input_boolean.override_active`
- `input_select.override_action` (START, STOP, THROTTLE)
- `input_number.override_duration_min`
- `input_number.default_override_duration_min`
- `input_number.max_override_duration_min`
- `input_boolean.allow_unsafe_override` (hardcoded false)
- `input_datetime.override_created_at`
- `input_datetime.override_valid_until`
- `input_text.override_command_id`
- `input_text.override_status` (accepted/rejected/expired)
- `input_select.autonomy_level` (MANUAL, ASSIST, SEMI_AUTO, AUTO)
- `input_number.default_autonomy_level`
- `input_number.min_autonomy_level`
- `input_number.max_autonomy_level`
- `input_boolean.allow_level_change_runtime`

### System / Takt

- `input_number.block_minutes` (default 10)
- `input_number.block_grace_period_sec` (optional)
- `input_select.system_state` (OFF, ARMED, RUNNING, THROTTLED, COOLDOWN, LOCKOUT, SAFE_MODE, ERROR)
- `input_select.decision_action` (START, STOP, THROTTLE, NOOP)
- `input_datetime.deadband_valid_until`
- `input_datetime.decision_timestamp`
- `input_datetime.last_start_at`
- `input_datetime.last_stop_at`
- `input_datetime.safety_lockout_until`
- `binary_sensor.safety_lockout_active`
- `binary_sensor.scheduler_ok` (optional)
- `sensor.scheduler_health` (optional)
- `sensor.time_source` (optional)

### Simulation / Replay

- `input_boolean.simulation_mode`
- `input_boolean.replay_mode`
- `input_text.replay_source`
- `input_number.replay_speed` (optional)

### Health / Betrieb (Optional)

- `binary_sensor.system_ready`
- `sensor.core_health` (ok/warn/error)
- `binary_sensor.mqtt_ok`
- `binary_sensor.db_ok`
- `binary_sensor.config_ok`
- `sensor.config_version`
- `sensor.config_reload_status` (success/failed)
- `input_datetime.config_reload_at`
- `sensor.storage_free_mb`
- `input_number.retention_days`
- `sensor.auth_failed_count`
- `sensor.rate_limited_count`
- `sensor.last_auth_error_at`
- `sensor.last_rate_limit_at`

### Aktoren (Simulation / Hardware)

- `switch.miner_relay` (virtuell oder ESPHome/MQTT)
- `light.reserve_led` (optional)
- `light.safety_led` (optional)

## Regeln R1-R5 (Template-Sensoren)

- `binary_sensor.r1_surplus_ok`
- `binary_sensor.r1_price_ok` (optional)
- `binary_sensor.r1_start_ok` (kombiniert)
- `binary_sensor.r2_soc_soft`
- `binary_sensor.r2_soc_hard`
- `binary_sensor.r2_grid_import_ok`
- `binary_sensor.r3_overtemp`
- `binary_sensor.r3_comm_timeout`
- `binary_sensor.r3_emergency_stop`
- `binary_sensor.r3_safety_override` (kombiniert)
- `binary_sensor.r4_forecast_ok`
- `binary_sensor.r4_forecast_block`
- `binary_sensor.r5_deadband_active`
- `sensor.r5_valid_until`

## Entscheidungslogik (Block)

- Trigger: alle 10 Minuten (oder konfigurierbar).
- Logik: R3 hat Prioritaet, danach R2, dann R4, R5, R1.
- Ergebnis in `input_select.decision_action` speichern.
- Systemzustand in `input_select.system_state` aktualisieren.
- `valid_until` (Deadband) setzen und in `input_datetime.deadband_valid_until` ablegen.
- `DecisionEvent` Felder pflegen: `reason`, `trigger`, `params`, `valid_until`, `command_id`.

## Erklaerungsmodell (Textbausteine)

- `sensor.decision_reason` (Kurzgrund)
- `sensor.decision_trigger` (Ausloeser)
- `sensor.decision_params` (JSON, optional)
- `sensor.decision_code` (z. B. NOOP_R4_BLOCKED_R5_ACTIVE)
- `sensor.rule_states` (JSON oder komprimiert)
- `sensor.decision_valid_until`
- `sensor.decision_event_id` (optional)
- `sensor.decision_block_id` (optional)
- `sensor.decision_explanation` (kompakte Erklaerung)
- Mapping folgt festen Textbausteinen aus R1-R5.

## UI-Blueprint (Dashboard)

1. Energiefluss (PV, Haus, Speicher, Miner, Netz)
2. Decision Card (Aktion + Grund + Datenbasis)
3. Kontrolle (Override, Deadbands, Modi)

## Preview / What-if (Optional)

- `input_boolean.preview_mode`
- `input_text.preview_input_json`
- `sensor.preview_decision_action`
- `sensor.preview_decision_reason`
- `sensor.preview_decision_code`
- `sensor.preview_cached_at`

## Simulationsmodus

- Manuelle Slider (`input_number`) fuer PV/Last/SoC.
- Optionaler CSV-Feed fuer Replays.
- Logging aktiv (Logbook + Recorder).

## Research / Export (Optional)

- `input_boolean.research_opt_in`
- `input_text.export_status`
- `input_text.export_hash`
- `input_text.export_manifest_ref`
- `input_text.export_scope`
- `input_datetime.export_requested_at`

## Testszenarien (Auszug)

- SH-1: stabiler Ueberschuss (Start + lange Laufphase)
- SH-2: wechselhafte PV (NOOP + Ruhezeiten)
- SH-3: SoC kritisch (Stop, Start blockiert)
- Safety: Uebertemperatur -> R3-Stop

## KPIs (Optional)

- `sensor.kpi_decision_latency_ms`
- `sensor.kpi_explanation_latency_ms`
- `sensor.kpi_thermal_incidents`
- `sensor.kpi_flapping_rate`
- `sensor.kpi_grid_import_wh`
- `sensor.kpi_explainability_coverage`

## Artefakte

- Regelmatrix (R1-R5 + Schwellen + Prioritaet)
- Testprotokolle (Szenarien + Erwartung + Ist)
- Aufbau- und Integrationsdoku (Hardware + Wiring + HA-Konfig)

## Offene Punkte

- Taktfrequenz fuer Entscheidungen (5/10/15 Minuten)
- Fehlerszenarien (Sensor-Ausfall, MQTT-Down)
- UI-Detailtiefe (wieviel Begruendung im Default-View)
