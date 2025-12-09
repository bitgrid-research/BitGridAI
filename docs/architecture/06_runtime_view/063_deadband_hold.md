# 063 – Runtime: Deadband / Hold (R5)

> **Kurzüberblick:**  
> **R5** stabilisiert Grenzbereiche: Zustand wird für `D` Blöcke gehalten (`valid_until`), nur Safety-Regeln dürfen brechen.

> **TL;DR (EN):**  
> **R5** holds state for `D` blocks to avoid flapping; only safety rules may break it.

---

## Ablauf / Sequence

1. **BlockScheduler** erkennt Schwankung um Start/Stop-Schwelle.  
2. **R5** setzt Deadband: `action = hold`, `valid_until = block_id + D`.  
3. **R2/R3** können Deadband jederzeit brechen; andere Regeln warten bis `valid_until`.  
4. **UI** zeigt Badge „Stabilisierung aktiv“ + Countdown.  
5. **Logging**: `DeadbandActivatedEvent`, DecisionEvent mit Reason `R5 deadband`.

---

## Parameter (MVP)

- `hold_blocks = 2` nach jedem state change.  
- Flapping-KPI beobachtet `switches/h` vs. Baseline; Tuning via Runbook RB-01.
