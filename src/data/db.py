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


def _migrate(conn: sqlite3.Connection) -> None:
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
