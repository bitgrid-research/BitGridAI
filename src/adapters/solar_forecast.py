"""
SolarForecastAdapter — lokale, deterministische PV-Prognose aus dem Sonnenstand.

Option-A-Forecast-Quelle: berechnet die Klarhimmel-PV-Obergrenze am Horizont
(``now + horizon``) rein aus der Sonnen-Geometrie, ohne Netzzugriff. Lokaler,
deterministischer Gegenpart zu den Cloud-Adaptern (``forecast.solar`` /
``open-meteo``) und damit ADR-011-konform (R4 nutzt nur lokale Quellen).

R4 verwendet den Wert als konservatives Veto gegen den Eco-Frischstart: liegt
schon die Klarhimmel-Obergrenze unter der Schwelle, steht die Sonne zu tief, um
den Start zu tragen (Schutz gegen Abend-/Morgen-Flapping). Da der Wert eine reine
Funktion von (Ort, Zeit, kWp) ist, bleibt der Entscheidungspfad replay-fähig.
"""

from __future__ import annotations

import logging
import math
import os
import threading
import time
from datetime import datetime, timedelta, timezone

from src.adapters.telemetry_ingest import TelemetryIngest
from src.core.signals import Signal

log = logging.getLogger(__name__)

_DEFAULT_PERFORMANCE_RATIO = 0.75  # typischer PR für Aufdach-Anlagen


def solar_elevation_deg(lat_deg: float, lon_deg: float, when_utc: datetime) -> float:
    """Sonnenhöhenwinkel (Grad) für Ort und UTC-Zeitpunkt.

    NOAA-Algorithmus zur Sonnenposition. Reine Funktion, deterministisch, kein
    I/O. Negativer Rückgabewert = Sonne unter dem Horizont (Nacht).
    """
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=timezone.utc)
    when_utc = when_utc.astimezone(timezone.utc)

    day_of_year = when_utc.timetuple().tm_yday
    hour = when_utc.hour + when_utc.minute / 60.0 + when_utc.second / 3600.0

    # Fraktionales Jahr (Radiant)
    gamma = 2.0 * math.pi / 365.0 * (day_of_year - 1 + (hour - 12.0) / 24.0)

    # Zeitgleichung (Minuten)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2.0 * gamma)
        - 0.040849 * math.sin(2.0 * gamma)
    )

    # Sonnendeklination (Radiant)
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2.0 * gamma)
        + 0.000907 * math.sin(2.0 * gamma)
        - 0.002697 * math.cos(3.0 * gamma)
        + 0.001480 * math.sin(3.0 * gamma)
    )

    # Wahre Ortszeit (Minuten); Zeitzonen-Offset = 0 für UTC
    time_offset = eqtime + 4.0 * lon_deg
    true_solar_time = hour * 60.0 + time_offset
    hour_angle_deg = true_solar_time / 4.0 - 180.0

    lat_rad = math.radians(lat_deg)
    ha_rad = math.radians(hour_angle_deg)
    sin_elev = math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(
        decl
    ) * math.cos(ha_rad)
    sin_elev = max(-1.0, min(1.0, sin_elev))  # numerische Sicherung für asin
    return math.degrees(math.asin(sin_elev))


def clear_sky_pv_kw(
    elevation_deg: float,
    kwp: float,
    performance_ratio: float = _DEFAULT_PERFORMANCE_RATIO,
) -> float:
    """Klarhimmel-PV-Obergrenze (kW) aus dem Sonnenhöhenwinkel.

    Obergrenze: ``P = kWp * PR * sin(Elevation)``, am Horizont auf 0 begrenzt.
    Bewusst konservativ: liegt schon dieser Bestfall (wolkenlos) unter der
    Schwelle, trägt die Sonne den Start sicher nicht.
    """
    if elevation_deg <= 0.0:
        return 0.0
    return kwp * performance_ratio * math.sin(math.radians(elevation_deg))


def forecast_pv_kw(
    lat_deg: float,
    lon_deg: float,
    when_utc: datetime,
    kwp: float,
    performance_ratio: float = _DEFAULT_PERFORMANCE_RATIO,
) -> float:
    """Klarhimmel-PV-Prognose (kW) für Ort und Zeitpunkt. Reine Funktion."""
    elevation = solar_elevation_deg(lat_deg, lon_deg, when_utc)
    return clear_sky_pv_kw(elevation, kwp, performance_ratio)


class SolarForecastAdapter:
    """Lokale PV-Prognose aus Sonnen-Geometrie (kein Netzzugriff).

    Schreibt die Klarhimmel-PV-Obergrenze am Horizont als ``pv_forecast_kw`` in
    ``TelemetryIngest`` — gleiche Schnittstelle wie die Cloud-Adapter, aber
    deterministisch und offline (ADR 011). Parameter via Konstruktor oder
    Umgebungsvariablen: ``FORECAST_LAT``, ``FORECAST_LON``, ``FORECAST_KWP``,
    ``FORECAST_PR``, ``FORECAST_POLL_MIN``, ``FORECAST_HORIZON_MIN``.
    """

    def __init__(
        self,
        ingest: TelemetryIngest,
        lat: float | None = None,
        lon: float | None = None,
        kwp: float | None = None,
        performance_ratio: float | None = None,
        poll_interval_min: float | None = None,
        horizon_min: int | None = None,
    ) -> None:
        self._ingest = ingest
        self._lat = lat if lat is not None else float(os.getenv("FORECAST_LAT", "48.1"))
        self._lon = lon if lon is not None else float(os.getenv("FORECAST_LON", "11.6"))
        self._kwp = kwp if kwp is not None else float(os.getenv("FORECAST_KWP", "10.0"))
        self._pr = (
            performance_ratio
            if performance_ratio is not None
            else float(os.getenv("FORECAST_PR", str(_DEFAULT_PERFORMANCE_RATIO)))
        )
        self._poll_interval_sec = (
            poll_interval_min
            if poll_interval_min is not None
            else float(os.getenv("FORECAST_POLL_MIN", "10"))
        ) * 60
        self._horizon_min = (
            horizon_min
            if horizon_min is not None
            else int(os.getenv("FORECAST_HORIZON_MIN", "30"))
        )
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="solar-forecast"
        )
        self._thread.start()
        log.info(
            "SolarForecastAdapter gestartet — %.4f,%.4f %.1f kWp "
            "(Horizont: %d min, lokal/deterministisch)",
            self._lat,
            self._lon,
            self._kwp,
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
            except Exception as exc:  # pragma: no cover - defensiv wie Geschwister
                log.warning("Solar-Forecast-Berechnung fehlgeschlagen: %s", exc)

    def _poll_once(self) -> None:
        target = datetime.now(tz=timezone.utc) + timedelta(minutes=self._horizon_min)
        forecast_kw = forecast_pv_kw(self._lat, self._lon, target, self._kwp, self._pr)
        self._ingest.update(Signal.PV_FORECAST_KW, forecast_kw, source="solar-geometry")
        log.info(
            "PV-Klarhimmel-Prognose in %d min: %.2f kW",
            self._horizon_min,
            forecast_kw,
        )
