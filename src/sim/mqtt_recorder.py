"""
MqttRecorder — zeichnet Live-MQTT-Traffic als JSONL auf.

Zweck: Echtdaten aus der Produktion erfassen und später als Simulation
       wiederverwenden (→ src/sim/replay.py oder eigener Konverter).

Aufgezeichnetes Format (eine JSON-Zeile pro Nachricht):
  {"ts": "2024-01-15T10:05:23.412Z", "topic": "bitgrid/home/pv_inverter/power_w", "payload": "4200.5"}

Verwendung:
  python -m src.sim.mqtt_recorder                         # Standard-Ausgabe + Datei
  python -m src.sim.mqtt_recorder --output session.jsonl  # nur Datei
  python -m src.sim.mqtt_recorder --topic "shellies/#"    # andere Topics

Hardcoded Defaults:
  MQTT_HOST      = 192.168.1.10
  RECORDER_TOPIC = #          (alle Topics)
  RECORDER_OUT   = recordings/session.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.adapters.mqtt_client import MqttClient

log = logging.getLogger(__name__)

_DEFAULT_MQTT_HOST = os.getenv("MQTT_HOST", "192.168.1.10")
_DEFAULT_MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
_DEFAULT_TOPIC = os.getenv("RECORDER_TOPIC", "#")
_DEFAULT_OUT = os.getenv("RECORDER_OUT", "recordings/session.jsonl")


class MqttRecorder:
    """
    Subscribed zu MQTT-Topics und schreibt Nachrichten als JSONL.

    Jede Zeile ist ein gültiges JSON-Objekt → einfach weiterzuverarbeiten.
    """

    def __init__(
        self,
        mqtt: MqttClient,
        output_path: str | Path,
        topic: str = _DEFAULT_TOPIC,
    ) -> None:
        self._mqtt = mqtt
        self._topic = topic
        self._out = Path(output_path)
        self._out.parent.mkdir(parents=True, exist_ok=True)
        self._file = None
        self._count = 0

    def start(self) -> None:
        self._file = open(
            self._out, "a", encoding="utf-8", buffering=1
        )  # line-buffered
        self._mqtt.subscribe(self._topic, self._on_message)
        log.info("MqttRecorder gestartet — Topic: %s → %s", self._topic, self._out)

    def stop(self) -> None:
        if self._file:
            self._file.close()
        log.info("MqttRecorder gestoppt — %d Nachrichten aufgezeichnet", self._count)

    def _on_message(self, topic: str, payload: str) -> None:
        record = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "topic": topic,
            "payload": payload,
        }
        line = json.dumps(record, ensure_ascii=False)
        if self._file:
            self._file.write(line + "\n")
        print(line)
        self._count += 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser(description="BitGridAI MQTT Recorder")
    parser.add_argument("--host", default=_DEFAULT_MQTT_HOST)
    parser.add_argument("--port", type=int, default=_DEFAULT_MQTT_PORT)
    parser.add_argument(
        "--topic", default=_DEFAULT_TOPIC, help="MQTT-Topic oder Wildcard (default: #)"
    )
    parser.add_argument(
        "--output",
        default=_DEFAULT_OUT,
        help="Ausgabedatei (JSONL, default: recordings/session.jsonl)",
    )
    args = parser.parse_args()

    mqtt = MqttClient(
        host=args.host,
        port=args.port,
        user=os.getenv("MQTT_USER", ""),
        password=os.getenv("MQTT_PASSWORD", ""),
    )
    mqtt.connect()

    recorder = MqttRecorder(mqtt, output_path=args.output, topic=args.topic)
    recorder.start()

    log.info("Aufnahme läuft — Ctrl+C zum Stoppen")
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        recorder.stop()
        mqtt.disconnect()


if __name__ == "__main__":
    main()
