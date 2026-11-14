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
├── bithamster_ki.py       # BitHamster im Dashboard (Cron + Dienst, nur lesend, s. unten)
├── bithamster_season.py   # Kontext zur saisonalen Automatik (Messung: data/research_cards.py)
├── bithamster_log.py      # Antwort-Log (eigene SQLite-Datei, nie bitgrid.db)
├── bithamster_eval.py     # Hamster-Test gegen den echten Kontext
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

## BitHamster im Produktiv-Dashboard (`bithamster_ki.py`)

Seit 13.11.2026. Erklärt im Dashboard, was die Automatik gerade macht, und
schlägt aus der Forschungs-DB Optimierungen vor. Läuft per Cron auf dem
HA-Host (`7,37 * * * *`, Checkout `BitGridAI-kpi-sync`, Log
`logs/bithamster_ki.log`).

Ablauf je Lauf:

1. HA-Zustände lesen, ausschließlich per `GET /api/states`.
2. `daily_kpi` und `daily_miner_kpi` der letzten 14 vollständigen Tage lesen
   (`mode=ro`, Tage unter 99 % Abdeckung zählen nicht).
3. Daraus in Python einen festen deutschen Kontext bauen. Alle Zahlen, die
   Aufwach-Regel, der nächste Schritt und die Jahreszeit stehen fertig drin.
4. Persona: `src/ha/config/bithamster_SOUL.md` (liegt im HA-Config-Ordner,
   wird bei jedem Lauf frisch gelesen, Änderung wirkt ohne Neustart).
5. Modell `qwen3.8-flash-next` auf GX10 (vLLM, OpenAI-kompatibel,
   `BITHAMSTER_LLM_URL` in der Server-`.env`), JSON-Antwort, ohne Thinking.
6. Ergebnis nach `www/bithamster_ki.json`, immer mit den zugrunde liegenden
   `facts`. Bei Fehlern `ok=false`, die Karten zeigen dann nichts Veraltetes.

Anzeige: KI-Zone unter dem regelbasierten Text der Hamster-Karte (Übersicht,
nur bei `ok` und höchstens 2 h alt) und die Karte "BitHamster" im Tab
Forschung (`views/forschung_hamster.yaml`), umschaltbar zwischen "Analyse"
und "Frag mich" (`input_boolean.bithamster_fragemodus`).

Aufträge und Chat ("Frag mich"): Die Knöpfe Optimierung finden,
Datenaufzeichnung prüfen, Fehler finden, Verbesserungsvorschläge, Tab
erklären und Frage senden rufen `script.bithamster_auftrag` auf, das nur
`input_text.bithamster_auftrag` auf `<auftrag>|<zeitstempel>` setzt
(`packages/bithamster.yaml`). Ein systemd-User-Dienst auf dem HA-Host
(`bithamster-ask.service`, `bithamster_ki --watch`, Linger an, Unit-Datei nur
auf dem Server) macht alle 3 s ein einzelnes GET auf den Auftrag; bei neuem
Auftrag fester Kontext je Auftrag (Aufzeichnungsstatus, Verfügbarkeit,
Tab-Karten aus dem Dashboard-YAML, Frage) und Antwort nach
`www/bithamster_ask.json`, samt Verlauf der letzten 30 Antworten (`history`).
Antwortzeit gemessen 8,5 bis 9,5 s (13.11.2026), davon rund 7 s Modell.
Fehler (HA-Neustart, GX10 ausgelastet) werden geloggt und nach 30 s erneut
versucht. Log: `journalctl --user -u bithamster-ask`.

Der Kontext enthält außerdem einen Vergleich mit den 30 Tagen davor und eine
fest berechnete Einordnung "erwartbar / auffällig / gut" samt Gesamturteil.
Das Modell hatte eine nur in Worten gegebene Regel ignoriert und einen
winterlich leeren Akku "auffällig" genannt; fertige Befunde gibt es dagegen
zuverlässig wieder.

**Nur lesend ist technisch erzwungen, nicht per Prompt:** Das Modell bekommt
Text und gibt Text zurück, ohne Werkzeuge und ohne HA-Token. Der einzige
POST im Modul geht an das Modell. Die Vorschläge sind Hypothesen für den
Menschen und fließen nie automatisch in `core/`, Schwellen oder
Automationen zurück. Die regelbasierte Erklärung (Text A) bleibt davon
unberührt.

Bekannte Grenze: Das Modell hält sich nicht immer an "keine Ursache
hineindeuten" (Live-Lauf 13.11.2026). Deshalb zeigt die Karte stets die
Datengrundlage.

### Saisonale Automatik prüfen (`bithamster_season.py`)

Die Messung selbst liegt in `src/data/research_cards.py` (auch Quelle der Karte
"Akku über Nacht"), `bithamster_season.py` formuliert daraus den Kontext. Rechnet die Tabelle "Saisonale Schwellwerte" (gleiche Formel wie
`mvp_saison_automatik`) und misst die echten Nächte seit Einführung der
Formel (28.08.2026) aus `energy_states`: Nachtverbrauch, Akku am Morgen,
Abschalt-SoC der Miner, Netzbezug nachts. Das Urteil (Hausreserve zu
niedrig / passt / zu hoch) fällt in Python am gemessenen Akkustand am
Morgen nach Mining-Tagen (Ziel 15 %). Nächte ohne Mining werden ausdrücklich
nicht den Minern angelastet. Ergebnis 13.11.2026: Regel hält (26/26 bzw.
9/10 Tage Abschaltung an der Schwelle), Hausreserve im September und
Oktober zu niedrig (Akku morgens 6 % bzw. 2 %), vermeidbarer Netzbezug aber
nur rund 29 kWh in zwei Monaten. Der Rest des nächtlichen Netzbezugs fällt
in Nächten ohne Mining an.

### Aufträge "Alles prüfen" und "Fehlende KPI-Karten"

Beide sehen alle Tabs mit ihren Karten, die saisonale Prüfung, den
Aufzeichnungsstatus und einen Datenbestand (welche Spalten der letzten 14
Tage wirklich gefüllt sind, damit keine Karte auf leeren Daten vorgeschlagen
wird). Nach jeder Antwort laufen feste Prüfungen (`finish_answer`):

- **Pflichtbefunde** ("Alles prüfen", "Optimierung finden"): fest
  berechnete Befunde, die das Modell nennen muss. Übersieht es einen, setzt
  Python ihn als "Fest berechnet: …" nach vorn.
- **Vorhandene Karten** ("Fehlende KPI-Karten"): Vorschläge, die es schon
  gibt, werden aussortiert (erster Live-Lauf: 2 von 4).
- **Erledigte Befunde** (Saison): Monate, deren Nächte alle vor ADR 033 (13.11.2026)
  liegen, kommen als "BEREITS KORRIGIERT" in den Kontext, mit dem gemessenen
  Abschalt-SoC statt des neuen Tabellenwerts. Anlass: "Optimierung finden" schlug Stunden
  nach ADR 033 vor, die Reserve anzuheben. Pflichtbefunde gelten schon als genannt, wenn
  der Monatsname in einem Punkt steht.
- **Inhaltsfilter** ("Fehlende KPI-Karten"): Dopplungen werden auch am Inhalt erkannt
  (`CARD_TOPICS`, z. B. "Nacht-Grundlast-Check" = Akku über Nacht, "Sats pro kWh Trend" =
  Mining-Effizienz), nicht nur am Namen.
- **Veraltete Daten** ("Fehlende KPI-Karten", "Tab verbessern"): der Datenbestand nennt
  je Tabelle die letzte Zeile; älter als 3 Tage heißt VERALTET, Vorschläge darauf fliegen
  raus. Anlass: `decision_events` hat 259 Zeilen, alle vom Testlauf am 02.07.2026, das
  Modell schlug darauf ein "Regel-Log" vor ("die Daten sind alle da").
- **Gestern** (alle Aufträge): fertige Tageswerte von gestern inkl. Poolertrag aus der
  F2Pool-Abrechnung, damit das Modell nichts aus Mittelwerten hochrechnet (Eval: "Sats
  gestern" vorher 2/3, danach 3/3).
- **Zahlencheck** (alle Aufträge): jede Zahl der Antwort muss im Kontext
  stehen (Rundung, Summe und Differenz genannter Zahlen erlaubt). Sonst
  zeigt die Karte "Zahl nicht im Kontext, bitte prüfen".

### Auftrag "Tab verbessern" (`tabcheck`)

Nimmt den Tab aus `input_select.bithamster_tab` (dasselbe Auswahlfeld wie "Tab
erklären"). Der Hamster sieht die Karten des Tabs, die Entitäten, die der Tab anzeigt,
mit ihren Live-Werten (`tab_value_lines`, aus dem Dashboard-YAML samt aller
`!include`-Dateien, rekursiv, höchstens 45 Werte), die Karten der anderen Tabs und den
Datenbestand. Vorschläge, die eine Karte eines anderen Tabs doppeln (Inhaltsfilter), fliegen raus;
Karten des eigenen Tabs darf er nennen, das sind ja die Verbesserungen. Grenze: er sieht Entitäten und Titel, nicht die gerenderte Karte (Layout,
Farben, Lesbarkeit beurteilt er nicht). Erster Live-Lauf (Tab Energie, 13.11.2026): 3 von
4 geprüften Vorschlägen trafen zu, darunter der fehlende Vergleich mit Solar und Netz.

### Wintermodus (November bis Februar)

Entscheidung des Nutzers vom 13.11.2026: im Winter zählt zuerst, dass der Akku lädt und
durch die Nacht kommt, Mining ist zweitrangig. `winter_lines` setzt dafür einen festen
Block in jeden Kontext (Priorität, leere Morgen, Heizstab-Befund aus
`research_cards.heizstab_vs_battery`). Die Steuerung ändert sich dadurch nicht. Befund
am selben Tag: Der Heizstab (AC ELWA 2) nahm seit 15.10. 46 kWh Solarstrom, ausnahmslos
bei Akku unter 95 %; er regelt selbst und ist in HA nur lesbar, Akku-Vorrang wird am Gerät
eingestellt. Die Karte "Akku-Höchststand und Start" zeigt dieselbe Zahl, damit eine
Änderung am Gerät messbar wird.

### Antwort-Log (`bithamster_log.py`)

Jede Antwort (Aufträge, Analyse-Lauf, Eval) landet mit dem exakten
Kontext in einer **eigenen** SQLite-Datei `data/bithamster_log.db` auf dem
HA-Host (Dienst und Cron mit `--log-db`). Bewusst nicht in `bitgrid.db`:
Die Forschungs-DB enthält Messungen und bleibt für den Hamster nur lesend,
Modelltext ist keine Messung. Mit dem gespeicherten Kontext lässt sich jede
Antwort nachträglich prüfen und vor/nach einer Änderung vergleichen.

### Hamster testen (`bithamster_eval.py`)

```bash
python -m src.explain.bithamster_eval --db data/bitgrid.db \
  --soul <ha-config>/bithamster_SOUL.md --dashboard <ha-config>/bitgrid_dashboard_v3.yaml \
  --recording-status <ha-config>/www/recording_status.json \
  --log-db data/bithamster_log.db --runs 3
# Geloggte Antworten mit geänderten Prüfungen neu bewerten, ohne Modellaufruf:
python -m src.explain.bithamster_eval --db x --soul x --log-db data/bithamster_log.db --regrade <eval_run>
```

Stellt 11 Szenarien (alle Aufträge, zwei Tabs, drei feste Fragen) je
mehrfach mit dem echten Kontext und bewertet: JSON lesbar, keine Zahl
außerhalb des Kontexts, Pflichtbefunde vom Modell selbst genannt, keine
vorhandene Karte, keine bekannte Falschaussage (verlorene Sats ohne
Überschuss, "auffällig" trotz Gesamturteil, Super-Schwelle obwohl Super
gesperrt). Schreibt nichts nach HA. Die Prüfungen sind notwendige
Bedingungen: Eine bestandene Antwort kann trotzdem schlecht erklären, das
bleibt Gegenlesen der geloggten Antworten.

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
