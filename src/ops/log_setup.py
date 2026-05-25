"""
BitGridAI Log-Setup — zentralisierte Logging-Konfiguration.

Zwei Handler:
  Console (StreamHandler):         INFO+ (überschreibbar via LOG_LEVEL)
  File (TimedRotatingFileHandler): DEBUG+, rollt täglich, 14 Tage History

Verwendung:
    from src.ops.log_setup import setup_logging
    setup_logging(log_dir=Path("data/logs"))
"""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_CONSOLE_FMT = "%(asctime)s %(name)-30s %(levelname)-8s %(message)s"
_FILE_FMT = "%(asctime)s %(name)-40s %(levelname)-8s %(message)s"

_log_file_path: Path | None = None


def get_log_file() -> Path | None:
    """Gibt den konfigurierten Log-Dateipfad zurück."""
    return _log_file_path


def setup_logging(
    log_dir: Path | str | None = None,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
) -> None:
    """
    Konfiguriert Python-Logging für BitGridAI.

    Idempotent — zweiter Aufruf ist no-op.
    Root-Logger auf DEBUG setzen damit Handler selbst filtern.
    """
    global _log_file_path

    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    console.setFormatter(logging.Formatter(_CONSOLE_FMT))
    root.addHandler(console)

    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / "bitgrid.log"
        _log_file_path = path

        fh = TimedRotatingFileHandler(
            path,
            when="midnight",
            backupCount=14,
            encoding="utf-8",
        )
        fh.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
        fh.setFormatter(logging.Formatter(_FILE_FMT))
        root.addHandler(fh)
