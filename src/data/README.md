# src/data

Persistenz, Logs, KPIs, Export und Replay-Artefakte.

`data/` speichert alles, was nach einem Neustart noch da sein soll: `DecisionEvent`s, `EnergyState`-Snapshots, KPIs und Export-Manifeste. Keine Entscheidungs- oder Erklärungslogik — nur sauberes Speichern und Abrufen.

---

## Verzeichnisstruktur

```
data/
├── db.py                  # DB-Verbindung (SQLite default, austauschbar)
├── models.py              # Tabellenschemas / ORM-Modelle
├── event_store.py         # DecisionEvents schreiben und lesen
├── state_store.py         # EnergyState-Snapshots für Replay
├── kpi.py                 # KPI-Berechnung und -Aggregation
├── export.py              # Export-Manifest, Anonymisierung, CSV-Export
└── __init__.py
```

---

## Log-Schema

### `decision_events` Tabelle

```sql
CREATE TABLE decision_events (
    id            TEXT PRIMARY KEY,       -- command_id (UUID)
    block_id      TEXT NOT NULL,          -- "2024-01-15T10:00:00"
    timestamp     TEXT NOT NULL,          -- ISO 8601 UTC
    action        TEXT NOT NULL,          -- START | STOP | THROTTLE | NOOP
    decision_code TEXT NOT NULL,          -- z.B. "STOP_R3_OVERTEMP"
    reason        TEXT NOT NULL,          -- maschinenlesbar
    trigger       TEXT NOT NULL,          -- BLOCK_TICK | SAFETY_ASYNC | OVERRIDE
    params_json   TEXT,                   -- JSON: verwendete Schwellen
    valid_until   TEXT,                   -- ISO 8601 UTC
    explain_short TEXT,                   -- Kurzerklärung (aus explain/)
    state_ref     TEXT                    -- Verweis → energy_states.block_id
);
```

### `energy_states` Tabelle

```sql
CREATE TABLE energy_states (
    block_id                TEXT PRIMARY KEY,
    window_start            TEXT NOT NULL,
    window_end              TEXT NOT NULL,
    pv_power_w              REAL,
    house_load_w            REAL,
    grid_import_w           REAL,
    battery_soc_pct         REAL,
    miner_temp_c            REAL,
    miner_heartbeat_age_sec REAL,
    surplus_kw              REAL,
    quality                 TEXT,          -- ok | warn | error
    missing_signals_json    TEXT,          -- JSON-Array
    -- Optionale Felder
    grid_export_w           REAL,
    energy_price_ct_kwh     REAL,
    pv_forecast_kw          REAL
);
```

### `kpi_log` Tabelle

```sql
CREATE TABLE kpi_log (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id                 TEXT NOT NULL,
    timestamp                TEXT NOT NULL,
    decision_latency_ms      REAL,
    explanation_latency_ms   REAL,
    thermal_incidents        INTEGER,
    flapping_rate            REAL,
    grid_import_wh           REAL,
    explainability_coverage  REAL
);
```

---

## API (`event_store.py`, `state_store.py`)

```python
class EventStore:
    def write(self, event: DecisionEvent, explain: ExplainResult) -> None: ...
    def read(self, block_id: str) -> DecisionEvent | None: ...
    def read_range(self, start: datetime, end: datetime) -> list[DecisionEvent]: ...
    def latest(self, n: int = 10) -> list[DecisionEvent]: ...

class StateStore:
    def write(self, state: EnergyState) -> None: ...
    def read(self, block_id: str) -> EnergyState | None: ...
    def read_range(self, start: datetime, end: datetime) -> list[EnergyState]: ...
```

---

## Export-Manifest (`export.py`)

Für Forschungs-Export (opt-in, `research_export` Feature-Flag):

```python
@dataclass
class ExportManifest:
    export_id: str              # UUID
    scope: str                  # "30d" | "custom"
    requested_at: datetime
    hash_sha256: str            # Datei-Hash für Integrität
    anonymized: bool            # immer True im Research-Export
    events_count: int
    state_snapshots_count: int
    status: Literal["pending", "ready", "failed"]
```

**Anonymisierung:** Alle absoluten Zeitstempel → relative Offsets. Keine Geräte-IDs, keine IP-Adressen. Nur Energiewerte und Entscheidungen.

---

## Retention

```yaml
# ops/config/system.yaml
data:
  retention_days: 90
  db_path: "data/bitgrid.db"
  storage_warn_mb: 500
  storage_error_mb: 1000
```

---

## Konventionen

**Append-only:** `decision_events` und `energy_states` werden innerhalb der Retention-Periode nie modifiziert oder gelöscht. Korrekturen → neuer Event mit `correction_ref`.

**Kein Join-Chaos:** Tabellen sind bewusst flach. `state_ref` ist ein weicher Verweis, keine FK-Kaskade.

**Replay-Safe:** `state_store` gibt exakt dieselben Werte zurück, die beim Schreiben übergeben wurden. Keine Nachberechnung beim Lesen.

**SQLite als Default:** Für Single-Home-Deployment ausreichend. Interface ist abstrahiert — Austausch gegen Postgres ohne Änderungen an `event_store.py` möglich.

---

## Einstiegspunkte für Entwickler

| Aufgabe | Datei |
|---|---|
| Schema erweitern | `models.py` + Migration-Skript |
| Event abfragen | `event_store.py` |
| Replay vorbereiten | `state_store.read_range()` → `sim/replay.py` |
| KPI berechnen | `kpi.py` |
| Export vorbereiten | `export.py` |

---

## Nächste Schritte

- [ ] `models.py` — Tabellen-Schema und Migrations-Baseline
- [ ] `db.py` — SQLite-Verbindung mit WAL-Mode
- [ ] `event_store.py` — Write + Read + Range-Query
- [ ] `state_store.py` — Snapshot-Persistenz für Replay
- [ ] `kpi.py` — KPI-Berechnung pro Block
- [ ] `export.py` — CSV-Export + Manifest + Anonymisierung
