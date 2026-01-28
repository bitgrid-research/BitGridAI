# 23.3 – Abgrenzung zur Architektur

Dieses Unterkapitel grenzt das **konzeptionelle Systemmodell** bewusst von der **technischen Architektur** ab.
Es beschreibt, welche Aspekte *Teil des Modells* sind und welche explizit **nicht** betrachtet werden, um eine klare Trennung zwischen *Denken* und *Implementieren* sicherzustellen.

Technische Details und konkrete Umsetzungen sind ausgelagert und in der
[Architekturübersicht](../../../architecture/README.md) dokumentiert.

&nbsp;

## Ziel der Abgrenzung

Die Abgrenzung verfolgt drei zentrale Ziele:

1. **Modellstabilität**
   Das Systemmodell soll unabhängig von konkreten Technologien, Frameworks oder Plattformen bestehen.
2. **Vergleichbarkeit**
   Entscheidungen und Zustände sollen auch dann vergleichbar bleiben, wenn sich die technische Umsetzung ändert.
3. **Erklärbarkeit**
   Nutzer- und forschungsrelevante Konzepte sollen nicht durch Implementierungsdetails überlagert werden.

&nbsp;

## Bestandteil des Systemmodells

Zum Systemmodell im Sinne dieses Kapitels gehören:

* konzeptionelle **Komponenten** (z. B. Messung, Regelbewertung, Entscheidung, Zustand),
* **Zustandsdefinitionen** und Zustandsübergänge,
* **Entscheidungsregeln** und deren Zusammenspiel (R1–R5),
* zeitliche Konzepte wie **Blocklogik**, Ruhezeiten und Deadbands,
* die Unterscheidung zwischen **Entscheidung**, **Aktion** und **Systemzustand**,
* Anforderungen an **Erklärbarkeit** und Logging auf Modellebene.

Diese Elemente definieren *was* das System tut und *warum* es dies tut.

&nbsp;

## Nicht Bestandteil des Systemmodells

Explizit **nicht** Teil des Systemmodells sind:

* konkrete Softwarearchitekturen oder Modulstrukturen,
* Programmiersprachen, Frameworks oder Laufzeitumgebungen,
* API-Designs, Datenbankschemata oder Message-Broker,
* Hardware-spezifische Details oder Gerätekonfigurationen,
* konkrete UI-Implementierungen oder Designsysteme.

Diese Aspekte beantworten die Frage *wie* das System umgesetzt wird und sind daher bewusst ausgelagert.

&nbsp;

## Verhältnis zur Architekturübersicht

Die Architekturübersicht:

* setzt das hier beschriebene Systemmodell **technisch um**,
* kann sich weiterentwickeln, ohne das Modell zu verändern,
* dient als Referenz für Implementierung, Deployment und Betrieb.

Umgekehrt gilt:

* Änderungen an der Architektur dürfen **nicht implizit** das Systemmodell verändern,
* Modelländerungen müssen **explizit** begründet und dokumentiert werden.

Diese Entkopplung stellt sicher, dass konzeptionelle Aussagen der Arbeit auch bei veränderter technischer Basis gültig bleiben.

&nbsp;

## Einordnung

Durch die klare Trennung von Systemmodell und Architektur wird verhindert, dass:

* Implementierungsdetails als konzeptionelle Notwendigkeiten missverstanden werden,
* technische Einschränkungen die Modelllogik verzerren,
* spätere Optimierungen die Erklärbarkeit unterlaufen.

Das Systemmodell fungiert damit als **stabile Referenzebene** für Forschung, UX-Gestaltung und Evaluation.



---

> **Nächster Schritt:** Im nächsten Kapitel folgt das Erklärungsmodell.
>
> 👉 Weiter zu **[24 - Erklärungsmodell](../../24_explanation_model/README.md)**
>
> 🔙 Zurück zu **[23 - Systemmodell & Entscheidungslogik](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
