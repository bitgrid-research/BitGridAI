# 8.6 - Fail-Safe, Degradation & Robustheit

Lieber sicher stehen als falsch laufen.

BitGridAI steuert reale Energieflüsse und Hardware.  
Fehler, Ausfälle oder unvollständige Informationen sind daher **kein Ausnahmefall**, sondern ein fester Bestandteil der Realität.

Dieses Kapitel beschreibt, wie BitGridAI mit **Unsicherheit, Teil- und Totalausfällen** umgeht – und warum das System im Zweifel **immer konservativ und sicher** handelt.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster zieht im Maschinenraum einen großen roten Hebel mit der Aufschrift „SAFE MODE“. Einige Anzeigen sind grau, aber alles ist ruhig.)*
![Hamster im Safe Mode](../../media/pixel_art_hamster_safe_mode.png)

&nbsp;

## Ziel: Definiertes Verhalten statt Chaos

Grundprinzip:
> **Ein System ohne Daten oder Kontrolle darf keine riskanten Entscheidungen treffen.**

Fail-Safe bedeutet bei BitGridAI nicht „Absturz“, sondern:
- klar definierte Zustände,
- beobachtbare Degradation,
- vorhersehbares Verhalten.

&nbsp;

## Sicherheits-Hierarchie

BitGridAI folgt einer festen Prioritätenordnung:

1. **R3 – Safety (immer führend)**  
   Schutz von Hardware, Netz und Infrastruktur.

2. **Systemintegrität**  
   Konsistenter Zustand, keine Seiteneffekte bei Fehlern.

3. **Autarkie & Stabilität**  
   Akku- und Netzschutz (R2, R5).

4. **Optimierung**  
   Profitabilität und Forecasts (R1, R4).

Optimierung ist jederzeit verzichtbar – Sicherheit nicht.

&nbsp;

## Fail-Safe-Auslöser (Beispiele)

Ein Fail-Safe-Zustand wird ausgelöst bei:

- Übertemperatur oder Hardware-Grenzwerten
- fehlenden Pflichtsignalen (Sensoren, Telemetrie)
- Adapter- oder Kommunikationsausfällen
- inkonsistenter oder ungültiger Konfiguration
- internen Fehlern im Core
- expliziten Shutdown-Signalen (z.B. USV)

Diese Auslöser sind **explizit modelliert**, nicht implizit.

&nbsp;

## Degradation statt Blackout

BitGridAI unterscheidet zwischen:

### Normalbetrieb
- alle Pflichtsignale verfügbar
- alle Regeln aktiv
- Optimierung erlaubt

### Degradierter Betrieb
- einzelne Signale oder Komponenten fehlen
- `EnergyState.degraded = true`
- Optimierungsregeln treten zurück
- konservative Entscheidungen

### Fail-Safe / Safe Mode
- Sicherheitsgrenzen verletzt oder unklar
- Mining / flexible Last **aus**
- Zustand bleibt stabil, keine Eskalation

&nbsp;

## Verhalten im Degradationsfall

Bei Degradation gilt:

- **keine Schätzung fehlender Daten**
- **keine stillen Annahmen**
- **keine Optimierung auf unsicherer Basis**

Konkret:
- R1 (Profit) und R4 (Forecast) werden ausgesetzt
- R5 (Stabilität) wird defensiv angewendet
- R3 (Safety) bleibt aktiv

&nbsp;

## Determinismus im Fehlerfall

Auch im Fehlerfall bleibt BitGridAI deterministisch:

- gleiche Eingangslage → gleiche Entscheidung
- keine zufälligen Fallbacks
- kein „Best Guess“-Verhalten

Das ist entscheidend für:
- Replays
- Audits
- Vertrauen in das System

&nbsp;

## Sichtbarkeit & Transparenz

Fail-Safe und Degradation sind **nie unsichtbar**:

- Health-Status wechselt (`warn` / `error`)
- Safety- oder Degradation-Events werden erzeugt
- UI zeigt den Zustand klar an
- Explainability liefert den Grund („missing telemetry“, „over temperature“)

Der Nutzer soll jederzeit wissen:
> *Warum das System gerade nichts tut.*

&nbsp;

## Rückkehr zum Normalbetrieb

Die Rückkehr erfolgt **automatisch**, aber kontrolliert:

- fehlende Signale sind wieder valide
- Grenzwerte wieder im sicheren Bereich
- Health-Status wechselt auf `ok`
- nächster Block-Tick entscheidet regulär

Kein Neustart, kein manueller Reset erforderlich.

&nbsp;

## Abgrenzung

Nicht Bestandteil dieses Kapitels sind:
- konkrete Hardware-Grenzwerte (siehe Konfiguration)
- Alarmierungsregeln
- Betriebshandbücher / Runbooks

Diese Themen gehören in Betriebs- oder Sicherheitsdokumentation.

&nbsp;

## Zusammenfassung

Fail-Safe und Degradation sind kein „Notfallmechanismus“,  
sondern ein **zentrales Architekturprinzip** von BitGridAI.

Das System:
- bleibt ruhig unter Stress,
- handelt konservativ bei Unsicherheit,
- und bevorzugt Stillstand gegenüber Risiko.

---

> **Nächster Schritt:** Ein robustes System muss nicht nur sicher reagieren, sondern auch beobachtbar sein.  
> Im nächsten Kapitel betrachten wir **Logging, Events & Monitoring**.
>
> 👉 Weiter zu **[8.7 Logging, Events & Monitoring](./087_logging_and_monitoring.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
