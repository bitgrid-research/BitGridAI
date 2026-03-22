"""
Standalone Miner-Poller für den Docker-Container.

Liest MINER_HOSTS aus der Umgebung, pollt beide Avalon-Miner per CGMiner API
und published die Ergebnisse auf MQTT.

MINER_HOSTS Format: "ip:port:worker_id,ip:port:worker_id"
  Beispiel: "192.168.178.69:4028:001,192.168.178.70:4028:002"
"""

import json
import logging
import os
import socket
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from typing import Any

# .env laden falls vorhanden (lokaler Betrieb ohne Docker)
_env_file = Path(__file__).parents[2] / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            value = value.split("#")[0].strip()
            os.environ.setdefault(key.strip(), value)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
LOCATION = os.getenv("MQTT_LOCATION", "home")
POLL_INTERVAL = float(os.getenv("CANAAN_POLL_INTERVAL_SEC", "30"))
SOCKET_TIMEOUT = 5


def parse_hosts() -> list[tuple[str, int, str]]:
    raw = os.getenv("MINER_HOSTS", "192.168.178.69:4028:001")
    result = []
    for entry in raw.split(","):
        parts = entry.strip().split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 4028
        worker_id = parts[2] if len(parts) > 2 else host.replace(".", "_")
        result.append((host, port, worker_id))
    return result


def cgminer_cmd(host: str, port: int, cmd: dict[str, str]) -> dict[str, Any]:
    with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT) as s:
        s.sendall(json.dumps(cmd).encode())
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\x00" in chunk:
                break
    result: dict[str, Any] = json.loads(data.rstrip(b"\x00"))
    return result


def poll_miner(host: str, port: int, worker_id: str) -> dict[str, Any]:
    try:
        summary: dict[str, Any] = cgminer_cmd(host, port, {"command": "summary"}).get("SUMMARY", [{}])[0]
        pools: list[dict[str, Any]] = cgminer_cmd(host, port, {"command": "pools"}).get("POOLS", [{}])

        mhs = summary.get("MHS av") or summary.get("MHS 5s") or 0.0
        hashrate_ths = float(mhs) / 1_000_000.0

        accepted = int(summary.get("Accepted", 0))
        rejected = int(summary.get("Rejected", 0))
        hw_errors = int(summary.get("Hardware Errors", 0))
        uptime_sec = int(summary.get("Elapsed", 0))

        active_pool: dict[str, Any] = next((p for p in pools if p.get("Status") == "Alive"), {})
        pool_url = active_pool.get("URL", "")

        if hashrate_ths > 0:
            mode = "RUNNING"
        else:
            mode = "IDLE"

        return {
            "worker_id": worker_id,
            "status": "online",
            "mode": mode,
            "hashrate_ths": round(hashrate_ths, 2),
            "accepted": accepted,
            "rejected": rejected,
            "hw_errors": hw_errors,
            "uptime_sec": uptime_sec,
            "pool": pool_url,
        }
    except Exception as exc:
        log.warning("Miner %s nicht erreichbar: %s", host, exc)
        return {
            "worker_id": worker_id,
            "status": "offline",
            "mode": "OFFLINE",
            "hashrate_ths": 0.0,
            "accepted": 0,
            "rejected": 0,
            "hw_errors": 0,
            "uptime_sec": 0,
            "pool": "",
        }


def publish(client: mqtt.Client, worker_id: str, data: dict[str, Any]) -> None:
    base = f"bitgrid/{LOCATION}/miner/{worker_id}"
    for key, value in data.items():
        if key == "worker_id":
            continue
        client.publish(f"{base}/{key}", str(value), retain=True)
    log.info(
        "Miner %s | %s | %.2f TH/s | acc=%d rej=%d",
        worker_id,
        data["mode"],
        data["hashrate_ths"],
        data["accepted"],
        data["rejected"],
    )


def main() -> None:
    hosts = parse_hosts()
    log.info("Starte Miner-Poller: %d Miner, Intervall %.0fs", len(hosts), POLL_INTERVAL)

    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    while True:
        for host, port, worker_id in hosts:
            data = poll_miner(host, port, worker_id)
            publish(client, worker_id, data)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
