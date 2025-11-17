# 07 – Verteilungssicht / Deployment View

> **Kurzüberblick:**
> 
> Lokal verteilter Stack im **geschlossenen LAN**: Core, Module und UI **on-prem**; Kommunikation über **MQTT/REST/WebSocket**; **kein Cloud-Backend**. Betriebsvarianten: **Standalone**, **Distributed Local Network**, **Hybrid (optional, verschlüsselte Spiegelung)**.

> **TL;DR (EN):**
> 
> Locally distributed stack in a **closed LAN**: core, modules, and UI **on-prem**; communication via **MQTT/REST/WebSocket**; **no cloud backend**.  
> Deployment variants: **standalone**, **distributed local network**, **hybrid (optional, encrypted mirroring)**.

---

## Überblick / Overview

Die Verteilungssicht beschreibt, wie BitGridAI auf Hardware- und Netzebene installiert und betrieben wird.
Das System ist vollständig **lokal ausführbar** und benötigt keine permanente Cloud-Anbindung.
Alle Komponenten kommunizieren innerhalb eines **geschlossenen lokalen Netzwerks**, um Datenschutz, Energieeffizienz und Kontrolle zu gewährleisten.

> The deployment view describes how BitGridAI is installed and operated at hardware and network level.
> The system runs **fully locally** and requires no persistent cloud connection.
> All components communicate within a **closed local network**, ensuring privacy, energy efficiency, and user control.

---

## Zielarchitektur / Target Architecture

```
+----------------------------------------------------------------+
|                        Lokales Netzwerk                        |
|----------------------------------------------------------------|
|  [ PV-Wechselrichter ]   [ Speicher ]      [ Mining / Flexible ]|
|          ↓                     ↓                   ↓            |
|        [ modules/ ] → [ core + Explain-Agent ] ← [ MQTT Broker ]|
|                  ↓             ↓                ↓              |
|         [ data/ + replay ]   [ ui/ ]        [ research node ]  |
|                  ↓                                   ↓         |
|          [ Nutzer / Dashboard ]          [ Research Toggle ]   |
+----------------------------------------------------------------+
```

> ```
> +----------------------------------------------------------------+
> |                         Local Network                          |
> |----------------------------------------------------------------|
> |  [ PV inverter ]       [ storage ]        [ miner/flex load ]  |
> |          ↓                     ↓                   ↓           |
> |        [ modules/ ] → [ core + Explain-Agent ] ← [ MQTT broker ]|
> |                  ↓             ↓                ↓             |
> |      [ data + replay ]      [ ui/ ]        [ research node ]  |
> |                  ↓                                   ↓        |
> |        [ user / dashboard ]             [ research toggle ]   |
> +----------------------------------------------------------------+
> ```

---

## Hardwareumgebung / Hardware Environment

| Komponente                              | Beschreibung                                        | Energiebezug           |
| --------------------------------------- | --------------------------------------------------- | ---------------------- |
| **Controller / Edge Node**              | Führt Core, Explain-Agent (On-Device-LLM) und UI aus| Lokale Versorgung / PV |
| **PV-Wechselrichter**                   | Liefert Leistungsdaten                              | Erzeugt PV-Energie     |
| **Energiespeicher**                     | Puffert Überschussenergie                           | Lokale Kapazität       |
| **Mining Node / Flexible Last**         | Dynamischer Energieverbraucher                      | Regelbar über Core     |
| **Research/Replay Terminal**            | Offline-Analyse, Export, KPI-Reports                | Lokale Versorgung      |
| **Nutzergerät (Tablet, Browser)**       | Zugriff auf Erklärschnittstelle & Research-Toggle   | WLAN / LAN lokal       |

> | Component                             | Description                    | Power Source        |
> | ------------------------------------- | ------------------------------ | ------------------- |
> | **Controller** | Runs core, modules, and UI     | Local supply / PV   |
> | **PV Inverter**                       | Provides power data            | Generates PV energy |
> | **Energy Storage**    | Buffers surplus energy         | Local capacity      |
> | **Mining Node / Flexible Load**       | Dynamic energy consumer        | Controlled by Core  |
> | **User Device (Tablet, Browser)**     | Accesses explanation interface | Local WLAN / LAN    |

---

## Softwareumgebung / Software Environment

| Komponente              | Technologie                                    | Beschreibung                                   |
| ----------------------- | ---------------------------------------------- | ---------------------------------------------- |
| **Core**                | Python                                         | Regel-Engine, BlockScheduler, Hodl-Policies    |
| **Explain-Agent**       | On-Device LLM / Transformers (quantisiert)     | Microcopy & What-if-Erklärungen, läuft offline |
| **Module**              | Python / MQTT / Modbus                         | Adapter für Geräteintegration                  |
| **Datenhaltung**        | SQLite / Parquet / JSON                        | Logging, KPIs, Replay Runner                   |
| **Erklärschnittstelle** | Svelte/Tailwind oder Home Assistant Frontend   | Visualisierung, Overrides, Research-Toggle     |
| **Betriebssystem**      | Raspberry Pi OS / Debian / Ubuntu Server       | Lokaler Edge-Betrieb                           |

> | Component                 | Technology                                   | Description                     |
> | ------------------------- | -------------------------------------------- | ------------------------------- |
> | **Core**                  | Python                                       | Rule engine and decision logic  |
> | **Modules**               | Python / MQTT                                | Adapters for device integration |
> | **Database**              | SQLite / JSON                                | Local logging and replay        |
> | **Explanation Interface** | Svelte / Tailwind or Home Assistant frontend | Visualization and feedback      |
> | **Operating System**      | Raspberry Pi OS / Linux                      | Local edge deployment           |

---

## Betriebssystem & Hardening (ergänzt)

| Ebene | Maßnahme | Tools / Hinweise |
| --- | --- | --- |
| **OS** | Minimal-Image (Debian 12 / Ubuntu 24.04 LTS). Nur `openssh`, `python`, `mosquitto`, `bitgrid-core`. | `ansible/playbooks/os_hardening.yml` |
| **Netzwerk** | Dediziertes LAN bzw. IoT-VLAN mit Firewall „deny all“ + Allowlist (MQTT 1883, UI 8443). | `ufw`/`nftables`; getrennte Segmente wie im Deployment-Setup für HA/IoT. |
| **Fail-Safe** | Miner geht OFF bei Sensor- oder Netzwerkfehler (Safety-Design). | Studien-Template „Fail-Safe-Design“. |
| **USV-Integration** | Geordneter Shutdown bei Stromausfall. | USV-Add-on triggert Stop-Sequenz. |
| **Secrets** | Keine Cloud-Keys; `.env` → `chmod 600`; SSH via ed25519/YubiKey. | `setup/scripts/lockdown.ps1`. |
| **Updates** | Rolling Updates nach bestandenem Replay + Wartungsplan (HA, Unraid, Miner). | „Updates & Wartung“-Playbook, `bin/apply-config`. |
| **Monitoring** | `healthd` (CPU/Temp/Disk) + Shelly Plug & Temp-Sensor aus Deployment-Rig. | MQTT `health/#`, Hardware-Sensoren. |
| **Backup** | Tägliches DB-/Config-Backup. | Borg/Duplicati Jobs. |
| **Security Docs** | security.txt, HSTS, TLS überall, Responsible Disclosure. | Hinweise aus Security-Kapitel. |

---

## Ressourcen & Performance Budgets (ergänzt)

| Komponente | Minimum | Empfehlung | Notizen |
| --- | --- | --- | --- |
| **Edge Node / Controller** | 4 vCPU, 4 GB RAM, 64 GB SSD | 6 vCPU, 8 GB RAM, 256 GB NVMe | LLM (Mistral 7B ~3 GB RAM); Unraid-Server im Keller-Rig möglich |
| **MQTT Broker** | 1 vCPU, 512 MB RAM | 2 vCPU, 1 GB RAM | Co-located oder separat |
| **Home Assistant / Unraid** | 2 vCPU, 2 GB RAM | 4 vCPU, 4 GB RAM | Deployment-Rig nutzt Unraid + HA-Add-ons |
| **Netzwerk** | 1 GbE / WiFi6 | 1 GbE kabelgebunden | VLAN-Trennung (IoT) empfohlen |
| **Power Budget** | < 25 W Idle | < 40 W Peak | USV Pflicht |
| **Sensorik** | — | Shelly Plug + Temp-Sensor | Aus Hardware-Setup |
| **Storage Throughput** | 50 MB/s | 150 MB/s NVMe | Für Replay/Exports |
| **LLM-Runtime** | — | 3 GB RAM + 1 vCPU | Local-first Mistral |
| **Backup-System** | — | Borg/Duplicati | tägliche Jobs |

Performance-Grenzen spiegeln UI-Budgets (Kap. 13) und Laufzeitpfade (Kap. 06). Deployment-Playbooks (`setup/ansible/*`) führen `scripts/post_deploy_check.py` nach jedem Rollout aus.

## Deployment-Varianten / Deployment Variants

| Variante                      | Beschreibung                                      | Einsatz                                  |
| ----------------------------- | ------------------------------------------------- | ---------------------------------------- |
| **Standalone**                | Kompletter Stack auf einem Thin Client           | Prototyping, Forschung, lokale Steuerung |
| **Distributed Local Network** | Core, Explain-Agent, Module und UI auf getrennten Geräten | Skalierte Forschungsumgebungen, A/B-Tests |
| **Hybrid Mode**               | Optionale externe Datenspiegelung (verschlüsselt)       | Vergleichende Evaluationen / Backup      |

> | Variant                       | Description                                  | Use Case                             |
> | ----------------------------- | -------------------------------------------- | ------------------------------------ |
> | **Standalone**                | Full stack on a single thin client          | Prototyping, research, local control |
> | **Distributed Local Network** | Core, modules, and UI on separate devices    | Scaled research setups               |
> | **Hybrid Mode**               | Optional external data mirroring (encrypted) | Comparative evaluation / backup      |

---

## Netzwerkkonfiguration / Network Configuration

* **Protokolle:** MQTT, REST, WebSocket (ausschließlich lokal)
* **Sicherheit:** TLS optional, lokale Firewall aktiv
* **Adressierung:** statisch (z. B. `192.168.178.50`), mDNS für UI und Research-Panel
* **Datenschutz & Forschung:** Research-Toggle steuert Export; keine Cloud-Synchronisation; Replay-Files bleiben lokal

> - **Protocols:** MQTT, REST, WebSocket (local only)
> - **Security:** optional TLS, local firewall active
> - **Addressing:** static (e.g., `192.168.178.50`)
> - **Privacy:** no telemetry, no cloud synchronization

---

## Nachhaltigkeit und Datenschutz / Sustainability and Privacy

* **Energieeffizienter Betrieb:** Core und Module laufen auf stromsparender Hardware
* **Autarke Infrastruktur:** Lokale Speicherung aller Logs, Modelle und Konfigurationen
* **Transparente Datenhaltung:** Jede Entscheidung ist auditierbar
* **Keine Abhängigkeiten:** Kein zentraler Server oder Drittanbieter-Dienst erforderlich

> - **Energy-efficient operation:** Core and modules run on low-power hardware
> - **Autonomous infrastructure:** All logs, models, and configurations are stored locally
> - **Transparent data handling:** Every decision is auditable
> - **No dependencies:** No central server or third-party API required

---

## Zusammenfassung / Summary

Die Verteilungssicht zeigt BitGridAI als **lokal verteiltes, energieautonomes System**,
das physische Geräte, digitale Logik und menschliche Interaktion sicher und nachvollziehbar verbindet.
Durch lokale Netzwerke, offene Protokolle und minimalistische Hardware bleibt das System effizient, kontrollierbar und vollständig transparent.

> The deployment view presents BitGridAI as a **locally distributed, energy-autonomous system**
> connecting physical devices, digital logic, and human interaction in a secure and transparent way.
> Through local networks, open protocols, and minimalist hardware, the system remains efficient, controllable, and fully transparent.

*Weiter mit **[08 Konzepte / Concepts](./08_concepts.md)**.*
