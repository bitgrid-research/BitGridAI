# src/ops

Betrieb: Health, Config-Reload, Monitoring.

Ops prüft den Systemzustand, lädt Konfiguration sicher nach und publiziert Observability-Events. Keine Entscheidungslogik — nur Infrastruktur für einen stabilen, beobachtbaren Betrieb.

---

## Verzeichnisstruktur

```
ops/
├── health_check.py        # System-Health aggregieren und publizieren
├── config_loader.py       # YAML-Konfigs laden, validieren, hot-reload
├── metrics.py             # KPI-Metriken berechnen und exportieren
├── events.py              # Health- und System-Event-Typen + Publisher
├── config/
│   ├── rules.yaml         # Schwellen für R1–R5 (kein Neustart nötig)
│   ├── adapters.yaml      # Adapter-Einstellungen (Topics, Timeouts)
│   ├── system.yaml        # Block-Dauer, Autonomie-Defaults, Logging
│   └── feature_flags.yaml # Feature-Flags (Preview, Simulation, Export, ...)
└── __init__.py
```

---

## Health-Schema (`events.py`)

```python
@dataclass
class SystemHealth:
    status: Literal["ok", "warn", "error"]
    components: dict[str, ComponentHealth]
    timestamp: datetime
    config_version: str

@dataclass
class ComponentHealth:
    component: str           # "core" | "mqtt" | "db" | "config"
    status: Literal["ok", "warn", "error"]
    message: str | None
    last_ok: datetime | None
```

**MQTT-Topic:** `bitgrid/home/system/health` (Retained)

**HA-Entitäten:** `binary_sensor.system_ready`, `sensor.core_health`

---

## Config-Format (`config/rules.yaml`)

```yaml
# Alle Schwellen für R1–R5. Hot-reload ohne Neustart.
rules:
  r1:
    surplus_min_kw: 1.5
    price_max_ct_kwh: 25.0       # null = deaktiviert

  r2:
    soc_soft_min_pct: 20.0
    soc_hard_min_pct: 10.0
    max_grid_import_w: 500.0

  r3:
    max_chip_temp_c: 85.0
    t_resume_c: 75.0
    comm_timeout_sec: 60
    safety_lockout_min: 30

  r4:
    forecast_lookahead_min: 60
    min_predicted_surplus_kw: 2.0
    price_spike_threshold_ct: 30.0

  r5:
    deadband_hold_blocks: 2
    min_runtime_blocks: 3
    min_pause_blocks: 2
```

---

## Config-Reload (`config_loader.py`)

```python
class ConfigLoader:
    def load(self, path: str) -> Config: ...
    def validate(self, config: Config) -> list[str]: ...   # gibt Fehlerliste zurück
    def hot_reload(self) -> ReloadResult: ...              # atomarer Austausch

@dataclass
class ReloadResult:
    success: bool
    config_version: str    # SHA256 der Config-Datei
    errors: list[str]
    timestamp: datetime
```

**Ablauf:**
1. Neue Config laden und validieren
2. Bei Fehlern: alte Config behalten, `ReloadResult(success=False)`
3. Bei Erfolg: atomarer Tausch (kein Zwischenzustand sichtbar)
4. `ConfigReloaded`-Event → Core und Adapter reagieren

---

## Feature-Flags (`config/feature_flags.yaml`)

```yaml
features:
  preview_mode: false          # What-if Vorschau in UI
  research_export: false       # Anonymisierter Export für Forschung
  simulation_mode: false       # Sim-Modus statt Live-MQTT
  replay_mode: false           # Replay historischer Daten
  auth_enabled: true           # API-Authentifizierung
```

Feature-Flags werden über Config-Reload aktiviert — kein Neustart nötig.

---

## Metriken (`metrics.py`)

KPIs werden einmal pro Block berechnet und gespeichert:

| KPI | Einheit | Ziel |
|---|---|---|
| `decision_latency_ms` | ms | < 500 ms |
| `explanation_latency_ms` | ms | < 200 ms |
| `thermal_incidents` | Anzahl | 0 |
| `flapping_rate` | Wechsel/h | sinkend |
| `grid_import_wh` | Wh | minimiert |
| `explainability_coverage` | % | 100 % |

---

## Konventionen

**Kein Core-Import:** `ops/` importiert keine `core/`-Logik. Dependency-Richtung: `core` liest Config aus `ops/`, nicht umgekehrt.

**Config ist der einzige Ort für Schwellen:** Nie Schwellen im Anwendungscode hardcoden. Ausnahme: absolute Safety-Limits in `r3_safety.py` als Compile-Time-Konstante als letzte Absicherung.

**Atomarer Reload:** Config-Wechsel ist immer vollständig oder gar nicht. Niemals halbe Configs.

---

## Einstiegspunkte für Entwickler

| Aufgabe | Datei |
|---|---|
| Schwelle anpassen | `config/rules.yaml` (kein Neustart) |
| Feature aktivieren/deaktivieren | `config/feature_flags.yaml` |
| Health-Logik erweitern | `health_check.py` + `events.py` |
| Neues KPI | `metrics.py` |

---

## Nächste Schritte

- [ ] `config/rules.yaml` — Schwellen für R1–R5 mit sinnvollen Defaults
- [ ] `config/system.yaml` — Block-Dauer, Logging-Level, Retention
- [ ] `config/feature_flags.yaml` — alle Flags deaktiviert als Default
- [ ] `config_loader.py` — Laden, Validieren, Hot-Reload
- [ ] `health_check.py` — Aggregation + MQTT-Publish
- [ ] `events.py` — Event-Typen und Publisher
