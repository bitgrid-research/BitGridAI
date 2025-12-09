# 091 – Architekturentscheidungen (DE · Kurzfassung)

> **Kurzüberblick:**  
> ADRs verankern **Local-First**, **Erklärbarkeit**, **Nachhaltigkeit**, **Determinismus**. Kernpunkte: **R1–R5**, **10-Min-BlockScheduler**, **EnergyState (SSoT)**, **Deadband**, **MQTT+REST**, **AGPLv3**, **kein Cloud-Backend**.

> **TL;DR (EN):**  
> ADRs lock in local-first, explainability, sustainability, deterministic control (R1–R5, 10-min cadence, EnergyState, deadband, MQTT/REST, AGPLv3, no cloud).

---

## ADR-Übersicht (Auszug)

| ADR | Entscheidung | Begründung |
| --- | --- | --- |
| **001 Local-First** | Alles on-prem, keine Cloud. | Datenschutz, Autonomie, Resilienz. |
| **002 MQTT-Bus** | MQTT für State/Cmd/Events; REST optional. | Lose Kopplung, Standard, leichtgewichtig. |
| **003 SQLite + Parquet** | Runtime-DB + Langzeit/Replay. | Portabel, auditierbar, wartungsarm. |
| **004 Explainability-UI** | „Warum jetzt?“ + Timeline + Preview. | Vertrauen > reine Visualisierung. |
| **005 Nachhaltigkeit** | Surplus/Preis als Steuergröße. | Effizienz, Autarkie, Forschung. |
| **006 10-Min-BlockScheduler** | `block=floor(epoch/600)`. | Stabilität, Anti-Flapping, Audit. |
| **007 Deterministische R1–R5** | Kein Black-Box-ML im Regelpfad. | Testbar, erklärbar. |
| **008 EnergyState SSoT** | Ein Schreiber, viele Leser. | Konsistenz, weniger Race-Conditions. |
| **009 Deadband/Hysterese** | Haltefenster D Blöcke. | Weniger Flapping, Hardware-Schutz. |
| **010 Manual Override** | Block-TTL, Reason `manual_override`. | Nutzerkontrolle ohne Policy-Drift. |
| **011 Lokale Forecasts** | R4 nutzt nur lokale Quellen. | Keine Cloud, reduzierte Abhängigkeit. |
| **012 Append-only + YAML-Version** | Logs/Configs versioniert. | Reproducibility, Audit. |
| **013 Lizenz AGPLv3** | Copyleft, Klarheit 3rd-Party. | Offenheit, Forschung. |
| **014 Privacy by Default** | Keine Telemetrie, minimale Ports. | DSGVO, Vertrauen. |
| **015 Safety First** | Stop → Safe bei SoC/Temperatur. | Hardware-Schutz, Vertrauen. |
| **016 MQTT/REST Contract** | Topics/Endpoints klar definiert. | Interop, Tests. |
| **017 KPIs als Ziele** | Wirkung messen (Grid↓, Flapping↓, Coverage). | Evidenz statt Behauptung. |
| **018 Energy-Path-Policies** | Export/Heat/Hodl Policy-Set + Logging. | Transparente Opportunitätskosten. |
| **019 PoW Telemetrie & Hash-Proof** | Pflichtwerte/Proben vom Miner. | Sicherheit, Compliance, Forschung. |

> Vollständige Tabellen/EN-Version: `docs/architecture/09_design_decisions.md`.
