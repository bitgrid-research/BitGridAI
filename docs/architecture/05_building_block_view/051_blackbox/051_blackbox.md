# 05.1.1 System-Whitebox und Schnittstellen

Level 1 zeigt BitGridAI als Ganzes. Wir bleiben aussen, zaehlen die Ports und sagen kurz, was an jedem Stecker passiert. Details folgen in Level 2.

## Scope und Verantwortung

- Lokale, deterministische Steuerung von Energiefluessen (PV, Speicher, Netz, Miner).
- Erklaerbare Entscheidungen mit klaren Triggern und Parametern.
- Keine Cloud-Abhaengigkeit: alle Schnittstellen laufen lokal (MQTT, REST, Datei).

## Top-Level-Bausteine (Blackboxes in der System-Whitebox)

| Baustein | Verantwortung | Provided Interfaces | Required Interfaces |
| --- | --- | --- | --- |
| **Core-Orchestrierung (`core/`)** | Taktung (Block-Scheduler), Regelwerk (R1-R5), EnergyState als Single Source of Truth. | DecisionEvents, Valid-Until-Deadbands, konsolidierter State. | Telemetrie aus Adaptern, Konfiguration, User-Overrides. |
| **Adapter & Feld-I/O (`modules/`)** | Anbindung von PV, Smart Meter, Speicher, Miner. Uebersetzung von Protokollen. | Messwerte (MQTT/REST), Health-Events, Aktor-Quittungen. | Hardware-Protokolle (MQTT, Modbus, REST), Core-Kommandos. |
| **UI & Explainability (`ui/`, `explain/`)** | Lokale Web-UI, API-Layer, Explain-Agent fuer Begruendungen und Was-waere-wenn. | REST/WS-Endpoints, Decision-Previews, Overrides, Explain-Sessions. | State-Feed, DecisionEvents, Auth-Token, Textbausteine. |
| **Data & Research (`data/`, `research/`)** | Persistenz (SQLite, Parquet), Audit- und Replay-Daten, Exporte bei Opt-in. | Append-only Logs, KPIs, Export-Bundles, Health-Metriken. | DecisionEvents, Metrik-Streams, Export-Auftraege. |

> Detail-Whiteboxes zu diesen Bausteinen stehen in Kapitel 5.2.

## Externe Schnittstellen (stabil)

- **MQTT**: Realtime-Daten (`sensor/#`, `energy/state/#`), Steuerkommandos (`miner/cmd/set`), Health (`health/#`).
- **REST (lokal)**: `GET /state`, `GET /timeline`, `GET /preview`, `POST /override`, `POST /research/export`.
- **Dateien**: `config/*.yaml` (Profile), `data/bitgrid.sqlite`, `data/parquet/*.parq`, `explain/*.json` (Textbausteine).

## Ein- und Ausgaenge der System-Whitebox

- **Inputs**: Messwerte (PV, Netz, Speicher, Temperaturen), Prognosen (Preis/Wetter), User-Commands (Override, Research-Toggle), Health-Signale.
- **Outputs**: Aktor-Kommandos (start/stop/set_power), DecisionEvents inkl. Reason/Trigger/Params, State- und Timeline-Feeds, Export-Bundles fuer Replays.

## Randbedingungen

- Deterministisch und testbar: gleicher Input im Core fuehrt zu gleichem Output.
- Safety-first: Temperatur- und Autarkie-Schutz ueberschreiben Optimierungsregeln.
- Datenhoheit: alle Daten bleiben lokal; Exporte nur bei explizitem Opt-in.

---
> Weiter zu **[5.2 Level-2-Whiteboxes](../052_whitebox/README.md)**  
> Zurueck zur **[Kapiteluebersicht](../README.md)**
