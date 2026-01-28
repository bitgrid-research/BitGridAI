# 24.3 – Konsistenz zwischen Logs und UI-Begründung

Dieses Unterkapitel beschreibt, **wie Erklärungen konsistent mit den Systemlogs verknüpft werden**, sodass Entscheidungen sowohl für Nutzer:innen als auch für Analyse und Forschung **nachvollziehbar und überprüfbar** bleiben.

Ziel ist es, sicherzustellen, dass **jede im Interface dargestellte Begründung eindeutig auf geloggte Entscheidungsdaten zurückführbar** ist.

&nbsp;

## Ziel der Konsistenz

Die Konsistenz zwischen Logs und UI verfolgt drei zentrale Ziele:

1. **Nachvollziehbarkeit**
   Jede UI-Erklärung muss in den Logs rekonstruierbar sein.
2. **Widerspruchsfreiheit**
   Logs und UI dürfen keine unterschiedlichen Bedeutungen derselben Entscheidung transportieren.
3. **Wiederverwendbarkeit**
   Dieselben Entscheidungsdaten sollen für UI, Analyse und Evaluation genutzt werden können.

Erklärungen werden damit nicht als UI-Artefakt verstanden, sondern als **Interpretation strukturierter Entscheidungsdaten**.

&nbsp;

## Einheitliche Entscheidungscodes

Jede Systementscheidung wird mit einem **eindeutigen Entscheidungscode** versehen.

### Entscheidungsdimensionen

Ein Entscheidungscode setzt sich konzeptionell aus folgenden Bestandteilen zusammen:

* **Entscheidungstyp**
  (`START`, `STOP`, `THROTTLE`, `NOOP`)
* **Primäre Regelursache**
  (z. B. `R2_HARD`, `R4_BLOCKED`, `R5_ACTIVE`)
* **Sekundäre Kontextregeln**
  (optional, z. B. zusätzliche aktive Regeln)

Diese Codes bilden die **Single Source of Truth** für alle weiteren Darstellungen.

&nbsp;

## Nachvollziehbare Begründungsdaten

Neben dem Entscheidungscode werden **strukturierte Begründungsdaten** geloggt.

### Zentrale Log-Bestandteile

Ein Entscheidungslog enthält mindestens:

* Zeitstempel und Blockreferenz,
* aktuellen Systemzustand,
* Entscheidungstyp,
* Regelzustände (R1–R5),
* relevante Zustandswerte (selektiv),
* Hinweis auf Override-Ereignisse (falls vorhanden).

Diese Daten bilden die **vollständige Grundlage** für jede Erklärung.

&nbsp;

## Ableitung der UI-Begründung aus Logs

Die UI generiert ihre Begründungen **nicht frei**, sondern leitet sie aus den Log-Daten ab:

1. Auswahl des Entscheidungscodes,
2. Zuordnung der passenden Textbausteine (vgl. Kapitel 24.2),
3. Kontextuelle Kürzung oder Gewichtung je nach Interface.

Dabei gilt:

* Die **Bedeutung** der Erklärung bleibt identisch.
* Nur die **Darstellungstiefe** variiert.

&nbsp;

## Abgleich zwischen Log und UI

Für jede im UI dargestellte Erklärung gilt:

* Es existiert ein **korrespondierender Logeintrag**.
* Die UI-Erklärung lässt sich vollständig aus diesem Logeintrag rekonstruieren.
* Abweichungen zwischen Log und UI gelten als **Systemfehler**.

### Beispiel

**Log (strukturiert):**

* Entscheidung: `NOOP`
* Regelzustände: `R1=true`, `R2=true`, `R3=true`, `R4=false`, `R5=true`

**UI-Erklärung:**

> "Keine Aktion: Prognose instabil und Ruhezeit aktiv."

Die UI-Erklärung ist eine **komprimierte Projektion** der Log-Daten.

&nbsp;

## Bedeutung für Analyse und Evaluation

Durch die enge Kopplung von Logs und Erklärungen wird ermöglicht:

* quantitative Analyse erklärter Entscheidungen,
* Vergleich von Entscheidungs- und Wahrnehmungsmustern,
* spätere Optimierung ohne Bedeutungsverschiebung.

Logs dienen damit nicht nur der Fehleranalyse, sondern als **semantisches Rückgrat** des Systems.

&nbsp;

## Einordnung

Die Konsistenz zwischen Logs und UI-Begründung stellt sicher, dass das System **nicht nur korrekt entscheidet**, sondern seine Entscheidungen auch **dauerhaft verständlich kommuniziert**.

Damit bildet dieses Unterkapitel den Abschluss des Erklärungsmodells und die Brücke zum folgenden Kapitel über das **Interface Design**.




---

> **Nächster Schritt:** Im nächsten Kapitel folgt das Interface Design.
>
> 👉 Weiter zu **[25 - Interface Design](../../25_interface_design/README.md)**
>
> 🔙 Zurück zu **[24 - Erklärungsmodell](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
