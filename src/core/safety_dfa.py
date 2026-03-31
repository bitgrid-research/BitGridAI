"""
R3 Safety as a formal Deterministic Finite Automaton (DFA).

Theoretical background (ABK W2):
    Q = finite set of states
    Σ = input alphabet (discretized sensor tokens)
    δ = transition function Q × Σ → Q
    q0 = initial state
    F = set of accepting states

This DFA is equivalent to the Typ-3 (regular) grammar derived from R3.
It is deterministic, replay-safe, and fully testable without mocks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from src.core.models import EnergyState


# ---------------------------------------------------------------------------
# Alphabet Σ — discretized input tokens
# ---------------------------------------------------------------------------

SensorToken = Literal[
    "temp_ok",
    "temp_hot",
    "comm_ok",
    "comm_lost",
]


def discretize(state: EnergyState, cfg: "SafetyDFAConfig") -> list[SensorToken]:
    """Map a raw EnergyState to a sequence of SensorTokens (Σ*)."""
    tokens: list[SensorToken] = []
    tokens.append(
        "temp_hot" if state.miner_temp_c > cfg.max_chip_temp_c else "temp_ok"
    )
    tokens.append(
        "comm_lost"
        if state.miner_heartbeat_age_sec > cfg.comm_timeout_sec
        else "comm_ok"
    )
    return tokens


# ---------------------------------------------------------------------------
# States Q
# ---------------------------------------------------------------------------


class SafetyState(str, Enum):
    """States of the R3 Safety DFA."""

    CHECKING = "CHECKING"   # initial state — evaluating inputs
    SAFE = "SAFE"           # all checks passed → miner may run
    STOPPED = "STOPPED"     # safety veto → miner must stop


# ---------------------------------------------------------------------------
# Transition function δ: Q × Σ → Q
# ---------------------------------------------------------------------------

# δ[current_state][token] = next_state
_DELTA: dict[SafetyState, dict[SensorToken, SafetyState]] = {
    SafetyState.CHECKING: {
        "temp_ok":   SafetyState.CHECKING,   # still checking comm
        "temp_hot":  SafetyState.STOPPED,
        "comm_ok":   SafetyState.SAFE,
        "comm_lost": SafetyState.STOPPED,
    },
    SafetyState.SAFE: {
        "temp_ok":   SafetyState.SAFE,
        "temp_hot":  SafetyState.STOPPED,
        "comm_ok":   SafetyState.SAFE,
        "comm_lost": SafetyState.STOPPED,
    },
    SafetyState.STOPPED: {
        # Once stopped, only a fresh evaluation (reset) can recover.
        # Within a single block the DFA stays stopped.
        "temp_ok":   SafetyState.STOPPED,
        "temp_hot":  SafetyState.STOPPED,
        "comm_ok":   SafetyState.STOPPED,
        "comm_lost": SafetyState.STOPPED,
    },
}


# ---------------------------------------------------------------------------
# DFA
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SafetyDFAConfig:
    max_chip_temp_c: float = 85.0
    comm_timeout_sec: float = 60.0


@dataclass
class SafetyDFA:
    """
    Formal DFA for the R3 Safety rule.

    Usage::

        dfa = SafetyDFA()
        result = dfa.run(energy_state)
        if result.vetoed:
            # R3 says STOP
    """

    cfg: SafetyDFAConfig = field(default_factory=SafetyDFAConfig)

    # q0 — initial state (reset at the start of every block)
    _state: SafetyState = field(default=SafetyState.CHECKING, init=False, repr=False)
    _trace: list[tuple[SensorToken, SafetyState]] = field(
        default_factory=list, init=False, repr=False
    )

    # F — accepting states (= safety passed, no veto)
    ACCEPTING: frozenset[SafetyState] = field(
        default=frozenset({SafetyState.SAFE}), init=False, repr=False
    )

    def reset(self) -> None:
        """Reset to q0 — call at the start of each new block."""
        self._state = SafetyState.CHECKING
        self._trace = []

    def step(self, token: SensorToken) -> SafetyState:
        """Apply one transition δ(q, token) → q'."""
        next_state = _DELTA[self._state][token]
        self._trace.append((token, next_state))
        self._state = next_state
        return self._state

    def run(self, state: EnergyState) -> "SafetyDFAResult":
        """
        Evaluate a full EnergyState:
        1. Reset DFA
        2. Discretize state → token sequence
        3. Feed tokens through DFA
        4. Return result
        """
        self.reset()
        tokens = discretize(state, self.cfg)
        for token in tokens:
            self.step(token)

        accepted = self._state in self.ACCEPTING
        return SafetyDFAResult(
            final_state=self._state,
            vetoed=not accepted,
            reason=_veto_reason(self._trace),
            trace=list(self._trace),
        )


@dataclass(frozen=True)
class SafetyDFAResult:
    final_state: SafetyState
    vetoed: bool           # True → R3 says STOP
    reason: str            # machine-readable reason code
    trace: list[tuple[SensorToken, SafetyState]]


def _veto_reason(trace: list[tuple[SensorToken, SafetyState]]) -> str:
    for token, state in trace:
        if state == SafetyState.STOPPED:
            if token == "temp_hot":
                return "OVERTEMP"
            if token == "comm_lost":
                return "COMM_TIMEOUT"
    return "SAFE"
