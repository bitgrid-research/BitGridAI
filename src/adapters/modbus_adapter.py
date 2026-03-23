"""
ModbusAdapter — generischer Modbus-TCP-Adapter für Batterie-BMS.

Register-Adressen je Hersteller:
  Pylontech:  0x0000  scale=1.0
  BYD:        0x0100  scale=0.1
  Victron:    840     scale=0.1  (Venus OS Modbus TCP)
  Deye/Growatt: 103   scale=1.0

Dependency: pip install 'pymodbus>=3.0'
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import TYPE_CHECKING

from src.core.signals import Signal
from .telemetry_ingest import TelemetryIngest

if TYPE_CHECKING:
    from pymodbus.client import ModbusTcpClient

log = logging.getLogger(__name__)


class ModbusAdapter:
    """
    Pollt Batterie-SoC über Modbus TCP.

    Lazy-Connect mit automatischem Reconnect bei Verbindungsabbruch.
    """

    def __init__(
        self,
        ingest: TelemetryIngest,
        host: str | None = None,
        port: int | None = None,
        soc_register: int | None = None,
        soc_scale: float | None = None,
        unit_id: int | None = None,
        poll_interval_sec: float | None = None,
    ) -> None:
        self._ingest = ingest
        self._host = (
            host if host is not None else os.getenv("MODBUS_HOST", "192.168.1.100")
        )
        self._port = port if port is not None else int(os.getenv("MODBUS_PORT", "502"))
        self._soc_register = (
            soc_register
            if soc_register is not None
            else int(os.getenv("MODBUS_SOC_REG", "0x0000"), 0)
        )
        self._soc_scale = (
            soc_scale
            if soc_scale is not None
            else float(os.getenv("MODBUS_SOC_SCALE", "1.0"))
        )
        self._unit_id = (
            unit_id if unit_id is not None else int(os.getenv("MODBUS_UNIT_ID", "1"))
        )
        self._poll_interval_sec = (
            poll_interval_sec
            if poll_interval_sec is not None
            else float(os.getenv("MODBUS_POLL_SEC", "10"))
        )
        self._running = False
        self._thread: threading.Thread | None = None
        self._client: ModbusTcpClient | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="modbus-poll"
        )
        self._thread.start()
        log.info(
            "ModbusAdapter gestartet — %s:%s Reg=0x%04X",
            self._host,
            self._port,
            self._soc_register,
        )

    def stop(self) -> None:
        self._running = False
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass

    def _loop(self) -> None:
        while self._running:
            try:
                self._poll_once()
            except Exception as exc:
                log.warning("Modbus-Poll fehlgeschlagen: %s", exc)
                self._client = None
            time.sleep(self._poll_interval_sec)

    def _poll_once(self) -> None:
        client = self._get_client()
        result = client.read_holding_registers(
            address=self._soc_register,
            count=1,
            slave=self._unit_id,
        )
        if result.isError():
            raise RuntimeError(f"Modbus-Fehler: {result}")

        soc_pct = max(0.0, min(100.0, result.registers[0] * self._soc_scale))
        self._ingest.update(
            Signal.BATTERY_SOC_PCT,
            soc_pct,
            source=f"modbus:{self._host}:reg{self._soc_register:#06x}",
        )
        log.debug("Modbus SoC: %.1f %%", soc_pct)

    def _get_client(self) -> ModbusTcpClient:
        if self._client is None:
            try:
                from pymodbus.client import ModbusTcpClient
            except ImportError:
                raise ImportError(
                    "pymodbus nicht installiert: pip install 'pymodbus>=3.0'"
                )
            self._client = ModbusTcpClient(host=self._host, port=self._port, timeout=5)
            self._client.connect()
        assert self._client is not None
        return self._client
