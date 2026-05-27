"""
ProductionRunner — verdrahtet alle BitGridAI-Komponenten für den Live-Betrieb.

Startreihenfolge:
  1. Config laden (rules.yaml)
  2. DB öffnen (SQLite WAL)
  3. MQTT verbinden
  4. Adapter-Callbacks registrieren
  5. Initialen Block sofort auslösen
  6. Block-Loop (asyncio) + API-Server (uvicorn) parallel starten
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn

from src.adapters.actuation_writer import ActuationWriter
from src.adapters.health_monitor import HealthMonitor
from src.adapters.mqtt_client import MqttClient
from src.adapters.telemetry_ingest import TelemetryIngest, raw_from_ingest
from src.core import block_scheduler
from src.core.energy_context import build_energy_state
from src.core.override_handler import OverrideHandler
from src.core.rule_engine import evaluate as engine_evaluate
from src.core.signals import Signal
from src.data.db import get_connection
from src.data.event_store import EventStore
from src.data.kpi import write_kpi
from src.data.state_store import StateStore
from src.explain.explain_agent import ExplainAgent
from src.ops.config_loader import ConfigLoader, rules_to_engine_config
from src.ui import api as ui_api

log = logging.getLogger(__name__)

_MINER_CMD_TOPIC = os.getenv("MINER_CMD_TOPIC", "bitgrid/miner/cmd/relay")


class ProductionRunner:
    """Orchestriert alle BitGridAI-Komponenten. Keine Business-Logik hier."""

    def __init__(self) -> None:
        self._cfg = ConfigLoader(os.getenv("RULES_CONFIG", "config/rules.yaml"))
        self._cfg.load()

        self._conn = get_connection(os.getenv("DB_PATH", "data/bitgrid.db"))
        self._event_store = EventStore(self._conn)
        self._state_store = StateStore(self._conn)

        self._ingest = TelemetryIngest(stale_threshold_sec=60.0)
        self._health = HealthMonitor(stale_warn_sec=30.0, stale_error_sec=60.0)
        self._mqtt = MqttClient(
            host=os.getenv("MQTT_HOST", "localhost"),
            port=int(os.getenv("MQTT_PORT", "1883")),
            user=os.getenv("MQTT_USER", ""),
            password=os.getenv("MQTT_PASSWORD", ""),
            on_connect_cb=lambda: self._health.report_connected("mqtt"),
            on_disconnect_cb=lambda reason: self._health.report_disconnected(
                "mqtt", reason
            ),
        )
        self._actuation = ActuationWriter(
            publish_fn=lambda topic, payload: self._mqtt.publish(topic, payload)
        )
        self._overrides = OverrideHandler(conn=self._conn)
        self._explain = ExplainAgent()

        ui_api.set_stores(self._event_store, self._explain)
        ui_api.set_override_handler(self._overrides)
        ui_api.set_health_monitor(self._health)

        flags_path = Path("ops/config/feature_flags.yaml")
        if flags_path.exists():
            import yaml as _yaml  # noqa: PLC0415

            _flags = _yaml.safe_load(flags_path.read_text(encoding="utf-8")) or {}
            _auth = _flags.get("features", {}).get("auth_enabled", False)
        else:
            _auth = False
        ui_api.set_auth(enabled=_auth, token=os.getenv("API_TOKEN", ""))
        _export = (
            _flags.get("features", {}).get("research_export", False)
            if flags_path.exists()
            else False
        )
        ui_api.set_research_export(enabled=_export)

        self._last_action: str | None = None
        self._blocks_since_change: int = 0

    # ------------------------------------------------------------------
    # Adapter-Setup
    # ------------------------------------------------------------------

    def _setup_adapters(self) -> None:
        """Registriert MQTT-Topics → Signal-Mappings auf dem gemeinsamen Client."""

        def _float_cb(signal: Signal) -> object:
            def _cb(topic: str, payload: str) -> None:
                try:
                    self._ingest.update(signal, float(payload), source=topic)
                except ValueError:
                    log.debug("Ungültiger Wert auf %s: %r", topic, payload)

            return _cb

        def _on_grid(topic: str, payload: str) -> None:
            try:
                val = float(payload)
                if val >= 0:
                    self._ingest.update(Signal.GRID_IMPORT_W, val, source=topic)
                    self._ingest.update(Signal.GRID_EXPORT_W, 0.0, source=topic)
                else:
                    self._ingest.update(Signal.GRID_IMPORT_W, 0.0, source=topic)
                    self._ingest.update(Signal.GRID_EXPORT_W, -val, source=topic)
            except ValueError:
                pass

        def _on_heartbeat(topic: str, payload: str) -> None:
            self._ingest.update(Signal.MINER_HEARTBEAT_AGE_SEC, 0.0, source=topic)

        self._mqtt.subscribe(
            os.getenv("PV_MQTT_TOPIC", "bitgrid/home/pv_inverter/power_w"),
            _float_cb(Signal.PV_POWER_W),  # type: ignore[arg-type]
        )
        self._mqtt.subscribe(
            os.getenv("GRID_MQTT_TOPIC", "bitgrid/home/grid_meter/power_w"),
            _on_grid,
        )
        self._mqtt.subscribe(
            os.getenv("SOC_MQTT_TOPIC", "bitgrid/home/battery/soc_pct"),
            _float_cb(Signal.BATTERY_SOC_PCT),  # type: ignore[arg-type]
        )
        self._mqtt.subscribe(
            os.getenv("MINER_TEMP_TOPIC", "bitgrid/miner/status/temp_c"),
            _float_cb(Signal.MINER_TEMP_C),  # type: ignore[arg-type]
        )
        self._mqtt.subscribe(
            os.getenv("MINER_HEARTBEAT_TOPIC", "bitgrid/miner/status/heartbeat"),
            _on_heartbeat,
        )
        self._mqtt.subscribe(
            os.getenv("MINER_POWER_TOPIC", "bitgrid/miner/status/power_w"),
            _float_cb(Signal.MINER_POWER_W),  # type: ignore[arg-type]
        )
        self._mqtt.subscribe(
            os.getenv("PV_FORECAST_TOPIC", "bitgrid/forecast/pv_kw"),
            _float_cb(Signal.PV_FORECAST_KW),  # type: ignore[arg-type]
        )

    # ------------------------------------------------------------------
    # Block-Zyklus
    # ------------------------------------------------------------------

    def _run_block(self) -> None:
        """Führt einen vollständigen 10-Minuten-Block-Zyklus aus."""
        t_start = time.perf_counter()
        now = datetime.now(tz=timezone.utc)

        block_id = block_scheduler.get_block_id(now)
        window_start, window_end = block_scheduler.get_window(now)
        raw = raw_from_ingest(self._ingest)
        state = build_energy_state(block_id, window_start, window_end, raw)

        engine_config = rules_to_engine_config(self._cfg.data)
        ui_api.set_engine_config(engine_config)
        event = engine_evaluate(
            state,
            config=engine_config,
            last_action=self._last_action,
            blocks_since_last_change=self._blocks_since_change,
            autonomy_level=self._overrides.autonomy_level,
        )
        decision_latency_ms = (time.perf_counter() - t_start) * 1000

        t_explain = time.perf_counter()
        explain_result = self._explain.explain(
            event.decision_code,
            event.params,
            energy_state_ref=state.block_id,
        )
        explain_short = explain_result.short
        explanation_latency_ms = (time.perf_counter() - t_explain) * 1000

        self._event_store.write(event, explain_short=explain_short)
        self._state_store.write(state)

        # Publish explain fields to MQTT so HA study dashboards can display them
        for _topic, _payload in [
            ("bitgrid/explain/code", event.decision_code),
            ("bitgrid/explain/action", event.decision.action),
            ("bitgrid/explain/block_id", state.block_id),
            ("bitgrid/explain/trigger", explain_result.trigger),
            ("bitgrid/explain/effect", explain_result.effect),
            ("bitgrid/explain/data_basis", explain_result.data_basis),
            ("bitgrid/explain/options", explain_result.options),
            ("bitgrid/explain/short", explain_short),
        ]:
            try:
                self._mqtt.publish(_topic, _payload)
            except Exception:
                log.debug("MQTT-Publish fehlgeschlagen: %s", _topic)

        write_kpi(
            self._conn,
            block_id=block_id,
            decision_latency_ms=decision_latency_ms,
            explanation_latency_ms=explanation_latency_ms,
            battery_soc_pct=state.battery_soc_pct,
            override_active=int(self._overrides.get_active() is not None),
        )

        action = event.decision.action
        cmd = self._actuation.decision_to_command(action, event.decision.command_id)
        if cmd is not None:
            self._actuation.write(cmd, topic=_MINER_CMD_TOPIC)

        ui_api.set_state(
            {
                "block_id": state.block_id,
                "pv_power_w": state.pv_power_w,
                "house_load_w": state.house_load_w,
                "surplus_kw": state.surplus_kw,
                "battery_soc_pct": state.battery_soc_pct,
                "miner_temp_c": state.miner_temp_c,
                "quality": state.quality,
                "missing_signals": list(state.missing_signals),
            }
        )
        ui_api.set_decision(
            {
                "action": action,
                "decision_code": event.decision_code,
                "short": explain_short,
                "valid_until": event.decision.valid_until.isoformat(),
                "command_id": event.decision.command_id,
            }
        )

        if action != self._last_action:
            self._blocks_since_change = 0
        else:
            self._blocks_since_change += 1
        self._last_action = action

        log.info(
            "Block %s | %s | %s | decision=%.0fms explain=%.0fms",
            block_id,
            action,
            event.decision_code,
            decision_latency_ms,
            explanation_latency_ms,
        )

    async def _block_loop(self) -> None:
        """Wartet auf Blockgrenzen und triggert _run_block()."""
        while True:
            now = datetime.now(tz=timezone.utc)
            _, window_end = block_scheduler.get_window(now)
            sleep_sec = max(1.0, (window_end - now).total_seconds())
            log.debug("Nächster Block-Tick in %.0f s", sleep_sec)
            await asyncio.sleep(sleep_sec)
            try:
                self._run_block()
            except Exception:
                log.exception("Fehler im Block-Zyklus — System läuft weiter")

    # ------------------------------------------------------------------
    # Einstiegspunkt
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Startet MQTT, Adapter, Block-Loop und API-Server."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        )
        log.info("BitGridAI ProductionRunner startet")

        self._mqtt.connect()
        self._setup_adapters()

        try:
            self._run_block()
        except Exception:
            log.exception("Initialer Block fehlgeschlagen — fahre trotzdem fort")

        server = uvicorn.Server(
            uvicorn.Config(
                ui_api.app,
                host="0.0.0.0",
                port=int(os.getenv("API_PORT", "8080")),
                log_level="warning",
            )
        )

        async def _main() -> None:
            await asyncio.gather(self._block_loop(), server.serve())

        try:
            asyncio.run(_main())
        finally:
            log.info("BitGridAI fährt herunter")
            self._mqtt.disconnect()
            self._conn.close()


if __name__ == "__main__":
    ProductionRunner().run()
