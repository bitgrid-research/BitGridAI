# 24 – Erklärungsmodell

Dieses Kapitel beschreibt das **Erklärungsmodell** des Systems. Es definiert, **wie Entscheidungen erklärt werden**, aus welchen **Bestandteilen** sich eine Erklärung zusammensetzt und wie diese **systematisch aus der Entscheidungslogik** (Kapitel 23) abgeleitet wird.

Der Fokus liegt nicht auf der Darstellung einzelner UI-Elemente, sondern auf einem **konzeptionellen Modell**, das sicherstellt, dass Erklärungen:

* konsistent,
* nachvollziehbar,
* und über verschiedene Interfaces hinweg wiederverwendbar sind.

&nbsp;


## Ziel des Erklärungsmodells

Das Erklärungsmodell verfolgt drei zentrale Ziele:

1. **Transparenz von Entscheidungen**
   Nutzer sollen verstehen können, *warum* das System gehandelt oder bewusst nicht gehandelt hat.
2. **Konsistenz über Systemgrenzen hinweg**
   Dieselbe Entscheidung soll in Logs, UI und Analyse gleich begründet werden.
3. **Reduktion kognitiver Belastung**
   Erklärungen sollen kurz, strukturiert und situationsangemessen sein.

Das Modell versteht Erklärungen als **systematische Ableitung aus Regeln und Zuständen**, nicht als nachträgliche Rechtfertigung.

&nbsp;

## Erklärung als strukturierte Bausteine

Jede Erklärung wird als Kombination klar definierter **Bausteine** verstanden. Diese Bausteine sind unabhängig vom Interface und können je nach Kontext unterschiedlich dargestellt werden.

## Baustein 1 – Auslöser

Der Auslöser beschreibt, **welche Bedingung oder Regelkonstellation** zu einer Entscheidung geführt hat.

Beispiele:

* Erreichen oder Unterschreiten eines Schwellenwerts,
* Ablauf eines Zeitfensters,
* Sicherheitsereignis.

Der Auslöser beantwortet die Frage:

> *Was hat diese Entscheidung ausgelöst?*

&nbsp;

## Baustein 2 – Datenbasis

Die Datenbasis benennt die **relevanten Zustandsdaten**, auf die sich die Entscheidung stützt.

Beispiele:

* PV-Überschuss,
* Ladezustand des Speichers,
* Temperatur,
* Prognosezustand.

Die Datenbasis beantwortet die Frage:

> *Worauf stützte sich das System?*

&nbsp;

## Baustein 3 – Wirkung

Die Wirkung beschreibt, **was das System entschieden hat**.

Beispiele:

* Starten,
* Stoppen,
* Drosseln,
* bewusstes Nicht-Handeln (`NOOP`).

Dieser Baustein beantwortet die Frage:

> *Was hat das System getan (oder nicht getan)?*

&nbsp;

## Baustein 4 – Optionen (implizit oder explizit)

Der Options-Baustein beschreibt, **welche Alternativen prinzipiell möglich gewesen wären**, auch wenn sie nicht gewählt wurden.

Beispiele:

* Start wäre ohne Deadband möglich gewesen,
* Weiterbetrieb wäre ohne Sicherheitslimit erlaubt gewesen.

Dieser Baustein beantwortet die Frage:

> *Was hätte das System grundsätzlich auch tun können?*

Optionen müssen nicht immer angezeigt werden, sind aber für Analyse und Vertrauen relevant.

&nbsp;

## Ableitung von Erklärungen aus Entscheidungsregeln

Erklärungen werden **direkt aus der Entscheidungslogik** abgeleitet:

* Jede Entscheidung basiert auf einem Satz von **Regelzuständen** (R1–R5).
* Diese Regelzustände werden in **menschlich verständliche Aussagen** übersetzt.
* Die Übersetzung folgt festen Mustern, keine freien Texte.

### Beispielhafte Ableitung

Regelzustände:

* R1: erfüllt
* R2: erfüllt
* R3: erfüllt
* R4: blockiert
* R5: erfüllt

Abgeleitete Erklärung:

> „Kein Start: Prognose instabil, obwohl Energie- und Speicherbedingungen erfüllt sind.“

Damit bleibt die Erklärung:

* regelbasiert,
* überprüfbar,
* konsistent über alle Systemebenen.

&nbsp;

## Erklärung von Nicht-Handeln (NOOP)

Ein zentrales Element des Erklärungsmodells ist die explizite Erklärung von **bewusstem Nicht-Handeln**.

Annahmen:

* Nicht-Handeln ist eine **aktive Entscheidung**, kein Systemfehler.
* Gerade in ruhigen Systemen ist NOOP der häufigste Entscheidungsfall.

Beispiele:

* „Keine Aktion: Mindestpause noch aktiv.“
* „Keine Aktion: Sicherheitsreserve wird gehalten.“

Die Erklärung von NOOP ist entscheidend für:

* Vertrauen,
* mentale Modelle,
* spätere Optimierung und Analyse.

&nbsp;

## Konsistenz zwischen Logs, UI und Analyse

Das Erklärungsmodell fordert eine **einheitliche semantische Grundlage** für alle Erklärungen:

* Logs enthalten strukturierte Regelzustände und Entscheidungen.
* UI-Texte werden aus denselben Bausteinen generiert.
* Analyse- und Evaluationsschritte greifen auf identische Bedeutungen zurück.

Unterschiede bestehen ausschließlich in:

* Detailtiefe,
* Darstellung,
* zeitlicher Perspektive.

Damit wird verhindert, dass UI-Erklärungen und Systemlogs widersprüchliche Aussagen machen.

&nbsp;

## Einordnung

Das Erklärungsmodell bildet die **Brücke zwischen Systemlogik und Nutzerwahrnehmung**.
Es stellt sicher, dass Entscheidungen nicht nur korrekt, sondern auch **kommunizierbar und überprüfbar** sind.

Auf dieser Basis kann im nächsten Kapitel beschrieben werden, **wie diese Erklärungen konkret im Interface dargestellt werden**.




---

> **Nächster Schritt:** Das Erklärungsmodell steht.
> Im nächsten Kapitel folgt das Interface Design.
>
> 👉 Weiter zu **[25 - Interface Design](../25_interface_design/README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
