"""
RecordingStatus — read-only health report for the research database.

Answers one question: is the nightly recording chain
(HA recorder -> ha_history_sync -> bitgrid.db) still delivering data?

The module only reads. It opens the database with SQLite's ``mode=ro`` and
writes a single JSON artefact that the HA dashboard fetches from ``/local/``.
It deliberately imports nothing from ``src`` and uses only the standard
library, so it also runs in an older checkout of this repository.

What the numbers mean, and what they do not:
  * ``blocks`` counts the 10-minute blocks present per UTC day (144 = complete).
  * A complete day means "fully transferred", not "fully measured".
    ``ha_history_sync.resample_to_blocks`` forward-fills missing readings, so
    an HA outage inside a synced window still yields 144 blocks. This report
    cannot see such filled blocks and says so instead of hiding it.

Staleness of the report itself is judged by the consumer (the dashboard card
compares ``generated_at`` with the current time). A report that is no longer
refreshed must not be able to stay green.

CLI:
    python -m src.data.recording_status --db data/bitgrid.db --out status.json

Exit codes: 0 report written, 1 report written but the database could not be
read (the JSON then carries ``level: error``), 2 report could not be written.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

SCHEMA_VERSION = 2
BLOCK_MINUTES = 10
BLOCKS_PER_DAY = 24 * 60 // BLOCK_MINUTES
# The sync runs once per day. 24 h cadence plus 2 h tolerance for a slow or
# delayed run. The dashboard card uses the same limit for ``generated_at``.
MAX_AGE_HOURS = 26
# Completed days shown and evaluated, in addition to the running day.
HISTORY_DAYS = 7

TABLES = ("energy_states", "device_states", "miner_states")
_PRIMARY_TABLE = "energy_states"
_BLOCK_ID_FORMAT = "%Y-%m-%dT%H:%M:%S"

_LEVEL_RANK = {"ok": 0, "warn": 1, "error": 2}

# Blocks that exist but were not measured (found 14.11.2026). The sync fills a
# window without readings with the last value and marks it quality=ok, so a
# Home Assistant outage looks like a complete day. Two signatures, both
# physically impossible for this house:
#   held  the four core values (house load, SoC, grid import, PV) identical
#         for at least SUSPECT_HELD_BLOCKS blocks in a row: on 07./08.08.2026
#         23 h with exactly the same numbers.
#   zero  house load exactly 0 W for at least SUSPECT_ZERO_BLOCKS blocks in a
#         row: the house never draws 0 W (smallest real value 3 W); on
#         27.05.2026 PV and house load stood at 0 for 13 h while the battery
#         charged from 18 to 100 %. Template sensors with float(0) turn a
#         lost SMA session into 0 W.
# Single zero blocks are left out: they appear on many days and can be a
# rounding of the house-load template. Read-only, nothing is changed in the
# database; the card shows the ranges, analyses can exclude them.
SUSPECT_HELD_BLOCKS = 6
SUSPECT_ZERO_BLOCKS = 3
_CORE_COLUMNS = "house_load_w, battery_soc_pct, grid_import_w, pv_power_w"


def _to_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return ts.astimezone(timezone.utc)


def _parse_block_id(block_id: str) -> datetime:
    """Block ids are naive UTC timestamps (see ha_history_sync)."""
    return datetime.strptime(block_id[:19], _BLOCK_ID_FORMAT).replace(
        tzinfo=timezone.utc
    )


def _iso(ts: datetime | None) -> str | None:
    return None if ts is None else ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row is not None


def _table_status(
    conn: sqlite3.Connection, table: str, now: datetime
) -> dict[str, Any]:
    if not _table_exists(conn, table):
        return {"exists": False, "rows": 0, "latest_block": None, "age_hours": None}
    # Table names come from the TABLES constant, never from input.
    rows, latest = conn.execute(
        f"SELECT COUNT(*), MAX(block_id) FROM {table}"  # noqa: S608
    ).fetchone()
    latest_ts = _parse_block_id(latest) if latest else None
    age = (
        None
        if latest_ts is None
        else round((now - latest_ts).total_seconds() / 3600.0, 2)
    )
    return {
        "exists": True,
        "rows": int(rows),
        "latest_block": _iso(latest_ts),
        "age_hours": age,
    }


def _day_rows(
    conn: sqlite3.Connection, first_day: datetime, now: datetime
) -> dict[str, dict[str, int]]:
    cur = conn.execute(
        """
        SELECT substr(block_id, 1, 10) AS day,
               COUNT(*) AS blocks,
               SUM(CASE WHEN quality = 'warn' THEN 1 ELSE 0 END) AS q_warn,
               SUM(CASE WHEN quality = 'error' THEN 1 ELSE 0 END) AS q_error,
               SUM(CASE WHEN missing_signals_json IS NOT NULL
                         AND missing_signals_json NOT IN ('', '[]')
                        THEN 1 ELSE 0 END) AS missing
        FROM energy_states
        WHERE block_id >= ? AND block_id < ?
        GROUP BY day
        """,
        (
            first_day.strftime(_BLOCK_ID_FORMAT),
            (now + timedelta(days=1)).strftime(_BLOCK_ID_FORMAT),
        ),
    )
    return {
        row[0]: {
            "blocks": int(row[1]),
            "quality_warn": int(row[2] or 0),
            "quality_error": int(row[3] or 0),
            "missing_signals": int(row[4] or 0),
        }
        for row in cur.fetchall()
    }


def suspect_runs(
    rows: list[tuple[str, Any, Any, Any, Any]],
) -> list[dict[str, Any]]:
    """Ranges of stored-but-not-measured blocks, see SUSPECT_HELD_BLOCKS.

    ``rows`` are (block_id, house_load_w, battery_soc_pct, grid_import_w,
    pv_power_w) ordered by block_id. Returns
    [{"from", "to", "blocks", "kind"}] with kind "held" or "zero".
    """
    runs: list[dict[str, Any]] = []

    def close(run: list[Any] | None, kind: str, minimum: int) -> None:
        if run and run[2] >= minimum:
            runs.append({"from": run[0], "to": run[1], "blocks": run[2], "kind": kind})

    held: list[Any] | None = None
    zero: list[Any] | None = None
    prev: tuple[Any, ...] | None = None
    prev_id: str | None = None
    for block_id, load, soc, imp, pv in rows:
        core = (load, soc, imp, pv)
        # A gap between blocks ends every run.
        contiguous = prev_id is not None and _parse_block_id(
            block_id
        ) - _parse_block_id(prev_id) == timedelta(minutes=BLOCK_MINUTES)
        if contiguous and core == prev and load not in (None, 0, 0.0):
            if held is None:
                held = [prev_id, block_id, 2]
            else:
                held[1], held[2] = block_id, held[2] + 1
        else:
            close(held, "held", SUSPECT_HELD_BLOCKS)
            held = None
        if load in (0, 0.0):
            if zero is not None and contiguous:
                zero[1], zero[2] = block_id, zero[2] + 1
            else:
                close(zero, "zero", SUSPECT_ZERO_BLOCKS)
                zero = [block_id, block_id, 1]
        else:
            close(zero, "zero", SUSPECT_ZERO_BLOCKS)
            zero = None
        prev, prev_id = core, block_id
    close(held, "held", SUSPECT_HELD_BLOCKS)
    close(zero, "zero", SUSPECT_ZERO_BLOCKS)
    return sorted(runs, key=lambda r: str(r["from"]))


def suspect_by_day(runs: list[dict[str, Any]]) -> dict[str, int]:
    """Suspect blocks per UTC day (a run may cross midnight)."""
    out: dict[str, int] = {}
    for run in runs:
        ts = _parse_block_id(run["from"])
        for _ in range(run["blocks"]):
            key = ts.strftime("%Y-%m-%d")
            out[key] = out.get(key, 0) + 1
            ts += timedelta(minutes=BLOCK_MINUTES)
    return dict(sorted(out.items()))


def _history(conn: sqlite3.Connection, today: datetime) -> dict[str, Any] | None:
    """
    Gaps over the whole recording period, not only the last days.

    Evaluates every completed UTC day from the first full day of recording up
    to yesterday. A day without any block is "missing", a day with fewer than
    144 blocks is "partial". Consecutive missing days are merged into ranges.

    The first day of recording is partial by nature (recording started some
    time during that day) and is therefore not counted as a gap.

    This is informational: old gaps do not change ``level``. Otherwise a gap
    from months ago would keep the status red forever and hide new problems.
    """
    blocks_per_day = {
        row[0]: int(row[1])
        for row in conn.execute(
            "SELECT substr(block_id, 1, 10), COUNT(*) FROM energy_states"
            " WHERE block_id < ? GROUP BY 1",
            (today.strftime(_BLOCK_ID_FORMAT),),
        )
    }
    if not blocks_per_day:
        return None

    first_key = min(blocks_per_day)
    first_day = _parse_block_id(first_key + "T00:00:00")
    start = (
        first_day
        if blocks_per_day[first_key] >= BLOCKS_PER_DAY
        else first_day + timedelta(days=1)
    )

    complete = 0
    partial: list[dict[str, Any]] = []
    missing_ranges: list[dict[str, Any]] = []
    missing_days = 0
    day = start
    while day < today:
        key = day.strftime("%Y-%m-%d")
        blocks = blocks_per_day.get(key, 0)
        if blocks >= BLOCKS_PER_DAY:
            complete += 1
        elif blocks > 0:
            partial.append({"date": key, "blocks": blocks})
        else:
            missing_days += 1
            previous = (day - timedelta(days=1)).strftime("%Y-%m-%d")
            if missing_ranges and missing_ranges[-1]["to"] == previous:
                missing_ranges[-1]["to"] = key
                missing_ranges[-1]["days"] += 1
            else:
                missing_ranges.append({"from": key, "to": key, "days": 1})
        day += timedelta(days=1)

    warn_blocks, error_blocks = conn.execute(
        "SELECT SUM(CASE WHEN quality = 'warn' THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN quality = 'error' THEN 1 ELSE 0 END) FROM energy_states"
    ).fetchone()
    # Column names are module constants, never user input.
    suspects = suspect_runs(
        conn.execute(
            f"SELECT block_id, {_CORE_COLUMNS} FROM energy_states"
            " WHERE block_id < ? ORDER BY block_id",
            (today.strftime(_BLOCK_ID_FORMAT),),
        ).fetchall()
    )

    return {
        "first_day": first_key,
        "first_day_blocks": blocks_per_day[first_key],
        "evaluated_from": start.strftime("%Y-%m-%d"),
        "evaluated_to": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
        "days_total": complete + len(partial) + missing_days,
        "days_complete": complete,
        "days_partial": len(partial),
        "days_missing": missing_days,
        "missing_ranges": missing_ranges,
        "partial": partial,
        # Blocks of every completed day that has data, for the month calendar
        # in the dashboard. A day that is absent here has no block at all.
        "blocks_by_day": dict(sorted(blocks_per_day.items())),
        "quality_warn_blocks": int(warn_blocks or 0),
        "quality_error_blocks": int(error_blocks or 0),
        "suspect_runs": suspects,
        "suspect_by_day": suspect_by_day(suspects),
        "suspect_blocks": sum(r["blocks"] for r in suspects),
    }


_LOG_TS = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ "
_RUN_START = re.compile(r"^" + _LOG_TS + r"INFO Hole HA History ")
_RUN_BLOCKS = re.compile(r"^" + _LOG_TS + r"INFO Sync fertig: (\d+) neu, ")
# The miner sync is the last of the three steps of ha_history_sync.main().
_RUN_END = re.compile(r"^" + _LOG_TS + r"INFO Miner-Sync fertig: ")
_RUN_FAILURE = re.compile(
    r"^Traceback \(most recent call last\)|^" + _LOG_TS + "ERROR "
)
# Enough for many runs (one run writes roughly 1 kB), small enough to stay cheap.
_LOG_TAIL_BYTES = 256 * 1024


def _log_time(text: str, local_tz: tzinfo | None) -> datetime:
    """Log timestamps are naive server-local time."""
    naive = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    local = naive.replace(tzinfo=local_tz) if local_tz else naive.astimezone()
    return local.astimezone(timezone.utc)


def parse_sync_log(text: str, local_tz: tzinfo | None = None) -> dict[str, Any] | None:
    """
    Extract the most recent run of ``ha_history_sync`` from its log.

    A run counts as successful when it reached its last step and logged
    neither a traceback nor an ERROR line. Returns ``None`` when the log
    contains no run at all.
    """
    lines = text.splitlines()
    start_index = None
    for index in range(len(lines) - 1, -1, -1):
        if _RUN_START.match(lines[index]):
            start_index = index
            break
    if start_index is None:
        return None

    started = _RUN_START.match(lines[start_index])
    assert started is not None
    finished: datetime | None = None
    blocks_added: int | None = None
    failed = False
    for line in lines[start_index + 1 :]:
        blocks = _RUN_BLOCKS.match(line)
        if blocks:
            blocks_added = int(blocks.group(2))
        end = _RUN_END.match(line)
        if end:
            finished = _log_time(end.group(1), local_tz)
        if _RUN_FAILURE.match(line):
            failed = True

    return {
        "last_start": _iso(_log_time(started.group(1), local_tz)),
        "last_end": _iso(finished),
        "ok": finished is not None and not failed,
        "blocks_added": blocks_added,
    }


def read_sync_log(
    log_path: str | Path, schedule: str | None, local_tz: tzinfo | None = None
) -> dict[str, Any]:
    """Read the tail of the sync log and describe the most recent run."""
    result: dict[str, Any] = {
        "schedule": schedule,
        "log_readable": False,
        "last_start": None,
        "last_end": None,
        "ok": None,
        "blocks_added": None,
    }
    try:
        with open(log_path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            handle.seek(max(0, handle.tell() - _LOG_TAIL_BYTES))
            text = handle.read().decode("utf-8", errors="replace")
    except OSError as exc:
        log.warning("Sync-Log nicht lesbar: %s", exc)
        return result
    result["log_readable"] = True
    parsed = parse_sync_log(text, local_tz)
    if parsed is not None:
        result.update(parsed)
    return result


def apply_sync(status: dict[str, Any], sync: dict[str, Any]) -> None:
    """Attach the sync run to the report and degrade the level if it failed."""
    status["sync"] = sync
    if not sync["log_readable"]:
        status["level"] = _raise_level(status["level"], "warn")
        status["reasons"].append("Das Log des nächtlichen Syncs ist nicht lesbar.")
    elif sync["last_start"] is None:
        status["level"] = _raise_level(status["level"], "warn")
        status["reasons"].append("Im Sync-Log steht kein einziger Lauf.")
    elif not sync["ok"]:
        status["level"] = "error"
        status["reasons"].append(
            "Der letzte Sync-Lauf ist mit einem Fehler abgebrochen (siehe Sync-Log)."
        )


def _raise_level(current: str, candidate: str) -> str:
    return candidate if _LEVEL_RANK[candidate] > _LEVEL_RANK[current] else current


def build_status(conn: sqlite3.Connection, now: datetime) -> dict[str, Any]:
    """
    Build the status report for the database behind ``conn``.

    Pure with respect to its inputs: the same database content and the same
    ``now`` always produce the same report.
    """
    now = _to_utc(now)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    first_day = today - timedelta(days=HISTORY_DAYS)

    tables = {table: _table_status(conn, table, now) for table in TABLES}
    primary = tables[_PRIMARY_TABLE]

    level = "ok"
    reasons: list[str] = []
    days: list[dict[str, Any]] = []
    history: dict[str, Any] | None = None

    if not primary["exists"]:
        level = "error"
        reasons.append("Tabelle energy_states fehlt in der Datenbank.")
    elif primary["latest_block"] is None:
        level = "error"
        reasons.append("energy_states ist leer, es wurde noch nichts aufgezeichnet.")
    else:
        if primary["age_hours"] > MAX_AGE_HOURS:
            level = "error"
            reasons.append(
                f"Jüngster Block ist {primary['age_hours']:.0f} h alt "
                f"(Grenze {MAX_AGE_HOURS} h): der nächtliche Sync läuft nicht."
            )

        history = _history(conn, today)
        per_day = _day_rows(conn, first_day, now)
        empty_days: list[str] = []
        short_days: list[str] = []
        warn_blocks = 0
        error_blocks = 0
        for offset in range(HISTORY_DAYS + 1):
            day = first_day + timedelta(days=offset)
            key = day.strftime("%Y-%m-%d")
            complete = day < today
            row = per_day.get(
                key,
                {
                    "blocks": 0,
                    "quality_warn": 0,
                    "quality_error": 0,
                    "missing_signals": 0,
                },
            )
            days.append(
                {"date": key, "complete": complete, "expected": BLOCKS_PER_DAY, **row}
            )
            warn_blocks += row["quality_warn"]
            error_blocks += row["quality_error"]
            if not complete:
                continue
            if row["blocks"] == 0:
                empty_days.append(key)
            elif row["blocks"] < BLOCKS_PER_DAY:
                short_days.append(f"{key} ({row['blocks']}/{BLOCKS_PER_DAY})")

        if empty_days:
            level = "error"
            reasons.append("Tage ganz ohne Daten: " + ", ".join(empty_days) + ".")
        if error_blocks:
            level = "error"
            reasons.append(
                f"{error_blocks} Blöcke mit quality=error "
                "(mindestens zwei Kernsignale fehlten)."
            )
        if short_days:
            level = _raise_level(level, "warn")
            reasons.append("Unvollständige Tage: " + ", ".join(short_days) + ".")
        if warn_blocks:
            level = _raise_level(level, "warn")
            reasons.append(
                f"{warn_blocks} Blöcke mit quality=warn (ein Kernsignal fehlte)."
            )

    for table in TABLES:
        if table == _PRIMARY_TABLE:
            continue
        info = tables[table]
        if not info["exists"] or info["latest_block"] is None:
            level = _raise_level(level, "warn")
            reasons.append(f"{table} ist leer oder fehlt.")
        elif info["age_hours"] > MAX_AGE_HOURS:
            level = _raise_level(level, "warn")
            reasons.append(
                f"{table} hängt {info['age_hours']:.0f} h zurück "
                f"(Grenze {MAX_AGE_HOURS} h)."
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso(now),
        "max_age_hours": MAX_AGE_HOURS,
        "level": level,
        "reasons": reasons,
        "tables": tables,
        "days": days,
        "history": history,
    }


def error_status(now: datetime, message: str) -> dict[str, Any]:
    """Report used when the database itself could not be read."""
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso(_to_utc(now)),
        "max_age_hours": MAX_AGE_HOURS,
        "level": "error",
        "reasons": [f"Datenbank nicht lesbar: {message}"],
        "tables": {},
        "days": [],
        "history": None,
    }


def open_readonly(db_path: str | Path) -> sqlite3.Connection:
    """Open the database so that this process cannot modify it."""
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{path} existiert nicht")
    return sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=10.0)


def write_atomic(status: dict[str, Any], out_path: str | Path) -> None:
    """
    Write the report so that a reader never sees a half-written file.

    The temporary file lives in the target directory because ``os.replace`` is
    only atomic within one file system.
    """
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=str(target.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(status, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        # mkstemp creates 0600; the HA container reads the file as another user.
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, target)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def run(
    db_path: str | Path,
    out_path: str | Path,
    now: datetime,
    sync_log: str | Path | None = None,
    sync_schedule: str | None = None,
) -> dict[str, Any]:
    """Build the report for ``db_path`` and write it to ``out_path``."""
    try:
        conn = open_readonly(db_path)
        try:
            status = build_status(conn, now)
        finally:
            conn.close()
    except (OSError, sqlite3.Error, ValueError) as exc:
        log.error("Datenbank nicht lesbar: %s", exc)
        status = error_status(now, str(exc))
        status["db_readable"] = False
    else:
        status["db_readable"] = True
    if sync_log is not None:
        apply_sync(status, read_sync_log(sync_log, sync_schedule))
    else:
        status["sync"] = None
    write_atomic(status, out_path)
    return status


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statusbericht der Datenaufzeichnung als JSON schreiben"
    )
    parser.add_argument("--db", default=os.getenv("BITGRID_DB", "data/bitgrid.db"))
    parser.add_argument("--out", required=True, help="Zielpfad der JSON-Datei")
    parser.add_argument(
        "--sync-log",
        default=None,
        help="Log von ha_history_sync, daraus wird der letzte Lauf gelesen",
    )
    parser.add_argument(
        "--sync-schedule",
        default=None,
        help="Uhrzeit des taeglichen Sync-Laufs (Serverzeit), nur zur Anzeige",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    args = _parse_args()
    try:
        status = run(
            args.db,
            args.out,
            datetime.now(tz=timezone.utc),
            sync_log=args.sync_log,
            sync_schedule=args.sync_schedule,
        )
    except OSError as exc:
        log.error("Statusbericht konnte nicht geschrieben werden: %s", exc)
        raise SystemExit(2) from exc
    print(f"recording_status: {status['level']} -> {args.out}")
    for reason in status["reasons"]:
        print(f"  - {reason}")
    raise SystemExit(0 if status["db_readable"] else 1)


if __name__ == "__main__":
    main()
