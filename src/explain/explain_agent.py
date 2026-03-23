"""
ExplainAgent — übersetzt DecisionEvents in menschenlesbare Texte.

Keine freien Strings im Core. Nur ExplainAgent erzeugt Texte.
Read-only: verändert nie EnergyState oder Decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_TEXT_BLOCKS_PATH = Path(__file__).parent / "mappings" / "text_blocks.yaml"
_DEFAULT_LANG = "de"


@dataclass
class ExplainResult:
    decision_code: str
    short: str
    long: str
    trigger: str
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

        return ExplainResult(
            decision_code=decision_code,
            short=short,
            long=long,
            trigger=trigger,
            params=params,
            rule_states=rule_states or {},
            energy_state_ref=energy_state_ref,
            lang=self._lang,
        )

    def _interpolate(self, template: str, params: dict[str, Any]) -> str:
        """Interpoliert {key} und {key:.nf} — fehlende Keys → '?'."""
        if not template:
            return ""
        try:
            return template.format_map(_SafeDict(params))
        except Exception:
            return template


class _SafeDict(dict[str, Any]):
    """Gibt '?' zurück für fehlende Keys statt KeyError."""

    def __missing__(self, key: str) -> str:
        return "?"
