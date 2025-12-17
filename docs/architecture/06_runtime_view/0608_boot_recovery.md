# 06.08 - Szenario: Boot & Recovery

Stabil ab Minute null.

Bevor BitGridAI optimieren, entscheiden oder eingreifen kann, muss es **zuverlässig starten** – und mit Teil- oder Totalausfällen umgehen können.  
Dieses Szenario beschreibt, wie das System beim Hochfahren seine Abhängigkeiten prüft, einen konsistenten Anfangszustand herstellt und wie es sich bei Ausfällen von Infrastrukturkomponenten verhält.

Ziel ist ein **deterministisches Verhalten**:  
Kein undefinierter Zustand, kein stilles Weiterlaufen, kein Aktionismus.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster startet eine Maschine mit einer Checkliste: „Config ✓, DB ✓, MQTT ✓“. Daneben ein Notfallhebel mit der Aufschrift „Safe Mode“.)*

&nbsp;

## Das Ziel: Definierter Start, kontrollierte Degradation

BitGridAI unterscheidet klar zwischen:
- **Startfähigkeit** (Was muss verfügbar sein, damit das System „ready“ ist?)
- **Betriebsfähigkeit** (Was passiert, wenn Abhängigkeiten zur Laufzeit ausfallen?)

Jede Phase ist explizit, beobachtbar und über Health-Signale nach außen sichtbar.

&nbsp;

## Der Ablauf beim Systemstart (vereinfacht)

1. **Initialisierung (Boot):**  
   Beim Start lädt das System die Konfiguration und validiert sie gegen ein festes Schema.  
   Anschließend werden die Pflichtabhängigkeiten geprüft:
   - Datenbank (SQLite)
   - MQTT-Broker

2. **Bereitschaft (Ready):**  
   Erst wenn alle erforderlichen Dienste erreichbar sind, setzt das System seinen Zustand auf `ready`.  
   Vorher werden **keine** Regelentscheidungen getroffen.

3. **Zustandswiederherstellung (Replay):**  
   Falls vorhanden, wird der letzte persistierte Zustand geladen.  
   Der Core initialisiert daraus den aktuellen `EnergyState`.

4. **Regelstart (First Tick):**  
   Mit dem ersten Block-Tick startet der normale Regelzyklus (R1–R5).

&nbsp;

## Recovery-Pfade bei Ausfällen

### Broker-Ausfall (MQTT)

- Adapter pausieren oder puffern eingehende bzw. ausgehende Signale.
- Der System-Health-Status wechselt auf `warn` oder `error`.
- Der Core bleibt deterministisch und trifft Entscheidungen konservativ:
  - Wechsel in Safe- oder Stop-Zustände, falls erforderlich.

### Datenbank-Ausfall (DB)

- Der Core schaltet auf einen **Minimalbetrieb ohne Persistenz**.
- Health-Status wird auf `error` gesetzt.
- Entscheidungen laufen weiter, aber ohne dauerhafte Speicherung.

### Wiederkehr der Abhängigkeiten

- Automatischer Reconnect zur DB bzw. zum Broker.
- Health-Status wechselt zurück auf `ok`.
- Der normale Blockbetrieb wird ohne Neustart fortgesetzt.

&nbsp;

## Schnittstellen & Signale

- **Health-Events** für:
  - Konfiguration
  - Datenbank
  - MQTT-Broker
- Zustände sind extern beobachtbar (Monitoring, UI).
- Retry- und Backoff-Strategien sind explizit in Adapter- und Core-Komponenten definiert.

---

> **Nächster Schritt:** Der Start ist abgesichert – aber was passiert, wenn Datenquellen ausfallen?  
> Jetzt betrachten wir, **wie BitGridAI mit Adapter- und Sensor-Ausfällen umgeht**.
>
> 👉 Weiter zu **[06.09 - Adapter- & Sensor-Ausfall](./0609_adapter_sensor_failure.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
