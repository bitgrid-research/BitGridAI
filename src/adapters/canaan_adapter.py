"""
CanaanAdapter — liest Temperatur und Hashrate vom Canaan Avalon Q via CGMiner-API.

CGMiner API: TCP-Socket Port 4028, JSON-Protokoll (Canaan-Firmware-kompatibel).
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time

from src.core.signals import Signal
from .telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)

_SOCKET_TIMEOUT_SEC = 5
_RECV_BUFFER = 4096


class CanaanAdapter:
    """Pollt den Canaan Avalon Q CGMiner-API und schreibt Werte in TelemetryIngest."""

    def __init__(
        self,
        ingest: TelemetryIngest,
        host: str | None = None,
        port: int | None = None,
        poll_interval_sec: float | None = None,
    ) -> None:
        self._ingest = ingest
        self._host = host if host is not None else os.getenv("MINER_HOST", "192.168.1.50")
        self._port = port if port is not None else int(os.getenv("MINER_API_PORT", "4028"))
        self._poll_interval_sec = (
            poll_interval_sec if poll_interval_sec is not None
            else float(os.getenv("CANAAN_POLL_INTERVAL_SEC", "10"))
        )
        self._running = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="canaan-poll"
        )
        self._thread.start()
        log.info("CanaanAdapter gestartet — %s:%s", self._host, self._port)

    def stop(self) -> None:
        self._running = False
        log.info("CanaanAdapter gestoppt")

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        while self._running:
            try:
                self._poll_once()
            except Exception as exc:
                log.warning("CGMiner-Poll fehlgeschlagen: %s", exc)
            time.sleep(self._poll_interval_sec)

    def _poll_once(self) -> None:
        raw = self._send_command({"command": "summary"})
        summary = raw.get("SUMMARY", [{}])[0]

        temp_c = self._parse_temp(summary)
        power_w = self._parse_power(summary)
        hashrate_th = self._parse_hashrate(summary)

        source = f"canaan_api:{self._host}"

        self._ingest.update(Signal.MINER_TEMP_C, temp_c, source=source)
        self._ingest.update(Signal.MINER_HEARTBEAT_AGE_SEC, 0.0, source=source)

        if power_w > 0:
            self._ingest.update(Signal.MINER_POWER_W, power_w, source=source)
        if hashrate_th > 0:
            self._ingest.update(Signal.MINER_HASHRATE_TH, hashrate_th, source=source)

        log.debug("Canaan: %.1f°C  %.0fW  %.1f TH/s", temp_c, power_w, hashrate_th)

    # ------------------------------------------------------------------
    # CGMiner TCP-Protokoll
    # ------------------------------------------------------------------

    def _send_command(self, cmd: dict) -> dict:
        with socket.create_connection(
            (self._host, self._port), timeout=_SOCKET_TIMEOUT_SEC
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
    # Canaan Avalon Q Feld-Mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_temp(summary: dict) -> float:
        for key in ("Max Temp", "Temperature"):
            val = summary.get(key)
            if val is not None:
                return float(val)
        log.warning("Canaan: kein Temperatur-Feld — nehme 999°C (Safety-Stop)")
        return 999.0

    @staticmethod
    def _parse_power(summary: dict) -> float:
        for key in ("Power", "Watts"):
            val = summary.get(key)
            if val is not None:
                return float(val)
        return 0.0

    @staticmethod
    def _parse_hashrate(summary: dict) -> float:
        for key in ("GHS 5s", "GHS av"):
            val = summary.get(key)
            if val is not None:
                return float(val) / 1000.0  # GH/s → TH/s
        return 0.0
