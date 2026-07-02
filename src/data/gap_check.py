"""
GapCheck — erkennt fehlende 10-Minuten-Bloecke in energy_states.

Verwendung:
  python -m src.data.gap_check              # letzte 7 Tage
  python -m src.data.gap_check --days 30
  python -m src.data.gap_check --from 2026-06-01 --to 2026-06-30

Gibt Exit-Code 1 zurueck wenn Luecken gefunden wurden — nuetzlich in CI oder
als Pre-Check vor Analysen.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from datetime import datetime, timedelta, timezone

from src.data.db import get_connection

log = logging.getLogger(__name__)

BLOCK_MINUTES = 10


def find_gaps(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
) -> list[tuple[datetime, datetime]]:
    """
    Gibt alle Luecken in energy_states im Zeitraum [start, end) zurueck.

    Eine Luecke ist ein Intervall ohne Eintrag, das groesser als ein Block ist.
    Gibt Liste von (luecke_start, luecke_end)-Tupeln zurueck.
    """
    cur = conn.execute(
        """
        SELECT window_start FROM energy_states
        WHERE window_start >= ? AND window_start < ?
        ORDER BY window_start
        """,
        (start.isoformat(), end.isoformat()),
    )
    present = [datetime.fromisoformat(row[0]) for row in cur.fetchall()]

    if not present:
        # Gesamter Zeitraum fehlt
        return [(start, end)]

    gaps: list[tuple[datetime, datetime]] = []
    step = timedelta(minutes=BLOCK_MINUTES)

    # Luecke am Anfang
    first_block = _floor_to_block(start)
    if present[0] > first_block + step:
        gaps.append((first_block, present[0]))

    # Innere Luecken
    for i in range(1, len(present)):
        expected = present[i - 1] + step
        actual = present[i]
        if actual > expected + step:
            gaps.append((expected, actual))

    # Luecke am Ende
    last_expected = _floor_to_block(end) - step
    if present[-1] < last_expected:
        gaps.append((present[-1] + step, _floor_to_block(end)))

    return gaps


def gap_count_minutes(gaps: list[tuple[datetime, datetime]]) -> float:
    return sum((e - s).total_seconds() / 60 for s, e in gaps)


def print_gap_report(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
) -> int:
    """Gibt Gap-Report aus. Gibt Anzahl der Luecken zurueck."""
    cur = conn.execute(
        "SELECT COUNT(*), MIN(window_start), MAX(window_start) FROM energy_states WHERE window_start >= ? AND window_start < ?",
        (start.isoformat(), end.isoformat()),
    )
    count, first, last = cur.fetchone()

    span_days = (end - start).days
    expected_blocks = int((end - start).total_seconds() / 60 / BLOCK_MINUTES)

    print(
        f"Zeitraum: {start.strftime('%Y-%m-%d')} bis {end.strftime('%Y-%m-%d')} ({span_days}d)"
    )
    print(f"Erwartet: {expected_blocks} Bloecke | Vorhanden: {count}")
    if first:
        print(f"Erster:   {first}")
        print(f"Letzter:  {last}")

    gaps = find_gaps(conn, start, end)
    total_min = gap_count_minutes(gaps)

    if not gaps:
        print("Luecken:  keine — energy_states ist lueckenlos.")
        return 0

    print(
        f"Luecken:  {len(gaps)} Intervalle = {total_min:.0f} min ({total_min/60:.1f}h fehlend)"
    )
    print()
    for gap_start, gap_end in gaps[:20]:
        dur = (gap_end - gap_start).total_seconds() / 60
        print(
            f"  {gap_start.strftime('%Y-%m-%d %H:%M')} -> {gap_end.strftime('%Y-%m-%d %H:%M')} ({dur:.0f} min)"
        )
    if len(gaps) > 20:
        print(f"  ... +{len(gaps) - 20} weitere Luecken")

    print()
    print(f"Tipp: make sync-history schliesst diese Luecken via HA REST API.")
    return len(gaps)


def _floor_to_block(ts: datetime) -> datetime:
    ts_utc = ts.astimezone(timezone.utc)
    floored_min = (ts_utc.minute // 10) * 10
    return ts_utc.replace(minute=floored_min, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(description="Luecken in energy_states pruefen")
    parser.add_argument(
        "--days", type=int, default=7, help="Letzte N Tage pruefen (default: 7)"
    )
    parser.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD")
    parser.add_argument("--db", default="data/bitgrid.db")
    args = parser.parse_args()

    now = datetime.now(tz=timezone.utc)
    if args.from_date:
        start = datetime.fromisoformat(args.from_date).replace(tzinfo=timezone.utc)
    else:
        start = now - timedelta(days=args.days)
    end = (
        datetime.fromisoformat(args.to_date).replace(tzinfo=timezone.utc)
        if args.to_date
        else now
    )

    conn = get_connection(args.db)
    try:
        gap_count = print_gap_report(conn, start, end)
    finally:
        conn.close()

    raise SystemExit(1 if gap_count > 0 else 0)


if __name__ == "__main__":
    main()
