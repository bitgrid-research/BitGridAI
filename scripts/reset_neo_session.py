"""
reset_neo_session.py — erzwingt eine frische SOUL.md fuer laufende Chats.

Hermes laedt SOUL.md nur beim **Sessionstart**, nicht bei jeder Nachricht
(offizielle Doku: "SOUL is read when the cached system prompt is assembled
at session start"). Ein Discord-Kanal ist aus Hermes' Sicht EINE lang laufende
Session, die ueber Container-Neustarts hinweg bestehen bleibt. Wer also
SOUL.md/config.yaml aendert und Hermes neu startet, sieht in einem
bestehenden Discord-Chat trotzdem die ALTE Identitaet, bis diese eine Session
beendet wird — am 2026-07-22 live beobachtet: Neo stellte sich in Discord noch
mit der alten Rolle vor, obwohl SOUL.md im Container laengst die neue war.

Waehrend der aktiven Entwicklungsphase (haeufige Neustarts) ist das lastige
manuelle Nachschlagen ueber `hermes sessions list/delete`. Dieses Skript macht
daraus einen Handgriff: nach jedem SOUL.md/config-Neustart einmal ausfuehren,
dann startet die naechste Nachricht in jedem Chat-Kanal garantiert frisch.

    python scripts/reset_neo_session.py            # zeigt betroffene Sessions, fragt nach
    python scripts/reset_neo_session.py --yes       # loescht ohne Rueckfrage

Cron-Sessions (`cron_*`) sind ausgenommen: die kriegen sowieso pro Lauf eine
neue Session, die betrifft dieses Problem nicht.

Env (.env): UMBREL_HOST_GIGI, UMBREL_USER_GIGI, UMBREL_SUDO_PASS_GIGI
"""

from __future__ import annotations

import argparse
import io
import shlex
import subprocess
import sys

from dotenv import dotenv_values

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENV = dotenv_values(".env")
UMBREL = (ENV.get("UMBREL_HOST_GIGI") or ENV.get("UMBREL_HOST") or "").rstrip("/")
UMBREL_USER = ENV.get("UMBREL_USER_GIGI") or ENV.get("UMBREL_USER") or "umbrel"
SUDO = ENV.get("UMBREL_SUDO_PASS_GIGI") or ENV.get("UMBREL_SUDO_PASS") or ""
CONTAINER = "hermes-agent_web_1"


def ssh(befehl: str, timeout: int = 30) -> str:
    remote = f"echo {shlex.quote(SUDO)} | sudo -S -p '' bash -c " + shlex.quote(befehl)
    voll = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        f"{UMBREL_USER}@{UMBREL}",
        remote,
    ]
    ergebnis = subprocess.run(voll, capture_output=True, text=True, timeout=timeout)
    return (ergebnis.stdout or "") + (ergebnis.stderr or "")


def alle_interaktiven_sitzungen() -> list[str]:
    """Listet ALLE Sessions ungefiltert und schliesst nur cron_*-Sessions aus.

    Der --source-Filter von `hermes sessions list` erwies sich am 23.07.2026
    als unzuverlaessig: er lieferte "No sessions found" fuer eine Session, die
    im ungefilterten Listing nachweislich vorhanden und aktiv war (Discord,
    zuletzt vor 7 Minuten aktiv). Deshalb hier bewusst kein serverseitiger
    Quellen-Filter mehr, sondern client-seitiges Ausschliessen von cron_*.
    """
    ausgabe = ssh(f"docker exec {CONTAINER} hermes sessions list --limit 100")
    ids = []
    for zeile in ausgabe.splitlines():
        teile = zeile.rsplit(None, 1)
        if len(teile) != 2 or zeile.startswith("─") or teile[1] == "ID":
            continue
        sid = teile[1]
        if sid.count("_") >= 2 and not sid.startswith("cron_"):
            ids.append(sid)
    return ids


def main() -> None:
    p = argparse.ArgumentParser(
        description="Loescht laufende Chat-Sessions, damit die naechste Nachricht die aktuelle SOUL.md laedt"
    )
    p.add_argument("--yes", action="store_true", help="Ohne Rueckfrage loeschen")
    args = p.parse_args()

    ids = alle_interaktiven_sitzungen()

    if not ids:
        print("Keine laufenden Chat-Sessions gefunden, nichts zu tun.")
        return

    print(f"{len(ids)} Session(en): {', '.join(ids)}")

    if not args.yes:
        antwort = input("Diese Sessions loeschen? [y/N] ").strip().lower()
        if antwort != "y":
            print("Abgebrochen, nichts geloescht.")
            return

    for sid in ids:
        out = ssh(f"docker exec {CONTAINER} hermes sessions delete {sid} --yes")
        status = "OK" if "Deleted session" in out else out.strip()[:120]
        print(f"  {sid}: {status}")

    print(
        "Fertig. Die naechste Nachricht in jedem Kanal startet frisch mit der aktuellen SOUL.md."
    )


if __name__ == "__main__":
    main()
