"""
ActuationWriter — übersetzt Decisions in Aktor-Kommandos.

Idempotenz: gleiche command_id → keine zweite Nachricht.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Callable

log = logging.getLogger(__name__)

_DEDUP_CACHE_SIZE = 10


@dataclass
class ActuationCommand:
    target: str          # z.B. "miner_relay"
    action: str          # "ON" | "OFF"
    command_id: str
    source: str = "bitgrid/core"


class ActuationWriter:
    """Sendet Aktor-Kommandos via MQTT, dedupliziert nach command_id."""

    def __init__(self, publish_fn: Callable[[str, str], None]) -> None:
        self._publish = publish_fn
        self._seen: deque[str] = deque(maxlen=_DEDUP_CACHE_SIZE)

    def write(self, cmd: ActuationCommand, topic: str) -> bool:
        """
        Sendet ein Kommando. Gibt False zurück wenn bereits gesendet.
        """
        if cmd.command_id in self._seen:
            log.debug("Duplikat übersprungen: %s", cmd.command_id)
            return False

        self._publish(topic, cmd.action)
        self._seen.append(cmd.command_id)
        log.info("Aktor-Kommando: %s → %s auf %s", cmd.command_id, cmd.action, topic)
        return True

    def decision_to_command(
        self,
        action: str,
        command_id: str,
    ) -> ActuationCommand | None:
        """Übersetzt eine Decision-Action in ein ActuationCommand."""
        if action == "START":
            return ActuationCommand(target="miner_relay", action="ON", command_id=command_id)
        if action == "STOP":
            return ActuationCommand(target="miner_relay", action="OFF", command_id=command_id)
        return None  # NOOP / THROTTLE → kein Kommando
