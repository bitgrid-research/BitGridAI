# 05.2.1 - Whitebox: Core-Orchestrierung

Hier entscheidet sich alles.

Der Core ist der **deterministische Entscheidungskern** von BitGridAI.  
Er arbeitet im festen **10-Minuten-Takt**, bewertet die Regeln **R1–R5** und pflegt den `EnergyState` als **Single Source of Truth**.

Keine Hardware.  
Keine Protokolle.  
Keine UI.

Nur Zustand, Zeit und Regeln.

![Hamster im Core-Orchestrator](../../../../media/bithamster_052.png)

&nbsp;

## Scope und Verantwortung

- Deterministische Steuerung im 10-Minuten-Takt  
- Bewertung der Regeln R1–R5  
- Pflege des `EnergyState` als Single Source of Truth  
- Durchsetzung von Safety-, Autarkie- und Stabilitätsgrenzen  

&nbsp;

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **Block-Scheduler** | Erzwingt 10-Minuten-Blockfenster, vergibt `valid_until` (Deadbands). | Entkoppelt Flapping, gibt den Systemtakt vor. |
| **Energy Context** | Konsolidiert Messwerte und Forecasts zum `EnergyState`. | Validiert Einheiten, Zeitstempel und Vollständigkeit. |
| **Rule Engine** | Bewertet R1–R5, erzeugt `Decision` und `DecisionEvent`. | Priorisierung: Safety > Autarkie > Stabilität > Optimierung. |
| **Override Handler** | Verarbeitet manuelle Eingriffe mit TTL und Scope. | Konfliktprüfung gegen Safety- und Autarkie-Regeln. |

&nbsp;

## Level-3-Details

- **[5.2.1.1 Block-Scheduler](./05211_block_scheduler.md)**  
- **[5.2.1.2 Energy Context](./05212_energy_context.md)**  
- **[5.2.1.3 Rule Engine](./05213_rule_engine.md)**  
- **[5.2.1.4 Override Handler](./05214_override_handler.md)**  

&nbsp;

## Schnittstellen

**Provided**

- `DecisionEvent` (inkl. `reason`, `trigger`, `params`)
- `valid_until` (Deadband-Grenzen)
- State-Feed (`GET /state`, MQTT `energy/state/#`)
- Health-Status des Entscheidungspfads

**Required**

- Telemetrie aus `modules/` (PV, Netz, Speicher, Miner)
- Forecast- und Preisdaten
- User-Overrides (`POST /override`)
- Konfiguration (`config/*.yaml`)

&nbsp;

## Hauptdatenflüsse

1. Telemetrie & Forecasts → Energy Context → konsolidierter `EnergyState`  
2. Block-Scheduler → Rule Engine → `Decision` / `DecisionEvent`  
3. Decision → Adapter-Kommandos (MQTT/REST) + UI/Explain-Feed  
4. Decision & State → Data/Research (Logs, KPIs, Exporte)

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Deterministisch:** Gleicher Input → gleicher Output (Replay-fähig)  
- **Safety-first:** Temperatur- und Autarkie-Regeln überstimmen Optimierungen  
- **Timeboxing:** Jede Auswertung bleibt innerhalb eines Blockfensters  
- **Fail-ruhig:** Keine hektischen Reaktionen, kein Flapping  

---
> **Nächster Schritt:** Der Core ist aufgeteilt. Jetzt gehen wir ins Detail und schauen,
> wie der Systemtakt funktioniert und warum er so wichtig ist.
>
> 👉 Weiter zu **[5.2.2 - Whitebox: Adapter & Feld-I/O](../0522_adapters_whitebox/README.md)** 
>
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](../README.md)**
