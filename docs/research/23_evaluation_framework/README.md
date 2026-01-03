# Evaluation Framework / Evaluationsrahmen

## Überblick

Das Evaluation Framework beschreibt, wie BitGridAI im Rahmen einer
Between-Subjects-Studie (Baseline vs. Explainability-Layer) bewertet wird.
Im Fokus stehen Verständnis der Entscheidungslogik, Vertrauen,
wahrgenommene Kontrolle, kognitive Belastung und Energieeffizienz.

---

## Evaluationsziele

1. **Erklärbarkeit messen** - Verstehen Nutzer die Gründe für Start/Stop?
2. **Vertrauen und Kontrolle bewerten** - Fühlen sich Nutzer handlungsfähig?
3. **Kognitive Belastung erfassen** - Führen Erklärungen zu Mehrbelastung?
4. **Energieeffizienz analysieren** - Welche Unterschiede zeigen sich zwischen den Varianten?
5. **Transparenzvalidierung** - Sind Logs und UI-Begründungen konsistent?

---

## Studiendesign

- **Design:** Between-Subjects (Baseline-UI vs. Explainability-Layer).
- **Stichprobe:** N=10, heterogener technischer Hintergrund.
- **Dauer:** 10 Tage, täglich 10-15 Min (Daily Diary Method).
- **Aufgaben:** Speicher/PV-Status prüfen, Laststeuerung validieren, Override testen.
- **Setting:** Smart-Home-Labor mit simulierten PV- und Batterieprofilen.

---

## Methodik

| Ebene                    | Methode                                               | Ziel                                                                  |
| ------------------------ | ----------------------------------------------------- | --------------------------------------------------------------------- |
| **Systemebene**          | Logging, Energiemessung, Baseline/XAI-Vergleich        | Bewertung von Laststeuerung, Reaktionszeiten und Effizienz           |
| **Nutzerebene**          | Daily Diary, Leitfaden-Interviews                     | Untersuchung mentaler Modelle, Verständnis, Vertrauen                |
| **Interaktionsebene**    | Task-basierte Szenarien, Override-Tests               | Messung von Klarheit, Task-Zeit, Fehlerraten                           |
| **Qualitative Analyse**  | Inhaltsanalyse (Diary + Interviews)                   | Muster in Wahrnehmung, Vertrauen, Kontrollgefühl                      |
| **Quantitative Analyse** | Metriken (SUS, NASA-TLX, Energie, Vertrauen, Logs)    | Vergleichbare Kennzahlen zwischen beiden Bedingungen                  |

---

## Evaluationsumgebung

* **Hardware:** x86 Mini-PC mit UmbrelOS, UmbrelHome (4TB), Tablet für Dashboard,
  ASIC-Lasten (Bitaxe Gamma, NerdQaxe++), Shelly Plug S Gen3.
* **KI/Erklärung:** lokales LLM via Ollama, quantisierte Modelle (Phi-3 Mini, Mistral 7B).
* **Sensorik:** simulierte PV- und Batterieprofile, reale ASIC-Telemetrie.
* **UI-Plattform:** lokales Dashboard in zwei Varianten (Baseline/XAI).
* **Datenerfassung:** JSON-Logs, Erklärtexte, Nutzeraktionen.

---

## Erhebungsinstrumente

- **Daily Diary Einträge** (kurze tägliche Interaktion, 10 Tage).
- **Leitfaden-Interviews** zum Verständnis und Vertrauen.
- **Fragebögen:** SUS (Usability) und NASA-TLX (Belastung).
- **System-Logs:** Entscheidungen, Gründe, Overrides, Energieflüsse.

---

## Bewertungsmetriken

| Kategorie              | Metrik                               | Beschreibung                                                         |
| ---------------------- | ------------------------------------ | -------------------------------------------------------------------- |
| **Explainability**     | Verständnisrate (%)                 | Anteil korrekt erklärter Entscheidungen (Diary + Interview)         |
| **Trust & Control**    | Vertrauen (Likert) / Override-Rate   | Subjektives Vertrauen und Eingriffsverhalten                         |
| **Cognitive Load**     | NASA-TLX Score                       | Mentale Belastung pro Sitzung                                        |
| **Usability**          | SUS / Task-Zeit                      | Subjektive Usability und objektive Task-Dauer                         |
| **Energy Efficiency**  | kWh-Einsparung                       | Differenz zwischen Baseline und Explainability-Variante              |
| **Transparency**       | Log-Konsistenz                       | Vergleich interner Entscheidung und UI-Begründung                   |

---

## Auswertung & Dokumentation

* Vergleich der beiden UI-Varianten (Baseline vs. Explainability) auf allen Metriken.
* Triangulation aus Logs, Diarys, Interviews und Fragebögen.
* Ergebnisdokumentation in Notebooks oder internen Dashboards
  mit Fokus auf Erklärqualität, Vertrauen und Nutzbarkeit.

---

## Zusammenfassung

Der Evaluationsrahmen verbindet technische Messdaten mit Nutzerwahrnehmung,
um die Wirkung eines erklärenden KI-Layers auf Verständnis, Vertrauen,
Kontrolle und Belastung zu prüfen. Die Studie liefert damit belastbare
Gestaltungsimpulse für transparente, lokal ausgeführte Energiesysteme.

---

> **Nächster Schritt:** Der Evaluationsrahmen steht.
> Im nächsten Kapitel folgt die Literaturübersicht.
>
> 👉 Weiter zu **[29 - Literaturübersicht](../29_literature_review/README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
