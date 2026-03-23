"""
BitGridAI — Produktions-Einstiegspunkt.

Startet alle Adapter, verbindet Schichten und läuft den 10-Minuten-Tick-Loop.

Verwendung:
  python -m src.main
  python -m src.main --rules src/ops/config/rules.yaml --db data/bitgrid.db
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)


def _setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)-30s %(levelname)s %(message)s",
    )


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass  # python-dotenv optional — Variablen können direkt gesetzt sein


def main(rules_path: str, db_path: str) -> None:
    from src.adapters.actuation_writer import ActuationWriter
    from src.adapters.forecast_adapter import ForecastAdapter
    from src.adapters.modbus_adapter import ModbusAdapter
    from src.adapters.mqtt_client import MqttClient
    from src.adapters.mqtt_inverter_adapter import MqttInverterAdapter
    from src.adapters.price_adapter import PriceAdapter
    from src.adapters.shelly_adapter import ShellyAdapter
    from src.adapters.shelly_em_adapter import ShellyEMAdapter
    from src.adapters.telemetry_ingest import TelemetryIngest
    from src.core.production_runner import ProductionRunner
    from src.data.db import get_connection
    from src.data.event_store import EventStore
    from src.data.state_store import StateStore
    from src.ops.config_loader import ConfigLoader, rules_to_engine_config

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    rules_data = ConfigLoader(rules_path).load()
    engine_config = rules_to_engine_config(rules_data)
    log.info("Rules geladen: %s", rules_path)

    # ------------------------------------------------------------------
    # MQTT
    # ------------------------------------------------------------------
    mqtt = MqttClient(
        host=os.getenv("MQTT_HOST", "192.168.1.10"),
        port=int(os.getenv("MQTT_PORT", "1883")),
        user=os.getenv("MQTT_USER", ""),
        password=os.getenv("MQTT_PASSWORD", ""),
    )
    mqtt.connect()
    log.info("MQTT verbunden")

    # ------------------------------------------------------------------
    # TelemetryIngest — gemeinsamer Signal-Cache
    # ------------------------------------------------------------------
    ingest = TelemetryIngest(stale_threshold_sec=60.0)

    # ------------------------------------------------------------------
    # Infrastruktur-Adapter starten
    # ------------------------------------------------------------------

    # PV-Wechselrichter via MQTT
    inverter = MqttInverterAdapter(mqtt=mqtt, ingest=ingest)
    inverter.register()

    # Netz-Zähler (Shelly EM / 3EM)
    shelly_em = ShellyEMAdapter(mqtt=mqtt, ingest=ingest)
    shelly_em.register()

    # Batterie-BMS via Modbus TCP
    modbus = ModbusAdapter(ingest=ingest)
    modbus.start()

    # Strompreis (aWATTar oder ENTSO-E)
    price = PriceAdapter(ingest=ingest)
    price.start()

    # PV-Prognose (forecast.solar)
    forecast = ForecastAdapter(ingest=ingest)
    forecast.start()

    # Miner-Adapter: Canaan Avalon Q (Standard) — alternativ BitaxeAdapter
    # Auskommentieren/ersetzen je nach Hardware:
    miner_enabled = os.getenv("MINER_HOST")
    if miner_enabled:
        from src.adapters.canaan_adapter import CanaanAdapter

        canaan = CanaanAdapter(ingest=ingest)
        canaan.start()
        log.info("CanaanAdapter gestartet")

    bitaxe_enabled = os.getenv("BITAXE_HOST")
    if bitaxe_enabled:
        from src.adapters.bitaxe_adapter import BitaxeAdapter

        bitaxe = BitaxeAdapter(ingest=ingest)
        bitaxe.start()
        log.info("BitaxeAdapter gestartet")

    # ------------------------------------------------------------------
    # Relay-Steuerung (Shelly Plug S)
    # ------------------------------------------------------------------
    shelly = ShellyAdapter(mqtt=mqtt, ingest=ingest)
    shelly.register()
    relay_topic = shelly.relay_command_topic

    writer = ActuationWriter(publish_fn=shelly.publish_relay)

    # ------------------------------------------------------------------
    # Persistenz
    # ------------------------------------------------------------------
    conn = get_connection(db_path)
    event_store = EventStore(conn)
    state_store = StateStore(conn)

    # ------------------------------------------------------------------
    # ProductionRunner starten
    # ------------------------------------------------------------------
    runner = ProductionRunner(
        config=engine_config,
        ingest=ingest,
        writer=writer,
        relay_topic=relay_topic,
        event_store=event_store,
        state_store=state_store,
    )

    log.info("Alle Adapter bereit — starte Block-Tick-Loop")
    try:
        runner.run_loop(tick_interval_sec=600.0)
    except KeyboardInterrupt:
        log.info("BitGridAI gestoppt")
    finally:
        mqtt.disconnect()


if __name__ == "__main__":
    _load_env()
    _setup_logging()

    parser = argparse.ArgumentParser(description="BitGridAI Production Runner")
    parser.add_argument(
        "--rules",
        default=os.getenv("RULES_PATH", "src/ops/config/rules.yaml"),
        help="Pfad zu rules.yaml",
    )
    parser.add_argument(
        "--db",
        default=os.getenv("DB_PATH", "data/bitgrid.db"),
        help="Pfad zur SQLite-Datenbank",
    )
    args = parser.parse_args()

    main(rules_path=args.rules, db_path=args.db)
