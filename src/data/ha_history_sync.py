"""
HAHistorySync — zieht HA REST History und schreibt lueckenlos in energy_states.

Garantie: Solange HA laeuft, hat die HA-DB vollstaendige Sensorhistorie.
Dieser Sync zieht diese Historie und schreibt fehlende 10-Minuten-Bloecke
in energy_states — ohne vorhandene Eintraege zu ueberschreiben.

CLI:
  python -m src.data.ha_history_sync              # letzte 2 Tage
  python -m src.data.ha_history_sync --days 7     # letzte 7 Tage
  python -m src.data.ha_history_sync --from 2026-06-01 --to 2026-06-30

Env-Vars (aus .env):
  UMBREL_HOST   — HA-Host-IP
  HA_PORT       — HA-Port    (default: 8123)
  HA_TOKEN      — Long-Lived Access Token
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.data.db import get_connection
from src.data.state_store import StateStore
from src.core.models import EnergyState

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

_UMBREL_HOST = os.getenv("UMBREL_HOST", "")
_HA_PORT = os.getenv("HA_PORT", "8123")
_HA_TOKEN = os.getenv("HA_TOKEN", "")

# HA-Entitaeten → EnergyState-Felder
# Reihenfolge bestimmt die API-Abfrage-Reihenfolge — nicht aendern ohne Tests.
ENTITY_MAP: list[tuple[str, str]] = [
    ("sensor.pv_power_w", "pv_power_w"),
    ("sensor.house_load_w", "house_load_w"),
    ("sensor.grid_import_w", "grid_import_w"),
    ("sensor.grid_export_w", "grid_export_w"),
    ("sensor.battery_soc_pct", "battery_soc_pct"),
    # 2026-07-21: war `sensor.miner_temp_c`, die es in HA nie gab. Folge: der
    # `or 0.0`-Fallback unten schrieb 2833 Bloecke lang glatte 0.0 C, und weil
    # miner_temp_c nicht in _CRITICAL_FIELDS steht, blieb quality dabei "ok".
    # Ein still erfundener Messwert ist schlimmer als eine Luecke.
    ("sensor.miner_max_chip_temp_c", "miner_temp_c"),
    ("sensor.miner_heartbeat_age_sec", "miner_heartbeat_age_sec"),
    ("sensor.miner_total_power_w", "miner_power_w"),
    # energy_price_ct_kwh bewusst NICHT gemappt: der MVP nutzt keinen
    # Boersenpreis (Entscheidung 2026-07-21). Die Entity existiert in HA
    # nicht, ein Mapping wuerde die Entity-Vorabpruefung jede Nacht Alarm
    # schlagen lassen, und ein Waechter der immer schreit wird ignoriert.
    # Die 7,8 ct im System sind die Einspeiseverguetung
    # (input_number.feed_in_tariff_ct_kwh), nicht der Bezugspreis: das Feld
    # energy_price_ct_kwh ist die R1-Schranke gegen Netz-Mining und bleibt
    # None, solange kein echter Bezugspreis vorliegt.
    ("sensor.pv_forecast_kw", "pv_forecast_kw"),
    # Heizstab (AC ELWA 2): bewusst nur der Solar-Anteil, nicht power1_grid.
    # Gleiche Konvention wie sensor.heizstab_energy_integral in
    # configuration.yaml, das ebenfalls power1_solar integriert. Vorher stand
    # heizstab_power_w hart auf None, die Spalte war ueber alle Bloecke leer.
    ("sensor.ac_elwa_2_power1_solar", "heizstab_power_w"),
]

# Verbraucher-Plugs → device_states-Tabelle (pro Plug, 10-min-Bloecke).
# sensor.geraete_power_w (Summe) ist im HA-Recorder ausgeschlossen und wird
# bewusst nicht gespeichert: Summe = SUM(power_w) ueber die Haushalts-Plugs.
DEVICE_ENTITY_MAP: list[tuple[str, str]] = [
    ("sensor.shellyplugsg3_9070694abdf4_leistung", "kuehlschraenke"),
    ("sensor.shellyplugsg3_d885ac1e9adc_leistung", "waschmaschine"),
    ("sensor.shellyplugsg3_9070694c99d4_leistung", "tv"),
    ("sensor.shellyplugsg3_d885ac18c3b4_leistung", "buero"),
    # Miner-Infrastruktur: Lueftungs-Shelly (mvp_auto schaltet ihn, misst nicht)
    ("sensor.shellyplusplugs_d4d4daf4eda4_leistung", "lueftung"),
    # Noch nicht zugeordneter Plug (~40 W Dauerlast) — Slug spaeter per
    # UPDATE device_states SET device = '<name>' umbenennbar
    ("sensor.shellyplugsg3_d0cf13db3a00_leistung", "plug_d0cf13db3a00"),
]

# Zustand je Miner → miner_states-Tabelle.
#
# Der Zweck ist Fehlererkennung, nicht Vollstaendigkeit: energy_states haelt
# nur Summe und Maximum ueber beide Geraete, damit ist nicht erkennbar, ob ein
# einzelner Miner einen Schaltbefehl ignoriert hat.
#
# Entscheidend ist das Paar workmode_set (Befehl der Automation) und
# workmode_status (Rueckmeldung des Geraets). Laufen sie auseinander, hat das
# Schalten nicht gegriffen.
#
# Aussenwert-Konvention: True/1 = Relais an. Der Shelly meldet den Klartext
# "AN"/"AUS", deshalb laeuft dieses Feld ueber den Text-Pfad.
MINER_TEXT_FIELDS = ("workmode_set", "workmode_status", "relay_on")
MINER_NUMERIC_FIELDS = (
    "mode_power_w",
    "power_w",
    "itemp_c",
    "hbitemp_c",
    "hbotemp_c",
    "tmax_c",
    "ths",
    "rejection_rate_pct",
)
MINER_ENTITY_MAP: dict[str, dict[str, str]] = {
    "miner1": {
        "workmode_set": "select.miner1_workmode_set",
        "workmode_status": "sensor.miner1_workmode_status",
        "relay_on": "sensor.shelly_miner1_status",
        "mode_power_w": "sensor.miner1_mode_power_output",
        "power_w": "sensor.shellyplugsg3_dcb4d9c5567c_leistung",
        "itemp_c": "sensor.miner1_itemp",
        "hbitemp_c": "sensor.miner1_hbitemp",
        "hbotemp_c": "sensor.miner1_hbotemp",
        "tmax_c": "sensor.miner1_tmax",
        "ths": "sensor.miner1_thsspd",
        "rejection_rate_pct": "sensor.miner1_rejection_rate",
    },
    "miner2": {
        "workmode_set": "select.miner2_workmode_set",
        "workmode_status": "sensor.miner2_workmode_status",
        "relay_on": "sensor.shelly_miner2_status",
        "mode_power_w": "sensor.miner2_mode_power_output",
        "power_w": "sensor.shellyplugsg3_d0cf13d86254_leistung",
        "itemp_c": "sensor.miner2_itemp",
        "hbitemp_c": "sensor.miner2_hbitemp",
        "hbotemp_c": "sensor.miner2_hbotemp",
        "tmax_c": "sensor.miner2_tmax",
        "ths": "sensor.miner2_thsspd",
        "rejection_rate_pct": "sensor.miner2_rejection_rate",
    },
}
_RELAY_ON_STATES = {"AN", "an", "on", "ON", "True", "true"}

_CRITICAL_FIELDS = {"pv_power_w", "house_load_w", "battery_soc_pct"}
_HEARTBEAT_FALLBACK = 5.0  # sec — gilt als "ok" wenn kein Signal vorhanden


# ---------------------------------------------------------------------------
# HA REST API
# ---------------------------------------------------------------------------


def _ha_url(host: str, port: str) -> str:
    return f"http://{host}:{port}"


def verify_entities(
    entity_ids: list[str],
    ha_base_url: str,
    token: str,
    timeout: int = 30,
) -> list[str]:
    """
    Prueft vor dem Sync, welche der erwarteten Entitaeten es in HA ueberhaupt
    gibt, und gibt die fehlenden zurueck.

    Datenwaechter an der Quelle: eine umbenannte oder geloeschte Entity liefert
    ueber die History-API einfach eine leere Liste, was von "Sensor war in dem
    Zeitraum aus" nicht zu unterscheiden ist. Ohne diese Pruefung faellt so ein
    Fehler erst auf, wenn Monate spaeter jemand die Spalte auswertet (real
    passiert mit sensor.miner_temp_c, 2833 Bloecke lang 0.0 C).
    """
    req = Request(
        f"{ha_base_url}/api/states", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            states: list[dict[str, Any]] = json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError) as exc:
        log.warning("Entity-Vorabpruefung uebersprungen (HA nicht lesbar): %s", exc)
        return []

    known = {s.get("entity_id", "") for s in states}
    return [e for e in entity_ids if e not in known]


def _fetch_raw(
    start: datetime,
    end: datetime,
    entity_ids: list[str],
    ha_base_url: str,
    token: str,
    timeout: int = 30,
) -> dict[str, list[tuple[datetime, str]]]:
    """
    Gemeinsamer HTTP-Kern der History-Abfrage: liefert je Entitaet die rohen
    (timestamp, state)-Paare, zeitlich sortiert, ohne jede Interpretation.

    Gibt leeres dict zurueck bei Verbindungsfehlern (wird im Caller geloggt).
    """
    # HA erwartet UTC-Timestamps mit Z-Suffix im URL-Pfad.
    # +00:00 wird als Literal '+' interpretiert (URL-Space) und fuehrt zu 400.
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    entity_param = ",".join(entity_ids)

    url = (
        f"{ha_base_url}/api/history/period/{start_str}"
        f"?end_time={end_str}&filter_entity_id={entity_param}&minimal_response=true"
    )
    req = Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urlopen(req, timeout=timeout) as resp:
            raw: list[list[dict[str, Any]]] = json.loads(resp.read().decode())
    except URLError as exc:
        log.error("HA API nicht erreichbar: %s", exc)
        return {}
    except json.JSONDecodeError as exc:
        log.error("HA API Antwort kein gueltiges JSON: %s", exc)
        return {}

    # raw ist eine Liste von Listen, eine pro Entitaet, in Abfragereihenfolge.
    # Mit minimal_response=true hat nur das erste Element entity_id.
    result: dict[str, list[tuple[datetime, str]]] = {}
    for i, entity_history in enumerate(raw):
        if not entity_history:
            continue
        entity_id = entity_history[0].get(
            "entity_id", entity_ids[i] if i < len(entity_ids) else ""
        )
        readings: list[tuple[datetime, str]] = []
        for entry in entity_history:
            ts_str = entry.get("last_changed") or entry.get("last_updated", "")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            readings.append((ts, str(entry.get("state", ""))))
        if readings:
            result[entity_id] = sorted(readings, key=lambda x: x[0])

    return result


def fetch_history_text(
    start: datetime,
    end: datetime,
    entity_ids: list[str],
    ha_base_url: str,
    token: str,
    timeout: int = 30,
) -> dict[str, list[tuple[datetime, str | None]]]:
    """
    Wie fetch_history, aber ohne Float-Konvertierung: liefert den rohen
    HA-State als String.

    Gebraucht fuer Zustaende, die keine Zahl sind (Miner-Betriebsmodus
    "Eco"/"Standard"/"Super", Relais "AN"/"AUS"). fetch_history wuerde daraus
    None machen, weil float("Eco") scheitert.
    """
    raw_result = _fetch_raw(start, end, entity_ids, ha_base_url, token, timeout)
    result: dict[str, list[tuple[datetime, str | None]]] = {}
    for entity_id, entries in raw_result.items():
        readings: list[tuple[datetime, str | None]] = []
        for ts, state_str in entries:
            value = (
                state_str if state_str not in ("unavailable", "unknown", "") else None
            )
            readings.append((ts, value))
        if readings:
            result[entity_id] = readings
    return result


def fetch_history(
    start: datetime,
    end: datetime,
    entity_ids: list[str],
    ha_base_url: str,
    token: str,
    timeout: int = 30,
) -> dict[str, list[tuple[datetime, float | None]]]:
    """
    Ruft HA History API ab und gibt pro Entitaet eine sortierte Liste
    von (timestamp, value)-Tupeln zurueck.

    Gibt leeres dict zurueck bei Verbindungsfehlern (wird im Caller geloggt).
    """
    result: dict[str, list[tuple[datetime, float | None]]] = {}
    for entity_id, entries in _fetch_raw(
        start, end, entity_ids, ha_base_url, token, timeout
    ).items():
        readings: list[tuple[datetime, float | None]] = []
        for ts, state_str in entries:
            try:
                value: float | None = float(state_str)
            except (ValueError, TypeError):
                value = None  # "unavailable", "unknown", etc.
            readings.append((ts, value))
        if readings:
            result[entity_id] = readings

    return result


# ---------------------------------------------------------------------------
# Resampling: HA-Rohdaten → 10-Minuten-Bloecke
# ---------------------------------------------------------------------------


def _floor_to_block(ts: datetime) -> datetime:
    """Rundet auf naechste 10-Minuten-Grenze ab (UTC)."""
    ts_utc = ts.astimezone(timezone.utc)
    floored_min = (ts_utc.minute // 10) * 10
    return ts_utc.replace(minute=floored_min, second=0, microsecond=0)


def _last_value_in_window(
    readings: list[tuple[datetime, float | None]],
    win_start: datetime,
    win_end: datetime,
) -> float | None:
    """Letzter gueltiger Wert im Zeitfenster; vorwaerts-gefuellt aus Vorgaengerblock."""
    in_window = [v for ts, v in readings if win_start <= ts < win_end and v is not None]
    if in_window:
        return in_window[-1]
    # Vorwaerts-Fill: letzter gueltiger Wert vor dem Fenster
    before = [v for ts, v in readings if ts < win_start and v is not None]
    return before[-1] if before else None


def _last_text_in_window(
    readings: list[tuple[datetime, str | None]],
    win_start: datetime,
    win_end: datetime,
) -> str | None:
    """Wie _last_value_in_window, aber fuer nicht-numerische Zustaende."""
    in_window = [v for ts, v in readings if win_start <= ts < win_end and v is not None]
    if in_window:
        return in_window[-1]
    before = [v for ts, v in readings if ts < win_start and v is not None]
    return before[-1] if before else None


def resample_to_blocks(
    entity_readings: dict[str, list[tuple[datetime, float | None]]],
    entity_map: list[tuple[str, str]],
    start: datetime,
    end: datetime,
) -> list[EnergyState]:
    """
    Konvertiert HA-Rohdaten in eine Liste lueckenloser EnergyState-Bloecke.

    Jeder Block repraesentiert 10 Minuten. Fehlende Werte werden vorwaerts-
    gefuellt. Gaenzlich fehlende kritische Signale senken die quality.
    """
    entity_id_to_field = dict(entity_map)
    states: list[EnergyState] = []

    t = _floor_to_block(start)
    block_end_bound = _floor_to_block(end)

    while t < block_end_bound:
        win_end = t + timedelta(minutes=10)
        block_id = t.strftime("%Y-%m-%dT%H:%M:%S")

        values: dict[str, float | None] = {}
        for entity_id, field in entity_map:
            readings = entity_readings.get(entity_id, [])
            values[field] = _last_value_in_window(readings, t, win_end)

        # Qualitaets-Assessment.
        # quality haengt weiter nur an den kritischen Dauersignalen (die sind
        # immer da, ihr Ausfall ist echte Stoerung). missing_signals listet
        # dagegen JEDES fehlende Feld: sonst verschwindet eine Luecke in einem
        # optionalen Signal spurlos hinter dem `or`-Fallback weiter unten, und
        # genau das ist 2026-07-21 bei miner_temp_c aufgeflogen.
        missing = [f for _, f in entity_map if values.get(f) is None]
        critical_missing = [f for f in missing if f in _CRITICAL_FIELDS]
        quality: Literal["ok", "warn", "error"]
        if critical_missing:
            quality = "error" if len(critical_missing) >= 2 else "warn"
        else:
            quality = "ok"

        pv = values.get("pv_power_w") or 0.0
        load = values.get("house_load_w") or 0.0

        states.append(
            EnergyState(
                block_id=block_id,
                window_start=t,
                window_end=win_end,
                pv_power_w=pv,
                house_load_w=load,
                grid_import_w=values.get("grid_import_w") or 0.0,
                battery_soc_pct=values.get("battery_soc_pct") or 0.0,
                # Fail-safe wie im Live-Pfad (core/energy_context.py: fehlende
                # Temperatur → 999.0, damit R3 sicher greift). Vorher stand hier
                # 0.0, also genau die Gegenrichtung: eine fehlende Temperatur
                # konnte im Replay nie einen Sicherheits-Stopp ausloesen. Der
                # Wert ist ueber missing_signals als "nicht gemessen" erkennbar.
                miner_temp_c=values.get("miner_temp_c") or 999.0,
                miner_heartbeat_age_sec=values.get("miner_heartbeat_age_sec")
                or _HEARTBEAT_FALLBACK,
                surplus_kw=(pv - load) / 1000.0,
                quality=quality,
                missing_signals=tuple(missing),
                grid_export_w=values.get("grid_export_w"),
                miner_power_w=values.get("miner_power_w"),
                heizstab_power_w=values.get("heizstab_power_w"),
                energy_price_ct_kwh=values.get("energy_price_ct_kwh"),
                pv_forecast_kw=values.get("pv_forecast_kw"),
            )
        )
        t = win_end

    return states


def resample_device_blocks(
    entity_readings: dict[str, list[tuple[datetime, float | None]]],
    device_map: list[tuple[str, str]],
    start: datetime,
    end: datetime,
) -> list[tuple[str, str, float]]:
    """
    Konvertiert Plug-Rohdaten in (block_id, device, power_w)-Zeilen.

    Gleiche Fenster- und Forward-Fill-Semantik wie resample_to_blocks.
    Bloecke ohne jeglichen Wert (Plug nie gesehen) werden ausgelassen,
    damit ein spaeterer Sync sie noch fuellen kann.
    """
    rows: list[tuple[str, str, float]] = []

    t = _floor_to_block(start)
    block_end_bound = _floor_to_block(end)

    while t < block_end_bound:
        win_end = t + timedelta(minutes=10)
        block_id = t.strftime("%Y-%m-%dT%H:%M:%S")
        for entity_id, device in device_map:
            readings = entity_readings.get(entity_id, [])
            value = _last_value_in_window(readings, t, win_end)
            if value is not None:
                rows.append((block_id, device, value))
        t = win_end

    return rows


MinerRow = tuple[
    str,
    str,
    str | None,
    str | None,
    int | None,
    float | None,
    float | None,
    float | None,
    float | None,
    float | None,
    float | None,
    float | None,
    float | None,
]


def resample_miner_blocks(
    text_readings: dict[str, list[tuple[datetime, str | None]]],
    start: datetime,
    end: datetime,
    miner_map: dict[str, dict[str, str]] | None = None,
) -> list[MinerRow]:
    """
    Konvertiert die Miner-Rohdaten in Zeilen fuer miner_states.

    Alles laeuft ueber den Text-Pfad und wird hier konvertiert: die Modi sind
    Strings, die numerischen Felder liegen als Zahl-im-String vor. Ein Block
    ohne jede Information zu einem Miner wird ausgelassen, damit ein spaeterer
    Sync ihn noch fuellen kann (gleiche Semantik wie resample_device_blocks).
    """
    miner_map = miner_map or MINER_ENTITY_MAP
    rows: list[MinerRow] = []

    t = _floor_to_block(start)
    block_end_bound = _floor_to_block(end)

    while t < block_end_bound:
        win_end = t + timedelta(minutes=10)
        block_id = t.strftime("%Y-%m-%dT%H:%M:%S")

        for miner, fields in miner_map.items():
            texts: dict[str, str | None] = {}
            for field, entity_id in fields.items():
                texts[field] = _last_text_in_window(
                    text_readings.get(entity_id, []), t, win_end
                )
            if all(v is None for v in texts.values()):
                continue

            relay_raw = texts.get("relay_on")
            relay = None if relay_raw is None else int(relay_raw in _RELAY_ON_STATES)

            numeric: dict[str, float | None] = {}
            for field in MINER_NUMERIC_FIELDS:
                raw = texts.get(field)
                try:
                    numeric[field] = None if raw is None else float(raw)
                except ValueError:
                    numeric[field] = None

            rows.append(
                (
                    block_id,
                    miner,
                    texts.get("workmode_set"),
                    texts.get("workmode_status"),
                    relay,
                    numeric["mode_power_w"],
                    numeric["power_w"],
                    numeric["itemp_c"],
                    numeric["hbitemp_c"],
                    numeric["hbotemp_c"],
                    numeric["tmax_c"],
                    numeric["ths"],
                    numeric["rejection_rate_pct"],
                )
            )
        t = win_end

    return rows


# ---------------------------------------------------------------------------
# Sync-Logik
# ---------------------------------------------------------------------------


def sync(
    start: datetime,
    end: datetime,
    conn: sqlite3.Connection,
    ha_base_url: str,
    token: str,
) -> tuple[int, int]:
    """
    Synchronisiert den Zeitraum [start, end) in energy_states.

    Gibt (neue_bloecke, uebersprungene_bloecke) zurueck.
    Bestehende Eintraege werden nie ueberschrieben (INSERT OR IGNORE).
    """
    entity_ids = [eid for eid, _ in ENTITY_MAP]
    for missing_entity in verify_entities(entity_ids, ha_base_url, token):
        log.error(
            "Quell-Entity existiert nicht in HA: %s, die zugehoerige Spalte "
            "bleibt leer bzw. faellt auf den Fallback zurueck!",
            missing_entity,
        )
    log.info(
        "Hole HA History %s bis %s (%d Entitaeten)...",
        start.strftime("%Y-%m-%d %H:%M"),
        end.strftime("%Y-%m-%d %H:%M"),
        len(entity_ids),
    )
    entity_readings = fetch_history(start, end, entity_ids, ha_base_url, token)

    if not entity_readings:
        log.warning("Keine Daten von HA erhalten — Sync abgebrochen.")
        return 0, 0

    blocks = resample_to_blocks(entity_readings, ENTITY_MAP, start, end)
    log.info("%d Bloecke resamplet", len(blocks))

    store = StateStore(conn)
    added = 0
    skipped = 0

    for state in blocks:
        existing = store.read(state.block_id)
        if existing is not None:
            skipped += 1
        else:
            store.write(state)
            added += 1

    log.info("Sync fertig: %d neu, %d bereits vorhanden", added, skipped)
    return added, skipped


def sync_devices(
    start: datetime,
    end: datetime,
    conn: sqlite3.Connection,
    ha_base_url: str,
    token: str,
) -> tuple[int, int]:
    """
    Synchronisiert Verbraucher-Plugs [start, end) in device_states.

    Gibt (neue_zeilen, uebersprungene_zeilen) zurueck.
    Bestehende Eintraege werden nie ueberschrieben (INSERT OR IGNORE).
    """
    entity_ids = [eid for eid, _ in DEVICE_ENTITY_MAP]
    for missing_entity in verify_entities(entity_ids, ha_base_url, token):
        log.error(
            "Plug-Entity existiert nicht in HA: %s, dieser Verbraucher fehlt "
            "ab jetzt in device_states!",
            missing_entity,
        )
    log.info(
        "Hole Plug-History %s bis %s (%d Plugs)...",
        start.strftime("%Y-%m-%d %H:%M"),
        end.strftime("%Y-%m-%d %H:%M"),
        len(entity_ids),
    )
    entity_readings = fetch_history(start, end, entity_ids, ha_base_url, token)

    if not entity_readings:
        log.warning("Keine Plug-Daten von HA erhalten — Device-Sync uebersprungen.")
        return 0, 0

    rows = resample_device_blocks(entity_readings, DEVICE_ENTITY_MAP, start, end)

    added = 0
    skipped = 0
    for row in rows:
        cur = conn.execute(
            "INSERT OR IGNORE INTO device_states (block_id, device, power_w)"
            " VALUES (?, ?, ?)",
            row,
        )
        if cur.rowcount:
            added += 1
        else:
            skipped += 1
    conn.commit()

    log.info("Device-Sync fertig: %d neu, %d bereits vorhanden", added, skipped)
    return added, skipped


def sync_miners(
    start: datetime,
    end: datetime,
    conn: sqlite3.Connection,
    ha_base_url: str,
    token: str,
) -> tuple[int, int]:
    """
    Synchronisiert den Zustand je Miner [start, end) in miner_states.

    Gibt (neue_zeilen, uebersprungene_zeilen) zurueck.
    Bestehende Eintraege werden nie ueberschrieben (INSERT OR IGNORE).
    """
    entity_ids = [
        eid for fields in MINER_ENTITY_MAP.values() for eid in fields.values()
    ]
    for missing_entity in verify_entities(entity_ids, ha_base_url, token):
        log.error(
            "Miner-Entity existiert nicht in HA: %s, das zugehoerige Feld in "
            "miner_states bleibt leer!",
            missing_entity,
        )
    log.info(
        "Hole Miner-History %s bis %s (%d Entitaeten, %d Miner)...",
        start.strftime("%Y-%m-%d %H:%M"),
        end.strftime("%Y-%m-%d %H:%M"),
        len(entity_ids),
        len(MINER_ENTITY_MAP),
    )
    text_readings = fetch_history_text(start, end, entity_ids, ha_base_url, token)

    if not text_readings:
        log.warning("Keine Miner-Daten von HA erhalten, Miner-Sync uebersprungen.")
        return 0, 0

    rows = resample_miner_blocks(text_readings, start, end)

    added = 0
    skipped = 0
    for row in rows:
        cur = conn.execute(
            # Reihenfolge muss exakt der Tupel-Reihenfolge in
            # resample_miner_blocks entsprechen (MINER_NUMERIC_FIELDS).
            # SQLite prueft das nicht: es fuellt stur der Reihe nach, und ein
            # verrutschtes Feld landet als plausible Zahl in der falschen
            # Spalte. Genau das ist beim Einbau von power_w passiert.
            "INSERT OR IGNORE INTO miner_states (block_id, miner, workmode_set,"
            " workmode_status, relay_on, mode_power_w, power_w, itemp_c,"
            " hbitemp_c, hbotemp_c, tmax_c, ths, rejection_rate_pct)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )
        if cur.rowcount:
            added += 1
        else:
            skipped += 1
    conn.commit()

    log.info("Miner-Sync fertig: %d neu, %d bereits vorhanden", added, skipped)
    return added, skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronisiert HA History → energy_states (lueckenlos)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=2,
        help="Letzte N Tage synchronisieren (default: 2)",
    )
    parser.add_argument(
        "--from",
        dest="from_date",
        metavar="YYYY-MM-DD",
        help="Startdatum (ueberschreibt --days)",
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        metavar="YYYY-MM-DD",
        help="Enddatum exklusiv (default: jetzt)",
    )
    parser.add_argument(
        "--db",
        default="data/bitgrid.db",
        help="Pfad zur SQLite-DB (default: data/bitgrid.db)",
    )
    parser.add_argument(
        "--ha-url",
        default=None,
        help=f"HA Base URL (default: http://UMBREL_HOST:HA_PORT)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    # .env laden falls vorhanden
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

    host = os.getenv("UMBREL_HOST", _UMBREL_HOST)
    port = os.getenv("HA_PORT", _HA_PORT)
    token = os.getenv("HA_TOKEN", _HA_TOKEN)

    if not host:
        log.error("UMBREL_HOST nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)
    if not token:
        log.error("HA_TOKEN nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)

    args = _parse_args()
    ha_url = args.ha_url or _ha_url(host, port)

    now = datetime.now(tz=timezone.utc)
    if args.from_date:
        start = datetime.fromisoformat(args.from_date).replace(tzinfo=timezone.utc)
    else:
        start = now - timedelta(days=args.days)

    if args.to_date:
        end = datetime.fromisoformat(args.to_date).replace(tzinfo=timezone.utc)
    else:
        end = now

    conn = get_connection(args.db)
    try:
        added, skipped = sync(start, end, conn, ha_url, token)
        print(f"Sync: +{added} neue Bloecke, {skipped} uebersprungen")
        if added == 0 and skipped == 0:
            print("Warnung: Keine Daten empfangen — HA erreichbar?")
        dev_added, dev_skipped = sync_devices(start, end, conn, ha_url, token)
        print(f"Devices: +{dev_added} neue Zeilen, {dev_skipped} uebersprungen")
        min_added, min_skipped = sync_miners(start, end, conn, ha_url, token)
        print(f"Miner: +{min_added} neue Zeilen, {min_skipped} uebersprungen")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
