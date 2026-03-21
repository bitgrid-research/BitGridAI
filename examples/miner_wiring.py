"""
Beispiel: Canaan Avalon Q 90TH + Shelly Plug S anschließen.

Zeigt wie CanaanAdapter, ShellyAdapter und ActuationWriter zusammengesteckt werden.
Für Produktion in den Core-Runner integrieren.

Starten (aus Repo-Root):
  python examples/miner_wiring.py
"""

from __future__ import annotations

import logging
import os
import time

from src.adapters.actuation_writer import ActuationCommand, ActuationWriter
from src.adapters.canaan_adapter import CanaanAdapter
from src.adapters.mqtt_client import MqttClient
from src.adapters.shelly_adapter import ShellyAdapter
from src.adapters.telemetry_ingest import TelemetryIngest
from src.core.signals import Signal

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    mqtt = MqttClient(
        host=os.getenv("MQTT_HOST", "192.168.1.10"),
        port=int(os.getenv("MQTT_PORT", "1883")),
        user=os.getenv("MQTT_USER", ""),
        password=os.getenv("MQTT_PASSWORD", ""),
    )
    mqtt.connect()

    ingest = TelemetryIngest(stale_threshold_sec=60.0)

    shelly = ShellyAdapter(mqtt=mqtt, ingest=ingest)
    shelly.register()

    writer = ActuationWriter(publish_fn=shelly.publish_relay)
    relay_topic = shelly.relay_command_topic
    log.info("Relay-Topic: %s", relay_topic)

    canaan = CanaanAdapter(ingest=ingest)
    canaan.start()

    log.info("Läuft — Ctrl+C zum Beenden")
    try:
        cycle = 0
        while True:
            time.sleep(10)
            cycle += 1

            log.info(
                "Telemetrie: temp=%.1f°C  power=%.0fW  hashrate=%.1fTH/s  heartbeat=%.0fs",
                ingest.get_value(Signal.MINER_TEMP_C) or 0,
                ingest.get_value(Signal.MINER_POWER_W) or 0,
                ingest.get_value(Signal.MINER_HASHRATE_TH) or 0,
                ingest.get_value(Signal.MINER_HEARTBEAT_AGE_SEC) or -1,
            )

            if cycle == 3:
                sent = writer.write(
                    ActuationCommand(target="miner_relay", action="ON", command_id="test-001"),
                    relay_topic,
                )
                log.info("Test-Befehl gesendet: %s", sent)

    except KeyboardInterrupt:
        log.info("Stoppe...")
    finally:
        canaan.stop()
        mqtt.disconnect()


if __name__ == "__main__":
    main()
