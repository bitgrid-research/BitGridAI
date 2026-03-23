"""
ProductionRunner — orchestriert den 10-Minuten Block-Tick im Echtbetrieb.

Verbindet alle Schichten:
  TelemetryIngest → RawMeasurements → EnergyState → RuleEngine
  → ActuationWriter → EventStore + StateStore

run_once() ist die testbare Einheit — kein I/O, nur Orchestrierung.
run_loop() ist der blockierende Produktions-Loop.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from src.adapters.actuation_writer import ActuationWriter
from src.adapters.telemetry_ingest import TelemetryIngest
from src.core import block_scheduler, rule_engine
from src.core.energy_context import build_energy_state, raw_from_ingest
from src.core.models import DecisionEvent
from src.core.override_handler import OverrideHandler
from src.core.rule_engine import RuleEngineConfig
from src.data.event_store import EventStore
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
    ) -> None:
        self._config = config
        self._ingest = ingest
        self._writer = writer
        self._relay_topic = relay_topic
        self._event_store = event_store
        self._state_store = state_store
        self._override = override_handler or OverrideHandler()
        self._last_action: str | None = None
        self._blocks_since_change: int = 0

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

        event = rule_engine.evaluate(
            state,
            config=self._config,
            last_action=self._last_action,
            blocks_since_last_change=self._blocks_since_change,
            now=now,
        )

        # Override: manuelle Eingriffe, aber nie gegen R3
        active_override = self._override.get_active(now)
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

        # Deadband-Zähler aktualisieren
        if effective_action != self._last_action:
            self._blocks_since_change = 0
            self._last_action = effective_action
        else:
            self._blocks_since_change += 1

        # Relay-Kommando senden
        cmd = self._writer.decision_to_command(
            effective_action, event.decision.command_id
        )
        if cmd is not None:
            self._writer.write(cmd, self._relay_topic)

        # Persistenz
        self._event_store.write(event)
        self._state_store.write(state)

        log.info(
            "[%s] %s | quality=%s surplus=%.1f kW temp=%.0f°C soc=%.0f%%",
            block_id,
            event.decision_code,
            state.quality,
            state.surplus_kw,
            state.miner_temp_c,
            state.battery_soc_pct,
        )
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
