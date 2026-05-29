# 27 – Evaluationsrahmen

[TODO: Studiendesign ausarbeiten]

Dieses Kapitel beschreibt den **Evaluationsrahmen**, mit dem BitGridAI im Rahmen einer empirischen Studie untersucht wird.
Ziel ist es, die Wirkung eines **Explainability-Layers** im Vergleich zu einer **Baseline-UI** systematisch zu bewerten.

Der Fokus liegt auf dem **Verständnis der Entscheidungslogik**, dem **Vertrauen der Nutzer**, der **wahrgenommenen Kontrolle**, der **kognitiven Belastung** sowie auf **energiebezogenen Effekten**.

&nbsp;

## Überblick

Die Evaluation ist als **Between-Subjects-Studie** angelegt, in der zwei Systemvarianten verglichen werden:

* **Baseline-Variante**: Anzeige von Zuständen und Aktionen ohne erklärenden Layer
* **Explainability-Variante**: Anzeige von Zuständen inklusive erklärender Begründungen gemäß Kapitel 24

Die Studie kombiniert **technische Messungen** mit **nutzerzentrierten Erhebungsmethoden**.

&nbsp;

## Evaluationsziele

Die Evaluation verfolgt fünf zentrale Ziele:

1. **Erklärbarkeit messen**
   Verstehen Nutzer die Gründe für Start-, Stop- und NOOP-Entscheidungen?
2. **Vertrauen und Kontrolle bewerten**
   Fühlen sich Nutzer informiert und handlungsfähig?
3. **Kognitive Belastung erfassen**
   Erhöhen erklärende Informationen die mentale Belastung?
4. **Energiebezogene Effekte analysieren**
   Unterscheiden sich Energieverbrauch und Schaltverhalten zwischen den Varianten?
5. **Transparenz validieren**
   Sind UI-Begründungen und Systemlogs konsistent?

&nbsp;

## Studiendesign

* **Design:** Between-Subjects (Baseline vs. Explainability)
* **Stichprobe:** N = 10, heterogener technischer Hintergrund
* **Dauer:** 10 Tage
* **Täglicher Aufwand:** ca. 10–15 Minuten
* **Methodischer Ansatz:** Daily Diary Method kombiniert mit Abschlussinterviews

### Aufgaben

Die Teilnehmenden bearbeiten wiederkehrende Aufgaben, u. a.:

* Prüfung von PV- und Speicherzuständen
* Einordnung von Start- und Stop-Entscheidungen
* Bewertung von NOOP-Situationen
* Test manueller Overrides

### Setting

* Smart-Home-Laborumgebung
* Simulierte PV- und Batterieprofile
* Reale, steuerbare Lasten

&nbsp;

## Methodik

| Ebene                    | Methode                                     | Ziel                                            |
| ------------------------ | ------------------------------------------- | ----------------------------------------------- |
| **Systemebene**          | Logging, Energiemessung, Variantenvergleich | Analyse von Schaltverhalten und Energieeffekten |
| **Nutzerebene**          | Daily Diary, Leitfaden-Interviews           | Verständnis, Vertrauen, mentale Modelle         |
| **Interaktionsebene**    | Task-basierte Tests, Override-Szenarien     | Klarheit, Task-Zeit, Fehlannahmen               |
| **Qualitative Analyse**  | Inhaltsanalyse                              | Muster in Wahrnehmung und Vertrauen             |
| **Quantitative Analyse** | Standardisierte Skalen und Metriken         | Vergleichbarkeit der Bedingungen                |

&nbsp;

## Evaluationsumgebung

### Hardware

* x86 Mini-PC mit lokalem System (z. B. UmbrelOS)
* Tablet als Smart-Home-Dashboard
* Steuerbare ASIC-Lasten (z. B. Bitaxe Gamma, NerdQaxe++)
* Messsteckdosen (z. B. Shelly Plug S Gen3)

### Software & KI

* Lokales Dashboard in zwei UI-Varianten
* Lokales LLM via Ollama
* Quantisierte Modelle (z. B. Phi-3 Mini, Mistral 7B)

### Datenbasis

* Simulierte PV- und Batterieprofile
* Reale Telemetriedaten der Lasten
* Strukturierte JSON-Logs (Entscheidungen, Gründe, Overrides)

&nbsp;

## Erhebungsinstrumente

* **Daily Diary**: kurze tägliche Einträge über Wahrnehmung und Verständnis
* **Leitfaden-Interviews**: Vertiefung von Vertrauen und mentalen Modellen
* **Fragebögen**:

  * SUS (Usability)
  * NASA-TLX (kognitive Belastung)
* **Systemlogs**: Entscheidungen, Regelzustände, Energieflüsse

&nbsp;

## Bewertungsmetriken

| Kategorie            | Metrik                            | Beschreibung                                 |
| -------------------- | --------------------------------- | -------------------------------------------- |
| **Explainability**   | Verständnisrate (%)               | Anteil korrekt erklärter Entscheidungen      |
| **Trust & Control**  | Vertrauen (Likert), Override-Rate | Subjektives Vertrauen und Eingriffsverhalten |
| **Cognitive Load**   | NASA-TLX Score                    | Mentale Belastung pro Sitzung                |
| **Usability**        | SUS, Task-Zeit                    | Subjektive Usability und objektive Dauer     |
| **Energy Behaviour** | Schaltungen/Tag, Laufzeiten       | Systemruhe und Steuerungsverhalten           |
| **Transparency**     | Log-Konsistenz                    | Übereinstimmung Log ↔ UI                     |

&nbsp;

## Auswertung & Dokumentation

* Vergleich der beiden UI-Varianten über alle Metriken
* Triangulation aus Logs, Diaries, Interviews und Fragebögen
* Dokumentation der Ergebnisse in internen Dashboards oder Notebooks

Der Schwerpunkt liegt auf der **Erklärqualität** und deren Einfluss auf Vertrauen, Verständnis und Nutzung.

&nbsp;

## Zusammenfassung

Der Evaluationsrahmen verbindet **technische Systemdaten** mit **nutzerzentrierter Evaluation**, um die Wirkung eines erklärenden KI-Layers empirisch zu untersuchen.

Er liefert damit eine fundierte Grundlage für die Bewertung transparenter, lokal ausgeführter Energiemanagementsysteme.



---

> **Nächster Schritt:** Der Evaluationsrahmen steht.
> Im nächsten Kapitel folgen Reflexion & Transfer.
>
> 👉 Weiter zu **[28 - Reflexion & Transfer](../28_reflection_and_transfer/README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
