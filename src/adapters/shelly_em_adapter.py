"""
ShellyEMAdapter — Shelly EM / 3EM als Netz- und Hauszähler.

Shelly EM (1 Kanal):  Kanal 0 = Netz (positiv=Import, negativ=Export)
Shelly 3EM (3 Phasen): alle Phasen werden summiert

Liefert: grid_import_w, grid_export_w
"""

from __future__ import annotations

import logging
import os

from src.core.signals import Signal
from .mqtt_client import MqttClient
from .telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)

_BASE = "shellies"


class ShellyEMAdapter:
    """
    Liest Netzleistung vom Shelly EM oder 3EM.

    Liefert grid_import_w und grid_export_w an TelemetryIngest.
    """

    def __init__(
        self,
        mqtt: MqttClient,
        ingest: TelemetryIngest,
        device_id: str | None = None,
        channels: int | None = None,
    ) -> None:
        self._mqtt = mqtt
        self._ingest = ingest
        self._device_id = device_id if device_id is not None else os.getenv(
            "SHELLY_EM_DEVICE_ID", "shellyem-XXXXXX"
        )
        self._channels = channels if channels is not None else int(
            os.getenv("SHELLY_EM_CHANNELS", "1")
        )
        self._phase_power: dict[int, float] = {}

        if self._channels == 3:
            self._prefix = f"{_BASE}/shellytriphase-{self._device_id.split('-', 1)[-1]}"
        else:
            self._prefix = f"{_BASE}/{self._device_id}"

    def register(self) -> None:
        for ch in range(self._channels):
            topic = f"{self._prefix}/emeter/{ch}/power"
            self._mqtt.subscribe(topic, self._make_channel_callback(ch))
        log.info(
            "ShellyEMAdapter registriert — %s (%d Kanal/Kanäle)",
            self._device_id, self._channels,
        )

    def _make_channel_callback(self, channel: int):
        """Erzeugt einen Callback für den gegebenen Kanal."""
        def callback(topic: str, payload: str) -> None:
            try:
                watts = float(payload)
            except ValueError:
                log.warning("ShellyEM ungültige Payload auf %s: %r", topic, payload)
                return

            source = f"shelly_em:{self._device_id}:ch{channel}"

            if self._channels == 1:
                self._publish_grid(watts, source)
            else:
                self._phase_power[channel] = watts
                if len(self._phase_power) == 3:
                    self._publish_grid(sum(self._phase_power.values()), source)

        return callback

    def _publish_grid(self, watts: float, source: str) -> None:
        if watts >= 0:
            self._ingest.update(Signal.GRID_IMPORT_W, watts, source=source)
            self._ingest.update(Signal.GRID_EXPORT_W, 0.0, source=source)
        else:
            self._ingest.update(Signal.GRID_IMPORT_W, 0.0, source=source)
            self._ingest.update(Signal.GRID_EXPORT_W, abs(watts), source=source)

        log.debug("ShellyEM Netz: %.1f W (import=%.0f export=%.0f)",
                  watts, max(watts, 0), max(-watts, 0))
