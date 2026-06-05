# 20.2.4.5 - SD-WQ5 - Erkenntnisziele, Hypothesen & Pre-Registration

Festschreibung **vor** der Datenerhebung (gegen HARKing). Was die Studie
beantworten soll, wie gemessen wird und was eine Hypothese *falsifizieren* würde.
Ergänzt [2024a](./2024a_study_design_sampling.md)–[2024c](./2024c_ethics_privacy_analysis.md)
und das Szenario-Set [2024d](./2024d_scenarios/README.md).

> **Markierung:** 🟦 = mit Betreuer final bestätigen (Studien-Design-Entscheidung).

## Kernfrage

> Verbessert **persona-adaptive LLM-Erklärung** (Gruppe B) gegenüber **statischem
> Regeltext** (Gruppe A) das **Regelverständnis** *und* die **angemessene
> Override-Reaktion** von Laien — **bei gewahrter Treue** zur deterministischen
> Entscheidung?

Der USP: Da der Kern **deterministisch + auditierbar** ist, ist Faithfulness
*messbar* (siehe `study_faithfulness.py`) — das ist der wissenschaftliche Beitrag,
nicht „LLM erklärt schöner".

## Hypothesen (🟦 zu bestätigen)

| ID | Hypothese | Richtung |
|---|---|---|
| **H1** (primär) | Gruppe B erzielt einen höheren **Regelverständnis-Score (0–12)** als Gruppe A. | gerichtet, einseitig |
| **H2** | Gruppe B zeigt häufiger **angemessene** Override-Reaktionen (S4 akzeptieren, S9 begründet). | gerichtet |
| **H3** (explorativ) | Der Effekt ist bei Novizen größer als bei Vorgebildeten (Persona-Stufen). | explorativ, n=5/Stufe |
| **H0** | Kein Unterschied im Verständnis-Score zwischen A und B. | Nullhypothese |

## Operationalisierung

- **Primär-AV — Regelverständnis-Score (0–12)** nach Rubrik (unten), aus den offenen Fragen, blind doppelt bewertet (Interrater-κ).
- **Sekundär — Override-Angemessenheit:** kategorial (angemessen / Disuse / Misuse) je Override-Aufgabe; Ground-Truth unten.
- **Optional — Vertrauen:** Automation Trust Scale; ggf. SUS / Raw-NASA-TLX.
- **Manipulation:** Gruppe A = `explanation.group_a` (statisch), Gruppe B = `explanation.group_b.<persona>` (LLM) aus dem **eingefrorenen** Studien-Set (`src/sim/study_set/`).

## Rubrik — Regelverständnis-Score (0–12) (🟦 im Pilot kalibrieren)

4 Dimensionen × 0–3 Punkte:

| Dimension | 0 | 3 |
|---|---|---|
| **Regel-Identifikation** (R1–R5) | falsch/keine | korrekte Regel + Bedingung |
| **Prioritätskette** (R3>R2>R4>R5>R1) | kein Verständnis | erklärt, warum Sicherheit/Autarkie vorgeht |
| **Zentralkonzept „Steuern statt Einspeisen"** | nicht erfasst | artikuliert Eigenverbrauch-vor-Einspeisung |
| **Übertragung** (neue Situation) | rät | wendet Regel korrekt an |

## Override-Ground-Truth je Szenario

Definiert, welche Override-Reaktion **angemessen** ist (Voraussetzung für sauberes
Misuse/Disuse-Coding):

| Szenario | System | Angemessen | Override = |
|---|---|---|---|
| S1 START | mint | akzeptieren | unnötig |
| S2 NOOP (kein Überschuss) | wartet | akzeptieren | Misuse (kein Überschuss) |
| S3 NOOP (Preis) 🟦 | wartet | nuanciert (Nutzerpräferenz) | offen |
| **S4 STOP (Übertemp)** | stoppt | **akzeptieren (Safety)** | **Misuse** (Hauptitem) |
| S5 STOP (Comm) | stoppt | akzeptieren (Safety) | Misuse |
| S6 NOOP (soft) | wartet | akzeptieren | mildes Misuse (Reserve) |
| S7 STOP (hard) | stoppt | akzeptieren (Batterie) | Misuse |
| S8 STOP (Netzbezug) | stoppt | akzeptieren (kein Netz-Mining) | Misuse |
| **S9 NOOP (Forecast)** | wartet | begründet akzeptieren | **Disuse/Misuse** (Hauptitem) |
| S10 NOOP (Deadband) | hält | akzeptieren | mildes Misuse (Flapping) |

## Analyseplan (festgeschrieben)

- **Test:** Mann-Whitney-U (einseitig) auf den Verständnis-Score, A (n=5) vs. gepoolt B (n=15); Welch-/t-Test bei erfüllten Voraussetzungen (Shapiro-Wilk, Levene). Implementiert in `src/sim/study_analysis.py`.
- **Immer berichten:** Effektgröße **r** (bzw. Cohen's *d*), **95 %-KI**, **N** — **p nie isoliert**.
- **Persona-Stufen:** rein explorativ/deskriptiv (n=5/Zelle).
- **Qualitativ:** thematische Analyse (Braun & Clarke) der offenen Antworten + Override-Begründungen.
- **Triangulation:** Score × Themen × Verhaltensspur (Logs).

## Voraussetzungen vor Erhebung

- [x] **Szenario-Set eingefroren** (`study_freeze.py`, 10/10 verifiziert).
- [x] **Faithfulness-Vorprüfung** (Gruppe A 10/10) — Gruppe B nach Ollama-Anbindung.
- [ ] **Gruppe-B-Texte generiert + eingefroren** (externer Ollama-Rechner).
- [ ] **Rubrik im Pilot kalibriert** (2–3 Durchläufe) + Interrater-κ.
- [ ] **Hypothesen 🟦 + Ethikantrag** final.

## Limitationen (vorab, ehrlich)

- **N = 20** → nur **große** Effekte detektierbar (d ≈ 0,8 → Power ~55 %). Studie **hypothesen-generierend**, Triangulation > p-Wert.
- **Saison-Bias:** Szenarien aus Spätfrühlings-Daten; Häufigkeiten sommer-spezifisch.
- **Kern-Angleichung (offen):** Das **Energielabor** bildet den Realbetrieb (2× Avalon Q) **maßstabsgetreu** nach — gleiches SoC-Band-Schema, gleiche Modi (Eco/Std/Super), nur **leistungsskaliert** auf die kleinen Miner (Bitaxe/NerdQaxe); die SoC-Schwellen (50/58/80/90 %) sind **identisch**. Offen bleibt allein die Angleichung des **deterministischen Kerns** (`RuleEngineConfig`, kW-Überschuss-Logik R1; R4/R5 nicht im HA-Template) an dieses Schema → spätere Arbeit (ADR 020). Werte-Gegenüberstellung: [2024d](./2024d_scenarios/README.md).
- **Faithfulness automatisch nur Vorstufe** — manuelle Bewertung bleibt nötig.

---

> **Nächster Schritt:** Zurück zu **[20.2.4 - SD-CONTEXT](./README.md)**
>
> Zurück zur **[Hauptübersicht](../../../../README.md)**
