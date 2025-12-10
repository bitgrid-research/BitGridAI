# 03.2 Technischer Kontext (Technical Context)

Die Sicht unter der Haube.

Nachdem wir die fachlichen Nachbarn kennen, wird es hier technisch. Wir definieren, wie **BitGridAI** physisch und logisch mit seiner Umwelt verdrahtet ist.

Das System agiert als **lokaler Orchestrator** in einem geschlossenen LAN. Es koppelt PV, Speicher und Miner über diverse Protokolle, zentralisiert im `EnergyState` und getaktet durch den `BlockScheduler`.

*(Platzhalter für ein Bild: Ein technisches Diagramm im Pixel-Art-Stil. Der Hamster trägt einen Werkzeuggürtel und verbindet verschiedene Stecker – LAN, USB, WLAN – mit einer zentralen Box.)*
![Hamster verkabelt das System](../media/pixel_art_hamster_cables.png)

## Externe Systeme & Schnittstellen

BitGridAI kommuniziert mit folgenden Nachbarsystemen. Die Kommunikation erfolgt primär über **MQTT**, **REST** und **Modbus**.

| System | Schnittstelle | Datenrichtung | Zweck & Beschreibung |
| :--- | :--- | :--- | :--- |
| **Home Assistant** 🏠 | MQTT / REST | `In/Out` | Integration in das Smart Home. Austausch von Statusdaten (`State`) und Empfang von Kommandos über das UI von HA. |
| **PV-Wechselrichter** ☀️ | Modbus TCP / API | `In` | Auslesen von Erzeugungsdaten (Watt), Spannungen und Fehlerstatus. |
| **Smart Meter / Sensorik** 📏 | MQTT / SML / API | `In` | Die "Augen" des Systems. Import/Export-Daten am Netzanschlusspunkt, Phasenleistung und Momentanwerte (oft via SML-Lesekopf). |
| **Energiespeicher** 🔋 | API / MQTT | `In/Out` | Lesen des SoC (Ladestand). Schreiben von Lade-/Entlade-Limits oder Prioritäten. |
| **Mining-Controller** ⛏️ | LAN / API / SSH | `Out` | Steuerung der Miner. Setzen von Leistungsstufen (Power/Hashrate), Start/Stop-Befehle, Überwachung von Temperatur/Lüftern. |
| **Preis/Forecast** 🔮 | Datei / Lokaler Dienst | `In` | Liefert Tarife und Prognosen (für Regel R1/R4). Läuft oft als separater Container ("Sidecar") lokal mit. |
| **Erklär-UI** 🖥️ | WebSocket / REST | `Out` | Das Frontend für den Nutzer. Visualisierung von Energieflüssen & Entscheidungsgründen in Echtzeit. |
| **Research/Replay Node** 🎓 | Datei / CLI | `In` | Schnittstelle für die Wissenschaft. Auslesen von Parquet-Logs, Berechnung von KPIs und Durchführen von "Was-wäre-wenn"-Replays. |

## Grenzen & Datenflüsse (Boundaries & Flows)

Wir unterscheiden strikt zwischen dem, was **im** System passiert (Entscheidungshoheit) und dem, was **draußen** ist (Ausführung).

* **Inside BitGridAI:**
    * `EnergyState` (Single Source of Truth - SSoT)
    * `Rule Engine` (R1–R5) & `BlockScheduler` (10-Min-Takt)
    * `Explain-Agent` & `KPI/Logging`
    * Lokale Adapter (zur Protokoll-Übersetzung)

* **Outside:**
    * Physische Hardware (PV, Speicher, ASICs)
    * Externe UIs (Browser, Home Assistant Core)
    * Optionale lokale Forecast-Dienste

### Die zentralen Kommunikationsflüsse

1.  **Sensing (Input):**
    Sensoren/Meter/APIs $\rightarrow$ Adapter $\rightarrow$ **EnergyState** (Update SSoT).
2.  **Decision (Processing):**
    BlockScheduler (Trigger) $\rightarrow$ Rule Engine liest EnergyState $\rightarrow$ Generiert **DecisionEvent**.
3.  **Actuation (Output):**
    DecisionEvent $\rightarrow$ Adapter $\rightarrow$ Physischer Befehl an Miner/Speicher.
4.  **Feedback (User):**
    Overrides/Research-Toggle $\rightarrow$ Rule Engine $\rightarrow$ UI Feedback.

## Domain-Events (Interne Sprache)

Um die Entkopplung zu wahren, kommunizieren die internen Komponenten über Events. Diese spiegeln die technische Realität wider:

* `EnergyStateChangedEvent`: Neue Messwerte sind da.
* `DecisionEvent`: Eine Regel hat gefeuert (z.B. "Start Mining due to Surplus").
* `DeadbandActivatedEvent`: Eine Änderung wurde unterdrückt, um Flapping zu verhindern.
* `ExplainSessionCreated`: Der Nutzer hat eine Erklärung angefordert.
* `ResearchToggleChanged`: Der Modus für erweitertes Logging wurde umgeschaltet.

---
> **Nächster Schritt:** Wir wissen jetzt, wie wir technisch vernetzt sind. Jetzt widmen wir uns der großen Strategie, wie wir das System innerlich aufbauen und warum wir "Local-First" so ernst nehmen.
>
> 👉 Weiter zu **[04 Lösungsstrategie](../04_solution_strategy/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
