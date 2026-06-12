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
[Anhang G](../../../../thesis/kapitel/99_anhang/99g_kodierleitfaden_v1.tex):

| Dimension | 0 | 2 |
|---|---|---|
| **Korrektheit / Faithfulness** | widerspricht der Entscheidung / falsch | stimmt mit der deterministischen Entscheidung überein |
| **Vollständigkeit** | weder Auslöser noch Messwert | Auslöser + relevanter Messwert genannt |
| **Klarheit** | unverständlich / Fachjargon | laienverständlich, ein Satz, klare Alltagssprache |

A ist konstruktionsbedingt treu (Template-Interpolation) und dient als Referenz/Decke;
die Rubrik prüft vor allem, ob B diese Güte **hält**.

## Within-Vergleich und behaviorale Spur (Szenario-Auswahl)

Für den Within-Direktvergleich werden 3–4 repräsentative Szenarien gezeigt, darunter
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
  Effekte (d ≈ 0,8 → Power ~45 %, einseitig). Der **within**-Vergleich (gepaart, N=16)
  trägt mehr Power und beantwortet die Leitfrage direkter. Studie **hypothesen-generierend**,
  Triangulation > p-Wert.
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
