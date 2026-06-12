# Forschungsexport — BitGridAI Studiendaten für die Universität

Dieses Dokument beschreibt den Datenexport aus dem BitGridAI-System für die
statistische Auswertung der Nutzerstudie. Es richtet sich an die auswertende Person
an der Universität und an den Studienleiter.

> **Design:** Mixed, Einzelsitzung, N = 16 (Gruppe A statisch n = 8 vs. Gruppe B LLM
> n = 8, **ohne Personas**). Primäre AV: Nutzervertrauen (Automation Trust Scale, Jian
> 2000, 12–84). Within-Vergleich am Sitzungsende (beide Varianten gezeigt). Güte der
> LLM-Ausgaben separat in `study_guete.py`. Keine Prä/Post-Messung.

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
ebenfalls pseudonymisiert (P01–P16 statt Klarnamen) bevor sie an die
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

## 4. Fragebogen-/Score-Daten (participants.csv)

Die Daten werden separat in `data/study/participants.csv` gepflegt. Das Schema ist in
`src/sim/fixtures/participants_template.csv` dokumentiert. Alle Skalen werden einmalig
erhoben (Einzelsitzung, keine Prä/Post-Messung).

Pflichtfelder:

| Spalte | Einheit | Instrument |
|---|---|---|
| `participant_id` | — | P01…P16 |
| `group` | A/B | Randomisierung (A statisch / B LLM), n=8 je Gruppe |
| `trust` | 12–84 | Automation Trust Scale (Jian 2000), **primäre AV** |
| `sus` | 0–100 | SUS (Brooke 1996), optional |
| `tlx` | 0–100 | NASA-TLX Raw, optional |
| `fc_pref` | A/B/tie | Within-Forced-Choice nach Reveal (alle Probanden) |
| `trust_compare` | 1–7 | Within-Vergleichsrating (4=gleich, 7=B mehr), alle Probanden |
| `technikaffinitaet` | 1–5 | Likert-Item Demografiefragebogen |
| `btc_vorwissen` | 1–5 | Selbsteinschätzung Demografiefragebogen |

Die **Güte** der LLM-Ausgaben (FF2) wird getrennt erhoben (verblindetes 2-Rater-Rubrik-Rating,
`src/sim/fixtures/guete_ratings_template.csv`) und mit `src/sim/study_guete.py` ausgewertet.

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
=== PRIMÄR (H1, Vertrauen, Mann-Whitney-U, einseitig) ===
  H1: Vertrauen Jian-Summe (Gruppe B > A, einseitig, between)
    → mann_whitney: stat=12.0, p=0.041, r=0.45 [mittel] (N=16)

=== WITHIN (H2, Direktvergleich A vs. B) ===
  H2a: Forced-Choice B vs. A (Vorzeichentest, B > Zufall)
    → binomial: stat=11.0, p=0.105, p_hat=0.69 (N=16)
  H2b: Vergleichsrating vs. Mitte 4 (Wilcoxon, B-Seite > Mitte)
    → wilcoxon: stat=78.0, p=0.038, r=0.41 [mittel] (N=14)

=== SEKUNDÄR (deskriptiv, A vs. B) ===
  SUS (A vs. B, zweiseitig)
    → mann_whitney: stat=24.0, p=0.401, r=0.21 [klein] (N=16)
...

Hinweis: N=16; der between-Vergleich (n=8 je Gruppe) ist unterpowert. Der
Within-Vergleich (N=16) trägt mehr Power. ...
```

### Berichtspflicht (aus Methodik)

p-Werte werden nie isoliert berichtet. Pflichtformat:

```
stat=7.5, p=0.31, r=0.28 [klein] (N=16)
```

Effektgröße r nach Field (2018):
- r ≈ 0.1 → klein
- r ≈ 0.3 → mittel
- r ≈ 0.5 → groß

Mit balancierten Gruppen (n=8 je Gruppe) sind nur große Effekte zuverlässig detektierbar.
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
