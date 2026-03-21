"""
BlockScheduler — 10-Minuten-Takt mit block_id und valid_until.

Erzeugt block_id (ISO-8601 auf 10 Minuten gerundet) und berechnet
das Gültigkeitsfenster (valid_until) für jede Decision.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


BLOCK_DURATION_MIN: int = 10


def get_block_id(now: datetime | None = None) -> str:
    """
    Gibt die block_id für den aktuellen (oder übergebenen) Zeitpunkt zurück.

    Block_id = ISO-8601 auf 10 Minuten abgerundet, UTC.
    Beispiel: '2024-01-15T10:00:00'
    """
    if now is None:
        now = datetime.now(tz=timezone.utc)

    floored = now.replace(
        minute=(now.minute // BLOCK_DURATION_MIN) * BLOCK_DURATION_MIN,
        second=0,
        microsecond=0,
    )
    return floored.strftime("%Y-%m-%dT%H:%M:%S")


def get_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Gibt (window_start, window_end) für den aktuellen Block zurück."""
    if now is None:
        now = datetime.now(tz=timezone.utc)

    start = now.replace(
        minute=(now.minute // BLOCK_DURATION_MIN) * BLOCK_DURATION_MIN,
        second=0,
        microsecond=0,
    )
    end = start + timedelta(minutes=BLOCK_DURATION_MIN)
    return start, end


def get_valid_until(now: datetime | None = None) -> datetime:
    """
    Gibt valid_until für eine Decision zurück.

    Eine Decision gilt bis zum Ende des nächsten Blocks (= 2 Block-Dauern voraus),
    um Überlappungen beim Tick-Übergang zu vermeiden.
    """
    _, window_end = get_window(now)
    return window_end + timedelta(minutes=BLOCK_DURATION_MIN)
