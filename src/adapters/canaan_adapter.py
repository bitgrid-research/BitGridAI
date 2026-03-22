"""
CanaanAdapter — liest Temperatur und Hashrate von Canaan Avalon Minern via CGMiner-API.

Unterstützt mehrere Miner (multi-host). Pro Miner werden individuelle MQTT-Topics
published; Aggregat-Werte (Worst-case Temp, Summe Hashrate) gehen in TelemetryIngest.

CGMiner API: TCP-Socket Port 4028, JSON-Protokoll (Canaan-Firmware-kompatibel).

MQTT-Topics pro Miner:
  bitgrid/{location}/miner/{worker_id}/hashrate_ths
  bitgrid/{location}/miner/{worker_id}/accepted
  bitgrid/{location}/miner/{worker_id}/rejected
  bitgrid/{location}/miner/{worker_id}/hw_errors
  bitgrid/{location}/miner/{worker_id}/status
  bitgrid/{location}/miner/{worker_id}/uptime_sec
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional

from src.core.signals import Signal
from .telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)

_SOCKET_TIMEOUT_SEC = 5
_RECV_BUFFER = 4096


@dataclass
class MinerHost:
    host: str
    port: int = 4028
    worker_id: str = ""

    def __post_init__(self) -> None:
        if not self.worker_id:
            self.worker_id = self.host.replace(".", "_")


@dataclass
class MinerReading:
    worker_id: str
    host: str
    hashrate_ths: float
    temp_c: float
    accepted: int
    rejected: int
    hw_errors: int
    uptime_sec: int
    status: str  # "alive" | "dead" | "unknown"


class CanaanAdapter:
    """Pollt Canaan Avalon Miner CGMiner-API und schreibt Werte in TelemetryIngest."""

    def __init__(
        self,
        ingest: TelemetryIngest,
        hosts: list[MinerHost] | None = None,
        poll_interval_sec: float | None = None,
        mqtt_client: object | None = None,
        mqtt_location: str | None = None,
    ) -> None:
        self._ingest = ingest
        self._mqtt = mqtt_client
        self._location = mqtt_location or os.getenv("MQTT_LOCATION", "home")
        self._poll_interval_sec = (
            poll_interval_sec
            if poll_interval_sec is not None
            else float(os.getenv("CANAAN_POLL_INTERVAL_SEC", "30"))
        )
        self._hosts = hosts or self._hosts_from_env()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    @staticmethod
    def _hosts_from_env() -> list[MinerHost]:
        """Fallback: MINER_HOST / MINER_API_PORT für Einzel-Miner-Betrieb."""
        host = os.getenv("MINER_HOST", "192.168.1.50")
        port = int(os.getenv("MINER_API_PORT", "4028"))
        worker_id = os.getenv("MINER_WORKER_ID", "")
        return [MinerHost(host=host, port=port, worker_id=worker_id)]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="canaan-poll"
        )
        self._thread.start()
        log.info(
            "CanaanAdapter gestartet — %d Miner: %s",
            len(self._hosts),
            [h.host for h in self._hosts],
        )

    def stop(self) -> None:
        self._running = False
        log.info("CanaanAdapter gestoppt")

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        while self._running:
            try:
                self._poll_all()
            except Exception as exc:
                log.warning("CGMiner-Poll fehlgeschlagen: %s", exc)
            time.sleep(self._poll_interval_sec)

    def _poll_all(self) -> None:
        readings: list[MinerReading] = []
        last_poll_ts = time.monotonic()

        for miner in self._hosts:
            reading = self._poll_one(miner)
            readings.append(reading)
            if self._mqtt:
                self._publish_miner(reading)

        # Aggregat-Werte → TelemetryIngest (Worst-case / Summe)
        alive = [r for r in readings if r.status == "alive"]

        heartbeat_age = time.monotonic() - last_poll_ts
        source = "canaan_api"

        if alive:
            max_temp = max(r.temp_c for r in alive)
            total_hashrate_th = sum(r.hashrate_ths for r in alive)

            self._ingest.update(Signal.MINER_TEMP_C, max_temp, source=source)
            self._ingest.update(Signal.MINER_HEARTBEAT_AGE_SEC, heartbeat_age, source=source)
            if total_hashrate_th > 0:
                self._ingest.update(Signal.MINER_HASHRATE_TH, total_hashrate_th, source=source)

            log.debug(
                "Aggregate: %.1f TH/s | max_temp=%.1f°C | alive=%d/%d",
                total_hashrate_th,
                max_temp,
                len(alive),
                len(readings),
            )
        else:
            # Alle Miner tot — Safety: hohe Heartbeat-Age signalisieren
            log.warning("Alle Miner nicht erreichbar")
            self._ingest.update(
                Signal.MINER_HEARTBEAT_AGE_SEC, 9999.0, source=source
            )

    def _poll_one(self, miner: MinerHost) -> MinerReading:
        try:
            summary = self._send_command(miner, {"command": "summary"}).get("SUMMARY", [{}])[0]
            devs = self._send_command(miner, {"command": "devs"}).get("DEVS", [{}])[0]
            return MinerReading(
                worker_id=miner.worker_id,
                host=miner.host,
                hashrate_ths=self._parse_hashrate_ths(summary),
                temp_c=self._parse_temp(devs, summary),
                accepted=int(summary.get("Accepted", 0)),
                rejected=int(summary.get("Rejected", 0)),
                hw_errors=int(summary.get("Hardware Errors", 0)),
                uptime_sec=int(summary.get("Elapsed", 0)),
                status="alive",
            )
        except Exception as exc:
            log.warning("Miner %s nicht erreichbar: %s", miner.host, exc)
            return MinerReading(
                worker_id=miner.worker_id,
                host=miner.host,
                hashrate_ths=0.0,
                temp_c=0.0,
                accepted=0,
                rejected=0,
                hw_errors=0,
                uptime_sec=0,
                status="dead",
            )

    # ------------------------------------------------------------------
    # MQTT Publishing
    # ------------------------------------------------------------------

    def _publish_miner(self, r: MinerReading) -> None:
        base = f"bitgrid/{self._location}/miner/{r.worker_id}"
        assert self._mqtt is not None
        self._mqtt.publish(f"{base}/hashrate_ths", str(round(r.hashrate_ths, 2)))
        self._mqtt.publish(f"{base}/accepted", str(r.accepted))
        self._mqtt.publish(f"{base}/rejected", str(r.rejected))
        self._mqtt.publish(f"{base}/hw_errors", str(r.hw_errors))
        self._mqtt.publish(f"{base}/uptime_sec", str(r.uptime_sec))
        self._mqtt.publish(f"{base}/status", r.status)
        if r.temp_c > 0:
            self._mqtt.publish(f"{base}/temp_c", str(round(r.temp_c, 1)))

    # ------------------------------------------------------------------
    # CGMiner TCP-Protokoll
    # ------------------------------------------------------------------

    def _send_command(self, miner: MinerHost, cmd: dict) -> dict:
        with socket.create_connection(
            (miner.host, miner.port), timeout=_SOCKET_TIMEOUT_SEC
        ) as sock:
            sock.sendall(json.dumps(cmd).encode())
            raw = b""
            while True:
                chunk = sock.recv(_RECV_BUFFER)
                if not chunk:
                    break
                raw += chunk
                if b"\x00" in chunk:
                    break
        return json.loads(raw.rstrip(b"\x00"))

    # ------------------------------------------------------------------
    # Canaan Avalon Feld-Mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_hashrate_ths(summary: dict) -> float:
        # Avalon Q liefert MHS (Megahashes/s), nicht GHS
        for key in ("MHS av", "MHS 5s", "GHS av", "GHS 5s"):
            val = summary.get(key)
            if val is not None:
                mhs = float(val)
                # GHS → in TH/s: / 1000; MHS → TH/s: / 1_000_000
                if key.startswith("MHS"):
                    return mhs / 1_000_000.0
                else:
                    return mhs / 1_000.0
        return 0.0

    @staticmethod
    def _parse_temp(devs: dict, summary: dict) -> float:
        # Avalon Q: Temperatur kommt aus `devs`, Fallback `summary`
        for source in (devs, summary):
            for key in ("Temperature", "Max Temp", "Temp"):
                val = source.get(key)
                if val is not None:
                    t = float(val)
                    if t > 0:
                        return t
        # 0.0 = Temp-Feld vorhanden aber leer (Avalon-Eigenheit) — kein Safety-Stop
        log.debug("Canaan: kein Temperaturwert — Feld vorhanden aber 0.0")
        return 0.0
