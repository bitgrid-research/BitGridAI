# Simulation mit Realdaten

Dieses Dokument beschreibt wie man exportierte HA-Daten in der Simulation ausführt und die Ergebnisse interpretiert.

Voraussetzung: CSV-Datei wurde mit `ha_export_scenario.py` erstellt (siehe [REALDATEN.md](REALDATEN.md)).

---

## Zwei Modi

| Modus | Befehl | Wann verwenden |
|---|---|---|
| **Runner** | `python -m src.sim.runner` | Echtzeit-ähnlich, mit Wartezeit zwischen Blöcken |
| **Replay** | `python -m src.sim.replay` | Schnell, deterministisch, für Analyse und Tests |

Für die Arbeit mit Realdaten ist **Replay** der richtige Einstieg.

---

## Replay — Szenario durchlaufen

```bash
python -m src.sim.replay --scenario src/sim/scenarios/real_2026-04-20.csv
```

### Ausgabe (JSON-Array)

```json
[
  {
    "block_id": "2026-04-20T00:00:00",
    "action": "STOP",
    "decision_code": "STOP_R2_SOC_LOW",
    "reason": "SOC_BELOW_THRESHOLD"
  },
  {
    "block_id": "2026-04-20T06:10:00",
    "action": "START",
    "decision_code": "START_R1_SURPLUS",
    "reason": "SURPLUS_OK"
  },
  ...
]
```

### Ausgabe in Datei speichern

```bash
python -m src.sim.replay --scenario src/sim/scenarios/real_2026-04-20.csv \
  > results/replay_2026-04-20.json
```

### Alle Entscheidungen auf einen Blick

```bash
python -m src.sim.replay --scenario src/sim/scenarios/real_2026-04-20.csv \
  | python -c "import json,sys; [print(r['block_id'], r['action'], r['decision_code']) for r in json.load(sys.stdin)]"
```

---

## Runner — zeitgesteuert (optional)

```bash
# 1x Echtzeit: 1 Block = 10 Minuten Wartezeit
python -m src.sim.runner --scenario src/sim/scenarios/real_2026-04-20.csv --speed 1

# 60x schneller: 1 Block = 10 Sekunden
python -m src.sim.runner --scenario src/sim/scenarios/real_2026-04-20.csv --speed 60

# Maximale Geschwindigkeit ohne Wartezeit
python -m src.sim.runner --scenario src/sim/scenarios/real_2026-04-20.csv --speed 99999
```

### Runner-Ausgabe (eine Zeile pro Block)

```json
{"block": 1, "block_id": "2026-04-20T00:00:00", "pv_kw": 0.0, "surplus_kw": -0.42, "soc_pct": 82.5, "temp_c": 35.1, "action": "STOP", "code": "STOP_R2_SOC_LOW"}
{"block": 37, "block_id": "2026-04-20T06:00:00", "pv_kw": 1.2, "surplus_kw": 0.38, "soc_pct": 91.0, "temp_c": 36.2, "action": "NOOP", "code": "NOOP_R4_FORECAST_LOW"}
```

---

## Entscheidungscodes verstehen

| Präfix | Regel | Bedeutung |
|---|---|---|
| `START_R1_*` | R1 Profitabilität | Mining startet wegen Überschuss |
| `STOP_R2_SOC_LOW` | R2 Autarkie | Akku zu leer |
| `STOP_R2_GRID_IMPORT` | R2 Autarkie | Netzbezug zu hoch |
| `STOP_R3_OVERTEMP` | R3 Sicherheit | Miner zu heiß |
| `STOP_R3_HEARTBEAT` | R3 Sicherheit | Miner nicht erreichbar |
| `NOOP_R4_FORECAST_LOW` | R4 Prognose | PV-Forecast zu gering |
| `NOOP_R5_DEADBAND` | R5 Stabilität | Zu früh nach letzter Änderung |

---

## Szenarien vergleichen

Zwei Tage gegenüberstellen:

```bash
python -m src.sim.replay --scenario src/sim/scenarios/real_2026-04-20.csv > /tmp/a.json
python -m src.sim.replay --scenario src/sim/scenarios/real_2026-04-21.csv > /tmp/b.json

# Anzahl Mining-Starts pro Tag
python -c "import json; d=json.load(open('/tmp/a.json')); print('Starts:', sum(1 for r in d if r['action']=='START'))"
```

Mining-Uptime in Stunden aus einem Replay berechnen:

```bash
python -c "
import json, sys
d = json.load(open('results/replay_2026-04-20.json'))
running = sum(1 for r in d if r['action'] in ('START', 'NOOP') and 'STOP' not in r['decision_code'])
print(f'Uptime: {running * 10 / 60:.1f} h von {len(d) * 10 / 60:.0f} h')
"
```

---

## Szenario manuell anpassen

Manchmal lohnt es sich ein exportiertes CSV gezielt zu verändern, um Grenzfälle zu testen:

### Akku-Stresstest: SoC auf 15% absenken

```bash
# Spalte 4 (battery_soc_pct) für alle Blöcke auf 15 setzen
python -c "
import csv, sys

with open('src/sim/scenarios/real_2026-04-20.csv') as f:
    lines = f.readlines()

with open('src/sim/scenarios/stress_soc_low.csv', 'w') as f:
    for line in lines:
        if line.startswith('#'):
            f.write(line)
            continue
        parts = line.strip().split(',')
        parts[4] = '15.0'
        f.write(','.join(parts) + '\n')
"
python -m src.sim.replay --scenario src/sim/scenarios/stress_soc_low.csv
```

### Miner-Ausfall simulieren: Heartbeat auf 120s setzen

```bash
# Ab Block 50 (Minute 500) den Heartbeat auf 120 sec setzen
python -c "
with open('src/sim/scenarios/real_2026-04-20.csv') as f:
    lines = f.readlines()
with open('src/sim/scenarios/stress_heartbeat.csv', 'w') as f:
    for line in lines:
        if line.startswith('#'):
            f.write(line); continue
        parts = line.strip().split(',')
        if int(parts[0]) >= 500:
            parts[6] = '120.0'
        f.write(','.join(parts) + '\n')
"
```

### Überhitzung simulieren: Miner-Temp auf 88°C

```bash
sed 's/^\([^#][^,]*,[^,]*,[^,]*,[^,]*,[^,]*,\)[^,]*/\188.0/' \
  src/sim/scenarios/real_2026-04-20.csv \
  > src/sim/scenarios/stress_overtemp.csv
```

---

## Häufige Probleme

**Alle Entscheidungen sind `STOP_R2_SOC_LOW`**
→ `battery_soc_pct` ist leer (Sensor hatte keinen Wert). Spalte 4 im CSV prüfen.

**`miner_temp_c` überall leer**
→ Miner war offline an diesem Tag — `miner_heartbeat_age_sec` auf `120` bleibt, R3 greift.

**Zu viele `NOOP_R5_DEADBAND`**
→ Normal bei kurzen Szenarien — R5 erzwingt mindestens 3 Blöcke Laufzeit und 2 Blöcke Pause.

**Script findet Sensor nicht**
→ Entity-ID hat sich geändert. Im Script `ENTITIES`-Dict in `scripts/ha_export_scenario.py` anpassen.
