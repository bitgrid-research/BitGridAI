# 061 – Runtime: Normaler Start (R1)

> **Kurzüberblick:**  
> PV-Überschuss → **EnergyState** aktualisiert → **BlockScheduler (10 Min)** triggert **R1** → Mining startet inkl. **DecisionEvent + Erklärung**.

> **TL;DR (EN):**  
> PV surplus → EnergyState → 10-min scheduler triggers **R1** → start mining with DecisionEvent + rationale.

---

## Ablauf / Sequence

1. PV-Sensor publiziert Leistung (MQTT/Modbus).  
2. **Energy Context** aktualisiert **EnergyState (SSoT)** und berechnet `surplus`.  
3. **BlockScheduler** (`block_id=floor(epoch/600)`) ruft **Rule Engine (R1–R5)** auf.  
4. Wenn `surplus ≥ 1.5 kW` **und** `price ≤ 18 ct` (Beispiel) → **R1 start**.  
5. **Actuation** sendet `start/set_power` an Miner-Controller.  
6. **Explainability** erzeugt **DecisionEvent** mit Reason/Trigger/Parameter.  
7. **UI** zeigt Toast + Next-Block-Preview; Deadband (R5) hält Zustand für D Blöcke.

---

## Wichtige Parameter (MVP)

- `surplus_min_kw = 1.5` (rolling Ø 1 Block)  
- `price_max_ct_kwh = 18`  
- `min_runtime_blocks = 2` (Warmup)  
- Deadband: `hold_blocks = 2` nach state change.
