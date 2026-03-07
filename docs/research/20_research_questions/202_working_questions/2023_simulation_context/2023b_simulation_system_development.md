# Arbeitsprotokoll Hiwi Backend - Simulations- und Systementwicklung

## Rolle und Ziel

Dieses Dokument protokolliert die technische Arbeit im Backend fuer den lokalen Energielabor-Demonstrator von BitGridAI.

- Rolle: Backend, Simulations- und Systementwicklung
- Fokus: Home Assistant, lokale Systemarchitektur, Regel-Engine, Logging, KPI-Tracking
- Zielbild: lokal laufendes, transparentes und reproduzierbares Steuerungssystem fuer erklaerbare Energieautomation im Energielabor
- Gesamtziel im Projekt: belastbare technische Basis fuer Studienbetrieb und Demonstrationsbetrieb

&nbsp;

## Arbeitspakete Backend (AP B1-B6)

### AP B1 - Systemarchitektur und Infrastrukturaufbau (Monat 1)

Ziel ist der stabile Aufbau des Laborprototyps als lokale Laufzeitumgebung.

- Einrichtung der containerisierten Dienste fuer Datenerfassung, Steuerlogik, Modellinferenz und Logging
- Technische Grundkonfiguration der lokalen Sensor- und Aktorpfade (PV, Last, SOC, Temperatur, Preis, Miner)
- Abbildung zentraler Home-Assistant-Entities und Services als Integrationsbasis

Artefakte:

- Infrastruktur-Setup-Doku
- Architekturuebersicht (Dienste, Datenfluesse, Schnittstellen)
- Erstes lauffaehiges Basissystem

&nbsp;

### AP B2 - Datenmodell und Single Source of Truth (Monat 1-2)

Ziel ist ein einheitliches Energiedatenmodell fuer alle Entscheidungen und Auswertungen.

- Definition strukturierter Zustaende fuer PV, Last, Ueberschuss, SOC, Temperatur, Preis und Forecast
- Modellierung von Entscheidungsobjekten (Rule-ID, Aktion, Parameter, Reason)
- Aufbau eines Datenwoerterbuchs fuer Nachvollziehbarkeit und spaetere Analyse

Artefakte:

- Versioniertes Datenmodell
- Datenwoerterbuch mit Felddefinitionen
- Referenzbeispiele fuer gueltige Entscheidungsereignisse

&nbsp;

### AP B3 - Implementierung der Regel-Engine R1-R5 (Monat 2)

Ziel ist eine deterministische und pruefbare Laststeuerung.

- Umsetzung der Regeln R1-R5 mit klarer Priorisierung und Override-Logik
- Block-synchrone Verarbeitung von Entscheidungen als Events
- Dokumentation von Entscheidungspfaden inklusive Triggern und Schwellwerten

Artefakte:

- Regel-Engine-Spezifikation
- Testfaelle fuer Grenz- und Konfliktsituationen
- Entscheidungsprotokolle pro Regelzustand

&nbsp;

### AP B4 - Integration lokales Sprachmodell fuer Explainability (Monat 2-3)

Ziel ist die Generierung kurzer, konsistenter Erklaerungstexte auf Basis deterministischer Entscheidungen.

- Anbindung eines lokal ausgefuehrten LLM als Explanation Builder
- Uebergabe standardisierter Rule-Engine-Inputs an die Erklaerungsschicht
- Definition eines robusten Prompt- und Antwortformats fuer reproduzierbare Ausgabe

Artefakte:

- Schnittstellendoku Rule-Engine <-> Explainability-Layer
- Prompt-Template und Ausgabeformat
- Validierte Beispielerklaerungen fuer Kernszenarien

&nbsp;

### AP B5 - Logging, KPI-Erfassung und Versuchsdatengenerierung (Monat 3-4)

Ziel ist die systematische Datenerfassung fuer technische Validierung und empirische Auswertung.

- Aufbau eines Event-Loggings fuer Entscheidungen, Zustandsaenderungen und Interaktionen
- Erhebung zentraler KPIs (Entscheidungsanzahl, Start/Stop-Verhaeltnis, Temperatur-Events, Energieverbrauch, Autonomie-Level)
- Strukturierte Ablage fuer Analyse- und Studienzwecke

Artefakte:

- Logging-Schema und KPI-Definitionen
- Exportfaehige Datensaetze fuer Studienauswertung
- Monitoring-Ansichten fuer Laborbetrieb

&nbsp;

### AP B6 - Laborbetrieb, technische Validierung und Datenauswertung (Monat 4-6)

Ziel ist der stabile Betrieb im Energielabor inkl. Fehleranalyse und Iteration.

- Technische Begleitung von Demonstrationen und Studienbetrieb
- Analyse von Fehlerfaellen, Instabilitaeten und Regelausnahmezustaenden
- Iterative Absicherung der Szenarien auf Basis von Logs und Beobachtungen

Artefakte:

- Validierungsprotokolle
- Fehler- und Verbesserungslog
- Zusammenfassung technischer Lessons Learned fuer Transfer und Folgevorhaben


