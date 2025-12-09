# 07 – Deployment-Sicht / Deployment View

> **Kurzüberblick:**  
> Vollständig **lokal im geschlossenen LAN**: Core, Module, Explain-Agent, UI on-prem; Kommunikation via **MQTT/REST/WebSocket**; kein Cloud-Backend. Varianten: **Standalone**, **Distributed Local Network**, optional **Hybrid (verschlüsselte Spiegelung)**.

> **TL;DR (EN):**  
> Fully local in a closed LAN: core/modules/explain-agent/UI on-prem; MQTT/REST/WS; no cloud backend. Variants: standalone, distributed local, optional hybrid mirror.

---

## Zielarchitektur

```
[ PV / Storage / Sensoren ]
        → 
    [ modules/ ]
        → 
[ core + Explain-Agent ]
        ↔         →
   [ MQTT ]     [ ui/ ]
        →         →
 [ data/replay ] [ research node ]
```

> Local network only; MQTT broker + UI share state/logs; research node optional for exports/replays.

---

## Hardware & Software (Kurzfassung)

| Komponente | Beschreibung |
| --- | --- |
| **Controller / Edge Node** | Führt Core, Explain-Agent (on-device LLM) und UI aus. |
| **PV-Wechselrichter & Speicher** | liefern Daten für EnergyState; bleiben lokal erreichbar. |
| **Mining / Flexible Last** | Dynamischer Verbraucher, gesteuert über Core. |
| **MQTT Broker** | Lokaler Bus für State/Command/Explain-Events. |
| **Research/Replay Terminal** | Offline-Analyse, Export, KPI-Reports. |

| Software | Zweck |
| --- | --- |
| **Core (Python)** | Regel-Engine, BlockScheduler, Hodl-Policy. |
| **Module (Python/MQTT/Modbus)** | Adapter für Geräteintegration. |
| **UI (Svelte/HA-Frontend)** | Explainability, Overrides, Research-Toggle. |
| **Datenhaltung (SQLite/Parquet/JSON)** | Logging, KPIs, Replay Runner. |

---

## Betrieb & Hardening (Essentials)

- Minimal-OS (Debian/Ubuntu/RPi), nur notwendige Dienste.  
- Firewall **deny-all + Allowlist** (MQTT 1883, UI 8443).  
- **Stop → Safe** bei Sensor-/Netzfehler; USV für geordneten Shutdown.  
- `config/` + DB täglich sichern (Borg/Duplicati).  
- TLS optional; lokale Auth (HA-User); keine Telemetrie.

---

## Deployment-Varianten

| Variante | Einsatz |
| --- | --- |
| **Standalone** | Voller Stack auf Thin Client – Prototyping/Feldstudie. |
| **Distributed Local Network** | Core, Module, UI getrennt – A/B-Tests, Skalierung. |
| **Hybrid (optional)** | Verschlüsselte Datenspiegelung für Backup/Evaluation. |

---

## Netzwerkkonfiguration

- Protokolle: MQTT, REST, WebSocket **nur lokal**.  
- Statische Adressen / mDNS für UI & Research.  
- Privacy: kein Cloud-Backhaul, Research-Exports nur via Opt-in Toggle.

---

## Zusammenfassung

Deployment bleibt **lokal, energieeffizient und auditierbar**: offene Protokolle, minimierte Ports, klare Trennung zwischen Core, Adaptern, UI und Research-Knoten.
