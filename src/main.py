"""
BitGridAI — Produktions-Einstiegspunkt.

Startet alle Adapter, verbindet Schichten und läuft den 10-Minuten-Tick-Loop.

Verwendung:
  python -m src.main
  python -m src.main --rules src/ops/config/rules.yaml --db data/bitgrid.db
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import os
import threading
from pathlib import Path

log = logging.getLogger(__name__)


def _setup_logging(log_dir: str | None) -> None:
    from src.ops.log_setup import setup_logging

    setup_logging(
        log_dir=log_dir,
        console_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass  # python-dotenv optional — Variablen können direkt gesetzt sein


def main(rules_path: str, db_path: str) -> None:
    from typing import Any

    import uvicorn

    from src.adapters.actuation_writer import ActuationWriter
    from src.adapters.openmeteo_forecast_adapter import OpenMeteoForecastAdapter
    from src.adapters.modbus_adapter import ModbusAdapter
    from src.adapters.mqtt_client import MqttClient
    from src.adapters.mqtt_inverter_adapter import MqttInverterAdapter
    from src.adapters.price_adapter import PriceAdapter
    from src.adapters.shelly_adapter import ShellyAdapter
    from src.adapters.shelly_em_adapter import ShellyEMAdapter
    from src.adapters.telemetry_ingest import TelemetryIngest
    from src.core.models import DecisionEvent, EnergyState
    from src.core.override_handler import OverrideHandler
    from src.production_runner import ProductionRunner
    from src.data.db import get_connection
    from src.data.event_store import EventStore
    from src.data.state_store import StateStore
    from src.explain.explain_agent import ExplainAgent
    from src.ops.config_loader import ConfigLoader, rules_to_engine_config
    from src.ops.log_setup import get_log_file
    from src.ui import api as _api

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    rules_data = ConfigLoader(rules_path).load()
    engine_config = rules_to_engine_config(rules_data)
    log.info("Rules geladen: %s", rules_path)

    if (lf := get_log_file()) is not None:
        _api.set_log_file(lf)
        log.info("Log-Datei: %s", lf)

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

    # Batterie-BMS via Modbus TCP (opt-in — nur wenn MODBUS_HOST gesetzt)
    if os.getenv("MODBUS_HOST"):
        modbus = ModbusAdapter(ingest=ingest)
        modbus.start()

    # Strompreis (aWATTar oder ENTSO-E)
    price = PriceAdapter(ingest=ingest)
    price.start()

    # PV-Prognose (Open-Meteo — kein API-Key, kein Rate-Limit)
    forecast = OpenMeteoForecastAdapter(ingest=ingest, publish_fn=mqtt.publish)
    forecast.start()

    # HA-Telemetrie (opt-in via HA_URL + HA_TOKEN in .env)
    ha_url = os.getenv("HA_URL", "")
    ha_token = os.getenv("HA_TOKEN", "")
    if ha_url and ha_token:
        from src.adapters.ha_telemetry_adapter import HaTelemetryAdapter

        ha_adapter = HaTelemetryAdapter(
            ha_url=ha_url,
            ha_token=ha_token,
            ingest=ingest,
            poll_interval_sec=float(os.getenv("HA_POLL_INTERVAL_SEC", "30")),
        )
        ha_adapter.start()
    else:
        log.debug("HaTelemetryAdapter nicht gestartet — HA_URL oder HA_TOKEN fehlt")

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
    # Override-Handler + API-Wiring
    # ------------------------------------------------------------------
    override_handler = OverrideHandler(conn)

    def _on_tick(event: DecisionEvent, state: EnergyState) -> None:
        d = dataclasses.asdict(state)
        d["window_start"] = state.window_start.isoformat()
        d["window_end"] = state.window_end.isoformat()
        _api.set_state(d)
        _api.set_decision(
            {
                "decision_code": event.decision_code,
                "action": event.decision.action,
                "reason": event.reason,
                "params": event.params,
            }
        )

    _api.set_engine_config(engine_config)
    _api.set_override_handler(override_handler)
    _api.set_stores(event_store, None)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # API-Server im Hintergrund-Thread starten
    # ------------------------------------------------------------------
    api_port = int(os.getenv("API_PORT", "8080"))
    api_thread = threading.Thread(
        target=lambda: uvicorn.run(
            _api.app,
            host="0.0.0.0",
            port=api_port,
            log_level="warning",
        ),
        daemon=True,
        name="bitgrid-api",
    )
    api_thread.start()
    log.info("API-Server gestartet auf Port %d", api_port)

    # ------------------------------------------------------------------
    # ExplainAgent (opt-in — nur wenn OLLAMA_HOST gesetzt)
    # ------------------------------------------------------------------
    explainer = None
    if os.getenv("OLLAMA_HOST"):
        explain_agent = ExplainAgent()
        explainer = explain_agent.explain_short
        log.info(
            "ExplainAgent aktiv — %s model=%s persona=%s",
            os.getenv("OLLAMA_HOST"),
            explain_agent._ollama_model,
            explain_agent.persona,
        )
    else:
        log.debug("ExplainAgent nicht gestartet — OLLAMA_HOST fehlt")

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
        override_handler=override_handler,
        explainer=explainer,
        kpi_conn=conn,
        on_tick=_on_tick,
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
    parser.add_argument(
        "--log-dir",
        default=os.getenv("LOG_DIR", "data/logs"),
        help="Verzeichnis für rotierende Log-Dateien (default: data/logs)",
    )
    args = parser.parse_args()

    _setup_logging(log_dir=args.log_dir)

    main(rules_path=args.rules, db_path=args.db)
