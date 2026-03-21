"""
ForecastAdapter — PV-Ertragsprognose → pv_forecast_kw.

Quelle: forecast.solar (kostenlos, kein API-Key für Basis-Nutzung)
R4 nutzt pv_forecast_kw um Mining zu stoppen wenn Sonne bald wegfällt.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

from src.core.signals import Signal
from .telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)

_HTTP_TIMEOUT = 10


class ForecastAdapter:
    """
    Ruft PV-Prognose von forecast.solar ab.

    pv_forecast_kw = erwartete Leistung in horizon_min Minuten.
    """

    def __init__(
        self,
        ingest: TelemetryIngest,
        lat: float | None = None,
        lon: float | None = None,
        declination: int | None = None,
        azimuth: int | None = None,
        kwp: float | None = None,
        poll_interval_min: float | None = None,
        horizon_min: int | None = None,
    ) -> None:
        self._ingest = ingest
        self._lat = lat if lat is not None else float(os.getenv("FORECAST_LAT", "48.1"))
        self._lon = lon if lon is not None else float(os.getenv("FORECAST_LON", "11.6"))
        self._dec = declination if declination is not None else int(os.getenv("FORECAST_DEC", "35"))
        self._az = azimuth if azimuth is not None else int(os.getenv("FORECAST_AZ", "0"))
        self._kwp = kwp if kwp is not None else float(os.getenv("FORECAST_KWP", "10.0"))
        self._poll_interval_sec = (
            poll_interval_min if poll_interval_min is not None
            else float(os.getenv("FORECAST_POLL_MIN", "60"))
        ) * 60
        self._horizon_min = (
            horizon_min if horizon_min is not None
            else int(os.getenv("FORECAST_HORIZON_MIN", "60"))
        )
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="forecast-poll"
        )
        self._thread.start()
        log.info(
            "ForecastAdapter gestartet — %.4f,%.4f %.1f kWp (Horizont: %d min)",
            self._lat, self._lon, self._kwp, self._horizon_min,
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
                log.warning("Forecast-Abruf fehlgeschlagen: %s", exc)

    def _poll_once(self) -> None:
        url = (
            f"https://api.forecast.solar/estimate"
            f"/{self._lat}/{self._lon}/{self._dec}/{self._az}/{self._kwp}"
        )
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read())

        watts_map: dict[str, float] = data.get("result", {}).get("watts", {})
        if not watts_map:
            log.warning("Forecast: leere watts-Map")
            return

        forecast_kw = self._nearest_to_horizon(watts_map)
        self._ingest.update(Signal.PV_FORECAST_KW, forecast_kw, source="forecast.solar")
        log.info("PV-Prognose in %d min: %.2f kW", self._horizon_min, forecast_kw)

    def _nearest_to_horizon(self, watts_map: dict[str, float]) -> float:
        """Wählt den Prognosewert der dem Horizont-Zeitpunkt am nächsten liegt."""
        target = datetime.now(tz=timezone.utc) + timedelta(minutes=self._horizon_min)
        best_key: str | None = None
        best_delta: float | None = None

        for key in watts_map:
            try:
                dt = datetime.fromisoformat(key.replace(" ", "T"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                delta = abs((dt - target).total_seconds())
                if best_delta is None or delta < best_delta:
                    best_delta = delta
                    best_key = key
            except ValueError:
                continue

        return watts_map[best_key] / 1000.0 if best_key else 0.0
