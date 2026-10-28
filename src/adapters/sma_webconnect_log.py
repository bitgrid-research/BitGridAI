"""
SmaWebConnectLog - liest die Ertragslogs eines SMA-Wechselrichters lokal aus.

Zweck ist die Datenrettung: Das Geraet fuehrt seine Zaehlerstaende unabhaengig
von Home Assistant weiter. Faellt die Erfassung aus, laesst sich der Zeitraum
aus diesen Logs exakt rekonstruieren, ohne Sunny Portal und ohne Cloud.

Der Wechselrichter erlaubt nur vier gleichzeitige Sessions, und pysmaplus
belegt davon selbst eine. Deshalb ist die Klasse ein Context Manager, der die
Session im finally-Zweig garantiert wieder freigibt:

    with SmaWebConnectLog(host, password) as device:
        yields = device.day_yields(start, end)

Kein requests: das Projekt kommt ohne diese Abhaengigkeit aus, urllib reicht.
"""

from __future__ import annotations

import json
import logging
import ssl
from datetime import date, datetime, timezone
from types import TracebackType
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)

# Logger-Keys der WebConnect-Schnittstelle
KEY_5MIN = 28672  # Ertragslog, ein Zaehlerstand alle fuenf Minuten
KEY_DAILY = 28704  # Tageslog, ein Zaehlerstand je Mitternacht


class SmaWebConnectError(RuntimeError):
    """Login, Abfrage oder Antwortformat des Wechselrichters fehlgeschlagen."""


class SmaWebConnectLog:
    """
    Liest Zaehlerstands-Logs ueber die WebConnect-JSON-Schnittstelle.

    right: Zugriffsebene, "usr" (Benutzer) genuegt fuer die Ertragslogs.
    """

    def __init__(
        self,
        host: str,
        password: str,
        right: str = "usr",
        timeout: int = 30,
    ) -> None:
        if not host:
            raise ValueError("host ist leer: SMA_HOST in .env setzen")
        if not password:
            raise ValueError("password ist leer: SMA_PASSWORD in .env setzen")
        self._base = f"https://{host}"
        self._password = password
        self._right = right
        self._timeout = timeout
        self._sid: str | None = None
        # Der Wechselrichter liefert ein selbstsigniertes Zertifikat.
        self._ssl = ssl.create_default_context()
        self._ssl.check_hostname = False
        self._ssl.verify_mode = ssl.CERT_NONE

    # -- Session ------------------------------------------------------------

    def __enter__(self) -> SmaWebConnectLog:
        self.login()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.logout()

    def login(self) -> None:
        data = self._post(
            "/dyn/login.json", {"right": self._right, "pass": self._password}
        )
        result = data.get("result")
        sid = result.get("sid") if isinstance(result, dict) else None
        if not sid:
            raise SmaWebConnectError(
                f"Login abgelehnt (right={self._right}). "
                f"Antwort: {json.dumps(data)[:200]}"
            )
        self._sid = str(sid)
        log.debug("SMA-Session geoeffnet")

    def logout(self) -> None:
        """Gibt die Session frei. Fehler werden geloggt, nicht geworfen."""
        if not self._sid:
            return
        try:
            self._post(f"/dyn/logout.json?sid={self._sid}", {})
            log.debug("SMA-Session freigegeben")
        except (SmaWebConnectError, URLError, OSError) as err:
            # Nicht werfen: sonst verdeckt ein Logout-Fehler das eigentliche
            # Ergebnis. Die Session laeuft serverseitig ohnehin ab.
            log.warning("SMA-Logout fehlgeschlagen, Session laeuft ab: %s", err)
        finally:
            self._sid = None

    # -- Abfragen -----------------------------------------------------------

    def meter_series(
        self, start: datetime, end: datetime
    ) -> list[tuple[datetime, int]]:
        """Zaehlerstaende in Wh im Fuenf-Minuten-Raster, aufsteigend nach Zeit."""
        return self._logger_series(KEY_5MIN, start, end)

    def day_yields(self, start: datetime, end: datetime) -> dict[date, float]:
        """
        Tagesertraege in kWh, Schluessel ist der Tag in lokaler Zeit.

        Das Tageslog liefert den Zaehlerstand je Mitternacht. Der Zuwachs
        zwischen zwei Eintraegen ist der Ertrag des davorliegenden Tages.
        """
        rows = self._logger_series(KEY_DAILY, start, end)
        out: dict[date, float] = {}
        for (prev_ts, prev_v), (_, cur_v) in zip(rows, rows[1:]):
            out[prev_ts.astimezone().date()] = round((cur_v - prev_v) / 1000, 3)
        return out

    def _logger_series(
        self, key: int, start: datetime, end: datetime
    ) -> list[tuple[datetime, int]]:
        if self._sid is None:
            raise SmaWebConnectError(
                "Keine Session: login() oder Context Manager nutzen"
            )
        payload: dict[str, Any] = {
            "destDev": [],
            "key": key,
            "tStart": int(start.timestamp()),
            "tEnd": int(end.timestamp()),
        }
        data = self._post(f"/dyn/getLogger.json?sid={self._sid}", payload)
        result = data.get("result")
        if not isinstance(result, dict):
            raise SmaWebConnectError(
                f"Unerwartete Antwort auf key {key}: {json.dumps(data)[:200]}"
            )

        rows: list[tuple[datetime, int]] = []
        for entries in result.values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                ts, val = entry.get("t"), entry.get("v")
                if ts is None or val is None:
                    continue  # Luecke im Geraetelog, z.B. bei Firmware-Update
                rows.append(
                    (datetime.fromtimestamp(int(ts), tz=timezone.utc), int(val))
                )
        rows.sort(key=lambda row: row[0])
        return rows

    # -- HTTP ---------------------------------------------------------------

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = Request(
            f"{self._base}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=self._timeout, context=self._ssl) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except (URLError, OSError) as err:
            raise SmaWebConnectError(
                f"{self._base}{path} nicht erreichbar: {err}"
            ) from err
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as err:
            raise SmaWebConnectError(
                f"Keine JSON-Antwort von {path}: {raw[:120]}"
            ) from err
        if not isinstance(parsed, dict):
            raise SmaWebConnectError(
                f"Unerwarteter JSON-Typ von {path}: {type(parsed).__name__}"
            )
        return parsed


def resample_to_blocks(
    series: list[tuple[datetime, int]], block_minutes: int = 10
) -> dict[datetime, float]:
    """
    Rechnet Zaehlerstaende in mittlere Leistung je Block um.

    Schluessel ist der Blockbeginn (UTC), Wert die mittlere Leistung in W.
    Bloecke ohne vollstaendige Randwerte werden ausgelassen, statt sie zu
    schaetzen: ein geschaetzter Messwert ist schlimmer als ein fehlender.
    """
    if len(series) < 2:
        return {}
    by_ts = {int(ts.timestamp()): value for ts, value in series}
    known = sorted(by_ts)
    span = block_minutes * 60

    def meter_at(unix_ts: int) -> float | None:
        """Zaehlerstand, linear zwischen den benachbarten Messpunkten."""
        if unix_ts < known[0] or unix_ts > known[-1]:
            return None
        if unix_ts in by_ts:
            return float(by_ts[unix_ts])
        lo = max(t for t in known if t <= unix_ts)
        hi = min(t for t in known if t >= unix_ts)
        if hi == lo:
            return float(by_ts[lo])
        frac = (unix_ts - lo) / (hi - lo)
        return by_ts[lo] + frac * (by_ts[hi] - by_ts[lo])

    out: dict[datetime, float] = {}
    first = (known[0] // span) * span
    for block_start in range(first, known[-1], span):
        start_value = meter_at(block_start)
        end_value = meter_at(block_start + span)
        if start_value is None or end_value is None:
            continue
        watts = (end_value - start_value) * 3600 / span
        out[datetime.fromtimestamp(block_start, tz=timezone.utc)] = round(
            max(0.0, watts), 1
        )
    return out
