# ABK → BitGridAI: Formale Theorie trifft echte Software

Dieses Dokument verbindet das Studium von **Automaten, Berechenbarkeit und Komplexität (ABK)**
mit konkreten Verbesserungen an BitGridAI. Jedes Konzept aus der Vorlesung wird direkt
auf den Code abgebildet — und wo möglich umgesetzt.

---

## W1 — Formale Sprachen & Grammatiken

### Konzept: Formale Grammatik G = (V, Σ, P, S)

| Formal | BitGridAI |
|--------|-----------|
| Terminalalphabet Σ | Diskretisierte Sensorwerte + Aktionen |
| Nichtterminale V | Abstrakte Prüfstufen (SAFETY, AUTARKY, ...) |
| Produktionsregeln P | Regellogik R1–R5 |
| Startsymbol S | `DECISION` |

**Terminalalphabet Σ (echte Werte aus `src/core/models.py`):**
```
Zustände:
  surplus_ok    (surplus_kw >= 1.5)
  surplus_low   (surplus_kw <  1.5)
  soc_safe      (battery_soc_pct >  20%)
  soc_warn      (battery_soc_pct 10–20%)
  soc_critical  (battery_soc_pct <= 10%)
  temp_ok       (miner_temp_c <= 85°C)
  temp_hot      (miner_temp_c >  85°C)
  comm_ok       (miner_heartbeat_age_sec <= 60s)
  comm_lost     (miner_heartbeat_age_sec >  60s)
  price_ok      (energy_price_ct_kwh <= 25¢)
  price_high    (energy_price_ct_kwh >  25¢)
  forecast_ok   (pv_forecast_kw >= 2.0)
  forecast_low  (pv_forecast_kw <  2.0)

Aktionen (Terminale der Ausgabe):
  START   STOP   NOOP   THROTTLE
```

**Grammatik G für den Entscheidungskern:**
```
S         → S' | ε                    (ε-Sonderregel: nur wenn quality="error")
S'        → SAFETY ACTION
SAFETY    → temp_hot STOP             (R3: Sofortabschaltung)
SAFETY    → comm_lost STOP            (R3: Kommunikationsabbruch)
SAFETY    → temp_ok AUTARKY
AUTARKY   → soc_critical STOP        (R2: Hard-Min)
AUTARKY   → soc_warn NOOP            (R2: Soft-Min)
AUTARKY   → soc_safe STABILITY
STABILITY → START NOOP               (R5: MIN_RUNTIME_NOT_REACHED)
STABILITY → STOP  NOOP               (R5: MIN_PAUSE_NOT_REACHED)
STABILITY → PROFIT
PROFIT    → surplus_low NOOP         (R1: kein Überschuss)
PROFIT    → surplus_ok price_high NOOP  (R1: Preis zu hoch)
PROFIT    → surplus_ok price_ok START   (R1: Mining erlaubt)
ACTION    → START | STOP | NOOP | THROTTLE
```

### Konzept: Chomsky-Hierarchie

| Typ | Regel | BitGridAI-Entsprechung |
|-----|-------|----------------------|
| **Typ 3** (Regulär) | y ∈ Σ ∪ ΣV | R3 Safety: lineare if/else-Kette → **DFA möglich** |
| **Typ 2** (Kontextfrei) | x ∈ V | R1, R2, R4: verschachtelte Prüfungen |
| **Typ 1** (Kontextsensitiv) | \|x\| ≤ \|y\| | R5 Stability: vorheriger Zustand entscheidet |
| **Typ 0** (Unbeschränkt) | keine | Gesamtsystem als TM betrachtet |

### Konzept: ε-Sonderregelung

**Problem:** `quality = "error"` (>2 Signale fehlen) → ε-Wort = "tue nichts"

**Lösung im Code:** Neue Variable S' einführen, S nur als Einstieg mit ε-Option.

**Umsetzungsidee in `src/core/rule_engine.py`:**
```python
# Wenn quality == "error": sofort NOOP zurückgeben (= ε-Ableitung)
# Nur bei quality "ok" oder "warn": normale Regelkette (= S'-Ableitung)
if state.quality == "error":
    return Decision(action="NOOP", reason="DATA_QUALITY_ERROR")
```

---

## W2 — DFA, NFA, Reguläre Ausdrücke (geplant)

### Idee: R3 Safety als formaler DFA

R3 ist bereits Typ-3-Grammatik → kann als **deterministischer endlicher Automat** implementiert werden.

```
Zustände Q = { CHECKING, RUNNING, STOPPED }
Σ = { temp_ok, temp_hot, comm_ok, comm_lost, soc_safe, ... }
Startzustand q0 = CHECKING
Endzustände F = { RUNNING, STOPPED }

Übergänge δ:
  δ(CHECKING, temp_hot)  = STOPPED
  δ(CHECKING, comm_lost) = STOPPED
  δ(CHECKING, temp_ok)   = RUNNING
  δ(RUNNING,  temp_hot)  = STOPPED   (während Betrieb: sofort stoppen)
  δ(STOPPED,  temp_ok)   = CHECKING  (nach Abkühlung: neu prüfen)
```

**→ Implementierungsziel:** `src/core/safety_dfa.py` — formaler DFA für R3,
replay-fähig, deterministisch, testbar mit Automaten-Theorie.

---

## Offene Themen (folgen mit Vorlesung)

- [ ] W3: CFL, CNF, CYK — Entscheidungsgrammatik in Chomsky-Normalform bringen
- [ ] W4: Turingmaschine — Ist das Gesamtsystem TM-äquivalent?
- [ ] W5: Entscheidbarkeit — Welche Fragen über BitGridAI sind entscheidbar?
         z.B. "Wird der Miner jemals starten?" → Halteproblem-Analogie
- [ ] W5: NP — Optimale Lastverteilung als NP-Problem?

---

## Geplante Implementierungen

| Was | Wo | Status |
|-----|----|--------|
| DFA für R3 Safety | `src/core/safety_dfa.py` | geplant |
| Diskretisierung EnergyState → Σ* | `src/core/discretizer.py` | geplant |
| Automat-Visualisierung | `src/sim/` oder `src/ui/` | geplant |
| Grammatik-Validator (prüft ob Wort ∈ L(G)) | `src/sim/` | geplant |
