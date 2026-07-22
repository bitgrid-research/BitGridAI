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
    python scripts/reset_neo_session.py --source discord   # nur eine Quelle (Default: alle Chat-Quellen)

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

CHAT_QUELLEN = ("discord", "telegram", "whatsapp", "slack")


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


def sitzungen_je_quelle(quelle: str) -> list[str]:
    ausgabe = ssh(
        f"docker exec {CONTAINER} hermes sessions list --source {quelle} --limit 50"
    )
    ids = []
    for zeile in ausgabe.splitlines():
        teile = zeile.rsplit(None, 1)
        if len(teile) == 2 and teile[1].count("_") >= 2 and not zeile.startswith("─"):
            ids.append(teile[1])
    return ids


def main() -> None:
    p = argparse.ArgumentParser(
        description="Loescht laufende Chat-Sessions, damit die naechste Nachricht die aktuelle SOUL.md laedt"
    )
    p.add_argument(
        "--source",
        choices=CHAT_QUELLEN,
        help="Nur eine Quelle statt aller Chat-Kanaele (discord, telegram, whatsapp, slack)",
    )
    p.add_argument("--yes", action="store_true", help="Ohne Rueckfrage loeschen")
    args = p.parse_args()

    quellen = [args.source] if args.source else list(CHAT_QUELLEN)

    gefunden: dict[str, list[str]] = {}
    for quelle in quellen:
        ids = sitzungen_je_quelle(quelle)
        if ids:
            gefunden[quelle] = ids

    if not gefunden:
        print("Keine laufenden Chat-Sessions gefunden, nichts zu tun.")
        return

    for quelle, ids in gefunden.items():
        print(f"{quelle}: {len(ids)} Session(en) — {', '.join(ids)}")

    if not args.yes:
        antwort = input("Diese Sessions loeschen? [y/N] ").strip().lower()
        if antwort != "y":
            print("Abgebrochen, nichts geloescht.")
            return

    for quelle, ids in gefunden.items():
        for sid in ids:
            out = ssh(f"docker exec {CONTAINER} hermes sessions delete {sid} --yes")
            status = "OK" if "Deleted session" in out else out.strip()[:120]
            print(f"  {quelle}/{sid}: {status}")

    print(
        "Fertig. Die naechste Nachricht in jedem Kanal startet frisch mit der aktuellen SOUL.md."
    )


if __name__ == "__main__":
    main()
