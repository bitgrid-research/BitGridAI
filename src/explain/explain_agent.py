"""
ExplainAgent — übersetzt DecisionEvents in menschenlesbare Texte.

Keine freien Strings im Core. Nur ExplainAgent erzeugt Texte.
Read-only: verändert nie EnergyState oder Decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from src.core.models import DecisionEvent

_TEXT_BLOCKS_PATH = Path(__file__).parent / "mappings" / "text_blocks.yaml"
_DEFAULT_LANG = "de"


@dataclass
class ExplainResult:
    decision_code: str
    short: str
    long: str
    trigger: str
    data_basis: str
    effect: str
    options: str
    params: dict[str, Any]
    rule_states: dict[str, Any]
    energy_state_ref: str
    lang: str = "de"


class ExplainAgent:
    def __init__(self, lang: str = _DEFAULT_LANG) -> None:
        self._lang = lang
        self._blocks: dict[str, Any] = self._load_blocks()

    def _load_blocks(self) -> dict[str, Any]:
        with open(_TEXT_BLOCKS_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}

    def explain(
        self,
        decision_code: str,
        params: dict[str, Any],
        rule_states: dict[str, Any] | None = None,
        energy_state_ref: str = "",
    ) -> ExplainResult:
        """
        Übersetzt einen decision_code + params in einen ExplainResult.

        Fehlende Interpolationswerte → "?" statt Exception.
        """
        lang_blocks = self._blocks.get(self._lang, self._blocks.get("de", {}))
        block = lang_blocks.get(decision_code, {})

        short = self._interpolate(block.get("short", decision_code), params)
        long = self._interpolate(block.get("long", ""), params)
        trigger = self._interpolate(block.get("trigger", ""), params)
        data_basis = self._interpolate(block.get("data_basis", ""), params)
        effect = self._interpolate(block.get("effect", ""), params)
        options = self._interpolate(block.get("options", ""), params)

        return ExplainResult(
            decision_code=decision_code,
            short=short,
            long=long,
            trigger=trigger,
            data_basis=data_basis,
            effect=effect,
            options=options,
            params=params,
            rule_states=rule_states or {},
            energy_state_ref=energy_state_ref,
            lang=self._lang,
        )

    def explain_short(self, event: "DecisionEvent") -> str:
        """Convenience-Methode für Dependency Injection in ProductionRunner."""
        return self.explain(
            event.decision_code,
            event.params,
            energy_state_ref=event.state_snapshot.block_id,
        ).short

    def _interpolate(self, template: str, params: dict[str, Any]) -> str:
        """Interpoliert {key} und {key:.nf} — fehlende Keys → '?'."""
        if not template:
            return ""
        try:
            return template.format_map(_SafeDict(params))
        except Exception:
            return template


class _Missing:
    """Gibt '?' für jeden Format-Spec zurück, damit {key:.0f} nicht wirft."""

    def __format__(self, spec: str) -> str:
        return "?"

    def __str__(self) -> str:
        return "?"


class _SafeDict(dict[str, Any]):
    """Gibt _Missing zurück für fehlende oder None-Keys — safe für alle Format-Specs."""

    def __missing__(self, key: str) -> _Missing:
        return _Missing()

    def __getitem__(self, key: str) -> Any:
        value = super().__getitem__(key) if key in self else None
        if value is None:
            return _Missing()
        return value
