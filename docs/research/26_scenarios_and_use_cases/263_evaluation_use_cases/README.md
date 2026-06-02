# 26.3 – Use Cases für Tests & Evaluation

Dieses Unterkapitel beschreibt **konkrete Use Cases**, die im Rahmen der Evaluation systematisch geprüft werden.
Die Use Cases sind direkt aus den Szenarien der Kapitel **26.1 (Smart Home)** und **26.2 (Automotive)** abgeleitet und dienen als **Brücke zwischen Nutzungssituation, Interface und Messkriterien**.

Der Fokus liegt auf **Verständlichkeit, Nachvollziehbarkeit und Vertrauen**, nicht auf maximaler Effizienz oder Optimierung.

&nbsp;

## Ziel der Use Cases

Die Use Cases verfolgen drei Ziele:

1. **Operationalisierung der Szenarien**
   Abstrakte Szenarien werden in überprüfbare Aufgaben übersetzt.
2. **Vergleichbarkeit der Evaluation**
   Alle Teilnehmenden bearbeiten identische Aufgaben.
3. **Messbarkeit des Erklärformat-Effekts**
   Unterschiede zwischen statischem und adaptivem (persona-basiertem) Erklärformat werden sichtbar.

&nbsp;

## Task-basierte Use Cases

### UC-1 – Verständnis einer Startentscheidung

**Aufgabe**
Teilnehmende betrachten das Interface nach einer Startentscheidung.

**Prüffragen**

* Wird verstanden, *warum* das System gestartet hat?
* Können die Hauptgründe benannt werden?

**Beobachtbare Kriterien**

* korrekte verbale Wiedergabe der Begründung,
* Zeit bis zum Verständnis,
* Sicherheit der Aussage.

&nbsp;

### UC-2 – Verständnis von bewusstem Nicht-Handeln (NOOP)

**Aufgabe**
Teilnehmende sehen ein System, das trotz sichtbarem PV-Überschuss keine Aktion ausführt.

**Prüffragen**

* Wird das Nicht-Handeln als Entscheidung erkannt?
* Wird der zugrunde liegende Grund verstanden?

**Beobachtbare Kriterien**

* Fehlannahmen („System defekt“ vs. „bewusste Pause“),
* Vertrauen in das Systemverhalten,
* Nachfragebedarf.

&nbsp;

### UC-3 – Verständnis einer Stop-Entscheidung

**Aufgabe**
Das System stoppt eine laufende Last aufgrund einer Schutzregel.

**Prüffragen**

* Wird der Stop als Schutzmaßnahme interpretiert?
* Wird die Priorisierung nachvollzogen?

**Beobachtbare Kriterien**

* Akzeptanz der Entscheidung,
* wahrgenommene Fairness,
* Klarheit der Erklärung.
* 
&nbsp;

### UC-4 – Manuelle Override-Situation

**Aufgabe**
Teilnehmende lösen einen manuellen Override aus.

**Prüffragen**

* Wird die Abweichung von der Automatik erkannt?
* Wird klar, wann die Automatik wieder greift?

**Beobachtbare Kriterien**

* Verständnis des Sonderzustands,
* Vertrauen nach Rückkehr in den Automatikbetrieb.

&nbsp;

## Offene Verständnisfragen und Override-Aufgabe

Zur qualitativen Erfassung des mentalen Modells werden in der Einzelsitzung offene Fragen gestellt und eine Override-Aufgabe beobachtet.

### Offene Verständnisfragen (primäre Erhebung)

* „Wie funktioniert das System – was tut es und wozu?“
* „Was hattest du erwartet, und was hat dich überrascht?“
* „Erkläre die wichtigsten Regeln, nach denen das System entscheidet.“
* „Warum lässt das System die Last bei Sonnenüberschuss laufen, statt einzuspeisen?“

### Override-Aufgabe (sekundär)

* Beobachtung des Eingriffsverhaltens in einer gescripteten Situation (inklusive einer nicht überschreibbaren R3-Sicherheitsentscheidung).
* Mündliche Begründung des Eingriffs bzw. Nicht-Eingriffs.

&nbsp;

## Vergleich: statisch (Gruppe A) vs. adaptiv (Gruppe B)

Die Use Cases werden in zwei Erklärformaten geprüft — beide zeigen einen Erklärbereich, der Unterschied liegt allein in der Art der Erklärung:

* **Gruppe A – statisch**
  regelbasiert erzeugte, für alle Probanden wortgleiche Erklärtexte (kein Sprachmodell).
* **Gruppe B – adaptiv**
  persona-basierte LLM-Erklärung, an das Vorwissensniveau angepasst, gemäß Kapitel 24.

Verglichen werden u. a.:

* Regelverständnis (primär),
* Angemessenheit manueller Eingriffe (Override),
* optional Vertrauen,
* Log↔UI-Konsistenz.

&nbsp;

## Einordnung

Die Use Cases bilden die **operative Grundlage für den Evaluationsrahmen**.
Sie stellen sicher, dass Explainability nicht abstrakt, sondern **konkret überprüfbar** wird.

Im nächsten Kapitel wird beschrieben, **wie diese Use Cases systematisch ausgewertet werden**.



---

> **Nächster Schritt:** Im nächsten Kapitel folgt der Evaluationsrahmen.
>
> 👉 Weiter zu **[27 - Evaluationsrahmen](../../27_evaluation_framework/README.md)**
>
> 🔙 Zurück zu **[26 - Szenarien & Use Cases](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
