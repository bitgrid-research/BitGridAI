# 064 – Runtime: Manueller Override

> **Kurzüberblick:**  
> Nutzer kann **Start/Stop/Level** temporär setzen (`ttl_blocks`), wird geloggt als `manual_override` und fällt am Blockende automatisch zur Policy zurück.

> **TL;DR (EN):**  
> User can temporarily set start/stop/level with TTL; logged as `manual_override`, auto-rollback at block end.

---

## Ablauf / Sequence

1. UI/API sendet `POST /override {action, ttl_blocks, note}`.  
2. **Rule Engine** akzeptiert, setzt `valid_until_block`; Safety (R2/R3) bleibt vorrangig.  
3. **Actuation** führt Aktion aus (start/stop/set_power).  
4. **Explainability/UI** zeigt Override-Chip mit Countdown; Timeline markiert `manual_override`.  
5. Nach TTL/Blockende automatischer Rücksprung zur Policy; UI bestätigt.

---

## Parameter (MVP)

- `max_override_blocks = 3` (≈30 min).  
- Safety (R2/R3) kann Override jederzeit beenden.  
- DecisionEvent Reason: `manual_override`, `override_ttl`, optional `note`.
