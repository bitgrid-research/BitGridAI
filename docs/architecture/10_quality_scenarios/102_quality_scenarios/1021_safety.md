# 10.2.1 Safety – Schutz von Hardware & Infrastruktur

Sicherheit schlägt alles.

BitGridAI steuert reale Energieflüsse und physische Hardware.  
Ein Fehler kann nicht nur wirtschaftlichen Schaden verursachen, sondern **Geräte beschädigen oder Sicherheitsrisiken erzeugen**.

Dieses Qualitätsszenario beschreibt, wie BitGridAI in sicherheitskritischen Situationen reagieren **muss**, unabhängig von Optimierung, Nutzerwünschen oder Autonomie-Stufe.

Grundsatz:
> **Safety (R3) ist nicht verhandelbar.**

---

## Qualitätsziel

**Vermeidung von Hardware-Schäden und gefährlichen Betriebszuständen**  
durch deterministische, schnelle und nicht übersteuerbare Schutzmechanismen.

---

## Kontext

- BitGridAI läuft als Edge-System im LAN (Kap. 07)
- Entscheidungen erfolgen blockbasiert (Kap. 06)
- Sicherheitsregel **R3** ist stets aktiv
- Sensorik und Adapter liefern Telemetrie mit möglicher Verzögerung oder Ausfällen

---

## Szenario S-1: Übertemperatur am Miner

**Stimulus:**  
Ein Temperatursensor meldet einen Wert oberhalb des konfigurierten Grenzwerts.

**Quelle:**  
Miner-Hardware / Adapter

**Umgebung:**  
Laufender Mining-Betrieb (halb- oder vollautomatisch)

**Erwartete Systemreaktion:**
- Sofortiger Safety-Stop (unabhängig vom Block-Tick)
- Mining-Leistung wird auf 0 gesetzt
- DecisionEvent mit `rule = R3_SAFETY`
- Systemzustand bleibt stabil (`Safe Mode`)

**Akzeptanzkriterien:**
- Reaktionszeit < **1 Sekunde**
- Keine weitere Mining-Aktion bis Temperatur wieder unter Grenzwert
- Safety-Event ist im UI sichtbar und im Log persistiert

---

## Szenario S-2: Fehlende Pflicht-Telemetrie

**Stimulus:**  
Pflichtsignal (z.B. Temperatur, Netzstatus) bleibt aus oder ist ungültig.

**Quelle:**  
Sensor, Adapter oder Kommunikationsschicht

**Umgebung:**  
Normalbetrieb oder Autarkie-/Optimierungsmodus

**Erwartete Systemreaktion:**
- `EnergyState.degraded = true`
- Optimierungsregeln (R1, R4) werden ausgesetzt
- Übergang in Safe- oder Stop-Zustand
- Explainability meldet Ursache (`missing_telemetry`)

**Akzeptanzkriterien:**
- Keine Schätzung fehlender Werte
- Keine Start- oder Leistungssteigerungsentscheidung
- Klarer Hinweis im UI („Daten fehlen – Safe Mode aktiv“)

---

## Szenario S-3: Kritischer Systemfehler (Core / Adapter)

**Stimulus:**  
Interner Fehler im Core, Adapter-Absturz oder inkonsistenter Zustand.

**Quelle:**  
Software-Komponente

**Umgebung:**  
Beliebiger Betriebsmodus

**Erwartete Systemreaktion:**
- Aktive Verbraucher werden gestoppt
- Letzter konsistenter Zustand wird gesichert
- Health-Status wechselt auf `error`
- Keine automatischen Wiederanlaufversuche ohne valide Daten

**Akzeptanzkriterien:**
- Kein undefiniertes Verhalten
- Kein Weiterbetrieb mit veralteten Zuständen
- Fehlerursache ist nachvollziehbar dokumentiert

---

## Szenario S-4: Manueller Override vs. Sicherheit

**Stimulus:**  
Nutzer erzwingt einen manuellen Start trotz kritischer Bedingung.

**Quelle:**  
UI / API (`/override`)

**Umgebung:**  
Manueller oder assistierter Modus

**Erwartete Systemreaktion:**
- Override wird abgelehnt
- Safety-Regel R3 bleibt führend
- Nutzer erhält verständliche Rückmeldung („Override rejected: unsafe condition“)

**Akzeptanzkriterien:**
- Kein Sicherheitsmechanismus ist übersteuerbar
- Ablehnung ist transparent und begründet

---

## Messbare Qualitätsmerkmale

| Merkmal | Ziel |
|-------|------|
| Safety-Reaktionszeit | < 1 s |
| Übersteuerbarkeit von R3 | 0 % |
| Hardware-Schäden durch Software | 0 |
| Safety-Event-Sichtbarkeit | 100 % |

---

## Bezug zur Architektur

- **Regelwerk:** R3 (Kap. 06)
- **Fail-Safe & Degradation:** Kap. 08.6
- **Autonomie-Stufen:** Kap. 06.7
- **Logging & Monitoring:** Kap. 08.7

---

## Zusammenfassung

Safety ist kein Feature, sondern **die Grundlage des Systems**.

BitGridAI:
- bevorzugt Stillstand gegenüber Risiko,
- schützt Hardware auch gegen Nutzerwünsche,
- und bleibt selbst im Fehlerfall ruhig und vorhersehbar.

---

> **Nächster Schritt:**  
> Sicherheit allein reicht nicht. Ein gutes System muss auch **stabil** sein.
>
> 👉 Weiter zu **[10.2.2 Stabilität & Totband](./102_stability_scenarios.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
