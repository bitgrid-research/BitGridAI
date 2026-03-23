"""
ShellyAdapter — Shelly Plug S (Gen 1) als Miner-Relay via MQTT.

Subscribed zu Shelly-MQTT-Topics:
  shellies/{device_id}/relay/0/power   → miner_power_w (W)
  shellies/{device_id}/relay/0         → Relay-Status (on/off)

publish_relay() konvertiert 'ON'/'OFF' → 'on'/'off' (Shelly-Protokoll).
"""

from __future__ import annotations

import logging
import os

from src.core.signals import Signal
from .mqtt_client import MqttClient
from .telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)

_BASE = "shellies"


class ShellyAdapter:
    """
    Liest Shelly Plug S MQTT-Daten und speist TelemetryIngest.
    Stellt publish_relay() für ActuationWriter bereit.
    """

    def __init__(
        self,
        mqtt: MqttClient,
        ingest: TelemetryIngest,
        device_id: str | None = None,
    ) -> None:
        self._mqtt = mqtt
        self._ingest = ingest
        self._device_id = (
            device_id
            if device_id is not None
            else os.getenv("SHELLY_DEVICE_ID", "shellyplug-s-XXXXXX")
        )
        self._prefix = f"{_BASE}/{self._device_id}"

    # ------------------------------------------------------------------
    # Topics
    # ------------------------------------------------------------------

    @property
    def relay_command_topic(self) -> str:
        return f"{self._prefix}/relay/0/command"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def register(self) -> None:
        self._mqtt.subscribe(f"{self._prefix}/relay/0/power", self._on_power)
        self._mqtt.subscribe(f"{self._prefix}/relay/0", self._on_relay_status)
        log.info(
            "ShellyAdapter registriert — %s | Relay: %s",
            self._device_id,
            self.relay_command_topic,
        )

    # ------------------------------------------------------------------
    # Publish (für ActuationWriter)
    # ------------------------------------------------------------------

    def publish_relay(self, topic: str, payload: str) -> None:
        """Konvertiert 'ON'/'OFF' → 'on'/'off' (Shelly-Protokoll)."""
        self._mqtt.publish(topic, payload.lower())
        log.info("Shelly Relay: %s → %r", topic, payload.lower())

    # ------------------------------------------------------------------
    # MQTT-Callbacks
    # ------------------------------------------------------------------

    def _on_power(self, topic: str, payload: str) -> None:
        try:
            watts = float(payload)
            self._ingest.update(
                Signal.MINER_POWER_W, watts, source=f"shelly:{self._device_id}"
            )
            log.debug("Shelly Leistung: %.1f W", watts)
        except ValueError:
            log.warning("Shelly ungültige Power-Payload: %r", payload)

    def _on_relay_status(self, topic: str, payload: str) -> None:
        log.debug("Shelly Relay-Status: %s", payload)
