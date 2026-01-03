# Evaluation Framework / Evaluationsrahmen

## Ueberblick

Das Evaluation Framework beschreibt, wie BitGridAI im Rahmen einer
Between-Subjects-Studie (Baseline vs. Explainability-Layer) bewertet wird.
Im Fokus stehen Verstaendnis der Entscheidungslogik, Vertrauen,
wahrgenommene Kontrolle, kognitive Belastung und Energieeffizienz.

---

## Evaluationsziele

1. **Erklaerbarkeit messen** - Verstehen Nutzer die Gruende fuer Start/Stop?
2. **Vertrauen und Kontrolle bewerten** - Fuehlen sich Nutzer handlungsfaehig?
3. **Kognitive Belastung erfassen** - Fuehren Erklaerungen zu Mehrbelastung?
4. **Energieeffizienz analysieren** - Welche Unterschiede zeigen sich zwischen den Varianten?
5. **Transparenzvalidierung** - Sind Logs und UI-Begruendungen konsistent?

---

## Studiendesign

- **Design:** Between-Subjects (Baseline-UI vs. Explainability-Layer).
- **Stichprobe:** N=10, heterogener technischer Hintergrund.
- **Dauer:** 10 Tage, taeglich 10-15 Min (Daily Diary Method).
- **Aufgaben:** Speicher/PV-Status pruefen, Laststeuerung validieren, Override testen.
- **Setting:** Smart-Home-Labor mit simulierten PV- und Batterieprofilen.

---

## Methodik

| Ebene                    | Methode                                               | Ziel                                                                  |
| ------------------------ | ----------------------------------------------------- | --------------------------------------------------------------------- |
| **Systemebene**          | Logging, Energiemessung, Baseline/XAI-Vergleich        | Bewertung von Laststeuerung, Reaktionszeiten und Effizienz           |
| **Nutzerebene**          | Daily Diary, Leitfaden-Interviews                     | Untersuchung mentaler Modelle, Verstaendnis, Vertrauen                |
| **Interaktionsebene**    | Task-basierte Szenarien, Override-Tests               | Messung von Klarheit, Task-Zeit, Fehlerraten                           |
| **Qualitative Analyse**  | Inhaltsanalyse (Diary + Interviews)                   | Muster in Wahrnehmung, Vertrauen, Kontrollgefuehl                      |
| **Quantitative Analyse** | Metriken (SUS, NASA-TLX, Energie, Vertrauen, Logs)    | Vergleichbare Kennzahlen zwischen beiden Bedingungen                  |

---

## Evaluationsumgebung

* **Hardware:** x86 Mini-PC mit UmbrelOS, UmbrelHome (4TB), Tablet fuer Dashboard,
  ASIC-Lasten (Bitaxe Gamma, NerdQaxe++), Shelly Plug S Gen3.
* **KI/Erklaerung:** lokales LLM via Ollama, quantisierte Modelle (Phi-3 Mini, Mistral 7B).
* **Sensorik:** simulierte PV- und Batterieprofile, reale ASIC-Telemetrie.
* **UI-Plattform:** lokales Dashboard in zwei Varianten (Baseline/XAI).
* **Datenerfassung:** JSON-Logs, Erklaertexte, Nutzeraktionen.

---

## Erhebungsinstrumente

- **Daily Diary Eintraege** (kurze taegliche Interaktion, 10 Tage).
- **Leitfaden-Interviews** zum Verstaendnis und Vertrauen.
- **Frageboegen:** SUS (Usability) und NASA-TLX (Belastung).
- **System-Logs:** Entscheidungen, Gruende, Overrides, Energiefluesse.

---

## Bewertungsmetriken

| Kategorie              | Metrik                               | Beschreibung                                                         |
| ---------------------- | ------------------------------------ | -------------------------------------------------------------------- |
| **Explainability**     | Verstaendnisrate (%)                 | Anteil korrekt erklaerter Entscheidungen (Diary + Interview)         |
| **Trust & Control**    | Vertrauen (Likert) / Override-Rate   | Subjektives Vertrauen und Eingriffsverhalten                         |
| **Cognitive Load**     | NASA-TLX Score                       | Mentale Belastung pro Sitzung                                        |
| **Usability**          | SUS / Task-Zeit                      | Subjektive Usability und objektive Task-Dauer                         |
| **Energy Efficiency**  | kWh-Einsparung                       | Differenz zwischen Baseline und Explainability-Variante              |
| **Transparency**       | Log-Konsistenz                       | Vergleich interner Entscheidung und UI-Begruendung                   |

---

## Auswertung & Dokumentation

* Vergleich der beiden UI-Varianten (Baseline vs. Explainability) auf allen Metriken.
* Triangulation aus Logs, Diarys, Interviews und Frageboegen.
* Ergebnisdokumentation in Notebooks oder internen Dashboards
  mit Fokus auf Erklaerqualitaet, Vertrauen und Nutzbarkeit.

---

## Zusammenfassung

Der Evaluationsrahmen verbindet technische Messdaten mit Nutzerwahrnehmung,
um die Wirkung eines erklaerenden KI-Layers auf Verstaendnis, Vertrauen,
Kontrolle und Belastung zu pruefen. Die Studie liefert damit belastbare
Gestaltungsimpulse fuer transparente, lokal ausgefuehrte Energiesysteme.

---

> **Naechster Schritt:** Der Evaluationsrahmen steht.
> Im naechsten Kapitel folgt die Literaturuebersicht.
>
> 👉 Weiter zu **[29 - Literaturuebersicht](./literature_review.md)**
>
> 🔙 Zurueck zu **[22 - Interface Design](./22_interface_design/README.md)**
>
> 🏠 Zurueck zur **[Hauptuebersicht](../README.md)**
