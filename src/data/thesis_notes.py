"""
Thesis notes: what the production data shows and what the thesis has to say
about it (card "Masterarbeit", tab Forschung).

A checklist, not thesis text. Every number is read from the research DB or
from the cards built in the same run, so the card cannot drift away from the
data; the fixed sentences name the limits that belong next to each number
(quality axis "Wissenschaftliche Sauberkeit": no overstating, limitations
transparent). Dated observations that cannot be recomputed (migration,
manual checks of the language model) carry their date in the text.

Read-only. Written by research_cards.py into research_cards.json ("thesis").
"""

from __future__ import annotations

import sqlite3
from typing import Any

from src.data.recording_status import suspect_by_day, suspect_runs

# Groups in the order of the card.
G_FRAME = "Einordnung"
G_FINDING = "Befunde aus den Produktivdaten"
G_METHOD = "Datenbasis und Methodik"
G_LIMIT = "Limitationen, die genannt werden müssen"
G_EXPLAIN = "Erklärschicht (Sprachmodell)"
G_OPEN = "Aus dem System noch offen"

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


def de(value: float | int | None, digits: int = 0) -> str:
    """German number format (1.234,5); '—' for a missing value."""
    if value is None:
        return "—"
    text = f"{float(value):,.{digits}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def de_day(iso: str | None) -> str:
    """2026-05-25 -> 25.05.2026."""
    if not iso or len(iso) < 10:
        return "—"
    return f"{iso[8:10]}.{iso[5:7]}.{iso[0:4]}"


def _one(conn: sqlite3.Connection, sql: str) -> tuple[Any, ...]:
    try:
        row = conn.execute(sql).fetchone()
    except sqlite3.OperationalError:
        return ()
    return tuple(row) if row else ()


def _note(nid: str, group: str, title: str, text: str) -> dict[str, str]:
    """``nid`` is stable: the thesis cites it as ``% Befund: <nid>``."""
    return {"id": nid, "group": group, "title": title, "text": text}


# Same rule as research_cards.unmeasured_days: fewer than 6 blocks not ok.
_MEASURED = "COALESCE(quality_warn, 0) + COALESCE(quality_error, 0) < 6"


def _recording(conn: sqlite3.Connection) -> list[dict[str, str]]:
    row = _one(
        conn,
        # Sums only over measured days: a day with at least one hour of
        # warn/error blocks (stored, not measured) would add wrong values.
        "SELECT COUNT(*), SUM(blocks >= 144), MIN(day), MAX(day),"
        " COALESCE(SUM(quality_error), 0),"
        f" SUM(CASE WHEN {_MEASURED} THEN pv_kwh END),"
        f" SUM(CASE WHEN {_MEASURED} THEN mining_kwh END),"
        f" SUM(CASE WHEN {_MEASURED} THEN grid_import_kwh END),"
        f" SUM(CASE WHEN {_MEASURED} THEN grid_export_kwh END),"
        f" SUM(CASE WHEN {_MEASURED} THEN heizstab_kwh END),"
        f" SUM(NOT ({_MEASURED}))"
        " FROM daily_kpi",
    )
    if not row or not row[0]:
        return []
    days, full, first, last, errors, pv, mining, imp, exp, heiz, unmeasured = row
    return [
        _note(
            "datenbasis",
            G_METHOD,
            "Datenbasis",
            f"{de(days)} Tage vom {de_day(first)} bis {de_day(last)}, davon"
            f" {de(full)} vollständig (144 Blöcke zu 10 Minuten), {de(errors)}"
            " Blöcke mit Qualitätsfehler. Summen über die"
            f" {de(days - (unmeasured or 0))} gemessenen Tage (ohne"
            f" {de(unmeasured or 0)} Tage mit mindestens einer Stunde ohne Messung):"
            " Solar"
            f" {de(pv)} kWh, Mining {de(mining)} kWh, Heizstab {de(heiz)} kWh,"
            f" Netzbezug {de(imp)} kWh, Einspeisung {de(exp)} kWh. Ein Haushalt,"
            " eine Anlage: Fallstudie, keine Stichprobe.",
        ),
        _note(
            "lueckenfuellung",
            G_METHOD,
            "Nachträglicher Abgleich am 14.11.2026",
            "50 fehlende und 9 unvollständige Tage wurden aus dem"
            " Home-Assistant-Recorder nachgeholt (Aufbewahrung 365 Tage,"
            " Rohwerte lagen vor). Vorhandene Blöcke wurden dabei nicht"
            " überschrieben. Muss im Methodenteil stehen: Die Lücken waren"
            " Lücken im Abgleich, nicht in der Messung.",
        ),
    ] + _suspect(conn)


def _suspect(conn: sqlite3.Connection) -> list[dict[str, str]]:
    """Stored-but-not-measured blocks (recording_status.suspect_runs)."""
    try:
        rows = conn.execute(
            "SELECT block_id, house_load_w, battery_soc_pct, grid_import_w,"
            " pv_power_w FROM energy_states ORDER BY block_id"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    runs = [r for r in suspect_runs(rows) if r["blocks"] >= 6]
    if not runs:
        return []
    days = [d for d, n in suspect_by_day(runs).items() if n >= 6]
    hours = sum(r["blocks"] for r in runs) / 6
    held = sum(r["blocks"] for r in runs if r["kind"] == "held") / 6
    return [
        _note(
            "ungemessen",
            G_LIMIT,
            "Gespeichert, aber nicht gemessen",
            f"{de(hours)} Stunden in {len(runs)} Zeiträumen an {len(days)} Tagen"
            f" ({de_day(days[0])} bis {de_day(days[-1])}) wurden gespeichert,"
            " obwohl Home Assistant keine Werte lieferte, und standen bis zum"
            f" 14.11.2026 als quality=ok in der Datenbank: {de(held)} Stunden mit"
            " eingefrorenen Werten (der"
            " Abgleich schrieb den letzten Wert fort, am 07./08.08.2026 23"
            " Stunden lang), der Rest mit Hausverbrauch 0 W (eine verlorene"
            " SMA-Verbindung wird über die Vorgabe 0 zum Messwert; am"
            " 27.05.2026 lud der Akku von 18 auf 100 %, während PV 0 W"
            " zeigte). Erkannt über physikalisch unmögliche Muster und am"
            " 14.11.2026 als quality=warn markiert (Messwerte unverändert,"
            " Backup vorher, jeder Block trägt den Grund). Akku über Nacht,"
            " Akku-Höchststand und Prognose lassen Tage mit mindestens einer"
            " Stunde davon aus, ebenso die Summen in „Datenbasis“."
            " Neue Fälle markiert der Abgleich seither selbst. Gehört in den"
            " Methodenteil: Erkennungsregel, Anzahl, Umgang.",
        )
    ]


def _automation(auto: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    sw = auto.get("switching") or {}
    months = [m for m in sw.get("months") or [] if m.get("mining_days")]
    if months:
        days = sum(m["mining_days"] for m in months)
        over = sum(m["days_over"] for m in months)
        dropouts = sum(m.get("dropouts", 0) for m in months)
        worst = max(months, key=lambda m: m["max_start_stop"])
        out.append(
            _note(
                "schaltwechsel",
                G_FINDING,
                "Qualitätsziel Schaltwechsel wird verfehlt",
                f"Ziel sind höchstens {sw.get('target', 2)} Start/Stopp-Wechsel"
                f" je Tag. An {de(over)} von {de(days)} Tagen mit Mining"
                f" ({de(100 * over / days)} %) waren es mehr, Höchstwert"
                f" {de(worst['max_start_stop'])} im"
                f" {MONTHS[int(worst['month'][5:7])]}. Gezählt am gemeldeten"
                f" Modus des Miners seit {de_day(sw.get('since'))}."
                f" {de(dropouts)} kurze Aus-Phasen unter"
                f" {sw.get('dropout_max_min', 15)} Minuten zählen als"
                " Verbindungsabbruch, nicht als Stopp und Start (nach einem"
                " Stopp sperrt die Automatik den Neustart 15 Minuten). Stand 14.11.2026: ohne diese"
                " Trennung wären es 64 Tage (41 %), mit 5 Minuten Grenze 21:"
                " Die Pausen sind zweigeteilt (194 unter 5 Minuten, 324 über eine"
                " Stunde, 23 dazwischen), das Ergebnis also robust. Das Ziel ist"
                " in 01.2 über DecisionEvents definiert, die es in der Produktion"
                " nicht gibt: Definition in der Arbeit anpassen.",
            )
        )
    su = auto.get("surplus") or {}
    if su.get("hours"):
        reasons: dict[str, float] = {}
        known = 0.0
        for m in su.get("months") or []:
            for label, hours in (m.get("reasons") or {}).items():
                if label != "unbekannt":
                    reasons[label] = reasons.get(label, 0.0) + hours
                    known += hours
        top = max(reasons.items(), key=lambda x: x[1]) if reasons else None
        cause = (
            f" Für {de(known, 1)} Stunden liegt die Diagnose der Automatik vor,"
            f" häufigster Grund: {top[0]} ({de(top[1], 1)} Stunden)."
            if top
            else ""
        )
        out.append(
            _note(
                "ueberschuss",
                G_FINDING,
                "Ungenutzter Solarüberschuss",
                f"{de(su['hours'], 1)} Stunden mit mehr als 1 kW Einspeisung bei"
                f" stehenden Minern, zusammen {de(su['export_kwh'], 1)} kWh."
                f"{cause} Der Akku lud dann an seiner Leistungsgrenze, der Rest"
                " ging ins Netz. Das ist eine Folge der Regelpriorität (Akku"
                " vor Mining), kein Fehler; als Zielkonflikt diskutieren.",
            )
        )
    sf = auto.get("safety") or {}
    if sf:
        hot_rows = [r for r in sf.get("rows") or [] if r.get("hot_blocks")]
        worst_hot = max(hot_rows, key=lambda r: r["hot_blocks"]) if hot_rows else None
        hot_text = (
            f" {de(worst_hot['hot_blocks'])} davon bei {worst_hot['miner']} im"
            f" {MONTHS[int(worst_hot['month'][5:7])]}."
            if worst_hot
            else ""
        )
        out.append(
            _note(
                "uebertemperatur",
                G_FINDING,
                "Übertemperatur",
                f"{de(sf.get('hot_blocks_total'))} Blöcke mit Chip-Temperatur ab"
                f" {sf.get('tmax_limit_c', 110)} °C.{hot_text} Das Qualitätsziel"
                " in 01.2 nennt 0 Ereignisse über 85 °C; gemessen wird aber die"
                " Chip-Temperatur, deren Schutzschwelle bei 112 °C liegt. Die"
                " beiden Angaben meinen verschiedene Messgrößen: in der Arbeit"
                " eine Definition festlegen.",
            )
        )
        out.append(
            _note(
                "schaltfehler",
                G_LIMIT,
                "Schaltfehler sind fast ganz ein Umzugsartefakt",
                f"{de(sf.get('errors_total'))} Blöcke mit abweichendem Soll und"
                " Ist. 92 davon liegen am 12. und 13.08.2026, dem Umzug des"
                " Servers (Befehl Eco, Miner gemeldet Off). Nicht als"
                " Fehlerrate der Steuerung berichten.",
            )
        )
    return out


def _cards(cards: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    judged = [
        m for m in (cards.get("nights") or {}).get("months") or [] if m.get("verdict")
    ]
    if judged:
        words = {
            "passt": "passt",
            "zu_niedrig": "zu niedrig",
            "zu_hoch": "zu hoch",
        }
        parts = ", ".join(
            f"{MONTHS[m['month']]}: Akku morgens"
            f" {de(m['morning_after_mining'], 1)} % nach"
            f" {m['mined_nights']} Mining-Tagen ({words.get(m['verdict'], '—')})"
            for m in judged
        )
        floor = (cards.get("settings") or {}).get("floor_pct")
        out.append(
            _note(
                "hausreserve",
                G_FINDING,
                "Saisonale Hausreserve (ADR 028, ADR 033)",
                f"Ziel sind {de(floor)} % Akku am Morgen. {parts}. Die Urteile"
                " bis 13.11.2026 stammen aus Nächten mit der alten Formel,"
                " ADR 033 gilt erst seit diesem Tag: ein Vorher-Nachher-"
                " Vergleich ist erst mit den Winterdaten möglich.",
            )
        )
    hz = cards.get("heizstab") or {}
    if hz.get("days"):
        out.append(
            _note(
                "heizstab",
                G_FINDING,
                "Heizstab konkurriert mit dem Akku",
                f"In {hz['days']} Tagen nahm der Heizstab"
                f" {de(hz.get('heizstab_kwh_not_full'), 1)} kWh Solarstrom,"
                " während der Akku nicht voll war; an"
                f" {hz.get('empty_mornings')} Morgen war der Akku leer. Das Gerät"
                " regelt selbst und ist in Home Assistant nur lesbar. Zeigt die"
                " Grenze eines Steuerkerns, der nicht alle flexiblen Lasten"
                " kontrolliert.",
            )
        )
    fc = cards.get("forecast") or {}
    if fc.get("days_used"):
        out.append(
            _note(
                "prognose",
                G_FINDING,
                "Solarprognose im Winter unbrauchbar ungenau",
                f"Über {fc['days_used']} Tage: mittlere Abweichung"
                f" {de(fc.get('mae_pct'))} %, systematisch"
                f" {de(fc.get('bias_pct'))} % zu hoch. Kurzer Zeitraum, nur"
                " Winter: stützt die Entscheidung, die Prognose nur als Veto"
                " (R4) und nicht als Startsignal zu nutzen, belegt aber keine"
                " Jahresaussage.",
            )
        )
    eff = [
        m
        for m in (cards.get("efficiency") or {}).get("miners") or []
        if m.get("verdict")
    ]
    if eff:
        parts = ", ".join(f"{m['miner']} {de(m.get('change_pct'), 1)} %" for m in eff)
        out.append(
            _note(
                "effizienz",
                G_FINDING,
                "Miner-Effizienz stabil",
                f"Änderung der Watt je Terahash seit dem ersten Monat: {parts}"
                " (nur reine Eco-Tage, Monatsmedian). Kein Verschleiß messbar.",
            )
        )
    return out


def _log_sources(conn: sqlite3.Connection) -> list[dict[str, str]]:
    modes = _one(
        conn,
        "SELECT COUNT(*), MIN(timestamp) FROM ha_decision_log WHERE kind = 'mode'",
    )
    rules = _one(
        conn,
        "SELECT COUNT(*), MIN(timestamp) FROM ha_decision_log WHERE kind = 'rule'",
    )
    diag = _one(conn, "SELECT COUNT(*), MIN(timestamp) FROM ha_diagnose_log")
    core = _one(conn, "SELECT COUNT(*), MAX(timestamp) FROM decision_events")
    out: list[dict[str, str]] = []
    if modes and modes[0]:
        out.append(
            _note(
                "protokoll",
                G_METHOD,
                "Entscheidungsprotokoll der Produktion",
                f"{de(modes[0])} Moduswechsel seit {de_day(str(modes[1])[:10])},"
                f" {de(rules[0] if rules else 0)} Regelwechsel mit Begründung seit"
                f" {de_day(str(rules[1])[:10]) if rules and rules[1] else '—'},"
                f" {de(diag[0] if diag else 0)} Soll-Ist-Diagnosen seit"
                f" {de_day(str(diag[1])[:10]) if diag and diag[1] else '—'}."
                " Nachträglich aus Sensoren geholt, die Home Assistant selbst"
                " schreibt (kein nachberechneter Grund). Die Schwellen je Tag"
                " stehen in settings_history, exakt ab dem 14.11.2026, die"
                " berechneten Saisonschwellen ab dem 26.08.2026.",
            )
        )
        out.append(
            _note(
                "protokoll_grenzen",
                G_LIMIT,
                "Grenzen des Entscheidungsprotokolls",
                "Protokolliert ist der Zustand der Regeln (zum Beispiel R1"
                " Stopp, Cooldown), nicht welcher Zweig der Automation"
                " geschaltet hat. Einzelne Handeingriffe sind nicht"
                " rekonstruierbar, nur Phasen im Handbetrieb. Vor dem"
                " 31.08.2026 gibt es Moduswechsel ohne Begründung. Ein"
                " vollständiger Replay der Produktion ist damit nicht möglich.",
            )
        )
    if core and core[0]:
        out.append(
            _note(
                "zwei_steuerungen",
                G_LIMIT,
                "Zwei Steuerungen: Python-Kern und Home-Assistant-Regeln",
                f"Der deterministische Python-Kern (src/core, Regeln R1 bis R5)"
                f" lief nur im Testbetrieb: {de(core[0])} Entscheidungen, die"
                f" letzte am {de_day(str(core[1])[:10])}. Alle Produktivdaten"
                " stammen aus den Regeln in Home Assistant (R1 bis R8, YAML)."
                " Die Arbeit muss klar trennen, welche Aussage für welches"
                " System gilt: Replay-Fähigkeit ist für den Kern gezeigt"
                " (Simulation, Lab), für die Produktion nur eingeschränkt.",
            )
        )
    return out


# Dated observations that the DB cannot recompute.
FIXED_NOTES: tuple[dict[str, str], ...] = (
    _note(
        "einordnung",
        G_FRAME,
        "Wohin diese Punkte gehören",
        "Die Arbeit ist ein Experiment zu Erklärtexten; das System ist die"
        " Versuchsapparatur. Messwerte und Produktivzahlen gehören nicht in"
        " Kapitel 4 (Regel vom 14.11.2026). Die Befunde unten sind Material für"
        " Kapitel 5 (Datenbasis), Kapitel 6 (eigener deskriptiver Abschnitt"
        " ohne Forschungsfrage, damit er nicht als Studienergebnis gelesen"
        " wird) und Kapitel 7 (Limitationen). Für Kapitel 4 liefert die"
        " Merkliste nur den Befund zur Erklärschicht.",
    ),
    _note(
        "kap4_hausreserve",
        G_OPEN,
        "Kapitel 4.5 Saisonale Hausreserve ist überholt",
        "Der Entwurf beschreibt die Grundlast 535 W als bewusste Abwägung."
        " Seit ADR 033 (13.11.2026) gilt eine neue Formel mit 570 W,"
        " Abendlücke 0,75 h, Wirkungsgrad 80 % und Boden 5 %. Entschieden"
        " am 14.11.2026: Kapitel 4 beschreibt nur den aktuellen Stand (ADR"
        " 033), die alte Formel entfällt. Ausnahme: Zeigt der Stimulus der"
        " Studie Werte der alten Formel, nennt Kapitel 5 diese Werte so, wie"
        " die Teilnehmenden sie sahen.",
    ),
    _note(
        "sprachmodell",
        G_EXPLAIN,
        "Sprachmodell nur lesend, mit deterministischem Filter",
        "Prüflauf am 14.11.2026 über alle 9 Tabs (lokales Modell, ein Lauf):"
        " 31 Aussagen erzeugt, 7 davon vom festen Filter verworfen (Karte"
        " existiert schon, Datenquelle veraltet, Widerspruch zum Karteninhalt)."
        " Von den 24 verbliebenen hielt die manuelle Prüfung nur einen Teil"
        " für zutreffend; typische Fehler: vorhandene Karten erneut"
        " vorgeschlagen, Rohwert falsch gelesen. Einzelbeobachtung ohne"
        " Zweitprüfer, kein Gütemaß. Stützt die Architekturentscheidung: das"
        " Modell erklärt und schlägt vor, es schaltet nichts.",
    ),
    _note(
        "winter",
        G_LIMIT,
        "Winter ohne Mining",
        "Im November blieb der Akku fast durchgehend unter der Hausreserve,"
        " die Miner standen. Aussagen zur Steuerung stützen sich auf Juni bis"
        " Oktober; für den Winter zeigt die Arbeit, dass die Automatik"
        " korrekt nicht schaltet, nicht wie gut sie schaltet.",
    ),
    _note(
        "qualitaetsziele",
        G_OPEN,
        "Vor der Abgabe klären",
        "Definition der Qualitätsziele Schaltwechsel und Übertemperatur an"
        " die Messung anpassen. Entscheiden, ob der schaltende Zweig der"
        " Automation noch protokolliert wird. Stichtag für alle Zahlen aus"
        " der Produktion festlegen und im Text nennen (die Werte hier"
        " ändern sich täglich). Wirtschaftlichkeit (Tab Bitcoin: Ertrag gegen"
        " Investition) nur mit diesem Stichtag übernehmen. Die Prüfung der"
        " Hausreserve-Formel mit Winterdaten (Februar 2027) liegt nach der"
        " Abgabe: als Ausblick nennen, nicht als Ergebnis.",
    ),
)

GROUP_ORDER = (G_FRAME, G_FINDING, G_METHOD, G_LIMIT, G_EXPLAIN, G_OPEN)


def build(conn: sqlite3.Connection, cards: dict[str, Any]) -> list[dict[str, str]]:
    """All notes, ordered by group. ``cards`` is the dict of the same run."""
    notes = (
        _automation(cards.get("automation") or {})
        + _cards(cards)
        + _recording(conn)
        + _log_sources(conn)
        + list(FIXED_NOTES)
    )
    return sorted(notes, key=lambda n: GROUP_ORDER.index(n["group"]))
