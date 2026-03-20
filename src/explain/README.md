# src/explain

Erklärungslogik: Entscheidungscodes → menschenlesbare Texte.

Der Explain-Baustein übersetzt technische `DecisionEvent`s in strukturierte, konsistente Erklärungen für UI und Logging. Keine freien Strings im Core — alle Texte kommen aus definierten Bausteinen.

---

## Verzeichnisstruktur

```
explain/
├── explain_agent.py       # Hauptlogik: DecisionEvent → ExplainResult
├── decision_codes.py      # Alle gültigen Decision-Codes als Konstanten
├── code_generator.py      # EnergyState + Decision → Decision-Code ableiten
├── mappings/
│   ├── rule_map.yaml      # Regel → Code-Bedingungen
│   └── text_blocks.yaml   # Alle Textbausteine (DE + EN)
└── __init__.py
```

---

## Decision-Code-Format (`decision_codes.py`)

Decision-Codes sind maschinenlesbare, stabile Bezeichner für jede mögliche Entscheidung:

```
{ACTION}_{PRIMARY_RULE}_{KONTEXT}

Beispiele:
  START_R1_SURPLUS_OK           → R1: Surplus über Schwelle
  NOOP_R5_DEADBAND_ACTIVE       → R5: Deadband hält Entscheidung stabil
  STOP_R3_OVERTEMP              → R3: Safety-Stop, Übertemperatur
  STOP_R2_SOC_HARD_MIN          → R2: SoC unter Hard-Minimum
  NOOP_R4_FORECAST_BLOCKED      → R4: Forecast-Einbruch blockiert Start
  START_R4_FORECAST_PEAK        → R4: Startet vor erwartetem Preis-Peak
```

**Regel:** Codes sind stabil über Releases. Neue Codes nur addieren, nie umbenennen — Log- und UI-Konsistenz hängen davon ab.

---

## Text-Bausteine (`mappings/text_blocks.yaml`)

```yaml
de:
  START_R1_SURPLUS_OK:
    short: "Überschuss verfügbar"
    long: "PV-Leistung übersteigt Hausverbrauch um {surplus_kw:.1f} kW. Start ist wirtschaftlich."
    trigger: "Schwelle {r1_surplus_min_kw:.1f} kW überschritten"

  STOP_R3_OVERTEMP:
    short: "Sicherheitsstopp: Übertemperatur"
    long: "Miner-Temperatur {miner_temp_c:.0f}°C überschreitet Sicherheitsgrenze {r3_max_chip_temp_c:.0f}°C."
    trigger: "R3 Safety-Override (asynchron)"

  NOOP_R5_DEADBAND_ACTIVE:
    short: "Ruhephase aktiv"
    long: "Entscheidung bleibt stabil bis {valid_until}. Flapping-Schutz aktiv."
    trigger: "Mindesthaltezeit nicht abgelaufen"

en:
  START_R1_SURPLUS_OK:
    short: "Surplus available"
    long: "PV output exceeds house load by {surplus_kw:.1f} kW. Start is profitable."
    trigger: "Threshold {r1_surplus_min_kw:.1f} kW exceeded"
```

---

## Regel-Mapping (`mappings/rule_map.yaml`)

```yaml
rules:
  R1:
    signals: [pv_power_w, house_load_w, surplus_kw, energy_price_ct_kwh]
    thresholds: [r1_surplus_min_kw, r1_price_max_ct_kwh]
    codes:
      - condition: "surplus_kw >= r1_surplus_min_kw"
        action: START
        code: START_R1_SURPLUS_OK
      - condition: "surplus_kw < r1_surplus_min_kw"
        action: NOOP
        code: NOOP_R1_INSUFFICIENT_SURPLUS

  R3:
    signals: [miner_temp_c, miner_heartbeat_age_sec]
    thresholds: [r3_max_chip_temp_c, r3_comm_timeout_sec]
    codes:
      - condition: "miner_temp_c > r3_max_chip_temp_c"
        action: STOP
        code: STOP_R3_OVERTEMP
      - condition: "miner_heartbeat_age_sec > r3_comm_timeout_sec"
        action: STOP
        code: STOP_R3_COMM_TIMEOUT
```

---

## Ausgabeformat (`explain_agent.py`)

```python
@dataclass
class ExplainResult:
    decision_code: str           # z.B. "STOP_R3_OVERTEMP"
    short: str                   # Kurzerklärung für UI-Card
    long: str                    # Detailerklärung mit interpolierten Werten
    trigger: str                 # Was hat die Entscheidung ausgelöst
    params: dict                 # Verwendete Schwellen-Werte
    rule_states: dict            # {"R1": "ok", "R2": "ok", "R3": "triggered", ...}
    energy_state_ref: str        # block_id für Audit-Trail
    lang: str                    # "de" | "en"
```

---

## Konventionen

**Keine freien Strings im Core:** `rule_engine.py` erzeugt nur Reason-Codes (z.B. `"R3_OVERTEMP"`). Der `explain_agent` macht daraus menschenlesbare Texte. Niemals Erklärungen direkt in Core-Code schreiben.

**Log ↔ UI-Konsistenz:** `decision_code` ist in Log und UI identisch — jeder Log-Eintrag ist damit direkt in der UI nachvollziehbar.

**Template-Interpolation:** Texte nutzen `{key:.format}`-Syntax mit Werten aus `ExplainResult.params`. Fehlende Werte → `"?"` statt Exception.

**Read-only:** `explain_agent` verändert nie `EnergyState` oder `Decision`. Nur lesen, übersetzen, ausgeben.

---

## Einstiegspunkte für Entwickler

| Aufgabe | Datei |
|---|---|
| Neuen Code hinzufügen | `decision_codes.py` + `text_blocks.yaml` + `rule_map.yaml` |
| Neue Sprache | `text_blocks.yaml` (neue Sprach-Sektion) |
| Erklärungslogik | `explain_agent.py` |
| Code-Generierung debuggen | `code_generator.py` |

---

## Nächste Schritte

- [ ] `decision_codes.py` — vollständige Code-Liste für R1–R5 als Konstanten
- [ ] `mappings/text_blocks.yaml` — DE-Texte für alle Codes
- [ ] `mappings/rule_map.yaml` — Bedingungen und Code-Mapping pro Regel
- [ ] `explain_agent.py` — Template-Interpolation + ExplainResult
- [ ] `code_generator.py` — EnergyState + Decision → Code ableiten
