# 08.6 Logging & Tracing

Das digitale Gedächtnis und die Blackbox.

Logging und Tracing sind essenziell, um im Nachhinein zu verstehen, warum das System eine bestimmte Entscheidung getroffen hat – insbesondere bei verteilten Abläufen zwischen Adaptern, Core und UI.

Wir setzen auf **strukturiertes, append-only Logging** direkt auf dem Edge-Device, um die **Reproduzierbarkeit** (Replay) und die **Auditierbarkeit** aller Entscheidungen zu gewährleisten. Zero Outbound Telemetry ist dabei das oberste Gebot.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster sortiert Datenpakete in einen großen Ordner mit der Aufschrift "Audit-Log". Die Pakete sind mit Zeitstempeln und Rule-IDs beschriftet.)*
![Hamster sortiert Log-Daten](../../media/pixel_art_hamster_audit_log.png)

## 1. Die Logging-Prinzipien

Alle Logging- und Tracing-Maßnahmen folgen diesen strengen Regeln:

1.  **Lokal & Offline:** Es gibt **keine Cloud-Backhauls**. Alle Logs und Traces bleiben auf dem Edge-Device. Ports für externe Kommunikation sind minimal gehalten (z.B. nur für Preis-Updates).
2.  **Strukturiert & Event-basiert:** Wir loggen keine einfachen Textzeilen, sondern strukturierte Datenobjekte. Das ermöglicht das einfache Filtern und die Analyse.
    * Kern-Events: `DecisionEvent`, `EnergyStateChangedEvent`, `DeadbandActivatedEvent`, `ExplainSession`.
3.  **Append-only:** Log-Dateien werden nur angehängt, nie verändert. Dies ist die Basis für die Auditierbarkeit. Exports erhalten Hashes, um die Integrität beim Transfer zu sichern.
4.  **Versioniert:** Änderungen in der Logik werden im Log mitgeschrieben. Geloggt werden die **YAML-Configs**, die **Prompt-Versionen** des Explain-Agents und die **Microcopy** der UI.
5.  **Privacy-by-Default:** Die Logs enthalten keine direkten personenbezogenen Daten. Research-Exports benötigen das Opt-in des Nutzers (Toggle).

## 2. Die Ablagestruktur

Je nach Verwendungszweck landen die Daten an unterschiedlichen Orten (siehe 08.2 Persistenz):

| Speicherort | Daten-Charakter | Inhalt & Zweck |
| :--- | :--- | :--- |
| **`data/bitgrid.sqlite`** | Operational (Hot) | Kurzfristige Timeline, KPI-Zwischenstände (z.B. Flapping-Rate), schneller Zugriff für das UI. |
| **`data/parquet/*.parq`** | Analytical (Cold) | **Langzeit-Logs.** Sämtliche `EnergyState`- und `DecisionEvent`-Historie über Jahre. Ideal für den Replay-Runner. |
| **`config/*.yaml`** | Static | Sämtliche Policies, Flags und Schwellenwerte. Sind versionskontrolliert. |
| **`explain/*.json`** | Research/Context | Gespeicherte `ExplainSessions`, Prompt-Historie und Sprachversionen (DE/EN). |

## 3. Tracing-Punkte (Hooks)

Tracing ist notwendig, um verteilte Abläufe (z.B. Core $\rightarrow$ MQTT $\rightarrow$ Adapter) nachzuvollziehen.

* **MQTT Topics:** Der lokale Broker ist der zentrale Hub für Tracing. Events wie `energy/state/#`, `miner/state/#` und `explain/events/#` erlauben es einem externen Tool (oder dem UI) im "Listen-Only"-Modus, den gesamten Fluss zu verfolgen.
* **REST Endpunkte:** API-Calls wie `GET /state`, `/timeline` oder `POST /override` werden geloggt. Kritische Endpunkte wie `POST /decisions` protokollieren die Ankunft des Befehls in der Actuation-Schicht.
* **UI Events:** Auch User-Interaktionen sind Teil des Audit-Trails. Events wie `toast_shown` (wurde der Nutzer informiert?), `override_enter/exit` und `export_reason` werden geloggt.

## 4. Lokale KPIs (Key Performance Indicators)

KPIs werden lokal berechnet und dienen der Vertrauensbildung. Sie sind Teil des Logs und der UI:

* **Trust:** Wie oft haben die Regeln R1/R4 die erwartete Wirkung erzielt?
* **Coverage:** Wie oft konnte der Miner laufen (gemessen am theoretischen Überschuss)?
* **Flapping Rate:** Wie oft musste Regel R5 (Deadband) eingreifen?

---
> **Nächster Schritt:** Wir haben die Regeln und die Oberfläche definiert. Nun klären wir die letzten übergreifenden Konzepte, bevor wir zu den Design-Entscheidungen kommen.
>
> 👉 Weiter zu **[08.7 Testbarkeit & Simulation](./087_testability_and_simulation.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
