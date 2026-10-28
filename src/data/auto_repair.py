"""
AutoRepair - repariert die bekannten Erfassungsfehler in energy_states.

Entstanden aus den Vorfaellen vom September 2026 (siehe data/recovery/):
ein dreitaegiger Erfassungsausfall wurde als "0 W" statt als Luecke
aufgezeichnet, 24 Tage fehlten in der Datenbank, und der History-Sync
schrieb den letzten bekannten Wert in die Zukunft fort.

## Warum das hier vorsichtig ist

Der ausgefallene SMA-Watchdog war selbst eine automatische Reparatur. Er hat
den Schaden verursacht, den er verhindern sollte, weil er ohne Begrenzung in
einen laufenden Fehler hineinregelte. Diese Reparatur ist deshalb nach
Eingriffstiefe gestaffelt und haelt sich an feste Grenzen:

1. `--dry-run` ist der Standard. Ohne `--apply` wird nichts geschrieben.
2. Es werden nur Werte ersetzt, die **nachweislich falsch** sind: eine 0, der
   ein echter Zaehlerzuwachs des Geraets gegenuebersteht. Ein vorhandener
   Messwert wird nie ueberschrieben.
3. `MAX_BLOCKS_PER_RUN` begrenzt jeden Lauf. Wuerde eine Reparatur mehr
   Bloecke anfassen, bricht sie ab und meldet, statt die Datenbank
   umzuschreiben. Das faengt Programmierfehler ab, bevor sie Daten kosten.
4. Rekonstruierte Werte werden als solche markiert (`quality='warn'`,
   `pv_power_w_reconstructed` in `missing_signals_json`), damit keine
   Auswertung sie fuer Originalmessungen haelt.
5. Zaehlerabweichungen werden nur **gemeldet**, nie automatisch korrigiert:
   dafuer gibt es zu viele legitime Ursachen (Geraetetausch, Zaehlerueberlauf).

CLI:
  python -m src.data.auto_repair                 # Bericht, aendert nichts
  python -m src.data.auto_repair --apply         # repariert
  python -m src.data.auto_repair --days 30       # anderer Zeitraum
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from src.adapters.sma_webconnect_log import (
    SmaWebConnectError,
    SmaWebConnectLog,
    resample_to_blocks,
)
from src.data.db import get_connection

log = logging.getLogger(__name__)

BLOCK_MINUTES = 10
# Obergrenze je Lauf. Groessere Schaeden gehoeren angesehen, nicht automatisch
# ueberschrieben. Der Septemberausfall umfasste 351 Bloecke.
MAX_BLOCKS_PER_RUN = 600
# Ab dieser Leistung gilt ein Block als echte Erzeugung, darunter als Rauschen.
MIN_RECONSTRUCT_W = 20.0
RECONSTRUCTED_MARKER = "pv_power_w_reconstructed"


@dataclass
class RepairAction:
    """Ein einzelner Reparaturschritt und sein Ergebnis."""

    kind: str
    detail: str
    blocks: int = 0
    applied: bool = False
    blocked: bool = False


@dataclass
class RepairReport:
    """Ergebnis eines Laufs."""

    actions: list[RepairAction] = field(default_factory=list)

    @property
    def changed(self) -> int:
        return sum(a.blocks for a in self.actions if a.applied)

    @property
    def blocked(self) -> bool:
        return any(a.blocked for a in self.actions)

    def render(self) -> str:
        lines = ["", "=== AutoRepair ==="]
        if not self.actions:
            lines.append("  Nichts zu tun, energy_states ist konsistent.")
        for action in self.actions:
            if action.blocked:
                state = "ABGEBROCHEN"
            elif action.applied:
                state = "repariert"
            elif action.blocks:
                state = "erkannt (dry-run)"
            else:
                state = "ok"
            lines.append(f"  [{state}] {action.kind}: {action.detail}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Stufe 1: eindeutig falsche Daten entfernen
# ---------------------------------------------------------------------------


def remove_future_blocks(
    conn: sqlite3.Connection, now: datetime, apply: bool
) -> RepairAction:
    """
    Loescht Bloecke, die in der Zukunft liegen.

    Der History-Sync hielt bei einem Enddatum in der Zukunft den letzten
    bekannten Wert fest und schrieb ihn als quality="ok" fort. Solche Bloecke
    sind keine Messung, sondern eine Fortschreibung, und damit wertlos.
    Die Ursache ist in ha_history_sync behoben, das Aufraeumen bleibt noetig.
    """
    cutoff = now.strftime("%Y-%m-%dT%H:%M")
    count = int(
        conn.execute(
            "SELECT COUNT(*) FROM energy_states WHERE window_start > ?", (cutoff,)
        ).fetchone()[0]
    )
    if count == 0:
        return RepairAction("Zukunftsbloecke", "keine gefunden")
    if count > MAX_BLOCKS_PER_RUN:
        return RepairAction(
            "Zukunftsbloecke",
            f"{count} Bloecke nach {cutoff} - mehr als das Limit von "
            f"{MAX_BLOCKS_PER_RUN}, bitte manuell pruefen",
            blocks=count,
            blocked=True,
        )
    if apply:
        for table, column in (
            ("energy_states", "window_start"),
            ("device_states", "block_id"),
            ("miner_states", "block_id"),
        ):
            conn.execute(f"DELETE FROM {table} WHERE {column} > ?", (cutoff,))
        conn.commit()
    return RepairAction(
        "Zukunftsbloecke",
        f"{count} Bloecke nach {cutoff} entfernt (samt device_/miner_states)",
        blocks=count,
        applied=apply,
    )


# ---------------------------------------------------------------------------
# Stufe 2: PV-Nullen gegen den Geraetezaehler rekonstruieren
# ---------------------------------------------------------------------------


def find_pv_zero_blocks(
    conn: sqlite3.Connection, start: datetime, end: datetime
) -> list[str]:
    """Bloecke mit pv_power_w = 0, die noch nicht als rekonstruiert gelten."""
    rows = conn.execute(
        "SELECT window_start FROM energy_states"
        " WHERE window_start >= ? AND window_start < ?"
        "   AND pv_power_w = 0"
        "   AND (missing_signals_json IS NULL"
        "        OR missing_signals_json NOT LIKE ?)"
        " ORDER BY window_start",
        (
            start.strftime("%Y-%m-%dT%H:%M"),
            end.strftime("%Y-%m-%dT%H:%M"),
            f"%{RECONSTRUCTED_MARKER}%",
        ),
    ).fetchall()
    return [str(r[0]) for r in rows]


def reconstruct_pv_from_meter(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
    device_blocks: dict[datetime, float],
    apply: bool,
) -> RepairAction:
    """
    Ersetzt falsche PV-Nullen durch die Leistung aus dem Geraetezaehler.

    Angefasst wird nur, wo die Datenbank 0 zeigt und das Geraet fuer denselben
    Block echte Erzeugung meldet. Nachts bleibt die 0 stehen, weil das Geraet
    dort ebenfalls 0 liefert: eine Null ist nur dann falsch, wenn ihr ein
    Zaehlerzuwachs widerspricht.
    """
    zero_blocks = find_pv_zero_blocks(conn, start, end)
    if not zero_blocks:
        return RepairAction("PV-Nullen", "keine verdaechtigen Nullen gefunden")

    candidates: list[tuple[float, str]] = []
    for ts_text in zero_blocks:
        parsed = datetime.fromisoformat(ts_text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        watts = device_blocks.get(parsed)
        if watts is not None and watts >= MIN_RECONSTRUCT_W:
            candidates.append((watts, ts_text))

    if not candidates:
        return RepairAction(
            "PV-Nullen",
            f"{len(zero_blocks)} Nullen geprueft, keine davon widerlegt "
            f"(Geraet meldet dort ebenfalls keine Erzeugung)",
        )
    if len(candidates) > MAX_BLOCKS_PER_RUN:
        return RepairAction(
            "PV-Nullen",
            f"{len(candidates)} widerlegte Nullen - mehr als das Limit von "
            f"{MAX_BLOCKS_PER_RUN}, bitte manuell pruefen",
            blocks=len(candidates),
            blocked=True,
        )

    energy_kwh = sum(w for w, _ in candidates) * (BLOCK_MINUTES / 60) / 1000
    if apply:
        for watts, ts_text in candidates:
            row = conn.execute(
                "SELECT house_load_w, grid_import_w, missing_signals_json"
                " FROM energy_states WHERE window_start = ?",
                (ts_text,),
            ).fetchone()
            if row is None:
                continue
            house, grid, missing_json = row
            try:
                missing = json.loads(missing_json) if missing_json else []
            except json.JSONDecodeError:
                missing = []
            if not isinstance(missing, list):
                missing = []
            if RECONSTRUCTED_MARKER not in missing:
                missing.append(RECONSTRUCTED_MARKER)
            surplus = round((watts - float(house or 0) - float(grid or 0)) / 1000, 3)
            conn.execute(
                "UPDATE energy_states SET pv_power_w = ?, surplus_kw = ?,"
                " quality = 'warn', missing_signals_json = ?"
                " WHERE window_start = ?",
                (watts, surplus, json.dumps(missing), ts_text),
            )
        conn.commit()

    return RepairAction(
        "PV-Nullen",
        f"{len(candidates)} Bloecke aus dem Geraetezaehler rekonstruiert "
        f"({energy_kwh:.3f} kWh), markiert als {RECONSTRUCTED_MARKER}",
        blocks=len(candidates),
        applied=apply,
    )


# ---------------------------------------------------------------------------
# Stufe 3: nur melden
# ---------------------------------------------------------------------------


def report_day_deviation(
    conn: sqlite3.Connection, device_days: dict[str, float], tolerance_pct: float = 5.0
) -> RepairAction:
    """
    Vergleicht die Tagessummen der Datenbank mit dem Geraetelog.

    Reine Meldung: Eine Abweichung kann viele Ursachen haben, von einer
    Erfassungsluecke bis zu einem Geraetetausch. Automatisch zu korrigieren
    hiesse raten.
    """
    deviations: list[str] = []
    for day, device_kwh in sorted(device_days.items()):
        row = conn.execute(
            "SELECT SUM(pv_power_w) FROM energy_states WHERE window_start LIKE ?",
            (f"{day}%",),
        ).fetchone()
        if row is None or row[0] is None:
            continue
        db_kwh = float(row[0]) * (BLOCK_MINUTES / 60) / 1000
        if device_kwh <= 0:
            continue
        diff_pct = abs(db_kwh - device_kwh) / device_kwh * 100
        if diff_pct > tolerance_pct:
            deviations.append(
                f"{day}: DB {db_kwh:.2f} kWh gegen Geraet {device_kwh:.2f} kWh "
                f"({diff_pct:.1f}%)"
            )
    if not deviations:
        return RepairAction(
            "Tagesabgleich", f"alle Tage innerhalb von {tolerance_pct:.0f}%"
        )
    return RepairAction(
        "Tagesabgleich",
        f"{len(deviations)} Tag(e) ausserhalb der Toleranz: "
        + "; ".join(deviations[:5]),
        blocks=len(deviations),
    )


# ---------------------------------------------------------------------------
# Orchestrierung
# ---------------------------------------------------------------------------


def run_repair(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
    sma_host: str,
    sma_password: str,
    apply: bool,
) -> RepairReport:
    """Fuehrt alle Reparaturstufen aus. Ohne apply wird nichts geschrieben."""
    report = RepairReport()

    # Stufe 1 braucht kein Geraet
    report.actions.append(remove_future_blocks(conn, end, apply))

    # Stufe 2 und 3 brauchen das Geraetelog. Faellt es aus, laeuft der Rest
    # trotzdem: eine fehlende Quelle darf keine Reparatur verhindern, die
    # bereits erledigt ist.
    if not sma_host or not sma_password:
        report.actions.append(
            RepairAction(
                "Geraetelog",
                "SMA_HOST oder SMA_PASSWORD fehlt in .env, "
                "PV-Rekonstruktion uebersprungen",
            )
        )
        return report

    try:
        with SmaWebConnectLog(sma_host, sma_password) as device:
            series = device.meter_series(start, end)
            device_days = {
                day.isoformat(): kwh
                for day, kwh in device.day_yields(start, end).items()
            }
    except (SmaWebConnectError, ValueError) as err:
        report.actions.append(
            RepairAction("Geraetelog", f"nicht lesbar: {err}", blocked=True)
        )
        return report

    device_blocks = resample_to_blocks(series, BLOCK_MINUTES)
    report.actions.append(
        reconstruct_pv_from_meter(conn, start, end, device_blocks, apply)
    )
    report.actions.append(report_day_deviation(conn, device_days))
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repariert bekannte Erfassungsfehler in energy_states"
    )
    parser.add_argument(
        "--days", type=int, default=14, help="Zeitraum rueckwaerts (default: 14)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aenderungen wirklich schreiben (ohne: nur Bericht)",
    )
    parser.add_argument("--db", default="data/bitgrid.db", help="Pfad zur SQLite-DB")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    args = _parse_args()

    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

    now = datetime.now(tz=timezone.utc)
    start = now - timedelta(days=args.days)

    conn = get_connection(args.db)
    try:
        report = run_repair(
            conn,
            start,
            now,
            os.getenv("SMA_HOST", ""),
            os.getenv("SMA_PASSWORD", ""),
            args.apply,
        )
    finally:
        conn.close()

    print(report.render())
    if not args.apply and any(a.blocks and not a.blocked for a in report.actions):
        print("\n  Nichts geschrieben. Mit --apply anwenden.")
    if report.blocked:
        print("\n  Mindestens eine Reparatur wurde abgebrochen, siehe oben.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
