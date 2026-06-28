"""
ha_recorder_audit.py — Read-only Audit des Home-Assistant-Recorders.

Zweck: vor dem Einsatz des DEV-BitHamster pruefen, ob alle Signale, die fuer die
Solar-Mining-Analyse gebraucht werden (PV, Verbrauch, Netz, Speicher/SoC, Miner,
Wetter, Sonnenstand, Einstrahlung/Prognose, Entscheidungen), sauber aufgezeichnet
sind: Vorhandensein, Zeitraum, Sampling-Dichte und Tages-Luecken.

Strikt read-only. Es wird nie geschrieben. Empfehlung: gegen einen Snapshot laufen
lassen, nicht gegen die Live-DB:
    sqlite3 home-assistant_v2.db ".backup snapshot.db"

Verwendung:
    python scripts/ha_recorder_audit.py --db path/to/home-assistant_v2.db
    python scripts/ha_recorder_audit.py --db snapshot.db --out audit_report.md
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Feature-Gruppen fuer das Analyse-Ziel (Substring-Match auf entity_id, lowercase).
FEATURE_GROUPS: dict[str, list[str]] = {
    "PV-Erzeugung": ["pv", "solar", "inverter", "erzeug"],
    "Hausverbrauch": ["house", "load", "verbrauch", "consumption"],
    "Netz (Bezug/Einspeisung)": ["grid", "netz", "import", "export", "einspeis"],
    "Speicher (SoC/Leistung)": ["soc", "battery", "batt", "speicher", "akku"],
    "Miner": ["miner", "mining", "avalon", "hashrate", "hash_rate", "chip", "asic"],
    "Wetter": ["weather", "outdoor", "aussen", "cloud", "wolke", "humidity", "rain", "regen"],
    "Sonnenstand": ["sun", "sonne", "elevation", "azimuth", "azimut"],
    "Einstrahlung/Prognose": ["forecast", "prognose", "irradiance", "ghi", "radiation", "einstrahl"],
    "Entscheidungen/Baender": ["bg_decision", "decision", "rule_", "band", "_mode", "autonomy"],
}

_SECONDS_PER_DAY = 86400.0


@dataclass
class EntityStat:
    entity_id: str
    count: int
    first: datetime | None
    last: datetime | None
    days_with_data: int = 0

    @property
    def span_days(self) -> float:
        if self.first is None or self.last is None:
            return 0.0
        return (self.last - self.first).total_seconds() / _SECONDS_PER_DAY

    @property
    def coverage_pct(self) -> float:
        span = self.span_days
        if span < 1.0:
            return 100.0 if self.count > 0 else 0.0
        return min(100.0, 100.0 * self.days_with_data / (span + 1.0))

    @property
    def avg_interval_min(self) -> float:
        if self.count < 2 or self.span_days <= 0:
            return 0.0
        return self.span_days * 24 * 60 / (self.count - 1)


@dataclass
class GroupResult:
    name: str
    entities: list[EntityStat] = field(default_factory=list)

    @property
    def present(self) -> bool:
        return any(e.count > 0 for e in self.entities)


def _connect_ro(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise SystemExit(f"DB nicht gefunden: {db_path}")
    uri = f"file:{db_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _ts_to_dt(value: object) -> datetime | None:
    """Recorder speichert epoch-Sekunden (modern) oder ISO-Text (legacy)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _collect_modern(conn: sqlite3.Connection) -> list[EntityStat]:
    rows = conn.execute(
        """
        SELECT sm.entity_id, COUNT(*) AS n,
               MIN(s.last_updated_ts) AS first_ts, MAX(s.last_updated_ts) AS last_ts
        FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id
        GROUP BY sm.entity_id
        """
    ).fetchall()
    stats: list[EntityStat] = []
    for entity_id, n, first_ts, last_ts in rows:
        stats.append(
            EntityStat(entity_id, int(n), _ts_to_dt(first_ts), _ts_to_dt(last_ts))
        )
    return stats


def _collect_legacy(conn: sqlite3.Connection) -> list[EntityStat]:
    rows = conn.execute(
        """
        SELECT entity_id, COUNT(*) AS n,
               MIN(last_updated) AS first_ts, MAX(last_updated) AS last_ts
        FROM states GROUP BY entity_id
        """
    ).fetchall()
    return [
        EntityStat(entity_id, int(n), _ts_to_dt(first_ts), _ts_to_dt(last_ts))
        for entity_id, n, first_ts, last_ts in rows
    ]


def _fill_days_with_data(
    conn: sqlite3.Connection, stat: EntityStat, modern: bool
) -> None:
    if modern:
        row = conn.execute(
            """
            SELECT COUNT(DISTINCT CAST(s.last_updated_ts / 86400 AS INT))
            FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id
            WHERE sm.entity_id = ?
            """,
            (stat.entity_id,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(DISTINCT substr(last_updated, 1, 10)) "
            "FROM states WHERE entity_id = ?",
            (stat.entity_id,),
        ).fetchone()
    stat.days_with_data = int(row[0]) if row and row[0] is not None else 0


def _match_groups(stats: list[EntityStat]) -> list[GroupResult]:
    results: list[GroupResult] = []
    for name, keywords in FEATURE_GROUPS.items():
        group = GroupResult(name)
        for st in stats:
            eid = st.entity_id.lower()
            if any(kw in eid for kw in keywords):
                group.entities.append(st)
        group.entities.sort(key=lambda e: e.count, reverse=True)
        results.append(group)
    return results


def _fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d") if dt else "—"


def build_report(db_path: Path) -> str:
    conn = _connect_ro(db_path)
    try:
        modern = _has_table(conn, "states_meta")
        stats = _collect_modern(conn) if modern else _collect_legacy(conn)
        groups = _match_groups(stats)
        # Tages-Luecken nur fuer relevante (gematchte) Entities berechnen.
        relevant = {e.entity_id: e for g in groups for e in g.entities}
        for st in relevant.values():
            _fill_days_with_data(conn, st, modern)
    finally:
        conn.close()

    overall_first = min((s.first for s in stats if s.first), default=None)
    overall_last = max((s.last for s in stats if s.last), default=None)

    lines: list[str] = []
    lines.append("# HA-Recorder Audit")
    lines.append("")
    lines.append(f"- Datei: `{db_path}`")
    lines.append(f"- Schema: {'modern (states_meta)' if modern else 'legacy'}")
    lines.append(f"- Entities gesamt: {len(stats)}")
    lines.append(f"- Zeitraum: {_fmt_dt(overall_first)} bis {_fmt_dt(overall_last)}")
    lines.append("")
    lines.append("## Feature-Coverage fuer das Analyse-Ziel")
    lines.append("")

    for g in groups:
        mark = "OK" if g.present else "FEHLT"
        lines.append(f"### [{mark}] {g.name}")
        if not g.entities:
            lines.append("- keine passende Entity gefunden")
            lines.append("")
            continue
        lines.append("")
        lines.append("| entity_id | Werte | von | bis | Tages-Coverage | ~Intervall |")
        lines.append("|---|---:|---|---|---:|---:|")
        for e in g.entities[:12]:
            lines.append(
                f"| `{e.entity_id}` | {e.count} | {_fmt_dt(e.first)} | "
                f"{_fmt_dt(e.last)} | {e.coverage_pct:.0f}% | "
                f"{e.avg_interval_min:.1f} min |"
            )
        if len(g.entities) > 12:
            lines.append(f"| … und {len(g.entities) - 12} weitere | | | | | |")
        lines.append("")

    missing = [g.name for g in groups if not g.present]
    lines.append("## Fazit")
    lines.append("")
    if missing:
        lines.append("Fehlende Feature-Gruppen (blockieren oder schwaechen die Analyse):")
        for name in missing:
            lines.append(f"- **{name}**")
    else:
        lines.append("Alle Feature-Gruppen sind vorhanden.")
    lines.append("")
    lines.append(
        "Hinweis: niedrige Tages-Coverage oder ein spaeter Start bedeuten, dass die "
        "betroffene Saison nur teilweise analysierbar ist. Seasonale Aussagen entsprechend "
        "vorsichtig (Effektgroesse statt nur p-Wert, kleine Stichprobe beachten)."
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only HA-Recorder Audit")
    parser.add_argument(
        "--db",
        default="src/ha/config/home-assistant_v2.db",
        help="Pfad zur home-assistant_v2.db (oder einem Snapshot)",
    )
    parser.add_argument(
        "--out",
        default="",
        help="optionaler Pfad fuer einen Markdown-Report (sonst stdout)",
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
