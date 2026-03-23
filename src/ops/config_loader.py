"""
ConfigLoader — lädt, validiert und hot-reloads YAML-Konfigurationen.

Atomarer Austausch: entweder vollständig neue Config oder alte bleibt aktiv.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from src.core.rule_engine import RuleEngineConfig


@dataclass
class ReloadResult:
    success: bool
    config_version: str  # SHA256 der geladenen Datei
    errors: list[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ConfigLoader:
    """Lädt eine YAML-Datei und stellt hot-reload bereit."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: dict[str, Any] = {}
        self._version: str = ""

    def load(self) -> dict[str, Any]:
        """Lädt und gibt Config-Dict zurück. Wirft bei Fehler."""
        raw = self._path.read_text(encoding="utf-8")
        data: dict[str, Any] = yaml.safe_load(raw) or {}
        self._data = data
        self._version = hashlib.sha256(raw.encode()).hexdigest()[:12]
        return data

    def hot_reload(self) -> ReloadResult:
        """Lädt neu, behält alte Config bei Fehler."""
        try:
            raw = self._path.read_text(encoding="utf-8")
            new_data: dict[str, Any] = yaml.safe_load(raw) or {}
            errors = self._validate(new_data)
            if errors:
                return ReloadResult(
                    success=False, config_version=self._version, errors=errors
                )
            self._data = new_data
            self._version = hashlib.sha256(raw.encode()).hexdigest()[:12]
            return ReloadResult(success=True, config_version=self._version, errors=[])
        except Exception as exc:
            return ReloadResult(
                success=False, config_version=self._version, errors=[str(exc)]
            )

    def _validate(self, data: dict[str, Any]) -> list[str]:
        """Einfache Strukturvalidierung — gibt Fehlerliste zurück."""
        errors: list[str] = []
        if not isinstance(data, dict):
            errors.append("Config muss ein YAML-Mapping sein")
        return errors

    @property
    def data(self) -> dict[str, Any]:
        return self._data

    @property
    def version(self) -> str:
        return self._version


def rules_to_engine_config(data: dict[str, Any]) -> "RuleEngineConfig":
    """
    Konvertiert geladenes rules.yaml-Dict → RuleEngineConfig.

    Fehlende Schlüssel → Defaults aus RuleEngineConfig.__init__.
    """
    from src.core.rule_engine import RuleEngineConfig

    r = data.get("rules", {})
    r1 = r.get("r1", {})
    r2 = r.get("r2", {})
    r3 = r.get("r3", {})
    r4 = r.get("r4", {})
    r5 = r.get("r5", {})

    return RuleEngineConfig(
        surplus_min_kw=r1.get("surplus_min_kw", 1.5),
        price_max_ct_kwh=r1.get("price_max_ct_kwh", 25.0),
        soc_soft_min_pct=r2.get("soc_soft_min_pct", 20.0),
        soc_hard_min_pct=r2.get("soc_hard_min_pct", 10.0),
        max_grid_import_w=r2.get("max_grid_import_w", 500.0),
        max_chip_temp_c=r3.get("max_chip_temp_c", 85.0),
        t_resume_c=r3.get("t_resume_c", 75.0),
        comm_timeout_sec=r3.get("comm_timeout_sec", 60.0),
        min_predicted_surplus_kw=r4.get("min_predicted_surplus_kw", 2.0),
        price_spike_threshold_ct=r4.get("price_spike_threshold_ct", 30.0),
        deadband_hold_blocks=r5.get("deadband_hold_blocks", 2),
        min_runtime_blocks=r5.get("min_runtime_blocks", 3),
        min_pause_blocks=r5.get("min_pause_blocks", 2),
    )
