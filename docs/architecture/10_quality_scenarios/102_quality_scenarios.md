# 102 – Qualitätsszenarien (Auszug)

> **Kurzüberblick:**  
> Szenarien aus Kap. 10 prüfen **Transparenz, Nachhaltigkeit, Resilienz, HCI, Safety, Stabilität, Hodl/PoW-Traceability**.

> **TL;DR (EN):**  
> Scenarios validate transparency, sustainability, resilience, HCI, safety, stability, hodl/PoW traceability.

---

| ID | Szenario | Zielqualität | Antwort/Maß |
| --- | --- | --- | --- |
| **S1** | Transparente Begründung (R1) | Explainability | Reason/Trigger/Params; Explanation Latency < 2s. |
| **S2** | Energieadaptive Steuerung | Nachhaltigkeit | Stop bei Surplus/Preis unter Schwelle; Flapping↓ ggü. Baseline. |
| **S3** | MQTT/Broker Down → Hold | Resilienz | **hold** + Offline-Puffer; Availability > 99 %. |
| **S4** | Manueller Override | HCI/Autonomie | Start/Stop mit TTL; Auto-Rollback am Blockende. |
| **S6** | Safety-Stop (Temp) | Sicherheit | Sofortiger Stop; Deadband ignoriert; Thermal Incidents = 0. |
| **S7** | Autarkie-Schutz (SoC) | Sicherheit/Autonomie | Stop/Block bei Low SoC; Resume mit Hysterese. |
| **S8** | Deadband-Stabilität | Vorhersagbarkeit | Hold D Blöcke; Switches/h sinken. |
| **S9** | Prognose-Start (R4) | Vorhersagbarkeit | Start nur bei stabiler Forecast-Confidence. |
| **S11** | Hodl-Entscheidung | Nachhaltigkeit/Traceability | `preferred_path=hodl`, `sats_per_kWh` geloggt. |
| **S12** | PoW-Telemetrie & Sicherheit | Sicherheit/Compliance | Reaktion <2s auf Effizienz/Temp-Abweichung; Hashprobe geloggt. |

> Vollständige Details & Runbooks siehe `docs/architecture/10_quality_scenarios.md`.
