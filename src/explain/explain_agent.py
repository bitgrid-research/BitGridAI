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
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from src.core.models import DecisionEvent

_TEXT_BLOCKS_PATH = Path(__file__).parent / "mappings" / "text_blocks.yaml"
_B_REFERENCES_PATH = Path(__file__).parent / "mappings" / "b_references.yaml"
_HAMSTER_STATES_PATH = Path(__file__).parent / "mappings" / "hamster_states.yaml"
_DEFAULT_LANG = "de"

# Systemanweisung für den LLM-Prompt (Gruppe B). Eine einzige, generische
# Laien-Stimme. Keine Persona-Achse: die Studie vergleicht nur A (statisch) vs.
# B (LLM), ohne nutzertyp-spezifische Frames.
_B_INSTRUCTION: str = (
    "Du bist ein freundlicher Assistent für eine Heimsolar-App. "
    "Das System steuert einen Miner, der läuft wenn die Solaranlage mehr Strom erzeugt "
    "als das Haus gerade braucht, also bei Solarüberschuss. "
    "Die Batterie ist der Hausspeicher. "
    "Sprich den Nutzer direkt an ('du'). "
    "Benutze einfache Alltagssprache: 'dein Solarstrom', 'der Miner', 'dein Speicher'. "
    "Keine Abkürzungen, kein Englisch, kein Chinesisch. "
    "Antworte immer auf Deutsch."
)

log = logging.getLogger(__name__)


def load_b_references(lang: str = _DEFAULT_LANG) -> dict[str, str]:
    """Lädt die Gruppe-B-Gold-Referenz je decision_code: Code → Idealsatz.

    Dient als Few-Shot-Anker im LLM-Prompt (Gruppe B) und als Vergleichsziel
    (Gold-Referenz) bei der Güte-Bewertung des echten LLM-Outputs. Fehlt die
    Datei, wird {} zurückgegeben.
    """
    try:
        with open(_B_REFERENCES_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    blocks = data.get(lang, data.get("de", {}))
    if not isinstance(blocks, dict):
        return {}
    return {str(k): str(v) for k, v in blocks.items()}


def load_hamster_states(lang: str = _DEFAULT_LANG) -> dict[str, dict[str, str]]:
    """Lädt Hamster-Anzeigezustände je Aktion (START/THROTTLE/NOOP/STOP).

    Die Anzeige spiegelt die Systementscheidung des 10-Minuten-Blocks und ist
    unabhängig von der Formulierung. Fehlt die Datei, wird {} zurückgegeben.
    """
    try:
        with open(_HAMSTER_STATES_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    blocks = data.get(lang, data.get("de", {}))
    return blocks if isinstance(blocks, dict) else {}


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
        self._b_references: dict[str, str] = load_b_references(lang)
        self._ollama_host: str = os.getenv("OLLAMA_HOST", "").rstrip("/")
        self._ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
        self._ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT_SEC", "30"))

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
        # Few-Shot-Anker: Gruppe-B-Gold-Referenz bevorzugen, sonst Block-Beispiel.
        example = self._b_references.get(decision_code, "") or block.get("example", "")

        if self._ollama_host:
            llm_short = self._call_ollama(
                decision_code, trigger, effect, data_basis, example
            )
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
        example: str = "",
    ) -> str | None:
        """Ruft Ollama auf und gibt einen natürlichsprachlichen Satz zurück.

        Gibt None zurück bei Timeout, Verbindungsfehler oder leerem Response.
        Template-Wert bleibt als Fallback erhalten.
        """
        example_line = (
            example
            or "Der Miner läuft, deine Anlage erzeugt 1,5 kW mehr als du verbrauchst."
        )
        prompt = (
            f"{_B_INSTRUCTION}\n\n"
            "Schreibe genau EINEN vollständigen deutschen Satz (max. 25 Wörter). "
            "Nenne mindestens EINE konkrete Zahl aus den Messwerten. "
            "Keine Einleitung, kein Bullet-Point, kein Englisch, kein Chinesisch.\n"
            f"Beispiel für diese Situation: '{example_line}'\n\n"
            f"Was passiert: {effect}\n"
            f"Warum: {trigger}\n"
            f"Messwerte: {data_basis}\n"
        )
        body = json.dumps(
            {
                "model": self._ollama_model,
                "prompt": prompt,
                "stream": False,
                "think": False,  # disable qwen3 thinking-mode so output goes to "response"
                "options": {"num_predict": 60, "temperature": 0.3},
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


class _DeNum:
    """Formatiert Zahlen mit deutschem Dezimalkomma (3.0 → 3,0, 28.0 → 28,0)."""

    def __init__(self, value: float) -> None:
        self._value = value

    def __format__(self, spec: str) -> str:
        return format(self._value, spec).replace(".", ",")

    def __str__(self) -> str:
        return str(self._value).replace(".", ",")


class _SafeDict(dict[str, Any]):
    """Gibt _Missing zurück für fehlende oder None-Keys — safe für alle Format-Specs."""

    def __missing__(self, key: str) -> _Missing:
        return _Missing()

    def __getitem__(self, key: str) -> Any:
        value = super().__getitem__(key) if key in self else None
        if value is None:
            return _Missing()
        # Zahlen mit deutschem Dezimalkomma rendern (bool bleibt unangetastet)
        if not isinstance(value, bool) and isinstance(value, (int, float)):
            return _DeNum(value)
        return value
