"""
Integration-Tests — voller Pfad: Signal → EnergyState → RuleEngine → Aktion.

Testet das Zusammenspiel aller Schichten ohne echte Hardware.
MQTT wird durch einen Capture-Buffer ersetzt.

Kritische Invarianten:
- Übertemperatur-Signal → immer STOP, nie START
- Fehlende Signale → quality=error, aber keine Exception
- Surplus + alle Signale OK → START
- house_load_w-Fallback aus Energiebilanz funktioniert
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Callable

import pytest

from src.adapters.actuation_writer import ActuationCommand, ActuationWriter
from src.adapters.telemetry_ingest import TelemetryIngest
from src.core import rule_engine
from src.core.energy_context import build_energy_state, raw_from_ingest
from src.core.production_runner import ProductionRunner
from src.core.rule_engine import RuleEngineConfig
from src.core.signals import Signal
from src.data.event_store import EventStore
from src.data.state_store import StateStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ingest() -> TelemetryIngest:
    return TelemetryIngest(stale_threshold_sec=60.0)


@pytest.fixture
def capture_writer() -> tuple[ActuationWriter, list[tuple[str, str]]]:
    """ActuationWriter mit Capture-Buffer statt echtem MQTT."""
    sent: list[tuple[str, str]] = []

    def _publish(topic: str, payload: str) -> None:
        sent.append((topic, payload))

    return ActuationWriter(publish_fn=_publish), sent


@pytest.fixture
def in_memory_stores():
    conn = sqlite3.connect(":memory:")
    from src.data.db import _SCHEMA

    conn.executescript(_SCHEMA)
    return EventStore(conn), StateStore(conn)


@pytest.fixture
def runner(ingest, capture_writer, in_memory_stores) -> tuple[ProductionRunner, list]:
    writer, sent = capture_writer
    event_store, state_store = in_memory_stores
    r = ProductionRunner(
        config=RuleEngineConfig(),
        ingest=ingest,
        writer=writer,
        relay_topic="test/miner/relay/command",
        event_store=event_store,
        state_store=state_store,
    )
    return r, sent


def _feed(ingest: TelemetryIngest, **signals: float) -> None:
    """Hilfsfunktion: Signal-Werte in TelemetryIngest schreiben."""
    mapping = {
        "pv_power_w": Signal.PV_POWER_W,
        "house_load_w": Signal.HOUSE_LOAD_W,
        "grid_import_w": Signal.GRID_IMPORT_W,
        "grid_export_w": Signal.GRID_EXPORT_W,
        "battery_soc_pct": Signal.BATTERY_SOC_PCT,
        "miner_temp_c": Signal.MINER_TEMP_C,
        "miner_heartbeat_age_sec": Signal.MINER_HEARTBEAT_AGE_SEC,
        "miner_power_w": Signal.MINER_POWER_W,
        "energy_price_ct_kwh": Signal.ENERGY_PRICE_CT_KWH,
        "pv_forecast_kw": Signal.PV_FORECAST_KW,
    }
    for name, value in signals.items():
        ingest.update(mapping[name], value, source="test")


# ---------------------------------------------------------------------------
# Vollständige Pipeline
# ---------------------------------------------------------------------------


class TestSurplusStartsPipeline:
    def test_start_command_sent_on_surplus(self, runner, ingest) -> None:
        """PV-Überschuss + alle Signale OK → relay 'on' gesendet."""
        prod, sent = runner
        _feed(
            ingest,
            pv_power_w=4000,
            house_load_w=600,
            grid_import_w=0,
            battery_soc_pct=80,
            miner_temp_c=65,
            miner_heartbeat_age_sec=5,
        )

        event = prod.run_once(now=datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc))

        assert event.decision.action == "START"
        assert len(sent) == 1
        assert (
            sent[0][1] == "ON"
        )  # ActuationWriter — Shelly-Konversion in ShellyAdapter

    def test_decision_persisted(self, runner, ingest, in_memory_stores) -> None:
        """DecisionEvent und EnergyState werden in DB geschrieben."""
        prod, _ = runner
        event_store, state_store = in_memory_stores
        _feed(
            ingest,
            pv_power_w=4000,
            house_load_w=600,
            grid_import_w=0,
            battery_soc_pct=80,
            miner_temp_c=65,
            miner_heartbeat_age_sec=5,
        )

        event = prod.run_once(now=datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc))

        stored = event_store.read(event.decision.command_id)
        assert stored is not None
        assert stored["action"] == "START"


class TestSafetyPipeline:
    def test_overtemp_sends_off(self, runner, ingest) -> None:
        """Übertemperatur → relay 'off', unabhängig vom PV-Überschuss."""
        prod, sent = runner
        _feed(
            ingest,
            pv_power_w=6000,
            house_load_w=600,
            grid_import_w=0,
            battery_soc_pct=90,
            miner_temp_c=91,
            miner_heartbeat_age_sec=5,
        )

        event = prod.run_once()

        assert event.decision.action == "STOP"
        assert "R3" in event.decision_code
        assert len(sent) == 1
        assert sent[0][1] == "OFF"

    def test_comm_timeout_sends_off(self, runner, ingest) -> None:
        """Kein Heartbeat seit >60s → R3 STOP."""
        prod, sent = runner
        _feed(
            ingest,
            pv_power_w=4000,
            house_load_w=600,
            grid_import_w=0,
            battery_soc_pct=80,
            miner_temp_c=65,
            miner_heartbeat_age_sec=120,
        )

        event = prod.run_once()

        assert event.decision.action == "STOP"
        assert "COMM_TIMEOUT" in event.reason

    def test_overtemp_cannot_be_overridden(self, runner, ingest) -> None:
        """R3 überstimmt aktiven Override — Safety ist non-negotiable."""
        from src.core.override_handler import OverrideHandler

        prod, sent = runner

        prod._override.request("START", duration_min=60, command_id="override-001")
        _feed(
            ingest,
            pv_power_w=6000,
            house_load_w=600,
            grid_import_w=0,
            battery_soc_pct=90,
            miner_temp_c=93,
            miner_heartbeat_age_sec=5,
        )

        event = prod.run_once()

        assert event.decision.action == "STOP"
        assert "R3" in event.decision_code


class TestMissingSignals:
    def test_missing_signals_produce_quality_error(self, ingest) -> None:
        """Mehr als 2 fehlende Pflicht-Signale → quality='error'."""
        # Nur miner_temp_c gesetzt, Rest fehlt
        ingest.update(Signal.MINER_TEMP_C, 65.0, source="test")
        raw = raw_from_ingest(ingest)
        now = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        state = build_energy_state("2024-06-15T12:00:00", now, now, raw)
        assert state.quality == "error"
        assert len(state.missing_signals) > 2

    def test_missing_miner_temp_triggers_r3(self, runner, ingest) -> None:
        """Kein miner_temp_c → Fallback 999°C → R3 STOP."""
        prod, sent = runner
        # Alle außer miner_temp_c
        _feed(
            ingest,
            pv_power_w=4000,
            house_load_w=600,
            grid_import_w=0,
            battery_soc_pct=80,
            miner_heartbeat_age_sec=5,
        )

        event = prod.run_once()

        assert event.decision.action == "STOP"
        assert "R3" in event.decision_code

    def test_no_exception_on_all_missing(self, runner, ingest) -> None:
        """Alle Signale fehlen → keine Exception, sicherer Zustand."""
        prod, sent = runner
        event = prod.run_once()  # ingest ist leer
        assert event.decision.action == "STOP"  # sichere Defaults → R3


class TestHouseLoadFallback:
    def test_house_load_derived_from_energy_balance(self, ingest) -> None:
        """house_load_w wird aus Energiebilanz berechnet wenn nicht direkt gemessen."""
        _feed(
            ingest,
            pv_power_w=4000,
            grid_import_w=0,
            grid_export_w=1000,
            battery_soc_pct=80,
            miner_temp_c=65,
            miner_heartbeat_age_sec=5,
            miner_power_w=1500,
        )
        # house_load_w bewusst NICHT gesetzt

        raw = raw_from_ingest(ingest)
        now = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        state = build_energy_state("2024-06-15T12:00:00", now, now, raw)

        # pv(4000) + import(0) - export(1000) - miner(1500) = 1500W Basislast
        assert state.house_load_w == pytest.approx(1500.0)
        assert "house_load_w" not in state.missing_signals

    def test_surplus_correct_with_derived_house_load(self, ingest) -> None:
        """surplus_kw stimmt mit abgeleitetem house_load_w überein."""
        _feed(
            ingest,
            pv_power_w=5000,
            grid_import_w=0,
            grid_export_w=500,
            battery_soc_pct=80,
            miner_temp_c=65,
            miner_heartbeat_age_sec=5,
            miner_power_w=1000,
        )

        raw = raw_from_ingest(ingest)
        now = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        state = build_energy_state("2024-06-15T12:00:00", now, now, raw)

        # house_load = 5000 + 0 - 500 - 1000 = 3500W
        # surplus = (5000 - 3500) / 1000 = 1.5 kW
        assert state.surplus_kw == pytest.approx(1.5)


class TestDeduplication:
    def test_same_command_not_sent_twice(self, runner, ingest) -> None:
        """ActuationWriter dedupliziert — gleiche command_id → nur einmal senden."""
        prod, sent = runner
        _feed(
            ingest,
            pv_power_w=4000,
            house_load_w=600,
            grid_import_w=0,
            battery_soc_pct=80,
            miner_temp_c=65,
            miner_heartbeat_age_sec=5,
        )

        event = prod.run_once(now=datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc))

        # Gleiche command_id direkt nochmal senden
        cmd = ActuationCommand(
            target="miner_relay", action="ON", command_id=event.decision.command_id
        )
        result = prod._writer.write(cmd, "test/topic")

        assert result is False  # Duplikat erkannt
        assert len(sent) == 1  # Nur einmal wirklich gesendet
