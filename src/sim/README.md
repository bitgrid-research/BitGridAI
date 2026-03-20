# src/sim

Simulation und Replay von Szenarien — ohne physische Hardware.

Simulation ersetzt reale Messwerte durch kontrollierte Datenquellen. Replay spielt historische `EnergyState`-Snapshots deterministisch nach und erzeugt Entscheidungen neu. Beide Modi lassen sich in Home Assistant (Slider) oder CLI (CSV-Feed) betreiben.

---

## Verzeichnisstruktur

```
sim/
├── runner.py              # Haupt-Einstieg: Sim-Loop oder Replay
├── scenario_loader.py     # CSV/JSON-Szenarien einlesen und validieren
├── state_injector.py      # EnergyState-Frames über MQTT oder direkt injizieren
├── replay.py              # Historische EnergyStates re-evaluieren
├── scenarios/
│   ├── sh1_stable_surplus.csv      # SH-1: stabiler Überschuss → Start + Laufphase
│   ├── sh2_variable_pv.csv         # SH-2: wechselhafte PV → NOOP + Ruhezeiten
│   ├── sh3_soc_critical.csv        # SH-3: SoC kritisch → Stop, Start blockiert
│   └── sh4_safety_overtemp.csv     # SH-4: Übertemperatur → R3-Stop
└── fixtures/
    ├── state_nominal.json           # Normalbetrieb (alle Signale, quality=ok)
    ├── state_degraded.json          # Fehlende Signale (quality=warn)
    └── state_safety_triggered.json  # R3 aktiv (miner_temp_c > 85)
```

---

## Szenario-Format (`scenarios/*.csv`)

```csv
# Spalten: timestamp_offset_min, pv_power_w, house_load_w, grid_import_w,
#          battery_soc_pct, miner_temp_c, miner_heartbeat_age_sec,
#          energy_price_ct_kwh, pv_forecast_kw
# Leerzeilen und #-Kommentare werden ignoriert

0,   3200, 800,  0,   80, 42, 5,  8.2, 3.1
10,  3400, 850,  0,   78, 43, 5,  8.1, 3.2
20,  1200, 900, 300,  75, 44, 5,  9.0, 1.5
30,     0, 950, 950,  72, 45, 5, 12.0, 0.0
```

**Pflichtfelder:** `pv_power_w`, `house_load_w`, `grid_import_w`, `battery_soc_pct`, `miner_temp_c`, `miner_heartbeat_age_sec`

Optionale Felder können leer bleiben — `energy_context` behandelt sie als `None`.

---

## Fixture-Format (`fixtures/*.json`)

Serialisierte `EnergyState`-Objekte für deterministische Unit-Tests:

```json
{
  "block_id": "2024-01-15T10:00:00",
  "window_start": "2024-01-15T10:00:00Z",
  "window_end": "2024-01-15T10:10:00Z",
  "pv_power_w": 3200.0,
  "house_load_w": 800.0,
  "grid_import_w": 0.0,
  "battery_soc_pct": 80.0,
  "miner_temp_c": 42.0,
  "miner_heartbeat_age_sec": 5.0,
  "surplus_kw": 2.4,
  "quality": "ok",
  "missing_signals": []
}
```

---

## Betriebsmodi

### CLI-Simulation (CSV-Feed)

```bash
python -m sim.runner --scenario scenarios/sh1_stable_surplus.csv --speed 10
# --speed 10 = 10-fache Echtzeit, jeder 10-Minuten-Block in 1 Minute
```

### Replay (Regression)

```bash
python -m sim.replay --fixture fixtures/state_nominal.json
# Gibt DecisionEvent als JSON aus → vergleichbar mit gespeichertem Baseline
```

### Home Assistant (Slider-Modus)

HA liest `input_boolean.simulation_mode` aus `src/ha/`. Im Sim-Modus werden `input_number.*`-Slider-Werte als Messwerte genutzt statt MQTT.

---

## Testszenarien (Erwartungen)

| Szenario | Erwartete Entscheidungsfolge |
|---|---|
| SH-1: Stabiler Überschuss | `START` → `NOOP` (Deadband) → `NOOP` → ... |
| SH-2: Wechselhafte PV | `START` → `NOOP` (R5-Hold) → `STOP` → `NOOP` |
| SH-3: SoC kritisch | `STOP` (R2-Hard) → `NOOP` → `NOOP` |
| SH-4: Übertemperatur | `STOP` (R3, async) → `NOOP` (Lockout) |

Erwartungen als parametrisierte Tests: `tests/sim/test_scenarios.py`

---

## Konventionen

**Read-only:** Replay und Simulation verändern nie den Live-MQTT-Broker oder die Produktions-DB. Alle Ausgaben gehen in separate Topics (`bitgrid/sim/*`) oder Dateien.

**Zeitkontrolle:** `runner.py` stellt eine injizierbare `SimClock` bereit, die die echte Systemuhr ersetzt. Kein `time.sleep()` in Core-Code — immer die injizierte Clock nutzen.

**Reproduzierbarkeit:** Jede Simulation hat eine `seed`-Option für zufällige Variationen. Mit gleichem Seed: gleicher Output.

---

## Nächste Schritte

- [ ] `scenarios/sh1_stable_surplus.csv` — erstes Szenario
- [ ] `scenarios/sh3_soc_critical.csv` — R2-Grenzfall
- [ ] `scenarios/sh4_safety_overtemp.csv` — R3-Grenzfall
- [ ] `fixtures/state_nominal.json` — Basis-Fixture für Unit-Tests
- [ ] `runner.py` — CSV-Feed mit konfigurierbarer Geschwindigkeit
- [ ] `replay.py` — Deterministic Re-evaluation mit Baseline-Vergleich
