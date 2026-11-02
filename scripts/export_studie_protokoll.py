"""Export the study session protocol from the lab Home Assistant.

Every session event on the lab is a state change of a helper in
src/ha/lab_only/lab_studie.yaml (VP, group, session on/off, verwertbar, note,
pause counter) or of the replay (lab_demo_running), and the participant's
tablet reports what it shows (input_text.lab_studie_tablet_anzeige). This
script reads that history over the REST API and writes

  data/study/sitzungen.csv    one row per session (VP, group, times, pauses,
                              verwertbar, notes, exposure checks)
  data/study/exposition.csv   every change of what the tablet showed during a
                              session (time, sim clock, variant, hamster text)
  data/study/eingaben.csv     every task input during a session (field, old and
                              new value, sim clock, person or automation),
                              from input_text.lab_studie_eingabe

data/study/ is gitignored (pseudonymous VP codes only, still study data).
Run it after each session day; the recorder keeps the history, but the CSV is
the archived protocol. Re-running rewrites both files from the full history.

Host and token come from .env (LAB_HOST, HA_TOKEN), never from code.

Usage: python scripts/export_studie_protokoll.py [--days 60] [--out data/study]
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

SESSION = "input_boolean.lab_studie_sitzung"
VP = "input_select.lab_studie_vp"
GROUP = "input_select.lab_studie_gruppe"
USABLE = "input_select.lab_studie_verwertbar"
NOTE = "input_text.lab_studie_notiz"
PAUSES = "counter.lab_studie_pausen"
RUNNING = "input_boolean.lab_demo_running"
SHOWN = "input_text.lab_studie_tablet_anzeige"
CLOCK = "sensor.lab_sim_clock"
INPUT = "input_text.lab_studie_eingabe"
ENTITIES = [SESSION, VP, GROUP, USABLE, NOTE, PAUSES, RUNNING, SHOWN, CLOCK, INPUT]


@dataclass(frozen=True)
class Change:
    at: datetime
    state: str


History = dict[str, list[Change]]


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def fetch_history(base: str, token: str, start: datetime, end: datetime) -> History:
    query = urllib.parse.urlencode(
        {"filter_entity_id": ",".join(ENTITIES), "end_time": end.isoformat()}
    )
    url = f"{base}/api/history/period/{urllib.parse.quote(start.isoformat())}?{query}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data: list[list[dict[str, Any]]] = json.loads(resp.read())
    hist: History = {e: [] for e in ENTITIES}
    for series in data:
        for item in series:
            entity = str(item["entity_id"])
            at = datetime.fromisoformat(str(item["last_changed"])).astimezone()
            hist.setdefault(entity, []).append(Change(at, str(item["state"])))
    for changes in hist.values():
        changes.sort(key=lambda c: c.at)
    return hist


def state_at(changes: list[Change], at: datetime) -> str:
    """State of an entity at a point in time ('' before the first record)."""
    value = ""
    for c in changes:
        if c.at > at:
            break
        value = c.state
    return value


def within(changes: list[Change], start: datetime, end: datetime) -> list[Change]:
    return [c for c in changes if start <= c.at < end]


def drop_restores(changes: list[Change]) -> list[Change]:
    """Drop records whose state equals the previous one.

    HA writes every entity again when it starts (restore_state); for the tablet
    display and the input log that is no new event. Real events always differ
    (the input log carries its own wall-clock time, the display log changes only
    when the display does), found live 17.10.2026 after a lab restart.
    """
    return [
        c for i, c in enumerate(changes) if i == 0 or c.state != changes[i - 1].state
    ]


def sessions(hist: History, now: datetime) -> list[tuple[datetime, datetime, bool]]:
    """(start, end, closed) intervals in which the session flag was on."""
    out: list[tuple[datetime, datetime, bool]] = []
    start: datetime | None = None
    for c in hist[SESSION]:
        if c.state == "on" and start is None:
            start = c.at
        elif c.state != "on" and start is not None:
            out.append((start, c.at, True))
            start = None
    if start is not None:
        out.append((start, now, False))
    return out


def run_intervals(
    hist: History, start: datetime, end: datetime
) -> list[tuple[datetime, datetime]]:
    on_at: datetime | None = start if state_at(hist[RUNNING], start) == "on" else None
    out: list[tuple[datetime, datetime]] = []
    for c in within(hist[RUNNING], start, end):
        if c.state == "on" and on_at is None:
            on_at = c.at
        elif c.state != "on" and on_at is not None:
            out.append((on_at, c.at))
            on_at = None
    if on_at is not None:
        out.append((on_at, end))
    return out


def parse_shown(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def fmt(at: datetime | None) -> str:
    return at.strftime("%Y-%m-%d %H:%M:%S") if at else ""


def export(hist: History, now: datetime, out_dir: Path) -> tuple[int, int, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    session_rows: list[dict[str, Any]] = []
    exposure_rows: list[dict[str, Any]] = []
    input_rows: list[dict[str, Any]] = []
    shown_log = drop_restores(hist[SHOWN])
    input_log = drop_restores(hist[INPUT])
    for start, end, closed in sessions(hist, now):
        # VP and group as they stood when the session was closed (the session
        # locks both; a change under "Technik entsperren" is flagged below).
        last = end - timedelta(seconds=1)
        vp = state_at(hist[VP], last)
        group = state_at(hist[GROUP], last)
        vp_changes = [c.state for c in within(hist[VP], start, last)]
        group_changes = [c.state for c in within(hist[GROUP], start, last)]
        runs = run_intervals(hist, start, end)
        notes = [c.state for c in within(hist[NOTE], start, end) if c.state.strip()]
        shown = [(c.at, parse_shown(c.state)) for c in within(shown_log, start, end)]
        for at, s in shown:
            exposure_rows.append(
                {
                    "vp": vp,
                    "zeit": fmt(at),
                    "sim_uhr": state_at(hist[CLOCK], at),
                    "variante_tablet": s.get("v", ""),
                    "hamster": s.get("k", ""),
                    "bild": s.get("i", ""),
                    "konto": s.get("u", ""),
                    "admin": s.get("a", ""),
                    "seite": s.get("p", ""),
                }
            )
        inputs = [(c.at, parse_shown(c.state)) for c in within(input_log, start, end)]
        final: dict[str, Any] = {}
        for at, e in inputs:
            if not e:
                continue
            input_rows.append(
                {
                    "vp": vp,
                    "zeit": fmt(at),
                    "sim_uhr": e.get("s", ""),
                    "feld": e.get("f", ""),
                    "vorher": e.get("v", ""),
                    "nachher": e.get("w", ""),
                    "quelle": "Person" if e.get("p") == 1 else "Automatik",
                }
            )
            if e.get("p") == 1:
                final[str(e.get("f", ""))] = e.get("w", "")
        variants = {str(s.get("v", "")) for _, s in shown if s}
        session_rows.append(
            {
                "vp": vp,
                "test": "ja" if vp == "TEST" else "nein",
                "gruppe": group,
                "beginn": fmt(start),
                "ende": fmt(end) if closed else "",
                "abgeschlossen": "ja" if closed else "nein (laeuft)",
                "erstes_play": fmt(runs[0][0]) if runs else "",
                "lauf_netto_s": round(sum((b - a).total_seconds() for a, b in runs)),
                "starts": len(runs),
                # at the end itself (not 1 s before): nothing resets these after closing, and
                # a value set in the same second as "Sitzung abschliessen" was missed (19.10.2026)
                "pausen": state_at(hist[PAUSES], end),
                "verwertbar": state_at(hist[USABLE], end),
                "notizen": " | ".join(dict.fromkeys(notes)),
                "vp_gewechselt": "ja" if vp_changes else "nein",
                "gruppe_gewechselt": "ja" if group_changes else "nein",
                "tablet_meldungen": len(shown),
                "tablet_variante_passt": (
                    "ja"
                    if variants == {group}
                    else ("keine Meldung" if not variants else "NEIN")
                ),
                "tablet_admin_konto": (
                    "ja" if any(s.get("a") == 1 for _, s in shown) else "nein"
                ),
                "eingaben": sum(1 for _, e in inputs if e.get("p") == 1),
                "eingaben_endwerte": "; ".join(f"{k}={v}" for k, v in final.items()),
            }
        )
    for name, rows in (
        ("sitzungen.csv", session_rows),
        ("exposition.csv", exposure_rows),
        ("eingaben.csv", input_rows),
    ):
        path = out_dir / name
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            if rows:
                writer = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter=";")
                writer.writeheader()
                writer.writerows(rows)
    return len(session_rows), len(exposure_rows), len(input_rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=60, help="history window (days back)")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "study")
    args = ap.parse_args()
    env = load_env()
    if not env.get("LAB_HOST") or not env.get("HA_TOKEN"):
        raise SystemExit("! LAB_HOST and HA_TOKEN must be set in .env")
    now = datetime.now(timezone.utc).astimezone()
    hist = fetch_history(
        f"http://{env['LAB_HOST']}:8123",
        env["HA_TOKEN"],
        now - timedelta(days=args.days),
        now,
    )
    n_sessions, n_exposure, n_inputs = export(hist, now, args.out)
    print(
        f"{n_sessions} Sitzung(en), {n_exposure} Anzeige-Wechsel, "
        f"{n_inputs} Eingabe(n) -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
