# src/ha

Home Assistant: YAML-Konfigurationen, Templates, Automationen und Dashboards.

`src/ha/` bildet das gesamte Regelwerk R1–R5 als HA-Template-Sensoren ab und stellt die primäre UI für Simulation und Betrieb bereit. Kein Python — nur HA-YAML.

Vollständiges Datenmodell und Ablaufplan: [procedure.md](./procedure.md)

---

## Verzeichnisstruktur (geplant)

```
ha/
├── procedure.md               # Arbeitsplan + vollständiges Entity-Listing
├── docker-compose.yml         # HA + MQTT-Broker für lokale Entwicklung
└── config/
    ├── configuration.yaml     # Haupt-Config (include-Wurzel)
    ├── helpers.yaml           # input_number, input_boolean, input_select, input_datetime
    ├── template_sensors.yaml  # binary_sensor.r1_* bis r5_*, sensor.surplus_kw, ...
    ├── automations/
    │   ├── decision_loop.yaml     # 10-Minuten-Takt → Entscheidungslogik R1–R5
    │   ├── safety_async.yaml      # R3 asynchron (sofort bei Übertemperatur)
    │   ├── override_handler.yaml  # Override-Timeout, Ablauf, Expiry
    │   └── config_reload.yaml     # Config-Reload-Trigger
    └── dashboards/
        ├── energy_flow.yaml       # PV / Haus / Speicher / Miner / Netz
        ├── decision_card.yaml     # Aktion + Grund + Datenbasis
        └── control_panel.yaml    # Override, Deadbands, Autonomie-Level
```

---

## Pflicht-Entitäten (Kurzübersicht)

Vollständige Liste → [procedure.md](./procedure.md)

### Sensor-Inputs (via MQTT oder Simulation-Slider)

| Entität | Signal | Pflicht |
|---|---|---|
| `sensor.pv_power_w` | PV-Leistung | ja |
| `sensor.house_load_w` | Hausverbrauch | ja |
| `sensor.grid_import_w` | Netzbezug | ja |
| `sensor.battery_soc_pct` | Ladezustand Batterie | ja |
| `sensor.miner_temp_c` | Miner-Temperatur | ja |
| `sensor.miner_heartbeat_age_sec` | Kommunikationsalter | ja |
| `sensor.energy_price_ct_kwh` | Strompreis | optional |
| `sensor.pv_forecast_kw` | PV-Prognose | optional |

### Abgeleitete Werte

| Entität | Beschreibung |
|---|---|
| `sensor.surplus_kw` | `(pv_power_w - house_load_w) / 1000` |
| `sensor.block_id` | Aktuelles 10-Minuten-Fenster |
| `binary_sensor.telemetry_complete` | Alle Pflicht-Signale vorhanden |
| `binary_sensor.energy_state_degraded` | Mindestens ein Pflicht-Signal fehlt |

### Regel-Sensoren

| Entität | Regel |
|---|---|
| `binary_sensor.r1_start_ok` | R1: Surplus + Preis OK |
| `binary_sensor.r2_soc_soft` | R2: SoC über Soft-Minimum |
| `binary_sensor.r2_soc_hard` | R2: SoC über Hard-Minimum |
| `binary_sensor.r3_safety_override` | R3: Übertemperatur oder Timeout → STOP sofort |
| `binary_sensor.r4_forecast_ok` | R4: Prognose erlaubt Start |
| `binary_sensor.r5_deadband_active` | R5: Deadband-Haltezeit aktiv |

### Entscheidung und Erklärung

| Entität | Beschreibung |
|---|---|
| `input_select.decision_action` | `START` / `STOP` / `THROTTLE` / `NOOP` |
| `input_select.system_state` | `OFF` / `ARMED` / `RUNNING` / `COOLDOWN` / `LOCKOUT` / `SAFE_MODE` |
| `sensor.decision_code` | z.B. `STOP_R3_OVERTEMP` |
| `sensor.decision_explanation` | Kurztext für UI-Card |
| `input_datetime.deadband_valid_until` | Ende der Deadband-Periode |

---

## Entscheidungs-Logik (`decision_loop.yaml`)

Priorität: **R3 > R2 > R5 > R4 > R1**

```
1. R3 aktiv?          → STOP sofort (nie überstimmbar)
2. R2 Hard-Min?       → STOP
3. R5 Deadband aktiv? → NOOP (keine Änderung)
4. R4 blockiert?      → NOOP
5. R1 Start-OK?       → START
6. sonst              → NOOP
```

R3 läuft zusätzlich als separate asynchrone Automation (`safety_async.yaml`) — reagiert sofort, nicht erst beim nächsten Block-Tick.

---

## Entwicklungsumgebung

```bash
cd src/ha
docker-compose up -d    # HA + Mosquitto MQTT lokal
```

Simulation ohne Hardware: `input_boolean.simulation_mode` auf `true` → `input_number.*`-Slider statt MQTT-Topics.

---

## Nächste Schritte

- [ ] `config/helpers.yaml` — alle `input_*`-Entitäten aus procedure.md
- [ ] `config/template_sensors.yaml` — `sensor.surplus_kw`, `binary_sensor.r1_*` bis `r5_*`
- [ ] `config/automations/decision_loop.yaml` — 10-Minuten-Takt + R1–R5-Logik
- [ ] `config/automations/safety_async.yaml` — R3 asynchron
- [ ] `config/dashboards/energy_flow.yaml` — Energiefluss-Übersicht
- [ ] `config/dashboards/decision_card.yaml` — Decision + Explain
- [ ] Simulation-Modus testen (SH-1 bis SH-4 aus `src/sim/`)
