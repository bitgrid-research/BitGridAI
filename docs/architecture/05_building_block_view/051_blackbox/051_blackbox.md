# 05.1.1 System-Blackbox und Schnittstellen

Level 1 zeigt **BitGridAI als Gesamtsystem**.  

Wir bleiben bewusst außen, zählen die Anschlüsse und beschreiben kurz,
**was an jedem Stecker passiert**.  
Wie es innen aussieht, folgt in Level 2.

![Hamster vor der System-Blackbox mit klar definierten Ein- und Ausgängen](../media/pixel_art_hamster_blackbox.png)

---

## Scope und Verantwortung

BitGridAI übernimmt folgende Aufgaben:

- Lokale, deterministische Steuerung von Energieflüssen (PV, Speicher, Netz, Miner).
- Erklärbare Entscheidungen mit klaren Triggern und Parametern.
- Kein Cloud-Zwang: alle relevanten Schnittstellen laufen lokal (MQTT, REST, Datei).

---

## Top-Level-Bausteine  
*(Blackboxes innerhalb der System-Blackbox)*

| Baustein | Verantwortung | Provided Interfaces | Required Interfaces |
| :-- | :-- | :-- | :-- |
| **Core-Orchestrierung (`core/`)** | Zeitliche Taktung (BlockScheduler), Regelwerk (R1–R5), `EnergyState` als Single Source of Truth. | DecisionEvents, Deadband-Status, konsolidierter Systemzustand. | Telemetrie aus Adaptern, Konfiguration, User-Overrides. |
| **Adapter & Feld-I/O (`modules/`)** | Anbindung von PV, Smart Meter, Speicher und Minern. Übersetzung externer Protokolle. | Messwerte, Health-Events, Aktor-Quittungen. | Hardware-Protokolle (MQTT, Modbus, REST), Core-Kommandos. |
| **UI & Explainability (`ui/`, `explain/`)** | Lokale Web-UI, API-Layer, Explain-Agent für Begründungen und „Was-wäre-wenn“-Szenarien. | REST-/WS-Endpunkte, Previews, Overrides, Explain-Sessions. | State-Feeds, DecisionEvents, Auth-Informationen, Textbausteine. |
| **Data & Research (`data/`, `research/`)** | Persistenz (SQLite, Parquet), Audit-Trails, Replay- und Exportfunktionen (Opt-in). | Append-only Logs, KPIs, Export-Bundles, Health-Metriken. | DecisionEvents, Metrik-Streams, Export-Aufträge. |

> Die detaillierte Innenansicht dieser Bausteine folgt in **Kapitel 5.2**.

---

## Externe Schnittstellen (stabil)

- **MQTT:** Realtime-Daten (`sensor/#`, `energy/state/#`), Steuerkommandos (`miner/cmd/set`), Health (`health/#`)
- **REST (lokal):**  
  `GET /state`, `GET /timeline`, `GET /preview`, `POST /override`, `POST /research/export`
- **Dateien:**  
  `config/*.yaml` (Profile),  
  `data/bitgrid.sqlite`,  
  `data/parquet/*.parq`,  
  `explain/*.json` (Textbausteine)

---

## Ein- und Ausgänge der System-Blackbox

- **Inputs:**  
  Messwerte (PV, Netz, Speicher, Temperaturen),  
  Prognosen (Preis, Wetter),  
  User-Commands (Overrides, Research-Toggle),  
  Health-Signale.

- **Outputs:**  
  Aktor-Kommandos (`start`, `stop`, `set_power`),  
  DecisionEvents inkl. Reason / Trigger / Parameter,  
  State- und Timeline-Feeds,  
  Export-Bundles für Replays.

---

## Randbedingungen

- **Deterministisch:** Gleicher Input im Core führt zu gleichem Output.
- **Safety-first:** Schutzmechanismen (Temperatur, Autarkie) übersteuern Optimierung.
- **Datenhoheit:** Alle Daten bleiben lokal; Exporte nur bei explizitem Opt-in.

---

> **Nächster Schritt:**  
> Die Anschlüsse sind klar. Jetzt öffnen wir die Bausteine.
>
> 👉 Weiter zu **[5.2 Level 2 – Die Whitebox (Innenleben)](../052_whitebox/README.md)**
>  
> 🔙 Zurück zur **[Kapitelübersicht](../README.md)**
