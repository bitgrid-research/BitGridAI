# System-Prompts & Ollama-Setup (Studie, Gruppe B)

**Stand:** 2026-06-22 · **Zweck:** ein Blatt für alles rund um die LLM-Erklärungen (Gruppe B).

> **Quelle der Wahrheit ist der Code.** Dieses Blatt dokumentiert und erklärt, was im Code steht; bei Abweichung gilt der Code. Kanonische Stellen: `src/explain/explain_agent.py` (Prompt + Ollama-Call), `src/explain/mappings/text_blocks.yaml` (Bausteine), `src/explain/mappings/b_references.yaml` (Gold-Referenzen), `src/sim/study_freeze.py` (Einfrieren), `src/sim/study_faithfulness.py` (Gates).

## 1. Gruppe A vs. Gruppe B (die Manipulation)

| | Gruppe A | Gruppe B |
|---|---|---|
| Erzeugung | statische Templates, **kein LLM** | LLM (Ollama), eingefroren |
| Stimme | neutral, System-Ton | **BitHamster**: Ich-Form, warm, „du", Laien |
| Quelle | `text_blocks.yaml` über `ExplainAgent` | `_call_ollama` → eingefroren |
| Faktenbasis | R1–R5, Werte, Schwellen | **identisch zu A** |

Variiert wird **nur die Formulierungsebene** (Regel-Template vs. LLM-Stimme), nicht Format, nicht Informationsgehalt (Prereg `2024a`, `2024e`). H1 (einseitig): B erzeugt mehr Vertrauen als A.

## 2. Modell & Verbindung

Konfiguration über Umgebungsvariablen (`ExplainAgent.__init__`):

| Variable | Default | Bedeutung |
|---|---|---|
| `OLLAMA_HOST` | `""` (leer = kein LLM, A-Template bleibt) | z. B. `http://umbrel.local:11434` |
| `OLLAMA_MODEL` | `qwen3.5:9b` | Modell-Tag auf dem Ollama-Host |
| `OLLAMA_TIMEOUT_SEC` | `30` | Timeout je Anfrage |

Aufruf: `POST {OLLAMA_HOST}/api/generate`, JSON-Body:

```json
{
  "model": "<OLLAMA_MODEL>",
  "prompt": "<siehe Abschnitt 4>",
  "stream": false,
  "think": false,
  "options": { "num_predict": 120, "temperature": 0.3 }
}
```

`think: false` schaltet den qwen3-Thinking-Modus aus, damit der Text im Feld `response` landet. Bei Timeout/Fehler/leer → `None`, und der A-Template-Wert bleibt als Fallback (kein Crash).

## 3. System-Instruktion (`_B_INSTRUCTION`)

Konstante in `explain_agent.py`, eine einzige Hamster-Stimme (keine Persona-Achse):

```
Du bist BitHamster, das Maskottchen und der KI-Energieberater einer Heimsolar-App:
ein ruhiger, schlauer Krypto-Hamster mit AR-Brille, der eine Hardware-Wallet mit
Bitcoin-Logo in den Pfoten hält und für dich Bitcoin minet, wenn genug eigener
Solarstrom übrig ist und der Hausspeicher (Batterie) geladen genug ist, statt
Strom einzuspeisen.
Deine Aufgabe: die teils komplexen Smarthome-Automationen warm und einfach für
Laien erklären.
Sprich in der Ich-Form, denn deine Anzeige spiegelt deinen Zustand: du ruhst oder
döst, wenn du gestoppt bist, hältst geduldig die Stellung, wenn du wartest, minest
grün und sparsam im Eco-Modus und legst an Leistung zu, je mehr Solarstrom da ist,
von Standard bis zur vollen Super-Last.
Sprich den Nutzer mit 'du' an, benutze einfache Alltagssprache, keine Fachbegriffe,
kein Englisch, kein Chinesisch. Antworte immer auf Deutsch.
```

(BitHamster-Persona, strategie-neutral; bewusst **ohne** übertriebene Aura-Sprache, da die Standard/Super-Bilder noch überarbeitet werden, der Text bleibt so bild-agnostisch)

## 4. Prompt-Template (`_call_ollama`)

Pro Szenario zusammengesetzt aus der System-Instruktion, einem Few-Shot-Beispiel und den deterministischen Bausteinen:

```
{_B_INSTRUCTION}

Schreibe ein bis drei kurze deutsche Sätze (zusammen max. 45 Wörter),
vergleichbar lang wie eine vollständige Erklärung.
Nenne mindestens EINE konkrete Zahl aus den Messwerten.
Wenn eine Änderungsbedingung angegeben ist, nenne auch ihren
Schwellenwert (ab/unter welchem Wert sich der Zustand wieder ändert).
Keine Einleitung, kein Bullet-Point, kein Englisch, kein Chinesisch.
Beispiel für diese Situation: '{example}'

Was passiert: {effect}
Warum: {trigger}
Messwerte: {data_basis}
Änderungsbedingung: {options}        ← nur wenn options nicht leer
```

Die letzte Zeile (`Änderungsbedingung`) sorgt für die **Informations-Parität A↔B**: B trägt denselben Schwellenwert wie A (z. B. „ab 58 %", „unter 85 %"), damit nur die Stimme variiert.

## 5. Eingaben je Szenario (woher die Platzhalter kommen)

Alle aus `text_blocks.yaml` (Sprache `de`), interpoliert mit `params` des `DecisionEvent`:

| Platzhalter | Feld in `text_blocks.yaml` | Beispiel |
|---|---|---|
| `{effect}` | `effect` | „Miner bleibt aus, Akku lädt erst weiter" |
| `{trigger}` | `trigger` | „Akku 52 % liegt noch unter der Startgrenze 58 %" |
| `{data_basis}` | `data_basis` | „Akku 52 % · Eco-Start 58 %" |
| `{options}` | `options` | „Start ab 58 % Akku" |
| `{example}` | `b_references.yaml` (sonst `example` aus `text_blocks.yaml`) | siehe Abschnitt 6 |

Zahlen werden mit deutschem Dezimalkomma gerendert (`3.0` → `3,0`); fehlende Werte → `?` statt Absturz.

## 6. Few-Shot-Anker / Gold-Referenzen (`b_references.yaml`)

Ein idealer Text je `decision_code` in der BitHamster-Stimme. Doppelrolle: (a) Few-Shot-Anker im Prompt, (b) **Gold-Referenz** für die Güte-Bewertung (FF2), gegen die der echte LLM-Output verglichen wird. Beispiel (S1):

```
START_R1_SURPLUS_OK:
  "Ich mine gerade mit voller Leistung: deine Solaranlage liefert 3,0 kW mehr,
   als dein Haus braucht, und die nutze ich selbst, statt sie einzuspeisen."
```

## 7. Qualitäts-Gates

### 7a. Faithfulness-Vorprüfung (`study_faithfulness.py`, automatisch, reproduzierbar)

Da der Kern deterministisch ist, ist die wahre Aktion bekannt. Geprüft wird je Text:

1. **Aktions-Konsistenz** — kein Widerspruch zur START/STOP/THROTTLE/NOOP-Aktion (Term-Listen „läuft" vs. „gestoppt").
2. **Erdung** — mindestens ein konkreter Zahlenwert.
3. **Informations-Parität A↔B** — B trägt mindestens einen Schwellenwert aus dem A-`options`-Feld (`covers_change_condition`). Nennt A keine numerische Bedingung, ist die Prüfung „nicht anwendbar".

```
python -m src.sim.study_faithfulness
```

### 7b. Güte-Bewertung FF2 (`study_guete.py`)

Objektive Schicht = Faithfulness-Vorprüfung (A = treue Decke/Referenz). Rubrik-Schicht = zwei verblindete Rater, je Dimension 0–2: **Korrektheit, Vollständigkeit, Klarheit** + Halluzinations-Flag (0/1); Inter-Rater = quadratisch gewichtetes Cohen's κ.

```
python -m src.sim.study_guete                              # nur objektive Schicht
python -m src.sim.study_guete --ratings ratings.csv        # + Rubrik-Schicht
```

## 8. Freeze-Pipeline (reproduzierbar, ausfallsicher)

```
python -m src.sim.study_freeze                               # Surplus S1–S10, A + B-Platzhalter
python -m src.sim.study_freeze --set soc_band                # SoC-Band SB01–SB13
OLLAMA_HOST=http://host:11434 python -m src.sim.study_freeze # + Gruppe B (LLM)
```

Ergebnis: `src/sim/study_set/S*.json` (Surplus) bzw. `src/sim/study_set_soc_band/SB*.json` (SoC-Band) mit `decision`, `params`, `explanation.group_a` (Bausteine), `explanation.group_b_reference` (Gold), `explanation.group_b` (LLM oder `None`). Damit sind Stimuli + Erklärungen **eingefroren**, unabhängig von der Live-Verfügbarkeit des LLM. Das SoC-Band-Set ist in `src/sim/study_scenarios_soc_band.py` modelliert (13 Snapshots, gegen den Kern verifiziert).

## 9. Stand der Abgleich-Punkte (2026-06-22 erledigt)

1. **Länge vereinheitlicht.** Prompt, `b_references.yaml`-Kopf und Güte-Rubrik (`study_guete.py`) verlangen nun einheitlich **ein bis drei kurze Sätze, ~45 Wörter** (vergleichbar lang wie die Gruppe-A-Prosa), inklusive Änderungsbedingung. Die Länge ist damit für den A/B-Vergleich realistisch und kein Confound.
2. **Gold-Referenzen geerdet.** Die Surplus-Anker trugen die Schwellen bereits; ergänzt um SoC-Band-Anker (SB01–SB13) passend zu `study_scenarios_soc_band.py`, Zahlen an den HA-Recorder geerdet (Abschnitt 10).
3. **Modell gepinnt.** Studien-Modell = `OLLAMA_MODEL` (Default `qwen3.5:9b`); beim Freeze fest dokumentieren. Die ₿itsy-Agenten spielen in der Entwicklung keine Rolle mehr und sind hier nicht relevant.
4. **`_B_INSTRUCTION` strategie-neutral.** Beschreibt den Miner als flexible Last (Solarüberschuss + Hausspeicher-Ladezustand, Eco/Super) und passt zu Surplus- wie SoC-Band-Strategie.
5. **SoC-Band-Szenarien modelliert + freezebar.** Code-Set `src/sim/study_scenarios_soc_band.py` (13 Snapshots, 13/13 gegen den Kern verifiziert), einfrierbar über `python -m src.sim.study_freeze --set soc_band`.

Verbleibender Architektur-Punkt (DEV, nicht Studientext): die Modus-Rückfall-Hysterese (75/85 %) liest `r1_soc_band` noch nicht; bis dahin sind die „Rückfall"-Schwellen in Text/Referenz didaktisch (real fällt die Stufe an der Bandgrenze 80/90 %).

## 10. Reale Erdung (HA-Recorder, 24.05.–03.06.2026, Frühsommer)

> Korrektur 2026-06-23: frühere Erdung stützte sich auf das März-Fenster
> (28.03.–06.04.) mit schwacher PV und vor dem 21.05. lückenhaften PV/Last/Netz-
> Sensoren; daher die falsche Annahme „SoC max 75 %, Bänder ≥ 80 % real noch nicht
> erreicht". Die vollständigen Sommerdaten zeigen den Speicher fast täglich bei
> 99–100 % SoC, alle Bänder werden real durchlaufen.

| Größe | Realer Bereich | Verwendung |
|---|---|---|
| PV | 0–9,3 kW (Ø 2,0) | Szenario-PV-Werte |
| SoC | 5–100 % (Ø 56) | alle Bänder real erreicht (Speicher tgl. 99–100 %) |
| Hauslast | Ø 0,7 kW (max 5,1) | Last-Werte |
| Miner Eco | ~800 W/Miner → 1,6 kW gesamt | `MINER_MODE_POWER_W` (Sim) |
| Miner Super | ~1600 W/Miner → 3,2 kW gesamt | `MINER_MODE_POWER_W` (Sim) |
| Miner Standard | nie gesetzt → ~2,4 kW geschätzt | `MINER_MODE_POWER_W` (Annahme) |
| Chip-Temp | max ~75 °C | Übertemp-Szenario 113 °C konstruiert (real nie erreicht) |

Query read-only: `sqlite3.connect("file:src/ha/config/home-assistant_v2.db?mode=ro", uri=True)` (HA-DB nie schreiben).

## 11. Schnellreferenz

```
# Gruppe B lokal gegen den Ollama-Host erzeugen und einfrieren (Set wählen)
OLLAMA_HOST=http://umbrel.local:11434 OLLAMA_MODEL=qwen3.5:9b \
  python -m src.sim.study_freeze --set soc_band

# Treue + Parität prüfen
python -m src.sim.study_faithfulness

# Objektive Güte (FF2)
python -m src.sim.study_guete
```
