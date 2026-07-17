"""
R3 Safety — höchste Priorität, nie überstimmbar.

Stoppt den Miner bei:
- Übertemperatur (miner_temp_c > max_chip_temp_c)
- Kommunikations-Timeout (miner_heartbeat_age_sec > comm_timeout_sec)

R3 bricht die Evaluierung aller anderen Regeln ab.
allow_unsafe_override ist hardcoded False.
"""

from __future__ import annotations

from src.core.models import EnergyState, RuleVote

# Absolute Sicherheitsgrenzen als Compile-Time-Konstanten (letzte Absicherung).
#
# _ABSOLUTE_MAX_TEMP_C war bis 2026-07-17 auf 95.0 gesetzt. Dieser Wert lag
# unterhalb des normalen Betriebsfensters der real verbauten Avalon Q: 7 Tage
# Realbetrieb (n=1033 Messpunkte bei laufendem Miner, sensor.miner_max_chip_temp_c)
# ergaben Mittel 90.8 °C, Max 113.0 °C, davon 62.3 % der Zeit >= 95 °C. Der Kern
# haette die Hardware also im Normalbetrieb dauerhaft gestoppt, und weil min()
# hier jede Config klemmt, war das nicht konfigurierbar reparierbar.
# Neuer Envelope (Nutzer-Entscheidung 2026-07-17), gestufte Verteidigung:
#   112 °C  -> MVP drosselt Super auf Standard (packages/mvp_auto.yaml)
#   115 °C  -> R3 stoppt (input_number.r3_max_chip_temp_c)
#   120 °C  -> dieses Hardcap, letzte Absicherung gegen eine verstellte Config
# Aendern nur mit neuer Messreihe, nicht nach Gefuehl.
_ABSOLUTE_MAX_TEMP_C: float = 120.0
_ABSOLUTE_MAX_HEARTBEAT_SEC: float = 300.0


def evaluate(
    state: EnergyState,
    max_chip_temp_c: float = 85.0,
    t_resume_c: float = 75.0,
    comm_timeout_sec: float = 60.0,
) -> RuleVote | None:
    """
    Gibt einen RuleVote(STOP) zurück wenn Safety greift, sonst None.

    None bedeutet: R3 hat kein Veto — andere Regeln dürfen entscheiden.
    """
    effective_max_temp = min(max_chip_temp_c, _ABSOLUTE_MAX_TEMP_C)
    effective_timeout = min(comm_timeout_sec, _ABSOLUTE_MAX_HEARTBEAT_SEC)

    if state.miner_temp_c > effective_max_temp:
        return RuleVote(
            rule="R3",
            action="STOP",
            confidence=1.0,
            reason="OVERTEMP",
        )

    if state.miner_heartbeat_age_sec > effective_timeout:
        return RuleVote(
            rule="R3",
            action="STOP",
            confidence=1.0,
            reason="COMM_TIMEOUT",
        )

    return None
