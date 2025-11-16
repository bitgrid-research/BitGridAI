# 11 – Risiken und Technische Schulden / Risks and Technical Debt

> **Kurzüberblick:**
> 
> Bewertung entlang der BitGrid‑Leitplanken: **Local‑First**, **R1–R5**, **10‑Min‑BlockScheduler**, **EnergyState (SSoT)**, **Deadband**, **Privacy‑by‑Default**.
> Fokus: Betriebssicherheit (**Stop → Safe**), Datenkonsistenz, Erklärbarkeit, Wartbarkeit.

> **TL;DR (EN):**
> 
> Assessed against BitGrid guardrails: **local‑first**, **R1–R5**, **10‑min block scheduler**, **EnergyState (SSoT)**, **deadband**, **privacy‑by‑default**.
> Focus: operational safety (**stop → safe**), data consistency, explainability, maintainability.

---

## Überblick / Overview

Dieses Kapitel beschreibt identifizierte **Risiken** und bestehende **technische Schulden**. Ziel ist, Schwachstellen früh zu erkennen, Auswirkungen zu bewerten und **gezielte Gegenmaßnahmen** zu planen – ohne die Prinzipien **No‑Cloud**, **Explainable‑by‑Design** und **Nachhaltigkeit** zu verletzen.

> This chapter lists **risks** and existing **technical debt** with mitigation strategies, while preserving **no‑cloud**, **explainable‑by‑design**, and **sustainability** principles.

---

## Hauptrisiken / Key Risks

| Risiko                             | Beschreibung                                              | Wahrscheinlichkeit | Auswirkung | Gegenmaßnahme                                                                       |
| ---------------------------------- | --------------------------------------------------------- | ------------------ | ---------- | ----------------------------------------------------------------------------------- |
| **Hardwareausfall**                | Defekte Sensoren, Lüfterausfall am Miner, Pi‑Instabilität | Mittel             | Hoch       | Redundante Sensoren, **Health‑Monitor**, Auto‑Recovery, Thermal‑Alarme (R3/ADR‑015) |
| **MQTT‑Broker‑Ausfall**            | Unterbrochene Kommunikation Module↔Core                   | Hoch               | Mittel     | **Offline‑Puffer**, Retry/Backoff, Broker‑Watchdog, S3 „Offline‑Hold“ (ADR‑014)     |
| **Zeitdrift**                      | NTP‑Abweichungen → doppelte/fehlende Decisions            | Mittel             | Mittel     | **Drift‑Erkennung**, 1‑Block‑Hold & Re‑Sync (S10), UI‑Warnung (ADR‑006)             |
| **Fehlerhafte Regeldefinitionen**  | Inkonstente Parameter (S_THRESHOLD/P_MAX)                 | Mittel             | Mittel     | **Schema‑Validation**, Trockenlauf/Replay, Unit‑Tests R1–R5 (ADR‑007)               |
| **Forecast‑Fehler (R4)**           | Pre‑start zu früh/spät → Flapping/Verlust                 | Mittel             | Mittel     | σ‑Schwelle, Sicherheitsmarge, Priorität R2/R3>R4, schneller Disable (ADR‑011)       |
| **Deadband zu kurz/lang**          | Flapping oder Trägheit                                    | Mittel             | Mittel     | A/B‑Tests mit Replay, KPI‑Wache (Flapping↓), adaptive Empfehlung (ADR‑009)          |
| **Speicherüberlauf / Logwachstum** | Langzeit‑Logs füllen Datenträger                          | Niedrig            | Hoch       | Rotation/Archiv Parquet, Low‑Disk Alarm, Retention‑Policy                           |
| **UI‑Missverständnis**             | Erklärungen falsch interpretiert                          | Niedrig            | Mittel     | HCI‑Tests, Glossar‑Tooltips, „Warum?“-Dialog, A11y (ADR‑004)                        |
| **Sicherheitslücken (Ports)**      | Unnötige Dienste/Ports offen                              | Niedrig            | Hoch       | **Default‑Deny** Firewall, Port‑Cheatsheet, mTLS optional (ADR‑014)                 |
| **Modbus/Adapter‑Instabilität**    | Inverter/Smart‑Meter Timings                              | Mittel             | Mittel     | Adapter‑Timeouts, Circuit‑Breaker, Caching Frames                                   |
| **Hodl-Fehlparametrisierung**      | Falsches Energy-Path-Weighting → Liquiditäts-/Opportunitykosten | Mittel        | Mittel     | KPI-Governance (Energy→Sats, Traceability), Policy-Simulation, Double-Entry-Logs (ADR‑005/009) |
| **PoW-Regulatorik/Telemetrielücke**| Fehlende Hash-/Effizienzbelege → Compliance- oder Netzrisiken   | Niedrig        | Hoch       | Pflicht-Telemetrie & Hash-Sampling (ADR‑015), Alerts aus S12, exportierbarer Audit-Trail        |

> | Risk                     | Description                                      | Probability | Impact | Mitigation                                                                    |
> | ------------------------ | ------------------------------------------------ | ----------- | ------ | ----------------------------------------------------------------------------- |
> | **Hardware failure**     | Sensor faults, miner fan failure, Pi instability | Medium      | High   | Redundant sensors, health monitor, auto‑recovery, thermal alarms (R3/ADR‑015) |
> | **MQTT broker failure**  | Lost comms between modules and core              | High        | Medium | Offline buffer, retry/backoff, broker watchdog, S3 „offline hold“ (ADR‑014)   |
> | **Time drift**           | NTP skew → duplicate/missed decisions            | Medium      | Medium | Drift detection, 1‑block hold & re‑sync (S10), UI warning (ADR‑006)           |
> | **Invalid rule config**  | Inconsistent thresholds (S_THRESHOLD/P_MAX)      | Medium      | Medium | Schema validation, dry‑run/replay, unit tests R1–R5 (ADR‑007)                 |
> | **Forecast error (R4)**  | Pre‑start too early/late                         | Medium      | Medium | Sigma guard, safety margin, R2/R3>R4, quick disable (ADR‑011)                 |
> | **Deadband mis‑tuned**   | Flapping or sluggishness                         | Medium      | Medium | Replay A/B, KPI watch (flapping↓), adaptive hint (ADR‑009)                    |
> | **Storage overflow**     | Long‑term logs fill disk                         | Low         | High   | Rotation/archiving, low‑disk alarm, retention policy                          |
> | **UI misinterpretation** | Rationale misunderstood                          | Low         | Medium | HCI tests, glossary tooltips, “Why?” dialog, a11y (ADR‑004)                   |
> | **Open ports**           | Unneeded services exposed                        | Low         | High   | Default‑deny firewall, port cheatsheet, mTLS optional (ADR‑014)               |
> | **Adapter instability**  | Inverter/smart‑meter timing                      | Medium      | Medium | Timeouts, circuit breaker, frame caching                                      |
> | **Hodl policy misconfiguration** | Wrong energy-path weighting ? liquidity/opportunity loss | Medium | Medium | KPIs (energy?sats, traceability), policy simulation, double-entry logs (ADR-005/009) |
> | **PoW compliance/telemetry gap** | Missing hash/efficiency proof ? regulatory or grid risk | Low | High | Mandatory telemetry + hash sampling (ADR-015), alerts from S12, exportable audit trail |
---

## Technische Schulden / Technical Debt

| Bereich                 | Beschreibung                                | Risiko              | Gegenmaßnahme                                                      |
| ----------------------- | ------------------------------------------- | ------------------- | ------------------------------------------------------------------ |
| **Adapter‑Modularität** | Einige Geräteadapter eng mit Core gekoppelt | Erweiterungsaufwand | Plugin‑Architektur, Ports/Adapter strikt halten                    |
| **Logging‑Schema**      | Uneinheitliche Event‑Payloads               | Analysefehler       | Zentrales Eventschema (`DecisionEvent`, `EnergyStateChangedEvent`) |
| **Testabdeckung**       | MQTT/Rule‑Integrationstests fehlen          | Regressionen        | Test‑Harness mit simulierten Topics + Replay (Kap. 10)             |
| **Forecast‑Baseline**   | Einfache Heuristik                          | Startqualität       | Lokaler Forecast‑Evaluator mit σ‑Kriterium (ADR‑011)               |
| **A11y/UI**             | Barrierefreiheit unvollständig              | Usability           | Tastatur‑Navi, ARIA‑Labels, Kontrast‑Check                         |
| **Konfig‑Drift**        | YAMLs ohne Version/Hash                     | Reproduzierbarkeit  | Config‑Version + Hash im UI                                        |
| **Telemetry‑Checks**    | Keine automatische Prüfung                  | Privacy‑Leak        | „External‑Conn = 0“‑Wächter                                        |
| **Packaging**           | Uneinheitliche Deploy‑Artefakte             | Ops‑Overhead        | `make build`, `.deb`/`.tar.gz`, Checksums                          |

> | Area                   | Description                          | Risk             | Mitigation                                              |
> | ---------------------- | ------------------------------------ | ---------------- | ------------------------------------------------------- |
> | **Adapter modularity** | Some device adapters tightly coupled | Extension effort | Plugin architecture; strict ports/adapters              |
> | **Logging schema**     | Inconsistent event payloads          | Analysis errors  | Unified schema (DecisionEvent, EnergyStateChangedEvent) |
> | **Test coverage**      | Missing MQTT/rule integration tests  | Regressions      | Test harness with simulated topics + replay             |
> | **Forecast baseline**  | Simple heuristic                     | Start quality    | Local evaluator with sigma criterion                    |
> | **A11y/UI**            | Accessibility incomplete             | Usability        | Keyboard nav, ARIA labels, contrast checks              |
> | **Config drift**       | No version/hash                      | Reproducibility  | Config version + hash in UI                             |
> | **Telemetry checks**   | No automatic audit                   | Privacy leak     | „External‑Conn = 0“ watchdog                            |
> | **Packaging**          | Mixed deployment artifacts           | Ops overhead     | Unified builds + checksums                              |

---

## Risikoanalyse / Risk Analysis

| Kategorie             | Beschreibung                                   | Priorität |
| --------------------- | ---------------------------------------------- | --------- |
| **Betrieblich**       | Hardware‑/Netz‑Stabilität, Stromausfälle       | Hoch      |
| **Technisch**         | Modularität, Tests, Adapter‑Robustheit         | Hoch      |
| **Organisatorisch**   | Doku‑Lücken, begrenzte Kapazität               | Mittel    |
| **Forschungsbezogen** | Validität Nachhaltigkeits‑Metriken, UX‑Messung | Mittel    |

> | Category             | Description                                        | Priority |
> | -------------------- | -------------------------------------------------- | -------- |
> | **Operational**      | Hardware/network stability, power loss             | High     |
> | **Technical**        | Modularity, tests, adapter robustness              | High     |
> | **Organizational**   | Documentation gaps, limited capacity               | Medium   |
> | **Research‑related** | Validity of sustainability metrics, UX measurement | Medium   |

---

## Maßnahmenplan / Mitigation Plan

1. **Health‑Monitor** (Broker/Sensor/Miner) inkl. UI‑Alerts & Auto‑Recovery.
2. **Test‑Suite**: Unit (R1–R5), Integration (MQTT→Decision→Actuation), Replay‑Runner.
3. **Retention‑Policy**: Parquet‑Archiv, Low‑Disk‑Alarme, wöchentliche Rotation.
4. **Config‑Governance**: YAML‑Schema‑Validation, Version/Hash, ADR‑Review.
5. **Forecast‑Guardrails**: σ‑Schwelle, Margin, schneller Disable/Tuning.
6. **Firewall‑Profile**: Default‑Deny, Port‑Cheatsheet, regelmäßiger Portscan (lokal).
7. **A11y‑Backlog**: Kontrast, Keyboard, Screenreader‑Labels; HCI‑Tests.
8. **Runbooks**: „Broker down“, „Übertemperatur“, „Zeitdrift“, „Low‑Disk“ – Schritt‑für‑Schritt.

> 1) **Health monitor** with UI alerts & auto‑recovery.
> 2) **Test suite** (unit/integration/replay).
> 3) **Retention policy** with archive & low‑disk alarms.
> 4) **Config governance** (schema/version/hash/ADR review).
> 5) **Forecast guardrails** (sigma/margin/quick disable).
> 6) **Firewall profiles** (default‑deny, port cheatsheet).
> 7) **A11y backlog** (contrast/keyboard/screenreader).
> 8) **Runbooks** for frequent incidents.

---

## Frühe Warnindikatoren / Early Warning Indicators

* **Switches/h** ↑ trotz Deadband → Schwellen prüfen (R5).
* **Override‑Rate** ↑ → Regeln/Erklärungen unklar (ADR‑004/010).
* **Thermal‑Near‑Max** häufig → Lüfter/Staub/Leistungslevel anpassen (ADR‑015).
* **External‑Conn > 0** → Privacy‑Leak prüfen (ADR‑014).
* **Time‑Drift Events** → NTP/Lokalzeit prüfen; Hardware‑Clock defekt?

> **Signals:** switches/h up, override rate up, frequent thermal near‑max, any external connections, repeated time‑drift events.

---

## Traceability (Risiken ↔ Szenarien ↔ ADRs)

| Risiko             | Szenarien (Kap. 10) | ADR         |
| ------------------ | ------------------- | ----------- |
| MQTT‑Ausfall       | S3                  | ADR‑014     |
| Zeitdrift          | S10                 | ADR‑006     |
| Forecast‑Fehler    | S9                  | ADR‑011     |
| Übertemperatur     | S6                  | ADR‑015     |
| Low SoC            | S7                  | ADR‑015     |
| Flapping           | S8                  | ADR‑009     |
| UI‑Missverständnis | S1/S4               | ADR‑004/010 |
| Hodl-Traceability  | S11                 | ADR‑005/009 |
| PoW-Telemetrie     | S12                 | ADR‑015     |

---

## Zusammenfassung / Summary

Risikomanagement sichert **Stabilität, Erklärbarkeit und Nachhaltigkeit** im Betrieb. Durch gezielte Gegenmaßnahmen, Tests und klare Runbooks bleibt BitGridAI **lokal, auditierbar und vertrauenswürdig** – im Sinne der Ziele aus **01/04** und der ADRs **001–017**.

> Risk management preserves **stability, explainability, and sustainability** while keeping BitGridAI **local, auditable, and trustworthy**—aligned with goals from **01/04** and ADRs **001–017**.

*Weiter mit **[12 – HCI‑Perspektive / HCI Perspective](./12_hci_perspective.md)**.*
