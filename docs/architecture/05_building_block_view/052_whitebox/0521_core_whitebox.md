# 05.2.1 Whitebox Core-Orchestrierung

Scope: deterministische Steuerung im 10-Minuten-Takt, Regeln R1-R5, Pflege des `EnergyState` als Single Source of Truth.

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **Block-Scheduler** | Erzwingt 10-Minuten-Blockfenster, vergibt `valid_until` (Deadbands). | Triggert die Regel-Engine, entkoppelt Flapping. |
| **Energy Context** | Konsolidiert alle Messwerte/Forecasts zum `EnergyState`. | Validiert Einheiten, Zeitstempel und Vollstaendigkeit. |
| **Rule Engine** | Bewertet R1-R5, erstellt `Decision` und `DecisionEvent`. | Priorisierung: Safety > Autarkie > Stabilitaet > Optimierung. |
| **Override Handler** | Verarbeitet manuelle Eingriffe, setzt TTL/Scope. | Prueft Konflikte mit Safety/Autarkie. |

## Level-3-Details

- [5.2.1.1 Block-Scheduler](./0521_core_whitebox/05211_block_scheduler.md)
- [5.2.1.2 Energy Context](./0521_core_whitebox/05212_energy_context.md)
- [5.2.1.3 Rule Engine](./0521_core_whitebox/05213_rule_engine.md)
- [5.2.1.4 Override Handler](./0521_core_whitebox/05214_override_handler.md)

## Schnittstellen

- **Provided:** `DecisionEvent` (mit reason/trigger/params), `valid_until`, State-Feed (`/state`, MQTT `energy/state/#`), Health des Regelpfads.
- **Required:** Telemetrie aus `modules/` (PV, Netz, Speicher, Miner), Forecast/Preise, User-Overrides (`POST /override`), Konfiguration (`config/*.yaml`).

## Hauptdatenfluesse

1) Telemetrie/Forecasts -> Energy Context -> konsolidierter `EnergyState`.  
2) Block-Scheduler -> Rule Engine -> `Decision` / `DecisionEvent`.  
3) Decision -> Adapter-Kommandos (MQTT/REST) + UI/Explain-Feed.  
4) Decision/State -> Data/Research (Logs, KPIs, Exporte).

## Qualitaets- und Betriebsaspekte

- Deterministisch (gleicher Input -> gleicher Output) fuer Replays/Tests.
- Safety-first: Temperatur- und Autarkie-Checks ueberstimmen Optimierungen.
- Timeboxing: jede Regel-Auswertung < 1 Blockfenster; keine Blockierung des Schedulers.

---
> Zurueck zu **[5.2 Level-2-Whiteboxes](./README.md)**  
> Zurueck zu **[5.1 Whitebox Gesamtsystem](../051_blackbox/051_blackbox.md)**
