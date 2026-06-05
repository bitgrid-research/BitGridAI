# 27 – Evaluationsrahmen (v1)

Dieses Kapitel beschreibt den **Evaluationsrahmen**, mit dem BitGridAI in einer empirischen Studie untersucht wird.
Ziel ist es, die Wirkung des **Erklärformats** auf das **Regelverständnis** von Laiennutzern zu bewerten: Eine **adaptive, persona-basierte LLM-Erklärung** wird mit einem **statischen, regelbasierten Erklärtext** verglichen.

Der Fokus liegt auf dem **Verständnis der Entscheidungslogik** (mentales Modell), insbesondere auf dem zentralen Lernziel **energiebewusstes Steuern statt Einspeisen**. Ergänzend werden die **Angemessenheit manueller Eingriffe** (Override) und optional **Vertrauen** betrachtet.

&nbsp;

## Überblick

Die Evaluation ist als **Between-Subjects-Studie** in einer **Einzelsitzung** angelegt, in der zwei Erklärformate verglichen werden. Beide Varianten zeigen einen Erklärbereich — der Unterschied liegt allein in der *Art* der Erklärung:

* **Gruppe A – statisch** (n = 5): regelbasiert erzeugte, für alle Probanden wortgleiche Erklärtexte (kein Sprachmodell).
* **Gruppe B – adaptiv** (n = 15): natürlichsprachliche LLM-Erklärung in einer von **drei Persona-Stufen** (Laie → technisch versiert), je n = 5, gemäß Kapitel 24.

Die Studie kombiniert die **quantitative Hauptmessung** (Regelverständnis-Score) mit **qualitativen Erhebungen** (offene Fragen, Override-Aufgabe).

&nbsp;

## Evaluationsziele

1. **Regelverständnis messen (primär)**
   Verstehen Nutzer die Regeln (R1–R5) und ihr Zusammenspiel — und erkennen sie, dass das System Eigenverbrauch dem Einspeisen vorzieht?
2. **Override-Angemessenheit bewerten (sekundär)**
   Greifen Nutzer mit besserem Verständnis angemessener in die Automatik ein (kein vorschnelles Disuse, kein blindes Misuse)?
3. **Vertrauen erfassen (optional)**
   Unterscheidet sich das Vertrauen in die Automatisierung zwischen den Bedingungen?
4. **Transparenz validieren (Systemcheck)**
   Sind UI-Begründungen und Systemlogs (DecisionEvents) konsistent?

&nbsp;

## Studiendesign

* **Design:** Between-Subjects (Gruppe A statisch vs. Gruppe B adaptiv)
* **Stichprobe:** N = 20 — Gruppe A (statisch) n = 5, Gruppe B (adaptiv) n = 15 in 3 Persona-Stufen à n = 5; heterogener Hintergrund; Ausschluss von Domänen-Experten (Energie-/Regelungstechnik, Informatik) zur Vermeidung eines Ceiling-Effekts
* **Format:** Einzelsitzung, ca. 60–90 Minuten pro Proband (kein Längsschnitt)
* **Statistik:** t-Test für unabhängige Stichproben (einseitig) auf den Regelverständnis-Score; Primärvergleich Gruppe A vs. **gepoolte** Gruppe B (Cohen's *d*, 95 %-KI). Der Persona-Vergleich (n = 5 je Stufe) bleibt **explorativ/deskriptiv**.
* **Standardisierung:** identische, gescriptete Szenario-Abfolge für alle Probanden — eingespielt per **Replay** des deterministischen Regelkerns (die zehn Szenarien S01–S10: [Übersicht in Kapitel 26](../26_scenarios_and_use_cases/README.md#deterministische-studienszenarien-s01s10), kanonische Spezifikation in [20.2.4.4](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/README.md))

### Sitzungsablauf

1. Einwilligung
2. Demographie + **Vorwissens-Einstufung** (bestimmt in Gruppe B die Persona-Stufe)
3. Erwartungs-Vorfrage (naives Ausgangsmodell, qualitativ)
4. Lern-/Szenariophase am Dashboard (gescriptete Sequenz: R2-START bei Überschuss, R3-STOP, R4-Prognose, R5-Hysterese, Prioritätskonflikt)
5. **Offene Verständnisfragen** (primäre Erhebung, audioaufgezeichnet)
6. Override-Aufgabe + Abschluss (optional Trust, Verständlichkeits-Feedback)

### Setting

* Smart-Home-Laborumgebung
* Simulierte PV- und Batterieprofile (Szenario-Fixtures via Replay)
* Reale, steuerbare Last (ASIC-Miner als synthetisches Testobjekt)

&nbsp;

## Methodik

| Ebene                    | Methode                                      | Ziel                                              |
| ------------------------ | -------------------------------------------- | ------------------------------------------------- |
| **Nutzerebene**          | Offene Verständnisfragen (Rater-kodiert)     | Regelverständnis / mentales Modell (primäre AV)   |
| **Interaktionsebene**    | Override-Aufgabe, Verhaltensspur im Log      | Angemessenheit manueller Eingriffe                |
| **Qualitative Analyse**  | Thematische Analyse (Braun & Clarke)         | Muster und Fehlvorstellungen im Verständnis       |
| **Quantitative Analyse** | t-Test (Cohen's *d*, KI), Interrater-κ       | Gruppenvergleich des Regelverständnis-Scores      |
| **Systemebene**          | Logging, Log↔UI-Abgleich                     | Transparenz-/Konsistenzprüfung                    |

&nbsp;

## Evaluationsumgebung

### Hardware

* x86 Mini-PC mit lokalem System (z. B. UmbrelOS)
* Tablet als Smart-Home-Dashboard
* Steuerbare ASIC-Last (z. B. Bitaxe Gamma, NerdQaxe++)
* Messsteckdosen (z. B. Shelly Plug S Gen3)

### Software & KI

* Lokales Dashboard in zwei UI-Varianten (statisch / adaptiv)
* Lokales LLM via Ollama (**Qwen3:8b**), persona-adaptiver Prompt
* Deterministisches Template-Fallback bei LLM-Nichtverfügbarkeit

### Datenbasis

* Gescriptete PV-/Batterie-Szenarien ([S01–S10](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/README.md), Replay-Fixtures, für alle Probanden identisch)
* Reale Telemetriedaten der Last
* Strukturierte Logs (DecisionEvents: Entscheidungen, Gründe, Overrides)

&nbsp;

## Erhebungsinstrumente

* **Offene Verständnisfragen** (primär): „Wie funktioniert das System? · Erwartungen? · wichtigste Einflussregeln? · Warum Steuern statt Einspeisen?“ — audioaufgezeichnet, transkribiert
* **Demographie + Vorwissens-Einstufung**: Technikaffinität, Energie-/EMS-Vorwissen, Bitcoin-Vorwissen, Wärme-Nutzungsabsicht (steuert zugleich die Persona in Gruppe B)
* **Override-Aufgabe**: beobachtetes Eingriffsverhalten + mündliche Begründung
* **Optionale Skalen (einmalig)**: Automation Trust Scale; ergänzend SUS, Raw NASA-TLX
* **Systemlogs**: DecisionEvents, Override-Ereignisse, Template-Fallback-Vorkommen

&nbsp;

## Bewertungsmetriken

| Kategorie             | Metrik                                  | Beschreibung                                                        |
| --------------------- | --------------------------------------- | ------------------------------------------------------------------ |
| **Regelverständnis**  | Score 0–12 (Rubrik, 2 Rater, κ)         | Korrektheit der erklärten Regeln + Konzept „Steuern statt Einspeisen“ (primäre AV) |
| **Override**          | Angemessenheit (kategorial)             | angemessen / Disuse-Tendenz / Misuse-Tendenz; Verständnis der R3-Sperre |
| **Vertrauen (opt.)**  | Automation Trust Scale (Likert)         | subjektives Vertrauen, einmalig                                    |
| **Usability (opt.)**  | SUS, NASA-TLX                           | Usability bzw. kognitive Belastung, einmalig                       |
| **Transparenz**       | Log-Konsistenz                          | Übereinstimmung DecisionEvent ↔ UI-Begründung                      |

&nbsp;

## Auswertung & Dokumentation

* Primäranalyse: t-Test (Gruppe A vs. B) auf den Regelverständnis-Score; Voraussetzungsprüfung (Shapiro-Wilk, Levene → Welch/Mann-Whitney als Fallback)
* **p-Werte nie isoliert** — stets mit Effektgröße (Cohen's *d*), 95 %-KI und N
* Qualitativ: thematische Analyse der offenen Antworten und Override-Begründungen
* Triangulation aus Verständnis-Score, qualitativen Themen und Verhaltensspur
* Dokumentation in internen Notebooks; Rohdaten- und Log-Export für Auditierbarkeit

Der Schwerpunkt liegt auf der **Erklärqualität** und ihrem Einfluss auf das **Regelverständnis**.

&nbsp;

## Zusammenfassung

Der Evaluationsrahmen vergleicht in einer Einzelsitzung ein **statisches** mit einem **persona-adaptiven** Erklärformat und misst primär das **Regelverständnis** von Laiennutzern. Er verbindet die quantitative Hauptmessung mit qualitativen Erhebungen und einer beobachteten Override-Aufgabe — und liefert damit eine fundierte Grundlage für die Bewertung transparenter, lokal ausgeführter Energiemanagementsysteme.

&nbsp;

---

> **Nächster Schritt:** Der Evaluationsrahmen steht.
> Im nächsten Kapitel folgen Reflexion & Transfer.
>
> 👉 Weiter zu **[28 - Reflexion & Transfer](../28_reflection_and_transfer/README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
