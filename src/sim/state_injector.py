"""
StateInjector — injiziert EnergyStates für Tests (kein Live-I/O).

Im Sim-Modus ersetzt state_injector den Live-MQTT-Feed.
Alle Ausgaben gehen in separate bitgrid/sim/* Topics.
"""

from __future__ import annotations

from src.core.models import EnergyState


class StateInjector:
    """Hält einen injizierten EnergyState für Tests bereit."""

    def __init__(self) -> None:
        self._state: EnergyState | None = None

    def inject(self, state: EnergyState) -> None:
        self._state = state

    def get(self) -> EnergyState | None:
        return self._state

    def clear(self) -> None:
        self._state = None
