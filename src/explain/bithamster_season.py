"""Deterministic checks of the seasonal SoC automation for the KI hamster.

The seasonal automation (``automation.mvp_saison_automatik`` in
``packages/mvp_auto.yaml``, ADR 028) sets the stop threshold ("Hausreserve")
from two assumptions: the night base load (``input_number.mvp_night_baseload_w``)
and the length of the longest night of the month. ADR 028 was decided without
winter measurements. Since autumn 2026 the research database has the nights to
check those assumptions, so this module measures them and states the verdict.

Like the rest of the hamster, everything here is read-only and computed in
Python; the model only phrases the result (lesson from 13.11.2026: rules given
in words were applied unreliably, finished verdicts were reproduced correctly).
Nothing here feeds back into a threshold. Changing the base load stays a human
decision in the Einstellungen tab.
"""

from __future__ import annotations

from typing import Any

# The measurement itself lives in the data layer (also used by the Forschung
# cards, src/data/research_cards.py), so card and hamster cannot disagree.
# Re-exported here for the hamster and its tests.
from src.data.research_cards import (  # noqa: F401
    FORMULA_SINCE,
    MIN_MINED_NIGHTS,
    MIN_NIGHTS,
    NIGHT_HOURS,
    OFFSETS,
    RESERVE_CAP_PCT,
    RESERVE_FLOOR_PCT,
    RESERVE_FORMULA_V2_SINCE,
    RULE_HOLDS_SHARE,
    RULE_TOLERANCE_PCT,
    VERDICT_HIGH_MARGIN_PCT,
    low_limit,
    night_check,
    reserve_verdict,
    rule_holds,
    season_table,
)

MONTHS_DE = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


def _de(value: float | None, digits: int = 0) -> str:
    if value is None:
        return "unbekannt"
    text = f"{value:,.{digits}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def verdict_text(verdict: str, floor_pct: float) -> str:
    """German verdict sentence; the target is the configured floor (ADR 033)."""
    f = _de(floor_pct)
    return {
        "zu_niedrig": (
            f"HAUSRESERVE ZU NIEDRIG: Ziel sind {f} % am Morgen, der Akku reicht"
            " nicht durch die Nacht, der Rest kommt aus dem Netz."
        ),
        "zu_hoch": (
            f"HAUSRESERVE ZU HOCH: morgens bleibt deutlich mehr als {f} % übrig,"
            " die Miner könnten länger laufen."
        ),
        "passt": f"HAUSRESERVE PASST (Ziel {f} % am Morgen).",
    }[verdict]


def season_findings(
    table: list[dict[str, Any]], checks: dict[int, dict[str, Any]]
) -> list[str]:
    """Short, finished findings for the priority list ("Alles prüfen")."""
    by_month = {r["month"]: r for r in table}
    out = []
    for month in sorted(checks):
        c = checks[month]
        verdict = reserve_verdict(c)
        if verdict in (None, "passt"):
            continue
        word = "zu niedrig" if verdict == "zu_niedrig" else "zu hoch"
        # Live 13.11.2026: "Hausreserve 90 % war zu niedrig" mixed the new
        # table value (ADR 033) with nights measured under the old formula.
        # Name the measured shutdown SoC and the value that applies now.
        stops = sorted(v for v in c.get("stop_socs") or [] if v is not None)
        was = (
            f"Miner schalteten im Mittel bei {_de(stops[len(stops) // 2])} % ab,"
            if stops
            else ""
        )
        # Live 13.11.2026 ("Optimierung finden"): the model proposed raising
        # the reserve again, hours after ADR 033 had done exactly that. The
        # status goes first: answer points are clipped at 260 characters.
        if str(c.get("last_day") or "") < RESERVE_FORMULA_V2_SINCE:
            out.append(
                f"Saisonale Automatik {MONTHS_DE[month]}: BEREITS KORRIGIERT"
                f" (ADR 033). Die Hausreserve war {word} ({was} morgens"
                f" {_de(c['morning_after_mining'])} % statt"
                f" {_de(c.get('floor_pct', RESERVE_FLOOR_PCT))} %, Netzbezug"
                f" {_de(c['grid_kwh_after_mining'], 1)} kWh in {c['mined_nights']}"
                f" Nächten); seit 13.11.2026 gilt {by_month[month]['stop']} %."
                " Nichts mehr einstellen, im Februar prüfen."
            )
            continue
        out.append(
            f"Saisonale Automatik {MONTHS_DE[month]}: Hausreserve ist {word} ({was}"
            f" eingestellt {by_month[month]['stop']} %). Nach Mining-Tagen stand der"
            f" Akku morgens im Mittel bei {_de(c['morning_after_mining'])} % statt"
            f" {_de(c.get('floor_pct', RESERVE_FLOOR_PCT))} %. Netzbezug in diesen"
            f" {c['mined_nights']} Nächten {_de(c['grid_kwh_after_mining'], 1)} kWh"
            " (Tab Einstellungen, Karte Saisonale Schwellwerte). Stellschrauben:"
            " Grundlast, Abendlücke, Wirkungsgrad, Boden."
        )
    return out


def season_lines(
    table: list[dict[str, Any]],
    checks: dict[int, dict[str, Any]],
    settings: dict[str, float],
    month_now: int,
) -> list[str]:
    """Context block: the table as configured plus the measured verdict."""
    baseload_w = settings["baseload_w"]
    floor = settings["floor_pct"]
    lines = [
        "SAISONALE AUTOMATIK (Tab Einstellungen, Karte Saisonale Schwellwerte)",
        f"- Formel (ADR 033, seit 13.11.2026): Hausreserve = Nacht-Grundlast"
        f" {_de(baseload_w)} W × (längste Nacht des Monats + Abendlücke"
        f" {_de(settings['gap_h'], 2)} h) ÷ (Akku {_de(settings['capacity_kwh'], 1)} kWh ×"
        f" Wirkungsgrad {_de(settings['efficiency'] * 100)} %) + Boden {_de(floor)} %."
        " Alle vier Größen sind gemessen und im Tab Einstellungen einstellbar. Darüber"
        " Eco ab +10, Standard ab +25 (endet +20), Super ab +40 (endet +35). Über"
        " 100 % ist die Stufe im Monat gesperrt. Die Automatik setzt die Werte jede"
        " Nacht neu. Die Messung unten stammt aus Nächten, in denen noch die alte"
        " Formel galt (Grundlast × Nacht ÷ Akku + 15 %).",
        "- Tabelle mit den heutigen Einstellungen (Monat: Hausreserve / Eco ab /"
        " Standard ab / Super ab / Stufe):",
    ]
    for r in table:
        mark = " (JETZT)" if r["month"] == month_now else ""

        def cell(v: Any) -> str:
            return f"{v} %" if v is not None else "gesperrt"

        lines.append(
            f"  {MONTHS_DE[r['month']]}{mark}: {r['stop']} % / {cell(r['eco'])} /"
            f" {cell(r['std'])} / {cell(r['super'])} / {r['tier']}"
        )

    usable = {m: c for m, c in checks.items() if c["nights"] >= MIN_NIGHTS}
    if not usable:
        lines.append(
            "- Messung: noch zu wenige vollständige Nächte seit Einführung der Formel"
            f" ({FORMULA_SINCE}). Über die Formel kannst du nichts Gemessenes sagen."
        )
        return lines

    lines.append(
        f"- MESSUNG der echten Nächte seit {FORMULA_SINCE} (fest berechnet, genau so"
        " übernehmen):"
    )
    by_month = {r["month"]: r for r in table}
    all_nights = sum(c["nights"] for c in usable.values())
    all_hours = sum(c["night_h"] * c["nights"] for c in usable.values())
    all_kwh = sum(c["load_kwh"] * c["nights"] for c in usable.values())
    measured_w = all_kwh * 1000 / all_hours if all_hours else None
    for month in sorted(usable):
        c = usable[month]
        target = by_month[month]["stop"]
        lines.append(
            f"  - {MONTHS_DE[month]}: {c['nights']} Nächte, Haus nachts im Mittel"
            f" {_de(c['load_w'])} W über {_de(c['night_h'], 1)} h ="
            f" {_de(c['load_kwh'], 1)} kWh. Akku morgens im Mittel"
            f" {_de(c['morning_soc'])} %, in {c['morning_low']} von {c['nights']}"
            f" Nächten unter {_de(low_limit(floor))} %. Netzbezug nachts zusammen"
            f" {_de(c['grid_kwh'], 1)} kWh."
        )
        if c["mined_nights"] >= MIN_MINED_NIGHTS:
            k = c["mined_nights"]
            morning = c["morning_after_mining"]
            verdict = verdict_text(reserve_verdict(c) or "passt", floor)
            # Eval 13.11.2026: nights under the old formula were compared with
            # the NEW table value ("0 von 26 an der Schwelle 79 %"), a pure
            # artefact. Before ADR 033 only the measured shutdown SoC counts.
            if str(c.get("last_day") or "") < RESERVE_FORMULA_V2_SINCE:
                stops = sorted(v for v in c.get("stop_socs") or [] if v is not None)
                rule_part = (
                    f"    An {k} Tagen liefen die Miner nachmittags (alte Formel,"
                    f" abgeschaltet im Mittel bei {_de(stops[len(stops) // 2])} %)."
                    if stops
                    else f"    An {k} Tagen liefen die Miner nachmittags (alte Formel)."
                )
            else:
                at_stop, holds = rule_holds(c, target)
                rule = "REGEL HÄLT" if holds else "REGEL HÄLT NICHT ZUVERLÄSSIG, prüfen"
                rule_part = (
                    f"    An {k} Tagen liefen die Miner nachmittags; an {at_stop} davon"
                    f" schalteten sie an der Schwelle {target} % ab (±"
                    f"{_de(RULE_TOLERANCE_PCT)} %): {rule}."
                )
            lines.append(
                rule_part + " Am Morgen danach stand der"
                f" Akku im Mittel bei {_de(morning)} %: {verdict} Von Miner-Stopp bis"
                f" Morgen brauchte das Haus {_de(c['from_stop_kwh'], 1)} kWh aus dem"
                f" Akku; mit dem eingestellten Wirkungsgrad wären dafür"
                f" {_de(c['needed_stop'])} % Hausreserve nötig. Netzbezug"
                f" in den Nächten nach diesen Mining-Tagen zusammen"
                f" {_de(c['grid_kwh_after_mining'], 1)} kWh."
            )
        unmined = c["nights"] - c["mined_nights"]
        if unmined:
            lines.append(
                f"    In {unmined} Nächten liefen die Miner an dem Tag gar nicht (zu"
                " wenig Sonne oder gesperrt). Ein leerer Akku am Morgen liegt dann"
                " NICHT an den Minern, sondern am Hausverbrauch."
            )
    if measured_w is not None and baseload_w > 0:
        ratio = measured_w / baseload_w
        if ratio > 1.1:
            word = "HÖHER als eingestellt"
        elif ratio < 0.9:
            word = "NIEDRIGER als eingestellt"
        else:
            word = "passt zur Einstellung"
        lines.append(
            f"  - Nacht-Grundlast gemessen {_de(measured_w)} W über {all_nights} Nächte,"
            f" eingestellt {_de(baseload_w)} W: {word}."
        )
    lines.append(
        "  - Hinweis: Eine höhere Hausreserve schützt die Nacht, kostet aber Minen am"
        " Nachmittag. Das ist eine Abwägung für den Menschen, keine Fehlfunktion."
    )
    return lines
