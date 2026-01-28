# 23.2 – Entscheidungsregeln & Auslöser

Dieses Unterkapitel beschreibt die **Entscheidungsregeln und Auslöser**, die das Verhalten des Systems steuern.
Der Fokus liegt auf **klar definierten Schwellenwerten**, **zeitlichen Stabilitätsmechanismen** sowie **Override- und Kontrolllogik**, die gemeinsam ein ruhiges und erklärbares Systemverhalten sicherstellen.

&nbsp;

## Grundprinzip der Entscheidungsfindung

Die Entscheidungslogik folgt einem bewusst **konservativen Ansatz**:

* Entscheidungen werden **diskret und blockbasiert** getroffen (z. B. 10-Minuten-Intervalle).
* Messwerte lösen **keine direkten Aktionen** aus, sondern werden zunächst bewertet.
* Jede Entscheidung ist das Ergebnis einer **Regelkonstellation**, nicht eines einzelnen Triggers.
* Auch das **bewusste Nicht-Handeln (NOOP)** ist ein explizites Entscheidungsergebnis.

Dieses Prinzip dient der Vermeidung von Flapping, unnötigen Schaltvorgängen und schwer erklärbarem Systemverhalten.

&nbsp;

## Regelklassen (R1–R5)

Die Entscheidungsfindung basiert auf einem festen Satz expliziter Regeln, die unterschiedliche Schutz- und Steuerungsfunktionen erfüllen.

### R1 – Startregel (Energie- und Kontextbedingungen)

R1 bewertet, ob ein Start grundsätzlich **energetisch sinnvoll** ist.

Typische Kriterien:

* ausreichender PV-Überschuss über einem definierten Schwellenwert,
* optional günstige externe Rahmenbedingungen (z. B. Preis, Tageszeit).

R1 allein führt **nicht** zu einem Start, sondern definiert lediglich die *grundsätzliche Erlaubnis*.

&nbsp;

### R2 – Speicher- und Autarkieschutz

R2 schützt kritische Systemressourcen, insbesondere den Energiespeicher.

Charakteristika:

* Definition eines **harten Mindest-SoC**, unterhalb dessen ein Stop erzwungen wird,
* Definition eines **weichen SoC-Bereichs**, in dem keine neuen Starts erlaubt sind,
* klare Wiederfreigabeschwellen zur Vermeidung von Grenzflattern.

R2 kann sowohl Startentscheidungen blockieren als auch Stop-Entscheidungen auslösen.

&nbsp;

### R3 – Sicherheits- und Override-Regel

R3 dient dem unmittelbaren Schutz von Hardware und System.

Eigenschaften:

* reagiert auf sicherheitskritische Zustände (z. B. Temperatur, Health),
* kann Entscheidungen **asymmetrisch übersteuern**, unabhängig vom Blockrhythmus,
* erzwingt gegebenenfalls Stop oder Drosselung.

R3 hat stets **Vorrang** vor allen anderen Regeln.

&nbsp;

### R4 – Prognose- und Stabilitätsbewertung

R4 bewertet die **Zuverlässigkeit der Datenlage** für einen geplanten Start.

Typische Aspekte:

* Stabilität der PV-Erzeugung,
* Konsistenz von Wetter- oder Strahlungsinformationen,
* Vermeidung von Starts bei erkennbar instabilen Rahmenbedingungen.

R4 fungiert als **Start-Gate**, nicht als eigenständiger Auslöser.

&nbsp;

### R5 – Deadband und Anti-Flapping

R5 stellt sicher, dass Entscheidungen **zeitlich stabil** bleiben.

Zentrale Mechanismen:

* Mindestlaufzeiten nach einem Start,
* Mindestpausen nach einem Stop,
* Tageslimits für Start- und Stop-Vorgänge.

R5 priorisiert **Systemruhe und Vorhersehbarkeit** gegenüber kurzfristiger Optimierung.

&nbsp;

## Schwellenwerte und Stabilitätsfenster

Die Regeln arbeiten mit **klar definierten Schwellenwerten**, die häufig gestaffelt sind:

* **weiche Schwellen** (z. B. Start blockieren),
* **harte Schwellen** (z. B. Stop erzwingen).

Zusätzlich werden **zeitliche Stabilitätsfenster** genutzt, um kurzfristige Messwertschwankungen auszublenden.
Erst wenn Bedingungen über mehrere Zeitintervalle konsistent erfüllt sind, wird eine Entscheidung zugelassen.

&nbsp;

## Zeitliche Bedingungen und Ruhezeiten

Zeit ist ein zentrales Steuerungselement der Entscheidungslogik:

* Entscheidungen erfolgen nur zu **festen Zeitpunkten** (Blocklogik).
* Nach Schaltvorgängen greifen **Ruhezeiten**, in denen keine neue Entscheidung möglich ist.
* Tagesbasierte Limits begrenzen die maximale Anzahl von Zustandswechseln.

Diese zeitlichen Bedingungen sorgen dafür, dass das System auch bei volatilen Eingangsgrößen ruhig bleibt.

&nbsp;

## Override- und Kontrolllogik

Neben der regulären Entscheidungslogik existieren explizite **Override-Mechanismen**:

* Sicherheits-Overrides (R3) haben stets Priorität.
* Manuelle Eingriffe sind möglich, werden jedoch:

  * als Sonderzustand modelliert,
  * zeitlich begrenzt,
  * klar vom Automatikbetrieb abgegrenzt.

Jeder Override wird explizit geloggt und erklärt, um die Nachvollziehbarkeit des Systemverhaltens zu erhalten.

&nbsp;

## Zusammenfassung

Die Entscheidungsregeln und Auslöser sind so gestaltet, dass sie:

* stabile und vorhersehbare Entscheidungen ermöglichen,
* Sicherheits- und Schutzanforderungen priorisieren,
* bewusstes Nicht-Handeln als legitime Entscheidung behandeln,
* und eine spätere Analyse und Optimierung erlauben, ohne die Logik zu verändern.

Auf dieser Grundlage kann das Systemverhalten klar von seiner technischen Umsetzung abgegrenzt werden.



---

> **Nächster Schritt:** Im nächsten Unterkapitel folgt die Abgrenzung zur Architektur.
>
> 👉 Weiter zu **[23.3 - Abgrenzung zur Architektur](../233_architecture_boundary/README.md)**
>
> 🔙 Zurück zu **[23 - Systemmodell & Entscheidungslogik](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
