"""
DailyReport — deterministischer Tagesbericht aus bitgrid.db nach Markdown.

Dies ist die **Faktenseite** des Obsidian-Gedaechtnisses. Kein LLM, keine
Deutung, keine Empfehlung: nur gezaehlte und gerechnete Groessen aus der DB.
Zweimal aufgerufen ergibt zweimal dasselbe Dokument (Reproduzierbarkeit).

Die Deutung passiert getrennt davon in einer `*_hypothesen.md` desselben Tages,
geschrieben vom Nachtanalysten. Warum die Trennung physisch sein muss, steht in
`database_exploration/README.md`: sonst zitiert der Agent seine eigenen
unbestaetigten Vermutungen spaeter als Beleg.

Der Tag wird am **Sonnenstand** verankert, nicht an der Uhr: Sonnenhoechststand
ist die Mitte des energetisch relevanten Tages. Die Elevation kommt aus dem
HA-Recorder (sensor.sun_elevation); ist HA nicht erreichbar, faellt der Bericht
auf den PV-Peak zurueck und sagt das auch.

CLI:
  python -m src.data.daily_report                     # gestern
  python -m src.data.daily_report --date 2026-07-20
  python -m src.data.daily_report --date 2026-07-20 --out pfad/zur/datei.md
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from src.data.db import get_connection
from src.data.ha_history_sync import _ha_url, fetch_history

log = logging.getLogger(__name__)

BLOCK_MINUTES = 10
BLOCKS_PER_DAY = 24 * 60 // BLOCK_MINUTES
SUN_ENTITY = "sensor.sun_elevation"

# Schwellen aus dem Live-Regelwerk (packages/mvp_auto.yaml): stop 60,
# eco_start 70, std 85, super 100. Hier nur zum Zaehlen verwendet, nicht zum
# Entscheiden. Der Bandname nennt den hoechsten Modus, den die Leiter in
# diesem Bereich erlaubt.
SOC_BANDS: tuple[tuple[str, float, float], ...] = (
    ("gesperrt (<60%)", -1.0, 60.0),
    ("Halten (60-70%)", 60.0, 70.0),
    ("Eco (70-85%)", 70.0, 85.0),
    ("Standard (85-100%)", 85.0, 100.0),
    ("Super (100%)", 100.0, 1000.0),
)
TEMP_WARN_C = 100.0
TEMP_CRIT_C = 110.0
TEMP_MISSING_C = 999.0


def _fmt(value: float | None, digits: int = 1, suffix: str = "") -> str:
    if value is None:
        return "keine Daten"
    return f"{value:.{digits}f}{suffix}"


def _kwh_from_w(sum_w: float | None) -> float | None:
    """Summe der Block-Leistungen (W) in Energie (kWh) umrechnen."""
    if sum_w is None:
        return None
    return sum_w * (BLOCK_MINUTES / 60.0) / 1000.0


def _day_bounds(day: date) -> tuple[str, str]:
    """ISO-Grenzen des Tages, wie die block_id-Strings sie sortieren."""
    start = datetime.combine(day, time.min).strftime("%Y-%m-%dT%H:%M:%S")
    end = datetime.combine(day + timedelta(days=1), time.min).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    return start, end


def _fetch_sun(day: date) -> list[tuple[datetime, float | None]]:
    """Sonnenelevation des Tages aus dem HA-Recorder; leer wenn nicht lesbar."""
    host = os.getenv("UMBREL_HOST", "")
    token = os.getenv("HA_TOKEN", "")
    if not host or not token:
        return []
    start = datetime.combine(day, time.min).replace(tzinfo=timezone.utc)
    readings = fetch_history(
        start,
        start + timedelta(days=1),
        [SUN_ENTITY],
        _ha_url(host, os.getenv("HA_PORT", "8123")),
        token,
    )
    return readings.get(SUN_ENTITY, [])


def _section_quality(conn: sqlite3.Connection, day: date) -> str:
    start, end = _day_bounds(day)
    rows = conn.execute(
        "SELECT quality, missing_signals_json FROM energy_states "
        "WHERE block_id >= ? AND block_id < ?",
        (start, end),
    ).fetchall()
    n = len(rows)

    lines = ["## Datenqualitaet", ""]
    if n == 0:
        lines += [
            "**Keine Bloecke fuer diesen Tag in der DB.** Alles Weitere entfaellt.",
            "",
        ]
        return "\n".join(lines)

    counts: dict[str, int] = {}
    missing_counts: dict[str, int] = {}
    for quality, missing_json in rows:
        counts[quality] = counts.get(quality, 0) + 1
        for field in (missing_json or "[]").strip("[]").replace('"', "").split(","):
            field = field.strip()
            if field:
                missing_counts[field] = missing_counts.get(field, 0) + 1

    coverage = n / BLOCKS_PER_DAY * 100
    lines.append(
        f"- Bloecke: **{n} von {BLOCKS_PER_DAY}** ({coverage:.1f} % Abdeckung)"
    )
    lines.append(
        "- quality: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    )
    if missing_counts:
        lines.append(
            "- fehlende Signale: "
            + ", ".join(
                f"`{k}` in {v} Bloecken" for k, v in sorted(missing_counts.items())
            )
        )
    else:
        lines.append("- fehlende Signale: keine")
    if coverage < 99.0:
        lines.append("")
        lines.append(
            "> **Achtung:** Der Tag ist unvollstaendig. Zahlen unten sind Teilsummen, "
            "keine Tagessummen. `make sync-history` schliesst Luecken aus dem "
            "HA-Recorder nach."
        )
    lines.append("")
    return "\n".join(lines)


def _section_sun(day: date, sun: list[tuple[datetime, float | None]]) -> str:
    lines = ["## Tagesanker (Sonnenstand)", ""]
    valid = [(ts, v) for ts, v in sun if v is not None]
    if not valid:
        lines += [
            "Keine Elevationsdaten abrufbar (HA nicht erreichbar oder Zeitraum "
            "ausserhalb der Recorder-Aufbewahrung). Der Tag ist unten nur nach "
            "Uhrzeit gegliedert.",
            "",
        ]
        return "\n".join(lines)

    peak_ts, peak_val = max(valid, key=lambda x: x[1] or -90.0)
    above = [ts for ts, v in valid if (v or -90.0) > 0]
    lines.append(f"- Hoechststand: **{peak_val:.1f} Grad** um {peak_ts:%H:%M} UTC")
    if above:
        lines.append(
            f"- Sonne ueber dem Horizont: {min(above):%H:%M} bis {max(above):%H:%M} UTC"
        )
    lines.append("")
    return "\n".join(lines)


def _section_energy(conn: sqlite3.Connection, day: date) -> str:
    start, end = _day_bounds(day)
    row = conn.execute(
        "SELECT SUM(pv_power_w), SUM(house_load_w), SUM(grid_import_w), "
        "SUM(grid_export_w), SUM(miner_power_w), SUM(heizstab_power_w), "
        "MAX(pv_power_w) FROM energy_states WHERE block_id >= ? AND block_id < ?",
        (start, end),
    ).fetchone()
    peak_row = conn.execute(
        "SELECT block_id, pv_power_w FROM energy_states "
        "WHERE block_id >= ? AND block_id < ? ORDER BY pv_power_w DESC LIMIT 1",
        (start, end),
    ).fetchone()

    lines = ["## Energie", "", "| Groesse | Wert |", "|---|---|"]
    labels = (
        ("PV-Ertrag", 0),
        ("Hausverbrauch", 1),
        ("Netzbezug", 2),
        ("Einspeisung", 3),
        ("Mining", 4),
        ("Heizstab (PV-Anteil)", 5),
    )
    for label, idx in labels:
        lines.append(f"| {label} | {_fmt(_kwh_from_w(row[idx]), 2, ' kWh')} |")
    if peak_row:
        lines.append(
            f"| PV-Spitze | {_fmt(peak_row[1], 0, ' W')} um {peak_row[0][11:16]} UTC |"
        )
    lines.append("")
    return "\n".join(lines)


def _section_bitcoin(conn: sqlite3.Connection, day: date) -> str:
    """
    Sats-Ertrag des Tages, aus bitcoin_daily_settlement + der daraus in
    daily_kpi berechneten energy_to_sats-Kennzahl (siehe daily_kpi.py).
    Fehlt die Abrechnung (Sync nicht gelaufen, F2Pool-Ausfall), sagt der
    Bericht das explizit statt eine Zeile mit Nullen zu zeigen.
    """
    settlement = conn.execute(
        "SELECT earned_btc, pool_ths_avg, source FROM bitcoin_daily_settlement"
        " WHERE day = ?",
        (day.isoformat(),),
    ).fetchone()

    lines = ["## Bitcoin", ""]
    if settlement is None:
        lines.append(
            "Keine F2Pool-Abrechnungsdaten fuer diesen Tag (bitcoin_daily_settlement leer)."
        )
        lines.append("")
        return "\n".join(lines)

    earned_btc, pool_ths_avg, source = settlement
    kpi_row = conn.execute(
        "SELECT energy_to_sats FROM daily_kpi WHERE day = ?", (day.isoformat(),)
    ).fetchone()
    energy_to_sats = kpi_row[0] if kpi_row else None
    sats = round(earned_btc * 1e8)

    lines.append("| Groesse | Wert |")
    lines.append("|---|---|")
    lines.append(f"| Verdiente Sats | {sats:,} sats |".replace(",", "."))
    lines.append(f"| Verdiente BTC | {earned_btc:.8f} BTC |")
    lines.append(f"| Sats pro kWh | {_fmt(energy_to_sats, 2, ' sats/kWh')} |")
    if pool_ths_avg is not None:
        lines.append(f"| Pool-Hashrate (Tagesschnitt) | {pool_ths_avg:.1f} TH/s |")
    lines.append(f"| Quelle | {source} |")
    lines.append("")
    return "\n".join(lines)


def _section_soc(conn: sqlite3.Connection, day: date) -> str:
    start, end = _day_bounds(day)
    rows = conn.execute(
        "SELECT battery_soc_pct FROM energy_states "
        "WHERE block_id >= ? AND block_id < ? AND battery_soc_pct IS NOT NULL",
        (start, end),
    ).fetchall()
    lines = ["## Batterie und SoC-Baender", ""]
    if not rows:
        return "\n".join(lines + ["Keine SoC-Daten.", ""])

    socs = [r[0] for r in rows]
    lines.append(
        f"- Spanne: {min(socs):.0f} bis {max(socs):.0f} %, "
        f"Mittel {sum(socs) / len(socs):.1f} %"
    )
    lines.append("")
    lines.append("| Band | Bloecke | Anteil | Stunden |")
    lines.append("|---|---|---|---|")
    for label, low, high in SOC_BANDS:
        n = sum(1 for s in socs if low <= s < high)
        lines.append(
            f"| {label} | {n} | {n / len(socs) * 100:.1f} % | "
            f"{n * BLOCK_MINUTES / 60:.1f} h |"
        )
    lines.append("")
    return "\n".join(lines)


def _section_miners(conn: sqlite3.Connection, day: date) -> str:
    start, end = _day_bounds(day)
    miners = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT miner FROM miner_states "
            "WHERE block_id >= ? AND block_id < ? ORDER BY miner",
            (start, end),
        ).fetchall()
    ]
    lines = ["## Miner", ""]
    if not miners:
        return "\n".join(lines + ["Keine Miner-Daten fuer diesen Tag.", ""])

    lines.append("### Betriebsmodus (gemeldet)")
    lines.append("")
    lines.append("| Miner | Modus | Stunden |")
    lines.append("|---|---|---|")
    for miner in miners:
        for mode, n in conn.execute(
            "SELECT workmode_status, COUNT(*) FROM miner_states "
            "WHERE miner = ? AND block_id >= ? AND block_id < ? "
            "AND workmode_status IS NOT NULL "
            "GROUP BY workmode_status ORDER BY COUNT(*) DESC",
            (miner, start, end),
        ).fetchall():
            lines.append(f"| {miner} | {mode} | {n * BLOCK_MINUTES / 60:.1f} h |")
    lines.append("")

    lines.append("### Schaltfehler (befohlen != gemeldet)")
    lines.append("")
    deviations = conn.execute(
        "SELECT miner, block_id, workmode_set, workmode_status FROM miner_states "
        "WHERE block_id >= ? AND block_id < ? AND workmode_set IS NOT NULL "
        "AND workmode_status IS NOT NULL AND workmode_set != workmode_status "
        "ORDER BY block_id",
        (start, end),
    ).fetchall()
    if deviations:
        lines.append("| Zeit (UTC) | Miner | befohlen | gemeldet |")
        lines.append("|---|---|---|---|")
        for miner, block_id, cmd, status in deviations:
            lines.append(f"| {block_id[11:16]} | {miner} | {cmd} | {status} |")
    else:
        lines.append("Keine. Jeder Schaltbefehl wurde vom Geraet bestaetigt.")
    lines.append("")

    lines.append("### Temperatur")
    lines.append("")
    lines.append(
        "| Miner | max Einzelchip (tmax) | Spreizung tmax-Board | Bloecke >=110 C |"
    )
    lines.append("|---|---|---|---|")
    for miner in miners:
        row = conn.execute(
            "SELECT MAX(tmax_c), AVG(tmax_c - hbotemp_c), "
            "SUM(CASE WHEN tmax_c >= ? THEN 1 ELSE 0 END) "
            "FROM miner_states WHERE miner = ? AND block_id >= ? AND block_id < ? "
            "AND ths > 0",
            (TEMP_CRIT_C, miner, start, end),
        ).fetchone()
        lines.append(
            f"| {miner} | {_fmt(row[0], 0, ' C')} | {_fmt(row[1], 1, ' K')} | "
            f"{row[2] or 0} |"
        )
    lines.append("")
    lines.append(
        "> Spreizung = heissester Einzelchip minus Board-Ausgangstemperatur. "
        "Eine hohe Spreizung bei normaler Board-Temperatur deutet auf einen "
        "einzelnen Chip, nicht auf zu schwache Kuehlung des ganzen Geraets."
    )
    lines.append("")

    lines.append("### Effizienz je Modus")
    lines.append("")
    lines.append(
        "| Miner | Modus | Bloecke | TH/s | W gemessen | W/TH | W Typenschild |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for miner in miners:
        # power_w ist die Messung am Shelly, mode_power_w die Herstellerangabe
        # der Stufe. Auf die Messung wird gerechnet: das Geraet zieht rund 8 %
        # mehr, und genau diese Differenz entscheidet ueber die Grenzeffizienz.
        for mode, n, ths, watt, nominal in conn.execute(
            "SELECT workmode_status, COUNT(*), AVG(ths), AVG(power_w),"
            " AVG(mode_power_w) "
            "FROM miner_states WHERE miner = ? AND block_id >= ? AND block_id < ? "
            "AND ths > 0 AND power_w > 0 "
            "GROUP BY workmode_status ORDER BY AVG(power_w)",
            (miner, start, end),
        ).fetchall():
            wpt = watt / ths if ths else None
            lines.append(
                f"| {miner} | {mode} | {n} | {_fmt(ths, 1)} | {_fmt(watt, 0)} | "
                f"{_fmt(wpt, 2)} | {_fmt(nominal, 0)} |"
            )
    lines.append("")
    lines.append(
        "> Gerechnet wird auf **W gemessen** (Shelly). Das Typenschild steht nur "
        "zum Vergleich daneben und liegt rund 8 Prozent darunter. W/TH ist der "
        "Durchschnitt der Stufe, nicht der Grenzwert des Wechsels. Ob sich der "
        "Schritt Standard nach Super lohnt, entscheidet die Grenzeffizienz "
        "(Mehrverbrauch geteilt durch Mehrleistung), nicht dieser Mittelwert."
    )
    lines.append("")
    return "\n".join(lines)


def _section_flags(conn: sqlite3.Connection, day: date) -> str:
    """Rein regelbasierte Auffaelligkeiten. Keine Deutung, nur Schwellen."""
    start, end = _day_bounds(day)
    flags: list[str] = []

    crit = conn.execute(
        "SELECT COUNT(*) FROM energy_states WHERE block_id >= ? AND block_id < ? "
        "AND miner_temp_c >= ? AND miner_temp_c < ?",
        (start, end, TEMP_CRIT_C, TEMP_MISSING_C),
    ).fetchone()[0]
    if crit:
        flags.append(
            f"{crit} Bloecke mit Chiptemperatur >= {TEMP_CRIT_C:.0f} C "
            f"({crit * BLOCK_MINUTES} Minuten im roten Bereich)."
        )

    dev = conn.execute(
        "SELECT COUNT(*) FROM miner_states WHERE block_id >= ? AND block_id < ? "
        "AND workmode_set IS NOT NULL AND workmode_status IS NOT NULL "
        "AND workmode_set != workmode_status",
        (start, end),
    ).fetchone()[0]
    if dev:
        flags.append(
            f"{dev} Bloecke, in denen ein Miner den befohlenen Modus nicht meldete."
        )

    missing_blocks = (
        BLOCKS_PER_DAY
        - conn.execute(
            "SELECT COUNT(*) FROM energy_states WHERE block_id >= ? AND block_id < ?",
            (start, end),
        ).fetchone()[0]
    )
    if missing_blocks > 0:
        flags.append(f"{missing_blocks} Bloecke fehlen in der DB.")

    surplus_idle = conn.execute(
        "SELECT COUNT(*) FROM energy_states WHERE block_id >= ? AND block_id < ? "
        "AND grid_export_w > 1000 AND (miner_power_w IS NULL OR miner_power_w < 100)",
        (start, end),
    ).fetchone()[0]
    if surplus_idle:
        flags.append(
            f"{surplus_idle} Bloecke mit Einspeisung > 1000 W bei stehendem Miner "
            f"({surplus_idle * BLOCK_MINUTES / 60:.1f} h ungenutzter Ueberschuss)."
        )

    lines = ["## Auffaelligkeiten (regelbasiert)", ""]
    if flags:
        lines += [f"- {f}" for f in flags]
    else:
        lines.append("- Keine der geprueften Schwellen wurde ueberschritten.")
    lines.append("")
    return "\n".join(lines)


def build_report(conn: sqlite3.Connection, day: date, sun: list[Any]) -> str:
    header = [
        "---",
        f"datum: {day.isoformat()}",
        "typ: fakten",
        "quelle: data/bitgrid.db",
        "erzeugt_von: src/data/daily_report.py",
        "---",
        "",
        f"# Fakten {day.isoformat()}",
        "",
        "Deterministisch erzeugt, ohne Sprachmodell. Jede Zahl ist durch erneutes",
        "Ausfuehren des Generators reproduzierbar. Deutungen gehoeren in die",
        f"Datei `{day.isoformat()}_hypothesen.md`, nicht hierher.",
        "",
    ]
    parts = [
        "\n".join(header),
        _section_quality(conn, day),
        _section_sun(day, sun),
        _section_energy(conn, day),
        _section_bitcoin(conn, day),
        _section_soc(conn, day),
        _section_miners(conn, day),
        _section_flags(conn, day),
    ]
    return "\n".join(parts)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministischer Tagesbericht")
    parser.add_argument(
        "--date", default=None, help="Tag (YYYY-MM-DD), default: gestern"
    )
    parser.add_argument("--db", default="data/bitgrid.db")
    parser.add_argument("--out", default=None, help="Zieldatei (default: stdout)")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

    args = _parse_args()
    day = (
        date.fromisoformat(args.date)
        if args.date
        else (datetime.now(timezone.utc) - timedelta(days=1)).date()
    )

    conn = get_connection(args.db)
    try:
        text = build_report(conn, day, _fetch_sun(day))
    finally:
        conn.close()

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"Geschrieben: {path}")
    else:
        print(text)


if __name__ == "__main__":
    main()
