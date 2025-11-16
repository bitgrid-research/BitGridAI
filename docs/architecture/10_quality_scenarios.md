# 10 – Qualitätsszenarien / Quality Scenarios

> **Kurzüberblick:**
> 
> Szenarien validieren **Transparenz, Erklärbarkeit, Nachhaltigkeit, Resilienz, Vorhersagbarkeit**.
> Geprüft werden **R1–R5**, **10‑Min‑BlockScheduler**, **EnergyState (SSoT)**, **Deadband**, **Override‑TTL**, **Safety (Stop → Safe)**.

> **TL;DR (EN):**
> 
> Scenarios validate **transparency, explainability, sustainability, resilience, predictability**.
> We test **R1–R5**, **10‑min block scheduler**, **EnergyState (SSoT)**, **deadband**, **override TTL**, **safety (stop → safe)**.

---

## Überblick / Overview

Dieses Kapitel beschreibt Qualitätsszenarien, die das Verhalten von BitGridAI in realen Betriebssituationen definieren. Die Szenarien überprüfen, ob die Architektur die Kernziele – **Transparenz, Erklärbarkeit, Nachhaltigkeit, Resilienz** – erfüllt.

> This chapter defines quality scenarios describing BitGridAI’s behaviour under real‑world conditions. They verify whether the architecture achieves its core goals – **transparency, explainability, sustainability, resilience**.

---

## Zielqualitäten / Quality Attributes

| Qualität                | Beschreibung                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------- |
| **Transparenz**         | Alle Entscheidungen sind nachvollziehbar und begründet (Reason/Trigger/Parameter). |
| **Erklärbarkeit**       | Nutzer verstehen Systemverhalten in Echtzeit (UI‑Timeline, Next‑Block‑Preview).    |
| **Nachhaltigkeit**      | Verbrauch passt sich an PV‑Erzeugung/Preis an (Surplus, R1/R4).                    |
| **Datenschutz**         | Keine externen Datenströme; Local‑First; minimale Ports.                           |
| **Resilienz**           | Betrieb bei Teilfehlern (Sensor‑Stale, Broker‑Ausfall) gesichert.                  |
| **Vorhersagbarkeit**    | Deterministische Regeln, 10‑Min‑Blöcke, Deadband/Anti‑Flapping.                    |
| **Erweiterbarkeit**     | Module ohne Kernänderungen integrierbar (Adapter).                                 |
| **Benutzbarkeit (HCI)** | UI fördert Vertrauen, Kontrolle, Overrides.                                        |
| **Sicherheit**          | Stop → Safe bei SoC/Temperatur; Hysterese.                                         |

> | Quality             | Description                                                  |
> | ------------------- | ------------------------------------------------------------ |
> | **Transparency**    | Decisions are explainable with reason/trigger/parameters.    |
> | **Explainability**  | Real‑time understanding (timeline, next‑block preview).      |
> | **Sustainability**  | Consumption adapts to PV/price (surplus, R1/R4).             |
> | **Privacy**         | No outbound data; local‑first; minimal open ports.           |
> | **Resilience**      | Operates under partial failures (sensor stale, broker down). |
> | **Predictability**  | Deterministic rules, 10‑min blocks, deadband/anti‑flapping.  |
> | **Extensibility**   | New modules via adapters; no core changes.                   |
> | **Usability (HCI)** | UI promotes trust, control, overrides.                       |
> | **Safety**          | Stop → Safe on SoC/temperature with hysteresis.              |

---

## Szenario‑Template / Scenario Template

**Struktur:** *Preconditions · Stimulus · Environment · Response · Response Measure · Logs/Events · UI*

> **Structure:** *Preconditions · Stimulus · Environment · Response · Response Measure · Logs/Events · UI*

---

## S1 – Transparente Entscheidungsbegründung (Explainability)

**Preconditions**: Live‑Daten aktiv; UI verbunden.
**Stimulus**: PV‑Leistung ↑ führt zu `surplus` ≥ **1.5 kW**, Preis ≤ **18 ct**.
**Environment**: normal; keine Deadband‑Sperre.
**Response**: **R1 start**; DecisionEvent mit Reason/Trigger/Parameter; Timeline‑Eintrag.
**Response Measure**: **Explanation Latency** < **2 s** nach Decision.
**Logs/Events**: `DecisionEvent{reason=R1, trigger={surplus, price}}`.
**UI**: Toast „**Start (R1)** … Deadband bis +2“ + Next‑Block‑Preview.

---

## S2 – Energieadaptive Steuerung (Sustainability)

**Preconditions**: Mining läuft; Deadband nicht aktiv.
**Stimulus**: `surplus` fällt **unter 1.5 kW** oder Preis > **18 ct**.
**Environment**: normal.
**Response**: **stop** (R1 Bedingung entfällt); Begründung dokumentiert.
**Response Measure**: **Grid‑Import↓** vs. Baseline; **Flapping↓** um ≥ **Y %**.
**Logs/Events**: DecisionEvent `stop`, EnergyState Snapshot.
**UI**: Erklärung „Unter Schwelle – Stop“.

---

## S3 – Lokale Fehlertoleranz (Resilience)

**Preconditions**: Normalbetrieb.
**Stimulus**: MQTT‑Broker kurzzeitig **down** oder Netzverlust.
**Environment**: offline; Sensor‑Frames fehlen.
**Response**: **hold** (R5) bis `valid_until`; Logs **puffern**; UI Warnhinweis.
**Response Measure**: **System Availability** > **99 %**; kein ungeplanter Stop durch Kommunikationsfehler.
**Logs/Events**: Health‑Event `broker_down`; später `broker_up`.
**UI**: Banner „Offline‑Puffer aktiv“.

---

## S4 – Nutzer‑Override (HCI)

**Preconditions**: Mining **stop**, Block läuft.
**Stimulus**: User `POST /override {action=start, ttl=1 block}`.
**Environment**: normal; **R2/R3** okay.
**Response**: **start** bis Blockende; Reason=`manual_override`; Countdown.
**Response Measure**: **Override‑Latency** < **300 ms**; Auto‑Rollback am Blockende.
**Logs/Events**: DecisionEvent `manual_override`.
**UI**: Chip „Override (00:xx)“.

---

## S5 – Erweiterung durch neues Modul (Extensibility)

**Preconditions**: Core läuft.
**Stimulus**: Neues Modul publiziert auf `energy/state/…` oder registriert Device‑Topics.
**Environment**: gleichbleibend.
**Response**: Core **konsumiert** Daten ohne Neustart; neue Felder optional ignoriert.
**Response Measure**: **Hot‑plug success**; **Zero‑downtime**.
**Logs/Events**: Adapter‑Register‑Event.
**UI**: neues Gerät sichtbar.

---

## S6 – Safety‑Stop bei Temperatur (R3)

**Preconditions**: Mining läuft.
**Stimulus**: `t_miner ≥ T_MAX` (z. B. 75 °C).
**Environment**: normal.
**Response**: **sofort stop**; Deadband ignorieren; Resume erst `t_miner ≤ T_RESUME`.
**Response Measure**: **Thermal‑Incidents** = **0** (ungeplante Übertemperatur).
**Logs/Events**: DecisionEvent `R3 over_temp`.
**UI**: Alarm + Handlungshinweis.

---

## S7 – Autarkie‑Schutz bei SoC (R2)

**Preconditions**: Mining läuft; SoC sinkt.
**Stimulus**: `soc ≤ SOC_MIN` (z. B. 25 %).
**Environment**: normal.
**Response**: **stop/block**; erst `soc ≥ SOC_RESUME` wieder **start**.
**Response Measure**: **Self‑supply preserved**; keine Tiefentladung.
**Logs/Events**: DecisionEvent `R2 low_soc`.
**UI**: Hinweis „Autarkie‑Schutz aktiv“.

---

## S8 – Deadband‑Stabilität (R5)

**Preconditions**: Grenzbereich um Schwelle.
**Stimulus**: `surplus` rauscht ±0.2 kW um **1.5 kW**.
**Environment**: normal.
**Response**: **hold** für `D` Blöcke; nur R2/R3 dürfen brechen.
**Response Measure**: **Switches/h** ↓ um ≥ **Y %** ggü. Baseline.
**Logs/Events**: `DeadbandActivatedEvent`.
**UI**: Badge „Stabilisierung aktiv“.

---

## S9 – Prognose‑Start (R4)

**Preconditions**: Mining stop; Forecast lokal verfügbar.
**Stimulus**: **stabile** `forecast_surplus` für `N` Blöcke; `margin ≥ 0.3 kW`.
**Environment**: normal; Preis ≤ **P_MAX**.
**Response**: **pre‑start** → **start** zu Blockbeginn.
**Response Measure**: **Abgebrochene Starts** ↓; **Ertrag↑** ohne zusätzliche Flaps.
**Logs/Events**: DecisionEvent `R4 forecast_start`.
**UI**: Preview „Start im nächsten Block“.

---

## S10 – Zeitdrift & Re‑Sync

**Preconditions**: Betrieb; NTP driftet.
**Stimulus**: Drift > Δt.
**Environment**: normal.
**Response**: **hold 1 block**, Re‑Sync, dann normal; Hinweis im UI.
**Response Measure**: Keine Doppel‑Decisions im selben Block.
**Logs/Events**: `time_drift_detected`, `resynced`.

---

## Bewertung / Evaluation Criteria

| Kriterium                 | Metrik / Beobachtung          | Zielwert     |
| ------------------------- | ----------------------------- | ------------ |
| **Explanation Latency**   | Decision → UI‑Erklärung       | < **2 s**    |
| **Decision Latency**      | Block‑Tick → Decision         | < **300 ms** |
| **State Propagation**     | Sensor → EnergyState          | < **500 ms** |
| **Grid‑Import↓**          | (Baseline − Trial)/Baseline   | ≥ **X %**    |
| **Flapping↓**             | Switches/h ggü. Baseline      | ≥ **Y %**    |
| **Explanation Coverage↑** | Decisions mit Reason / alle   | ≥ **Z %**    |
| **Trust‑Score↑**          | Nutzerstudie (Likert)         | ≥ **T/5**    |
| **Thermal‑Incidents**     | ungeplante Übertemperaturen   | **0**        |
| **Privacy Check**         | erkannte externe Verbindungen | **0**        |

> Werte **X/Y/Z/T** projektspezifisch aus **01/04/08** ableiten.

---

## Testdaten & Replay / Test Data & Replay

* **Replay‑Runner** liest Parquet/SQLite und spielt Frames in Echtzeit/Accelerated ab.
* **Ziel**: deterministische Reproduktion; Vergleich Baseline ↔ Regel‑Varianten.
* **Artefakte**: `data/parquet/*.parq`, `data/bitgrid.sqlite`, `config/*.yaml`.

```bash
# Beispiel CLI
bitgrid-replay \
  --state data/parquet/2025-11-*.parq \
  --config config/rules.yaml \
  --speed 10x \
  --kpi out/kpi_report.json
```

---

## S11 � Hodl-Entscheidung & Traceability

**Preconditions**: `surplus = 1.5?kW`, BlockScheduler aktiv, Hodl-Policy = *local-first*.
**Stimulus**: Block-Tick triggert Energy-Path-Bewertung; Exportpreis < Grenzwert, Hodl erlaubt.
**Environment**: Keine Safety-Hits (R2/R3); Deadband frei.
**Response**: DecisionEvent enth�lt `preferred_path=hodl`, `rejected_path=export`, `sats_per_kWh`; Miner-Level wird innerhalb Blockfenster gesetzt.
**Response Measure**: 100?% der Energy-Path-Entscheidungen erzeugen Logeintrag (`energy_to_value`) < **500?ms**; UI zeigt Alternativvergleich.
**Logs/Events**: `energy_path_decision{block_id, preferred_path, sats_per_kWh}`, `energy_to_value.append`.
**UI**: Research-Panel mit Blockzeit, sats/kWh, Hinweis �Export verworfen (Preis < Schwelle)�.

---

## S12 � Proof-of-Work Telemetrie & Sicherheit

**Preconditions**: Mining aktiv; Telemetrie (`hashrate`, `efficiency`, `t_miner`) verf�gbar.
**Stimulus**: Effizienz driftet > **5?%** vom Ziel oder Temperatur n�hert sich `T_MAX - 2?�C`.
**Environment**: Normalbetrieb; keine weiteren Faults.
**Response**: Miner-Controller limitiert Leistung oder sendet `stop`; DecisionEvent dokumentiert `pow_hash_sample`; R3 l�st ggf. Stop ? Safe aus.
**Response Measure**: Reaktion < **2?s** nach Telemetrie-Anomalie; Temperatur bleibt < `T_MAX`; Hashprobe protokolliert.
**Logs/Events**: `telemetry_warning{metric=efficiency}`, `DecisionEvent{reason=R3, pow_hash_sample=...}`.
**UI**: Warnkarte �PoW Effizienzabweichung � Leistung limitiert� mit Link zur Hashprobe.

---
## Traceability‑Matrix (ADR ↔ Szenarien ↔ KPIs)

| Szenario | ADR‑Bezug                                    | KPIs                    |
| -------- | -------------------------------------------- | ----------------------- |
| S1, S4   | ADR‑004 (Explainability), ADR‑010 (Override) | Coverage↑, Trust↑       |
| S2, S9   | ADR‑005 (Sustainability), ADR‑011 (Forecast) | Grid‑Import↓, Flapping↓ |
| S3, S10  | ADR‑014 (Privacy/Local), ADR‑006 (Block)     | Availability↑           |
| S6, S7   | ADR‑015 (Safety), ADR‑007 (Rules)            | Thermal=0, Self‑supply  |
| S8       | ADR‑009 (Deadband)                           | Flapping↓               |
| S11      | ADR??'005/009 (Energy-Path Policies)           | Energy?Sats, Traceability |
| S12      | ADR??'015 (Safety)                             | PoW-Sicherheit, Thermal  |
---

## Akzeptanzkriterien (MVP) / Acceptance Criteria (MVP)

* **100 % Explanation Coverage** für Decisions im Testfenster.
* **Flapping↓** um ≥ **Y %** ggü. Baseline.
* **Thermal‑Incidents = 0**.
* **Privacy Check = 0** externe Verbindungen.
* **Trust‑Score ≥ T/5** in Nutzerstudie.

---

## Zusammenfassung / Summary

Die Szenarien beweisen, dass BitGridAI **funktional korrekt** und zugleich **vertrauenswürdig, effizient und erklärbar** arbeitet – im Sinne der Ziele aus **01/04** und der Prinzipien **Local‑First / No Cloud / Explainable by Design**.

> The scenarios demonstrate that BitGridAI is **functionally correct** and **trustworthy, efficient, explainable**—aligned with goals from **01/04** and principles **local‑first / no cloud / explainable by design**.

*Weiter mit **[11 – Risiken & Technische Schulden / Risks and Technical Debt](./11_risks_and_technical_debt.md)**.*
