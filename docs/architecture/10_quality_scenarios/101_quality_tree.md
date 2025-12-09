# 101 – Quality Tree / Qualitätsbaum

> **Kurzüberblick:**  
> Hauptqualitäten: **Transparenz & Erklärbarkeit**, **Autonomie/Privacy**, **Nachhaltigkeit**, **Vorhersagbarkeit/Stabilität**, **Sicherheit**, **Reproduzierbarkeit/Erweiterbarkeit**.

> **TL;DR (EN):**  
> Qualities: transparency/explainability, autonomy/privacy, sustainability, predictability/stability, safety, reproducibility/extensibility.

---

## Baum (Textuell)

- **Transparenz & Erklärbarkeit**  
  - Reason/Trigger/Params  
  - Timeline & Next-Block-Preview  
  - Explain-Agent on-device  
- **Autonomie & Privacy**  
  - Local-first, keine Telemetrie  
  - minimale Ports, lokale Auth  
- **Nachhaltigkeit**  
  - Surplus/Preis-Steuerung (R1/R4)  
  - Hodl/Heat/Export-Policies  
- **Vorhersagbarkeit & Stabilität**  
  - 10-Min-BlockScheduler, Deadband (R5)  
  - deterministische R1–R5  
- **Sicherheit**  
  - Thermo/SoC-Schutz (R3/R2), Stop → Safe  
  - Fail-Safe bei Fehlern  
- **Reproduzierbarkeit & Erweiterbarkeit**  
  - Append-only Logs, Replay  
  - Adapter-Architektur, MQTT/REST-Contracts

> Mirrors the table in `01/012_quality_goals.md` and scenarios in `10_quality_scenarios.md`.
