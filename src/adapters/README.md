# src/adapters

Adapter und I/O-Anbindung (MQTT, ESPHome, Modbus, REST).

Adapter übersetzen externe Signale in Domänenobjekte (`EnergyState`-Felder) und Aktor-Kommandos in Protokoll-spezifische Nachrichten. Der Core weiß nichts von MQTT oder ESPHome — er sieht nur `EnergyState`.

---

## Verzeichnisstruktur

```
adapters/
├── telemetry_ingest.py    # Eingehende Messwerte → normalisierte Felder
├── actuation_writer.py    # Decision → Aktor-Kommando (Relay, Switch)
├── health_monitor.py      # Verbindungs-Health, Timeout-Detection
├── mqtt_client.py         # MQTT-Verbindung, Subscribe/Publish
├── esphome_adapter.py     # ESPHome-spezifische Topics und Payloads
├── modbus_adapter.py      # Modbus-Polling (Wechselrichter, Batterie)
├── profiles/
│   ├── device_profiles.yaml   # Gerätespezifische Mappings (Einheiten, Topics)
│   └── topic_schema.yaml      # MQTT-Topic-Konventionen
└── __init__.py
```

---

## MQTT-Topic-Konvention (`profiles/topic_schema.yaml`)

```
bitgrid/{location}/{device}/{signal}

Beispiele:
  bitgrid/home/pv_inverter/power_w          → pv_power_w
  bitgrid/home/house_meter/import_w         → grid_import_w
  bitgrid/home/battery/soc_pct             → battery_soc_pct
  bitgrid/home/miner/temp_c               → miner_temp_c
  bitgrid/home/miner/heartbeat_age_sec    → miner_heartbeat_age_sec

Aktoren:
  bitgrid/home/miner/relay/set            → "ON" | "OFF"
  bitgrid/home/miner/relay/status         → "ON" | "OFF" | "ERROR"

Health:
  bitgrid/home/adapters/health            → JSON (siehe Health-Schema)
```

**Regel:** Alle Werte in SI-Einheiten (W, °C, %, s). Einheiten-Konversion passiert im Adapter, nie im Core.

---

## Payload-Schema

Alle eingehenden Payloads werden in dieses Format normalisiert:

```python
@dataclass
class TelemetryFrame:
    signal: str          # z.B. "pv_power_w"
    value: float
    timestamp: datetime  # UTC
    source: str          # z.B. "mqtt:bitgrid/home/pv_inverter/power_w"
    quality: Literal["ok", "stale", "error"]
```

Ausgehende Aktions-Kommandos:

```python
@dataclass
class ActuationCommand:
    target: str          # z.B. "miner_relay"
    action: str          # "ON" | "OFF" | "THROTTLE"
    command_id: str      # Echo des DecisionEvent.command_id
    source: str          # "bitgrid/core"
```

---

## Health-Schema (`health_monitor.py`)

```python
@dataclass
class AdapterHealth:
    adapter: str                          # "mqtt" | "esphome" | "modbus"
    status: Literal["ok", "warn", "error"]
    last_seen: datetime
    missing_signals: list[str]
    error_message: str | None
```

Health-Events werden als MQTT-Retained-Message publiziert:
```
bitgrid/home/adapters/health → {"adapter": "mqtt", "status": "ok", ...}
```

---

## Device-Profile (`profiles/device_profiles.yaml`)

Geräte-spezifische Konfiguration, um verschiedene Hardware zu unterstützen ohne Code-Änderung:

```yaml
devices:
  pv_inverter:
    type: esphome
    topic_prefix: "bitgrid/home/pv_inverter"
    signals:
      power_w:
        topic_suffix: "power_w"
        unit: "W"
        scale: 1.0        # Skalierungsfaktor falls nötig
        max_age_sec: 30   # Wert gilt als "stale" nach N Sekunden

  battery:
    type: modbus
    host: "192.168.1.100"
    port: 502
    registers:
      soc_pct:
        address: 0x0100
        type: uint16
        scale: 0.1
```

---

## Konventionen

**Kein Core-Import in Adaptern:** Adapter importieren nur `models.py`-Typen (`TelemetryFrame`, `ActuationCommand`). Niemals `rule_engine` oder `block_scheduler`.

**Stale-Detection:** Jedes Signal hat `max_age_sec` im Device-Profile. `health_monitor` markiert überfällige Signale als `quality="stale"` — `energy_context` reagiert mit `degraded`-Status.

**Idempotente Aktuation:** `actuation_writer` sendet bei gleichem `command_id` keine zweite Nachricht. Deduplizierung über In-Memory-Cache der letzten 10 `command_id`s.

**Retry-Logik:** Nur bei Verbindungsabbruch (Backoff: 1s → 5s → 30s). Keine Retry-Loops für Sensor-Ausfälle — fehlende Daten sind ein expliziter Zustand.

---

## Einstiegspunkte für Entwickler

| Aufgabe | Datei |
|---|---|
| Neues Gerät anbinden | `profiles/device_profiles.yaml` erweitern |
| Neues Protokoll | `adapters/<protokoll>_adapter.py` + Eintrag in `telemetry_ingest.py` |
| Topic-Mapping ändern | `profiles/topic_schema.yaml` |
| Health-Logik | `health_monitor.py` |

---

## Nächste Schritte

- [ ] `profiles/topic_schema.yaml` — MQTT-Topic-Konvention festlegen
- [ ] `profiles/device_profiles.yaml` — konkrete Hardware eintragen (PV-Wechselrichter, Batterie, Miner)
- [ ] `mqtt_client.py` — Subscribe + Retained-Status
- [ ] `telemetry_ingest.py` — Normalizer mit Stale-Detection
- [ ] `actuation_writer.py` — Relay-Steuerung mit Deduplizierung
- [ ] `health_monitor.py` — Health-Events + Timeout-Detection
