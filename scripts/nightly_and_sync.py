"""
nightly_and_sync.py -- taeglicher Wrapper um src.data.nightly.

Behebt zwei Luecken, die am 23.07.2026 gefunden wurden:
1. src.data.nightly liest UMBREL_HOST/HA_TOKEN nur aus os.environ, nicht aus
   .env direkt -- ohne explizites Laden bleibt der HA-Sync leer.
2. Der erzeugte Faktenbericht landet lokal (vault/2026/07/...), nicht im
   tatsaechlichen Obsidian-Vault auf Umbrel, den Neo/Hermes liest.

Gedacht fuer einen taeglichen Windows Scheduled Task (00:20 lokal = UTC auf
diesem Rechner). Bewusst kein Ersatz fuer eine Umbrel-seitige Pipeline,
nur die kurzfristige Absicherung fuer die Urlaubswoche.
"""

from __future__ import annotations

import base64
import logging
import os
import shlex
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
# /opt/data/vault ist im hermes-agent-Container ausdruecklich read-only
# gemountet (siehe SOUL.md). Der tatsaechlich beschreibbare Pfad ist der
# Host-Pfad hinter dem Bind-Mount (docker inspect hermes-agent_web_1),
# direkt ueber SSH auf dem Umbrel-Host, nicht ueber docker exec.
REMOTE_VAULT_DIR = (
    "/home/umbrel/umbrel/app-data/obsidian/data/config/"
    "BitGridAI_Obisdian_RAG_MVP/BitGridAI_MVP/database_exploration/2026/07"
)

log = logging.getLogger("nightly_and_sync")


def _ssh_run(
    cmd: str, host: str, user: str, sudo_pass: str, timeout: int = 120
) -> tuple[str, int]:
    remote = "sudo -S -p '' bash -c " + shlex.quote(cmd)
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", f"{user}@{host}", remote],
        input=f"{sudo_pass}\n",
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    out = "\n".join(
        line for line in (r.stdout or "").splitlines() if not line.startswith("[sudo]")
    )
    if r.returncode != 0:
        out += f"\n[STDERR]\n{r.stderr}"
    return out, r.returncode


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    load_dotenv(REPO_ROOT / ".env")

    yesterday = date.today() - timedelta(days=1)
    log.info("Starte nightly.py fuer %s", yesterday.isoformat())

    result = subprocess.run(
        [sys.executable, "-m", "src.data.nightly"],
        cwd=REPO_ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    log.info(result.stdout)
    if result.returncode != 0:
        log.error("nightly.py Exit-Code %s: %s", result.returncode, result.stderr)
        return

    local_file = (
        REPO_ROOT
        / "vault"
        / str(yesterday.year)
        / f"{yesterday.month:02d}"
        / f"{yesterday.isoformat()}_fakten.md"
    )
    if not local_file.exists():
        log.error("Erwartete lokale Datei fehlt: %s", local_file)
        return

    content = local_file.read_bytes()
    log.info("Lokale Datei gefunden: %s (%d Bytes)", local_file, len(content))

    host = (
        os.environ.get("UMBREL_HOST_GIGI") or os.environ.get("UMBREL_HOST", "")
    ).rstrip("/")
    user = os.environ.get("UMBREL_USER_GIGI", "umbrel")
    sudo_pass = os.environ.get("UMBREL_SUDO_PASS_GIGI") or os.environ.get(
        "UMBREL_SUDO_PASS", ""
    )
    if not host or not sudo_pass:
        log.error("UMBREL_HOST_GIGI/UMBREL_SUDO_PASS_GIGI fehlen, kein Sync moeglich")
        return

    b64 = base64.b64encode(content).decode("ascii")
    remote_path = f"{REMOTE_VAULT_DIR}/{local_file.name}"
    cmd = f"echo {b64} | base64 -d > {remote_path} && chown umbrel:umbrel {remote_path}"
    out, code = _ssh_run(cmd, host, user, sudo_pass)
    if code != 0:
        log.error("Uebertragung fehlgeschlagen (Exit %d): %s", code, out)
        return
    verify, vcode = _ssh_run(f"wc -c < {remote_path}", host, user, sudo_pass)
    if vcode != 0 or str(len(content)) not in verify:
        log.error(
            "Verifikation fehlgeschlagen: erwartet %d Bytes, Host meldet: %s",
            len(content),
            verify,
        )
        return
    log.info(
        "Verifiziert auf Umbrel: %s (%s Bytes bestaetigt)", remote_path, verify.strip()
    )


if __name__ == "__main__":
    main()
