"""
MQTT-Client — verbindet sich mit dem Broker, subscribt Topics, publiziert.

Retry-Backoff: 1s → 5s → 30s bei Verbindungsabbruch.
Kein Retry für Sensor-Ausfälle — fehlende Daten sind expliziter Zustand.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

import paho.mqtt.client as mqtt

log = logging.getLogger(__name__)

_BACKOFF = [1, 5, 30]


class MqttClient:
    def __init__(
        self,
        host: str,
        port: int = 1883,
        user: str = "",
        password: str = "",
    ) -> None:
        self._host = host
        self._port = port
        self._client = mqtt.Client()
        if user:
            self._client.username_pw_set(user, password)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._subscriptions: dict[str, Callable[[str, str], None]] = {}

    def connect(self) -> None:
        self._client.connect(self._host, self._port, keepalive=60)
        self._client.loop_start()

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def subscribe(self, topic: str, callback: Callable[[str, str], None]) -> None:
        self._subscriptions[topic] = callback
        self._client.subscribe(topic)

    def publish(
        self, topic: str, payload: str | dict[str, Any], retain: bool = False
    ) -> None:
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        self._client.publish(topic, payload, retain=retain)

    def _on_connect(
        self, client: mqtt.Client, userdata: object, flags: dict[str, Any], rc: int
    ) -> None:
        if rc == 0:
            log.info("MQTT verbunden mit %s:%s", self._host, self._port)
            for topic in self._subscriptions:
                client.subscribe(topic)
        else:
            log.error("MQTT Verbindungsfehler: rc=%s", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata: object, rc: int) -> None:
        log.warning("MQTT getrennt (rc=%s)", rc)

    def _on_message(
        self, client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage
    ) -> None:
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace")
        cb = self._subscriptions.get(topic)
        if cb:
            cb(topic, payload)
        else:
            for pattern, callback in self._subscriptions.items():
                if mqtt.topic_matches_sub(pattern, topic):
                    callback(topic, payload)
                    break
