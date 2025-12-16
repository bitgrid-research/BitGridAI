# 8.6 Fail-safe, Degradation & Robustheit

Im Zweifel: sicher.

BitGridAI interagiert mit realer Hardware, Energieflüssen und Kosten.  
Fehler, Ausfälle oder unvollständige Informationen sind daher kein Ausnahmefall, sondern **Teil der Realität**.

Dieses Kapitel beschreibt die **übergreifenden Prinzipien für Fehlertoleranz, Degradation und Fail-safe-Verhalten**.  
Ziel ist es, dass BitGridAI **niemals unkontrolliert weiterläuft**, sondern jederzeit nachvollziehbar, konservativ und sicher reagiert.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster steht neben einem großen roten Not-Aus-Knopf. Daneben Zahnräder, von denen einige bewusst angehalten sind.)*

---

## Ziel: Sicherheit vor Optimierung

Grundprinzip:
> **Wenn etwas unklar ist, wird nicht optimiert, sondern abgesichert.**

Fail-safe bedeutet in BitGridAI nicht „System aus“, sondern:
- definierte Zustände,
- erklärbares Verhalten,
- minimale, sichere Funktionalität.

---

## Zentrale Leitprinzipien

### 1. Safety schlägt alles (R3)

Die Sicherheitsregel (R3) ist **nicht verhandelbar**:
- sie gilt unabhängig von Autonomie-Level,
- sie kann nicht übersteuert werden,
- sie greift auch bei manuellen Overrides.

Beispiele:
- Übertemperatur → sofortiger Stop
- Hardware-Fehler → Stop
- kritischer Kommunikationsverlust → Stop oder Safe Mode

---

### 2. Keine stillen Fehler

BitGridAI kennt **keine stillen Fehlermodi**.

Jeder relevante Fehler führt zu:
- einem expliziten Health-Status (`warn` / `error`),
- einem Event (Log, Explain-Stream),
- einer sichtbaren Rückmeldung im UI.

---

### 3. Degradation statt Chaos

Nicht jeder Fehler erfordert einen Komplettstopp.

Das System unterscheidet zwischen:
- **voll betriebsfähig**
- **degradiert**
- **nicht betriebsfähig**

Degradation ist ein **bewusster Zustand**, kein Nebenprodukt.

---

## Typische Degradationsauslöser

BitGridAI schaltet in einen degradierten Modus bei:

- fehlender oder unvollständiger Telemetrie
- Ausfall von Adaptern oder Sensoren
- temporärem DB- oder Broker-Ausfall
- inkonsistenter oder nicht validierbarer Konfiguration

Diese Zustände sind im `EnergyState` explizit markiert.

---

## Verhalten im degradierten Modus

Im degradierten Zustand gelten folgende Regeln:

- Optimierungsregeln (R1, R4, R5) treten zurück
- Entscheidungen werden konservativ getroffen
- sicherheitsrelevante Informationen haben Vorrang
- falls Pflichtsignale fehlen → Safe oder Stop

Es wird **nicht geschätzt**, extrapoliert oder geraten.

---

## Fail-safe-Strategien

BitGridAI nutzt mehrere Fail-safe-Mechanismen:

### Safe Mode
- kontrolliertes Herunterfahren von Lasten
- System bleibt ansprechbar
- Recovery möglich ohne Neustart

### Stop
- sofortiges Abschalten steuerbarer Verbraucher
- Nutzung bei akuten Gefahrenlagen

### Minimalbetrieb
- eingeschränkter Betrieb ohne Persistenz oder externe Abhängigkeiten
- klar als Fehlerzustand gekennzeichnet

---

## Recovery-Prinzipien

Fehlerzustände sind **reversibel**, sobald die Ursache behoben ist.

Grundsätze:
- automatischer Reconnect (DB, MQTT, Adapter)
- kein manuelles „Freiklicken“ erforderlich
- Rückkehr in den Normalbetrieb erst bei validem Zustand

Ein Recovery ist immer:
- sichtbar,
- nachvollziehbar,
- dokumentiert.

---

## Zusammenspiel mit Explainability

Fail-safe- und Degradationsentscheidungen sind besonders erklärungsbedürftig.

Daher gilt:
- jeder Safe/Stop hat einen klaren Reason-Code,
- Erklärungen sind auch rückwirkend abrufbar,
- Nutzer sehen nicht nur *dass*, sondern *warum* etwas passiert ist.

---

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete Hardware-Grenzwerte
- Implementierungsdetails einzelner Adapter
- UI-Fehlermeldungstexte

Diese gehören in die jeweiligen Detaildokumentationen.

---

## Zusammenfassung

Die Fail-safe- und Degradationsprinzipien stellen sicher, dass BitGridAI:

- auch bei Fehlern kontrollierbar bleibt,
- niemals unbemerkt unsichere Entscheidungen trifft,
- Sicherheit immer über Komfort und Profit stellt.

BitGridAI darf Fehler machen – aber **keine gefährlichen**.

---

> **Nächster Schritt:** Sicherheit endet nicht beim Laufzeitverhalten.  
> Im nächsten Abschnitt betrachten wir **Security, Authentifizierung & Zugriffskontrolle**.
>
> 👉 Weiter zu **[8.7 Security & Zugriffskontrolle](./087_security_and_access_control.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
