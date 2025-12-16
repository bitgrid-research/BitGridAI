# 8.9 - Build-, Update- & Release-Prinzipien

Keine Überraschungen im Betrieb.

BitGridAI läuft lokal, steuert reale Hardware und trifft autonome Entscheidungen.  
Updates, Builds und Releases dürfen deshalb **niemals implizit oder unkontrolliert** erfolgen.

Dieses Kapitel beschreibt die **übergreifenden Prinzipien für Build, Update und Release** von BitGridAI.  
Ziel ist ein Betriebsmodell, das **vorhersehbar, rückrollbar und überprüfbar** ist – auch auf Edge-Hardware im Heimnetz.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster steht an einem Förderband. Jede Kiste trägt ein Etikett: „Build“, „Test“, „Replay OK“, „Release“. Ein roter Stempel: „Approved“.)*

&nbsp;

## Ziel: Kontrollierte Veränderung

Grundprinzip:
> **Ein Update ist nur dann erlaubt, wenn sein Verhalten vorab bekannt ist.**

Build- und Release-Prozesse müssen sicherstellen, dass:
- neue Versionen reproduzierbar entstehen,
- ihr Verhalten geprüft wurde,
- ein Rückweg jederzeit möglich ist.

&nbsp;

## Leitprinzipien

### 1. Deterministische Builds
- Builds entstehen aus versioniertem Quellcode.
- Abhängigkeiten sind fixiert und reproduzierbar.
- Das gleiche Commit erzeugt das gleiche Artefakt.

&nbsp;

### 2. Trennung von Code & Daten
- Container-Images enthalten **keine** Nutzerdaten.
- Konfiguration, Logs und Zustände liegen in Volumes.
- Updates dürfen keine Daten migrieren oder verändern, ohne explizite Schritte.

&nbsp;

### 3. Replay vor Release
- Jede neue Version wird gegen bekannte Zustände geprüft.
- Replays dienen als Gate vor Freigabe.
- Abweichendes Entscheidungsverhalten muss bewusst akzeptiert oder korrigiert werden.

&nbsp;

### 4. Rückrollbarkeit
- Alte Versionen bleiben verfügbar.
- Datenformate sind abwärtskompatibel oder versioniert.
- Ein Rollback darf keinen manuellen Daten-Eingriff erfordern.

&nbsp;

## Build-Prozess (konzeptionell)

Ein Build durchläuft logisch folgende Schritte:

1. **Source Freeze**  
   Quellcode und Konfiguration sind eindeutig versioniert.

2. **Artefakterstellung**  
   - Container-Images für Core, UI, MQTT
   - klar versioniert (SemVer oder vergleichbar)

3. **Automatisierte Tests**  
   - Unit- und Integrationstests
   - statische Checks

4. **Replay-Validierung**  
   - bekannte Szenarien
   - deterministische Entscheidungsvergleiche

Erst danach gilt ein Build als **releasefähig**.

&nbsp;

## Release-Prinzipien

### Versionierung
- Versionen sind eindeutig und nachvollziehbar.
- Breaking Changes sind explizit gekennzeichnet.
- Konfigurationsversionen sind Teil der Release-Dokumentation.

### Release-Artefakte
Ein Release umfasst:
- Container-Images
- Release-Notes
- Hinweise zu Konfigurationsänderungen
- Replay-Ergebnisse (implizit oder dokumentiert)

&nbsp;

## Update im Betrieb

Updates erfolgen **kontrolliert und bewusst**:

- keine automatischen Silent-Updates
- Updates werden explizit angestoßen
- laufender Betrieb wird sauber beendet oder in Safe-Zustand gebracht

Der Update-Prozess:
1. Stoppen der Dienste (geordnet)
2. Austausch der Images
3. Wiederverwendung bestehender Volumes
4. Neustart
5. Health- und Statusprüfung

&nbsp;

## Umgang mit Konfigurationsänderungen

- Konfigurationsänderungen sind von Code-Releases getrennt.
- Änderungen werden validiert (Schema, Plausibilität).
- Fehlerhafte Konfigurationen führen nicht zu instabilem Betrieb.

Konfigurations-Replays sind vor Produktivübernahme empfohlen.

&nbsp;

## Umbrel & Docker-Compose

Die Release-Prinzipien gelten unabhängig vom Packaging:

- **Docker Compose:**  
  Image-Update + Volumes behalten

- **Umbrel-App:**  
  Gleiches Image, anderes Packaging

Umbrel ist ein **Vertriebsmechanismus**, kein eigenes Release-Modell.

&nbsp;

## Fehlerfälle & Schutzmechanismen

- fehlgeschlagene Updates führen zu:
  - klaren Logs
  - Health-Status `error`
- es gibt keine halb angewendeten Updates
- im Zweifel bleibt die vorherige Version aktiv

&nbsp;

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete CI/CD-Tools
- Build-Skripte
- Registry-Details

Diese gehören in Entwickler- oder Betriebsdokumentation.

&nbsp;

## Zusammenfassung

Die Build-, Update- und Release-Prinzipien stellen sicher, dass BitGridAI:

- sich kontrolliert weiterentwickelt,
- jederzeit rückrollbar bleibt,
- keine Überraschungen im Betrieb verursacht.

BitGridAI verändert sich nicht heimlich –  
jede Änderung ist **bewusst, geprüft und erklärbar**.

---

> **Nächster Schritt:**  
> Architektur lebt von Entscheidungen.  
> Im nächsten Kapitel dokumentieren wir die **zentralen Architektur- und Designentscheidungen**.
>
> 👉 Weiter zu **[09 Architektur- & Designentscheidungen](../09_design_decisions/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
