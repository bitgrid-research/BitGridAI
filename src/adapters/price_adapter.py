"""
PriceAdapter — aktueller Börsenstrompreis → energy_price_ct_kwh.

Unterstützte Quellen:
  aWATTar   — kostenlos, kein API-Key, Deutschland/Österreich
  ENTSO-E   — kostenlos nach Registrierung, alle EU-Länder
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.core.signals import Signal
from .telemetry_ingest import TelemetryIngest

log = logging.getLogger(__name__)

_HTTP_TIMEOUT = 10

_AWATTAR_URLS = {
    "de": "https://api.awattar.de/v1/marketdata",
    "at": "https://api.awattar.at/v1/marketdata",
}


class PriceAdapter:
    """
    Ruft stündlich den aktuellen Börsenstrompreis ab.

    aWATTar: kein Key, sofort nutzbar.
    ENTSO-E: Token aus https://transparency.entsoe.eu
    """

    def __init__(
        self,
        ingest: TelemetryIngest,
        source: str | None = None,
        country: str | None = None,
        poll_interval_min: float | None = None,
        vat_factor: float | None = None,
        entsoe_token: str | None = None,
        entsoe_area: str | None = None,
    ) -> None:
        self._ingest = ingest
        self._source = (source if source is not None else os.getenv("PRICE_SOURCE", "awattar")).lower()
        self._country = (country if country is not None else os.getenv("AWATTAR_COUNTRY", "de")).lower()
        self._poll_interval_sec = (
            poll_interval_min if poll_interval_min is not None
            else float(os.getenv("PRICE_POLL_MIN", "60"))
        ) * 60
        self._vat = vat_factor if vat_factor is not None else float(os.getenv("PRICE_VAT_FACTOR", "1.19"))
        self._entsoe_token = entsoe_token if entsoe_token is not None else os.getenv("ENTSOE_TOKEN", "")
        self._entsoe_area = entsoe_area if entsoe_area is not None else os.getenv(
            "ENTSOE_AREA", "10Y1001A1001A82H"
        )
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="price-poll"
        )
        self._thread.start()
        log.info(
            "PriceAdapter gestartet — Quelle: %s/%s (alle %.0f min)",
            self._source, self._country, self._poll_interval_sec / 60,
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
                log.warning("Preis-Abruf fehlgeschlagen (%s): %s", self._source, exc)

    def _poll_once(self) -> None:
        if self._source == "awattar":
            price_ct = self._fetch_awattar()
        elif self._source == "entsoe":
            price_ct = self._fetch_entsoe()
        else:
            raise ValueError(f"Unbekannte Quelle: {self._source!r}")

        self._ingest.update(
            Signal.ENERGY_PRICE_CT_KWH, price_ct,
            source=f"price:{self._source}",
        )
        log.info("Strompreis: %.2f Ct/kWh (inkl. MwSt, %s/%s)", price_ct, self._source, self._country)

    # ------------------------------------------------------------------
    # aWATTar (kostenlos, kein Key) — Bug-Fix: nutzt self._country
    # ------------------------------------------------------------------

    def _fetch_awattar(self) -> float:
        base = _AWATTAR_URLS.get(self._country, _AWATTAR_URLS["de"])
        now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        url = f"{base}?start={now_ms}"

        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read())

        items = data.get("data", [])
        if not items:
            raise RuntimeError("aWATTar: leere Antwort")

        eur_mwh = float(items[0]["marketprice"])
        return (eur_mwh / 10.0) * self._vat  # EUR/MWh → Ct/kWh inkl. MwSt

    # ------------------------------------------------------------------
    # ENTSO-E (kostenlos mit Token)
    # ------------------------------------------------------------------

    def _fetch_entsoe(self) -> float:
        if not self._entsoe_token:
            raise RuntimeError("ENTSO-E: ENTSOE_TOKEN nicht gesetzt")

        now = datetime.now(tz=timezone.utc)
        period = now.strftime("%Y%m%d%H00")
        params = {
            "securityToken": self._entsoe_token,
            "documentType": "A44",
            "in_Domain": self._entsoe_area,
            "out_Domain": self._entsoe_area,
            "periodStart": period,
            "periodEnd": period,
        }
        url = f"https://web-api.tp.entsoe.eu/api?{urlencode(params)}"

        import xml.etree.ElementTree as ET
        req = Request(url, headers={"Accept": "application/xml"})
        with urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            tree = ET.parse(resp)

        ns = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}
        price_elem = tree.getroot().find(".//ns:price.amount", ns)
        if price_elem is None or price_elem.text is None:
            raise RuntimeError("ENTSO-E: kein price.amount in Antwort")

        return (float(price_elem.text) / 10.0) * self._vat
