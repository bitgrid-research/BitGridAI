# 26 – Szenarien & Use Cases

Dieses Kapitel beschreibt **typische Nutzungsszenarien und Use Cases**, die das entwickelte System adressiert.
Die Szenarien dienen nicht als vollständige Abbildung realer Haushalte oder Fahrzeugsysteme, sondern als **repräsentative Situationen**, anhand derer sich Systemverhalten, Erklärbarkeit und Interface-Gestaltung prüfen lassen.

Sie bilden die Grundlage für die **Validierung der Interfaces** (Kapitel 25) sowie für die **Evaluation des Gesamtsystems** (Kapitel 27).

&nbsp;

## Ziel der Szenarien

Die beschriebenen Szenarien verfolgen drei Ziele:

1. **Veranschaulichung des Systemverhaltens**
   Abstrakte Regeln und Zustände werden in konkrete Alltagssituationen übersetzt.
2. **Überprüfung der Erklärbarkeit**
   Es wird geprüft, ob Entscheidungen – insbesondere Nicht-Entscheidungen – verständlich kommuniziert werden können.
3. **Ableitung prüfbarer Use Cases**
   Die Szenarien dienen als Basis für Tests, Metriken und Evaluation.

Die Szenarien sind bewusst **typisch statt extrem** gewählt, um den Fokus auf Alltagstauglichkeit zu legen.

&nbsp;

## Szenarien im Smart-Home-Kontext

### Szenario SH-1: Klarer Sonnentag mit stabilem Überschuss

**Beschreibung**
Ein Haushalt mit Photovoltaik-Anlage erlebt einen sonnigen Tag mit konstantem Energieüberschuss.

**Erwartetes Systemverhalten**

* Start einer flexiblen Last nach Erreichen stabiler Bedingungen,
* längere, zusammenhängende Laufphase,
* automatischer Stop bei abnehmendem Überschuss.

**Relevante Aspekte**

* Einhaltung von Mindestlaufzeiten,
* klare Zustandskommunikation im Dashboard,
* nachvollziehbare Erklärung von Start und Stop.

&nbsp;

### Szenario SH-2: Wechselhafte Bewölkung

**Beschreibung**
Die PV-Erzeugung schwankt stark durch wechselnde Bewölkung.

**Erwartetes Systemverhalten**

* kein häufiger Start/Stop,
* bewusstes Nicht-Handeln trotz kurzzeitiger Überschüsse,
* Priorisierung von Systemruhe.

**Relevante Aspekte**

* Erklärung von NOOP-Entscheidungen,
* Wahrnehmung von Stabilität durch Nutzer:innen.

&nbsp;

### Szenario SH-3: Kritischer Ladezustand des Speichers

**Beschreibung**
Der Ladezustand des Speichers nähert sich einer definierten Untergrenze.

**Erwartetes Systemverhalten**

* Blockieren neuer Starts,
* ggf. Stop einer laufenden Last,
* Schutz der Speicherreserve.

**Relevante Aspekte**

* Priorisierung von Sicherheitsregeln,
* verständliche Begründung trotz subjektiv vorhandener Energie.

&nbsp;

## Szenarien im Automotive-Kontext

### Szenario AU-1: Kurzer Blick während der Fahrt

**Beschreibung**
Die Nutzer:in wirft während der Fahrt einen kurzen Blick auf das In-Car-Interface.

**Erwartetes Systemverhalten**

* klare Anzeige des aktuellen Zustands,
* keine Detailinformationen,
* keine Aufforderung zur Interaktion.

**Relevante Aspekte**

* Reduktion kognitiver Last,
* schnelle Erfassbarkeit der Information.

&nbsp;

### Szenario AU-2: Rückblick nach Fahrtende

**Beschreibung**
Nach Abschluss einer Fahrt wird das Systemverhalten rückblickend betrachtet.

**Erwartetes Systemverhalten**

* kurze Erklärung vergangener Entscheidungen,
* Fokus auf wesentliche Ereignisse,
* konsistente Terminologie.

**Relevante Aspekte**

* Nachvollziehbarkeit ohne Echtzeitkontext,
* Konsistenz zwischen Log und UI.

&nbsp;

## Deterministische Studienszenarien (S01–S10)

Die obigen Szenarien sind **illustrativ**. Für Simulation und Evaluation werden sie
zu **zehn deterministischen Szenarien** verdichtet, eingebettet in einen
zusammenhängenden Mining-Tag. Jedes Szenario ist ein 10-Minuten-Block mit vollständig
spezifiziertem `EnergyState`, sodass der Entscheidungskern per **Replay** exakt
reproduzierbar denselben `decision_code` erzeugt — identisch für alle Probanden
(vgl. Kapitel 27).

Die kanonische Spezifikation (Datengrundlage, IST-Belegung aus Realdaten, Methodik)
liegt im Studiendesign-Kontext:
**[20.2.4.4 - Szenarien für Simulation und Studie](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/README.md)**.

| ID | Szenario | Regel | Erwartete Entscheidung | Datei |
|---|---|---|---|---|
| **S1** | Klarer Start | R1 | `START_R1_SURPLUS_OK` | [S01](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S01_klarer_start.md) |
| **S2** | Kein Überschuss | R1 | `NOOP_R1_INSUFFICIENT_SURPLUS` | [S02](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S02_kein_ueberschuss.md) |
| **S3** ⚑ | Sonne, aber Preis hoch | R1 | `NOOP_R1_PRICE_TOO_HIGH` | [S03](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S03_preis_zu_hoch.md) |
| **S4** ⚑ | Übertemperatur | R3 | `STOP_R3_OVERTEMP` | [S04](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S04_uebertemperatur.md) |
| **S5** | Kommunikationsausfall | R3 | `STOP_R3_COMM_TIMEOUT` | [S05](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S05_kommunikationsausfall.md) |
| **S6** ⚑ | Batterie-Schutz (soft) | R2 | `NOOP_R2_SOC_SOFT_MIN` | [S06](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S06_batterie_soft.md) |
| **S7** | Batterie-Notstopp (hard) | R2 | `STOP_R2_SOC_HARD_MIN` | [S07](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S07_batterie_hard.md) |
| **S8** ⚑ | Wolke → Netzbezug | R2 | `STOP_R2_GRID_IMPORT_EXCEEDED` | [S08](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S08_netzbezug.md) |
| **S9** ⚑ | Forecast blockiert | R4 | `NOOP_R4_FORECAST_PV_INSUFFICIENT` | [S09](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S09_forecast.md) |
| **S10** | Anti-Flapping | R5 | `NOOP_R5_MIN_RUNTIME_NOT_REACHED` | [S10](../20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/S10_anti_flapping.md) |

⚑ = diskriminierende Items (kontraintuitiv) — sie trennen die statische von der
persona-adaptiven Erklärung. Die Szenarien decken alle Regeln R1–R5 und die
Prioritätskette R3 > R2 > R4 > R5 > R1 ab.

&nbsp;

## Ableitung von Use Cases

Aus den Szenarien lassen sich konkrete **Use Cases** ableiten, die für Tests und Evaluation genutzt werden.

### Beispielhafte Use Cases

* **UC-1:** Nutzer:in versteht, warum keine Aktion ausgeführt wurde.
* **UC-2:** Nutzer:in erkennt den aktuellen Systemzustand innerhalb weniger Sekunden.
* **UC-3:** System verhindert unnötige Schaltvorgänge bei instabilen Bedingungen.
* **UC-4:** Sicherheitsrelevante Stops werden klar kommuniziert.

Jeder Use Case ist durch:

* beobachtbares Systemverhalten,
* erklärbare Begründungen,
* und messbare Kriterien gekennzeichnet.

&nbsp;

## Einordnung

Die Szenarien und Use Cases bilden die **Brücke zwischen konzeptionellem Modell und Evaluation**.
Sie stellen sicher, dass das System nicht nur formal korrekt, sondern auch **im Alltag verständlich und akzeptabel** ist.

Im nächsten Kapitel wird auf dieser Basis der **Evaluationsrahmen** definiert.


---

> **Nächster Schritt:** Die Szenarien sind beschrieben.
> Im nächsten Kapitel folgt der Evaluationsrahmen.
>
> 👉 Weiter zu **[27 - Evaluationsrahmen](../27_evaluation_framework/README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
