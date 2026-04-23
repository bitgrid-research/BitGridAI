# Reale HA-Daten als Simulationsszenario

Dieses Dokument beschreibt wie man aus der Home Assistant Datenbank echte Messdaten exportiert und als Simulationsszenario verwendet.

## Voraussetzungen

- SSH-Zugang zum Umbrel (`umbrel@192.168.178.62`)
- Python 3.11+ lokal installiert
- Repo ausgecheckt, Virtual Environment aktiv

## Schritt 1: Datenbank vom Umbrel holen

Die HA-SQLite-Datenbank liegt auf dem Umbrel-Host. Lokale Kopie erstellen:

```bash
scp umbrel@umbrel.local:~/umbrel/app-data/home-assistant/data/home-assistant_v2.db /tmp/ha.db
```

> Die DB ist read-only — das Script schreibt nie zurück.

## Schritt 2: Szenario exportieren

```bash
# Einzelner Tag
python scripts/ha_export_scenario.py \
  --db /tmp/ha.db \
  --start 2026-04-20 \
  --out src/sim/scenarios/real_2026-04-20.csv

# Ganzer Monat
python scripts/ha_export_scenario.py \
  --db /tmp/ha.db \
  --start 2026-04-01 \
  --end 2026-05-01 \
  --out src/sim/scenarios/real_april_2026.csv

# Standard-Output (kein --out): src/sim/scenarios/real_<start>.csv
python scripts/ha_export_scenario.py --db /tmp/ha.db --start 2026-04-20
```

### Ausgabe des Scripts

```
→ DB:       /tmp/ha.db
→ Zeitraum: 2026-04-20 – 2026-04-20
→ Ausgabe:  src/sim/scenarios/real_2026-04-20.csv
→ Schema:   new
→ Sensoren gefunden (8/8):
     ✓ sensor.pv_power_w              (144 Messpunkte)
     ✓ sensor.house_load_w            (144 Messpunkte)
     ✓ sensor.grid_import_w           (143 Messpunkte)
     ✓ sensor.grid_export_w           (98 Messpunkte)
     ✓ sensor.battery_soc_pct         (144 Messpunkte)
     ✓ sensor.miner_total_power_w     (132 Messpunkte)
     ✓ sensor.miner_max_chip_temp_c   (132 Messpunkte)
     ✓ sensor.ac_elwa_2_..._power1_solar (67 Messpunkte)
✓ 144 Blöcke exportiert → src/sim/scenarios/real_2026-04-20.csv
```

## Schritt 3: Szenario-CSV prüfen

```bash
head -5 src/sim/scenarios/real_2026-04-20.csv
```

```
# Exportiert aus HA-History: 2026-04-20 – 2026-04-20
# Blöcke gesamt: 144  davon befüllt: 138
# timestamp_offset_min, pv_power_w, house_load_w, grid_import_w, battery_soc_pct, ...
0,0.00,420.30,410.20,82.50,35.10,5.0,,,0.00,0.00,1200.00
10,0.00,385.00,380.00,83.10,35.20,5.0,,,0.00,0.00,980.00
```

### Was leer bleibt (normal)

| Spalte | Warum leer |
|---|---|
| `energy_price_ct_kwh` | Kein Strompreis-Feed in HA — manuell ergänzen wenn gewünscht |
| `pv_forecast_kw` | Forecast ist in HA nicht historisch gespeichert |
| Lücken bei Sensorausfall | Werden per Forward-Fill geschlossen |

## Schritt 4: Szenario in der Simulation ausführen

```bash
python -m src.sim.runner src/sim/scenarios/real_2026-04-20.csv
```

Oder im Replay-Modus (deterministisch, ohne Seiteneffekte):

```bash
python -m src.sim.replay src/sim/scenarios/real_2026-04-20.csv
```

## Spaltenformat (vollständig)

| # | Spalte | Einheit | Pflicht | Quelle |
|---|---|---|---|---|
| 0 | `timestamp_offset_min` | min | Ja | berechnet |
| 1 | `pv_power_w` | W | Ja | `sensor.pv_power_w` |
| 2 | `house_load_w` | W | Ja | `sensor.house_load_w` |
| 3 | `grid_import_w` | W | Ja | `sensor.grid_import_w` |
| 4 | `battery_soc_pct` | % | Ja | `sensor.battery_soc_pct` |
| 5 | `miner_temp_c` | °C | Ja | `sensor.miner_max_chip_temp_c` |
| 6 | `miner_heartbeat_age_sec` | s | Ja | Default 5.0 (gesund) |
| 7 | `energy_price_ct_kwh` | ct/kWh | Nein | — leer lassen oder manuell |
| 8 | `pv_forecast_kw` | kW | Nein | — leer lassen |
| 9 | `grid_export_w` | W | Nein | `sensor.grid_export_w` |
| 10 | `miner_power_w` | W | Nein | `sensor.miner_total_power_w` |
| 11 | `heizstab_power_w` | W | Nein | `sensor.ac_elwa_2_..._power1_solar` |

## Typische Szenarien bauen

### Sonniger Sommertag mit viel PV

```bash
python scripts/ha_export_scenario.py --db /tmp/ha.db --start 2026-06-21
```

### Bewölkter Tag mit Netzbezug

Tage mit hohem `grid_import_w` und niedrigem `pv_power_w` suchen:

```bash
# DB direkt abfragen (Tage mit Netzbezug > 5 kWh)
sqlite3 /tmp/ha.db "
  SELECT date(datetime(last_updated_ts, 'unixepoch')), round(sum(state)/6,1) as kwh
  FROM states s JOIN states_meta m ON s.metadata_id = m.metadata_id
  WHERE m.entity_id = 'sensor.grid_import_w'
    AND state NOT IN ('unknown','unavailable')
    AND last_updated_ts > unixepoch('2026-01-01')
  GROUP BY 1 HAVING kwh > 5 ORDER BY kwh DESC LIMIT 10
"
```

### Akku-Stresstest (niedriger SoC)

```bash
# Tage mit minimalem SoC < 20%
sqlite3 /tmp/ha.db "
  SELECT date(datetime(last_updated_ts, 'unixepoch')), round(min(state),1) as min_soc
  FROM states s JOIN states_meta m ON s.metadata_id = m.metadata_id
  WHERE m.entity_id = 'sensor.battery_soc_pct'
    AND state NOT IN ('unknown','unavailable')
    AND last_updated_ts > unixepoch('2026-01-01')
  GROUP BY 1 HAVING min_soc < 20 ORDER BY min_soc ASC LIMIT 10
"
```

## Hinweise für den Mitarbeiter

- **Resampling:** Das Script mittelt alle Messwerte auf 10-Minuten-Blöcke (gleicher Takt wie der Core)
- **Forward-Fill:** Fehlende Blöcke (Sensor offline, HA-Neustart) werden mit dem letzten bekannten Wert gefüllt — das CSV hat immer lückenlose Blöcke
- **Heartbeat:** `miner_heartbeat_age_sec` ist in HA nicht historisch — wird auf `5.0` (gesund) gesetzt; für Ausfall-Tests manuell auf `> 60` setzen
- **Mehrere Tage:** Ein Monats-CSV hat 144 × 30 = 4320 Blöcke — für Langzeittests geeignet
- **Kommentarzeilen** (mit `#`) werden vom `ScenarioLoader` ignoriert
