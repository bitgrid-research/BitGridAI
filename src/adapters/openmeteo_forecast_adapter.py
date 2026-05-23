"""
OpenMeteoForecastAdapter — PV-Ertragsprognose via Open-Meteo API.

Kein API-Key erforderlich. Liefert global_tilted_irradiance (W/m²)
für die tatsächliche Panel-Neigung und wird in geschätzte PV-Leistung (kW)
umgerechnet: pv_kw = (gti_W_m2 / 1000) * kwp * performance_ratio

Ersetzt ForecastAdapter (forecast.solar) — gleiche Schnittstelle,
kein Rate-Limit, kein Account.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.core.signals import Signal
from src.adapters.telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)

_BASE_URL = "https://api.open-meteo.com/v1/forecast"
_HTTP_TIMEOUT = 10
_PERFORMANCE_RATIO = 0.75  # typischer PR für Aufdach-Anlagen


class OpenMeteoForecastAdapter:
    """
    Ruft PV-Prognose von Open-Meteo ab und schreibt pv_forecast_kw in TelemetryIngest.

    Parameter werden via Konstruktor oder Umgebungsvariablen gesetzt:
      FORECAST_LAT, FORECAST_LON, FORECAST_DEC (Neigung °), FORECAST_AZ (Azimut °),
      FORECAST_KWP, FORECAST_POLL_MIN, FORECAST_HORIZON_MIN
    """

    def __init__(
        self,
        ingest: TelemetryIngest,
        lat: float | None = None,
        lon: float | None = None,
        tilt: int | None = None,
        azimuth: int | None = None,
        kwp: float | None = None,
        poll_interval_min: float | None = None,
        horizon_min: int | None = None,
        publish_fn: Callable[[str, str], None] | None = None,
        mqtt_topic: str = "bitgrid/forecast/pv_kw",
    ) -> None:
        self._ingest = ingest
        self._lat = lat if lat is not None else float(os.getenv("FORECAST_LAT", "48.1"))
        self._lon = lon if lon is not None else float(os.getenv("FORECAST_LON", "11.6"))
        self._tilt = tilt if tilt is not None else int(os.getenv("FORECAST_DEC", "35"))
        self._az = (
            azimuth if azimuth is not None else int(os.getenv("FORECAST_AZ", "0"))
        )
        self._kwp = kwp if kwp is not None else float(os.getenv("FORECAST_KWP", "10.0"))
        self._poll_interval_sec = (
            poll_interval_min
            if poll_interval_min is not None
            else float(os.getenv("FORECAST_POLL_MIN", "60"))
        ) * 60
        self._horizon_min = (
            horizon_min
            if horizon_min is not None
            else int(os.getenv("FORECAST_HORIZON_MIN", "60"))
        )
        self._publish_fn = publish_fn
        self._mqtt_topic = mqtt_topic
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="openmeteo-forecast-poll"
        )
        self._thread.start()
        log.info(
            "OpenMeteoForecastAdapter gestartet — %.4f,%.4f %.1f kWp "
            "Neigung %d° Azimut %d° (Horizont: %d min)",
            self._lat,
            self._lon,
            self._kwp,
            self._tilt,
            self._az,
            self._horizon_min,
        )

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        self._poll_once()
        while self._running:
            time.sleep(self._poll_interval_sec)
            try:
                self._poll_once()
            except Exception as exc:
                log.warning("Open-Meteo Abruf fehlgeschlagen: %s", exc)

    def _poll_once(self) -> None:
        params = urlencode(
            {
                "latitude": self._lat,
                "longitude": self._lon,
                "hourly": "global_tilted_irradiance",
                "tilt": self._tilt,
                "azimuth": self._az,
                "timezone": "UTC",
                "forecast_days": 1,
            }
        )
        url = f"{_BASE_URL}?{params}"
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read())

        times: list[str] = data["hourly"]["time"]
        gti_values: list[float] = data["hourly"]["global_tilted_irradiance"]

        forecast_kw = self._value_at_horizon(times, gti_values)
        self._ingest.update(Signal.PV_FORECAST_KW, forecast_kw, source="open-meteo")
        if self._publish_fn is not None:
            self._publish_fn(self._mqtt_topic, f"{forecast_kw:.2f}")
        log.info(
            "PV-Prognose in %d min: %.2f kW (GTI→kW via %.1f kWp PR=%.2f)",
            self._horizon_min,
            forecast_kw,
            self._kwp,
            _PERFORMANCE_RATIO,
        )

    def _value_at_horizon(self, times: list[str], values: list[float]) -> float:
        """Wählt den GTI-Wert am nächsten zum Horizont-Zeitpunkt, konvertiert zu kW."""
        target = datetime.now(tz=timezone.utc) + timedelta(minutes=self._horizon_min)
        best_idx: int | None = None
        best_delta: float | None = None

        for i, ts in enumerate(times):
            try:
                dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
                delta = abs((dt - target).total_seconds())
                if best_delta is None or delta < best_delta:
                    best_delta = delta
                    best_idx = i
            except ValueError:
                continue

        if best_idx is None:
            return 0.0

        gti_w_m2 = values[best_idx]
        return (gti_w_m2 / 1000.0) * self._kwp * _PERFORMANCE_RATIO
