# 07 – Verteilungssicht / Deployment View

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
+------------------------------------------------------+
|                    Lokales Netzwerk                  |
|------------------------------------------------------|
|  [ PV-Wechselrichter ]     [ Speicher ]              |
|          ↓                        ↓                  |
|        [ modules/ ] → [ core/ ] ← [ MQTT Broker ]    |
|                  ↓             ↓                     |
|            [ data/ ]       [ ui/ ]                   |
|                  ↓                                   |
|          [ Nutzer / Dashboard ]                |
+------------------------------------------------------+
```

> ```
> +------------------------------------------------------+
> |                    Local Network                     |
> |------------------------------------------------------|
> |  [ PV Inverter ]           [ Storage Unit ]          |
> |          ↓                        ↓                  |
> |        [ modules/ ] → [ core/ ] ← [ MQTT Broker ]    |
> |                  ↓             ↓                     |
> |            [ data/ ]       [ ui/ ]                   |
> |                  ↓                                   |
> |          [ User / Local Dashboard ]                  |
> +------------------------------------------------------+
> ```

---

## Hardwareumgebung / Hardware Environment

| Komponente                              | Beschreibung                    | Energiebezug           |
| --------------------------------------- | ------------------------------- | ---------------------- |
| **Controller**   | Führt Core, Module und UI aus   | Lokale Versorgung / PV |
| **PV-Wechselrichter**                   | Liefert Leistungsdaten          | Erzeugt PV-Energie     |
| **Energiespeicher**     | Puffert Überschussenergie       | Lokale Kapazität       |
| **Mining Node / Flexibler Verbraucher** | Dynamischer Energieverbraucher  | Regelbar über Core     |
| **Nutzergerät (Tablet, Browser)**       | Zugriff auf Erklärschnittstelle | WLAN / LAN lokal       |

> | Component                             | Description                    | Power Source        |
> | ------------------------------------- | ------------------------------ | ------------------- |
> | **Controller** | Runs core, modules, and UI     | Local supply / PV   |
> | **PV Inverter**                       | Provides power data            | Generates PV energy |
> | **Energy Storage**    | Buffers surplus energy         | Local capacity      |
> | **Mining Node / Flexible Load**       | Dynamic energy consumer        | Controlled by Core  |
> | **User Device (Tablet, Browser)**     | Accesses explanation interface | Local WLAN / LAN    |

---

## Softwareumgebung / Software Environment

| Komponente              | Technologie                                    | Beschreibung                        |
| ----------------------- | ---------------------------------------------- | ----------------------------------- |
| **Core**                | Python                                         | Regel-Engine und Entscheidungslogik |
| **Module**              | Python / MQTT                                  | Adapter für Geräteintegration       |
| **Datenbank**           | SQLite / JSON                                  | Lokales Logging und Replay          |
| **Erklärschnittstelle** | Svelte / Tailwind oder Home Assistant Frontend | Visualisierung und Feedback         |
| **Betriebssystem**      | Raspberry Pi OS / Linux                        | Lokaler Edge-Betrieb                |

> | Component                 | Technology                                   | Description                     |
> | ------------------------- | -------------------------------------------- | ------------------------------- |
> | **Core**                  | Python                                       | Rule engine and decision logic  |
> | **Modules**               | Python / MQTT                                | Adapters for device integration |
> | **Database**              | SQLite / JSON                                | Local logging and replay        |
> | **Explanation Interface** | Svelte / Tailwind or Home Assistant frontend | Visualization and feedback      |
> | **Operating System**      | Raspberry Pi OS / Linux                      | Local edge deployment           |

---

## Deployment-Varianten / Deployment Variants

| Variante                      | Beschreibung                                      | Einsatz                                  |
| ----------------------------- | ------------------------------------------------- | ---------------------------------------- |
| **Standalone**                | Kompletter Stack auf einem Thin Client           | Prototyping, Forschung, lokale Steuerung |
| **Distributed Local Network** | Core, Module und UI auf getrennten Geräten        | Skalierte Forschungsumgebungen           |
| **Hybrid Mode**               | Optionale externe Datenspiegelung (verschlüsselt) | Vergleichende Evaluationen / Backup      |

> | Variant                       | Description                                  | Use Case                             |
> | ----------------------------- | -------------------------------------------- | ------------------------------------ |
> | **Standalone**                | Full stack on a single thin client          | Prototyping, research, local control |
> | **Distributed Local Network** | Core, modules, and UI on separate devices    | Scaled research setups               |
> | **Hybrid Mode**               | Optional external data mirroring (encrypted) | Comparative evaluation / backup      |

---

## Netzwerkkonfiguration / Network Configuration

* **Protokolle:** MQTT, REST, WebSocket (ausschließlich lokal)
* **Sicherheit:** TLS optional, lokale Firewall aktiv
* **Adressierung:** statisch (z. B. `192.168.178.50`)
* **Datenschutz:** keine Telemetrie, keine Cloud-Synchronisation

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

* [08 Konzepte / Concepts](./08_concepts.md)
