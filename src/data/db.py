"""
DB — SQLite-Verbindung mit WAL-Mode und Schema-Initialisierung.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decision_events (
    id            TEXT PRIMARY KEY,
    block_id      TEXT NOT NULL,
    timestamp     TEXT NOT NULL,
    action        TEXT NOT NULL,
    decision_code TEXT NOT NULL,
    reason        TEXT NOT NULL,
    trigger       TEXT NOT NULL,
    params_json   TEXT,
    valid_until   TEXT,
    explain_short TEXT,
    state_ref     TEXT
);

CREATE TABLE IF NOT EXISTS energy_states (
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
    quality                 TEXT,
    missing_signals_json    TEXT,
    grid_export_w           REAL,
    miner_power_w           REAL,
    heizstab_power_w        REAL,
    energy_price_ct_kwh     REAL,
    pv_forecast_kw          REAL
);

CREATE TABLE IF NOT EXISTS device_states (
    block_id  TEXT NOT NULL,
    device    TEXT NOT NULL,
    power_w   REAL,
    PRIMARY KEY (block_id, device)
);

-- Zustand je Miner pro 10-Minuten-Block. energy_states haelt nur die Summe
-- (miner_power_w) und das Maximum (miner_temp_c) ueber alle Geraete, damit
-- laesst sich kein Schaltfehler einem Geraet zuordnen.
--
-- Der Kern der Tabelle ist das Paar workmode_set / workmode_status:
--   set    = was die Automation befohlen hat (select.minerN_workmode_set)
--   status = was der Miner tatsaechlich meldet (sensor.minerN_workmode_status)
-- Laufen die beiden ueber mehrere Bloecke auseinander, hat ein Schaltbefehl
-- nicht gegriffen. Genau dieser Fall ist heute unsichtbar.
CREATE TABLE IF NOT EXISTS miner_states (
    block_id        TEXT NOT NULL,
    miner           TEXT NOT NULL,
    workmode_set    TEXT,
    workmode_status TEXT,
    relay_on        INTEGER,
    mode_power_w    REAL,
    itemp_c         REAL,
    hbitemp_c       REAL,
    hbotemp_c       REAL,
    -- tmax_c ist die hoechste Einzelchip-Temperatur des Geraets und damit der
    -- Wert, der R3 ausloest (configuration.yaml bildet miner_max_chip_temp_c
    -- als max ueber beide minerN_tmax). Zusammen mit hbotemp_c (Board-Ausgang)
    -- laesst sich unterscheiden, ob ein ganzes Board heiss laeuft oder nur ein
    -- einzelner Chip die Abschaltung triggert.
    tmax_c          REAL,
    -- mode_power_w ist das Typenschild der Stufe (nur 800/1300/1600), KEINE
    -- Messung. power_w ist die am Shelly gemessene Wirkleistung. Fuer jede
    -- Effizienzaussage gilt power_w, sonst rechnet man mit Katalogwerten.
    power_w             REAL,
    -- Ertragsseite des A/B-Vergleichs Standard gegen Super: ohne TH/s je
    -- Geraet ist nicht bewertbar, ob der Mehrverbrauch der hoeheren Stufe
    -- durch Mehrleistung gedeckt ist. rejection_rate mindert den Ertrag.
    ths                 REAL,
    rejection_rate_pct  REAL,
    PRIMARY KEY (block_id, miner)
);

CREATE TABLE IF NOT EXISTS active_overrides (
    command_id    TEXT PRIMARY KEY,
    action        TEXT NOT NULL,
    valid_until   TEXT NOT NULL,
    requested_by  TEXT NOT NULL DEFAULT 'operator',
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kpi_log (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id                 TEXT NOT NULL,
    timestamp                TEXT NOT NULL,
    decision_latency_ms      REAL,
    explanation_latency_ms   REAL,
    thermal_incidents        INTEGER,
    flapping_rate            REAL,
    grid_import_wh           REAL,
    explainability_coverage  REAL,
    self_consumption_wh      REAL,
    battery_soc_pct          REAL,
    miner_runtime_blocks     INTEGER,
    override_active          INTEGER
);

CREATE TABLE IF NOT EXISTS override_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT NOT NULL,
    action        TEXT NOT NULL,
    duration_min  INTEGER,
    command_id    TEXT,
    accepted      INTEGER NOT NULL,
    reject_reason TEXT,
    user_reason   TEXT
);

-- ---------------------------------------------------------------------------
-- Tagesaggregate
--
-- Zweck ist ausschliesslich Verdichtung fuer die Analyse, kein neuer
-- Informationsgehalt: jede Zeile ist aus energy_states/miner_states
-- reproduzierbar und wird von src/data/daily_kpi.py neu berechnet.
--
-- Der Nutzen ist Groessenordnung: ein Monat sind 4464 Bloecke, aber nur 31
-- Zeilen hier. Fuer einen Analyse-Agenten mit begrenztem Kontextfenster ist
-- das der Unterschied zwischen "Frage nicht beantwortbar" und "eine Tabelle".
-- Details bleiben in den Blocktabellen und gehen nicht verloren: wer genauer
-- hinsehen will, steigt ueber block_id wieder ab.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_kpi (
    day                  TEXT PRIMARY KEY,   -- YYYY-MM-DD (UTC)
    blocks               INTEGER NOT NULL,
    coverage_pct         REAL    NOT NULL,   -- blocks / 144
    quality_warn         INTEGER NOT NULL,
    quality_error        INTEGER NOT NULL,
    missing_signals      TEXT,               -- JSON: Feld -> Anzahl Bloecke
    pv_kwh               REAL,
    house_kwh            REAL,
    grid_import_kwh      REAL,
    grid_export_kwh      REAL,
    mining_kwh           REAL,
    heizstab_kwh         REAL,
    pv_peak_w            REAL,
    pv_peak_block        TEXT,
    soc_min_pct          REAL,
    soc_max_pct          REAL,
    soc_mean_pct         REAL,
    -- Stunden je SoC-Band. Die Grenzen sind die Schaltschwellen aus
    -- packages/mvp_auto.yaml, das Band benennt den hoechsten dort erlaubten
    -- Modus. Wer hier andere Grenzen setzt, beschreibt eine Anlage, die es
    -- nicht gibt.
    soc_h_locked         REAL,               -- < 60 %, P1 erzwingt Standby
    soc_h_hold           REAL,               -- 60-70 %, laeuft weiter, kein Start
    soc_h_eco            REAL,               -- 70-85 %
    soc_h_standard       REAL,               -- 85-100 %
    soc_h_super          REAL,               -- 100 %
    -- regelbasierte Auffaelligkeiten, dieselben Schwellen wie im Tagesbericht
    blocks_temp_ge_110   INTEGER,
    blocks_switch_mismatch INTEGER,
    blocks_surplus_idle  INTEGER,            -- Einspeisung > 1000 W, Miner steht
    computed_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_miner_kpi (
    day                 TEXT NOT NULL,
    miner               TEXT NOT NULL,
    h_eco               REAL,
    h_standard          REAL,
    h_super             REAL,
    h_standby           REAL,
    ths_mean            REAL,
    watt_mean           REAL,
    w_per_th            REAL,
    tmax_max_c          REAL,
    tmax_mean_c         REAL,
    spread_mean_k       REAL,   -- tmax minus Board-Ausgang: Hinweis auf Einzelchip
    blocks_ge_110       INTEGER,
    switch_mismatches   INTEGER,
    rejection_mean_pct  REAL,
    computed_at         TEXT NOT NULL,
    PRIMARY KEY (day, miner)
);

-- ---------------------------------------------------------------------------
-- Views: das Fachvokabular liegt in der DB, nicht im Prompt.
--
-- Damit brauchen die Analyse-Werkzeuge kein frei formuliertes SQL. Ein
-- Sprachmodell waehlt eine View und einen Zeitraum, nicht Joins und
-- Spaltennamen. Das haelt die Abfragen reproduzierbar und die Antworten klein.
-- ---------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_schaltfehler AS
SELECT block_id, miner, workmode_set, workmode_status
FROM miner_states
WHERE workmode_set IS NOT NULL
  AND workmode_status IS NOT NULL
  AND workmode_set <> workmode_status;

CREATE VIEW IF NOT EXISTS v_ungenutzter_ueberschuss AS
SELECT block_id, grid_export_w, miner_power_w, battery_soc_pct, pv_power_w
FROM energy_states
WHERE grid_export_w > 1000
  AND (miner_power_w IS NULL OR miner_power_w < 100);

-- watt_mittel ist die am Shelly GEMESSENE Wirkleistung, nicht das Typenschild
-- der Stufe. Bis 2026-07-21 stand hier mode_power_w, also 800/1300/1600 als
-- Katalogwert. Damit sahen alle Effizienzzahlen exakt und waren doch nur die
-- Herstellerangabe zurueckgerechnet.
CREATE VIEW IF NOT EXISTS v_modus_effizienz AS
SELECT miner,
       workmode_status AS modus,
       COUNT(*)        AS bloecke,
       AVG(ths)        AS ths_mittel,
       AVG(power_w)    AS watt_mittel,
       AVG(power_w) / NULLIF(AVG(ths), 0) AS w_pro_th,
       AVG(mode_power_w) AS watt_typenschild,
       AVG(tmax_c)     AS tmax_mittel,
       MAX(tmax_c)     AS tmax_max
FROM miner_states
WHERE ths > 0 AND power_w > 0
GROUP BY miner, workmode_status;
"""


_KPI_MIGRATIONS: list[tuple[str, str]] = [
    ("self_consumption_wh", "ALTER TABLE kpi_log ADD COLUMN self_consumption_wh  REAL"),
    ("battery_soc_pct", "ALTER TABLE kpi_log ADD COLUMN battery_soc_pct      REAL"),
    (
        "miner_runtime_blocks",
        "ALTER TABLE kpi_log ADD COLUMN miner_runtime_blocks INTEGER",
    ),
    ("override_active", "ALTER TABLE kpi_log ADD COLUMN override_active      INTEGER"),
]

_ENERGY_STATE_MIGRATIONS: list[tuple[str, str]] = [
    ("miner_power_w", "ALTER TABLE energy_states ADD COLUMN miner_power_w    REAL"),
    ("heizstab_power_w", "ALTER TABLE energy_states ADD COLUMN heizstab_power_w REAL"),
]


def _migrate_soc_bands(conn: sqlite3.Connection) -> None:
    """Baut daily_kpi neu, wenn dort noch die alten SoC-Bandgrenzen stehen.

    Bis 2026-07-21 teilte die Tabelle bei 50/60/75/90 Prozent und hiess die
    letzte Spalte soc_h_full. Diese Grenzen entsprachen keiner Schaltschwelle
    der Anlage (60/70/85/100 laut packages/mvp_auto.yaml), die Bandnamen
    behaupteten also Modi, die dort nie gefahren wurden.

    Umgerechnet werden koennen die alten Stunden nicht, sie muessen aus
    energy_states neu gezaehlt werden. Weil jede Zeile ohnehin reproduzierbar
    ist, faellt dabei nichts weg: der naechste daily_kpi-Lauf fuellt sie wieder.
    """
    spalten = {
        row[1] for row in conn.execute("PRAGMA table_info(daily_kpi)").fetchall()
    }
    if not spalten or "soc_h_hold" in spalten:
        return
    conn.execute("DROP TABLE daily_kpi")
    conn.executescript(_SCHEMA)
    conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    _migrate_soc_bands(conn)

    existing_kpi = {
        row[1] for row in conn.execute("PRAGMA table_info(kpi_log)").fetchall()
    }
    for col, ddl in _KPI_MIGRATIONS:
        if col not in existing_kpi:
            conn.execute(ddl)

    existing_es = {
        row[1] for row in conn.execute("PRAGMA table_info(energy_states)").fetchall()
    }
    for col, ddl in _ENERGY_STATE_MIGRATIONS:
        if col not in existing_es:
            conn.execute(ddl)

    conn.commit()


def get_connection(db_path: str | Path = "data/bitgrid.db") -> sqlite3.Connection:
    """Gibt eine SQLite-Verbindung mit WAL-Mode zurück."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    _migrate(conn)
    return conn
