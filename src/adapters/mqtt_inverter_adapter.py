"""
MqttInverterAdapter — generischer PV-Wechselrichter über MQTT.

Funktioniert mit ESPHome-Bridge, Home Assistant MQTT,
Solarman-to-MQTT, eigener ESPHome-Modbus-Firmware.
"""

from __future__ import annotations

import logging
import os

from src.core.signals import Signal
from .mqtt_client import MqttClient
from .telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)


class MqttInverterAdapter:
    """
    Liest PV-Leistung von einem MQTT-Topic → pv_power_w.

    scale: Skalierungsfaktor (z.B. 1000.0 wenn Topic in kW statt W).
    """

    def __init__(
        self,
        mqtt: MqttClient,
        ingest: TelemetryIngest,
        topic: str | None = None,
        scale: float | None = None,
    ) -> None:
        self._mqtt = mqtt
        self._ingest = ingest
        self._topic = topic if topic is not None else os.getenv(
            "PV_MQTT_TOPIC", "bitgrid/home/pv_inverter/power_w"
        )
        self._scale = scale if scale is not None else float(os.getenv("PV_MQTT_SCALE", "1.0"))

    def register(self) -> None:
        self._mqtt.subscribe(self._topic, self._on_message)
        log.info(
            "MqttInverterAdapter registriert — Topic: %s (scale=%.1f)",
            self._topic, self._scale,
        )

    def _on_message(self, topic: str, payload: str) -> None:
        try:
            raw = float(payload)
        except ValueError:
            log.warning("Wechselrichter ungültige Payload: %r", payload)
            return

        watts = raw * self._scale
        self._ingest.update(Signal.PV_POWER_W, watts, source=f"mqtt_inverter:{topic}")
        log.debug("PV: %.0f W", watts)
