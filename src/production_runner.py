"""
ProductionRunner — orchestriert den 10-Minuten Block-Tick im Echtbetrieb.

Verbindet alle Schichten:
  TelemetryIngest → RawMeasurements → EnergyState → RuleEngine
  → ActuationWriter → EventStore + StateStore + KpiLog

run_once() ist die testbare Einheit — kein I/O, nur Orchestrierung.
run_loop() ist der blockierende Produktions-Loop.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Callable, Literal

from src.adapters.actuation_writer import ActuationWriter
from src.adapters.telemetry_ingest import TelemetryIngest, raw_from_ingest
from src.core import block_scheduler, rule_engine
from src.core.energy_context import build_energy_state
from src.core.models import DecisionEvent
from src.core.override_handler import OverrideHandler
from src.core.rule_engine import RuleEngineConfig
from src.data.event_store import EventStore
from src.data.kpi import write_kpi
from src.data.state_store import StateStore

log = logging.getLogger(__name__)


class ProductionRunner:
    """
    Orchestriert einen Block-Tick: Sensor-Snapshot → Entscheidung → Aktion.

    Zustand der letzten Entscheidung (last_action, blocks_since_change)
    wird zwischen Ticks gehalten — R5 Deadband funktioniert nur so.
    """

    def __init__(
        self,
        config: RuleEngineConfig,
        ingest: TelemetryIngest,
        writer: ActuationWriter,
        relay_topic: str,
        event_store: EventStore,
        state_store: StateStore,
        override_handler: OverrideHandler | None = None,
        explainer: Callable[[DecisionEvent], str] | None = None,
        kpi_conn: sqlite3.Connection | None = None,
        on_tick: Callable[[DecisionEvent, Any], None] | None = None,
    ) -> None:
        self._config = config
        self._ingest = ingest
        self._writer = writer
        self._relay_topic = relay_topic
        self._event_store = event_store
        self._state_store = state_store
        self._override = override_handler or OverrideHandler()
        self._explainer = explainer
        self._kpi_conn = kpi_conn
        self._on_tick = on_tick
        self._last_action: str | None = None
        self._blocks_since_change: int = 0
        self._miner_runtime_blocks: int = 0

    # ------------------------------------------------------------------
    # Testbare Einheit — ein Block-Tick
    # ------------------------------------------------------------------

    def run_once(self, now: datetime | None = None) -> DecisionEvent:
        """
        Führt einen vollständigen Block-Tick durch.

        1. Sensor-Snapshot aus TelemetryIngest
        2. EnergyState bauen (inkl. house_load_w-Fallback)
        3. Regeln evaluieren (R1–R5)
        4. Override prüfen (nicht für R3-Safety)
        5. Relay-Kommando senden
        6. Persistieren
        """
        now = now or datetime.now(tz=timezone.utc)
        block_id = block_scheduler.get_block_id(now)
        window_start, window_end = block_scheduler.get_window(now)

        raw = raw_from_ingest(self._ingest)
        state = build_energy_state(block_id, window_start, window_end, raw)

        t0 = time.monotonic()
        event = rule_engine.evaluate(
            state,
            config=self._config,
            last_action=self._last_action,
            blocks_since_last_change=self._blocks_since_change,
            now=now,
        )
        decision_latency_ms = (time.monotonic() - t0) * 1000

        # Override: manuelle Eingriffe, aber nie gegen R3
        active_override = self._override.get_active(now)
        effective_action: Literal["START", "STOP", "THROTTLE", "NOOP"]
        if active_override and not event.decision_code.startswith("STOP_R3_"):
            log.info(
                "Override aktiv: %s → %s (Override-Aktion)",
                event.decision.action,
                active_override.action,
            )
            # Override ersetzt Entscheidung (vereinfacht — kein neues DecisionEvent)
            effective_action = active_override.action
        else:
            effective_action = event.decision.action

        action_changed = effective_action != self._last_action

        # Deadband-Zähler und Miner-Laufzeit aktualisieren
        if action_changed:
            self._blocks_since_change = 0
            self._last_action = effective_action
        else:
            self._blocks_since_change += 1

        if effective_action == "START":
            self._miner_runtime_blocks += 1

        # Relay-Kommando senden
        cmd = self._writer.decision_to_command(
            effective_action, event.decision.command_id
        )
        if cmd is not None:
            self._writer.write(cmd, self._relay_topic)

        # Persistenz
        t1 = time.monotonic()
        explain_short = self._explainer(event) if self._explainer else ""
        explanation_latency_ms = (
            (time.monotonic() - t1) * 1000 if self._explainer else None
        )

        self._event_store.write(event, explain_short=explain_short)
        self._state_store.write(state)

        if self._kpi_conn is not None:
            pv = state.pv_power_w or 0.0
            export = state.grid_export_w or 0.0
            write_kpi(
                self._kpi_conn,
                block_id=block_id,
                decision_latency_ms=decision_latency_ms,
                explanation_latency_ms=explanation_latency_ms,
                thermal_incidents=(
                    1 if event.decision_code.startswith("STOP_R3_") else 0
                ),
                flapping_rate=1.0 if action_changed else 0.0,
                grid_import_wh=(state.grid_import_w or 0.0) / 6.0,
                explainability_coverage=100.0 if explain_short else 0.0,
                self_consumption_wh=max(0.0, pv - export) / 6.0,
                battery_soc_pct=state.battery_soc_pct,
                miner_runtime_blocks=self._miner_runtime_blocks,
                override_active=1 if active_override else 0,
            )

        log.info(
            "[%s] %s → %s | soc=%.0f%% surplus=%.1fkW override=%s",
            block_id,
            event.decision_code,
            effective_action,
            state.battery_soc_pct or 0.0,
            state.surplus_kw,
            active_override.action if active_override else "—",
        )
        log.debug(
            "[%s] pv=%.1fkW load=%.1fkW soc=%.0f%% surplus=%.1fkW temp=%.0f°C "
            "grid_in=%.1fkW grid_ex=%.1fkW forecast=%.1fkW "
            "action=%s code=%s override=%s quality=%s missing=%s "
            "dec_lat=%.0fms exp_lat=%s",
            block_id,
            (state.pv_power_w or 0.0) / 1000.0,
            (state.house_load_w or 0.0) / 1000.0,
            state.battery_soc_pct or 0.0,
            state.surplus_kw,
            state.miner_temp_c or 0.0,
            (state.grid_import_w or 0.0) / 1000.0,
            (state.grid_export_w or 0.0) / 1000.0,
            state.pv_forecast_kw or 0.0,
            effective_action,
            event.decision_code,
            active_override.action if active_override else "—",
            state.quality,
            ",".join(state.missing_signals) if state.missing_signals else "—",
            decision_latency_ms,
            f"{explanation_latency_ms:.0f}ms" if explanation_latency_ms else "—",
        )
        if state.missing_signals:
            log.warning(
                "[%s] Fehlende Signale: %s",
                block_id,
                ", ".join(state.missing_signals),
            )
        if self._on_tick is not None:
            self._on_tick(event, state)
        return event

    # ------------------------------------------------------------------
    # Produktions-Loop
    # ------------------------------------------------------------------

    def run_loop(self, tick_interval_sec: float = 600.0) -> None:
        """
        Blockierender 10-Minuten-Tick-Loop.

        Fehler in einem Tick werden geloggt, der Loop läuft weiter.
        Nur KeyboardInterrupt beendet den Loop sauber.
        """
        log.info(
            "ProductionRunner gestartet — Tick alle %.0f s",
            tick_interval_sec,
        )
        while True:
            try:
                self.run_once()
            except Exception as exc:
                log.error("Tick-Fehler (weiter): %s", exc, exc_info=True)
            time.sleep(tick_interval_sec)
