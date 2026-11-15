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
# 15.11.2026, Artur: measured values that a design decision rests on belong
# to the system chapter (Kap. 4).
G_SYSTEM = "Systementwurf (Messwerte hinter Designentscheidungen)"
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
    # 15.11.2026, Artur: Kap. 4 cites the ADR 033 inputs. The values in force
    # come from the cards (read live from HA), so a change at the February 2027
    # review changes this text; the sample sizes are those of the ADR.
    st = cards.get("settings") or {}
    if all(st.get(k) is not None for k in ("baseload_w", "gap_h", "efficiency")):
        out.append(
            _note(
                "hausreserve_herleitung",
                G_SYSTEM,
                "Herleitung der Hausreserve (ADR 033)",
                f"In Kraft: Grundlast {de(st['baseload_w'])} W, Abendlücke"
                f" {de(st['gap_h'], 2)} h, Wirkungsgrad"
                f" {de(st['efficiency'] * 100)} %, Boden"
                f" {de(st.get('floor_pct'))} %. Stichproben laut ADR 033"
                " (Messung 28.08. bis 12.11.2026): Grundlast Median 569 W über"
                " 101 Nächte, Abendlücke aus 40 Mining-Tagen, Wirkungsgrad aus"
                " 22 Nächten. Wiedervorlage Februar 2027 mit Winternächten.",
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


# 15.11.2026: a mining day needs at least 1 kWh. Standby draws ~0,44 kWh/day
# and the pool still pays residuals, which gave fake ~120 sats/kWh on days
# without mining (all of November).
MIN_MINING_KWH = 1.0


def _sats(conn: sqlite3.Connection) -> list[dict[str, str]]:
    """Energy-to-Sats (ADR 026/029): the system's target metric.

    Measured mining days with a settlement above zero. A stored 0 on a day
    with mining is a missing settlement (Aug/Sep 2026), not an earning of
    zero. Per month sum(sats) / sum(kWh): weights short days by their energy,
    so a payout shifted across midnight does not dominate.
    """
    try:
        rows = conn.execute(
            "SELECT day, energy_to_sats, mining_kwh FROM daily_kpi"
            " WHERE energy_to_sats > 0 AND mining_kwh >= ?"
            f" AND {_MEASURED} ORDER BY day",
            (MIN_MINING_KWH,),
        ).fetchall()
        zeros = conn.execute(
            "SELECT COUNT(*) FROM daily_kpi WHERE energy_to_sats = 0"
            f" AND mining_kwh >= ? AND {_MEASURED}",
            (MIN_MINING_KWH,),
        ).fetchone()[0]
    except sqlite3.OperationalError:
        return []
    if not rows:
        return []
    months: dict[str, list[float]] = {}
    for day, sats, kwh in rows:
        acc = months.setdefault(str(day)[:7], [0.0, 0.0, 0.0])
        acc[0] += float(sats) * float(kwh)
        acc[1] += float(kwh)
        acc[2] += 1
    parts = ", ".join(
        f"{MONTHS[int(m[5:7])]} {de(a[0] / a[1], 1)}"
        f" ({de(a[2])} {'Tag' if a[2] == 1 else 'Tage'}, {de(a[1])} kWh)"
        for m, a in months.items()
    )
    gap = (
        f" {de(zeros)} Mining-Tage mit gespeicherter 0 sind fehlende"
        " Abrechnungen und nicht mitgezählt."
        if zeros
        else ""
    )
    return [
        _note(
            "energy_to_sats",
            G_FINDING,
            "Energy-to-Sats: Zielgröße des Systems (ADR 026, ADR 029)",
            f"{de(len(rows))} gemessene Mining-Tage mit Abrechnung,"
            f" {de_day(str(rows[0][0]))} bis {de_day(str(rows[-1][0]))}."
            f" Sats je kWh nach Monat (Summe Sats durch Summe kWh): {parts}."
            f"{gap} Tage unter {de(MIN_MINING_KWH)} kWh sind Standby. Die"
            " Annahme aus ADR 029, reiner Eco-Betrieb im Winter bringe mehr"
            " Sats je kWh, bestätigen die Daten bisher nicht (Nachtrag"
            " 15.11.2026). Der Wert hängt auch an Netzwerk-Difficulty und"
            " Pool-Glück, nicht nur an der Steuerung: ein Monatsvergleich"
            " zeigt keine Wirkung der Regeln.",
        )
    ]


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
    # 15.11.2026: "kap4_hausreserve" (Kap. 4.5 auf ADR 033) entfernt, erledigt
    # am 14.11.2026 (Abgleich: Befund hausreserve "aktuell"). Offene Notizen
    # hier haben kein Ablaufdatum: ist ein Punkt erledigt, die Notiz löschen,
    # sonst meldet Bitsy ihn weiter als offen.
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
        "saisonsperre_bug",
        G_LIMIT,
        "Regelfehler in der Produktion: Saison-Sperre (ADR 030)",
        "Am 25.09.2026 lief ein Miner in Super, obwohl die Saison Super"
        " sperrte. Ursache: die Schwelle wurde nur auf 100 % gedeckelt statt"
        " unerreichbar gemacht, bei vollem Akku griff R3 trotzdem; R5 war"
        " gleich gebaut. Behoben in den Home-Assistant-Regeln, nicht im"
        " Python-Kern. Zeigt: deterministisch heißt nachvollziehbar, nicht"
        " fehlerfrei. Der Fehler war nur auffindbar, weil Anzeige und"
        " Schaltlogik sichtbar widersprachen. Super-Phasen vor dem 25.09.2026"
        " in Übergangsmonaten sind kein gewolltes Regelverhalten.",
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

GROUP_ORDER = (G_FRAME, G_SYSTEM, G_FINDING, G_METHOD, G_LIMIT, G_EXPLAIN, G_OPEN)


def build(conn: sqlite3.Connection, cards: dict[str, Any]) -> list[dict[str, str]]:
    """All notes, ordered by group. ``cards`` is the dict of the same run."""
    notes = (
        _automation(cards.get("automation") or {})
        + _cards(cards)
        + _recording(conn)
        + _sats(conn)
        + _log_sources(conn)
        + list(FIXED_NOTES)
    )
    return sorted(notes, key=lambda n: GROUP_ORDER.index(n["group"]))
