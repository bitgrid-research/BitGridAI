# 20.2.4.5 - SD-WQ5 - Erkenntnisziele, Hypothesen & Pre-Registration

Festschreibung **vor** der Datenerhebung (gegen HARKing). Was die Studie
beantworten soll, wie gemessen wird und was eine Hypothese *falsifizieren* würde.
Ergänzt [2024a](./2024a_study_design_sampling.md)–[2024c](./2024c_ethics_privacy_analysis.md)
und das Szenario-Set [2024d](./2024d_scenarios/README.md).

> **Markierung:** 🟦 = mit Betreuer final bestätigen (Studien-Design-Entscheidung).

> **Design-Änderung (2026-06-11, vor Datenerhebung):** Auf Empfehlung des Betreuers
> wird die Studie auf einen **reinen A/B-Vertrauensvergleich ohne Personas** umgestellt.
> Der **Persona-Faktor entfällt vollständig** (Gruppe B nutzt eine einzige, generische
> LLM-Stimme; `_PERSONA_INSTRUCTIONS`/`OLLAMA_PERSONA` aus dem Code entfernt). Die
> **primäre AV wechselt von Regelverständnis auf Nutzervertrauen** (Automation Trust
> Scale, Jian 2000). Zwei Forschungsfragen: **FF1** (Vertrauen, A vs. B) und **FF2**
> (Güte der LLM-Ausgaben, objektiv). Das Design wird **mixed**: Between-Trust (primär)
> plus Within-Direktvergleich am Sitzungsende. Änderung erfolgt **vor** jeder Erhebung
> (kein HARKing) und ist 🟦 mit dem Betreuer abgestimmt.

> **Design-Änderung (2026-06-12, vor Datenerhebung):** Einordnung als **Design Science
> Research** (Artefakt BitGridAI + Evaluation + Feedback-Schleife). Die Studie ist
> formative Evaluation **mit** konfirmatorischem A/B-Kern (H1/H2); die Güte-Befunde (FF2)
> und qualitativen Themen fließen als Verbesserungs-Input in die Erklärschicht zurück.
> **Sitzung auf ~45 Min gestrafft** (Erwartungs-Vorfrage entfällt; Within auf 2–3 Szenarien).

> **Design-Änderung (2026-10-17, vor Datenerhebung; in dieser Datei nachgetragen am
> 2026-10-28):** Entschieden am 17.10.2026, also vor der ersten Probandensitzung (VP01,
> 20.10.2026), und mit dem Betreuer (Prof. Wallach) abgestimmt. **Transparenzhinweis:** In
> diese Datei erst am 28.10.2026 eingetragen. Bis dahin waren 4 von 16 Sitzungen erhoben,
> aber **nicht ausgewertet** (keine Einsicht in Vertrauenswerte). Die Abschnitte unten
> geben den Stand vom 12.06. wieder und gelten nur, soweit dieser Nachtrag nichts anderes
> festlegt.
>
> 1. **Manipulation: Sprachstil statt LLM vs. statisch.** Variante A = umgangssprachlich
>    (Ton des Maskottchens BitHamster), Variante B = technisch (Fachbegriffe, Regel-IDs).
>    Beide Varianten sind feste Textbausteine, die deterministisch aus den Regelwerten
>    befüllt werden (`src/ha/config/bitgrid_dashboard_v3.yaml`, Objekt `V.a`/`V.b`;
>    Übersicht `docs/thesis/studie/hamster_texte_ab_vergleich.md`). Bild, Zustandslogik
>    und Informationsgehalt sind identisch. Das lokale LLM diente nur zum Entwerfen der
>    Bausteine; im Stimulus läuft **kein** LLM, damit keine Ausgabevarianz die
>    Vergleichbarkeit stört.
> 2. **Stimulus:** Replay eines realen Messtags (11.07.2026, dargestellt als 21.07.2026),
>    ca. 20 Min, für alle Personen identische Abfolge. Konstruierte Abschnitte
>    (Sensor-Ausfall, Überhitzungs-Stopp) sind markiert. Ersetzt das Snapshot-Set S1–S10.
> 3. **Design: within-subjects**, N = 16. Jede Person durchläuft den Replay-Tag zweimal,
>    einmal mit A, einmal mit B. Die Reihenfolge (AB/BA) wechselt zwischen den Personen
>    (je 8 beginnen mit A bzw. B), um Lern- und Reihenfolgeeffekte auszubalancieren.
>    🟦 Festhalten, wie die Reihenfolge je VP bestimmt wird (strikt abwechselnd oder
>    über die Liste aus `scripts/build_randomisierung.py`, Seed 20261017).
> 4. **Primäre AV: Trust in Automation nach Körber (2019)** statt Jian (2000), nach jedem
>    Durchlauf erhoben; Fragebogen vor VP01 vollständig (Item 19 ergänzt). 🟦 Quelle in
>    `zotero_export.bib` nachtragen. **Nebenmaß:** SUS (deutsche Fassung), ebenfalls
>    je Durchlauf. Der NASA-TLX wird nicht erhoben.
> 5. **H1 (neu, primär):** Das Vertrauen unterscheidet sich zwischen A und B.
>    **Zweiseitig**, weil vor dem 20.10. keine Richtung dokumentiert wurde; eine jetzt
>    gesetzte Richtung wäre nicht mehr präregistriert. Wilcoxon-Vorzeichen-Rang-Test
>    (gepaart, zweiseitig) auf die TiA-Werte A vs. B, Effektgröße r, 95 %-KI, N = 16.
>    Reihenfolgeeffekt wird mitberichtet (Vergleich der Differenzen AB- vs. BA-Personen).
>    **Sensitivitätsanalyse:** nur der erste Durchlauf je Person als Between-Vergleich
>    (8 vs. 8, Mann-Whitney-U zweiseitig), weil das Sehen der ersten Variante die
>    Bewertung der zweiten beeinflussen kann (Carry-over). Die Studie bleibt
>    hypothesengenerierend. 🟦
> 6. **FF2 (neu): Faktengleichheit A/B** als Manipulationscheck. Je Zustand prüfen zwei
>    Rater verblindet, ob A und B dieselben Aussagen treffen (Messwert, Schwelle,
>    Konsequenz). Ersetzt „Güte der LLM-Ausgaben“; die Rubrik ist entsprechend
>    anzupassen. 🟦
> 7. **H2 (Forced-Choice-Direktvergleich am Sitzungsende):** offen, ob er zusätzlich zu
>    den beiden Durchläufen erhoben wird; vor der Auswertung festzulegen und hier
>    nachzutragen. 🟦
> 8. **Einführungsvideo** zu Beginn jeder Sitzung, für alle Personen identisch.

## Kernfrage

> **Wann vertrauen Nutzer den Erklärtexten mehr?** Erhöht eine **LLM-Erklärung**
> (Gruppe B) gegenüber **statischem Regeltext** (Gruppe A) das **Nutzervertrauen**, und
> ist ein etwaiges Vertrauens-Plus durch die objektive **Güte** der Ausgaben **gedeckt**
> (Kalibrierung) oder Über-Vertrauen?

Der USP: Da der Kern **deterministisch + auditierbar** ist, ist Faithfulness
*messbar* (siehe `study_faithfulness.py`). FF2 ist damit der Riegel gegen „LLM erklärt
nur schöner": ein Vertrauensgewinn ohne Güte-Deckung ist Über-Vertrauen, kein Fortschritt.

## Forschungsfragen und Hypothesen (🟦 zu bestätigen)

- **FF1 (Vertrauen):** Erhöht B gegenüber A das Nutzervertrauen?
- **FF2 (Güte):** Wie ist die objektive Güte der LLM-Ausgaben, und deckt sie ein
  Vertrauens-Plus (Kalibrierung)?

| ID | Hypothese | Richtung |
|---|---|---|
| **H1** (primär, between) | Gruppe B berichtet ein höheres **Vertrauen** (Jian-Summe 12–84) als Gruppe A. | gerichtet, einseitig |
| **H2** (within) | Im Direktvergleich wird B häufiger als vertrauenswürdiger gewählt als per Zufall, und das Vergleichsrating liegt über der neutralen Mitte. | gerichtet |
| **FF2** (deskriptiv) | Faithfulness-Rate und Rubrik-Güte von B (A als treue Referenz); Auswertung als Kalibrierung gegen FF1, keine klassische Nullhypothese. | deskriptiv/objektiv |
| **H0** | Kein Unterschied im Vertrauen zwischen A und B. | Nullhypothese |

## Operationalisierung

- **Primär-AV — Nutzervertrauen (12–84):** Automation Trust Scale (Jian 2000), auf die
  gesehene Variante, **vor** dem Reveal.
- **Within (H2):** je verglichenem Szenario Forced-Choice (A/B) + 7-stufiges
  Vergleichsrating (4 = gleich), nach dem Reveal, über alle N = 16.
- **FF2 — Güte:** objektive Faithfulness (`study_faithfulness.py`) + verblindetes
  2-Rater-Rubrik-Rating (`study_guete.py`) gegen die Gold-Referenz.
- **Optional/Nebenmaße:** SUS, Raw-NASA-TLX; behaviorale Override-/Verhaltensspur.
- **Manipulation:** Gruppe A = `explanation.group_a` (statisch), Gruppe B =
  `explanation.group_b` (ein LLM-Satz, ohne Personas) aus dem **eingefrorenen**
  Studien-Set (`src/sim/study_set/`).

## Rubrik — Güte der Erklärtexte (FF2) (🟦 im Pilot kalibrieren)

3 Dimensionen × 0–2 Punkte (Güte-Summe 0–6) + Halluzinations-Flag (0/1); zwei
verblindete Rater, Interrater-κ (gewichtet). Vollständig in
[Anhang G](../../../../thesis/kapitel/99_anhang/99g_kodierleitfaden_v2.tex):

| Dimension | 0 | 2 |
|---|---|---|
| **Korrektheit / Faithfulness** | widerspricht der Entscheidung / falsch | stimmt mit der deterministischen Entscheidung überein |
| **Vollständigkeit** | weder Auslöser noch Messwert | Auslöser + relevanter Messwert genannt |
| **Klarheit** | unverständlich / Fachjargon | laienverständlich, ein Satz, klare Alltagssprache |

A ist konstruktionsbedingt treu (Template-Interpolation) und dient als Referenz/Decke;
die Rubrik prüft vor allem, ob B diese Güte **hält**.

## Within-Vergleich und behaviorale Spur (Szenario-Auswahl)

Für den Within-Direktvergleich werden 2–3 repräsentative Szenarien gezeigt, darunter
die kontraintuitiven Items **S4** (Sicherheitsstopp) und **S9** (Forecast-Veto). Die
optionale Override-/Verhaltensspur nutzt dieselben Items als objektive Verlässlichkeits-
Triangulation des Selbstberichts (angemessen / Disuse / Misuse je Szenario):

| Szenario | System | Angemessen | Override = |
|---|---|---|---|
| **S4 STOP (Übertemp)** | stoppt | **akzeptieren (Safety)** | **Misuse** (Hauptitem) |
| **S9 NOOP (Forecast)** | wartet | begründet akzeptieren | **Disuse/Misuse** (Hauptitem) |
| S7 STOP (hard) | stoppt | akzeptieren (Batterie) | Misuse |
| S8 STOP (Netzbezug) | stoppt | akzeptieren (kein Netz-Mining) | Misuse |

## Analyseplan (festgeschrieben)

- **Primär (H1, between):** Mann-Whitney-U (einseitig) auf das Vertrauen, A (n=8) vs.
  B (n=8); Welch-/t-Test bei erfüllten Voraussetzungen (Shapiro-Wilk, Levene).
  Implementiert in `src/sim/study_analysis.py`.
- **Within (H2):** Binomial-/Vorzeichentest auf Forced-Choice (B vs. Zufall) und
  Wilcoxon-Vorzeichen-Rang-Test des Vergleichsratings gegen die Mitte 4, über alle N=16.
- **Güte (FF2):** Faithfulness-Raten deskriptiv; Rubrik-Mittelwerte + Interrater-κ
  (`study_guete.py`); Kalibrierungs-Gegenüberstellung Vertrauen × Güte.
- **Immer berichten:** Effektgröße **r** (bzw. Cohen's *d*), **95 %-KI**, **N** —
  **p nie isoliert**.
- **Qualitativ:** thematische Analyse (Braun & Clarke) der offenen Vertrauensbegründungen.
- **Triangulation:** Trust × Within-Vergleich × Güte × Verhaltensspur (Logs).

## Voraussetzungen vor Erhebung

- [x] **Szenario-Set eingefroren** (`study_freeze.py`, 10/10 verifiziert).
- [x] **Faithfulness-Vorprüfung** (Gruppe A 10/10) — Gruppe B nach Ollama-Anbindung.
- [ ] **Gruppe-B-Text generiert + eingefroren** (externer Ollama-Rechner).
- [ ] **Güte-Rubrik im Pilot kalibriert** (2–3 Texte) + Interrater-κ; zweiter Rater.
- [ ] **Trust-Bogen + Within-Vergleichsbogen** im Pilot validiert.
- [ ] **Hypothesen 🟦 + Ethikantrag** final.

## Limitationen (vorab, ehrlich)

- **N = 16** (balanciert 8 vs. 8) → der **between**-Primärtest erkennt nur **große**
  Effekte (d ≈ 0,8). Power hängt vom Verfahren ab: t-Test-Näherung ~45 %, aber das
  primär geplante **Mann-Whitney-U** liegt real bei nur ~40 % (einseitig; nachgerechnet
  11.08.2026 per Monte-Carlo-Simulation, 200.000 Wiederholungen: t-Test 45,1 %,
  Mann-Whitney-U 39,5 % ± 0,2 Prozentpunkte). Für 80 % Power wären n=20/Gruppe (N=40)
  nötig. Der **within**-Vergleich (gepaart, N=16) trägt mehr Power und beantwortet die
  Leitfrage direkter. Studie **hypothesen-generierend**, Triangulation > p-Wert.
- **Within-Reveal:** weil jede Person beide Varianten sieht, drohen Reihenfolge-/Demand-
  Effekte → Permutation der Reihenfolge, Trennung primär (vor Reveal)/within (nach Reveal),
  verblindete Auswertung.
- **Asymmetrische Güte:** A ist konstruktionsbedingt treu; FF2 prüft vor allem, ob B die
  Treue hält, nicht ob B treuer ist als A.
- **Saison-Bias:** Szenarien aus Spätfrühlings-Daten; Häufigkeiten sommer-spezifisch.
- **Faithfulness automatisch nur Vorstufe** — das manuelle Rubrik-Rating bleibt nötig.

---

> **Nächster Schritt:** Zurück zu **[20.2.4 - SD-CONTEXT](./README.md)**
>
> Zurück zur **[Hauptübersicht](../../../../README.md)**
