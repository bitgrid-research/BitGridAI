# 051 – Blackbox-Sicht / Black Box View

> **Kurzüberblick:**  
> Äußere Schnittstellen von BitGridAI: was von außen sichtbar ist (Inputs/Outputs), nicht wie es innen umgesetzt ist. Fokus auf **lokale, erklärbare Steuerung** ohne Cloud.

> **TL;DR (EN):**  
> External interfaces of BitGridAI: what the system exposes/consumes, not the internals. Local, explainable control—no cloud.

---

## Systemgrenzen / System Boundaries

**Innerhalb von BitGridAI**
- Rule Engine (R1–R5) + BlockScheduler (10 Min)
- EnergyState (SSoT), Explain-Agent (on-device), Logging/KPIs, Research-Toggle
- Adapter für PV, Speicher, Smart Meter, Miner (MQTT/REST/Modbus)

**Außerhalb von BitGridAI**
- PV/Storage/Smart-Meter/Mining-Hardware
- Home Assistant Core, externe UIs
- Optionale lokale Forecast/Preis-Dienste

---

## Externe Inputs

- **Messdaten**: PV-Leistung, Netzimport/-export, SoC, Temperaturen (MQTT/Modbus/REST)
- **Preise/Forecasts**: lokale Datei/Dienst (R1/R4)
- **User-Commands**: Overrides (`POST /override`), Research-Toggle, UI-Feedback
- **Health-Signale**: Broker-/Adapter-Status

## Externe Outputs

- **Actuation**: `start/stop/set_power` an Miner/Relais (REST/MQTT)
- **Explainability**: DecisionEvents + Reason/Trigger/Params (WS/REST/MQTT `explain/events/#`)
- **State & Timeline**: `GET /state`, `GET /timeline`, MQTT `energy/state/#`
- **Research/Export**: Replay/Export-Bundles (Datei/REST, nur bei Opt-in)

---

## Vertragsartefakte / Contracts (Auswahl)

- **MQTT Topics**: `energy/state/#`, `miner/cmd/set`, `miner/state/#`, `explain/events/#`, `health/#`
- **REST Endpunkte** (lokal): `/state`, `/timeline`, `/preview`, `/override`, `/research/export`
- **Dateien/DB**: `data/bitgrid.sqlite`, `data/parquet/*.parq`, `config/*.yaml`, `explain/*.json`

> Blackbox: klar definierte Inputs/Outputs, alles lokal, auditierbar und erklärbar.
