#!/usr/bin/env python3
"""
Weist HA-Geraeten einen Bereich (Area) zu ueber die WebSocket-API
(config/device_registry/update).

Einmal-Migration (25.08.2026): 6 Geraete hatten in HAs Bereichs-Register
KEINEN Raum zugewiesen, obwohl packages/devices.yaml den Raum laengst
dokumentiert (Kommentarblock "Zuordnung Key -> Shelly-Slug -> Raum"). Live
per Template-API verifiziert (areas()/area_entities()), nicht aus dem
lokalen .storage-Spiegel uebernommen (der ist laut Projekt-Konvention
potenziell veraltet). Nutzer-Entscheidung 25.08.2026 zu den zwei offenen
Faellen: GX-10 (Compute-Server, vorher gar keinem Raum zugeordnet) ->
Schlafzimmer 1.

Standard ist **Dry-Run** (zeigt nur den Plan); mit ``--apply`` wird live
ausgefuehrt.

Token: aus --token, sonst $BITGRIDAI_HA_TOKEN, sonst aus .env.
Host:  aus --host, sonst UMBREL_HOST/HA_PORT aus .env.

  python scripts/ha_assign_areas.py            # Dry-Run
  python scripts/ha_assign_areas.py --apply     # ausfuehren
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import websockets

# Geraete-Friendly-Name (Praefix reicht) -> Ziel-Bereichsname (exakt wie in HA).
PLANNED_ASSIGNMENTS: tuple[tuple[str, str], ...] = (
    ("Waschmaschine", "Hauswirtschaftsraum"),
    ("Kuehlschraenke", "Hauswirtschaftsraum"),
    ("TV Wohnzimmer", "Wohnzimmer"),
    ("David TV", "Schlafzimmer 1"),
    ("Michael PC", "Büro"),
    ("GX-10", "Schlafzimmer 1"),
    # 25.08.2026: "David PC" (Friendly-Name live verifiziert, NICHT "PC
    # Schlafzimmer" wie der alte Kommentarblock in devices.yaml behauptet)
    # war faelschlich im Bereich "Schlafzimmer" statt "Schlafzimmer 1" —
    # Nutzer-Meldung "der ist im falschen Raum".
    ("David PC", "Schlafzimmer 1"),
)


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


def _load_host(cli_host: str | None) -> str:
    if cli_host:
        return cli_host
    env = os.environ.get("UMBREL_HOST")
    port = os.environ.get("HA_PORT", "8123")
    if not env:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("UMBREL_HOST="):
                    env = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("HA_PORT="):
                    port = line.split("=", 1)[1].strip().strip('"') or port
    if not env:
        raise SystemExit("Kein Host: --host oder UMBREL_HOST/.env setzen")
    return f"http://{env}:{port}"


def _ws_url(host: str) -> str:
    h = host.rstrip("/")
    if h.startswith("https://"):
        return "wss://" + h[len("https://") :] + "/api/websocket"
    if h.startswith("http://"):
        return "ws://" + h[len("http://") :] + "/api/websocket"
    return "ws://" + h + "/api/websocket"


async def _call(ws: websockets.WebSocketClientProtocol, msg_id: int, payload: dict) -> dict:
    await ws.send(json.dumps({"id": msg_id, **payload}))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id and resp.get("type") == "result":
            return resp


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
        areas_resp = await _call(ws, msg_id, {"type": "config/area_registry/list"})
        if not areas_resp.get("success"):
            print(f"area_registry/list fehlgeschlagen: {areas_resp}", file=sys.stderr)
            return 2
        area_by_name = {a["name"]: a["area_id"] for a in areas_resp["result"]}

        msg_id += 1
        devices_resp = await _call(ws, msg_id, {"type": "config/device_registry/list"})
        if not devices_resp.get("success"):
            print(f"device_registry/list fehlgeschlagen: {devices_resp}", file=sys.stderr)
            return 2
        devices = devices_resp["result"]

        print(f"{'Modus:':8s} {'APPLY' if apply else 'DRY-RUN'}   Host: {host}")
        print("-" * 78)
        ok = 0
        skipped = 0
        for name_prefix, target_area_name in PLANNED_ASSIGNMENTS:
            target_area_id = area_by_name.get(target_area_name)
            if not target_area_id:
                print(f"  ✗ Bereich nicht gefunden: {target_area_name!r} (übersprungen)")
                skipped += 1
                continue

            matches = [
                d
                for d in devices
                if (d.get("name_by_user") or d.get("name") or "").startswith(name_prefix)
            ]
            if len(matches) != 1:
                print(
                    f"  ✗ {name_prefix!r}: {len(matches)} Treffer statt 1 "
                    f"({[d.get('name_by_user') or d.get('name') for d in matches]}) — übersprungen"
                )
                skipped += 1
                continue

            device = matches[0]
            device_name = device.get("name_by_user") or device.get("name")
            current_area = device.get("area_id")
            if current_area == target_area_id:
                print(f"  = {device_name}: bereits in {target_area_name!r}")
                ok += 1
                continue

            if not apply:
                print(f"  → {device_name}  ⇒  {target_area_name}")
                ok += 1
                continue

            msg_id += 1
            r = await _call(
                ws,
                msg_id,
                {
                    "type": "config/device_registry/update",
                    "device_id": device["id"],
                    "area_id": target_area_id,
                },
            )
            if r.get("success"):
                print(f"  ✓ zugewiesen: {device_name} → {target_area_name}")
                ok += 1
            else:
                print(f"  ✗ FEHLER: {device_name}: {r.get('error')}", file=sys.stderr)
                skipped += 1

        print("-" * 78)
        verb = "ausgeführt" if apply else "geplant"
        print(f"{ok} Zuweisung(en) {verb}, {skipped} übersprungen.")
        if not apply and ok:
            print("→ Zum Ausführen erneut mit --apply starten.")
        return 0


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(description="HA-Geräten einen Bereich zuweisen")
    parser.add_argument(
        "--host",
        default=None,
        help="HA-Basis-URL, z.B. http://umbrel.local:8123 "
        "(Default aus UMBREL_HOST/HA_PORT in .env)",
    )
    parser.add_argument("--token", default=None)
    parser.add_argument("--apply", action="store_true", help="Zuweisungen live ausführen")
    args = parser.parse_args()

    host = _load_host(args.host)
    token = _load_token(args.token)
    rc = asyncio.run(_run(host, token, args.apply))
    sys.exit(rc)


if __name__ == "__main__":
    main()
