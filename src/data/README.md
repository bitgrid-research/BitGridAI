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

## Aufzeichnungsstatus (`recording_status.py`)

Prüft, ob die nächtliche Aufzeichnung der Forschungsdaten noch läuft, und schreibt
einen Statusbericht als JSON. Rein lesend: die Datenbank wird mit `mode=ro`
geöffnet. Nur Standardbibliothek, keine `src`-Importe.

```bash
python -m src.data.recording_status --db data/bitgrid.db --out status.json \
    --sync-log logs/ha_history_sync.log --sync-schedule 03:45
```

Auf dem Produktivserver läuft das Modul per Cron nach dem History-Sync und schreibt
nach `www/recording_status.json` von Home Assistant. Die Karte „Datenaufzeichnung"
im Tab Einstellungen (`src/ha/config/views/aufzeichnung_status.yaml`) liest die Datei.

| Stufe | Auslöser |
|---|---|
| `error` | jüngster Block in `energy_states` älter als 26 h, ein abgeschlossener Tag ganz ohne Blöcke, oder Blöcke mit `quality=error` in den letzten 7 Tagen |
| `warn` | abgeschlossener Tag mit weniger als 144 Blöcken, Blöcke mit `quality=warn`, oder `device_states` / `miner_states` hängen mehr als 26 h zurück |
| `ok` | nichts davon |

Zusätzlich enthält der Bericht:

- `history`: Lücken über den gesamten Aufzeichnungszeitraum (fehlende Tage zu Zeiträumen
  zusammengefasst, unvollständige Tage, Blockzahl je Tag für den Monatskalender der Karte).
  Rein informativ: alte Lücken ändern `level` nicht, sonst bliebe die Ampel wegen eines
  Ausfalls von vor Monaten dauerhaft rot und würde neue Probleme verdecken. Der erste Tag
  der Aufzeichnung ist naturgemäß unvollständig und zählt nicht als Lücke.
- `sync` (nur mit `--sync-log`): letzter Lauf von `ha_history_sync` aus dessen Log
  (Start, Ende, Erfolg, neue Blöcke). Ein abgebrochener Lauf setzt `level` auf `error`,
  ein nicht lesbares Log auf `warn`. `--sync-schedule 03:45` ist nur die Anzeige der
  geplanten Uhrzeit (Serverzeit), das Modul plant selbst nichts.

Das Home-Assistant-Backup zeigt die Karte direkt aus den HA-Sensoren
(`sensor.backup_last_successful_automatic_backup` u. a.), es steht nicht im Bericht.
Es sichert Home Assistant samt Recorder, nicht `bitgrid.db`.

Der Bericht gilt für den Zeitpunkt seiner Erzeugung (`generated_at`). Ob er selbst noch
frisch ist, prüft die Karte: älter als `max_age_hours` ist rot, unabhängig von `level`.

**Grenze:** 144 Blöcke pro Tag heißt vollständig übertragen, nicht lückenlos gemessen.
`ha_history_sync.resample_to_blocks` füllt fehlende Werte vorwärts auf. Fällt Home
Assistant innerhalb eines synchronisierten Zeitraums aus, entstehen trotzdem 144 Blöcke
mit `quality=ok`. Der Bericht kann solche Blöcke nicht erkennen.

Exit-Codes: `0` Bericht geschrieben, `1` Bericht geschrieben, aber Datenbank nicht lesbar
(JSON trägt dann `level: error`), `2` Bericht konnte nicht geschrieben werden.

---

## Forschungs-Karten (`research_cards.py`)

Seit 13.11.2026. Cron auf dem HA-Host (`10 4 * * *`, nach dem Sync um 03:45), öffnet
`bitgrid.db` nur lesend und schreibt `www/research_cards.json` für die Karten
"Akku über Nacht" und "Solarprognose" im Tab Forschung (`views/forschung_kpi.yaml`).
Die Formelwerte (Grundlast, Akkugröße, Abendlücke, Wirkungsgrad, Boden; ADR 033) liest
es per GET aus HA (Fallback 570 W / 12,5 kWh / 0,75 h / 80 % / 5 %, im JSON als
`settings.source` vermerkt). Dazu kommt die Karte "Hardware-Zustand (W/TH)".

- **Akku über Nacht:** jede Nacht seit Einführung der Live-Formel (28.08.2026) von der
  Dämmerung (letzter Block mit PV ≥ 20 W) bis zum Morgen: Abschalt-SoC der Miner,
  Akku am Morgen, Hausverbrauch, Netzbezug. Monatsurteil zur Hausreserve (Ziel = Boden,
  5 % am Morgen; Nächte bis 13.11.2026 liefen noch mit der alten Formel) nur aus Nächten nach Mining-Tagen. Dieselbe Rechnung speist den BitHamster
  (`src/explain/bithamster_season.py`).
- **Solarprognose:** Tagessumme `pv_forecast_kw` gegen gemessene PV, dazu ein
  Profil nach Tageszeit. Zeitversatz 0: Obwohl `forecast.yaml` "jetzt + 60 min"
  abfragt, beschreibt der stündlich aktualisierte Wert praktisch die laufende Stunde
  (aus den Daten bestimmt, Juli und Oktober flachstes Profil bei 0 min; die erste
  Fassung mit 60 min zeigte fälschlich "nachmittags viel zu hoch"). Tagessummen hängen
  vom Versatz nicht ab. Befund 13.11.2026: im Sommer −6 bis −11 %, September +2 %,
  Oktober +16 %, November +74 %; der Fehler wächst mit tieferer Sonne.

- **Akku-Höchststand und Start:** je Tag der letzten 14 vollständigen Tage der höchste
  Akkustand gegen den Eco-Start des Monats (Saisontabelle) und die höchste Solarleistung
  als Info. Regel R7 startet allein über den Akku (plus 1 h Cooldown seit dem letzten
  Stopp, bei Sonne ≥ `mvp_pv_start_w` nur 15 min); die erste Fassung verlangte
  fälschlich beides. Vorschlag des BitHamsters: erklärt, warum im Winter nicht gemint wird.
- **Hardware-Zustand (W/TH):** Monatsmedian W/TH je Miner, nur Tage rein im Eco-Modus
  (mindestens 2 h Eco, keine Minute Standard oder Super). Der Tageswert mischt sonst die
  Modi und zeigt Verschleiß, wo nur die Saison wechselt (roh 16,2 → 17,2 → 16,4). Urteil
  "schlechter" ab +5 % gegen den ersten Monat mit mindestens 3 Tagen. Befund 13.11.2026:
  beide Miner stabil (−0,7 % und −0,5 %, 16,0 bis 16,1 W/TH seit Mai). Nicht zu
  verwechseln mit "Mining-Effizienz" im Tab Bitcoin (Sats je kWh).

Reine Anzeige: keine Entity, keine Automation, kein Rückfluss in Schwellen.

## Konventionen

**Append-only:** `decision_events` und `energy_states` werden innerhalb der Retention-Periode nie modifiziert oder gelöscht. Korrekturen → neuer Event mit `correction_ref`.

**Einzige dokumentierte Ausnahme (13.11.2026): Nachholen der Wetterspalten.**
`resample_to_blocks` hat die sechs Spalten `cloud_coverage_pct`, `outdoor_temp_c`,
`outdoor_humidity_pct`, `heizung_energy_kwh_today`, `sun_azimuth_deg` und
`sun_elevation_deg` seit 23.08.2026 zwar aus HA geholt, aber nie an `EnergyState`
übergeben; die Spalten blieben leer. Behoben in `resample_to_blocks`, nachgeholt mit
`python -m src.data.ha_history_sync --from 2026-08-23 --backfill-weather`
(`backfill_columns`): füllt ausschließlich **leere** Zellen dieser sechs Spalten in
**bestehenden** Blöcken aus der HA-History, legt keine Blöcke an und überschreibt
nichts. Vorher Sicherung `data/bitgrid.db.bak-20261113-weather` (SQLite-Backup-API),
danach Abgleich gegen sie: 11.754 Blöcke je Spalte gefüllt, 0 Zeilen mit einer
Änderung in einer anderen Spalte, 0 vorher gefüllte Wetterzellen verändert, übrige
Tabellen unverändert. Abdeckung seither: Wetter und Sonnenstand ab 01.07.2026
lückenlos, Heizungsenergie ab Mitte Juli, Mai ohne HA-History. Gleiche Grenze wie
beim Sync: Bei HA-Ausfällen ist der Wert vorwärts gefüllt.

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

## Entscheidungsprotokoll (`ha_decision_sync.py`)

Holt nachts (Cron 03:50) aus Home Assistant, warum die produktive Steuerung geschaltet
hat, und schreibt es in `ha_decision_log`, `ha_diagnose_log` und `settings_history`
(ADR 034). Nur lesend an HA, `INSERT OR IGNORE` in der DB: ein zweiter Lauf über
denselben Zeitraum ändert nichts.

```bash
python -m src.data.ha_decision_sync                 # letzte 3 Tage
python -m src.data.ha_decision_sync --from 2026-08-26 --to 2026-11-14
```

`decision_events` bleibt dem Python-Kern vorbehalten. `automation_cards.py` wertet das
Protokoll für den Tab Forschung aus (Schlüssel `automation` in `research_cards.json`),
`thesis_notes.py` baut daraus die Merkliste „Masterarbeit“ (Schlüssel `thesis`).

### Gespeichert, aber nicht gemessen (seit 14.11.2026)

`recording_status.suspect_runs` findet Blöcke, die der Abgleich geschrieben hat, obwohl
Home Assistant keine Werte lieferte: dieselben vier Kernwerte (Haus, SoC, Netzbezug, PV)
über mindestens 6 Blöcke (eingefroren) oder Hausverbrauch exakt 0 W über mindestens 3
Blöcke (das Haus zieht nie 0 W). Stand 14.11.2026: 117 Stunden in 22 Zeiträumen
(27.05. bis 25.09.2026), alle als `quality=ok` gespeichert. Die Datenbank wird nicht
verändert; Karte „Datenaufzeichnung“, BitHamster und die Merkliste zeigen die Zeiträume,
`research_cards.frozen_forecast_days` lässt eingefrorene Prognosetage aus. Neue Fälle
markiert `ha_history_sync` selbst: `quality=warn` mit `house_load_w:held` (letzter
Hausverbrauchswert älter als 30 min) oder `house_load_w:zero` in `missing_signals`.

## Stand-Abgleich mit der Masterarbeit (`thesis_sync.py`)

Seit 14.11.2026. Prüft ohne Sprachmodell, ob der Thesis-Entwurf noch zu Code,
Studienmaterial und Forschungsdaten passt. Grundlage sind die Kommentare, die
jeder Eintrag der Arbeit trägt (`% Quelle:`, `% Stand:`, `% Befund: <id>
(Stichtag TT.MM.JJJJ)`). Gemeldet werden:

| Signal | Bedeutung | Stärke |
|---|---|---|
| zitierte ADR ersetzt | Kopfzeile einer neueren ADR nennt `**Ersetzt (teilweise):** ADR NNN` | stark |
| Befund geändert | Wortlaut der Merkliste weicht vom Tagesabzug des zitierten Stichtags ab | stark |
| Befund fehlt im Text | Merklisten-Punkt der Gruppen Befunde, Methodik, Limitationen, Erklärschicht ohne Marker | Hinweis |
| zitierte Datei geändert | Datei (auch gitignorierte Studienmaterialien, auch Dateien im Thesis-Ordner) jünger als das Stand-Datum | schwach |

Die Merkliste (`thesis_notes.py`) gibt jedem Punkt eine feste `id`. Der Server
legt mit `research_cards --snapshot-dir data/stichtage` jede Nacht einen Abzug
ab (Cron 04:10). `scripts/thesis_open_export.py` (lokal, gitignored) führt die
Prüfung aus, schreibt sie in `thesis_open.json` (Karte „Masterarbeit“, Bitsy
liest sie für die Thesis-Aufgaben) und als `notizen/abgleich_system.md` in den
Thesis-Ordner, die Claude im Thesis-Fenster zu Beginn jeder Sitzung liest.
Ein Eintrag fällt aus der Meldung, sobald seine `% Stand:`-Zeile ein Datum nach
der Änderung trägt.
