# 11 – Risiken & Technische Schulden (Kurzfassung)

> **Kurzüberblick:**  
> Risiken entlang **Local-First / R1–R5 / 10-Min-Block / EnergyState / Deadband / Privacy-by-Default**. Fokus: Betriebssicherheit (Stop → Safe), Datenkonsistenz, Erklärbarkeit, Wartbarkeit.

> **TL;DR (EN):**  
> Risks assessed vs. local-first, R1–R5, 10-min cadence, EnergyState, deadband, privacy-by-default; focus on safety, consistency, explainability, maintainability.

---

## Hauptrisiken (Auszug)

| Risiko | Auswirkung | Gegenmaßnahme |
| --- | --- | --- |
| Hardwareausfall (Sensor/Lüfter/Pi) | Hoch | Health-Monitor, Redundanz, Thermal-Alarme (R3). |
| MQTT-Broker-Ausfall | Mittel | Offline-Puffer, Retry/Backoff, „offline hold“ (S3). |
| Zeitdrift | Mittel | Drift-Erkennung, 1-Block-Hold + Re-Sync (S10). |
| Fehlerhafte Regeldefinition | Mittel | Schema-Validation, Replay/Dry-Run, Unit-Tests R1–R5. |
| Forecast-Fehler (R4) | Mittel | Sigma/Margin, R2/R3 priorisiert, schnelles Disable. |
| Deadband falsch getuned | Mittel | Replay A/B, Flapping-KPI, adaptive Empfehlung. |
| Storage-Überlauf | Hoch | Rotation/Archiv, Low-Disk-Alarm. |
| UI-Missverständnis | Mittel | HCI-Tests, Glossar-Tooltips, „Why?“ Dialog. |
| PoW-Telemetrielücke | Hoch | Pflicht-Hashproben, Alerts aus S12, Audit-Trail. |

---

## Technische Schulden (Auszug)

- Adapter-Modularität ausbauen (strict ports/plugins).  
- Logging-Schema vereinheitlichen (DecisionEvent, EnergyStateChangedEvent).  
- MQTT/Rule-Integrationstests ergänzen; Forecast-Evaluator verbessern.  
- A11y-Gaps (Keyboard/ARIA/Kontrast) schließen.  
- Packaging standardisieren (`make build`, `.deb/.tar.gz`, Checksums).

---

## Maßnahmenplan (Kurz)

1. Health-Monitor + UI-Alerts.  
2. Test-Suite (Unit/Integration/Replay).  
3. Retention-Policy + Alarme.  
4. Config-Governance (Schema, Version/Hash, ADR-Review).  
5. Forecast-Guardrails & Disable-Flag.  
6. Firewall-Profil (deny-all + Allowlist).  
7. A11y-Backlog umsetzen.  
8. Runbooks für Broker-Down, Übertemperatur, Zeitdrift, Low-Disk.

> Volltext mit DE/EN-Tabellen: `docs/architecture/11_risks_and_technical_debt.md`.
