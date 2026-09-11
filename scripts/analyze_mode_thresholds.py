"""
analyze_mode_thresholds.py — Read-only Analyse der Miner-Schaltschwellen (Eco/Standard/Super).

Zweck: Grundlage fuer den Schwellenwert-Vorschlag in
docs/architecture/09_design_decisions/092_soc_saison_schwellen_vorschlag_de.md.
Wertet aus, wie oft die Live-Schaltung (mvp_auto.yaml) tatsaechlich wechselt,
wie viel Ueberschuss der pauschale Nachmittags-Cap kappt, wie haeufig Super
direkt (ohne Standard-Zwischenschritt) auf Eco kollabiert, und wie viel
Naechtliche Grundlast die aktuelle Stop-Schwelle ueber das Minimum hinaus deckt.

Strikt read-only, nie Schreibzugriff auf data/bitgrid.db.

Verwendung:
    python scripts/analyze_mode_thresholds.py
    python scripts/analyze_mode_thresholds.py --db data/bitgrid.db --out report.md
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

# Standort-Defaults wie src/adapters/solar_forecast.py (FORECAST_LAT/FORECAST_LON).
LAT_DEG = 48.1
LON_DEG = 11.6

# Aktuelle Live-Schwellen aus src/ha/config/packages/mvp_auto.yaml (Stand dieser
# Session, vom Nutzer-Dashboard-Screenshot bestaetigt).
STOP_PCT = 60.0
ECO_PCT = 70.0
STD_PCT = 85.0
STD_COLLAPSE_PCT = 83.0  # soc_std_on - 2, siehe mvp_auto.yaml Z.321
SUPER_PCT = 100.0

# Batterie: nutzbare Kapazitaet am Wechselrichterausgang, gemessen (Kommentar
# mvp_auto.yaml Z.75-86), nicht die Nennkapazitaet.
BATTERY_USABLE_KWH = 12.5

# Kandidaten fuer eine eigene soc_super_off-Schwelle (Sensitivitaets-Sweep).
SUPER_OFF_CANDIDATES = [88.0, 90.0, 92.0, 95.0]

# Kandidaten fuer eine angehobene Winter-Stop-Schwelle (Autarkie-Vorrang).
WINTER_STOP_CANDIDATES = [60.0, 65.0, 68.0, 70.0]

# Flap-Back-Fenster: A->B->A gilt als Flap-Back, wenn B <= 6 Bloecke (60 Min) dauert.
FLAP_BACK_MAX_BLOCKS = 6
BLOCK_MINUTES = 10

# Datensatz liegt komplett in CEST (Mai-Aug, keine Zeitumstellung im Fenster).
# Fuer eine Wiederholung im Winter (CET, UTC+1) muss dieser Offset angepasst werden.
UTC_TO_LOCAL_HOURS = 2


# ---------------------------------------------------------------------------
# Sonnenstand (NOAA-Algorithmus) — Kopie der reinen Funktion aus
# src/adapters/solar_forecast.py::solar_elevation_deg, damit dieses Skript wie
# alle anderen scripts/*.py ohne Abhaengigkeit vom src-Package laeuft. Gleiche
# Formel, keine eigenstaendige Herleitung — bei Aenderung dort auch hier pruefen.
# ---------------------------------------------------------------------------


def solar_elevation_deg(lat_deg: float, lon_deg: float, when_utc: datetime) -> float:
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=timezone.utc)
    when_utc = when_utc.astimezone(timezone.utc)

    day_of_year = when_utc.timetuple().tm_yday
    hour = when_utc.hour + when_utc.minute / 60.0 + when_utc.second / 3600.0
    gamma = 2.0 * math.pi / 365.0 * (day_of_year - 1 + (hour - 12.0) / 24.0)

    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2.0 * gamma)
        - 0.040849 * math.sin(2.0 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2.0 * gamma)
        + 0.000907 * math.sin(2.0 * gamma)
        - 0.002697 * math.cos(3.0 * gamma)
        + 0.001480 * math.sin(3.0 * gamma)
    )
    time_offset = eqtime + 4.0 * lon_deg
    true_solar_time = hour * 60.0 + time_offset
    hour_angle_deg = true_solar_time / 4.0 - 180.0

    lat_rad = math.radians(lat_deg)
    ha_rad = math.radians(hour_angle_deg)
    sin_elev = math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(
        decl
    ) * math.cos(ha_rad)
    sin_elev = max(-1.0, min(1.0, sin_elev))
    return math.degrees(math.asin(sin_elev))


def true_solar_noon_utc(day: date, lat_deg: float, lon_deg: float) -> datetime:
    """Uhrzeit (UTC) des Sonnenhoechststands an einem Tag, per Scan (2-Min-Schritte)."""
    start = datetime(day.year, day.month, day.day, 8, 0, tzinfo=timezone.utc)
    best_t, best_elev = start, -91.0
    for i in range(0, 8 * 60, 2):  # 08:00-16:00 UTC deckt Sonnenmittag in DE ganzjaehrig ab
        t = start + timedelta(minutes=i)
        elev = solar_elevation_deg(lat_deg, lon_deg, t)
        if elev > best_elev:
            best_elev, best_t = elev, t
    return best_t


# ---------------------------------------------------------------------------
# DB-Zugriff
# ---------------------------------------------------------------------------


def connect_ro(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise SystemExit(f"DB nicht gefunden: {db_path}")
    return sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)


def block_dt(block_id: str) -> datetime:
    """block_id ist ISO ohne Offset, repraesentiert aber UTC (siehe window_start)."""
    return datetime.fromisoformat(block_id).replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# 1) Modus-Effizienzprofil (reale Leistung/Hashrate je Modus)
# ---------------------------------------------------------------------------


@dataclass
class ModeProfile:
    miner: str
    modus: str
    bloecke: int
    ths_mittel: float
    watt_mittel: float
    w_pro_th: float


def mode_efficiency_profile(conn: sqlite3.Connection) -> list[ModeProfile]:
    rows = conn.execute(
        "SELECT miner, modus, bloecke, ths_mittel, watt_mittel, w_pro_th "
        "FROM v_modus_effizienz ORDER BY miner, watt_mittel"
    ).fetchall()
    return [ModeProfile(*r) for r in rows]


def combined_mode_power_ths(
    profiles: list[ModeProfile],
) -> dict[str, tuple[float, float]]:
    """Ueber beide Miner gemittelt (blockgewichtet): modus -> (watt, ths)."""
    acc: dict[str, list[float]] = {}
    for p in profiles:
        w_sum, th_sum, n_sum = acc.get(p.modus, [0.0, 0.0, 0.0])
        acc[p.modus] = [
            w_sum + p.watt_mittel * p.bloecke,
            th_sum + p.ths_mittel * p.bloecke,
            n_sum + p.bloecke,
        ]
    return {
        modus: (w / n, t / n) if n else (0.0, 0.0)
        for modus, (w, t, n) in acc.items()
    }


# ---------------------------------------------------------------------------
# 2) Moduswechsel & Flap-Backs (unabhaengige Neuberechnung)
# ---------------------------------------------------------------------------


@dataclass
class Segment:
    modus: str
    start_block: str
    n_blocks: int


@dataclass
class TransitionStats:
    miner: str
    segments: list[Segment]
    transitions: int
    flap_backs: int
    transitions_by_month: dict[str, int]
    super_exit_targets: dict[str, int]  # Super -> X : Anzahl
    super_exit_socs: list[float]


def _segments_for_miner(conn: sqlite3.Connection, miner: str) -> list[Segment]:
    rows = conn.execute(
        "SELECT block_id, workmode_status FROM miner_states "
        "WHERE miner = ? ORDER BY block_id",
        (miner,),
    ).fetchall()
    segments: list[Segment] = []
    for block_id, modus in rows:
        if segments and segments[-1].modus == modus:
            segments[-1].n_blocks += 1
        else:
            segments.append(Segment(modus, block_id, 1))
    return segments


def transition_stats(conn: sqlite3.Connection, miner: str) -> TransitionStats:
    segments = _segments_for_miner(conn, miner)
    transitions = max(0, len(segments) - 1)

    flap_backs = 0
    for i in range(len(segments) - 2):
        if (
            segments[i].modus == segments[i + 2].modus
            and segments[i + 1].n_blocks <= FLAP_BACK_MAX_BLOCKS
        ):
            flap_backs += 1

    by_month: dict[str, int] = {}
    for seg in segments[1:]:
        month = seg.start_block[:7]  # 'YYYY-MM'
        by_month[month] = by_month.get(month, 0) + 1

    super_exit_targets: dict[str, int] = {}
    super_exit_socs: list[float] = []
    soc_by_block = _soc_lookup(conn)
    for i in range(len(segments) - 1):
        if segments[i].modus == "Super":
            target = segments[i + 1].modus
            super_exit_targets[target] = super_exit_targets.get(target, 0) + 1
            soc = soc_by_block.get(segments[i + 1].start_block)
            if soc is not None:
                super_exit_socs.append(soc)

    return TransitionStats(
        miner=miner,
        segments=segments,
        transitions=transitions,
        flap_backs=flap_backs,
        transitions_by_month=by_month,
        super_exit_targets=super_exit_targets,
        super_exit_socs=super_exit_socs,
    )


_SOC_CACHE: dict[str, float] | None = None


def _soc_lookup(conn: sqlite3.Connection) -> dict[str, float]:
    global _SOC_CACHE
    if _SOC_CACHE is None:
        rows = conn.execute(
            "SELECT block_id, battery_soc_pct FROM energy_states "
            "WHERE quality = 'ok'"
        ).fetchall()
        _SOC_CACHE = {b: s for b, s in rows if s is not None}
    return _SOC_CACHE


def switch_mismatch_summary(conn: sqlite3.Connection) -> tuple[int, int]:
    """blocks_switch_mismatch/switch_mismatches messen workmode_set != workmode_status
    (Kommando vs. tatsaechlicher Zustand, z.B. Hardware-Verzoegerung) — das ist NICHT
    dasselbe wie Moduswechsel-Flapping und wird hier nur zur Einordnung mitgeliefert."""
    daily = conn.execute(
        "SELECT COALESCE(SUM(blocks_switch_mismatch), 0) FROM daily_kpi"
    ).fetchone()[0]
    per_miner = conn.execute(
        "SELECT COALESCE(SUM(switch_mismatches), 0) FROM daily_miner_kpi"
    ).fetchone()[0]
    return int(daily), int(per_miner)


# ---------------------------------------------------------------------------
# 3) Nachmittags-Cap-Quantifizierung
# ---------------------------------------------------------------------------


@dataclass
class AfternoonFinding:
    month: str
    blocks_after_noon: int
    blocks_capped_for_standard: int
    blocks_capped_for_super: int
    foregone_wh: float
    foregone_th_hours: float


def afternoon_cap_analysis(
    conn: sqlite3.Connection, mode_power_ths: dict[str, tuple[float, float]]
) -> list[AfternoonFinding]:
    """Blocke nach dem wahren Sonnenmittag, in denen realer Ueberschuss (PV-Haus)
    einen hoeheren Modus getragen haette, der Miner aber (mode_status) niedriger
    lief. Kontrafaktische Schaetzung auf Basis der REALISIERTEN SoC-Trajektorie,
    keine Batteriedynamik-Neusimulation."""
    rows = conn.execute(
        "SELECT es.block_id, es.pv_power_w, es.house_load_w, ms.workmode_status "
        "FROM energy_states es JOIN miner_states ms ON es.block_id = ms.block_id "
        "WHERE es.quality = 'ok' AND ms.miner = 'miner1' "
        "AND es.pv_power_w IS NOT NULL AND es.house_load_w IS NOT NULL"
    ).fetchall()

    watt_eco, ths_eco = mode_power_ths.get("Eco", (0.0, 0.0))
    watt_std, ths_std = mode_power_ths.get("Standard", (0.0, 0.0))
    watt_sup, ths_sup = mode_power_ths.get("Super", (0.0, 0.0))

    noon_cache: dict[date, datetime] = {}

    def is_after_noon(dt: datetime) -> bool:
        d = dt.date()
        if d not in noon_cache:
            noon_cache[d] = true_solar_noon_utc(d, LAT_DEG, LON_DEG)
        return dt >= noon_cache[d]

    by_month: dict[str, list[float]] = {}
    for block_id, pv, house, modus in rows:
        dt = block_dt(block_id)
        if not is_after_noon(dt):
            continue
        month = block_id[:7]
        acc = by_month.setdefault(month, [0, 0, 0, 0.0, 0.0])
        acc[0] += 1
        surplus = pv - house
        block_h = BLOCK_MINUTES / 60.0

        capped_for_std = surplus >= watt_std and modus in ("Eco", "Standby")
        capped_for_sup = surplus >= watt_sup and modus in ("Eco", "Standard", "Standby")
        if capped_for_std:
            acc[1] += 1
        if capped_for_sup:
            acc[2] += 1

        if capped_for_sup:
            watt_actual, ths_actual = mode_power_ths.get(modus, (0.0, 0.0))
            acc[3] += (watt_sup - watt_actual) * block_h
            acc[4] += (ths_sup - ths_actual) * block_h
        elif capped_for_std:
            watt_actual, ths_actual = mode_power_ths.get(modus, (0.0, 0.0))
            acc[3] += (watt_std - watt_actual) * block_h
            acc[4] += (ths_std - ths_actual) * block_h

    findings = []
    for month in sorted(by_month):
        n, cap_std, cap_sup, wh, thh = by_month[month]
        findings.append(
            AfternoonFinding(month, int(n), int(cap_std), int(cap_sup), wh, thh)
        )
    return findings


# ---------------------------------------------------------------------------
# 4) Sensitivitaets-Sweep fuer eine eigene soc_super_off-Schwelle
# ---------------------------------------------------------------------------


def super_off_sweep(
    conn: sqlite3.Connection, mode_power_ths: dict[str, tuple[float, float]]
) -> dict[float, float]:
    """Fuer jeden Kandidatenwert C: wie viele TH-Stunden haette Miner1 zusaetzlich
    im Standard-Band verbracht, waere Super statt direkt auf Eco erst auf Standard
    gefallen (und Standard haette wie heute erst bei STD_COLLAPSE_PCT weiter auf Eco
    gewechselt)? Basiert auf der REALISIERTEN SoC-Kurve nach jedem Super-Austritt."""
    soc = _soc_lookup(conn)
    segments = _segments_for_miner(conn, "miner1")
    watt_std, ths_std = mode_power_ths.get("Standard", (0.0, 0.0))
    watt_eco, ths_eco = mode_power_ths.get("Eco", (0.0, 0.0))
    block_h = BLOCK_MINUTES / 60.0

    # Alle Bloecke chronologisch mit SoC, um nach jedem Super-Austritt vorwaerts
    # zu laufen, bis SoC unter STD_COLLAPSE_PCT faellt.
    all_blocks = conn.execute(
        "SELECT block_id FROM miner_states WHERE miner = 'miner1' ORDER BY block_id"
    ).fetchall()
    block_index = {b[0]: i for i, b in enumerate(all_blocks)}
    ordered_ids = [b[0] for b in all_blocks]

    results: dict[float, float] = {}
    for candidate in SUPER_OFF_CANDIDATES:
        gained_th_hours = 0.0
        for i, seg in enumerate(segments):
            if seg.modus != "Super" or i + 1 >= len(segments):
                continue
            exit_block = segments[i + 1].start_block
            idx = block_index.get(exit_block)
            if idx is None:
                continue
            exit_soc = soc.get(exit_block)
            if exit_soc is None or exit_soc >= candidate:
                continue  # Kandidat waere noch nicht unterschritten -> bliebe in Super
            # Ab hier laeuft der Block heute in Eco; zaehle, wie viele Folgebloecke
            # SoC >= STD_COLLAPSE_PCT haben (die haetten unter dem Fix in Standard
            # verbracht werden koennen) bis SoC darunter faellt oder der naechste
            # echte Segmentwechsel kommt.
            j = idx
            while j < len(ordered_ids):
                bid = ordered_ids[j]
                s = soc.get(bid)
                if s is None or s < STD_COLLAPSE_PCT:
                    break
                gained_th_hours += (ths_std - ths_eco) * block_h
                j += 1
        results[candidate] = gained_th_hours
    return results


# ---------------------------------------------------------------------------
# 5) Monatstrend PV-Ueberschuss (empirischer Anker fuer Saison-Extrapolation)
# ---------------------------------------------------------------------------


@dataclass
class MonthlySurplus:
    month: str
    days: int
    hours_ge_standard: float  # /Tag
    hours_ge_super: float  # /Tag


def monthly_surplus_trend(
    conn: sqlite3.Connection, mode_power_ths: dict[str, tuple[float, float]]
) -> list[MonthlySurplus]:
    watt_std, _ = mode_power_ths.get("Standard", (0.0, 0.0))
    watt_sup, _ = mode_power_ths.get("Super", (0.0, 0.0))
    rows = conn.execute(
        "SELECT block_id, pv_power_w, house_load_w FROM energy_states "
        "WHERE quality = 'ok' AND pv_power_w IS NOT NULL AND house_load_w IS NOT NULL"
    ).fetchall()

    by_month: dict[str, dict] = {}
    for block_id, pv, house in rows:
        month = block_id[:7]
        d = block_id[:10]
        acc = by_month.setdefault(month, {"days": set(), "std_blocks": 0, "sup_blocks": 0})
        acc["days"].add(d)
        surplus = pv - house
        if surplus >= watt_std:
            acc["std_blocks"] += 1
        if surplus >= watt_sup:
            acc["sup_blocks"] += 1

    out = []
    for month in sorted(by_month):
        acc = by_month[month]
        n_days = len(acc["days"]) or 1
        out.append(
            MonthlySurplus(
                month=month,
                days=n_days,
                hours_ge_standard=acc["std_blocks"] * BLOCK_MINUTES / 60.0 / n_days,
                hours_ge_super=acc["sup_blocks"] * BLOCK_MINUTES / 60.0 / n_days,
            )
        )
    return out


# ---------------------------------------------------------------------------
# 6) Naechtliche Grundlast + Batteriepuffer-Rechnung
# ---------------------------------------------------------------------------


@dataclass
class NightBaseline:
    mean_w: float
    median_w: float
    n_blocks: int


def night_baseline(conn: sqlite3.Connection) -> NightBaseline:
    """22-06 Uhr lokal = 20-04 Uhr UTC (CEST, siehe UTC_TO_LOCAL_HOURS)."""
    rows = conn.execute(
        "SELECT house_load_w, window_start FROM energy_states WHERE quality = 'ok'"
    ).fetchall()
    loads = []
    for house_w, window_start in rows:
        if house_w is None:
            continue
        dt = datetime.fromisoformat(window_start)
        hour = dt.hour
        if hour >= 20 or hour < 4:
            loads.append(house_w)
    loads.sort()
    n = len(loads)
    mean_w = sum(loads) / n if n else 0.0
    median_w = loads[n // 2] if n else 0.0
    return NightBaseline(mean_w=mean_w, median_w=median_w, n_blocks=n)


def stop_threshold_night_hours(stop_pct: float, night_load_w: float) -> float:
    """Wie viele Stunden Grundlast deckt die Kapazitaet OBERHALB von stop_pct?"""
    usable_kwh_above_stop = BATTERY_USABLE_KWH * (100.0 - stop_pct) / 100.0
    if night_load_w <= 0:
        return 0.0
    return usable_kwh_above_stop * 1000.0 / night_load_w


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def build_report(db_path: Path) -> str:
    conn = connect_ro(db_path)
    lines: list[str] = []
    try:
        lines.append("# Analyse: Miner-Schaltschwellen (Eco/Standard/Super)")
        lines.append("")
        lines.append(f"- DB: `{db_path}`")
        lines.append(f"- Erzeugt: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
        lines.append("")

        # 1) Modus-Effizienzprofil
        profiles = mode_efficiency_profile(conn)
        mode_power_ths = combined_mode_power_ths(profiles)
        lines.append("## 1) Modus-Effizienzprofil (real gemessen, `v_modus_effizienz`)")
        lines.append("")
        lines.append("| Miner | Modus | Blöcke | TH/s Ø | Watt Ø | W/TH |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for p in profiles:
            lines.append(
                f"| {p.miner} | {p.modus} | {p.bloecke} | {p.ths_mittel:.1f} | "
                f"{p.watt_mittel:.0f} | {p.w_pro_th:.1f} |"
            )
        lines.append("")
        lines.append(
            "Kombiniert (blockgewichtet über beide Miner), Basis für alle "
            "Wh/TH-h-Schätzungen unten:"
        )
        for modus, (w, t) in sorted(mode_power_ths.items(), key=lambda kv: kv[1][0]):
            lines.append(f"- **{modus}**: {w:.0f} W, {t:.1f} TH/s")
        lines.append("")

        # 2) Moduswechsel & Flap-Backs
        lines.append("## 2) Moduswechsel & Flap-Backs (unabhängige Neuberechnung)")
        lines.append("")
        daily_mismatch, miner_mismatch = switch_mismatch_summary(conn)
        for miner in ("miner1", "miner2"):
            ts = transition_stats(conn, miner)
            lines.append(f"### {miner}")
            lines.append(f"- Gesamt-Wechsel: **{ts.transitions}**")
            lines.append(
                f"- Flap-Backs (A→B→A, B ≤ {FLAP_BACK_MAX_BLOCKS * BLOCK_MINUTES} Min.): "
                f"**{ts.flap_backs}**"
            )
            lines.append(
                "- Wechsel/Monat: "
                + ", ".join(f"{m}: {n}" for m, n in sorted(ts.transitions_by_month.items()))
            )
            lines.append(
                f"- Super-Austritte nach Ziel-Modus: {ts.super_exit_targets} "
                f"(SoC bei Austritt: Ø {sum(ts.super_exit_socs)/len(ts.super_exit_socs):.1f}%, "
                f"n={len(ts.super_exit_socs)})"
                if ts.super_exit_socs
                else "- Keine Super-Austritte im Datensatz"
            )
            lines.append("")
        lines.append(
            f"**Zur Einordnung** (andere Kennzahl, kein Flapping-Maß): "
            f"`blocks_switch_mismatch` (daily_kpi) Summe = {daily_mismatch}, "
            f"`switch_mismatches` (daily_miner_kpi) Summe = {miner_mismatch}. "
            f"Das misst `workmode_set != workmode_status` (Kommando vs. tatsächlicher "
            f"Hardware-Zustand, z.B. Verzögerung), NICHT Moduswechsel-Flapping — "
            f"nicht verwechseln."
        )
        lines.append("")

        # 3) Nachmittags-Cap
        lines.append("## 3) Nachmittags-Cap: verschenkter Überschuss nach Sonnenmittag")
        lines.append("")
        lines.append(
            "Blöcke nach dem wahren (astronomischen) Sonnenmittag, in denen "
            "`pv_power_w - house_load_w` einen höheren Modus getragen hätte, als "
            "Miner 1 tatsächlich lief (`workmode_status`)."
        )
        lines.append("")
        lines.append(
            "| Monat | Blöcke nach Mittag | ...mit Std-Überschuss, gekappt | "
            "...mit Super-Überschuss, gekappt | Verschenkt Wh | Verschenkt TH-h |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|")
        total_wh, total_thh = 0.0, 0.0
        for f in afternoon_cap_analysis(conn, mode_power_ths):
            total_wh += f.foregone_wh
            total_thh += f.foregone_th_hours
            lines.append(
                f"| {f.month} | {f.blocks_after_noon} | {f.blocks_capped_for_standard} | "
                f"{f.blocks_capped_for_super} | {f.foregone_wh:,.0f} | {f.foregone_th_hours:.1f} |"
            )
        lines.append(f"| **Summe** | | | | **{total_wh:,.0f}** | **{total_thh:.1f}** |")
        lines.append("")
        lines.append(
            "Kontrafaktische Schätzung auf Basis der realisierten SoC-Trajektorie "
            "(keine Batteriedynamik-Neusimulation) — Miner 1 only, da Miner 2 keine "
            "Super-Stufe hat."
        )
        lines.append("")

        # 4) Sensitivitaets-Sweep
        lines.append("## 4) Sensitivitäts-Sweep: eigene `soc_super_off`-Schwelle")
        lines.append("")
        lines.append(
            "Zusätzliche Standard-Stunden (in TH-h), wenn Super beim Runterschalten "
            "erst auf Standard fiele (statt direkt auf Eco), solange SoC über dem "
            f"Kandidatenwert bleibt, danach wie heute weiter bis {STD_COLLAPSE_PCT}% "
            "(bestehende P3.5-Schwelle):"
        )
        lines.append("")
        lines.append("| Kandidat (%) | Gewonnene TH-h (Miner 1, ganzer Zeitraum) |")
        lines.append("|---:|---:|")
        for candidate, gained in super_off_sweep(conn, mode_power_ths).items():
            lines.append(f"| {candidate:.0f} | {gained:.1f} |")
        lines.append("")

        # 5) Monatstrend
        lines.append("## 5) Monatstrend: Stunden/Tag mit ausreichend Überschuss")
        lines.append("")
        lines.append("| Monat | Tage | Std-Stunden/Tag (Ø) | Super-Stunden/Tag (Ø) |")
        lines.append("|---|---:|---:|---:|")
        for m in monthly_surplus_trend(conn, mode_power_ths):
            lines.append(
                f"| {m.month} | {m.days} | {m.hours_ge_standard:.2f} | {m.hours_ge_super:.2f} |"
            )
        lines.append("")
        lines.append(
            "Empirischer Anker für die Herbst/Winter/Frühling-Extrapolation über das "
            "Tageslängen-Verhältnis (Juni fehlt in der DB, Mai nur Teilmonat ab 25.05.)."
        )
        lines.append("")

        # 6) Grundlast + Batteriepuffer
        lines.append("## 6) Nächtliche Grundlast & Batteriepuffer")
        lines.append("")
        nb = night_baseline(conn)
        lines.append(
            f"- Grundlast 22-06 Uhr lokal (angenommen UTC+{UTC_TO_LOCAL_HOURS}, CEST): "
            f"Ø {nb.mean_w:.0f} W, Median {nb.median_w:.0f} W (n={nb.n_blocks} Blöcke)"
        )
        lines.append(f"- Nutzbare Akkukapazität: {BATTERY_USABLE_KWH} kWh")
        lines.append("")
        lines.append("| Stop-Schwelle | Reserve über Grundlast (Stunden) |")
        lines.append("|---:|---:|")
        for stop_pct in WINTER_STOP_CANDIDATES:
            hours = stop_threshold_night_hours(stop_pct, nb.mean_w)
            lines.append(f"| {stop_pct:.0f}% | {hours:.1f} h |")
        lines.append("")
        lines.append(
            "Rechengrundlage für die Winter-Stop-Schwelle: wie viele Stunden "
            "Grundlast deckt die Kapazität oberhalb der Schwelle bei aktueller "
            "(Sommer-)Grundlast — im Winter ggf. höher, siehe Vorschlagsdokument."
        )

    finally:
        conn.close()

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only Analyse der Miner-Schaltschwellen gegen data/bitgrid.db"
    )
    parser.add_argument("--db", default="data/bitgrid.db", help="Pfad zu bitgrid.db")
    parser.add_argument(
        "--out", default="", help="optionaler Pfad für einen Markdown-Report (sonst stdout)"
    )
    args = parser.parse_args()

    report = build_report(Path(args.db))
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"Report geschrieben: {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
