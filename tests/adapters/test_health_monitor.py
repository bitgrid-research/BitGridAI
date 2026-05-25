"""Unit-Tests für HealthMonitor ConnState-Tracking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.adapters.health_monitor import HealthMonitor


def test_unknown_before_any_event() -> None:
    monitor = HealthMonitor()
    health = monitor.get("mqtt")
    assert health.conn_state == "unknown"
    assert health.status == "error"


def test_report_connected_sets_state() -> None:
    monitor = HealthMonitor()
    monitor.report_connected("mqtt")
    health = monitor.get("mqtt")
    assert health.conn_state == "connected"
    assert health.status == "ok"


def test_report_disconnected_sets_error() -> None:
    monitor = HealthMonitor()
    monitor.report_connected("mqtt")
    monitor.report_disconnected("mqtt", reason="connection refused")
    health = monitor.get("mqtt")
    assert health.conn_state == "disconnected"
    assert health.status == "error"
    assert "connection refused" in (health.error_message or "")


def test_report_disconnected_without_reason() -> None:
    monitor = HealthMonitor()
    monitor.report_connected("mqtt")
    monitor.report_disconnected("mqtt")
    health = monitor.get("mqtt")
    assert health.conn_state == "disconnected"


def test_reconnect_clears_disconnect_reason() -> None:
    monitor = HealthMonitor()
    monitor.report_disconnected("mqtt", reason="timeout")
    monitor.report_connected("mqtt")
    health = monitor.get("mqtt")
    assert health.conn_state == "connected"
    assert health.error_message is None


def test_stale_connected_adapter_is_warn() -> None:
    monitor = HealthMonitor(stale_warn_sec=10.0, stale_error_sec=30.0)
    monitor.report_connected("mqtt")
    # Simuliere veralteten Heartbeat durch direkten Eingriff
    past = datetime.now(tz=timezone.utc) - timedelta(seconds=20)
    monitor._last_seen["mqtt"] = past

    health = monitor.get("mqtt")
    assert health.conn_state == "connected"
    assert health.status == "warn"


def test_all_adapters_returns_all_known() -> None:
    monitor = HealthMonitor()
    monitor.report_connected("mqtt")
    monitor.report_disconnected("modbus", reason="timeout")

    adapters = monitor.all_adapters()
    names = {a.adapter for a in adapters}
    assert "mqtt" in names
    assert "modbus" in names


def test_heartbeat_updates_last_seen() -> None:
    monitor = HealthMonitor(stale_warn_sec=60.0, stale_error_sec=120.0)
    monitor.heartbeat("shelly")
    health = monitor.get("shelly")
    assert health.status == "ok"
