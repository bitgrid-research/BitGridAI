# Forschungsexport — BitGridAI Studiendaten für die Universität

Dieses Dokument beschreibt den Datenexport aus dem BitGridAI-System für die
statistische Auswertung der Nutzerstudie. Es richtet sich an die auswertende Person
an der Universität und an den Studienleiter.

---

## 1. Export abrufen

Der Export läuft über die REST-API des produktiven BitGridAI-Systems.
Das Feature-Flag `research_export: true` muss in `ops/config/feature_flags.yaml`
gesetzt sein (standardmäßig deaktiviert).

```bash
# ZIP herunterladen (läuft lokal auf umbrel.local)
curl -X POST http://umbrel.local:8080/research/export \
  -H "Authorization: Bearer $API_TOKEN" \
  --output data/study/export_$(date +%Y%m%d).zip

# ZIP entpacken
unzip data/study/export_$(date +%Y%m%d).zip -d data/study/raw/
```

Der ZIP enthält drei Dateien:

| Datei | Inhalt |
|---|---|
| `events.parquet` | Alle DecisionEvents (append-only) |
| `manifest.json` | Exportzeitpunkt, Zeilenzahl, Spaltenübersicht, Format-Version |
| `CHECKSUMS.sha256` | SHA-256-Prüfsummen beider Dateien |

---

## 2. Parquet-Schema: events.parquet

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | string | Eindeutige UUID des DecisionEvent |
| `block_id` | string | Blockanfang als ISO-8601-Timestamp (z.B. `2026-06-10T14:00:00`) |
| `timestamp` | string | Tatsächlicher Schreib-Timestamp (UTC) |
| `action` | string | `START` \| `STOP` \| `NOOP` |
| `decision_code` | string | Stabiler Code (z.B. `START_R1_SURPLUS_OK`, `STOP_R3_OVERTEMP`) |
| `reason` | string | Kurzform der Entscheidungsbegründung |
| `trigger` | string | `BLOCK_TICK` \| `SAFETY_ASYNC` \| `OVERRIDE` |
| `params_json` | string | JSON-String mit allen Schwellenwerten und Messwerten zum Entscheidungszeitpunkt |
| `valid_until` | string | Gültigkeitsende der Entscheidung (ISO-8601) |
| `explain_short` | string | Natürlichsprachliche Erklärung (leer wenn Modell nicht verfügbar) |
| `state_ref` | string | Verweis auf den EnergyState-Snapshot (block_id) |

### Abgeleitete Variablen für die Studie

Aus `params_json` können alle Messwerte extrahiert werden:

```python
import json, pandas as pd

events = pd.read_parquet("data/study/raw/events.parquet")
params = events["params_json"].apply(json.loads).apply(pd.Series)

# Wichtige Felder in params_json:
# surplus_kw, battery_soc_pct, miner_temp_c, pv_power_w,
# house_load_w, grid_import_w, pv_forecast_kw
```

### Override-Ereignisse erkennen

Manuelle Eingriffe der Probanden erscheinen als `trigger == "OVERRIDE"`:

```python
overrides = events[events["trigger"] == "OVERRIDE"]

# R3-Override-Versuche (sollten blockiert werden — trotzdem geloggt)
r3_attempts = events[
    (events["trigger"] == "OVERRIDE") &
    (events["decision_code"].str.startswith("STOP_R3"))
]
```

---

## 3. Pseudonymisierung

**Vor der Übergabe an die Universität:**

Das System speichert keine personenbezogenen Daten in der Ereignisdatenbank.
Die `events.parquet` enthält ausschließlich Systemereignisse ohne Personenkenner.

Die Zuordnung Proband → Zeitraum erfolgt über eine **separate Teilnehmerliste**
(nicht im System gespeichert), die der Studienleiter führt. Diese Liste wird
ebenfalls pseudonymisiert (P01–P10 statt Klarnamen) bevor sie an die
auswertende Person übergeben wird.

**Workflow:**
1. Studienleiter exportiert `events.parquet` pro Proband (nach Datum filtern)
2. Studienleiter benennt Dateien um: `events_P01.parquet`, `events_P02.parquet`, ...
3. Zusammenführen mit `participant_id`-Spalte:

```python
import pandas as pd
from pathlib import Path

parts = []
for f in sorted(Path("data/study/raw/per_participant").glob("events_P*.parquet")):
    pid = f.stem.replace("events_", "")
    df = pd.read_parquet(f)
    df["participant_id"] = pid
    parts.append(df)

events_merged = pd.concat(parts, ignore_index=True)
events_merged.to_parquet("data/study/events_merged.parquet", index=False)
```

---

## 4. Fragebogendaten (participants.csv)

Die Fragebogendaten werden separat in `data/study/participants.csv` gepflegt.
Das Schema ist in `src/sim/fixtures/participants_template.csv` dokumentiert.

Pflichtfelder:

| Spalte | Einheit | Instrument |
|---|---|---|
| `participant_id` | — | P01…P10 |
| `group` | B/E | Randomisierung |
| `sus_pre` / `sus_post` | 0–100 | SUS (Brooke 1996) |
| `trust_pre` / `trust_post` | 12–84 | Automation Trust Scale (Jian 2000) |
| `tlx_pre` / `tlx_mid` / `tlx_post` | 0–100 | NASA-TLX Raw |
| `vignette_pre` / `vignette_post` | 0–10 | Vignetten-Test |
| `waerme_absicht` | 1–5 | Likert-Item Demographiefragebogen |
| `btc_vorwissen` | 1–5 | Selbsteinschätzungsskala Demographiefragebogen |

---

## 5. Statistische Auswertung

Das Skript `src/sim/study_analysis.py` führt alle vordefinierten Tests durch:

```bash
python -m src.sim.study_analysis \
  --events data/study/events_merged.parquet \
  --participants data/study/participants.csv \
  --out data/study/study_results.json
```

### Ausgabeformat (Konsole)

```
=== ZWISCHEN-GRUPPEN (Mann-Whitney-U) ===
  H1: Vignetten-Score post (Gruppe E > B)
    → U=3.5, p=0.095, r=0.42 [mittel] (N=10)
  H3: Trust post (Gruppe E > B)
    → U=5.0, p=0.222, r=0.28 [klein] (N=10)
...

=== INNERHALB GRUPPE E (Wilcoxon Prä→Post) ===
  Vignette prä→post (E)
    → W=1.0, p=0.063, r=0.65 [groß] (N=5 Paare)
...

Hinweis: Power bei n=5 je Gruppe ≈ 20 % für r=0.3. ...
```

### Berichtspflicht (aus Methodik §5.8.2)

p-Werte werden nie isoliert berichtet. Pflichtformat:

```
U=7.5, p=0.31, r=0.28 [klein] (N=10)
```

Effektgröße r nach Field (2018):
- r ≈ 0.1 → klein
- r ≈ 0.3 → mittel
- r ≈ 0.5 → groß

Mit n=5 je Gruppe ist die statistische Power für r=0.3 ca. 20 %.
Nicht-signifikante Befunde schließen mittlere Effekte nicht aus.

---

## 6. Prüfsummen verifizieren

```bash
cd data/study/raw/
sha256sum --check CHECKSUMS.sha256
```

---

## 7. Checkliste vor Datenübergabe an Uni

- [ ] Export-Datum und Proband-ID stimmen überein
- [ ] `events_merged.parquet` hat Spalte `participant_id`
- [ ] `participants.csv` ist vollständig ausgefüllt (keine leeren Pflichtfelder)
- [ ] Klarnamen wurden durch P01–P10 ersetzt
- [ ] SHA-256 geprüft (`sha256sum --check CHECKSUMS.sha256`)
- [ ] `data/study/` enthält **keine** `.env`-Dateien oder API-Tokens
