#!/usr/bin/env python3
"""
Benennt HA-Entities über die WebSocket-API um (entity_registry/update_entity).

Einmal-Migration: entfernt Serial-/IP-haltige Entity-IDs (SMA-Wechselrichter,
AC-ELWA-Heizstab) zugunsten serienfreier Namen, passend zur bereinigten
Repo-Config. Standard ist **Dry-Run** (zeigt nur den Plan); mit ``--apply``
werden die Renames live ausgeführt.

Token: aus --token, sonst $BITGRIDAI_HA_TOKEN, sonst aus .env.
Host:  aus --host (Default http://192.168.178.62:8123).

  python scripts/ha_rename_entities.py            # Dry-Run
  python scripts/ha_rename_entities.py --apply     # ausführen
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import websockets

# Regelbasierte Substitutionen: Serial-/IP-haltige Fragmente → serienfreie Namen.
# Werden auf JEDE entity_id der Registry angewandt (Reihenfolge beachtet).
SUBSTITUTIONS: tuple[tuple[str, str], ...] = (
    ("sn_3012953672", "sma_tripower"),  # SMA Sunny Tripower (PV)
    ("sn_3015995559", "sma_storage"),  # SMA Sunny Boy Storage (Batterie)
    ("_192_168_178_58", ""),  # AC ELWA 2 Heizstab — lokale IP im Namen
)


def compute_new_id(entity_id: str) -> str:
    """Wendet alle Substitutionen an; gibt die bereinigte entity_id zurück."""
    new = entity_id
    for old_frag, new_frag in SUBSTITUTIONS:
        new = new.replace(old_frag, new_frag)
    return new


def _load_token(cli_token: str | None) -> str:
    if cli_token:
        return cli_token
    env = os.environ.get("BITGRIDAI_HA_TOKEN") or os.environ.get("HA_TOKEN")
    if env:
        return env
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            for key in ("BITGRIDAI_HA_TOKEN", "HA_TOKEN"):
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("Kein Token: --token oder BITGRIDAI_HA_TOKEN/.env setzen")


def _ws_url(host: str) -> str:
    h = host.rstrip("/")
    if h.startswith("https://"):
        return "wss://" + h[len("https://") :] + "/api/websocket"
    if h.startswith("http://"):
        return "ws://" + h[len("http://") :] + "/api/websocket"
    return "ws://" + h + "/api/websocket"


async def _run(host: str, token: str, apply: bool) -> int:
    url = _ws_url(host)
    async with websockets.connect(url, max_size=8 * 1024 * 1024) as ws:
        hello = json.loads(await ws.recv())
        if hello.get("type") != "auth_required":
            print(f"Unerwartete Begrüßung: {hello}", file=sys.stderr)
            return 2
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth = json.loads(await ws.recv())
        if auth.get("type") != "auth_ok":
            print(f"Auth fehlgeschlagen: {auth}", file=sys.stderr)
            return 2

        msg_id = 1
        await ws.send(json.dumps({"id": msg_id, "type": "config/entity_registry/list"}))
        while True:
            resp = json.loads(await ws.recv())
            if resp.get("id") == msg_id and resp.get("type") == "result":
                break
        if not resp.get("success"):
            print(f"entity_registry/list fehlgeschlagen: {resp}", file=sys.stderr)
            return 2
        existing = {e["entity_id"] for e in resp["result"]}
        planned = [
            (old, compute_new_id(old))
            for old in sorted(existing)
            if compute_new_id(old) != old
        ]

        print(f"{'Modus:':8s} {'APPLY' if apply else 'DRY-RUN'}   Host: {host}")
        print(f"Betroffen: {len(planned)} Entity(s)")
        print("-" * 78)
        ok = 0
        skipped = 0
        for old, new in planned:
            if new in existing:
                print(f"  ⚠ Ziel belegt:     {new} (übersprungen)")
                skipped += 1
                continue

            if not apply:
                print(f"  → {old}\n     ⇒ {new}")
                ok += 1
                continue

            msg_id += 1
            await ws.send(
                json.dumps(
                    {
                        "id": msg_id,
                        "type": "config/entity_registry/update",
                        "entity_id": old,
                        "new_entity_id": new,
                    }
                )
            )
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == msg_id and r.get("type") == "result":
                    break
            if r.get("success"):
                print(f"  ✓ umbenannt: {old} → {new}")
                ok += 1
            else:
                print(f"  ✗ FEHLER:   {old}: {r.get('error')}", file=sys.stderr)
                skipped += 1

        print("-" * 78)
        verb = "ausgeführt" if apply else "geplant"
        print(f"{ok} Rename(s) {verb}, {skipped} übersprungen.")
        if not apply and ok:
            print("→ Zum Ausführen erneut mit --apply starten.")
        return 0


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(description="HA-Entities serienfrei umbenennen")
    parser.add_argument("--host", default="http://192.168.178.62:8123")
    parser.add_argument("--token", default=None)
    parser.add_argument("--apply", action="store_true", help="Renames live ausführen")
    args = parser.parse_args()

    token = _load_token(args.token)
    rc = asyncio.run(_run(args.host, token, args.apply))
    sys.exit(rc)


if __name__ == "__main__":
    main()
