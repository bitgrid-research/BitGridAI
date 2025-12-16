# 10.2.5 Safety – Schutz von Hardware & Infrastruktur

Sicherheit schlägt alles.

BitGridAI steuert reale Energieflüsse und physische Hardware.  
Fehler wirken sich hier nicht nur wirtschaftlich aus, sondern können **Geräte beschädigen oder sicherheitskritische Situationen erzeugen**.

Dieses Qualitätsszenario beschreibt, wie BitGridAI in sicherheitsrelevanten Situationen reagieren **muss** – unabhängig von Optimierungszielen, Nutzerwünschen oder Autonomie-Stufe.

Grundsatz:
> **Safety (R3) ist nicht verhandelbar.**

---

## Qualitätsziel

**Vermeidung von Hardware-Schäden und gefährlichen Betriebszuständen**  
durch schnelle, deterministische und nicht übersteuerbare Schutzmechanismen.

---

## Kontext

- Betrieb als lokales Edge-System im LAN (Kap. 07)
- Blockbasierte Entscheidungslogik (Kap. 06)
- Sicherheitsregel **R3** ist jederzeit aktiv
- Sensorik und Adapter können verzögert, fehlerhaft oder nicht verfügbar sein

---

## Szenario S-1: Übertemperatur an der Mining-Hardware

**Stimulus:**  
Ein Temperatursensor meldet einen Wert oberhalb des konfigurierten Grenzwerts.

**Quelle:**  
Mining-Hardware / Sensor-Adapter

**Betriebszustand:**  
Mining aktiv (halb- oder vollautomatischer Modus)

**Erwartete Systemreaktion:**
- Sofortiger Safety-Stop (unabhängig vom Block-Takt)
- Mining-Leistung wird auf `0` gesetzt
- Erzeugung eines `DecisionEvent` mit `rule = R3_SAFETY`
- Übergang in einen stabilen Safe-Zustand

**Akzeptanzkriterien:**
- Reaktionszeit < **1 Sekunde**
- Kein erneuter Start, solange der Grenzwert überschritten ist
- Safety-Ereignis ist im UI sichtbar und persistent geloggt

---

## Szenario S-2: Fehlende oder ungültige Pflicht-Telemetrie

**Stimulus:**  
Ein sicherheitsrelevantes Pflichtsignal (z.B. Temperatur, Netzstatus) fehlt oder ist ungültig.

**Quelle:**  
Sensor, Adapter oder Kommunikationsschicht

**Betriebszustand:**  
Normalbetrieb oder Optimierungsmodus

**Erwartete Systemreaktion:**
- Setzen von `EnergyState.degraded = true`
- Aussetzen aller Optimierungsregeln (R1, R4)
- Übergang in Safe- oder Stop-Zustand
- Dokumentation der Ursache (`missing_telemetry`) in Explain-Events

**Akzeptanzkriterien:**
- Keine Schätzung oder Interpolation fehlender Werte
- Keine Start- oder Leistungssteigerungsentscheidung
- Klarer Hinweis im UI („Safe Mode aktiv – Telemetrie fehlt“)

---

## Szenario S-3: Kritischer interner Systemfehler

**Stimulus:**  
Absturz eines Adapters, Core-Fehler oder inkonsistenter interner Zustand.

**Quelle:**  
Interne Software-Komponente

**Betriebszustand:**  
Beliebiger Autonomie- oder Betriebsmodus

**Erwartete Systemreaktion:**
- Aktive Verbraucher werden gestoppt
- Letzter konsistenter Zustand wird gesichert
- Health-Status wechselt auf `error`
- Kein automatischer Wiederanlauf ohne valide Eingangsdaten

**Akzeptanzkriterien:**
- Kein undefiniertes oder instabiles Verhalten
- Kein Weiterbetrieb mit veralteten Zuständen
- Fehlerursache ist nachvollziehbar dokumentiert

---

## Szenario S-4: Manueller Override im Konflikt mit Safety

**Stimulus:**  
Ein Nutzer erzwingt einen manuellen Start trotz sicherheitskritischer Bedingung.

**Quelle:**  
UI oder API (`/override`)

**Betriebszustand:**  
Manueller oder assistierter Modus

**Erwartete Systemreaktion:**
- Override wird abgelehnt
- Sicherheitsregel R3 bleibt führend
- Nutzer erhält eine verständliche und begründete Rückmeldung

**Akzeptanzkriterien:**
- Safety ist technisch nicht übersteuerbar
- Ablehnung ist transparent, erklärbar und geloggt

---

## Messbare Qualitätsmerkmale

| Merkmal | Ziel |
|-------|------|
| Safety-Reaktionszeit | < 1 s |
| Übersteuerbarkeit von R3 | 0 % |
| Hardware-Schäden durch Software | 0 |
| Sichtbarkeit von Safety-Events | 100 % |

---

## Bezug zur Architektur

- **Regelwerk:** R3 – Safety (Kap. 06)
- **Fail-Safe & Degradation:** Kap. 08.6
- **Autonomie-Stufen:** Kap. 06.7
- **Logging & Monitoring:** Kap. 08.7

---

## Zusammenfassung

Safety ist kein Feature, sondern **die Grundlage der gesamten Architektur**.

BitGridAI:
- bevorzugt Stillstand gegenüber Risiko,
- schützt Hardware auch vor Fehlbedienung,
- und bleibt selbst im Fehlerfall ruhig, deterministisch und erklärbar.

---

> **Nächster Schritt:**  
> Sicherheit schützt vor Schaden – aber ein gutes System muss auch langfristig
> **nachvollziehbar und reproduzierbar** bleiben.
>
> 👉 Weiter zu **[10.2.6 Reproduzierbarkeit & Erweiterbarkeit](./1026_reproducibility_and_extensibility.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
