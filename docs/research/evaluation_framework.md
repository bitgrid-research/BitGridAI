# Evaluation Framework / Evaluationsrahmen

## Überblick / Overview

Das **Evaluation Framework** definiert die methodische Grundlage zur Bewertung von BitGridAI im Hinblick auf **Erklärbarkeit, Nutzbarkeit und Energieeffizienz**.
Es kombiniert empirische HCI-Methoden mit technischer Leistungsanalyse und schafft damit eine Brücke zwischen Nutzerverhalten und Systemleistung.

> The **Evaluation Framework** defines the methodological foundation for evaluating BitGridAI regarding **explainability, usability, and energy efficiency**.
> It integrates empirical HCI methods with technical performance assessment, bridging user behavior and system functionality.

---

## Evaluationsziele / Evaluation Goals

1. **Erklärbarkeit messen** – Wie gut versteht der Nutzer Systementscheidungen in Echtzeit?
2. **Energieeffizienz analysieren** – Wie viel Energie wird durch intelligente Laststeuerung eingespart?
3. **Vertrauen bewerten** – Wie beeinflusst erklärbares Verhalten das Vertrauen in automatisierte Entscheidungen?
4. **Interaktion untersuchen** – Wie intuitiv ist die Benutzeroberfläche im Zusammenspiel mit Smart-Energy-Systemen?
5. **Transparenzvalidierung** – Wie konsistent und überprüfbar sind Systemlogs und Entscheidungsbegründungen?

> 1) **Measure explainability** – How well do users understand system decisions in real-time?
> 2) **Analyze energy efficiency** – How much energy is saved through intelligent load management?
> 3) **Assess trust** – How does explainable automation affect user trust?
> 4) **Evaluate interaction** – How intuitive is the user interface in Smart Energy contexts?
> 5) **Validate transparency** – How consistent and auditable are logs and decision explanations?

---

## Methodik / Methodology

| Ebene                    | Methode                                | Ziel                                                                    |
| ------------------------ | -------------------------------------- | ----------------------------------------------------------------------- |
| **Systemebene**          | Logging & Energiemessung               | Bewertung von Laststeuerung, Reaktionszeiten und Energieeffizienz       |
| **Nutzerebene**          | Think-Aloud & Interviews               | Untersuchung der mentalen Modelle und Akzeptanz erklärbarer Systeme     |
| **Interaktionsebene**    | Task-basierte Szenarien                | Messung von Verständlichkeit, Interaktionszeit und Fehlerraten          |
| **Qualitative Analyse**  | Inhaltsanalyse                         | Ableitung von Mustern in Nutzerfeedback und Wahrnehmung von Transparenz |
| **Quantitative Analyse** | Metriken (Energie, Nutzung, Vertrauen) | Objektive Vergleichswerte zur Leistungsbewertung                        |

> | Level                     | Method                         | Objective                                                   |
> | ------------------------- | ------------------------------ | ----------------------------------------------------------- |
> | **System Level**          | Logging & energy monitoring    | Evaluate load control, response times, and efficiency       |
> | **User Level**            | Think-aloud & interviews       | Explore mental models and acceptance of explainable systems |
> | **Interaction Level**     | Task-based scenarios           | Measure clarity, task time, and error rate                  |
> | **Qualitative Analysis**  | Content analysis               | Derive user perception and transparency patterns            |
> | **Quantitative Analysis** | Metrics (energy, usage, trust) | Provide comparable benchmarks for evaluation                |

---

## Evaluationsumgebung / Evaluation Environment

* **Hardware:** Lokale Workstation oder Edge-System (z. B. Mini-PC mit BitGrid Core Umgebung)
* **Sensorik:** Virtuelle oder reale Smart-Energy-Datenquellen (PV, Speicher, Lasten)
* **UI-Plattform:** Browserbasiertes Dashboard / integrierte lokale Schnittstelle
* **Datenerfassung:** JSON-basierte Logfiles & strukturierte Nutzerstudien
* **Teilnehmende:** 10–15 Proband:innen mit unterschiedlichem technologischem Hintergrund

> - **Hardware:** Local workstation or edge system (e.g., Mini-PC running BitGrid Core environment)
> - **Sensors:** Real or simulated Smart Energy data sources (PV, storage, flexible loads)
> - **UI Platform:** Web-based dashboard / integrated local interface
> - **Data Collection:** JSON logs & structured user studies
> - **Participants:** 10–15 users with varied technical backgrounds

---

## Bewertungsmetriken / Evaluation Metrics

| Kategorie             | Metrik                    | Beschreibung                                                             |
| --------------------- | ------------------------- | ------------------------------------------------------------------------ |
| **Explainability**    | Verständlichkeitsrate (%) | Anteil der erklärten Systementscheidungen, die korrekt verstanden werden |
| **Energy Efficiency** | kWh-Einsparung            | Differenz zwischen optimiertem und unoptimiertem Betrieb                 |
| **Transparency**      | Log-Integrität            | Vergleich zwischen interner Entscheidung und UI-Darstellung              |
| **User Trust**        | Vertrauen (Likert-Skala)  | Subjektive Bewertung nach Szenario-Interaktion                           |
| **Usability**         | Task Completion Time      | Zeit bis zur erfolgreichen Benutzerreaktion                              |

> | Category              | Metric                 | Description                                           |
> | --------------------- | ---------------------- | ----------------------------------------------------- |
> | **Explainability**    | Comprehension rate (%) | Share of system explanations correctly understood     |
> | **Energy Efficiency** | Energy savings (kWh)   | Difference between optimized and baseline operation   |
> | **Transparency**      | Log consistency        | Comparison between internal and UI-reported decisions |
> | **User Trust**        | Trust (Likert scale)   | Subjective user evaluation after interaction          |
> | **Usability**         | Task completion time   | Time to successful user action                        |

---

## Auswertung & Dokumentation / Evaluation & Reporting

* Ergebnisse werden in **Jupyter Notebooks** oder internen Analyse-Dashboards visualisiert (z. B. Energieprofile, Nutzerfeedback, Vertrauensindizes).
* Qualitative Daten (z. B. Interviewantworten) werden thematisch codiert und mit quantitativen Metriken korreliert.
* Jede Evaluationsrunde endet mit einem **Iterativen Verbesserungszyklus** (Design → Test → Analyse → Anpassung).

> - Results are visualized using **Jupyter Notebooks** or internal analytics dashboards (e.g., energy profiles, feedback, trust indices).
> - Qualitative data is thematically coded and correlated with quantitative metrics.
> - Each evaluation cycle follows an **iterative improvement loop** (design → test → analyze → adapt).

---

## Zusammenfassung / Summary

Das Evaluationsframework dient als methodisches Rückgrat für die **Validierung von BitGridAI**.
Es verknüpft **technische Messdaten mit menschlicher Wahrnehmung**, um sowohl Effizienz als auch Akzeptanz erklärbarer, lokal gesteuerter Energiesysteme zu messen.

> The evaluation framework provides the methodological backbone for **validating BitGridAI**.
> It links **technical metrics with human perception** to assess both efficiency and acceptance of explainable, locally managed energy systems.
