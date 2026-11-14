"""Answer log of the KI hamster: every answer with the exact context it got.

Kept in its OWN SQLite file (``data/bithamster_log.db`` on the HA host), not
in the research database ``bitgrid.db``:

- The research DB holds measurements and stays read-only for the hamster.
  Model text is not a measurement; mixing both would blur what was measured
  and what a language model said about it.
- Storing the full prompt next to each answer makes every answer auditable
  afterwards (which facts did it see, which numbers did it invent) and lets
  answers be compared over time, e.g. before/after a SOUL or context change.

Writing the log must never break an answer: errors are logged and swallowed.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS hamster_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at    TEXT NOT NULL,
    kind            TEXT NOT NULL,          -- ask | analyse | eval
    request_id      TEXT,
    task            TEXT,
    label           TEXT,
    tab             TEXT,
    question        TEXT,
    model           TEXT,
    ok              INTEGER NOT NULL,
    error           TEXT,
    headline        TEXT,
    text            TEXT,
    points_json     TEXT,                   -- punkte (ask) or optimierungen (analyse)
    checks_json     TEXT,                   -- deterministic post-checks
    duration_s      REAL,
    prompt          TEXT,                   -- exact user message sent to the model
    eval_run        TEXT                    -- groups the rows of one eval run
);
CREATE INDEX IF NOT EXISTS idx_hamster_log_time ON hamster_log (generated_at);
CREATE INDEX IF NOT EXISTS idx_hamster_log_task ON hamster_log (kind, task);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    """Open (and create) the log database."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.executescript(SCHEMA)
    return conn


def _row(
    kind: str, result: dict[str, Any], prompt: str | None, eval_run: str | None
) -> tuple[Any, ...]:
    if kind == "analyse":
        lage = result.get("lage") or {}
        headline, text = lage.get("headline"), lage.get("text")
        points: Any = result.get("optimierungen") or []
    else:
        answer = result.get("answer") or {}
        headline, text = answer.get("headline"), answer.get("text")
        points = answer.get("punkte") or []
    checks = result.get("checks")
    return (
        str(result.get("generated_at") or ""),
        kind,
        result.get("request_id"),
        result.get("task") or ("analyse" if kind == "analyse" else None),
        result.get("label"),
        result.get("tab"),
        result.get("question"),
        result.get("model"),
        1 if result.get("ok") else 0,
        result.get("error"),
        headline,
        text,
        json.dumps(points, ensure_ascii=False),
        json.dumps(checks, ensure_ascii=False) if checks is not None else None,
        result.get("duration_s"),
        prompt,
        eval_run,
    )


def log_entry(
    path: str | Path,
    kind: str,
    result: dict[str, Any],
    *,
    prompt: str | None = None,
    eval_run: str | None = None,
) -> bool:
    """Append one answer. Returns False (and logs) instead of raising."""
    try:
        conn = connect(path)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO hamster_log (generated_at, kind, request_id, task,"
                    " label, tab, question, model, ok, error, headline, text,"
                    " points_json, checks_json, duration_s, prompt, eval_run)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    _row(kind, result, prompt, eval_run),
                )
        finally:
            conn.close()
    except Exception:  # the answer itself is already written; never fail here
        log.exception("bithamster log: could not write %s", path)
        return False
    return True


def import_history(path: str | Path, ask_json: dict[str, Any]) -> int:
    """One-off: copy the existing card history (bithamster_ask.json) into the log.

    Skips request_ids already logged, so it can run more than once. These old
    rows have no prompt (it was not stored before 13.11.2026).
    """
    history = ask_json.get("history")
    if not isinstance(history, list):
        return 0
    conn = connect(path)
    try:
        known = {
            r[0]
            for r in conn.execute(
                "SELECT request_id FROM hamster_log WHERE request_id IS NOT NULL"
            )
        }
        rows = [
            _row("ask", h, None, None)
            for h in reversed(history)
            if isinstance(h, dict) and h.get("request_id") not in known
        ]
        with conn:
            conn.executemany(
                "INSERT INTO hamster_log (generated_at, kind, request_id, task,"
                " label, tab, question, model, ok, error, headline, text,"
                " points_json, checks_json, duration_s, prompt, eval_run)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
    finally:
        conn.close()
    return len(rows)
