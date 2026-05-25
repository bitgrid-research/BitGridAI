"""
ExplainAgent — übersetzt DecisionEvents in menschenlesbare Texte.

Keine freien Strings im Core. Nur ExplainAgent erzeugt Texte.
Read-only: verändert nie EnergyState oder Decision.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml

if TYPE_CHECKING:
    from src.core.models import DecisionEvent

_TEXT_BLOCKS_PATH = Path(__file__).parent / "mappings" / "text_blocks.yaml"
_DEFAULT_LANG = "de"

Persona = Literal["energie", "waerme", "tech"]
_VALID_PERSONAS: set[str] = {"energie", "waerme", "tech"}

# Persona-spezifische Systemanweisungen für den LLM-Prompt.
# "energie" ist der Default — breiteste Zielgruppe, kein Mining-Vokabular.
_PERSONA_INSTRUCTIONS: dict[str, str] = {
    "energie": (
        "Du bist ein freundlicher Assistent für eine Heimsolar-App. "
        "Sprich den Nutzer direkt an ('du'). Verwende einfache Sprache: "
        "'dein Solarstrom', 'du sparst', 'Stromnetz' statt technische Abkürzungen. "
        "Vermeide alle Bitcoin- und Mining-Begriffe. "
        "Erkläre was das System macht und was das konkret für den Nutzer bedeutet."
    ),
    "waerme": (
        "Du bist ein Assistent für ein Heimsystem mit Solarpanel und einem Gerät, "
        "das gleichzeitig Wärme erzeugt. Betone den Wärmegewinn: "
        "'dein Gerät heizt gerade', 'kostenlose Wärme aus deinem Solarüberschuss'. "
        "Das Gerät (Miner) ist Mittel zum Zweck — der Fokus liegt auf der "
        "gewonnenen Wärme für Raumheizung oder Warmwasser, nicht auf Bitcoin."
    ),
    "tech": (
        "Du bist ein technischer Assistent für ein deterministisches "
        "Energiemanagementsystem. Der Nutzer kennt Regelkern, Hashrate, Pool, "
        "SoC und decision_code. Gib volle Transparenz: nenne decision_code, "
        "welche Regel ausgelöst hat (R1–R5) und konkrete Messwerte mit Einheiten."
    ),
}

log = logging.getLogger(__name__)


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
        self._ollama_host: str = os.getenv("OLLAMA_HOST", "").rstrip("/")
        self._ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
        self._ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT_SEC", "5"))
        raw_persona = os.getenv("OLLAMA_PERSONA", "energie").strip().lower()
        if raw_persona not in _VALID_PERSONAS:
            log.warning(
                "Unbekannte OLLAMA_PERSONA=%r — verwende 'energie' als Fallback",
                raw_persona,
            )
            raw_persona = "energie"
        self._persona: str = raw_persona

    @property
    def persona(self) -> str:
        return self._persona

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

        if self._ollama_host:
            llm_short = self._call_ollama(decision_code, trigger, effect, data_basis)
            if llm_short:
                short = llm_short

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

    def _call_ollama(
        self,
        code: str,
        trigger: str,
        effect: str,
        data_basis: str,
    ) -> str | None:
        """Ruft Ollama auf und gibt einen natürlichsprachlichen Satz zurück.

        Gibt None zurück bei Timeout, Verbindungsfehler oder leerem Response.
        Template-Wert bleibt als Fallback erhalten.
        """
        persona_instruction = _PERSONA_INSTRUCTIONS.get(
            self._persona, _PERSONA_INSTRUCTIONS["energie"]
        )
        prompt = (
            f"{persona_instruction}\n\n"
            "Erkläre die folgende Systementscheidung in einem einzigen natürlichen "
            "deutschen Satz. Keine Einleitung, kein Bullet-Point:\n\n"
            f"Entscheidung: {code}\n"
            f"Wirkung: {effect}\n"
            f"Auslöser: {trigger}\n"
            f"Datenbasis: {data_basis}\n"
        )
        body = json.dumps(
            {
                "model": self._ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 100, "temperature": 0.3},
            }
        ).encode()
        try:
            req = urllib.request.Request(
                f"{self._ollama_host}/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._ollama_timeout) as resp:
                data: dict[str, Any] = json.loads(resp.read())
            text = (data.get("response") or "").strip()
            return text if text else None
        except Exception as exc:
            log.debug("Ollama nicht erreichbar (%s) — Template-Fallback", exc)
            return None

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
