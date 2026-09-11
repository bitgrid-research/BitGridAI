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
    pv_forecast_kw          REAL,
    battery_power_w         REAL,
    cloud_coverage_pct      REAL,
    outdoor_temp_c          REAL,
    outdoor_humidity_pct    REAL,
    heizung_energy_kwh_today REAL,
    sun_azimuth_deg         REAL,
    sun_elevation_deg       REAL
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

-- Tagesabrechnung des Mining-Pools (F2Pool). Anders als energy_states/
-- miner_states KEIN Block-Raster: F2Pool rechnet einmal taeglich ab
-- (~02:00, siehe packages/pool.yaml), ein 10-Minuten-Raster waere hier
-- unpassend. Rohfakt, nicht rekonstruierbar (im Gegensatz zu daily_kpi
-- unten) — deshalb INSERT OR IGNORE, nie ueberschrieben. Quelle: HAs
-- sensor.pool_settlement_history (F2Pool V2 API), Fallback
-- input_text.pool_btc_daily_log. Siehe src/data/pool_settlement_sync.py
-- und ADR 026 (docs/architecture/09_design_decisions/091_adr_de.md).
CREATE TABLE IF NOT EXISTS bitcoin_daily_settlement (
    day                  TEXT PRIMARY KEY,   -- UTC-Kalendertag, aus mining_date (F2Pool-Settlement)
    earned_btc           REAL NOT NULL,
    pool_ths_avg         REAL,               -- F2Pool-gemeldeter Tagesschnitt, nicht HA-lokal gemittelt
    btc_eur_price_approx REAL,               -- Naeherung: Kurs bei Tagesbeginn, NICHT Kurs zum Abrechnungszeitpunkt
    source               TEXT NOT NULL,      -- 'ha:pool_settlement_history' | 'ha:pool_btc_daily_log' (Fallback)
    captured_at          TEXT NOT NULL
);

-- BTC/EUR-Tageskurs fuer den Verlaufschart im BitcoinInfo-Tab
-- (views/stats_btc_price.yaml). price_eur ist der erste beobachtete
-- mempool.space-Tick des UTC-Kalendertags (downsample_daily() in
-- btc_power_law.py), kein echter Tagesdurchschnitt. INSERT OR REPLACE
-- (nicht OR IGNORE wie bitcoin_daily_settlement): ein erneuter Abruf
-- desselben abgeschlossenen Tages liefert denselben Wert, ein Ueberschreiben
-- kann also nichts verlieren, macht die Sync-Logik aber robust gegen
-- kuenftige Aenderungen an der Downsampling-Regel. Waechst unbegrenzt
-- (kein Rolling-Fenster, mempool.space liefert je Sync die volle Historie):
-- src/data/btc_price_history.py schreibt hier IMMER alles, das --days-
-- Fenster fuers Dashboard-JSON wird erst beim Export aus dieser Tabelle
-- herausgeschnitten, siehe Kommentar dort.
CREATE TABLE IF NOT EXISTS btc_price_daily (
    day        TEXT PRIMARY KEY,   -- UTC-Kalendertag (YYYY-MM-DD)
    price_eur  REAL NOT NULL,
    fetched_at TEXT NOT NULL
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
    -- Sats pro kWh Mining-Energie, aus bitcoin_daily_settlement. NULL wenn
    -- fuer den Tag keine Abrechnung vorliegt oder mining_kwh = 0 (keine
    -- erfundene Null, siehe compute_day() in daily_kpi.py). Offizielles
    -- Ziel laut docs/architecture/01_introduction_and_goals/012_quality_goals.md:
    -- >= 45 sats/kWh im 7-Tage-Schnitt (siehe View v_energy_to_sats_7d).
    energy_to_sats       REAL,
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

-- 7-Tage-Schnitt von energy_to_sats gegen das offizielle Ziel (>= 45 sats/kWh,
-- 012_quality_goals.md). Echte Kalendertage (date(a.day, '-7 days')), keine
-- ROWS-BETWEEN-Fensterfunktion: die wuerde stillschweigend ueber Luecketage
-- hinwegmitteln und einen 7-Tage-Schnitt behaupten, der in Wahrheit auf
-- weniger Tagen beruht.
CREATE VIEW IF NOT EXISTS v_energy_to_sats_7d AS
SELECT a.day, a.energy_to_sats,
       (SELECT AVG(b.energy_to_sats) FROM daily_kpi b
        WHERE b.day > date(a.day, '-7 days') AND b.day <= a.day
          AND b.energy_to_sats IS NOT NULL) AS energy_to_sats_7d_avg
FROM daily_kpi a
WHERE a.energy_to_sats IS NOT NULL;
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
    # 2026-08-23: sensor.battery_power_w wird von der Live-Automation
    # (mvp_p3b_pv_reactive_downgrade, R8) bereits als Entscheidungssignal
    # genutzt, war bisher aber nirgends persistiert — jede saisonale Analyse
    # musste den Akku-Fluss ueber pv_power_w-house_load_w annaehern statt das
    # echte Signal zu verwenden. Siehe
    # docs/architecture/09_design_decisions/092_soc_saison_schwellen_vorschlag_de.md.
    ("battery_power_w", "ALTER TABLE energy_states ADD COLUMN battery_power_w REAL"),
    # 2026-08-23: Wetter/Heizlast fuer die naechste saisonale Optimierung
    # (Fruehling-vs-Herbst-Frage, Winter-Grundlast) — siehe
    # docs/architecture/09_design_decisions/092_soc_saison_schwellen_vorschlag_de.md.
    # Alle vier haben HA-History erst ab Anfang/Mitte Juli 2026, nicht seit
    # Mai — die Luecke davor ist echt, keine erfundenen Werte.
    (
        "cloud_coverage_pct",
        "ALTER TABLE energy_states ADD COLUMN cloud_coverage_pct REAL",
    ),
    ("outdoor_temp_c", "ALTER TABLE energy_states ADD COLUMN outdoor_temp_c REAL"),
    (
        "outdoor_humidity_pct",
        "ALTER TABLE energy_states ADD COLUMN outdoor_humidity_pct REAL",
    ),
    (
        "heizung_energy_kwh_today",
        "ALTER TABLE energy_states ADD COLUMN heizung_energy_kwh_today REAL",
    ),
    ("sun_azimuth_deg", "ALTER TABLE energy_states ADD COLUMN sun_azimuth_deg REAL"),
    (
        "sun_elevation_deg",
        "ALTER TABLE energy_states ADD COLUMN sun_elevation_deg REAL",
    ),
]

_DAILY_KPI_MIGRATIONS: list[tuple[str, str]] = [
    ("energy_to_sats", "ALTER TABLE daily_kpi ADD COLUMN energy_to_sats REAL"),
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

    existing_dk = {
        row[1] for row in conn.execute("PRAGMA table_info(daily_kpi)").fetchall()
    }
    for col, ddl in _DAILY_KPI_MIGRATIONS:
        if col not in existing_dk:
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
