"""
HADecisionSync: holt das Entscheidungsprotokoll der produktiven HA-Steuerung
in die Forschungs-DB (ha_decision_log, ha_diagnose_log, settings_history).

Warum: energy_states/miner_states sagen, WAS passiert ist. Warum die
Automatik so geschaltet hat, stand bisher nur in HA (sensor.miner_N_log haelt
25 Eintraege, der Recorder 365 Tage) und waere danach verloren. Dieser Sync
liest nur (HA REST History) und schreibt mit INSERT OR IGNORE, ein zweiter
Lauf ueber denselben Zeitraum aendert nichts.

Quellen:
  sensor.miner_N_log            -> ha_decision_log   (seit 31.08.2026)
  sensor.miner_N_auto_diagnose  -> ha_diagnose_log
  sensor.mvp_saison_status      -> settings_history  (berechnete Schwellen)
  input_number/input_boolean    -> settings_history  (History, sobald der
                                   Recorder sie aufzeichnet; sonst Snapshot)

Grenze: einzelne Handeingriffe sind nicht rekonstruierbar (das HA-Logbook
nennt als Ausloeser nur das Geraet). Handbetrieb erscheint als
Diagnose-Code "auto_off".

CLI:
  python -m src.data.ha_decision_sync               # letzte 3 Tage
  python -m src.data.ha_decision_sync --from 2026-08-26 --to 2026-11-14
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.data.db import get_connection

log = logging.getLogger(__name__)

MINER_LOG_ENTITIES = {
    "miner1": "sensor.miner_1_log",
    "miner2": "sensor.miner_2_log",
}
MINER_MODE_ENTITIES = {
    "miner1": "sensor.miner1_workmode_status",
    "miner2": "sensor.miner2_workmode_status",
}
MINER_DIAGNOSE_ENTITIES = {
    "miner1": "sensor.miner_1_auto_diagnose",
    "miner2": "sensor.miner_2_auto_diagnose",
}
SEASON_ENTITY = "sensor.mvp_saison_status"
SEASON_KEYS = (
    "state",
    "hausreserve_pct",
    "eco_ab_pct",
    "standard_endet_pct",
    "standard_ab_pct",
    "super_endet_pct",
    "super_ab_pct",
)
# Helpers that feed the control logic (packages/mvp_auto.yaml). The recorder
# excluded their domains until 14.11.2026, so older history does not exist.
SETTING_ENTITIES = (
    "input_number.mvp_soc_eco_start_pct",
    "input_number.mvp_pv_start_w",
    "input_number.mvp_soc_std_pct",
    "input_number.mvp_soc_super_pct",
    "input_number.mvp_soc_stop_pct",
    "input_number.mvp_soc_super_off_pct",
    "input_number.mvp_soc_std_off_pct",
    "input_number.mvp_batt_discharge_super_downgrade_w",
    "input_number.mvp_batt_discharge_std_downgrade_w",
    "input_number.mvp_tmax_std_threshold_c",
    "input_number.mvp_room_temp_eco_threshold_c",
    "input_number.battery_capacity_kwh",
    "input_number.mvp_night_baseload_w",
    "input_number.mvp_evening_gap_h",
    "input_number.mvp_battery_efficiency_pct",
    "input_number.mvp_reserve_floor_pct",
    "input_boolean.mvp_night_block_enabled",
    "input_boolean.miner1_auto_load_management",
    "input_boolean.miner2_auto_load_management",
)

_EMPTY = ("", "unknown", "unavailable", "None", "none")
_MODE_ARROW = " → "
_SOC_RE = re.compile(r"SoC\s+(\d+(?:[.,]\d+)?)\s*%")
_TARGET_RE = re.compile(r"Ziel=([^|]+)")
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
CHUNK_DAYS = 7


def block_id_of(ts: datetime) -> str:
    """10-minute block id (UTC), same raster as energy_states.block_id."""
    ts = ts.astimezone(timezone.utc)
    return ts.replace(
        minute=ts.minute - ts.minute % 10, second=0, microsecond=0
    ).strftime("%Y-%m-%dT%H:%M:%S")


def _parse_ts(raw: str) -> datetime | None:
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def fetch_full_history(
    start: datetime,
    end: datetime,
    entity_ids: list[str],
    ha_base_url: str,
    token: str,
    timeout: int = 120,
) -> dict[str, list[dict[str, Any]]]:
    """State rows with attributes per entity, oldest first ({} on HTTP errors).

    Unlike ha_history_sync._fetch_raw this needs the attributes (the log entry
    and the diagnosis text live there), so no minimal_response.
    """
    url = (
        f"{ha_base_url}/api/history/period/{start.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        f"?end_time={end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        f"&filter_entity_id={','.join(entity_ids)}"
    )
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw: list[list[dict[str, Any]]] = json.loads(resp.read().decode())
    except (URLError, TimeoutError) as exc:
        log.error("HA API nicht erreichbar: %s", exc)
        return {}
    except json.JSONDecodeError as exc:
        log.error("HA API Antwort kein gueltiges JSON: %s", exc)
        return {}
    result: dict[str, list[dict[str, Any]]] = {}
    for rows in raw:
        if rows and rows[0].get("entity_id"):
            result[str(rows[0]["entity_id"])] = rows
    return result


def fetch_states(
    entity_ids: tuple[str, ...], ha_base_url: str, token: str, timeout: int = 30
) -> dict[str, str]:
    """Current state per entity (missing or unavailable entities are left out)."""
    req = Request(
        f"{ha_base_url}/api/states", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            rows: list[dict[str, Any]] = json.loads(resp.read().decode())
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        log.error("HA API /api/states fehlgeschlagen: %s", exc)
        return {}
    wanted = set(entity_ids)
    return {
        str(r["entity_id"]): str(r.get("state"))
        for r in rows
        if r.get("entity_id") in wanted and str(r.get("state")) not in _EMPTY
    }


# ---------------------------------------------------------------------------
# Pure parsers (no network, no DB)
# ---------------------------------------------------------------------------


def decision_rows(
    miner: str, history: list[dict[str, Any]], start: datetime
) -> list[tuple[Any, ...]]:
    """Rows for ha_decision_log from the state history of sensor.miner_N_log.

    Every state row of the log sensor is one event: its newest list entry
    (attributes.entries[-1]) describes it, last_updated is the exact time.
    The first row HA returns is the state carried over at the window start,
    not an event in the window, so rows at or before ``start`` are skipped.
    Lab-reset rows (empty list) and repeats of the same entry are skipped too.

    Only rule changes are taken from here. The log sensor also lists mode
    changes, but only since autumn 2026 and not completely (live check
    14.11.2026: 21 mode entries against 1318 rule entries); mode changes come
    from the miner status history instead, see ``mode_rows``.
    """
    rows: list[tuple[Any, ...]] = []
    prev_entry: dict[str, Any] | None = None
    for item in history:
        ts = _parse_ts(str(item.get("last_updated") or item.get("last_changed") or ""))
        entries = (item.get("attributes") or {}).get("entries") or []
        if ts is None or not isinstance(entries, list) or not entries:
            continue
        entry = entries[-1]
        if not isinstance(entry, dict) or entry == prev_entry:
            continue
        prev_entry = entry
        if ts <= start:
            continue
        rule_text = str(entry.get("rule") or "").strip()
        if not rule_text:
            continue
        if _MODE_ARROW in rule_text:
            continue
        kind, from_state, to_state = "rule", None, rule_text
        reason = str(entry.get("values") or "").strip()
        state = str(item.get("state") or "")
        soc = _SOC_RE.search(reason)
        stamp = ts.astimezone(timezone.utc).isoformat()
        rows.append(
            (
                f"{miner}|{stamp}",
                stamp,
                block_id_of(ts),
                miner,
                kind,
                from_state,
                to_state,
                None if state in _EMPTY else state,
                reason or None,
                float(soc.group(1).replace(",", ".")) if soc else None,
            )
        )
    return rows


def mode_rows(
    miner: str,
    history: list[dict[str, Any]],
    start: datetime,
    prev_mode: str | None,
) -> list[tuple[str, datetime, str | None, str]]:
    """Mode changes (id, time, from, to) from sensor.minerN_workmode_status.

    The reported mode is recorded since 05.2026. Rows without a value
    (unavailable/unknown, e.g. miner off the network) are ignored, so a
    dropout between two equal modes is not a change. The row carried over to
    the window start only sets the baseline when ``prev_mode`` is unknown.
    """
    rows: list[tuple[str, datetime, str | None, str]] = []
    for item in history:
        ts = _parse_ts(str(item.get("last_updated") or item.get("last_changed") or ""))
        mode = str(item.get("state") or "")
        if ts is None or mode in _EMPTY:
            continue
        if ts <= start:
            if prev_mode is None:
                prev_mode = mode
            continue
        if mode == prev_mode:
            continue
        stamp = ts.astimezone(timezone.utc).isoformat()
        rows.append((f"{miner}|mode|{stamp}", ts, prev_mode, mode))
        prev_mode = mode
    return rows


def reason_kind(summary: str) -> str:
    """Reason part of a diagnosis summary with all numbers masked as N."""
    return _NUMBER_RE.sub("N", summary.split("|")[-1]).strip()


def diagnose_rows(
    miner: str, history: list[dict[str, Any]], start: datetime
) -> list[tuple[Any, ...]]:
    """Rows for ha_diagnose_log, one per change of verdict or kind of reason.

    The summary text carries live numbers ("SoC 49.0% < Stop 50.0%") and
    changes with every reading. A new row is written when code, actual mode,
    target mode or the reason with the numbers masked changes. The masked
    reason matters: under the same verdict "ok" the text moves from "SoC <
    Stop" to "waiting for PV", and that is what the surplus card asks for
    (first version, 14.11.2026, compared the verdict only and reported an
    evening reason for the next morning). The row at the window start is
    kept: it is the state valid from ``start`` on and the primary key makes
    a repeated run harmless.
    """
    rows: list[tuple[Any, ...]] = []
    prev: tuple[str, str | None, str | None, str] | None = None
    for item in history:
        ts = _parse_ts(str(item.get("last_updated") or item.get("last_changed") or ""))
        code = str(item.get("state") or "")
        if ts is None or code in _EMPTY:
            continue
        attrs = item.get("attributes") or {}
        summary = str(attrs.get("summary") or "")
        target = _TARGET_RE.search(summary)
        actual = attrs.get("actual_mode")
        key = (
            code,
            str(actual) if actual is not None else None,
            target.group(1).strip() if target else None,
            reason_kind(summary),
        )
        if key == prev:
            continue
        prev = key
        ts = max(ts, start)
        night = attrs.get("night_block")
        rows.append(
            (
                ts.astimezone(timezone.utc).isoformat(),
                block_id_of(ts),
                miner,
                key[0],
                key[1],
                key[2],
                summary or None,
                None if night is None else int(bool(night)),
            )
        )
    return rows


def setting_changes(
    entity: str,
    history: list[dict[str, Any]],
    keys: tuple[str, ...],
    last_known: dict[str, str],
    start: datetime,
    skip_carried: bool = False,
) -> list[tuple[str, str, str, str, str]]:
    """Rows for settings_history: one per change of a value, source 'history'.

    ``last_known`` maps key -> value already stored; it is updated in place.
    ``skip_carried`` drops the row HA carries over to the window start. For
    helpers the recorder ignored for months that row can be a months-old
    value (recorded 05.2026, excluded since), which must not be stored as if
    it were valid at ``start``; their baseline comes from the snapshot.
    """
    rows: list[tuple[str, str, str, str, str]] = []
    for item in history:
        ts = _parse_ts(str(item.get("last_updated") or item.get("last_changed") or ""))
        if ts is None or str(item.get("state")) in _EMPTY:
            continue
        if skip_carried and ts <= start:
            continue
        stamp = max(ts, start).astimezone(timezone.utc).isoformat()
        attrs = item.get("attributes") or {}
        for key in keys:
            raw = item.get("state") if key == "state" else attrs.get(key)
            if raw is None or str(raw) in _EMPTY:
                continue
            value = str(raw)
            if last_known.get(key) == value:
                continue
            last_known[key] = value
            rows.append((stamp, entity, key, value, "history"))
    return rows


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def _last_settings(
    conn: sqlite3.Connection, entity: str, until: str | None = None
) -> dict[str, str]:
    """Last stored value per key, optionally as of ``until`` (ISO timestamp).

    A sync window must compare with the values valid at its START: against
    the newest stored value a change inside an already synced window would be
    written again at the window start on every nightly run.
    """
    rows = conn.execute(
        "SELECT key, value FROM settings_history WHERE entity = ?"
        " AND (? IS NULL OR timestamp <= ?) ORDER BY timestamp",
        (entity, until, until),
    ).fetchall()
    return {str(k): str(v) for k, v in rows}


def _insert(conn: sqlite3.Connection, sql: str, rows: list[tuple[Any, ...]]) -> int:
    added = 0
    for row in rows:
        added += conn.execute(sql, row).rowcount
    return added


def sync_window(
    start: datetime,
    end: datetime,
    conn: sqlite3.Connection,
    ha_base_url: str,
    token: str,
) -> dict[str, int]:
    """Sync one window [start, end). Returns new rows per table."""
    entities = (
        list(MINER_LOG_ENTITIES.values())
        + list(MINER_MODE_ENTITIES.values())
        + list(MINER_DIAGNOSE_ENTITIES.values())
        + [SEASON_ENTITY]
        + list(SETTING_ENTITIES)
    )
    hist = fetch_full_history(start, end, entities, ha_base_url, token)
    added = {"decisions": 0, "diagnose": 0, "settings": 0}
    for miner, entity in MINER_LOG_ENTITIES.items():
        added["decisions"] += _insert(
            conn,
            "INSERT OR IGNORE INTO ha_decision_log (id, timestamp, block_id, miner,"
            " kind, from_state, to_state, rule_active, reason, soc_pct)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            decision_rows(miner, hist.get(entity, []), start),
        )
    start_iso = start.astimezone(timezone.utc).isoformat()
    for miner, entity in MINER_MODE_ENTITIES.items():
        prev = conn.execute(
            "SELECT to_state FROM ha_decision_log WHERE miner = ? AND kind = 'mode'"
            " AND timestamp <= ? ORDER BY timestamp DESC LIMIT 1",
            (miner, start_iso),
        ).fetchone()
        for row_id, ts, from_mode, to_mode in mode_rows(
            miner, hist.get(entity, []), start, prev[0] if prev else None
        ):
            stamp = ts.astimezone(timezone.utc).isoformat()
            # Rule and reason the watchdog had written last before the switch
            # (rule rows of this window are already stored above).
            ctx = conn.execute(
                "SELECT to_state, reason, soc_pct FROM ha_decision_log"
                " WHERE miner = ? AND kind = 'rule' AND timestamp <= ?"
                " ORDER BY timestamp DESC LIMIT 1",
                (miner, stamp),
            ).fetchone() or (None, None, None)
            added["decisions"] += conn.execute(
                "INSERT OR IGNORE INTO ha_decision_log (id, timestamp, block_id,"
                " miner, kind, from_state, to_state, rule_active, reason, soc_pct)"
                " VALUES (?, ?, ?, ?, 'mode', ?, ?, ?, ?, ?)",
                (row_id, stamp, block_id_of(ts), miner, from_mode, to_mode, *ctx),
            ).rowcount
    for miner, entity in MINER_DIAGNOSE_ENTITIES.items():
        rows = diagnose_rows(miner, hist.get(entity, []), start)
        # The carried-over first row repeats the verdict already stored by the
        # previous window; drop it if nothing changed.
        last = conn.execute(
            "SELECT code, actual_mode, target_mode, summary FROM ha_diagnose_log"
            " WHERE miner = ? AND timestamp < ? ORDER BY timestamp DESC LIMIT 1",
            (miner, start_iso),
        ).fetchone()
        if (
            rows
            and last
            and (last[0], last[1], last[2], reason_kind(last[3] or ""))
            == (rows[0][3], rows[0][4], rows[0][5], reason_kind(rows[0][6] or ""))
        ):
            rows = rows[1:]
        added["diagnose"] += _insert(
            conn,
            "INSERT OR IGNORE INTO ha_diagnose_log (timestamp, block_id, miner,"
            " code, actual_mode, target_mode, summary, night_block)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
    for entity in (SEASON_ENTITY, *SETTING_ENTITIES):
        keys = SEASON_KEYS if entity == SEASON_ENTITY else ("state",)
        added["settings"] += _insert(
            conn,
            "INSERT OR IGNORE INTO settings_history (timestamp, entity, key, value,"
            " source) VALUES (?, ?, ?, ?, ?)",
            list(
                setting_changes(
                    entity,
                    hist.get(entity, []),
                    keys,
                    _last_settings(conn, entity, start_iso),
                    start,
                    skip_carried=entity != SEASON_ENTITY,
                )
            ),
        )
    conn.commit()
    return added


def snapshot_settings(
    conn: sqlite3.Connection, states: dict[str, str], now: datetime
) -> int:
    """Store the current value of every helper that differs from the last one.

    Covers helpers the recorder does not (yet) keep. The timestamp is the
    sync time, not the time of the change (source 'snapshot').
    """
    stamp = now.astimezone(timezone.utc).isoformat()
    added = 0
    for entity, value in sorted(states.items()):
        if _last_settings(conn, entity).get("state") == value:
            continue
        added += conn.execute(
            "INSERT OR IGNORE INTO settings_history (timestamp, entity, key, value,"
            " source) VALUES (?, ?, 'state', ?, 'snapshot')",
            (stamp, entity, value),
        ).rowcount
    conn.commit()
    return added


def sync(
    start: datetime,
    end: datetime,
    conn: sqlite3.Connection,
    ha_base_url: str,
    token: str,
) -> dict[str, int]:
    """Sync [start, end) in weekly chunks (the log attribute is large)."""
    total = {"decisions": 0, "diagnose": 0, "settings": 0}
    chunk = start
    while chunk < end:
        chunk_end = min(chunk + timedelta(days=CHUNK_DAYS), end)
        for name, n in sync_window(chunk, chunk_end, conn, ha_base_url, token).items():
            total[name] += n
        chunk = chunk_end
    return total


def _load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    parser = argparse.ArgumentParser(
        description="HA-Entscheidungsprotokoll -> Forschungs-DB (nur lesend an HA)"
    )
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD")
    parser.add_argument("--db", default="data/bitgrid.db")
    args = parser.parse_args(argv)

    _load_env()
    host = os.getenv("UMBREL_HOST", "")
    token = os.getenv("HA_TOKEN", "")
    if not host or not token:
        log.error("UMBREL_HOST und HA_TOKEN muessen in .env gesetzt sein.")
        return 1
    ha_url = f"http://{host}:{os.getenv('HA_PORT', '8123')}"

    now = datetime.now(tz=timezone.utc)
    start = (
        datetime.fromisoformat(args.from_date).replace(tzinfo=timezone.utc)
        if args.from_date
        else now - timedelta(days=args.days)
    )
    end = (
        datetime.fromisoformat(args.to_date).replace(tzinfo=timezone.utc)
        if args.to_date
        else now
    )
    end = min(end, now)

    conn = get_connection(args.db)
    try:
        added = sync(start, end, conn, ha_url, token)
        snap = snapshot_settings(
            conn, fetch_states(SETTING_ENTITIES, ha_url, token), now
        )
    finally:
        conn.close()
    print(
        f"Entscheidungen: +{added['decisions']}, Diagnose: +{added['diagnose']},"
        f" Einstellungen: +{added['settings']} (History) +{snap} (Snapshot)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
