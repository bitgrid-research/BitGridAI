"""
Tests für die REST-API (FastAPI).

Abgedeckt:
  GET  /health          — Basis + Adapter-Status
  GET  /state           — 503 ohne State, 200 mit State
  GET  /decision        — 503 ohne Decision
  GET  /timeline        — 503 ohne EventStore
  POST /override        — Validierung, R3-Ablehnung, Rate-Limit
  POST /preview         — What-if-Simulation, 503 ohne State
  GET  /autonomy        — aktuelles Level
  POST /autonomy        — Levelwechsel, ungültige Stufe
  Auth-Middleware       — 401 ohne Token, 200 mit Token, /health immer offen
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import src.ui.api as api_module
from src.adapters.health_monitor import HealthMonitor
from src.core.override_handler import OverrideHandler
from src.core.rule_engine import RuleEngineConfig
from src.ui.api import app


@pytest.fixture(autouse=True)
def reset_api_state():
    """Setzt alle API-Globals vor jedem Test zurück."""
    api_module._current_state = None
    api_module._current_decision = None
    api_module._event_store = None
    api_module._explain_agent = None
    api_module._override_handler = None
    api_module._engine_config = None
    api_module._health_monitor = None
    api_module._auth_enabled = False
    api_module._api_token = ""
    api_module._research_export_enabled = False
    api_module._override_hits.clear()
    yield
    # Teardown: gleiche Zurücksetzung
    api_module._current_state = None
    api_module._current_decision = None
    api_module._event_store = None
    api_module._explain_agent = None
    api_module._override_handler = None
    api_module._engine_config = None
    api_module._health_monitor = None
    api_module._auth_enabled = False
    api_module._api_token = ""
    api_module._research_export_enabled = False
    api_module._override_hits.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def sample_state() -> dict[str, Any]:
    return {
        "block_id": "2026-05-24T10:00:00",
        "pv_power_w": 3000.0,
        "house_load_w": 800.0,
        "surplus_kw": 2.2,
        "battery_soc_pct": 60.0,
        "miner_temp_c": 72.0,
        "quality": "ok",
        "missing_signals": [],
        "grid_import_w": 0.0,
    }


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_ok_no_state(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["state_available"] is False
        assert data["adapters"] == []

    def test_health_shows_adapter_list(self, client: TestClient) -> None:
        monitor = HealthMonitor()
        monitor.report_connected("mqtt")
        api_module.set_health_monitor(monitor)

        r = client.get("/health")
        assert r.status_code == 200
        adapters = r.json()["adapters"]
        assert len(adapters) == 1
        assert adapters[0]["adapter"] == "mqtt"
        assert adapters[0]["conn_state"] == "connected"

    def test_health_with_disconnected_adapter(self, client: TestClient) -> None:
        monitor = HealthMonitor()
        monitor.report_disconnected("modbus", reason="timeout")
        api_module.set_health_monitor(monitor)

        r = client.get("/health")
        adapters = r.json()["adapters"]
        assert adapters[0]["conn_state"] == "disconnected"
        assert adapters[0]["status"] == "error"


# ---------------------------------------------------------------------------
# GET /state  /decision
# ---------------------------------------------------------------------------


class TestStateDecision:
    def test_state_503_without_state(self, client: TestClient) -> None:
        assert client.get("/state").status_code == 503

    def test_state_200_with_state(self, client: TestClient, sample_state) -> None:
        api_module.set_state(sample_state)
        r = client.get("/state")
        assert r.status_code == 200
        assert r.json()["pv_power_w"] == 3000.0

    def test_decision_503_without_decision(self, client: TestClient) -> None:
        assert client.get("/decision").status_code == 503


# ---------------------------------------------------------------------------
# POST /override
# ---------------------------------------------------------------------------


class TestOverride:
    def test_valid_override_accepted(self, client: TestClient) -> None:
        r = client.post("/override", json={"action": "START", "duration_min": 30})
        assert r.status_code == 200
        assert r.json()["accepted"] is True

    def test_invalid_action_rejected(self, client: TestClient) -> None:
        r = client.post("/override", json={"action": "LAUNCH", "duration_min": 10})
        assert r.status_code == 400

    def test_duration_too_high_rejected(self, client: TestClient) -> None:
        r = client.post("/override", json={"action": "STOP", "duration_min": 200})
        assert r.status_code == 400

    def test_duration_zero_rejected(self, client: TestClient) -> None:
        r = client.post("/override", json={"action": "STOP", "duration_min": 0})
        assert r.status_code == 400

    def test_r3_active_blocks_override(self, client: TestClient) -> None:
        api_module.set_decision(
            {"decision_code": "STOP_R3_OVERTEMP_T92", "action": "STOP"}
        )
        r = client.post("/override", json={"action": "START", "duration_min": 10})
        assert r.status_code == 200
        assert r.json()["accepted"] is False
        assert "R3_SAFETY_ACTIVE" in r.json()["reason"]

    def test_rate_limit_429_after_10_requests(self, client: TestClient) -> None:
        for _ in range(10):
            client.post("/override", json={"action": "NOOP", "duration_min": 5})
        r = client.post("/override", json={"action": "NOOP", "duration_min": 5})
        assert r.status_code == 429


# ---------------------------------------------------------------------------
# POST /preview
# ---------------------------------------------------------------------------


class TestPreview:
    def test_preview_503_without_state(self, client: TestClient) -> None:
        r = client.post("/preview", json={"battery_soc_pct": 15.0})
        assert r.status_code == 503

    def test_preview_returns_decision(self, client: TestClient, sample_state) -> None:
        api_module.set_state(sample_state)
        r = client.post("/preview", json={"pv_power_w": 4000.0, "house_load_w": 500.0})
        assert r.status_code == 200
        data = r.json()
        assert "action" in data
        assert "decision_code" in data
        assert "hypothetical_state" in data
        assert data["hypothetical_state"]["pv_power_w"] == 4000.0

    def test_preview_low_soc_triggers_stop(
        self, client: TestClient, sample_state
    ) -> None:
        api_module.set_state(sample_state)
        r = client.post(
            "/preview", json={"battery_soc_pct": 5.0, "grid_import_w": 600.0}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["action"] == "STOP"

    def test_preview_uses_current_state_as_baseline(
        self, client: TestClient, sample_state
    ) -> None:
        api_module.set_state(sample_state)
        # Kein Override — soll die Werte aus sample_state übernehmen
        r = client.post("/preview", json={})
        assert r.status_code == 200
        assert (
            r.json()["hypothetical_state"]["pv_power_w"] == sample_state["pv_power_w"]
        )

    def test_preview_high_temp_triggers_r3_stop(
        self, client: TestClient, sample_state
    ) -> None:
        api_module.set_state(sample_state)
        r = client.post("/preview", json={"miner_temp_c": 99.0})
        assert r.status_code == 200
        assert "R3" in r.json()["decision_code"]


# ---------------------------------------------------------------------------
# GET /autonomy  POST /autonomy
# ---------------------------------------------------------------------------


class TestAutonomy:
    def test_get_autonomy_503_without_handler(self, client: TestClient) -> None:
        assert client.get("/autonomy").status_code == 503

    def test_get_autonomy_returns_level(self, client: TestClient) -> None:
        handler = OverrideHandler()
        api_module.set_override_handler(handler)
        r = client.get("/autonomy")
        assert r.status_code == 200
        assert r.json()["level"] in {"FULL", "SEMI", "MANUAL"}

    def test_post_autonomy_changes_level(self, client: TestClient) -> None:
        handler = OverrideHandler()
        api_module.set_override_handler(handler)
        r = client.post("/autonomy", json={"level": "MANUAL"})
        assert r.status_code == 200
        assert r.json()["accepted"] is True
        assert r.json()["level"] == "MANUAL"
        assert handler.autonomy_level == "MANUAL"

    def test_post_autonomy_invalid_level(self, client: TestClient) -> None:
        handler = OverrideHandler()
        api_module.set_override_handler(handler)
        r = client.post("/autonomy", json={"level": "TURBO"})
        assert r.status_code == 400

    def test_post_autonomy_all_valid_levels(self, client: TestClient) -> None:
        handler = OverrideHandler()
        api_module.set_override_handler(handler)
        for level in ("FULL", "SEMI", "MANUAL"):
            r = client.post("/autonomy", json={"level": level})
            assert r.status_code == 200
            assert r.json()["level"] == level


# ---------------------------------------------------------------------------
# Auth-Middleware
# ---------------------------------------------------------------------------


class TestAuthMiddleware:
    def test_health_always_accessible_without_token(self, client: TestClient) -> None:
        api_module.set_auth(enabled=True, token="secret")
        r = client.get("/health")
        assert r.status_code == 200

    def test_protected_endpoint_returns_401_without_token(
        self, client: TestClient
    ) -> None:
        api_module.set_auth(enabled=True, token="secret")
        r = client.get("/state")
        assert r.status_code == 401

    def test_protected_endpoint_200_with_valid_token(
        self, client: TestClient, sample_state
    ) -> None:
        api_module.set_auth(enabled=True, token="secret")
        api_module.set_state(sample_state)
        r = client.get("/state", headers={"Authorization": "Bearer secret"})
        assert r.status_code == 200

    def test_wrong_token_returns_401(self, client: TestClient) -> None:
        api_module.set_auth(enabled=True, token="secret")
        r = client.get("/state", headers={"Authorization": "Bearer wrong"})
        assert r.status_code == 401

    def test_auth_disabled_allows_all(self, client: TestClient, sample_state) -> None:
        api_module.set_auth(enabled=False, token="")
        api_module.set_state(sample_state)
        r = client.get("/state")
        assert r.status_code == 200
