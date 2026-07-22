"""
diagnose_nachtforscher.py — warum ist ein Cron-Versuch gescheitert oder gelungen?

Am 2026-07-21/22 brauchte es sieben verschiedene Fixes, bevor ein Versuch
ueberhaupt durchlief (Modell nicht konfiguriert, leeres Toolset, OOM, Denk-
Inkompatibilitaet, Modell ohne echtes Tool-Calling, zu kurzes Provider-Timeout,
manueller Neustart mitten im Lauf). Jeder Fund lag verstreut in
`cron/output/*.md`, `logs/agent.log` und den `config.yaml.bak-*`-Schnappschuessen.

Dieses Skript fasst das zusammen: eine Zeile pro Versuch, mit Ausgang und der
zu dem Zeitpunkt aktiven Konfiguration (welches Modell, welcher Timeout).

    python scripts/diagnose_nachtforscher.py                # ganze Historie
    python scripts/diagnose_nachtforscher.py --letzter       # nur der juengste Versuch, ausfuehrlich

Env (.env): UMBREL_HOST_GIGI, UMBREL_USER_GIGI, UMBREL_SUDO_PASS_GIGI
"""

from __future__ import annotations

import argparse
import io
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENV = dotenv_values(".env")
HOST = (ENV.get("UMBREL_HOST_GIGI") or ENV.get("UMBREL_HOST") or "").rstrip("/")
USER = ENV.get("UMBREL_USER_GIGI") or "umbrel"
SUDO = ENV.get("UMBREL_SUDO_PASS_GIGI") or ENV.get("UMBREL_SUDO_PASS") or ""

H = "/home/umbrel/umbrel/app-data/hermes-agent/data/hermes"
JOB_ID = "54857246e0dc"


def ssh(command: str, timeout: int = 90) -> str:
    """Fuehrt ein Kommando als root auf der Umbrel aus. Passwort per stdin."""
    remote = "sudo -S -p '' bash -c " + shlex.quote(command)
    try:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", f"{USER}@{HOST}", remote],
            input=f"{SUDO}\n",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return "\n".join(
        line for line in (r.stdout or "").splitlines() if not line.startswith("[sudo]")
    )


def config_snapshots() -> list[tuple[datetime, str]]:
    """Alle config.yaml.bak-* Dateien, chronologisch. Jede zeigt den Stand
    UNMITTELBAR VOR der im Dateinamen genannten Aenderung."""
    roh = ssh(f"ls -1 {H}/config.yaml.bak-* 2>/dev/null")
    treffer = []
    for pfad in roh.splitlines():
        m = re.search(r"(\d{8}T\d{6}Z)$", pfad.strip())
        if m:
            ts = datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ")
            treffer.append((ts, pfad.strip()))
    treffer.sort()
    return treffer


def werte_aus(pfad: str) -> dict[str, str]:
    roh = ssh(
        f"grep -E '^  default:|^  context_length:|gateway_timeout:|request_timeout_seconds:' "
        f"{pfad} 2>/dev/null"
    )
    werte: dict[str, str] = {}
    for zeile in roh.splitlines():
        if ":" not in zeile:
            continue
        schluessel, _, wert = zeile.strip().partition(":")
        werte.setdefault(schluessel.strip(), wert.strip())
    return werte


def aktive_config(
    zeitpunkt: datetime, snaps: list[tuple[datetime, str]]
) -> dict[str, str]:
    """Die Config, die zum gegebenen Zeitpunkt aktiv war: das juengste
    Backup, das NACH diesem Zeitpunkt liegt, zeigt den Vor-Zustand -
    also gilt bis zu diesem Backup-Zeitpunkt die Config DAVOR."""
    for ts, pfad in snaps:
        if ts >= zeitpunkt:
            return werte_aus(pfad)
    return werte_aus(f"{H}/config.yaml")


def cron_versuche() -> list[str]:
    roh = ssh(f"ls -1 {H}/cron/output/{JOB_ID}/*.md 2>/dev/null | sort")
    return [z.strip() for z in roh.splitlines() if z.strip()]


def lies_versuch(pfad: str) -> tuple[str, str]:
    """(Ausgang, Kurzfassung) eines einzelnen Versuchs."""
    inhalt = ssh(f"cat {shlex.quote(pfad)}")
    if "(FAILED)" in inhalt or "## Error" in inhalt:
        m = re.search(r"## Error\s*\n```\s*\n(.+?)\n```", inhalt, re.S)
        fehler = m.group(1).strip() if m else "unbekannter Fehler"
        return "FEHLGESCHLAGEN", fehler[:150]
    # Erfolgreicher Lauf: letzte nicht-leere Zeile ist meist das Fazit
    zeilen = [z for z in inhalt.splitlines() if z.strip()]
    return "OK", (zeilen[-1][:150] if zeilen else "(keine Ausgabe)")


def main() -> None:
    p = argparse.ArgumentParser(description="Diagnose der Nachtforscher-Cron-Versuche")
    p.add_argument(
        "--letzter", action="store_true", help="nur den juengsten Versuch, ausfuehrlich"
    )
    args = p.parse_args()

    if not HOST:
        raise SystemExit("UMBREL_HOST_GIGI fehlt in .env")

    snaps = config_snapshots()
    versuche = cron_versuche()
    if not versuche:
        print("Keine Versuche in cron/output/ gefunden.")
        return

    if args.letzter:
        versuche = versuche[-1:]

    print(f"{'Zeitpunkt':20s} {'Ausgang':14s} {'Modell':38s} {'Timeout':10s} Detail")
    print("-" * 130)
    for pfad in versuche:
        name = Path(pfad).stem  # z.B. 2026-07-22_09-31-27
        try:
            ts = datetime.strptime(name, "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            ts = None
        cfg = aktive_config(ts, snaps) if ts else {}
        modell = cfg.get("default", "?")
        timeout = cfg.get("request_timeout_seconds") or "(nicht gesetzt)"
        ausgang, detail = lies_versuch(pfad)
        zeitstr = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else name
        print(f"{zeitstr:20s} {ausgang:14s} {modell:38s} {timeout:10s} {detail}")


if __name__ == "__main__":
    main()
