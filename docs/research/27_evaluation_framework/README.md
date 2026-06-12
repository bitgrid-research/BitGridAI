# 27 – Evaluationsrahmen (v2)

Dieses Kapitel beschreibt den **Evaluationsrahmen**, mit dem BitGridAI in einer empirischen Studie untersucht wird.
Ziel ist es, die Wirkung des **Erklärformats** auf das **Nutzervertrauen** zu bewerten: Eine **LLM-Erklärung** (ohne Personas) wird mit einem **statischen, regelbasierten Erklärtext** verglichen. Ergänzend wird die **Güte** der LLM-Ausgaben objektiv gemessen.

Der Fokus liegt auf zwei Forschungsfragen: **FF1** (Vertrauen, A vs. B) und **FF2** (Güte der Ausgaben). Verbindendes Konzept ist die **Vertrauens-Kalibrierung**: Ist ein etwaiges Vertrauens-Plus der LLM-Variante durch die objektive Güte gedeckt, oder liegt Über-Vertrauen vor?

&nbsp;

## Überblick

Die Evaluation ist als **Mixed-Design** in einer **Einzelsitzung** angelegt: ein Between-Vergleich (A/B) für die primäre Trust-Messung plus ein Within-Direktvergleich am Sitzungsende. Beide Varianten zeigen einen Erklärbereich — der Unterschied liegt allein in der *Art* der Erklärung:

* **Gruppe A – statisch** (n = 8): regelbasiert erzeugte, für alle Probanden wortgleiche Erklärtexte (kein Sprachmodell).
* **Gruppe B – LLM** (n = 8): natürlichsprachliche LLM-Erklärung in **einer einzigen, generischen Stimme ohne Personas**. Die Faktenbasis (R1–R5) ist identisch zu A; variiert wird nur die Formulierung. 🟦

Die Studie kombiniert die **quantitative Hauptmessung** (Nutzervertrauen) mit einem **Within-Direktvergleich**, **qualitativen Vertrauensbegründungen** und einer **objektiven Güte-Bewertung** der Ausgaben.

&nbsp;

## Evaluationsziele

1. **Vertrauen messen (FF1, primär)**
   Erhöht die LLM-Erklärung (B) gegenüber dem statischen Regeltext (A) das Nutzervertrauen, between und im Within-Direktvergleich?
2. **Güte bewerten (FF2)**
   Wie ist die objektive Güte der LLM-Ausgaben (Faithfulness gegen den deterministischen Kern, Rubrik), und deckt sie ein Vertrauens-Plus (Kalibrierung)?
3. **Behaviorale Verlässlichkeit (optional)**
   Greifen Nutzer angemessen in die Automatik ein (kein vorschnelles Disuse, kein blindes Misuse)?
4. **Transparenz validieren (Systemcheck)**
   Sind UI-Begründungen und Systemlogs (DecisionEvents) konsistent?

&nbsp;

## Studiendesign

* **Design:** Mixed (Between-Faktor Gruppe A/B + Within-Direktvergleich)
* **Stichprobe:** N = 16 — Gruppe A (statisch) n = 8, Gruppe B (LLM) n = 8, **ohne Persona-Untergliederung**; heterogener Hintergrund; Ausschluss von Domänen-Experten (Energie-/Regelungstechnik, Informatik)
* **Format:** Einzelsitzung, ca. 60–90 Minuten pro Proband (kein Längsschnitt)
* **Statistik:** Mann-Whitney-U (einseitig) auf das Vertrauen, Gruppe A (n = 8) vs. B (n = 8); Welch-/t-Test bei erfüllten Voraussetzungen (r bzw. Cohen's *d*, 95 %-KI). Within: Binomial-/Vorzeichentest (Forced-Choice) und Wilcoxon (Vergleichsrating gegen die Mitte).
* **Standardisierung:** identische, gescriptete Szenario-Abfolge für alle Probanden — eingespielt per **Replay** des deterministischen Regelkerns (die zehn Szenarien S01–S10: [Übersicht in Kapitel 26](../26_scenarios_and_use_cases/README.md#deterministische-studienszenarien-s01s10), kanonische Spezifikation in [20.2.4.4](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/README.md))

### Sitzungsablauf

1. Einwilligung
2. Demographie + Vorwissen (Technikaffinität, BTC-Vorwissen; **keine** Persona-Steuerung)
3. Erwartungs-Vorfrage (naives Ausgangsmodell, qualitativ)
4. Szenariophase am Dashboard mit der **zugewiesenen** Variante (gescriptete Sequenz S01–S10)
5. **Trust-Messung (primär)** + offene Vertrauensfragen, audioaufgezeichnet, **vor** dem Reveal
6. **Reveal** der anderen Variante + **Within-Vergleich** (Forced-Choice + Vergleichsrating)
7. Abschluss + Debrief

### Setting

* Smart-Home-Laborumgebung
* Simulierte PV- und Batterieprofile (Szenario-Fixtures via Replay)
* Reale, steuerbare Last (ASIC-Miner als synthetisches Testobjekt)

&nbsp;

## Methodik

| Ebene                    | Methode                                      | Ziel                                              |
| ------------------------ | -------------------------------------------- | ------------------------------------------------- |
| **Nutzerebene**          | Automation Trust Scale + offene Fragen       | Nutzervertrauen (primäre AV, FF1)                 |
| **Within-Vergleich**     | Forced-Choice + Vergleichsrating             | Direktvergleich des Vertrauens (H2)               |
| **Output-Ebene**         | Faithfulness + Rubrik (2 Rater, κ)           | Objektive Güte der LLM-Ausgaben (FF2)             |
| **Qualitative Analyse**  | Thematische Analyse (Braun & Clarke)         | Wann/warum erzeugt ein Text mehr Vertrauen        |
| **Quantitative Analyse** | Mann-Whitney/Wilcoxon/Binomial (r, KI)       | Gruppen- und Within-Vergleich des Vertrauens      |
| **Systemebene**          | Logging, Log↔UI-Abgleich                     | Transparenz-/Konsistenzprüfung                    |

&nbsp;

## Evaluationsumgebung

### Hardware

* x86 Mini-PC mit lokalem System (z. B. UmbrelOS)
* Tablet als Smart-Home-Dashboard
* Steuerbare ASIC-Last (z. B. Bitaxe Gamma, NerdQaxe++)
* Messsteckdosen (z. B. Shelly Plug S Gen3)

### Software & KI

* Lokales Dashboard in zwei UI-Varianten (statisch / LLM)
* Lokales LLM via Ollama (**qwen3.5:9b**), eine generische Erklär-Instruktion (ohne Personas)
* Deterministisches Template-Fallback bei LLM-Nichtverfügbarkeit; Ausgaben werden eingefroren

### Datenbasis

* Gescriptete PV-/Batterie-Szenarien ([S01–S10](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/README.md), Replay-Fixtures, für alle Probanden identisch)
* Reale Telemetriedaten der Last
* Strukturierte Logs (DecisionEvents: Entscheidungen, Gründe, Overrides)

&nbsp;

## Erhebungsinstrumente

* **Automation Trust Scale** (primär): Jian 2000, 12 Items, auf die gesehene Variante, vor dem Reveal
* **Offene Vertrauensfragen**: „Hast du vertraut? · bei welchen Entscheidungen mehr/weniger? · haben die Texte das Vertrauen beeinflusst? · gab es einen unglaubwürdigen Text?“ — audioaufgezeichnet, transkribiert
* **Within-Vergleichsbogen**: Forced-Choice (A/B) + 7-stufiges Vergleichsrating + offene Begründung
* **Demographie + Vorwissen** (deskriptive Kovariaten; keine Persona-Steuerung)
* **Optionale Skalen (einmalig)**: SUS, Raw NASA-TLX
* **Güte-Rubrik (FF2)**: verblindetes 2-Rater-Rating der eingefrorenen Erklärtexte (kein Probandenbezug)
* **Systemlogs**: DecisionEvents, Override-Ereignisse, Template-Fallback-Vorkommen

&nbsp;

## Bewertungsmetriken

| Kategorie             | Metrik                                  | Beschreibung                                                        |
| --------------------- | --------------------------------------- | ------------------------------------------------------------------ |
| **Vertrauen (FF1)**   | Automation Trust Scale (12–84)          | subjektives Vertrauen, primäre AV (between)                        |
| **Within (H2)**       | Forced-Choice + Vergleichsrating (1–7)  | Direktvergleich des Vertrauens beider Varianten                    |
| **Güte (FF2)**        | Faithfulness + Rubrik 0–6 (2 Rater, κ)  | Korrektheit, Vollständigkeit, Klarheit; Halluzinations-Flag        |
| **Verlässlichkeit (opt.)** | Override-Angemessenheit (kategorial) | angemessen / Disuse-Tendenz / Misuse-Tendenz; Verständnis der R3-Sperre |
| **Usability (opt.)**  | SUS, NASA-TLX                           | Usability bzw. kognitive Belastung, einmalig                       |
| **Transparenz**       | Log-Konsistenz                          | Übereinstimmung DecisionEvent ↔ UI-Begründung                      |

&nbsp;

## Auswertung & Dokumentation

* Primäranalyse: Mann-Whitney-U (Gruppe A vs. B) auf das Vertrauen; Voraussetzungsprüfung (Shapiro-Wilk, Levene → Welch/t-Test)
* Within: Binomial-/Vorzeichentest (Forced-Choice) und Wilcoxon (Vergleichsrating gegen die Mitte)
* Güte (FF2): Faithfulness-Raten + Rubrik-Mittelwerte + Interrater-κ; Kalibrierung Vertrauen × Güte
* **p-Werte nie isoliert** — stets mit Effektgröße (r bzw. Cohen's *d*), 95 %-KI und N
* Qualitativ: thematische Analyse der offenen Vertrauensbegründungen
* Triangulation aus Trust-Score, Within-Vergleich, Güte und Verhaltensspur
* Dokumentation in internen Notebooks; Rohdaten- und Log-Export für Auditierbarkeit

Der Schwerpunkt liegt auf dem **Vertrauen** und seiner **Kalibrierung** gegen die objektive **Güte** der Erklärungen.

&nbsp;

## Zusammenfassung

Der Evaluationsrahmen vergleicht in einer Einzelsitzung ein **statisches** mit einem **LLM-basierten** Erklärformat (ohne Personas) und misst primär das **Nutzervertrauen**. Er kombiniert die Between-Hauptmessung mit einem Within-Direktvergleich, qualitativen Vertrauensbegründungen und einer objektiven **Güte-Bewertung** der Ausgaben — und liefert damit eine fundierte Grundlage für die Bewertung transparenter, lokal ausgeführter Energiemanagementsysteme.

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
