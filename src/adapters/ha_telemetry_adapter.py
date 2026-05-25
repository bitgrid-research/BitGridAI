"""
HaTelemetryAdapter — polls Home Assistant REST API and feeds TelemetryIngest.

Bridging layer: HA sensor states → BitGridAI signal cache.
Runs in a background thread, polls every poll_interval_sec seconds.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import urllib.request
import urllib.error
import json

from src.adapters.telemetry_ingest import TelemetryIngest
from src.core.signals import Signal

log = logging.getLogger(__name__)

# Map HA entity_id → (BitGridAI Signal, unit_factor)
# unit_factor: multiply HA value by this to get SI unit
_SENSOR_MAP: dict[str, tuple[Signal, float]] = {
    "sensor.pv_power_w": (Signal.PV_POWER_W, 1.0),
    "sensor.house_load_w": (Signal.HOUSE_LOAD_W, 1.0),
    "sensor.grid_import_w": (Signal.GRID_IMPORT_W, 1.0),
    "sensor.grid_export_w": (Signal.GRID_EXPORT_W, 1.0),
    "sensor.battery_soc_pct": (Signal.BATTERY_SOC_PCT, 1.0),
    "sensor.miner_max_chip_temp_c": (Signal.MINER_TEMP_C, 1.0),
    "sensor.miner_total_power_w": (Signal.MINER_POWER_W, 1.0),
}

_MINER_TEMP_ENTITY = "sensor.miner_max_chip_temp_c"


class HaTelemetryAdapter:
    """Polls HA REST API and writes values into TelemetryIngest."""

    def __init__(
        self,
        ha_url: str,
        ha_token: str,
        ingest: TelemetryIngest,
        poll_interval_sec: float = 30.0,
    ) -> None:
        self._url = ha_url.rstrip("/")
        self._token = ha_token
        self._ingest = ingest
        self._interval = poll_interval_sec
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="ha-telemetry"
        )
        self._thread.start()
        log.info(
            "HaTelemetryAdapter gestartet — %s (alle %.0fs)", self._url, self._interval
        )

    def _fetch_states(self, entity_ids: list[str]) -> dict[str, Any]:
        results: dict[str, Any] = {}
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        for eid in entity_ids:
            try:
                req = urllib.request.Request(
                    f"{self._url}/api/states/{eid}", headers=headers
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                    results[eid] = data.get("state")
            except Exception:
                pass
        return results

    def _loop(self) -> None:
        entity_ids = list(_SENSOR_MAP.keys())
        while True:
            try:
                states = self._fetch_states(entity_ids)
                miner_alive = False

                for eid, (signal, factor) in _SENSOR_MAP.items():
                    raw = states.get(eid)
                    if raw is None or raw in ("unavailable", "unknown", ""):
                        continue
                    try:
                        value = float(raw) * factor
                        self._ingest.update(signal, value)
                        if eid == _MINER_TEMP_ENTITY:
                            miner_alive = True
                    except (ValueError, TypeError):
                        pass

                # Miner heartbeat: 0 = alive (just saw a valid temp reading)
                if miner_alive:
                    self._ingest.update(Signal.MINER_HEARTBEAT_AGE_SEC, 0.0)

            except Exception as exc:
                log.warning("HaTelemetryAdapter poll-Fehler: %s", exc)

            time.sleep(self._interval)
