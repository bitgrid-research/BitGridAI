"""
BitaxeAdapter — liest Telemetrie vom Bitaxe via AxeOS HTTP-API.

AxeOS REST-Endpoint: GET http://{host}/api/system/info
Kein Login, kein spezielles Protokoll — einfaches HTTP-GET.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from urllib.request import Request, urlopen

from src.core.signals import Signal
from .telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)

_HTTP_TIMEOUT_SEC = 5
_API_PATH = "/api/system/info"


class BitaxeAdapter:
    """Pollt AxeOS HTTP-API und schreibt Werte in TelemetryIngest."""

    def __init__(
        self,
        ingest: TelemetryIngest,
        host: str | None = None,
        port: int | None = None,
        poll_interval_sec: float | None = None,
    ) -> None:
        self._ingest = ingest
        self._host = host if host is not None else os.getenv("BITAXE_HOST", "192.168.1.60")
        self._port = port if port is not None else int(os.getenv("BITAXE_PORT", "80"))
        self._poll_interval_sec = (
            poll_interval_sec if poll_interval_sec is not None
            else float(os.getenv("BITAXE_POLL_INTERVAL_SEC", "10"))
        )
        self._url = f"http://{self._host}:{self._port}{_API_PATH}"
        self._running = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="bitaxe-poll"
        )
        self._thread.start()
        log.info("BitaxeAdapter gestartet — %s", self._url)

    def stop(self) -> None:
        self._running = False
        log.info("BitaxeAdapter gestoppt")

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        while self._running:
            try:
                self._poll_once()
            except Exception as exc:
                log.warning("AxeOS-Poll fehlgeschlagen: %s", exc)
            time.sleep(self._poll_interval_sec)

    def _poll_once(self) -> None:
        data = self._fetch()
        source = f"axeos:{self._host}"

        temp_c = self._parse_temp(data)
        power_w = float(data.get("power", 0.0) or 0.0)
        hashrate_gh = float(data.get("hashRate", 0.0) or 0.0)

        self._ingest.update(Signal.MINER_TEMP_C, temp_c, source=source)
        self._ingest.update(Signal.MINER_HEARTBEAT_AGE_SEC, 0.0, source=source)

        if power_w > 0:
            self._ingest.update(Signal.MINER_POWER_W, power_w, source=source)
        if hashrate_gh > 0:
            self._ingest.update(Signal.MINER_HASHRATE_GH, hashrate_gh, source=source)

        log.debug(
            "Bitaxe: %.1f°C  %.1fW  %.0f GH/s  mining=%s",
            temp_c, power_w, hashrate_gh, data.get("isMining", "?"),
        )

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _fetch(self) -> dict:
        req = Request(self._url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=_HTTP_TIMEOUT_SEC) as resp:
            return json.loads(resp.read())

    # ------------------------------------------------------------------
    # Feld-Mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_temp(data: dict) -> float:
        val = data.get("temp")
        if val is not None:
            return float(val)
        log.warning("Bitaxe: kein 'temp'-Feld — nehme 999°C (Safety-Stop)")
        return 999.0
