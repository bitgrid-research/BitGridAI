# 26.1 – Szenarien im Smart-Home-Kontext

Dieses Unterkapitel beschreibt **typische Smart-Home-Situationen**, die für die Validierung von Systemverhalten, Erklärungsmodell und Interface-Design relevant sind.
Die Szenarien orientieren sich an **alltäglichen Nutzungsmustern** und bilden die Grundlage für Tests, Evaluation und Vergleichbarkeit.

Der Fokus liegt auf **Start- und Stop-Entscheidungen**, dem bewussten **Nicht-Handeln** sowie auf **manuellen Eingriffen im Alltag**.

&nbsp;

## Szenario SH-1 – PV-Überschuss und Startentscheidungen

**Beschreibung**
Ein Haushalt mit Photovoltaikanlage erzeugt über mehrere Stunden hinweg einen stabilen Energieüberschuss.

**Rahmenbedingungen**

* PV-Erzeugung konstant über definierter Schwelle
* Speicher-SoC im sicheren Bereich
* Keine aktiven Sicherheits- oder Ruhezeiten

**Erwartetes Systemverhalten**

* Start einer flexiblen Last ausschließlich zum Entscheidungszeitpunkt (Blocklogik)
* Keine Starts bei kurzfristigen Überschuss-Spitzen
* Zusammenhängende Laufphase ohne unnötige Unterbrechungen

**Relevante Aspekte für Evaluation**

* Verständlichkeit der Startbegründung
* Wahrgenommene Systemruhe
* Einhaltung zeitlicher Bedingungen (Mindestlaufzeit)

&nbsp;

## Szenario SH-2 – Wechselhafter Überschuss und bewusstes Nicht-Handeln

**Beschreibung**
Die PV-Erzeugung schwankt stark durch wechselnde Bewölkung.

**Rahmenbedingungen**

* Kurzzeitige Überschüsse unterbrochen von Einbrüchen
* Prognose- oder Stabilitätsregeln greifen

**Erwartetes Systemverhalten**

* Kein häufiger Start/Stop
* Explizite NOOP-Entscheidungen trotz temporär erfüllter Startbedingungen
* Priorisierung von Stabilität gegenüber kurzfristiger Nutzung

**Relevante Aspekte für Evaluation**

* Erklärung von Nicht-Handeln im Dashboard
* Vermeidung von Flapping
* Nutzervertrauen trotz sichtbarer Energieverfügbarkeit

&nbsp;

## Szenario SH-3 – Haus-Reserve und Stop-Entscheidungen

**Beschreibung**
Der Ladezustand des Energiespeichers nähert sich einer definierten Untergrenze.

**Rahmenbedingungen**

* Sinkender Speicher-SoC
* Aktive oder bevorstehende Schutzschwellen

**Erwartetes Systemverhalten**

* Blockieren neuer Starts
* Ggf. kontrollierter Stop einer laufenden Last
* Klare Priorisierung der Speicherreserve

**Relevante Aspekte für Evaluation**

* Verständlichkeit von Stop-Entscheidungen
* Akzeptanz von Schutzmechanismen
* Konsistenz zwischen Log und UI-Erklärung

&nbsp;

## Szenario SH-4 – Manuelle Overrides im Alltag

**Beschreibung**
Nutzer:innen greifen manuell in das System ein, z. B. durch einen expliziten Start- oder Stop-Befehl.

**Rahmenbedingungen**

* Override wird außerhalb des regulären Entscheidungszeitpunkts ausgelöst
* Automatik ist grundsätzlich aktiv

**Erwartetes Systemverhalten**

* Manuelle Aktion wird als Sonderzustand behandelt
* Automatiklogik bleibt grundsätzlich erhalten
* Rückkehr in den automatischen Betrieb wird klar kommuniziert

**Relevante Aspekte für Evaluation**

* Transparenz des Override-Zustands
* Vermeidung von Kontrollillusionen
* Dokumentation und Erklärung des Eingriffs

&nbsp;

## Zusammenfassung

Die Smart-Home-Szenarien decken die **häufigsten und relevantesten Alltagssituationen** ab, in denen Systementscheidungen für Nutzer:innen erklärbar sein müssen.

Sie dienen als Grundlage für:

* Interface-Validierung,
* Ableitung von Use Cases,
* und die Definition von Evaluationskriterien im nächsten Kapitel.



---

> **Nächster Schritt:** Im nächsten Unterkapitel folgen die Automotive-Szenarien.
>
> 👉 Weiter zu **[26.2 - Szenarien im Automotive-Kontext](../262_automotive_scenarios/README.md)**
>
> 🔙 Zurück zu **[26 - Szenarien & Use Cases](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
