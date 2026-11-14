"""BitHamster KI: read-only explainer for the production dashboard.

Runs as a cron job on the HA host (every 30 min). One run:

1. reads live states from Home Assistant (HTTP GET only),
2. reads daily KPIs from the research database (``mode=ro``),
3. turns both into a fixed, auditable German context block (all numbers are
   computed here in Python, never by the model),
4. sends that block plus the persona (``bithamster_SOUL.md`` in the HA config
   folder) to the local LLM on GX10 (OpenAI-compatible vLLM endpoint),
5. writes ``www/bithamster_ki.json`` for the dashboard (KI zone in the hamster
   card, "Hamster-Analyse" in the research tab).

Determinism boundary: this module lives in ``explain/`` and has no control
path. The model receives text and returns text; it gets no tools and no HA
token, so "read-only" does not depend on the prompt. The only POST request in
this module goes to the LLM, never to Home Assistant. Its output is advice for
a human (hypotheses), it never feeds back into ``core/`` or any automation.

The JSON always carries the deterministic ``facts`` the text was built from,
so every number the hamster mentions can be checked on the dashboard.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.data.recording_status import open_readonly, write_atomic
from src.explain import bithamster_research as br
from src.explain.bithamster_log import log_entry
from src.data.research_cards import (
    BATTERY_FULL_PCT,
    EMPTY_MORNING_PCT,
    WINTER_MONTHS,
    heizstab_vs_battery,
    night_check,
    season_table,
    settings_from_states,
)
from src.explain.bithamster_season import (
    MONTHS_DE,
    season_findings,
    season_lines,
)

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1
HISTORY_DAYS = 14
BASELINE_DAYS = 30
MIN_COVERAGE_PCT = 99.0
MAX_OPTIMIZATIONS = 3
HA_TIMEOUT_S = 20
LLM_TIMEOUT_S = 240
DEFAULT_MODEL = "qwen3.8-flash-next"

# Text limits for the dashboard (characters). Longer model output is cut.
LIMITS = {
    "headline": 60,
    "text": 260,
    "titel": 60,
    "befund": 260,
    "vorschlag": 260,
    "pruefen": 220,
}

# Live values: label -> entity_id. Read-only, picked from GET /api/states.
LIVE_ENTITIES: dict[str, str] = {
    "soc_pct": "sensor.sma_storage_battery_soc_total",
    "pv_w": "sensor.sma_tripower_pv_power",
    "grid_import_w": "sensor.grid_import_w",
    "miner_total_w": "sensor.miner_total_power_w",
    "miner1_mode": "sensor.miner1_workmode_status",
    "miner2_mode": "sensor.miner2_workmode_status",
}
DIAGNOSE_ENTITIES: dict[str, str] = {
    "Miner 1": "sensor.miner_1_auto_diagnose",
    "Miner 2": "sensor.miner_2_auto_diagnose",
}
# Current rule thresholds (Tab Steuerung -> Regelschwellen): label, entity, unit.
THRESHOLDS: list[tuple[str, str, str]] = [
    ("Stop-Schwelle Akku (Hausreserve)", "input_number.mvp_soc_stop_pct", "%"),
    ("Eco-Start Akku", "input_number.mvp_soc_eco_start_pct", "%"),
    # R7 (mvp_auto.yaml): NOT a start condition. Sun >= this only shortens the
    # cooldown after a stop from 1 h to 15 min (live 13.11.2026 the hamster
    # and the peak card treated it as a second start condition).
    ("Sonne für Schnellstart", "input_number.mvp_pv_start_w", "W"),
    ("Standard-Start Akku", "input_number.mvp_soc_std_pct", "%"),
    ("Super-Start Akku", "input_number.mvp_soc_super_pct", "%"),
    ("Chip-Temperatur-Grenze", "input_number.mvp_tmax_std_threshold_c", "°C"),
    ("Raumtemperatur-Grenze", "input_number.mvp_room_temp_eco_threshold_c", "°C"),
]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def de_num(value: float | None, digits: int = 1) -> str:
    """German number format (decimal comma, thousands dot)."""
    if value is None:
        return "unbekannt"
    text = f"{value:,.{digits}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def _to_float(raw: Any) -> float | None:
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    return number if number == number else None  # NaN guard


# ---------------------------------------------------------------------------
# Home Assistant (GET only)
# ---------------------------------------------------------------------------


def read_ha_states(
    base_url: str, token: str, timeout: int = HA_TIMEOUT_S
) -> dict[str, dict[str, Any]]:
    """Return all HA states keyed by entity_id. Uses GET only."""
    req = Request(
        base_url.rstrip("/") + "/api/states",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed local URL)
        data = json.loads(resp.read().decode("utf-8"))
    return {s["entity_id"]: s for s in data if isinstance(s, dict) and "entity_id" in s}


def live_facts(states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Pick the live values, thresholds and gate diagnosis from HA states."""

    def state(entity: str) -> Any:
        s = states.get(entity)
        if not s or s.get("state") in (None, "unknown", "unavailable"):
            return None
        return s.get("state")

    live: dict[str, Any] = {}
    for key, entity in LIVE_ENTITIES.items():
        raw = state(entity)
        live[key] = raw if key.endswith("_mode") else _to_float(raw)

    thresholds = []
    for label, entity, unit in THRESHOLDS:
        thresholds.append(
            {"label": label, "value": _to_float(state(entity)), "unit": unit}
        )

    night_on = state("input_boolean.mvp_night_block_enabled")
    night = {
        "enabled": night_on == "on",
        "start": str(state("input_datetime.mvp_night_block_start") or "")[:5],
        "end": str(state("input_datetime.mvp_night_block_end") or "")[:5],
    }

    diagnose = []
    for name, entity in DIAGNOSE_ENTITIES.items():
        s = states.get(entity) or {}
        attrs = s.get("attributes") or {}
        diagnose.append(
            {
                "name": name,
                "code": s.get("state"),
                "summary": attrs.get("summary"),
            }
        )
    return {
        "live": live,
        "thresholds": thresholds,
        "night_block": night,
        "night_active": state(NIGHT_ACTIVE_ENTITY) == "on",
        "diagnose": diagnose,
        "season_status": state(SEASON_STATUS_ENTITY),
    }


# ---------------------------------------------------------------------------
# Research database (read-only)
# ---------------------------------------------------------------------------


def window_means(
    conn: sqlite3.Connection, start: datetime, end: datetime
) -> dict[str, Any]:
    """Per-day means of the main daily KPIs for complete days in [start, end).

    Comparison baseline for "is this unusual?": without it the model labelled
    the November battery level "auffällig" although PV (10,8 kWh/day) was below
    house load (17,2 kWh/day) and the battery could not fill (13.11.2026).
    """
    row = conn.execute(
        "SELECT COUNT(*), MIN(day), MAX(day), AVG(pv_kwh), AVG(house_kwh),"
        " AVG(grid_import_kwh), AVG(grid_export_kwh), AVG(soc_max_pct)"
        " FROM daily_kpi WHERE day >= ? AND day < ? AND coverage_pct >= ?",
        (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), MIN_COVERAGE_PCT),
    ).fetchone()
    keys = [
        "days",
        "first_day",
        "last_day",
        "pv_kwh",
        "house_kwh",
        "grid_import_kwh",
        "grid_export_kwh",
        "soc_max_pct",
    ]
    return dict(zip(keys, row))


def research_facts(
    conn: sqlite3.Connection, today: datetime, days: int = HISTORY_DAYS
) -> dict[str, Any]:
    """Aggregate the last ``days`` complete days from daily_kpi/daily_miner_kpi.

    Only days before ``today`` with coverage >= MIN_COVERAGE_PCT count, so a
    running day or a gap never looks like "no surplus" or "no mismatch".
    """
    start = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT day, pv_kwh, house_kwh, grid_import_kwh, grid_export_kwh, mining_kwh,"
        " soc_min_pct, soc_max_pct, soc_h_locked, soc_h_hold, soc_h_eco, soc_h_standard,"
        " soc_h_super, blocks_surplus_idle, blocks_switch_mismatch, blocks_temp_ge_110,"
        " energy_to_sats, coverage_pct"
        " FROM daily_kpi WHERE day >= ? AND day < ? ORDER BY day",
        (start, end),
    ).fetchall()
    cols = [
        "day",
        "pv_kwh",
        "house_kwh",
        "grid_import_kwh",
        "grid_export_kwh",
        "mining_kwh",
        "soc_min_pct",
        "soc_max_pct",
        "soc_h_locked",
        "soc_h_hold",
        "soc_h_eco",
        "soc_h_standard",
        "soc_h_super",
        "blocks_surplus_idle",
        "blocks_switch_mismatch",
        "blocks_temp_ge_110",
        "energy_to_sats",
        "coverage_pct",
    ]
    all_days = [dict(zip(cols, r)) for r in rows]
    good = [d for d in all_days if (d["coverage_pct"] or 0) >= MIN_COVERAGE_PCT]
    skipped = len(all_days) - len(good)

    def total(key: str) -> float:
        return float(sum((d[key] or 0) for d in good))

    def mean(key: str) -> float | None:
        vals = [d[key] for d in good if d[key] is not None]
        return float(sum(vals)) / len(vals) if vals else None

    surplus_days = [d["day"] for d in good if (d["blocks_surplus_idle"] or 0) > 0]
    mismatch_days = [d["day"] for d in good if (d["blocks_switch_mismatch"] or 0) > 0]
    sunny = [d for d in good if (d["pv_kwh"] or 0) >= 10.0]

    mismatch = mismatch_breakdown(conn, start, end)
    miners: list[dict[str, Any]] = []
    if good:
        mrows = conn.execute(
            "SELECT miner, SUM(h_eco), SUM(h_standard), SUM(h_super), SUM(h_standby),"
            " AVG(w_per_th), MAX(tmax_max_c), SUM(blocks_ge_110), SUM(switch_mismatches)"
            " FROM daily_miner_kpi WHERE day >= ? AND day < ? GROUP BY miner ORDER BY miner",
            (start, end),
        ).fetchall()
        for r in mrows:
            miners.append(
                {
                    "miner": r[0],
                    "h_eco": float(r[1] or 0),
                    "h_standard": float(r[2] or 0),
                    "h_super": float(r[3] or 0),
                    "h_standby": float(r[4] or 0),
                    "w_per_th": _to_float(r[5]),
                    "tmax_max_c": _to_float(r[6]),
                    "blocks_ge_110": int(r[7] or 0),
                    "switch_mismatches": int(r[8] or 0),
                }
            )

    return {
        "window_days": days,
        "days_used": len(good),
        "days_skipped_incomplete": skipped,
        "first_day": good[0]["day"] if good else None,
        "last_day": good[-1]["day"] if good else None,
        "pv_kwh_total": total("pv_kwh"),
        "pv_kwh_mean": mean("pv_kwh"),
        "sunny_days": len(sunny),
        "house_kwh_total": total("house_kwh"),
        "grid_import_kwh_total": total("grid_import_kwh"),
        "grid_export_kwh_total": total("grid_export_kwh"),
        "mining_kwh_total": total("mining_kwh"),
        "soc_min_mean": mean("soc_min_pct"),
        "soc_max_mean": mean("soc_max_pct"),
        "soc_h_mean": {
            band: mean("soc_h_" + band)
            for band in ("locked", "hold", "eco", "standard", "super")
        },
        "surplus_idle_hours": total("blocks_surplus_idle") / 6.0,
        "surplus_idle_days": len(surplus_days),
        "switch_mismatch_blocks": int(total("blocks_switch_mismatch")),
        "switch_mismatch_days": len(mismatch_days),
        "switch_mismatch_breakdown": mismatch,
        "temp_ge_110_blocks": int(total("blocks_temp_ge_110")),
        "energy_to_sats_mean": mean("energy_to_sats"),
        "miners": miners,
        "baseline": window_means(
            conn,
            today - timedelta(days=days + BASELINE_DAYS),
            today - timedelta(days=days),
        ),
    }


# ---------------------------------------------------------------------------
# Context block for the model
# ---------------------------------------------------------------------------


# Same rest states as v_schaltfehler in src/data/db.py: a commanded/reported
# pair of two rest states is no switch error (decision 13.11.2026).
REST_STATES = {"Standby", "Off", "Idle"}


def mismatch_breakdown(
    conn: sqlite3.Connection, start: str, end: str
) -> dict[str, Any]:
    """Real switch errors vs. rest-state reports in the window.

    Since 13.11.2026 the KPI (v_schaltfehler) no longer counts "Standby
    commanded, Off/Idle reported": nobody wanted to mine and nothing was mined.
    Those rows are still useful as an availability hint (miner powered off or
    unreachable), so they are counted here separately and presented to the
    model explicitly as "no error". Background: the live run on 13.11.2026 got
    only the bare count and claimed lost Sats although all 644 rows were
    Standby/Off without any surplus.
    """
    result: dict[str, Any] = {
        "real": 0,
        "rest": 0,
        "rest_first": None,
        "rest_last": None,
    }
    try:
        rows = conn.execute(
            "SELECT workmode_set, workmode_status, COUNT(*), MIN(block_id), MAX(block_id)"
            " FROM miner_states WHERE block_id >= ? AND block_id < ?"
            " AND workmode_set IS NOT NULL AND workmode_status IS NOT NULL"
            " AND workmode_set <> workmode_status GROUP BY 1, 2",
            (start, end),
        ).fetchall()
    except sqlite3.OperationalError:  # table missing (fresh or partial DB)
        return result
    for cmd, status, count, first, last in rows:
        if cmd in REST_STATES and status in REST_STATES:
            result["rest"] += int(count)
            result["rest_first"] = min(filter(None, [result["rest_first"], first]))
            result["rest_last"] = max(filter(None, [result["rest_last"], last]))
        else:
            result["real"] += int(count)
    return result


def mismatch_lines(research: dict[str, Any]) -> list[str]:
    """Context lines: real switch errors, plus rest-state reports as a hint."""
    days = research.get("switch_mismatch_days", 0)
    b = research.get("switch_mismatch_breakdown") or {}
    lines = [
        f"- Echte Schaltfehler (Modus befohlen, Miner hat ihn nicht übernommen):"
        f" {b.get('real', 0)} Einträge an {days} Tagen, je Miner gezählt. Ein"
        " Schaltfehler kostet nur Ertrag, wenn gleichzeitig Überschuss da war."
    ]
    if b.get("rest"):
        span = ""
        if b.get("rest_first") and b.get("rest_last"):
            span = (
                f" zwischen {local_ts(b['rest_first'])} und"
                f" {local_ts(b['rest_last'])} Uhr"
            )
        lines.append(
            f"- KEIN Fehler, nur Hinweis: {b['rest']} Einträge{span}, in denen Standby"
            " gewollt war und der Miner Off oder Idle meldete. Gemint werden sollte"
            " da nicht, es ging nichts verloren. Nenne das nicht Fehler; höchstens"
            " die Frage, warum die Miner in der Zeit aus oder nicht erreichbar waren."
        )
    return lines


def baseline_lines(research: dict[str, Any]) -> list[str]:
    """Comparison with the period before, so "unusual" has a yardstick."""
    b = research.get("baseline") or {}
    days = research.get("days_used") or 0
    if not b.get("days") or not days:
        return [
            "- Kein Vergleichszeitraum mit vollständigen Tagen vorhanden. Ob etwas"
            " auffällig ist, kannst du nur mit der Jahreszeit begründen."
        ]

    def pair(label: str, now: float | None, before: float | None, unit: str) -> str:
        return f"{label} jetzt {de_num(now)} {unit}, vorher {de_num(before)} {unit}"

    return [
        f"- VERGLEICH mit den {b['days']} vollständigen Tagen davor"
        f" ({b['first_day']} bis {b['last_day']}), alles pro Tag: "
        + "; ".join(
            [
                pair("Sonne", research["pv_kwh_mean"], b["pv_kwh"], "kWh"),
                pair(
                    "Hausverbrauch",
                    research["house_kwh_total"] / days,
                    b["house_kwh"],
                    "kWh",
                ),
                pair(
                    "Netzbezug",
                    research["grid_import_kwh_total"] / days,
                    b["grid_import_kwh"],
                    "kWh",
                ),
                pair(
                    "Einspeisung",
                    research["grid_export_kwh_total"] / days,
                    b["grid_export_kwh"],
                    "kWh",
                ),
                pair(
                    "höchster Akkustand",
                    research["soc_max_mean"],
                    b["soc_max_pct"],
                    "%",
                ),
            ]
        )
        + ".",
        "- EINORDNUNG (fest berechnet, genau so übernehmen, nicht umdeuten):",
        *assessment_lines(research, b),
    ]


def assessment_lines(research: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Deterministic "expected vs. unusual" labels for the main KPIs.

    The model ignored a rule given in words and still called a low battery
    "auffällig" while PV was below house load (13.11.2026). The labels are
    therefore decided here; the model only phrases them.
    """
    days = research.get("days_used") or 0
    if not days:
        return []
    pv = research["pv_kwh_mean"] or 0.0
    house = research["house_kwh_total"] / days
    soc_max = research["soc_max_mean"]
    grid = research["grid_import_kwh_total"] / days
    export = research["grid_export_kwh_total"] / days
    pv_before = b.get("pv_kwh") or 0.0
    less_sun = pv < pv_before
    lines = []
    if soc_max is not None:
        if pv < house:
            lines.append(
                f"  - Akku-Höchststand {de_num(soc_max, 0)} %: ERWARTBAR. Die Sonne"
                f" ({de_num(pv)} kWh/Tag) liegt unter dem Hausverbrauch"
                f" ({de_num(house)} kWh/Tag), der Akku kann sich nicht füllen."
            )
        elif less_sun and soc_max < (b.get("soc_max_pct") or 0):
            lines.append(
                f"  - Akku-Höchststand {de_num(soc_max, 0)} %: ERWARTBAR, weniger Sonne als vorher."
            )
        else:
            lines.append(
                f"  - Akku-Höchststand {de_num(soc_max, 0)} %: AUFFÄLLIG. Genug Sonne für"
                " das Haus, trotzdem wird der Akku nicht voll."
            )
    if grid > (b.get("grid_import_kwh") or 0.0):
        lines.append(
            f"  - Netzbezug {de_num(grid)} kWh/Tag, höher als vorher: "
            + (
                "ERWARTBAR, weniger Sonne."
                if less_sun
                else "AUFFÄLLIG, obwohl nicht weniger Sonne."
            )
        )
    else:
        lines.append(
            f"  - Netzbezug {de_num(grid)} kWh/Tag: nicht höher als vorher, UNAUFFÄLLIG."
        )
    if export < 0.5:
        lines.append(
            f"  - Einspeisung {de_num(export, 2)} kWh/Tag: praktisch nichts verschenkt, GUT."
        )
    if research.get("surplus_idle_hours"):
        lines.append(
            f"  - {de_num(research['surplus_idle_hours'])} Stunden Überschuss bei stehenden"
            " Minern: AUFFÄLLIG, hier ging Sonne ungenutzt ins Netz."
        )
    if not any("AUFFÄLLIG" in line for line in lines):
        # Questions like "what is unusual?" pull the model towards inventing
        # something unusual (live 13.11.2026: grid import flipped to "auffällig").
        lines.append(
            "  - GESAMTURTEIL: In diesem Zeitraum ist NICHTS auffällig. Sag das"
            " genau so, auch wenn danach gefragt wird, und erfinde keine Auffälligkeit."
        )
    return lines


def season_text(month: int) -> str:
    """Deterministic season hint so the model does not judge winter as a fault."""
    if month in (11, 12, 1, 2):
        return (
            "Winter, sonnenarm. Wenig Minen und ein oft leerer Akku sind jetzt normal."
        )
    if month in (3, 4, 9, 10):
        return "Übergangszeit, Sonne schwankt stark."
    return "Sommer, sonnenreich. Jetzt sollte am meisten gemint werden."


def per_day(research: dict[str, Any], key: str) -> float | None:
    """Mean per complete day for a total from research_facts."""
    days = research.get("days_used") or 0
    return float(research[key]) / days if days else None


SEASON_STATUS_ENTITY = "sensor.mvp_saison_status"


def rules_in_words(
    thresholds: list[dict[str, Any]], season_status: str | None = None
) -> list[str]:
    """Spell out the switching rules from the current thresholds.

    The model mixed up stop and wake-up threshold (live run 13.11.2026, "bis er
    wieder über 81 % steigt" instead of 91 %); spelled out here it has no room
    to derive them itself.

    ``season_status`` is sensor.mvp_saison_status. In "Nur Eco" months the
    Standard/Super thresholds are capped at 100 % but the stages are blocked
    altogether; the eval on 13.11.2026 answered "Super startet erst bei
    100 % Akku" because only the capped number was in the context.
    """
    val = {t["label"]: t["value"] for t in thresholds}

    def num(label: str, unit: str) -> str:
        return f"{de_num(val.get(label), 0)} {unit}"

    if season_status == "Nur Eco":
        stages = (
            "- Standard und Super sind in diesem Monat GESPERRT (Saison: Nur Eco),"
            " egal wie voll der Akku ist. Es gibt dafür keine Startschwelle."
        )
    elif season_status == "Eco + Standard":
        stages = (
            f"- Standard ab {num('Standard-Start Akku', '%')} Akku. Super ist in"
            " diesem Monat GESPERRT (Saison: Eco + Standard), egal wie voll der Akku ist."
        )
    else:
        stages = (
            f"- Standard ab {num('Standard-Start Akku', '%')} Akku, Super ab"
            f" {num('Super-Start Akku', '%')} Akku."
        )
    return [
        f"- Fällt der Akku unter {num('Stop-Schwelle Akku (Hausreserve)', '%')}, schlafen die Miner"
        " (Hausreserve).",
        f"- Sie wachen wieder auf, sobald der Akku mindestens {num('Eco-Start Akku', '%')} hat"
        " und seit dem letzten Stopp 1 Stunde vergangen ist. Liefert die Sonne mindestens"
        f" {num('Sonne für Schnellstart', 'W')}, reichen 15 Minuten. Die Sonne ist KEINE"
        " Startbedingung, nur der Akku. Dazwischen ist das Halteband: kein Minen, der"
        " Akku lädt.",
        stages,
        f"- Über {num('Chip-Temperatur-Grenze', '°C')} Chip-Temperatur wird sofort abgeschaltet.",
    ]


NIGHT_ACTIVE_ENTITY = "binary_sensor.mvp_nacht_sperre_aktiv"
# Same order and titles as the hamster card in the Übersicht
# (bitgrid_dashboard_v3.yaml, key/head). Live 13.11.2026: the card showed
# "Akku lädt zuerst" with the resting winter hamster, the KI text said
# "ich schlafe"; sleeping is the night-block picture only.
CARD_STATES: dict[str, str] = {
    "night": "Nachtsperre aktiv (der Hamster schläft)",
    "eco": "Miner läuft sparsam (Eco)",
    "standard": "Miner läuft in Standard",
    "super": "Miner läuft auf Volllast (Super)",
    "charge": "Akku lädt zuerst (Miner aus, der Hamster ruht am Akku)",
    "hold": "Akku im Halteband (Miner aus, der Hamster wartet)",
    "ready": "Akku reicht, Start nach der Wartezeit",
}


def card_state(live: dict[str, Any]) -> str | None:
    """Key of the state the Übersicht card shows (temperature states left out)."""
    lv = live["live"]
    if live.get("night_active"):
        return "night"
    modes = {lv.get("miner1_mode"), lv.get("miner2_mode")}
    for mode in ("Super", "Standard", "Eco"):
        if mode in modes:
            return mode.lower()
    val = {t["label"]: t["value"] for t in live["thresholds"]}
    soc = lv.get("soc_pct")
    stop = val.get("Stop-Schwelle Akku (Hausreserve)")
    eco = val.get("Eco-Start Akku")
    if soc is None or stop is None or eco is None:
        return None
    if soc < stop:
        return "charge"
    return "hold" if soc < eco else "ready"


_SLEEP_RE = re.compile(r"\b(schlafe|schläft|schlafen|schlaf)\b", re.I)


def fit_to_card_state(lage: dict[str, Any], live: dict[str, Any]) -> bool:
    """Keep the words in line with the picture. Returns True if text changed.

    Outside the night block "schlafen" contradicts the card; the headline
    falls back to the card title, the verb becomes "ruhen".
    """
    key = card_state(live)
    if key is None or key == "night":
        return False
    head, text = str(lage.get("headline") or ""), str(lage.get("text") or "")
    if not (_SLEEP_RE.search(head) or _SLEEP_RE.search(text)):
        return False
    if _SLEEP_RE.search(head):
        lage["headline"] = CARD_STATES[key].split(" (")[0]
    words = {
        "schlafe": "ruhe",
        "schläft": "ruht",
        "schlafen": "ruhen",
        "schlaf": "Ruhe",
    }
    lage["text"] = _SLEEP_RE.sub(
        lambda m: _keep_case(m.group(0), words[m.group(0).lower()]), text
    )
    return True


def _keep_case(old: str, new: str) -> str:
    return new[0].upper() + new[1:] if old[:1].isupper() else new


def next_step(live: dict[str, Any]) -> str | None:
    """What changes next, derived from live SoC and thresholds (no model guess)."""
    soc = live["live"].get("soc_pct")
    val = {t["label"]: t["value"] for t in live["thresholds"]}
    stop = val.get("Stop-Schwelle Akku (Hausreserve)")
    eco = val.get("Eco-Start Akku")
    modes = {live["live"].get("miner1_mode"), live["live"].get("miner2_mode")}
    if soc is None or stop is None or eco is None:
        return None
    if modes <= {"Standby", None}:
        if soc < eco:
            return (
                f"Akku {de_num(soc, 0)} %. Aufwachen erst ab {de_num(eco, 0)} % Akku."
            )
        return (
            f"Akku {de_num(soc, 0)} % reicht. Start, sobald seit dem letzten Stopp"
            " die Wartezeit um ist (1 Stunde, bei viel Sonne 15 Minuten)."
        )
    return (
        f"Miner laufen. Fällt der Akku unter {de_num(stop, 0)} %, schlafen sie wieder."
    )


_BANDS = {
    "locked": "gesperrt (unter Hausreserve)",
    "hold": "Halteband (kein Minen)",
    "eco": "Eco",
    "standard": "Standard",
    "super": "Super",
}


def winter_lines(conn: sqlite3.Connection, now: datetime) -> list[str] | None:
    """Priorities and the heating-rod finding for the winter months, else None."""
    if now.astimezone().month not in WINTER_MONTHS:
        return None
    h = heizstab_vs_battery(conn, now)
    lines = [
        "- PRIORITÄT im Winter: 1. Der Akku lädt und kommt durch die Nacht."
        " 2. Mining ist zweitrangig, es läuft nur bei vollem Akku mit Überschuss."
        " Beginne die Lage mit dem Akku, nicht mit den Minern oder Sats.",
    ]
    if h.get("days"):
        lines.append(
            f"- In den letzten {h['days']} Tagen war der Akku an"
            f" {h['empty_mornings']} Morgen leer (unter {de_num(EMPTY_MORNING_PCT, 0)} %)."
        )
        if h["heizstab_kwh_not_full"] >= 1:
            lines.append(
                f"- BEFUND HEIZSTAB: Der Heizstab (AC ELWA 2) nahm"
                f" in den letzten {h['days']} Tagen zusammen"
                f" {de_num(h['heizstab_kwh_not_full'])} kWh Solarstrom (Summe, keine"
                " aktuelle Leistung), während der Akku"
                f" nicht voll war (unter {de_num(BATTERY_FULL_PCT, 0)} %). Diesen Strom"
                " kauft das Haus nachts aus dem Netz nach; Netzstrom kostet ein"
                " Vielfaches der Wärme aus Öl. Der Heizstab regelt selbst und ist in HA"
                " nur lesbar: Akku-Vorrang muss am Gerät eingestellt werden (Tab"
                " Forschung, Karte Akku-Höchststand und Start)."
            )
    return lines


def build_context(live: dict[str, Any], research: dict[str, Any], now: datetime) -> str:
    """Render all facts as plain German lines. Every number the model may use is here."""
    lv = live["live"]
    lines = [
        f"Zeitpunkt: {now.strftime('%d.%m.%Y %H:%M')}, Jahreszeit: {season_text(now.month)}",
        "",
        "LIVE-WERTE",
        f"- Akku-Ladestand: {de_num(lv.get('soc_pct'), 0)} %",
        f"- Solarleistung gerade: {de_num((lv.get('pv_w') or 0) / 1000 if lv.get('pv_w') is not None else None)} kW",
        f"- Netzbezug gerade: {de_num(lv.get('grid_import_w'), 0)} W",
        f"- Miner zusammen: {de_num(lv.get('miner_total_w'), 0)} W",
        f"- Miner 1 Modus: {lv.get('miner1_mode') or 'unbekannt'}",
        f"- Miner 2 Modus: {lv.get('miner2_mode') or 'unbekannt'}",
    ]
    for d in live["diagnose"]:
        lines.append(
            f"- Diagnose {d['name']}: {d['code'] or 'unbekannt'} ({d['summary'] or 'keine Angabe'})"
        )
    nb = live["night_block"]
    lines.append(
        f"- Nachtsperre: {'an' if nb['enabled'] else 'aus'}, {nb['start'] or '?'} bis {nb['end'] or '?'} Uhr"
    )
    season = live.get("season_status")
    blocked = {
        "Nur Eco": ("Standard-Start Akku", "Super-Start Akku"),
        "Eco + Standard": ("Super-Start Akku",),
    }.get(season or "", ())
    lines += [
        "",
        f"AKTUELLE SCHWELLWERTE (Saison diesen Monat: {season or 'unbekannt'})",
    ]
    for t in live["thresholds"]:
        if t["label"] in blocked:
            lines.append(f"- {t['label']}: GESPERRT in diesem Monat")
        else:
            lines.append(f"- {t['label']}: {de_num(t['value'], 0)} {t['unit']}")
    lines += ["", "REGELN IN WORTEN (fertig abgeleitet, so wiedergeben)"]
    lines += rules_in_words(live["thresholds"], season)
    key = card_state(live)
    if key:
        lines += [
            "",
            f"ZUSTAND IN DER ÜBERSICHT (Bild und Titel der Karte): {CARD_STATES[key]}."
            " Deine Überschrift und die Lage beschreiben genau diesen Zustand."
            " Vom Schlafen sprichst du NUR bei aktiver Nachtsperre; sonst ruht,"
            " wartet oder döst der Hamster.",
        ]
    step = next_step(live)
    if step:
        lines += ["", f"NÄCHSTER SCHRITT (in der Lage nennen): {step}"]

    winter = research.get("winter")
    if winter:
        lines += ["", "WINTERMODUS (November bis Februar, Entscheidung des Nutzers)"]
        lines += winter
    r = research
    lines += ["", f"FORSCHUNGS-DB, LETZTE {r['window_days']} TAGE"]
    if not r["days_used"]:
        lines.append(
            "- Keine vollständigen Tage im Zeitraum. Für Muster reichen die Daten nicht."
        )
        return "\n".join(lines)
    lines += [
        f"- Ausgewertet: {r['days_used']} vollständige Tage ({r['first_day']} bis {r['last_day']}),"
        f" {r['days_skipped_incomplete']} unvollständige Tage weggelassen.",
        f"- Sonne gesamt: {de_num(r['pv_kwh_total'])} kWh, im Schnitt {de_num(r['pv_kwh_mean'])} kWh pro Tag,"
        f" {r['sunny_days']} Tage mit mindestens 10 kWh.",
        f"- Hausverbrauch: im Schnitt {de_num(per_day(r, 'house_kwh_total'))} kWh pro Tag"
        f" ({de_num(r['house_kwh_total'])} kWh in {r['days_used']} Tagen zusammen).",
        f"- Netzbezug: im Schnitt {de_num(per_day(r, 'grid_import_kwh_total'))} kWh pro Tag,"
        f" Einspeisung im Schnitt {de_num(per_day(r, 'grid_export_kwh_total'))} kWh pro Tag.",
        f"- Strom fürs Minen: im Schnitt {de_num(per_day(r, 'mining_kwh_total'))} kWh pro Tag.",
        # Wording: the model read "Höchstwert im Schnitt" as the mean SoC (13.11.2026).
        f"- Akku-Ladestand: der HÖCHSTE Stand eines Tages lag im Mittel bei"
        f" {de_num(r['soc_max_mean'], 0)} %, der TIEFSTE Stand eines Tages im Mittel bei"
        f" {de_num(r['soc_min_mean'], 0)} %. (Das ist kein Tagesdurchschnitt.)",
        "- Stunden pro Tag im Schnitt je Akku-Band: "
        + ", ".join(
            f"{_BANDS[b]} {de_num(v)} h"
            for b, v in r["soc_h_mean"].items()
            if v is not None
        )
        + ".",
        f"- Ungenutzter Solarüberschuss (mehr als 1 kW ins Netz, Miner standen): {de_num(r['surplus_idle_hours'])} Stunden"
        f" an {r['surplus_idle_days']} Tagen."
        + (
            " Es gab also KEINE verpasste Gelegenheit zum Minen, behaupte keine."
            if not r["surplus_idle_hours"]
            else ""
        ),
        *mismatch_lines(r),
        f"- Blöcke mit Chip-Temperatur ab 110 °C: {r['temp_ge_110_blocks']}.",
    ]
    if r["energy_to_sats_mean"] is not None:
        lines.append(
            f"- Energie zu Sats im Schnitt: {de_num(r['energy_to_sats_mean'], 0)} Sats pro kWh."
        )
    lines += baseline_lines(r)
    for m in r["miners"]:
        lines.append(
            f"- {m['miner']}: Eco {de_num(m['h_eco'])} h, Standard {de_num(m['h_standard'])} h,"
            f" Super {de_num(m['h_super'])} h, Standby {de_num(m['h_standby'])} h;"
            f" Effizienz {de_num(m['w_per_th'])} W pro TH; höchste Chip-Temperatur"
            f" {de_num(m['tmax_max_c'], 0)} °C; Schaltfehler {m['switch_mismatches']}."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM call (OpenAI-compatible, vLLM on GX10)
# ---------------------------------------------------------------------------


def call_llm(
    base_url: str, model: str, system: str, user: str, timeout: int = LLM_TIMEOUT_S
) -> str:
    """Send one chat completion request and return the message text."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
        # Qwen3 family: answer directly, no hidden reasoning block in the output.
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed local URL)
        data = json.loads(resp.read().decode("utf-8"))
    return str(data["choices"][0]["message"]["content"])


def _clip(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "…"


def parse_answer(raw: str) -> dict[str, Any]:
    """Extract and validate the model's JSON. Raises ValueError if unusable."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model output")
    obj = json.loads(text[start : end + 1])
    if not isinstance(obj, dict):
        raise ValueError("model output is not an object")
    raw_lage = obj.get("lage")
    lage: dict[str, Any] = raw_lage if isinstance(raw_lage, dict) else {}
    headline = _clip(lage.get("headline"), LIMITS["headline"])
    body = _clip(lage.get("text"), LIMITS["text"])
    if not headline or not body:
        raise ValueError("lage.headline/lage.text missing")
    opts = []
    raw_opts = obj.get("optimierungen")
    for item in raw_opts if isinstance(raw_opts, list) else []:
        if not isinstance(item, dict):
            continue
        entry = {
            k: _clip(item.get(k), LIMITS[k])
            for k in ("titel", "befund", "vorschlag", "pruefen")
        }
        if entry["titel"] and entry["befund"] and entry["vorschlag"]:
            opts.append(entry)
        if len(opts) >= MAX_OPTIMIZATIONS:
            break
    return {"lage": {"headline": headline, "text": body}, "optimierungen": opts}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


SOC_PLACEHOLDER = "{akku}"


def live_soc_template(text: str, live: dict[str, Any]) -> str | None:
    """Lage text with the battery level as a placeholder the card fills live.

    The analysis runs every 30 minutes; the card showed "Akku steht bei 64 %"
    next to a live 63 % (13.11.2026). Only the exact live value is replaced,
    and only if no threshold has the same number (then it could mean either).
    None if the value does not occur, the card keeps the text as written.
    """
    soc = live["live"].get("soc_pct")
    if soc is None:
        return None
    value = de_num(soc, 0)
    taken = {
        de_num(t["value"], 0) for t in live["thresholds"] if t["value"] is not None
    }
    pattern = re.compile(rf"(?<![\d,.]){re.escape(value)}(?=\s*%)")
    if value in taken or not pattern.search(text):
        return None
    return pattern.sub(SOC_PLACEHOLDER, text)


def run(
    *,
    db: str | Path,
    out: str | Path,
    soul: str | Path,
    ha_url: str,
    ha_token: str,
    llm_url: str,
    model: str,
    log_db: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """One full run. Always writes a JSON file (ok=false with error on failure)."""
    now = now or datetime.now(timezone.utc)
    local_now = now.astimezone()
    result: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "generated_at": now.isoformat(),
        "model": model,
        "ok": False,
        "error": None,
        "lage": None,
        "optimierungen": [],
        "facts": None,
    }
    user: str | None = None
    try:
        states = read_ha_states(ha_url, ha_token)
        live = live_facts(states)
        conn = open_readonly(db)
        try:
            research = research_facts(conn, now)
            research["winter"] = winter_lines(conn, now)
        finally:
            conn.close()
        result["facts"] = {"live": live, "research": research}
        system = Path(soul).read_text(encoding="utf-8")
        context = build_context(live, research, local_now)
        user = (
            "Hier ist der aktuelle Kontext. Antworte genau mit dem JSON-Objekt aus deiner"
            " Anleitung, nichts sonst.\n\n" + context
        )
        answer = parse_answer(call_llm(llm_url, model, system, user))
        lage = answer.get("lage") or {}
        fit_to_card_state(lage, live)
        lage["text_live"] = live_soc_template(str(lage.get("text") or ""), live)
        result.update(answer)
        result["ok"] = True
    except Exception as exc:  # one bad run must still leave a readable file
        log.exception("bithamster run failed")
        result["error"] = f"{type(exc).__name__}: {exc}"[:300]
    write_atomic(result, out)
    if log_db:
        log_entry(log_db, "analyse", result, prompt=user)
    return result


# ---------------------------------------------------------------------------
# Auftraege: buttons and chat in the research tab ("Frag den Hamster")
# ---------------------------------------------------------------------------
#
# The dashboard only writes a request into an input_text ("<task>|<timestamp>",
# set by script.bithamster_auftrag). A cron job polls it every minute with a
# single GET; on a new request it builds the fixed context for that task and
# writes www/bithamster_ask.json. The model still gets text only.

REQUEST_ENTITY = "input_text.bithamster_auftrag"
QUESTION_ENTITY = "input_text.bithamster_frage"
TAB_ENTITY = "input_select.bithamster_tab"
ASK_LIMITS = {"headline": 70, "text": 600, "punkt": 260}
MAX_POINTS = 4
# Reviews over the whole app need more room than a single question.
TASK_MAX_POINTS = {
    "gesamtcheck": 6,
    "karten": 6,
    "tabcheck": 5,
    "entscheidung": 6,
    "schalten": 5,
    "befunde": 6,
    "thesis_woche": 6,
    "thesis_befunde": 6,
    "thesis_risiken": 6,
}
# Master's thesis tasks (bithamster_research.thesis_lines).
THESIS_TASKS = ("thesis_woche", "thesis_befunde", "thesis_risiken")
THESIS_RULES = (
    " Schreibe KEINEN Text für die Arbeit (keine Absätze, keine Formulierungs-"
    "vorschläge), nenne keine Quellen und nimm keine Studienergebnisse vorweg:"
    " die Erhebung läuft, Ergebnisse gibt es noch nicht. Nur Planung, Zuordnung"
    " und Hinweise, jeder Punkt mit Datei, Kapitel oder Datum aus dem Kontext."
)
# Tasks whose points are proposals: repeats of reviewed, rejected proposals
# are removed (bithamster_research.REVIEWED).
PROPOSAL_TASKS = ("optimierung", "verbesserung", "gesamtcheck", "karten", "tabcheck")
# Tasks that get the decision log: (task, hours back) when no day is named.
DECISION_TASKS = {"entscheidung": 24, "schalten": 72}
# Tasks that see every tab, the seasonal check and the data inventory.
OVERVIEW_TASKS = ("gesamtcheck", "karten")
# Tasks about the tab selected in input_select.bithamster_tab.
TAB_TASKS = ("tab", "tabcheck")
# Entities shown in the selected tab, with live value, for "tabcheck".
TAB_ENTITIES_MAX = 45

# energy_states columns worth a card, with a plain German name. energy_price_ct_kwh
# is left out on purpose: the MVP records no exchange price (ha_history_sync,
# decision 21.07.2026), so "empty" is by design, not a gap (eval 13.11.2026
# reported it as missing). The inventory
# says which ones are actually filled, so the model cannot propose a card on
# data that is empty (weather/sun columns were empty from 23.08.2026 on).
DATA_COLUMNS: list[tuple[str, str]] = [
    ("pv_power_w", "Solarleistung"),
    ("house_load_w", "Hausverbrauch"),
    ("battery_soc_pct", "Akku-Ladestand"),
    ("battery_power_w", "Akku-Lade-/Entladeleistung"),
    ("grid_import_w", "Netzbezug"),
    ("grid_export_w", "Einspeisung"),
    ("miner_power_w", "Miner-Leistung"),
    ("heizstab_power_w", "Heizstab-Leistung"),
    ("pv_forecast_kw", "Solarprognose"),
    ("outdoor_temp_c", "Außentemperatur"),
    ("cloud_coverage_pct", "Bewölkung"),
    ("sun_elevation_deg", "Sonnenstand"),
    ("heizung_energy_kwh_today", "Heizungs-Energie"),
]
# (table, date column, German description, words a card built on it uses).
# The date column makes "stale" visible: decision_events had 259 rows, all
# from a Python core test run on 02.07.2026 (production steers in HA YAML
# and writes none). Counting rows only, the model proposed a "Regel-Log"
# card with "the data is all there" (live 13.11.2026).
DATA_TABLES: list[tuple[str, str, str, tuple[str, ...]]] = [
    (
        "miner_states",
        "block_id",
        "Miner je 10 Minuten: befohlener und gemeldeter Modus, Temperatur",
        (),
    ),
    (
        "daily_kpi",
        "day",
        "Tageswerte: Energie, Akku-Bänder, Überschuss, Schaltfehler",
        (),
    ),
    (
        "daily_miner_kpi",
        "day",
        "Tageswerte je Miner: Stunden je Modus, W pro TH, Temperatur",
        (),
    ),
    ("bitcoin_daily_settlement", "day", "Poolertrag je Tag", ()),
    ("btc_price_daily", "day", "Bitcoin-Kurs je Tag", ()),
    (
        "decision_events",
        "block_id",
        "Entscheidungs-Ereignisse des Python-Kerns (nur Testbetrieb, NICHT die"
        " Produktion)",
        ("python-kern", "decision_events"),
    ),
    # Since 14.11.2026 (ADR 034): the production log. Live the same day the
    # hamster still called the decision data "stale since July" because only
    # decision_events was listed here.
    (
        "ha_decision_log",
        "timestamp",
        "Entscheidungsprotokoll der Produktion: Moduswechsel und Regelwechsel"
        " mit Begründung des Watchdogs (Karten Schaltwechsel, Ungenutzter"
        " Überschuss)",
        (),
    ),
    (
        "ha_diagnose_log",
        "timestamp",
        "Soll-Ist-Diagnose je Miner inklusive Handbetrieb",
        (),
    ),
    (
        "settings_history",
        "timestamp",
        "Verlauf der Schaltschwellen und Saisonwerte",
        (),
    ),
]
INVENTORY_DAYS = 14
# A table whose newest row is older than this is "stale" (no card on it).
STALE_DAYS = 3

# Existing cards by content, not by name (live 13.11.2026: "Akku über Nacht-
# Historie: morgendlicher Akkustand vs. Netzbezug nachts" passed the name
# filter although the card Akku über Nacht shows exactly that). A proposal is a
# duplicate if its text contains every word of one group (lower case,
# substring). Keep groups narrow: two or three words that only this card
# combines.
CARD_TOPICS: dict[str, list[tuple[str, ...]]] = {
    "Akku über Nacht": [
        ("nachtbilanz",),
        ("morgen", "akku", "netz"),
        ("hausreserve", "nacht"),
        ("grundlast", "nacht"),
        # Live 14.11.2026: "Akku-Entleerung nachts" proposed as a new card.
        ("entl", "nacht"),
        ("akku", "nachts"),
    ],
    # energy_to_sats_chart.yaml (Tab Bitcoin), live 13.11.2026 "Sats pro kWh Trend".
    "Mining-Effizienz": [("sats", "kwh")],
    "Solarprognose": [("prognose", "ist"), ("prognose", "gemessen")],
    "Hardware-Zustand (W/TH)": [("w pro th",), ("w/th",), ("watt je th",)],
    "Saisonale Schwellwerte": [("saison", "schwell")],
    # Live 13.11.2026: "Saison-Status: welche Stufen gesperrt sind (Nur Eco)".
    "Saisonsteuerung": [("saison", "gesperrt"), ("saison", "stufe"), ("nur eco",)],
    "Lücken": [("lücken",), ("aufzeichnung", "fehl")],
    # Since 14.11.2026 status, calendar per day and gaps are one card.
    "Datenaufzeichnung": [
        ("lücken",),
        ("aufzeichnung", "fehl"),
        ("aufzeichnung", "tag"),
        ("aufzeichnung", "kalender"),
    ],
    # Automation cards since 14.11.2026 (src/data/automation_cards.py).
    "Ungenutzter Solarüberschuss": [
        ("überschuss", "ungenutzt"),
        ("einspeis", "miner"),
        ("überschuss", "miner"),
    ],
    "Schaltwechsel": [("schaltwechsel",), ("flapping",), ("start", "stopp")],
    "Temperatur und Schaltfehler": [
        ("übertemp",),
        ("schaltfehler",),
        ("chip", "temperatur"),
    ],
    "Masterarbeit": [("masterarbeit",), ("thesis",)],
    "Akku-Höchststand und Start": [
        ("höchst", "akku"),
        ("akku", "eco-start"),
        ("akku-start",),
        ("akku", "start-schwelle"),
        ("akku", "für den start"),
        # The card also holds the note "Heizstab nahm X kWh, Akku nicht voll";
        # live 14.11.2026 proposed as new card "Heizstab vs. Akku".
        ("heizstab", "akku"),
    ],
    # Übersicht: PV, Verbrauch, Akku als Tageskurve (live 13.11.2026 schlug
    # "Tab verbessern" genau das für den Tab Energie vor).
    "Tagesverlauf": [
        ("solar", "verbrauch", "verlauf"),
        ("solarproduktion", "hausverbrauch"),
        ("solarerzeugung", "hausverbrauch"),
        ("solarerzeugung", "verbrauch"),
        ("netzbezug", "verlauf"),
    ],
}

# task -> (label shown on the card, instruction for the model)
TASKS: dict[str, tuple[str, str]] = {
    "optimierung": (
        "Optimierung finden",
        "Finde in den Daten die wichtigste Stellschraube der Automatik (Schwellen,"
        " Stufen, Zeiten), mit der mehr eigener Solarstrom zu Sats wird, ohne Akku"
        " oder Hardware zu gefährden. Pro Punkt: Befund mit Zahl, Idee, woran man"
        " es merkt.",
    ),
    "aufzeichnung": (
        "Datenaufzeichnung prüfen",
        "Prüfe anhand des Aufzeichnungsstatus, ob die nächtliche Datenaufzeichnung"
        " zuverlässig läuft: Lücken, unvollständige Tage, letzter Sync, Backup. Sag"
        " klar, ob alles in Ordnung ist und was als Nächstes zu tun wäre.",
    ),
    "fehler": (
        "Fehler finden",
        "Suche in Live-Werten, Gate-Diagnose, Schaltfehlern und Aufzeichnungsstatus"
        " nach Dingen, die nicht stimmen oder nicht verfügbar sind. Trenne klar"
        " zwischen echtem Fehler und normalem Verhalten (zum Beispiel Winter).",
    ),
    "verbesserung": (
        "Verbesserungsvorschläge",
        "Gib Vorschläge für den Haushalt: wie man Netzbezug senkt und mehr eigenen"
        " Solarstrom selbst nutzt (Verbrauch in Sonnenstunden, Heizstab, Akku). Nur"
        " was die Zahlen hergeben.",
    ),
    "tab": (
        "Tab erklären",
        "Erkläre in einfachen Worten, was der genannte Tab zeigt, Karte für Karte,"
        " und was die wichtigsten aktuellen Werte bedeuten. Nimm nur die"
        " aufgezählten Karten, erfinde keine.",
    ),
    "gesamtcheck": (
        "Alles prüfen",
        "Schau über die ganze Anwendung: alle Tabs mit ihren Karten, die saisonale"
        " Automatik (Tabelle und Messung der echten Nächte), Forschungsdaten,"
        " Aufzeichnung und Verfügbarkeit. Nenne die wichtigsten Befunde, der"
        " größte Nutzen zuerst: was nicht stimmt, wo die Automatik Ertrag"
        " verschenkt oder Netzstrom zieht, was im Dashboard unklar ist. Jeder"
        " Punkt mit Zahl aus dem Kontext und dem Tab, in dem man es sieht.",
    ),
    "karten": (
        "Fehlende KPI-Karten",
        "Welche KPI-Karten fehlen im Dashboard, damit du Optimierungen und Fehler"
        " besser findest und der Nutzer die Automatik besser versteht? Schlag nur"
        " Karten vor, deren Daten laut DATENBESTAND gefüllt und aktuell sind,"
        " und keine, die es laut Tab-Liste schon gibt, auch nicht unter anderem"
        " Namen (gleiche Frage = gleiche Karte). Behaupte nicht pauschal, alle"
        " Daten seien da. Pro Punkt: Kartenname, in welchen Tab, welche Frage"
        " sie beantwortet, welche Daten.",
    ),
    "tabcheck": (
        "Tab verbessern",
        "Schau dir den genannten Tab an: seine Karten und die Werte, die sie"
        " auswerten (Liste SENSORWERTE). Die Liste enthält ROHE Sensorwerte, nicht"
        " den Karteninhalt: die Karten rechnen und formatieren selbst (BTC mit"
        " Dezimalkomma und in Sats, Euro, Prozent, Balken, Diagramme). Ein Rohwert"
        " wie 5.6e-07 oder ein Zustand wie OK ist darum KEIN Anzeigefehler, und"
        " 'die Karte zeigt nur X' darfst du daraus nicht schließen. Kritisiere nur"
        " Inhalte: falsche Zuordnung, fehlende, veraltete oder nicht verfügbare"
        " Werte. Finde, was man an diesem Tab"
        " besser machen kann: Werte, die unklar, doppelt, veraltet oder nicht"
        " verfügbar sind; was zum Verstehen oder Optimieren fehlt (nur mit"
        " gefüllten, aktuellen Daten laut DATENBESTAND); was weg kann. Nichts"
        " vorschlagen, was es in einem anderen Tab schon gibt, dann den Tab"
        " nennen. Eine Karte, die im Winter wenig zeigt (Miner ruhen), ist nicht"
        " überflüssig: sie wird im Sommer gebraucht, schlage dafür kein Entfernen"
        " vor. Pro Punkt: welche Karte, was genau, warum, mit Zahl oder Wert"
        " aus dem Kontext.",
    ),
    # 14.11.2026: the researcher tasks, built on the decision log (ADR 034)
    # and the findings of the research cards.
    "entscheidung": (
        "Entscheidungen erklären",
        "Erkläre die Entscheidungen der Steuerung im ENTSCHEIDUNGSPROTOKOLL:"
        " welcher Miner wann in welchen Modus ging und warum, mit Uhrzeit, Regel"
        " und Akkustand. Fasse gleiche Vorgänge zusammen (zum Beispiel jede"
        " Nacht derselbe Stopp). Ein kurzes Aus unter 15 Minuten ist ein"
        " Verbindungsabbruch, keine Entscheidung. Steht kein Wechsel im"
        " Protokoll, sag, warum die Automatik nichts tun musste.",
    ),
    "schalten": (
        "Schaltverhalten prüfen",
        "Bewerte das Schaltverhalten der Automatik anhand der FORSCHUNGSBEFUNDE"
        " und des ENTSCHEIDUNGSPROTOKOLLS: Schaltwechsel gegen das Ziel,"
        " Abbrüche, Schwellen-Änderungen, ungenutzter Überschuss. Was ist"
        " gewollt, was ist ein Problem, was lässt sich an Schwellen oder"
        " Wartezeiten verbessern? Jeder Punkt mit Zahl.",
    ),
    "befunde": (
        "Befunde einordnen",
        "Ordne die FORSCHUNGSBEFUNDE für jemanden ein, der die Anlage nicht"
        " kennt: Was zeigen die Daten belastbar, was nur mit Vorbehalt (wenige"
        " Tage, nicht gemessene Tage, Winter), und was lässt sich daraus NICHT"
        " schließen? Keine neuen Ursachen erfinden; eine Zahl allein ist noch"
        " keine Ursache.",
    ),
    "thesis_woche": (
        "Masterarbeit: diese Woche",
        "Was ist laut Zeitplan und offenen Punkten DIESE WOCHE dran? Ordne nach"
        " Dringlichkeit: zuerst, was andere Punkte blockiert oder Vorlauf"
        " braucht (Antwort von Betreuung oder Prüfungsamt, Export aus dem"
        " Labornetz), dann das Schreibziel der Woche." + THESIS_RULES,
    ),
    "thesis_befunde": (
        "Masterarbeit: Befunde zuordnen",
        "Ordne die Punkte der MERKLISTE PRODUKTIVBEFUNDE den Kapiteln zu"
        " (4 System, 5 Methodik, 7 Diskussion/Limitationen) und sag zu jedem,"
        " mit welcher Einschränkung er berichtet werden muss. Warne, wo eine"
        " Zahl mehr behaupten würde, als die Daten tragen." + THESIS_RULES,
    ),
    "thesis_risiken": (
        "Masterarbeit: Risiken bis Abgabe",
        "Was gefährdet die Abgabe am Stichtag? Prüfe Tage bis zur Abgabe gegen"
        " Zeitplan, offene Punkte und Marker: Wo ist der Plan schon im Verzug,"
        " welche Klärungen brauchen Vorlauf, welche Kapitel sind am weitesten"
        " zurück (Wörter, fehlt-Marker)? Größtes Risiko zuerst." + THESIS_RULES,
    ),
    "frage": (
        "Frage",
        "Beantworte die Frage des Nutzers aus dem Kontext. Geben die Daten die"
        " Antwort nicht her, sag das ehrlich.",
    ),
}

# Cards without a group_header title, described by hand.
TAB_NOTES: dict[str, list[str]] = {
    "Übersicht": [
        "BitGridAI (Hamster-Karte: was die Automatik gerade macht, dazu Blockzeit,"
        " Balance und Bitcoin-Kurs)"
    ],
    "Grundriss": ["Grundriss des Hauses mit Geräten, Leistungen und Raumtemperaturen"],
}


def read_ha_state(
    base_url: str, token: str, entity: str, timeout: int = HA_TIMEOUT_S
) -> dict[str, Any] | None:
    """One entity via GET /api/states/<entity_id>; None if it does not exist."""
    req = Request(
        base_url.rstrip("/") + "/api/states/" + entity,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed local URL)
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    return data if isinstance(data, dict) else None


def parse_request(state: Any) -> str | None:
    """Task key from "<task>|<timestamp>", or None for empty/unknown values."""
    text = str(state or "")
    task = text.split("|", 1)[0].strip()
    return task if "|" in text and task in TASKS else None


def dashboard_tabs(path: str | Path) -> dict[str, list[str]]:
    """Tab title -> card titles, read from the dashboard YAML (group_header names)."""
    tabs: dict[str, list[str]] = {}
    current: str | None = None
    pending = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  - title: (.+)$", line)
        if m:
            current = m.group(1).strip().strip("\"'")
            tabs[current] = list(TAB_NOTES.get(current, []))
            continue
        if current and re.match(r"^\s+template: group_header\s*$", line):
            pending = 4
            continue
        if pending and current:
            pending -= 1
            m = re.match(r"^\s+name: (.+)$", line)
            if m:
                tabs[current].append(m.group(1).strip().strip("\"'"))
                pending = 0
    return tabs


_ENTITY_RE = re.compile(
    r"\b((?:sensor|binary_sensor|input_number|input_select|input_boolean|"
    r"input_text|switch|select|number|climate|weather|sun|automation|script|"
    r"button|light|calendar|todo)\.[a-z0-9_]+)\b"
)


# UI controls (view switches, selectors) are not values the user reads; live
# 13.11.2026 the hamster built a "contradiction" from input_boolean.fp_view_garage.
# Navigation helpers stored as numbers (calendar month offset, sim step).
_NAV_HELPER = re.compile(r"^input_number\.\w*(offset|sim_)")
_CONTROL_DOMAINS = (
    "input_select.",
    "input_boolean.",
    "input_text.",
    "sun.",
    "button.",
    "script.",
    "automation.",
)


def _with_includes(folder: Path, text: str, limit: int = 40) -> str:
    """Text plus every file it includes, recursively (relative to the includer)."""
    parts = [text]
    queue = [(folder, text)]
    seen: set[Path] = set()
    while queue:
        where, part = queue.pop(0)
        for inc in re.findall(r"!include\s+([\w./-]+\.yaml)", part):
            target = (where / inc).resolve()
            if target in seen or len(seen) >= limit:
                continue
            seen.add(target)
            try:
                content = target.read_text(encoding="utf-8")
            except OSError:
                continue
            parts.append(content)
            queue.append((target.parent, content))
    return "\n".join(parts)


def _tab_body(path: Path, tab: str) -> str:
    m = re.search(
        rf"^  - title: [\"']?{re.escape(tab)}[\"']?\s*$(.*?)(?=^  - title: |\Z)",
        path.read_text(encoding="utf-8"),
        flags=re.M | re.S,
    )
    return m.group(1) if m else ""


def tab_source(path: str | Path, tab: str) -> str:
    """YAML text of one tab plus everything it includes, recursively."""
    base = Path(path)
    body = _tab_body(base, tab)
    return _with_includes(base.parent, body) if body else ""


def tab_card_sources(path: str | Path, tab: str) -> list[tuple[str, str]]:
    """(card title, YAML incl. includes) per group_header section of the tab.

    A flat list let the model attach values to the wrong card (device energy
    counters of the history card "in Aktueller Verbrauch", live 13.11.2026).
    Text before the first header is "ohne Titel".
    """
    base = Path(path)
    body = _tab_body(base, tab)
    if not body:
        return []
    lines = body.splitlines()
    heads = [
        i
        for i, ln in enumerate(lines)
        if re.match(r"^\s+template: group_header\s*$", ln)
    ]
    cuts = [0] + heads + [len(lines)]
    out: list[tuple[str, str]] = []
    for a, b in zip(cuts, cuts[1:]):
        if a == b:
            continue
        title = "ohne Titel"
        if a in heads:
            for ln in lines[a + 1 : a + 5]:
                m = re.match(r"^\s+name: (.+)$", ln)
                if m:
                    title = m.group(1).strip().strip("\"'")
                    break
        # The section's own lines only start after the header card; lines in
        # front of the header (layout of the previous stack) belong to it too.
        out.append((title, _with_includes(base.parent, "\n".join(lines[a:b]))))
    return out


# Template sensors without a friendly name ("typ_computer_power_w"). Eval
# 13.11.2026: the model read the device group "Computer" as the miners.
_GROUP_WORDS = {
    "mining": "Mining (Miner-Steckdosen)",
    "computer": "Computer (PCs, Server, NAS, Router; NICHT die Miner)",
    "kuehlung": "Kühlung (Kühlschränke)",
    "unterhaltung": "Unterhaltung (TV)",
    "warmwasser": "Warmwasser",
    "haushaltsgeraete": "Haushaltsgeräte (Waschen, Spülen, Trocknen)",
    "sonstiges": "Sonstiges",
}


# Raw device names the hamster misread (13.11.2026: "Power1_solar, Karte ohne
# Titel"); same wording as the rows in views/heizstab.yaml.
_ENTITY_LABELS: dict[str, str] = {
    "sensor.ac_elwa_2_power1_solar": "Heizstab Leistung Solar (jetzt)",
    "sensor.ac_elwa_2_power1_grid": "Heizstab Leistung Netz (jetzt)",
    "sensor.ac_elwa_2_temperatur_1": "Heizstab Temperatur Kessel",
    "sensor.ac_elwa_2_screen_mode": "Heizstab Zustand (Standby = heizt nicht)",
}


def entity_label(entity: str, friendly: Any) -> str:
    """Readable name; groups and rooms get their meaning spelled out."""
    if entity in _ENTITY_LABELS:
        return _ENTITY_LABELS[entity]
    obj = entity.split(".", 1)[-1]
    m = re.match(r"typ_(\w+?)_power_w$", obj)
    if m:
        return "Gerätegruppe " + _GROUP_WORDS.get(m.group(1), m.group(1))
    m = re.match(r"raum_(\w+?)_power_w$", obj)
    if m:
        return "Raum " + m.group(1).replace("_", " ").capitalize()
    return str(friendly or entity)


# What custom-rendered cards display (their JS formats the raw values).
# Live 13.11.2026: from raw sensor values the hamster concluded "Abzahlung
# shows only the 400 EUR input" and "Langzeitbilanz shows only OK".
CARD_SHOWS: dict[str, str] = {
    "Poolerträge": "Balance, Gesamteinnahmen, Gesamtauszahlung, Ertrag gestern"
    " und heute (Schätzung), jeweils in BTC, Sats und Euro. Die Balance ist die"
    " Summe seit März 2026, fast ganz von den Avalon-Minern im Sommer",
    "Hardware-Abzahlung": "Prozent abbezahlt mit Balken, Investition (Summe der"
    " Geräteliste), Ertrag bisher in Euro und Sats, Noch offen in Euro",
    "Mining Verlauf": "Tabelle je Tag (Woche/Monat blätterbar): Start, Stopp,"
    " Laufzeit gesamt und je Modus, Energie kWh, Pool-Hashrate (inkl. Bitaxe),"
    " Sats, Sats pro kWh, Euro pro kWh",
    "Langzeitbilanz": "Balkendiagramm Sats je Monat (oder Jahr), Monatsertrag"
    " gesamt und Monatsdurchschnitt in Sats und Euro",
    "Bitcoin-Kurs": "Kursdiagramm BTC/EUR, BTC/USD und Power-Law, Zeitraum"
    " 1 Tag bis Max, Veränderung in Prozent",
    "Mining-Effizienz": "Balkendiagramm Sats pro kWh je Tag (Woche/Monat),"
    " Tagesdurchschnitt und Ziel; nur in diesem Tab",
    "Heizung (Öl)": "Tagesverlauf Brenner an/aus, Tabelle Status, aktuelle"
    " Leistung und Energie heute (Strom des Brenners, kein Ölverbrauch)",
    "Heizstab (elektrisch)": "Tagesverlauf Leistung und Kesseltemperatur,"
    " Tabelle Zustand, Temperatur, Leistung Solar und Leistung Netz",
    "Akku über Nacht": "je Nacht: Akku abends und morgens, Entladung, Netzbezug,"
    " Grundlast, ob die Hausreserve gereicht hat (aus 10-Minuten-Blöcken)",
    "Datenaufzeichnung": "Ampel der Aufzeichnung, letzter Abgleich und Backup,"
    " Monatskalender mit Blöcken je Tag, Lücken und unvollständige Tage seit"
    " Aufzeichnungsbeginn",
    "Ungenutzter Solarüberschuss": "je Monat Stunden und kWh Einspeisung über 1 kW"
    " bei stehenden Minern, mit dem Grund aus der Diagnose der Automatik",
    "Schaltwechsel": "je Monat Tage über dem Ziel von 2 Start/Stopp-"
    "Wechseln, Mittel, Höchstwert, Stunden im Handbetrieb, letzte 14 Tage",
    "Temperatur und Schaltfehler": "je Monat und Miner höchste"
    " Chip-Temperatur, Blöcke ab 110 °C, Schaltfehler",
    "Masterarbeit": "Merkliste der Befunde und offenen Punkte für die"
    " Thesis; keine Karte zum Verbessern",
    "Akku-Höchststand und Start": "je Tag höchster Akkustand gegen die"
    " Eco-Start-Schwelle, dazu Hinweis wie viel kWh der Heizstab nahm, während"
    " der Akku nicht voll war",
}


def tab_value_lines(
    path: str | Path, tab: str, states: dict[str, dict[str, Any]]
) -> list[str]:
    """Values the tab shows, grouped by card, with friendly name (read-only).

    Card titles alone gave generic advice; with the values the hamster sees
    what the user sees (unavailable, stale, odd numbers). Only entities that
    exist in HA count, UI controls are left out, at most TAB_ENTITIES_MAX.
    """
    lines: list[str] = []
    shown: set[str] = set()
    total = 0
    for title, text in tab_card_sources(path, tab):
        ents = []
        for ent in _ENTITY_RE.findall(text):
            if (
                ent in states
                and ent not in shown
                and not ent.startswith(_CONTROL_DOMAINS)
                and not _NAV_HELPER.search(ent)
            ):
                shown.add(ent)
                ents.append(ent)
        if not ents:
            continue
        lines.append(f"Karte {title}:")
        if title in CARD_SHOWS:
            lines.append(f"  (Die Karte zeigt: {CARD_SHOWS[title]})")
        for ent in ents:
            total += 1
            if total > TAB_ENTITIES_MAX:
                continue
            st = states[ent]
            attrs = st.get("attributes") or {}
            name = entity_label(ent, attrs.get("friendly_name"))
            unit = attrs.get("unit_of_measurement") or ""
            value = str(st.get("state"))
            if value in ("unknown", "unavailable"):
                value = value.upper()
            elif ent.startswith("climate.") and attrs.get("current_temperature"):
                # Live 14.11.2026: from the bare state "heat" the hamster
                # concluded the rooms have no temperature at all.
                cur = float(attrs["current_temperature"])
                value = f"{value}, Raum {de_num(cur, 1)} °C"
            elif re.fullmatch(r"-?\d+\.\d+", value):
                # HA states use a decimal point; the hamster writes German
                # ("37,4"), and the number check compares with the context
                # (live 13.11.2026: "37,4", "0,873" flagged as invented).
                digits = min(len(value.split(".")[1]), 3)
                value = de_num(float(value), digits)
            # Diagnosis sensors carry the reason in an attribute; the state
            # alone ("ok") made the model call the card uninformative.
            why = attrs.get("summary")
            extra = f" ({_clip(str(why), 140)})" if why else ""
            lines.append(
                f"- {name} ({ent}): {value}{' ' + unit if unit else ''}{extra}"
            )
    if total > TAB_ENTITIES_MAX:
        lines.append(f"- ... und {total - TAB_ENTITIES_MAX} weitere Werte.")
    return lines


def research_card_lines(path: str | Path, tab: str) -> list[str]:
    """What the JSON-backed research cards show right now (Tab Forschung).

    They read www/research_cards.json in the browser, so tab_value_lines sees
    no entity and the model called them empty ("Solarprognose: der
    Vergleich fehlt", eval 13.11.2026). One line per card with its headline
    numbers, from the same file the cards render.
    """
    if tab != "Forschung":
        return []
    d = _read_json(path)
    if not d:
        return ["Karten aus research_cards.json: Datei nicht lesbar."]
    lines: list[str] = []
    nights = d.get("nights") or {}
    months = nights.get("months") or []
    if months:
        lines.append(
            "Karte Akku über Nacht (eine Zeile je Monat, darunter die letzten Nächte):"
        )
        for m in months:
            judged = (
                f"Urteil {m['verdict']}"
                if m.get("verdict")
                else "noch kein Urteil (zu wenige Nächte nach Mining-Tagen)"
            )
            lines.append(
                f"- Monat {m['month']}: {m.get('nights')} Nächte, davon"
                f" {m.get('mined_nights')} nach Mining-Tagen; {judged}."
            )
        recent = nights.get("recent") or []
        if recent:
            last = recent[-1]
            lines.append(
                f"- {len(recent)} letzte Nächte als Balken, zuletzt {last.get('day')}:"
                f" morgens {de_num(last.get('morning_soc'), 0)} % Akku."
            )
    f = d.get("forecast") or {}
    if f.get("days_used"):
        lines += [
            "Karte Solarprognose:",
            f"- {f['days_used']} Tage verglichen, Prognose im Mittel"
            f" {de_num(f.get('bias_pct'), 0)} % daneben (positiv = zu hoch), mittlere"
            f" Abweichung je Tag {de_num(f.get('mae_pct'), 0)} %; Tagesbalken und"
            " Profil nach Tageszeit.",
        ]
    eff = (d.get("efficiency") or {}).get("miners") or []
    if eff:
        lines.append("Karte Hardware-Zustand (W/TH):")
        lines += [
            f"- {m['miner']}: {m.get('verdict') or 'kein Urteil'},"
            f" Änderung {de_num(m.get('change_pct'))} % seit dem ersten Monat"
            for m in eff
        ]
    peak = d.get("peak") or []
    if peak:
        started = sum(1 for x in peak if not x.get("missing"))
        best = max(x["soc_max"] for x in peak)
        lines += [
            "Karte Akku-Höchststand und Start:",
            f"- an {started} von {len(peak)} Tagen Start möglich, bester Tag"
            f" {de_num(best, 0)} % Akku, Eco-Start {de_num(peak[-1]['eco_start'], 0)} %.",
        ]
    return lines


def local_ts(iso: Any) -> str:
    """ISO timestamp (UTC in the status JSON) as local "dd.mm. HH:MM"."""
    try:
        ts = datetime.fromisoformat(str(iso))
    except ValueError:
        return "unbekannt"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone().strftime("%d.%m. %H:%M")


def recording_lines(status: dict[str, Any] | None) -> list[str]:
    """Recording status JSON (src/data/recording_status.py) as context lines."""
    if not status:
        return ["- Aufzeichnungsstatus nicht lesbar (Datei fehlt)."]
    lines = [
        f"- Ampel: {status.get('level')}, erzeugt {local_ts(status.get('generated_at'))} Uhr.",
    ]
    lines += [f"- Hinweis: {r}" for r in status.get("reasons") or []]
    sync = status.get("sync") or {}
    if sync:
        lines.append(
            f"- Letzter Sync: {local_ts(sync.get('last_start'))} Uhr,"
            f" {'erfolgreich' if sync.get('ok') else 'nicht erfolgreich'},"
            f" +{sync.get('blocks_added')} Blöcke, geplant täglich {sync.get('schedule')} Uhr."
        )
    h = status.get("history") or {}
    if h:
        lines.append(
            f"- Seit {h.get('first_day')}: {h.get('days_complete')} von {h.get('days_total')}"
            f" Tagen vollständig, {h.get('days_missing')} fehlen,"
            f" {h.get('days_partial')} unvollständig."
        )
        for r in (h.get("missing_ranges") or [])[:8]:
            lines.append(
                f"- Fehlt: {r.get('from')} bis {r.get('to')} ({r.get('days')} Tage)"
            )
        # Live 14.11.2026: without these lines the hamster reported "173 of
        # 173 days complete, no problems" although 117 h were stored but not
        # measured (recording_status.suspect_runs).
        runs = [r for r in h.get("suspect_runs") or [] if r.get("blocks", 0) >= 6]
        if runs:
            kinds = {"held": "Werte eingefroren", "zero": "Hausverbrauch 0 W"}
            total_h = sum(r["blocks"] for r in runs) / 6
            lines.append(
                f"- ACHTUNG, vollständig heißt nicht gemessen: {de_num(total_h, 0)}"
                f" Stunden in {len(runs)} Zeiträumen sind gespeichert, aber nicht"
                " gemessen (Home Assistant lieferte keine Werte). Diese Tage zählen"
                " oben als vollständig, ihre Tageswerte sind falsch."
            )
            for r in sorted(runs, key=lambda x: -x["blocks"])[:5]:
                lines.append(
                    f"- Nicht gemessen: ab {local_ts(r.get('from'))} Uhr,"
                    f" {de_num(r['blocks'] / 6, 1)} h, {kinds.get(r['kind'], r['kind'])}"
                )
    return lines


def error_lines(states: dict[str, dict[str, Any]], live: dict[str, Any]) -> list[str]:
    """Unavailable key entities and non-ok gate diagnosis (deterministic)."""
    watched = list(LIVE_ENTITIES.values()) + [e for _, e, _ in THRESHOLDS]
    watched += list(DIAGNOSE_ENTITIES.values())
    down = [
        e
        for e in watched
        if (states.get(e) or {}).get("state") in (None, "unknown", "unavailable")
    ]
    lines = [
        (
            f"- Nicht verfügbar: {', '.join(down)}."
            if down
            else "- Alle wichtigen Sensoren und Schwellen liefern Werte."
        )
    ]
    for d in live["diagnose"]:
        if d["code"] not in ("ok", None):
            lines.append(f"- Diagnose {d['name']} meldet {d['code']}: {d['summary']}")
    return lines


def season_context(
    conn: sqlite3.Connection, states: dict[str, dict[str, Any]], now: datetime
) -> tuple[list[str], list[str]]:
    """Seasonal table with today's settings plus the measured nights.

    Returns (context lines, short findings for the priority list).
    """
    st = settings_from_states(states)
    table = season_table(
        st["baseload_w"],
        st["capacity_kwh"],
        st["gap_h"],
        st["efficiency"],
        st["floor_pct"],
    )
    checks = night_check(
        conn, st["capacity_kwh"], efficiency=st["efficiency"], floor_pct=st["floor_pct"]
    )
    lines = season_lines(table, checks, st, now.astimezone().month)
    return lines, season_findings(table, checks)


def data_inventory(conn: sqlite3.Connection, now: datetime) -> dict[str, Any]:
    """Filled share per energy_states column (last INVENTORY_DAYS days), table sizes."""
    start = (now - timedelta(days=INVENTORY_DAYS)).strftime("%Y-%m-%d")
    inv: dict[str, Any] = {"blocks": 0, "columns": [], "tables": []}
    try:
        # Column and table names are module constants, never user input.
        cols = ", ".join(f"COUNT({c})" for c, _ in DATA_COLUMNS)
        row = conn.execute(
            f"SELECT COUNT(*), {cols} FROM energy_states WHERE block_id >= ?",
            (start,),
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if row and row[0]:
        inv["blocks"] = int(row[0])
        inv["columns"] = [
            (name, 100.0 * int(count or 0) / int(row[0]))
            for (_, name), count in zip(DATA_COLUMNS, row[1:])
        ]
    today = now.astimezone(timezone.utc).date()
    for table, col, desc, _ in DATA_TABLES:
        try:
            n, last = conn.execute(
                f"SELECT COUNT(*), MAX({col}) FROM {table}"
            ).fetchone()
        except sqlite3.OperationalError:
            n, last = 0, None
        age = None
        if last:
            try:
                age = (today - datetime.fromisoformat(str(last)[:10]).date()).days
            except ValueError:
                age = None
        stale = bool(n) and (age is None or age > STALE_DAYS)
        inv["tables"].append(
            (desc, int(n or 0), str(last)[:10] if last else None, stale)
        )
    return inv


def empty_columns(inv: dict[str, Any]) -> list[str]:
    """Names of columns filled in less than half of the blocks."""
    return [name for name, pct in inv["columns"] if pct < 50]


def inventory_lines(inv: dict[str, Any]) -> list[str]:
    """Data inventory as context lines ("only propose cards on filled data")."""
    lines = [
        "DATENBESTAND der Forschungs-DB (gefüllter Anteil der 10-Minuten-Blöcke,"
        f" letzte {INVENTORY_DAYS} Tage; unter 50 % taugt nicht für eine Karte)"
    ]
    if inv["blocks"]:
        filled = [f"{n} {de_num(p, 0)} %" for n, p in inv["columns"] if p >= 50]
        empty = [f"{n} {de_num(p, 0)} %" for n, p in inv["columns"] if p < 50]
        lines.append("- Gefüllt: " + ", ".join(filled) + ".")
        if empty:
            lines.append(
                "- LEER oder lückenhaft, dafür KEINE Karte vorschlagen: "
                + ", ".join(empty)
                + "."
            )
    else:
        lines.append("- Blockdaten nicht lesbar.")
    for desc, n, last, stale in inv["tables"]:
        if not n:
            state = "LEER, keine Karte darauf bauen"
        elif stale:
            state = (
                f"VERALTET, letzte Zeile {last}, kommt nichts mehr dazu. Keine Karte"
                " darauf bauen und nicht behaupten, die Daten seien da"
            )
        else:
            state = f"{n} Zeilen bis {last}"
        lines.append(f"- Tabelle {desc}: {state}.")
    return lines


def unusable_data_words(inv: dict[str, Any] | None) -> list[str]:
    """Words of cards that would need empty or stale tables."""
    if not inv:
        return []
    words: list[str] = []
    for (_, _, _, kw), (_, n, _, stale) in zip(DATA_TABLES, inv["tables"]):
        if not n or stale:
            words += list(kw)
    return words


def drop_unsupported_cards(
    points: list[str], inv: dict[str, Any] | None
) -> tuple[list[str], list[str]]:
    """Remove card proposals built on empty or stale data (see DATA_TABLES)."""
    words = unusable_data_words(inv)
    keep: list[str] = []
    dropped: list[str] = []
    for point in points:
        low = point.lower()
        (dropped if any(w in low for w in words) else keep).append(point)
    return keep, dropped


def priority_findings(
    season: list[str],
    inv: dict[str, Any] | None,
    research: dict[str, Any],
    recording: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Findings the model must not skip ("Alles prüfen"), each with check keys.

    The live run on 13.11.2026 answered "Automatik korrekt" although the
    context said "HAUSRESERVE ZU NIEDRIG" for September and October. As with
    the other verdicts, the selection happens here; ``keys`` are words that
    must appear in one answer point for the finding to count as mentioned.
    """
    out: list[dict[str, Any]] = []
    for text in season:
        month = next((m for m in MONTHS_DE.values() if f" {m}:" in text), None)
        # Month name is enough: "Oktober: Miner stoppten bei 75 %" is the
        # same finding without the word Hausreserve (live 13.11.2026 it was
        # added a second time).
        # Eval 13.11.2026 evening: "seit 13.11. auf 95 % korrigiert" (right:
        # 90 %) counted as mentioned; with the value as key the fixed text is
        # put in front instead.
        now_value = re.search(r"gilt (\d+) %", text)
        keys = [month or "Hausreserve"]
        if now_value:
            keys.append(now_value.group(1) + " %")
        out.append({"text": text, "keys": keys})
    empty = empty_columns(inv) if inv else []
    if empty:
        out.append(
            {
                "text": (
                    f"Datenaufzeichnung: {', '.join(empty)} sind in den letzten"
                    f" {INVENTORY_DAYS} Tagen leer. Ohne sie lässt sich Wetter nicht"
                    " mit Ertrag und Verbrauch vergleichen (Tab Forschung)."
                ),
                "keys": [empty[0]],
            }
        )
    hours = research.get("surplus_idle_hours") or 0
    if hours:
        out.append(
            {
                "text": (
                    f"{de_num(hours)} Stunden Überschuss bei stehenden Minern in"
                    f" {research.get('window_days')} Tagen (Tab Forschung)."
                ),
                "keys": ["Überschuss"],
            }
        )
    missing = ((recording or {}).get("history") or {}).get("days_missing")
    if missing:
        out.append(
            {
                "text": (
                    f"Aufzeichnung: {missing} Tage fehlen in der Forschungs-DB"
                    " (Tab Forschung, Karte Lücken)."
                ),
                "keys": [str(missing)],
            }
        )
    return out


def finding_mentioned(finding: dict[str, Any], answer: dict[str, Any]) -> bool:
    """True if one answer point (or the text) contains all keys of the finding."""
    keys = [k.lower() for k in finding["keys"] if k]
    parts = [answer.get("text") or ""] + list(answer.get("punkte") or [])
    return any(all(k in p.lower() for k in keys) for p in parts)


def ensure_findings(
    answer: dict[str, Any], findings: list[dict[str, Any]], max_points: int
) -> list[str]:
    """Put skipped priority findings in front, marked as computed. Returns them."""
    missing = [f for f in findings if not finding_mentioned(f, answer)]
    added = [
        _clip("Fest berechnet: " + f["text"], ASK_LIMITS["punkt"]) for f in missing
    ]
    if added:
        answer["punkte"] = (added + list(answer.get("punkte") or []))[:max_points]
    return added


def _norm_title(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("-", " ")).strip().lower()


def drop_existing_cards(
    points: list[str], tabs: dict[str, list[str]], by_name: bool = True
) -> tuple[list[str], list[str]]:
    """Remove card proposals whose name is a card that already exists.

    Live 13.11.2026: two of four proposals ("Saisonale Schwellwerte",
    "Aufzeichnungs-Lücken") already existed although the prompt forbade it.
    The proposal name is the text before the first "(" or ":"; it matches if
    it equals an existing title or ends with it ("Aufzeichnungs-Lücken" ends
    with "Lücken").
    """
    existing = [c for cards in tabs.values() for c in cards]
    titles = {_norm_title(c) for c in existing if len(c) <= 40}
    topics = [g for c in existing for g in CARD_TOPICS.get(c, [])]
    keep: list[str] = []
    dropped: list[str] = []
    for point in points:
        # Proposals usually read "Tab X: 'Name'. Frage: ..."; take the quoted
        # name if there is one, else the text before the first "(" or ":".
        quoted = re.search(
            r"['\u2018\u201a\u201c\u201e\"]([^'\u2019\u201c\u201d\"]{3,60})['\u2019\u201c\u201d\"]",
            point,
        )
        raw = quoted.group(1) if quoted else re.split(r"\s*[(:]", point, maxsplit=1)[0]
        name = _norm_title(raw)
        hit = by_name and any(
            name == t
            or name.endswith(" " + t)
            or (len(t) >= 8 and name.startswith(t + " "))
            for t in titles
        )
        low = point.lower()
        hit = hit or any(all(w in low for w in g) for g in topics)
        (dropped if hit else keep).append(point)
    return keep, dropped


_NUM_RE = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")


def _numbers(text: str) -> list[float]:
    return [float(m.replace(".", "").replace(",", ".")) for m in _NUM_RE.findall(text)]


def unverified_numbers(answer: dict[str, Any], context: str) -> list[str]:
    """Numbers in the answer that appear nowhere in the context (rounding allowed).

    A cheap hallucination check: every number the hamster may use is in the
    fixed context, so a number that is not there was invented or derived by
    the model and must be checked by a human. Integers up to 3 are ignored
    (counting words like "2 Punkte"). From 100 on, values within 1 % of a
    context number count as rounded (eval 13.11.2026: 579 W measured base
    load proposed as "580 W" is a rounding, not an invention).
    """
    known = set(_numbers(context))
    known_rounded = (
        {round(k) for k in known}
        | {round(k, 1) for k in known}
        | {round(k, 2) for k in known}
    )
    big = [k for k in known if k >= 100]
    text = " ".join([answer.get("headline") or "", answer.get("text") or ""])
    text += " " + " ".join(answer.get("punkte") or [])
    # Dates (02.07.2026, 13.11.) are not quantities; "07.202" was flagged.
    text = re.sub(r"\b\d{1,2}\.\d{1,2}\.(\d{2,4})?", " ", text)
    found = [
        (raw, float(raw.replace(".", "").replace(",", ".")))
        for raw in _NUM_RE.findall(text)
    ]

    def in_context(value: float) -> bool:
        if value <= 3 and value == int(value):
            return True
        if value in known or value in known_rounded:
            return True
        return value >= 100 and any(abs(value - k) <= 0.01 * k for k in big)

    # Sum or difference of two context numbers that the answer itself names
    # is checked arithmetic, not an invention (eval 13.11.2026: "Defizit
    # 6,4 kWh" next to 17,2 and 10,8). Products and ratios stay flagged on
    # purpose: "212 Sats/kWh x 0,6 kWh = 127 Sats" mixed a 14-day mean
    # with "gestern" and has to be read by a human.
    named = [v for _, v in found if in_context(v)]
    derived = {round(a + b, 1) for a in named for b in named} | {
        round(abs(a - b), 1) for a in named for b in named if a != b
    }
    out = []
    for raw, value in found:
        if in_context(value) or round(value, 1) in derived:
            continue
        if raw not in out:
            out.append(raw)
    return out


SATS_PER_BTC = 100_000_000
# Below this pool hashrate the two Avalon miners (tens of TH/s each) were off.
SMALL_MINER_MAX_THS = 5.0


def yesterday_lines(conn: sqlite3.Connection, now: datetime) -> list[str]:
    """Finished values of yesterday (UTC day, as stored), incl. pool revenue.

    Eval 13.11.2026: asked "Wie viele Sats gestern?", the model multiplied a
    14-day mean (Sats/kWh) by a 14-day mean (kWh/day) and called it
    yesterday. With the real numbers in the context there is nothing left
    to extrapolate.
    """
    day = (now.astimezone(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    label = f"{day[8:10]}.{day[5:7]}."
    try:
        kpi = conn.execute(
            "SELECT pv_kwh, house_kwh, mining_kwh, grid_import_kwh, coverage_pct"
            " FROM daily_kpi WHERE day = ?",
            (day,),
        ).fetchone()
    except sqlite3.OperationalError:
        kpi = None
    try:
        pool = conn.execute(
            "SELECT earned_btc FROM bitcoin_daily_settlement WHERE day = ?", (day,)
        ).fetchone()
    except sqlite3.OperationalError:
        pool = None
    try:
        ths = conn.execute(
            "SELECT pool_ths_avg FROM bitcoin_daily_settlement WHERE day = ?", (day,)
        ).fetchone()
    except sqlite3.OperationalError:
        ths = None
    lines = [
        f"GESTERN ({label}, fertige Tageswerte, genau so übernehmen). Live-Werte"
        " (Akkustand, Modus) gelten für JETZT, nicht für gestern; nicht mischen."
    ]
    if kpi:
        lines.append(
            f"- Sonne {de_num(kpi[0])} kWh, Haus {de_num(kpi[1])} kWh, Minen"
            f" {de_num(kpi[2], 2)} kWh, Netzbezug {de_num(kpi[3])} kWh"
            f" (Abdeckung {de_num(kpi[4], 0)} %)."
        )
    else:
        lines.append("- Für gestern gibt es noch keine Energie-Tageswerte.")
    if pool and pool[0] is not None:
        lines.append(
            f"- Poolertrag laut F2Pool-Abrechnung: {de_num(pool[0] * SATS_PER_BTC, 0)}"
            " Sats. Er entsteht aus der Rechenleistung der eigenen Geräte; der Pool"
            " rechnet sie nur ab."
        )
        # Eval 13.11.2026: "56 Sats aus 0,06 kWh im Eco-Modus". With the
        # Avalons off the pool still saw ~1.4 TH/s, the size of the Bitaxe on
        # the plug "FritzBox, Modem, Bitaxe". Name it so nothing is invented.
        if ths and ths[0] is not None:
            line = f"- Pool-Hashrate gestern im Mittel {de_num(ths[0])} TH/s."
            if ths[0] < SMALL_MINER_MAX_THS:
                line += (
                    " Das ist zu wenig für die Avalon-Miner (die standen); es passt"
                    " zum kleinen Bitaxe an der Steckdose 'FritzBox, Modem, Bitaxe'."
                    " Der Ertrag kam also sehr wahrscheinlich vom Bitaxe, nicht von"
                    " Miner 1 oder 2."
                )
            lines.append(line)
    else:
        lines.append(
            "- Für gestern liegt noch keine Pool-Abrechnung vor. Rechne KEINEN"
            " Ertrag hoch, sag, dass der Wert noch fehlt."
        )
    return lines


def prepare_ask(
    task: str,
    *,
    states: dict[str, dict[str, Any]],
    db: str | Path,
    now: datetime,
    dashboard: str | Path | None = None,
    recording_status: str | Path | None = None,
    tab: str | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    """Build the full user prompt for one task (shared by run_ask and the eval)."""
    live = live_facts(states)
    season: list[str] | None = None
    findings_season: list[str] = []
    inv: dict[str, Any] | None = None
    conn = open_readonly(db)
    # None = system zone with daylight saving per date (bithamster_research).
    local = None
    decisions: list[str] | None = None
    unmeasured: list[str] = []
    try:
        unmeasured = br.unmeasured_lines(conn)
        window = None
        if task == "frage":
            window = br.question_window(question, now, local)
        elif task in DECISION_TASKS:
            end = now.astimezone(timezone.utc)
            hours = DECISION_TASKS[task]
            window = (end - timedelta(hours=hours), end, f"letzte {hours} Stunden")
        if window:
            decisions = br.decision_lines(conn, window, local)
        research = research_facts(conn, now)
        research["winter"] = winter_lines(conn, now)
        yesterday = yesterday_lines(conn, now)
        season_tab = task in TAB_TASKS and tab in ("Einstellungen", "Steuerung")
        if task in ("optimierung", "frage") + OVERVIEW_TASKS or season_tab:
            season, findings_season = season_context(conn, states, now)
        if task in OVERVIEW_TASKS + ("tabcheck",):
            inv = data_inventory(conn, now)
    finally:
        conn.close()
    # Read for every task: the prompt lists them only for tab/overview tasks,
    # but fix_card_tabs needs them to correct "Tab X, Karte Y" in any answer.
    tabs = dashboard_tabs(dashboard) if dashboard else {}
    tab_values = (
        tab_value_lines(dashboard, tab, states)
        + research_card_lines(
            Path(dashboard).parent / "www" / "research_cards.json", tab
        )
        if task == "tabcheck" and dashboard and tab
        else None
    )
    recording = _read_json(recording_status)
    cards = (
        _read_json(Path(dashboard).parent / "www" / "research_cards.json")
        if dashboard
        else None
    )
    research_lines: list[str] | None
    if task in THESIS_TASKS:
        # Only the thesis context: live values and seasonal tables would
        # pull the answer back to the plant.
        research_lines = br.thesis_lines(
            cards,
            (
                _read_json(Path(dashboard).parent / "www" / "thesis_open.json")
                if dashboard
                else None
            ),
            now,
        ) or ["MASTERARBEIT: keine Daten lesbar (thesis_open.json fehlt)."]
    else:
        research_lines = (
            br.research_findings_lines(cards) + unmeasured
            if task not in ("tab", "aufzeichnung")
            else None
        )
    if task == "gesamtcheck":
        findings = priority_findings(findings_season, inv, research, recording)
    elif task == "optimierung":
        # Eval 13.11.2026: 2 of 3 answers called the automation "korrekt"
        # although the seasonal check said the reserve was too low. The
        # reserve is the main lever, so its finding is mandatory here too.
        # Findings already acted on ("BEREITS KORRIGIERT") belong to the full
        # review, not to "what to do next" (they pushed the winter heating-rod
        # finding down, 13.11.2026).
        open_season = [f for f in findings_season if "BEREITS KORRIGIERT" not in f]
        findings = priority_findings(open_season, None, {}, None)
    else:
        findings = []
    prompt = build_ask_prompt(
        task,
        live=live,
        research=research,
        now=now.astimezone(),
        states=states,
        recording=recording,
        tabs=tabs,
        tab=tab,
        question=question,
        season=season,
        inventory=inventory_lines(inv) if inv else None,
        findings=[f["text"] for f in findings],
        yesterday=yesterday,
        tab_values=tab_values,
        research_lines=research_lines,
        decisions=decisions,
    )
    return {
        "prompt": prompt,
        "tabs": tabs,
        "findings": findings,
        "inventory": inv,
        "tab": tab,
    }


_TAB_CARD_RE = re.compile(r"Tab ([A-ZÄÖÜ][\wäöüß]+), Karte ")


def fix_card_tabs(answer: dict[str, Any], tabs: dict[str, list[str]]) -> list[str]:
    """Correct "Tab X, Karte Y" where card Y lives in another tab. Returns fixes.

    Live 13.11.2026: "(Tab Energie, Karte Tagesbilanz)"; the card is in the
    Übersicht. The card title is matched as the longest known title that the
    text after "Karte " starts with; unknown or ambiguous titles stay as they
    are (only certain corrections).
    """
    where: dict[str, set[str]] = {}
    for tab, cards in tabs.items():
        for card in cards:
            if len(card) <= 40:
                where.setdefault(card, set()).add(tab)
    titles = sorted(where, key=len, reverse=True)
    fixes: list[str] = []

    def fix(text: str) -> str:
        out, pos = [], 0
        for m in _TAB_CARD_RE.finditer(text):
            rest = text[m.end() :]
            card = next((t for t in titles if rest.startswith(t)), None)
            tab = m.group(1)
            homes = where.get(card or "", set())
            if card and tab not in homes and len(homes) == 1:
                home = next(iter(homes))
                out.append(text[pos : m.start()] + f"Tab {home}, Karte ")
                fixes.append(f"{card}: Tab {tab} -> {home}")
            else:
                out.append(text[pos : m.end()])
            pos = m.end()
        return "".join(out) + text[pos:]

    answer["text"] = fix(str(answer.get("text") or ""))
    answer["punkte"] = [fix(str(p)) for p in answer.get("punkte") or []]
    return fixes


_SHOWN_CLAIM_RE = re.compile(
    r"\b(zeigt nur|nur (?:ein|eine|einen|die|den|das)\b|fehlt|fehlen|keine?n?|ohne)\b",
    re.I,
)
_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]{4,}")


def _contradicts_card(sentence: str) -> bool:
    """True if the sentence says a card lacks what CARD_SHOWS says it shows."""
    low = sentence.lower()
    m = _SHOWN_CLAIM_RE.search(sentence)
    if not m:
        return False
    for title, shows in CARD_SHOWS.items():
        if title.lower() not in low:
            continue
        if m.group(1).lower() == "zeigt nur":
            return True
        claim = {w.lower() for w in _WORD_RE.findall(sentence[m.end() :])}
        shown = {w.lower() for w in _WORD_RE.findall(shows)}
        if claim & shown:
            return True
    return False


def drop_shown_claims(answer: dict[str, Any]) -> list[str]:
    """Remove claims that a card lacks something it displays (tabcheck).

    Live 13.11.2026, twice in a row and despite the card description in the
    prompt: "Hardware-Abzahlung zeigt nur 400 Euro" (it shows percent, bar,
    Sats and the open rest). Points go entirely, sentences of the text too.
    """
    dropped: list[str] = []
    keep: list[str] = []
    for point in list(answer.get("punkte") or []):
        (dropped if _contradicts_card(point) else keep).append(point)
    answer["punkte"] = keep
    text = str(answer.get("text") or "")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = [x for x in sentences if not _contradicts_card(x)]
    dropped += [x for x in sentences if _contradicts_card(x)]
    answer["text"] = " ".join(kept)
    return dropped


def finish_answer(
    task: str, answer: dict[str, Any], prepared: dict[str, Any]
) -> dict[str, Any]:
    """Deterministic post-checks; returns what was changed, for card and log."""
    max_points = TASK_MAX_POINTS.get(task, MAX_POINTS)
    dropped: list[str] = []
    no_data: list[str] = []
    if task == "karten":
        answer["punkte"], dropped = drop_existing_cards(
            list(answer.get("punkte") or []), prepared["tabs"]
        )
    if task == "tabcheck":
        # Improvements to this tab name its own cards; only cards of the
        # other tabs count as duplicates here.
        others = {k: v for k, v in prepared["tabs"].items() if k != prepared.get("tab")}
        answer["punkte"], dropped = drop_existing_cards(
            list(answer.get("punkte") or []), others, by_name=False
        )
        dropped += drop_shown_claims(answer)
    if task == "karten" and dropped and not answer["punkte"]:
        # Eval 13.11.2026: every proposal already existed, the text still
        # said "Akku über Nacht und Prognose fehlen".
        answer["headline"] = "Keine neue Karte gefunden"
        answer["text"] = (
            "Alle meine Vorschläge gibt es schon im Dashboard. Mit den gefüllten"
            " Daten fällt mir gerade keine fehlende Karte ein."
        )
    if task in ("karten", "tabcheck"):
        answer["punkte"], no_data = drop_unsupported_cards(
            answer["punkte"], prepared.get("inventory")
        )
    reviewed: list[str] = []
    if task in PROPOSAL_TASKS:
        answer["punkte"], reviewed = br.drop_reviewed(list(answer.get("punkte") or []))
    model_covered = [finding_mentioned(f, answer) for f in prepared["findings"]]
    added = ensure_findings(answer, prepared["findings"], max_points)
    return {
        "dropped_existing": dropped,
        "dropped_no_data": no_data,
        "dropped_reviewed": reviewed,
        "added_findings": added,
        "findings_total": len(prepared["findings"]),
        "findings_by_model": sum(model_covered),
        "fixed_card_tabs": fix_card_tabs(answer, prepared["tabs"]),
        "unverified_numbers": unverified_numbers(answer, prepared["prompt"]),
    }


def build_ask_prompt(
    task: str,
    *,
    live: dict[str, Any],
    research: dict[str, Any],
    now: datetime,
    states: dict[str, dict[str, Any]],
    recording: dict[str, Any] | None,
    tabs: dict[str, list[str]],
    tab: str | None,
    question: str | None,
    season: list[str] | None = None,
    inventory: list[str] | None = None,
    findings: list[str] | None = None,
    yesterday: list[str] | None = None,
    tab_values: list[str] | None = None,
    research_lines: list[str] | None = None,
    decisions: list[str] | None = None,
) -> str:
    """User message for one request: instruction, answer format, fixed context."""
    label, instruction = TASKS[task]
    points = TASK_MAX_POINTS.get(task, MAX_POINTS)
    words = 40 if task in OVERVIEW_TASKS + ("tabcheck",) else 30
    parts = [
        f"AUFTRAG: {label}. {instruction}",
        "",
        "Für diesen Auftrag gilt NICHT das Format lage/optimierungen, sondern genau"
        " dieses JSON-Objekt, nichts sonst:",
        '{"headline": "max. 8 Wörter", "text": "2 bis 4 Sätze, max. 80 Wörter",'
        f' "punkte": ["0 bis {points} kurze Punkte, je max. {words} Wörter"]}}',
        "",
    ]
    if task in THESIS_TASKS:
        parts.append(f"HEUTE: {now:%d.%m.%Y}")
    else:
        parts.append(build_context(live, research, now))
    if yesterday and task not in THESIS_TASKS:
        parts += [""] + yesterday
    if season:
        parts += [""] + season
    if task in ("aufzeichnung", "fehler") + OVERVIEW_TASKS:
        parts += ["", "AUFZEICHNUNGSSTATUS"] + recording_lines(recording)
    if task in ("fehler",) + OVERVIEW_TASKS:
        parts += ["", "VERFÜGBARKEIT"] + error_lines(states, live)
    if findings:
        parts += [
            "",
            "WICHTIGSTE BEFUNDE (fest berechnet). Deine ersten Punkte MÜSSEN genau"
            " diese Befunde sein, in dieser Reihenfolge und mit ihren Zahlen."
            " Danach darfst du eigene ergänzen:",
        ] + [f"{i}. {f}" for i, f in enumerate(findings, 1)]
    if research_lines:
        parts += [""] + research_lines
    if decisions:
        parts += [""] + decisions
    if task in PROPOSAL_TASKS:
        parts += [""] + br.reviewed_lines()
    if task in OVERVIEW_TASKS:
        parts += [
            "",
            (
                "SCHON VORHANDENE KARTEN (diese NICHT noch einmal vorschlagen)"
                if task == "karten"
                else "ALLE TABS UND IHRE KARTEN (nur diese gibt es)"
            ),
        ]
        parts += [
            f"- {name}: " + ("; ".join(cards) if cards else "keine bekannt")
            for name, cards in tabs.items()
        ]
        parts += [""] + (inventory or ["DATENBESTAND: nicht lesbar."])
    if task == "tab":
        cards = tabs.get(tab or "", [])
        parts += [
            "",
            f"TAB: {tab or 'unbekannt'}",
            "Karten in diesem Tab: "
            + ("; ".join(cards) if cards else "keine bekannt")
            + ".",
        ]
    if task == "tabcheck":
        name = tab or "unbekannt"
        parts += [
            "",
            f"TAB: {name}",
            "Karten in diesem Tab: "
            + ("; ".join(tabs.get(name, [])) or "keine bekannt")
            + ".",
            "",
            "SENSORWERTE hinter den Karten dieses Tabs (live, ROH, NICHT so formatiert wie auf der Karte)",
        ]
        parts += tab_values or ["- keine Werte lesbar"]
        parts += ["", "KARTEN IN DEN ANDEREN TABS (nicht doppelt vorschlagen)"]
        parts += [
            f"- {other}: " + ("; ".join(cards) if cards else "keine bekannt")
            for other, cards in tabs.items()
            if other != name
        ]
        parts += [""] + (inventory or ["DATENBESTAND: nicht lesbar."])
    if task == "frage":
        parts += ["", f"FRAGE DES NUTZERS: {question or '(leer)'}"]
    return "\n".join(parts)


def parse_ask_answer(raw: str, max_points: int = MAX_POINTS) -> dict[str, Any]:
    """Validate {"headline","text","punkte"}. Raises ValueError if unusable."""
    text = re.sub(r"<think>.*?</think>", "", raw.strip(), flags=re.S)
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model output")
    obj = json.loads(text[start : end + 1])
    if not isinstance(obj, dict):
        raise ValueError("model output is not an object")
    headline = _clip(obj.get("headline"), ASK_LIMITS["headline"])
    body = _clip(obj.get("text"), ASK_LIMITS["text"])
    if not headline or not body:
        raise ValueError("headline/text missing")
    raw_points = obj.get("punkte")
    points = [
        _clip(p, ASK_LIMITS["punkt"])
        for p in (raw_points if isinstance(raw_points, list) else [])
        if isinstance(p, str) and p.strip()
    ][:max_points]
    return {"headline": headline, "text": body, "punkte": points}


def _read_json(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def run_ask(
    *,
    db: str | Path,
    out: str | Path,
    soul: str | Path,
    ha_url: str,
    ha_token: str,
    llm_url: str,
    model: str,
    dashboard: str | Path | None = None,
    recording_status: str | Path | None = None,
    log_db: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """Answer the pending dashboard request. None if there is nothing new."""
    request = read_ha_state(ha_url, ha_token, REQUEST_ENTITY)
    request_id = str((request or {}).get("state") or "")
    task = parse_request(request_id)
    previous = _read_json(out) or {}
    if task is None or previous.get("request_id") == request_id:
        return None

    now = now or datetime.now(timezone.utc)
    result: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "request_id": request_id,
        "task": task,
        "label": TASKS[task][0],
        "tab": None,
        "question": None,
        "generated_at": now.isoformat(),
        "model": model,
        "ok": False,
        "error": None,
        "answer": None,
        "checks": None,
    }
    prompt: str | None = None
    try:
        states = read_ha_states(ha_url, ha_token)
        tab = (states.get(TAB_ENTITY) or {}).get("state")
        question = (states.get(QUESTION_ENTITY) or {}).get("state")
        if question in ("unknown", "unavailable", ""):
            question = None
        result["tab"] = tab if task in TAB_TASKS else None
        result["question"] = question if task == "frage" else None
        prepared = prepare_ask(
            task,
            states=states,
            db=db,
            now=now,
            dashboard=dashboard,
            recording_status=recording_status,
            tab=tab,
            question=question,
        )
        prompt = prepared["prompt"]
        system = Path(soul).read_text(encoding="utf-8")
        t0 = time.monotonic()
        answer = parse_ask_answer(
            call_llm(llm_url, model, system, prompt),
            TASK_MAX_POINTS.get(task, MAX_POINTS),
        )
        result["duration_s"] = round(time.monotonic() - t0, 1)
        result["checks"] = finish_answer(task, answer, prepared)
        result["answer"] = answer
        result["ok"] = True
    except Exception as exc:  # the card must show the failure, not hang
        log.exception("bithamster ask failed")
        result["error"] = f"{type(exc).__name__}: {exc}"[:300]
    result["history"] = append_history(previous, result)
    write_atomic(result, out)
    if log_db:
        log_entry(log_db, "ask", result, prompt=prompt)
    return result


ASK_HISTORY_MAX = 30
_HISTORY_FIELDS = (
    "request_id",
    "task",
    "label",
    "tab",
    "question",
    "generated_at",
    "ok",
    "error",
    "answer",
    "checks",
)


def append_history(
    previous: dict[str, Any], result: dict[str, Any]
) -> list[dict[str, Any]]:
    """Newest-first list of past answers for the "Verlauf" in the card.

    Stored in the same JSON as the current answer, capped at ASK_HISTORY_MAX.
    A previous file without history (before 13.11.2026) still contributes
    its single answer so nothing already shown disappears.
    """
    raw = previous.get("history")
    old = [h for h in raw if isinstance(h, dict)] if isinstance(raw, list) else []
    if not old and previous.get("request_id"):
        old = [{k: previous.get(k) for k in _HISTORY_FIELDS}]
    entry = {k: result.get(k) for k in _HISTORY_FIELDS}
    return ([entry] + old)[:ASK_HISTORY_MAX]


WATCH_POLL_S = 3.0
WATCH_ERROR_BACKOFF_S = 30.0


def watch(
    *,
    poll_s: float = WATCH_POLL_S,
    max_rounds: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    **ask_kwargs: Any,
) -> int:
    """Answer dashboard requests as they come in (systemd service on the HA host).

    Replaces the once-a-minute cron for requests (13.11.2026, user wish
    "nicht so lange warten"): the wait was dominated by the poll interval
    (0..60 s), not by the model (about 7 s). Each round is the same single GET
    on the request entity as before; the model only runs on a new request.
    Errors (HA restarting, GX10 busy) are logged and retried after a back-off,
    so the service never dies on a transient failure. Returns the number of
    answered requests (for tests).
    """
    answered = 0
    rounds = 0
    while max_rounds is None or rounds < max_rounds:
        rounds += 1
        try:
            result = run_ask(**ask_kwargs)
        except Exception:  # keep the service alive, retry later
            log.exception("bithamster watch: round failed, retrying")
            sleep(WATCH_ERROR_BACKOFF_S)
            continue
        if result is not None:
            answered += 1
            log.info(
                "bithamster ask task=%s ok=%s error=%s",
                result["task"],
                result["ok"],
                result["error"],
            )
        sleep(poll_s)
    return answered


def _load_env_file(path: str = ".env") -> None:
    """Same minimal loader as the other cron modules (no python-dotenv)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(
                key.strip(), value.split(" #")[0].strip().strip('"').strip("'")
            )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="BitHamster KI: read-only dashboard explainer"
    )
    p.add_argument("--db", required=True, help="research database (opened read-only)")
    p.add_argument("--out", required=True, help="output JSON (HA www folder)")
    p.add_argument("--soul", required=True, help="persona file (bithamster_SOUL.md)")
    p.add_argument(
        "--llm-url",
        default=None,
        help="OpenAI-compatible base URL (env BITHAMSTER_LLM_URL)",
    )
    p.add_argument(
        "--model",
        default=None,
        help=f"model name (env BITHAMSTER_MODEL, default {DEFAULT_MODEL})",
    )
    p.add_argument(
        "--ha-url",
        default=None,
        help="HA base URL (default http://UMBREL_HOST:HA_PORT)",
    )
    p.add_argument(
        "--ask",
        action="store_true",
        help="answer a pending dashboard request (input_text.bithamster_auftrag)",
    )
    p.add_argument("--dashboard", default=None, help="dashboard YAML (task 'tab')")
    p.add_argument(
        "--recording-status", default=None, help="recording_status.json (tasks)"
    )
    p.add_argument(
        "--watch",
        action="store_true",
        help="keep running and answer requests within seconds (implies --ask)",
    )
    p.add_argument(
        "--poll", type=float, default=WATCH_POLL_S, help="watch poll interval (s)"
    )
    p.add_argument(
        "--log-db",
        default=None,
        help="own SQLite file for the answer log (never the research DB)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    _load_env_file()
    args = _parse_args(argv)
    host = os.getenv("UMBREL_HOST", "")
    ha_url = args.ha_url or (
        f"http://{host}:{os.getenv('HA_PORT', '8123')}" if host else ""
    )
    token = os.getenv("HA_TOKEN", "")
    llm_url = args.llm_url or os.getenv("BITHAMSTER_LLM_URL", "")
    model = args.model or os.getenv("BITHAMSTER_MODEL", DEFAULT_MODEL)
    missing = [
        n
        for n, v in (
            ("UMBREL_HOST/--ha-url", ha_url),
            ("HA_TOKEN", token),
            ("BITHAMSTER_LLM_URL", llm_url),
        )
        if not v
    ]
    if missing:
        log.error("missing configuration: %s", ", ".join(missing))
        return 2
    if args.watch:
        log.info("bithamster watch: polling every %.1f s", args.poll)
        watch(
            poll_s=args.poll,
            db=args.db,
            out=args.out,
            soul=args.soul,
            ha_url=ha_url,
            ha_token=token,
            llm_url=llm_url,
            model=model,
            dashboard=args.dashboard,
            recording_status=args.recording_status,
            log_db=args.log_db,
        )
        return 0
    if args.ask:
        asked = run_ask(
            db=args.db,
            out=args.out,
            soul=args.soul,
            ha_url=ha_url,
            ha_token=token,
            llm_url=llm_url,
            model=model,
            dashboard=args.dashboard,
            recording_status=args.recording_status,
            log_db=args.log_db,
        )
        if asked is None:
            return 0
        log.info(
            "bithamster ask task=%s ok=%s error=%s",
            asked["task"],
            asked["ok"],
            asked["error"],
        )
        return 0 if asked["ok"] else 1
    result = run(
        db=args.db,
        out=args.out,
        soul=args.soul,
        ha_url=ha_url,
        ha_token=token,
        llm_url=llm_url,
        model=model,
        log_db=args.log_db,
    )
    log.info(
        "bithamster ok=%s optimierungen=%d error=%s",
        result["ok"],
        len(result["optimierungen"]),
        result["error"],
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
