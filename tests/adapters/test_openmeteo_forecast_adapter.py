"""Tests für OpenMeteoForecastAdapter."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.openmeteo_forecast_adapter import (
    OpenMeteoForecastAdapter,
    _PERFORMANCE_RATIO,
)
from src.adapters.telemetry_ingest import TelemetryIngest
from src.core.signals import Signal


def _make_response(times: list[str], gti_values: list[float]) -> bytes:
    return json.dumps(
        {"hourly": {"time": times, "global_tilted_irradiance": gti_values}}
    ).encode()


def _adapter(
    ingest: TelemetryIngest, **kwargs: float | int
) -> OpenMeteoForecastAdapter:
    defaults: dict[str, float | int] = dict(
        lat=48.1,
        lon=11.6,
        tilt=35,
        azimuth=0,
        kwp=10.0,
        poll_interval_min=60,
        horizon_min=60,
    )
    defaults.update(kwargs)
    return OpenMeteoForecastAdapter(ingest=ingest, **defaults)


class TestValueAtHorizon:
    def test_nearest_timestamp_selected(self) -> None:
        ingest = TelemetryIngest()
        adapter = _adapter(ingest)

        now = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
        horizon = now + timedelta(minutes=60)

        # Zwei Einträge: einer genau am Horizont, einer weit entfernt
        t_near = horizon.strftime("%Y-%m-%dT%H:%M")
        t_far = (horizon + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")
        times = [t_far, t_near]
        values = [999.0, 500.0]

        result = adapter._value_at_horizon(times, values)
        expected = (500.0 / 1000.0) * 10.0 * _PERFORMANCE_RATIO
        assert abs(result - expected) < 0.001

    def test_gti_to_kw_conversion(self) -> None:
        ingest = TelemetryIngest()
        adapter = _adapter(ingest, kwp=5.0)

        now = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
        t = (now + timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M")

        # 800 W/m² × 5 kWp × 0.75 = 3.0 kW
        result = adapter._value_at_horizon([t], [800.0])
        assert abs(result - 3.0) < 0.001

    def test_empty_list_returns_zero(self) -> None:
        ingest = TelemetryIngest()
        adapter = _adapter(ingest)
        assert adapter._value_at_horizon([], []) == 0.0

    def test_zero_irradiance_at_night(self) -> None:
        ingest = TelemetryIngest()
        adapter = _adapter(ingest)

        now = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
        t = (now + timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M")

        assert adapter._value_at_horizon([t], [0.0]) == 0.0


class TestPollOnce:
    def test_poll_once_writes_signal(self) -> None:
        ingest = TelemetryIngest()
        adapter = _adapter(ingest)

        now = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
        t = (now + timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M")
        response_body = _make_response([t], [400.0])

        mock_resp = MagicMock()
        mock_resp.read.return_value = response_body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch(
            "src.adapters.openmeteo_forecast_adapter.urlopen", return_value=mock_resp
        ):
            adapter._poll_once()

        value = ingest.get_value(Signal.PV_FORECAST_KW)
        expected = (400.0 / 1000.0) * 10.0 * _PERFORMANCE_RATIO
        assert value is not None
        assert abs(value - expected) < 0.001
