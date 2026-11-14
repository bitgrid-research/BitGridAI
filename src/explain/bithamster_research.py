"""Research context for the BitHamster "Bitsy" (read-only, deterministic).

Three things the hamster lacked on 14.11.2026, each found in a live run:

1. The findings of every research card, for every task. Before, only the
   tab check of "Forschung" saw a few headline numbers; the model then called
   the forecast "useless" (it only saw 14 winter days) and claimed the heating
   rod "prevents" a full battery (0.8 kWh a day against a 12.5 kWh battery).
   ``research_findings_lines`` gives the numbers with their size and limits.
2. The decision log. A question that names a day ("Warum hat Miner 1 am 05.09.
   abgeschaltet?") gets the logged mode changes, the reason the watchdog wrote,
   the thresholds valid then and whether the day was measured
   (``decision_lines``). The hamster explains from the log, not from guesses.
3. A memory of proposals that were checked and rejected, with the reason
   (``REVIEWED``). The model sees the list; ``drop_reviewed`` removes repeats.

Nothing here writes anywhere or influences a control decision.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime, timedelta, timezone, tzinfo
from typing import Any


def de(value: Any, digits: int = 0) -> str:
    """German number format; '—' for a missing value."""
    if value is None:
        return "—"
    text = f"{float(value):,.{digits}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


MONTHS = (
    "",
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)


def _month(ym: str) -> str:
    try:
        return MONTHS[int(ym[5:7])]
    except (ValueError, IndexError):
        return ym


# ---------------------------------------------------------------------------
# 1. Findings of the research cards
# ---------------------------------------------------------------------------

BATTERY_KWH = 12.5


def research_findings_lines(cards: dict[str, Any] | None) -> list[str]:
    """Findings of all research cards (research_cards.json) as context lines."""
    if not cards:
        return []
    lines = [
        "FORSCHUNGSBEFUNDE (fest berechnet aus der Forschungs-DB, dieselben Zahlen"
        " wie die Karten im Tab Forschung; Tage, die nicht gemessen wurden, sind"
        " schon herausgerechnet)"
    ]
    auto = cards.get("automation") or {}
    su = auto.get("surplus") or {}
    if su.get("hours"):
        totals: dict[str, float] = {}
        for m in su.get("months") or []:
            for label, h in (m.get("reasons") or {}).items():
                totals[label] = totals.get(label, 0.0) + float(h)
        top = sorted(totals.items(), key=lambda x: -x[1])[:3]
        lines.append(
            f"- Ungenutzter Solarüberschuss: {de(su['hours'], 1)} h mit über 1 kW"
            f" Einspeisung bei stehenden Minern, {de(su.get('export_kwh'), 1)} kWh"
            " seit Aufzeichnungsbeginn. Gründe laut Diagnose: "
            + ", ".join(f"{k} {de(v, 1)} h" for k, v in top)
            + ". „Akku unter Stopp-Schwelle“ ist gewollt (Akku vor Mining)."
        )
    sw = auto.get("switching") or {}
    months = [m for m in sw.get("months") or [] if m.get("mining_days")]
    if months:
        days = sum(m["mining_days"] for m in months)
        over = sum(m["days_over"] for m in months)
        drops = sum(m.get("dropouts", 0) for m in months)
        lines.append(
            f"- Schaltwechsel: an {over} von {days} Mining-Tagen mehr als"
            f" {sw.get('target', 2)} Start/Stopp-Wechsel (Ziel verfehlt an"
            f" {de(100 * over / days)} % der Tage). {drops} kurze Abbrüche"
            f" (Aus unter {sw.get('dropout_max_min', 15)} min) sind KEINE"
            " Schaltwechsel der Automatik und schon herausgerechnet."
        )
    changes = sw.get("threshold_changes") or []
    if changes:
        c = changes[0]
        lines.append(
            f"- Letzte Schwellen-Änderung: {c['label']} {de(float(c['old']))} →"
            f" {de(float(c['new']))} % ({c['timestamp'][:16].replace('T', ' ')} UTC)."
        )
    sf = auto.get("safety") or {}
    if sf:
        lines.append(
            f"- Übertemperatur: {sf.get('hot_blocks_total', 0)} Blöcke ab"
            f" {sf.get('tmax_limit_c', 110)} °C seit Aufzeichnungsbeginn; Schaltfehler"
            f" {sf.get('errors_total', 0)}, davon 92 am Serverumzug 12./13.08.2026"
            " (kein Fehler der Steuerung)."
        )
    fc = cards.get("forecast") or {}
    fm = [m for m in fc.get("months") or [] if m.get("days")]
    if fm:
        lines.append(
            "- Solarprognose je Monat (Prognose gegen Messung): "
            + ", ".join(
                f"{_month(m['month'])} {'+' if (m['bias_pct'] or 0) > 0 else ''}"
                f"{de(m['bias_pct'])} %"
                for m in fm
                if m.get("bias_pct") is not None
            )
            + ". Saisonmuster: im Sommer leicht zu niedrig, bei tiefer Wintersonne"
            " weit zu hoch (Modell ohne Verschattung). Kein Datenfehler; im Winter"
            " als Startsignal ungeeignet, als Veto (R4) brauchbar."
        )
    hz = cards.get("heizstab") or {}
    if hz.get("days"):
        per_day = float(hz.get("heizstab_kwh_not_full") or 0) / max(hz["days"], 1)
        lines.append(
            f"- Heizstab: {de(hz.get('heizstab_kwh_not_full'), 1)} kWh Solarstrom in"
            f" {hz['days']} Tagen, während der Akku nicht voll war, im Mittel"
            f" {de(per_day, 1)} kWh am Tag (Akku {de(BATTERY_KWH, 1)} kWh). Das"
            " regelt das Gerät selbst; es erklärt NICHT allein, warum der Akku im"
            " Winter nicht voll wird (dafür fehlt die Sonne)."
        )
    return lines if len(lines) > 1 else []


def unmeasured_lines(conn: sqlite3.Connection) -> list[str]:
    """Days with at least one hour of blocks that were stored but not measured."""
    try:
        rows = conn.execute(
            "SELECT substr(block_id, 1, 10), COUNT(*) FROM energy_states"
            " WHERE quality <> 'ok' GROUP BY 1 HAVING COUNT(*) >= 6 ORDER BY 1"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    if not rows:
        return []
    hours = sum(int(n) for _, n in rows) / 6
    return [
        f"- Nicht gemessene Tage: {len(rows)} Tage mit zusammen {de(hours)} h, in"
        " denen Home Assistant keine Werte lieferte (quality=warn); ihre"
        " Tageswerte sind falsch: " + ", ".join(str(d)[5:] for d, _ in rows[:14]) + "."
    ]


# ---------------------------------------------------------------------------
# 2. Decision log for "why" questions
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})?")
_TIME_RE = re.compile(
    r"\b(\d{1,2})(?:[:.](\d{2}))?\s*uhr\b|\bum\s+(\d{1,2})[:.](\d{2})\b"
)
_WHY_RE = re.compile(r"\b(warum|wieso|weshalb|weswegen|wann)\b", re.I)
DECISION_MAX_LINES = 30
REST_MODES = frozenset({"Standby", "Off", "Idle"})
WINDOW_AROUND_TIME = timedelta(hours=2)
MINERS = {"miner1": "Miner 1", "miner2": "Miner 2"}
SEASON_ENTITY = "sensor.mvp_saison_status"
SEASON_LABELS = {
    "hausreserve_pct": "Stopp (Hausreserve)",
    "eco_ab_pct": "Eco ab",
    "standard_ab_pct": "Standard ab",
    "super_ab_pct": "Super ab",
}


def _to_local(t: datetime, local: tzinfo | None) -> datetime:
    """Local time of ``t``. Without ``local`` the system zone WITH daylight
    saving per date: a fixed offset taken from today (CET in November) put
    a stop on 05.09. at 18:29 instead of 19:29 CEST (live 14.11.2026)."""
    return t.astimezone(local) if local else t.astimezone()


def _from_local(naive: datetime, local: tzinfo | None) -> datetime:
    """Aware datetime for a local wall-clock time (see _to_local)."""
    return naive.replace(tzinfo=local) if local else naive.astimezone()


def question_window(
    question: str | None, now: datetime, local: tzinfo | None = None
) -> tuple[datetime, datetime, str] | None:
    """UTC window a question asks about, with a label; None if it names none.

    A date ("05.09.", "5.9.2026") selects that local day, narrowed to ±2 h if
    a time is named ("um 14:17", "14 Uhr"). "heute"/"gestern" work alike. A
    plain "warum" without a day asks about the last 24 hours.
    """
    if not question:
        return None
    text = question.lower()
    today = _to_local(now, local).date()
    day: date | None = None
    m = _DATE_RE.search(text)
    if m:
        d, mo = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        try:
            day = date(year, mo, d)
        except ValueError:
            day = None
        if day and not m.group(3) and day > today:
            day = date(year - 1, mo, d)
    elif "gestern" in text:
        day = today - timedelta(days=1)
    elif "heute" in text:
        day = today
    if day is None:
        if not _WHY_RE.search(text):
            return None
        end = now.astimezone(timezone.utc)
        return end - timedelta(hours=24), end, "letzte 24 Stunden"
    start_local = _from_local(datetime(day.year, day.month, day.day), local)
    t = _TIME_RE.search(text)
    if t:
        hh = int(t.group(1) or t.group(3))
        mm = int(t.group(2) or t.group(4) or 0)
        if 0 <= hh < 24 and 0 <= mm < 60:
            at = _from_local(datetime(day.year, day.month, day.day, hh, mm), local)
            return (
                (at - WINDOW_AROUND_TIME).astimezone(timezone.utc),
                (at + WINDOW_AROUND_TIME).astimezone(timezone.utc),
                f"{day:%d.%m.%Y} {hh:02d}:{mm:02d} ±2 h",
            )
    return (
        start_local.astimezone(timezone.utc),
        _from_local(
            datetime(day.year, day.month, day.day) + timedelta(days=1), local
        ).astimezone(timezone.utc),
        f"{day:%d.%m.%Y}",
    )


def _local(ts: str, local: tzinfo | None) -> str:
    try:
        t = datetime.fromisoformat(ts)
    except ValueError:
        return ts
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return _to_local(t, local).strftime("%d.%m. %H:%M")


def decision_lines(
    conn: sqlite3.Connection,
    window: tuple[datetime, datetime, str],
    local: tzinfo | None = None,
) -> list[str]:
    """Logged decisions, diagnosis, thresholds and data quality in the window."""
    start, end, label = window
    s_iso, e_iso = start.isoformat(), end.isoformat()
    lines = [
        f"ENTSCHEIDUNGSPROTOKOLL der Steuerung ({label}). Erkläre Entscheidungen"
        " NUR hieraus. „Regel“ und „Watchdog“ zeigen den Regelzustand, den die"
        " Automatik kurz vor dem Wechsel selbst geschrieben hat; welcher Zweig"
        " genau geschaltet hat, ist nicht protokolliert. Steht hier nichts, sag"
        " das, statt einen Grund zu erfinden."
    ]
    try:
        all_modes = conn.execute(
            "SELECT timestamp, miner, from_state, to_state, rule_active, reason"
            " FROM ha_decision_log WHERE kind = 'mode' AND timestamp >= ?"
            " AND timestamp < ? ORDER BY timestamp",
            (s_iso, e_iso),
        ).fetchall()
        # Standby/Off/Idle among each other are no decisions: live 14.11.2026
        # the model read a 0.2 s Standby -> Off -> Standby jump at 22:30 as
        # "switched to standby because the battery fell to 69 %".
        modes = [
            r for r in all_modes if not (r[2] in REST_MODES and r[3] in REST_MODES)
        ]
        rest_jumps = len(all_modes) - len(modes)
        rule_times = {
            (str(m), str(r)): str(ts)
            for ts, m, r in conn.execute(
                "SELECT timestamp, miner, to_state FROM ha_decision_log"
                " WHERE kind = 'rule' AND timestamp < ? ORDER BY timestamp",
                (e_iso,),
            ).fetchall()
        }
        diag = conn.execute(
            "SELECT timestamp, miner, code, summary FROM ha_diagnose_log"
            " WHERE timestamp >= ? AND timestamp < ? AND code <> 'ok'"
            " ORDER BY timestamp",
            (s_iso, e_iso),
        ).fetchall()
        season = conn.execute(
            "SELECT key, value FROM settings_history WHERE entity = ?"
            " AND timestamp <= ? ORDER BY timestamp",
            (SEASON_ENTITY, e_iso),
        ).fetchall()
        bad = conn.execute(
            "SELECT COUNT(*) FROM energy_states WHERE quality <> 'ok'"
            " AND block_id >= ? AND block_id < ?",
            (start.strftime("%Y-%m-%dT%H:%M:%S"), end.strftime("%Y-%m-%dT%H:%M:%S")),
        ).fetchone()
    except sqlite3.OperationalError:
        return lines + ["- Protokoll nicht lesbar (Tabellen fehlen)."]
    if not modes:
        lines.append("- Keine Moduswechsel in diesem Zeitraum.")
    if rest_jumps:
        lines.append(
            f"- {rest_jumps} Sprünge nur zwischen Standby, Off und Idle (Miner"
            " meldet kurz einen anderen Ruhezustand): KEINE Entscheidungen,"
            " nicht als Schalten erklären."
        )
    for ts, miner, frm, to, rule, reason in modes[:DECISION_MAX_LINES]:
        why = f"; Regel: {rule}" if rule else ""
        since = rule_times.get((str(miner), str(rule))) if rule else None
        if reason:
            written = f", geschrieben {_local(since, local)}" if since else ""
            why += f"; Watchdog{written}: „{reason}“"
        lines.append(
            f"- {_local(str(ts), local)} {MINERS.get(str(miner), miner)}:"
            f" {frm or '?'} → {to}{why}"
        )
    if len(modes) > DECISION_MAX_LINES:
        lines.append(f"- ... und {len(modes) - DECISION_MAX_LINES} weitere Wechsel.")
    for ts, miner, code, summary in diag[:8]:
        lines.append(
            f"- Diagnose {_local(str(ts), local)} {MINERS.get(str(miner), miner)}:"
            f" {code} ({summary or ''})"
        )
    valid = dict(season)
    if valid:
        lines.append(
            "- Damals geltende Saisonschwellen: "
            + ", ".join(
                f"{lbl} {de(float(valid[k]))} %"
                for k, lbl in SEASON_LABELS.items()
                if k in valid
            )
            + (f"; Saisonstatus {valid['state']}" if "state" in valid else "")
            + "."
        )
    else:
        lines.append(
            "- Damals geltende Schwellen: nicht protokolliert (erst seit 26.08.2026)."
        )
    if bad and bad[0]:
        lines.append(
            f"- ACHTUNG: {bad[0]} Zehn-Minuten-Blöcke in diesem Zeitraum wurden nicht"
            " gemessen (Home Assistant ohne Werte); Messwerte dort nicht verwenden."
        )
    return lines


# ---------------------------------------------------------------------------
# 3. Proposals that were checked and rejected
# ---------------------------------------------------------------------------

# (words that all appear in a repeat, short title, reason). Curated by hand
# after reviewing live answers; a new entry needs a date and a reason.
REVIEWED: list[tuple[tuple[str, ...], str, str]] = [
    (
        ("heizstab", "akku", "karte"),
        "Karte Heizstab gegen Akku",
        "14.11.2026: steht schon als Hinweis in Akku-Höchststand und Start.",
    ),
    (
        ("heizstab", "verhindert"),
        "Heizstab verhindert vollen Akku",
        "14.11.2026: rund 0,8 kWh am Tag gegen 12,5 kWh Akku; im Winter fehlt"
        " die Sonne, der Heizstab ist nicht die Ursache.",
    ),
    (
        ("halteband",),
        "Karte Halteband-Dauer",
        "14.11.2026: Akku-Höchststand und Start beantwortet „warum startet"
        " nichts“ direkter.",
    ),
    (
        ("off", "standby"),
        "Off statt Standby",
        "14.11.2026: beides sind Ruhezustände, zählt nicht als Fehler.",
    ),
    (
        ("prognose", "wertlos"),
        "Prognose wertlos",
        "14.11.2026: Saisonmuster, im Sommer brauchbar; Monatsvergleich auf der"
        " Karte.",
    ),
    (
        ("entl", "nacht", "karte"),
        "Karte Akku-Entleerung nachts",
        "14.11.2026: zeigt die Akku über Nacht schon.",
    ),
]


def reviewed_lines() -> list[str]:
    return ["SCHON GEPRÜFT UND VERWORFEN (nicht noch einmal vorschlagen):"] + [
        f"- {title}: {reason}" for _, title, reason in REVIEWED
    ]


def drop_reviewed(points: list[str]) -> tuple[list[str], list[str]]:
    """Remove points that repeat a reviewed and rejected proposal."""
    keep: list[str] = []
    dropped: list[str] = []
    for point in points:
        low = point.lower()
        hit = any(all(w in low for w in words) for words, _, _ in REVIEWED)
        (dropped if hit else keep).append(point)
    return keep, dropped


# ---------------------------------------------------------------------------
# 4. Master's thesis: plan, assign findings, risks (14.11.2026)
# ---------------------------------------------------------------------------
# Sources: the "thesis" notes in research_cards.json (production findings with
# limits) and thesis_open.json (open points, schedule and markers, copied by
# scripts/thesis_open_export.py from the thesis folder). No study data, no
# participant data, no thesis text: the hamster plans and warns, he does not
# write passages for the thesis (scientific integrity; every AI use is listed
# in appendix J anyway).
THESIS_ITEM_MAX = 220
THESIS_ITEMS_PER_SECTION = 6


def _sync_lines(sync: Any) -> list[str]:
    """Stand-Abgleich (src/data/thesis_sync.py) as facts for the thesis tasks.

    Deterministic findings only; the model ranks them, it does not search
    for drift itself (it estimates instead of counting).
    """
    if not isinstance(sync, dict):
        return []

    def where(e: dict[str, Any]) -> str:
        name = str(e.get("file", "")).split("/")[-1].replace(".tex", "")
        return f"{name}:{e.get('line')} ({e.get('section') or 'ohne Abschnitt'})"

    lines = [
        "STAND-ABGLEICH ARBEIT GEGEN SYSTEM (deterministisch geprüft, Fakten,"
        " nicht schätzen):"
    ]
    for r in sync.get("replaced") or []:
        lines.append(
            f"- VERALTET {where(r)}: zitiert ADR {int(r['adr']):03d}, ersetzt"
            f" durch ADR {int(r['by']):03d} ({r.get('by_title')})."
        )
    bf = sync.get("befunde") or {}
    for row in bf.get("notes") or []:
        for p in row.get("places") or []:
            if p.get("state") in ("geaendert", "neu_seit_stichtag"):
                lines.append(
                    f"- ZAHLEN GEÄNDERT: Befund {row['id']} in"
                    f" {str(p['file']).split('/')[-1]}:{p['line']} seit Stichtag"
                    f" {p.get('stichtag')}."
                )
    missing = bf.get("missing") or []
    if missing:
        lines.append(
            f"- Befunde der Merkliste noch nicht im Text: {', '.join(missing)}."
        )
    changed = sync.get("changed") or []
    if changed:
        lines.append(
            "- Zitierte Dateien seit dem Stand geändert (schwaches Signal): "
            + "; ".join(
                f"{c['path']} ({len(c.get('entries') or [])} Einträge)"
                for c in changed[:6]
            )
        )
    new_adrs = [u for u in sync.get("adr_uncited") or [] if u.get("date")]
    if new_adrs:
        lines.append(
            "- Neue ADR, nirgends zitiert: "
            + "; ".join(f"ADR {int(u['adr']):03d} {u.get('title')}" for u in new_adrs)
        )
    return lines if len(lines) > 1 else []


def thesis_lines(
    cards: dict[str, Any] | None, open_points: dict[str, Any] | None, now: datetime
) -> list[str]:
    """Context for the thesis tasks; empty if neither source is readable."""
    lines: list[str] = []
    if open_points:
        try:
            deadline = date.fromisoformat(str(open_points.get("deadline")))
            days_left = (deadline - now.astimezone().date()).days
        except ValueError:
            deadline, days_left = None, None
        exported = str(open_points.get("exported_at") or "")[:10]
        lines.append(
            "MASTERARBEIT, OFFENE PUNKTE (aus notizen/offene_punkte.md, Stand der"
            f" Liste {open_points.get('list_stand') or '?'}, kopiert {exported})"
        )
        if deadline:
            lines.append(
                f"- Abgabe {deadline:%d.%m.%Y}, noch {days_left} Tage."
                f" {open_points.get('open_total')} offene Punkte,"
                f" {open_points.get('markers_offen')} Stellen „fehlt“ und"
                f" {open_points.get('markers_pruefen')} Stellen „prüfen“ im Text."
            )
        for row in open_points.get("schedule") or []:
            mark = "DIESE WOCHE: " if row.get("now") else ""
            lines.append(
                f"- Zeitplan {row.get('week')}: {mark}{row.get('write')}"
                + (f" (parallel: {row.get('parallel')})" if row.get("parallel") else "")
            )
        for sec in open_points.get("sections") or []:
            items = list(sec.get("items") or [])
            lines.append(f"- Offen bei „{sec.get('section')}“ ({len(items)}):")
            for item in items[:THESIS_ITEMS_PER_SECTION]:
                text = str(item)
                if len(text) > THESIS_ITEM_MAX:
                    text = text[: THESIS_ITEM_MAX - 1].rstrip() + "…"
                lines.append(f"  - {text}")
            if len(items) > THESIS_ITEMS_PER_SECTION:
                lines.append(
                    f"  - ... und {len(items) - THESIS_ITEMS_PER_SECTION} weitere"
                )
        marks = [
            m
            for m in open_points.get("markers") or []
            if m.get("offen") or m.get("pruefen")
        ]
        if marks:
            lines.append(
                "- Marker je Datei (fehlt/prüfen/Wörter): "
                + "; ".join(
                    f"{str(m['file']).split('/')[-1].replace('.tex', '')}"
                    f" {m['offen']}/{m['pruefen']}/{m['words']}"
                    for m in marks
                )
            )
        lines += _sync_lines(open_points.get("sync"))
        plan = [s for s in open_points.get("plan") or [] if isinstance(s, dict)]
        if plan:
            lines.append(
                "FAHRPLAN (feste Reihenfolge aus thesis_sync.plan, nicht"
                " umsortieren, nur kommentieren):"
            )
            for no, step in enumerate(plan, start=1):
                state = str(step.get("state"))
                until = str(step.get("wait_until") or "")
                if state == "wartet" and len(until) == 10:
                    # ISO date -> "17.11.": a step that waits is no work now.
                    state += f" bis {until[8:10]}.{until[5:7]}."
                elif state == "wartet" and step.get("wait_who"):
                    state += f" auf {step['wait_who']}"
                lines.append(
                    f"- {no}. [{state}] {step.get('title')}"
                    f" ({len(step.get('items') or [])} Punkte; {step.get('who')})"
                )
    notes = (cards or {}).get("thesis") or []
    if notes:
        lines.append(
            "MERKLISTE PRODUKTIVBEFUNDE (Kontext für Kapitel 4 und Limitationen in"
            " Kapitel 7, kein eigener Ergebnisteil):"
        )
        lines += [f"- [{n['group']}] {n['title']}: {n['text']}" for n in notes]
    return lines
