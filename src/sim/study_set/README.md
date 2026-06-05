# Eingefrorenes Studien-Set (S1–S10)

Reproduzierbare Studien-Stimuli: je Szenario eine `S<n>.json` mit Eingangs-State,
deterministischer Kern-Entscheidung und Erklärungen. Erzeugt von
[`src/sim/study_freeze.py`](../study_freeze.py) aus [`study_scenarios.py`](../study_scenarios.py).

## Format je `S<n>.json`

| Feld | Inhalt |
|---|---|
| `sid`, `title` | Szenario-ID + Kurztitel |
| `actual_code` / `verified` | Kern-Output + ob == erwartetem Code |
| `decision` | action, code, **base_code** (für Text-Lookup), reason |
| `engine_input` | last_action, blocks_since_change (R5-Kontext) |
| `state`, `params` | Eingangs-`EnergyState` + verwendete Schwellen |
| `explanation.group_a` | **statische** Bausteine (short/long/trigger/data_basis/effect/options) |
| `explanation.group_b` | **LLM persona-adaptiv** je Persona (energie/waerme/tech) — `null` = Platzhalter |

## Gruppe B befüllen (wenn der externe Ollama-Rechner steht)

```bash
OLLAMA_HOST=http://<dein-rechner>:11434 OLLAMA_MODEL=qwen3:8b \
  python -m src.sim.study_freeze
```

→ generiert je Persona einen Satz und friert ihn ein. **Wichtig:** Damit sind die
Stimuli **reproduzierbar und ausfallsicher** — die Studie hängt nicht an der
Live-Verfügbarkeit des LLM, und der nicht-deterministische LLM-Output ist fixiert.

## Verifikation

`python -m src.sim.study_freeze` druckt `10/10 verifiziert` — der Kern-Output jedes
Szenarios stimmt mit dem erwarteten `decision_code` überein (auch als Unit-Test in
`tests/sim/test_study_freeze.py`).
