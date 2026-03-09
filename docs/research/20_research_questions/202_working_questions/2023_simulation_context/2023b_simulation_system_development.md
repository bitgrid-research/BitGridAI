# Simulations- und Systementwicklung

## Rolle und Ziel

Dieses Dokument protokolliert die technische Arbeit im Backend für den lokalen Energielabor-Demonstrator von BitGridAI.

- Rolle: Backend, Simulations- und Systementwicklung
- Fokus: Home Assistant, lokale Systemarchitektur, Regel-Engine, Logging, KPI-Tracking
- Zielbild: lokal laufendes, transparentes und reproduzierbares Steuerungssystem für erklärbare Energieautomation im Energielabor
- Gesamtziel im Projekt: belastbare technische Basis für Studienbetrieb und Demonstrationsbetrieb

&nbsp;


## Arbeitspakete Backend (AP B1-B6)

### AP B1 - Systemarchitektur und Infrastrukturaufbau (Monat 1)

Ziel ist der stabile Aufbau des Laborprototyps als lokale Laufzeitumgebung.

- Einrichtung der containerisierten Dienste für Datenerfassung, Steuerlogik, Modellinferenz und Logging
- Technische Grundkonfiguration der lokalen Sensor- und Aktorpfade (PV, Last, SOC, Temperatur, Preis, Miner)
- Abbildung zentraler Home-Assistant-Entities und Services als Integrationsbasis

Artefakte:

- Infrastruktur-Setup-Doku
- Architekturübersicht (Dienste, Datenflüsse, Schnittstellen)
- Erstes lauffähiges Basissystem

&nbsp;

### AP B2 - Datenmodell und Single Source of Truth (Monat 1-2)

Ziel ist ein einheitliches Energiedatenmodell für alle Entscheidungen und Auswertungen.

- Definition strukturierter Zustände für PV, Last, Überschuss, SOC, Temperatur, Preis und Forecast
- Modellierung von Entscheidungsobjekten (Rule-ID, Aktion, Parameter, Reason)
- Aufbau eines Datenwörterbuchs für Nachvollziehbarkeit und spätere Analyse

Artefakte:

- Versioniertes Datenmodell
- Datenwörterbuch mit Felddefinitionen
- Referenzbeispiele für gültige Entscheidungsereignisse

&nbsp;

### AP B3 - Implementierung der Regel-Engine R1-R5 (Monat 2)

Ziel ist eine deterministische und prüfbare Laststeuerung.

- Umsetzung der Regeln R1-R5 mit klarer Priorisierung und Override-Logik
- Block-synchrone Verarbeitung von Entscheidungen als Events
- Dokumentation von Entscheidungspfaden inklusive Triggern und Schwellwerten

Artefakte:

- Regel-Engine-Spezifikation
- Testfälle für Grenz- und Konfliktsituationen
- Entscheidungsprotokolle pro Regelzustand

&nbsp;

### AP B4 - Integration lokales Sprachmodell für Explainability (Monat 2-3)

Ziel ist die Generierung kurzer, konsistenter Erklärungstexte auf Basis deterministischer Entscheidungen.

- Anbindung eines lokal ausgeführten LLM als Explanation Builder
- Übergabe standardisierter Rule-Engine-Inputs an die Erklärungsschicht
- Definition eines robusten Prompt- und Antwortformats für reproduzierbare Ausgabe

Artefakte:

- Schnittstellendoku Rule-Engine <-> Explainability-Layer
- Prompt-Template und Ausgabeformat
- Validierte Beispielerklärungen für Kernszenarien

&nbsp;

### AP B5 - Logging, KPI-Erfassung und Versuchsdatengenerierung (Monat 3-4)

Ziel ist die systematische Datenerfassung für technische Validierung und empirische Auswertung.

- Aufbau eines Event-Loggings für Entscheidungen, Zustandsänderungen und Interaktionen
- Erhebung zentraler KPIs (Entscheidungsanzahl, Start/Stop-Verhältnis, Temperatur-Events, Energieverbrauch, Autonomie-Level)
- Strukturierte Ablage für Analyse- und Studienzwecke

Artefakte:

- Logging-Schema und KPI-Definitionen
- Exportfähige Datensätze für Studienauswertung
- Monitoring-Ansichten für Laborbetrieb

&nbsp;

### AP B6 - Laborbetrieb, technische Validierung und Datenauswertung (Monat 4-6)

Ziel ist der stabile Betrieb im Energielabor inkl. Fehleranalyse und Iteration.

- Technische Begleitung von Demonstrationen und Studienbetrieb
- Analyse von Fehlerfällen, Instabilitäten und Regelausnahmezuständen
- Iterative Absicherung der Szenarien auf Basis von Logs und Beobachtungen

Artefakte:

- Validierungsprotokolle
- Fehler- und Verbesserungslog
- Zusammenfassung technischer Lessons Learned für Transfer und Folgevorhaben


