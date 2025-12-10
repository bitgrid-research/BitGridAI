# 05.1 Level 1: Die System-Blackbox

Was macht der Kasten eigentlich?

Auf dieser Ebene abstrahieren wir das gesamte System zu einem einzigen Baustein: **BitGridAI**. Wir ignorieren *wie* es innen aussieht und konzentrieren uns ausschließlich darauf, welche Schnittstellen es nach außen anbietet.

Der Fokus liegt hier auf **lokaler, erklärbarer Steuerung** ohne Cloud-Zwang. Wir definieren die Grenzen zwischen unserer Software und der physischen Welt.

*(Platzhalter für ein Bild: Ein einfacher, schwarzer Würfel mit leuchtenden Linien. Kabel führen zu Symbolen für Sonne, Haus und Bitcoin. Ein Schild davor listet die Inputs und Outputs auf.)*
![Hamster auf der Blackbox](../media/pixel_art_blackbox.png)

## Systemgrenzen (Boundaries)

Wo hört BitGridAI auf und wo fängt der Rest der Welt an?

| Bereich | Was gehört dazu? (Inside BitGridAI) | Was ist draußen? (External Systems) |
| :--- | :--- | :--- |
| **Logik & Steuerung** | Rule Engine (R1–R5), BlockScheduler (10-Min-Takt), EnergyState (SSoT). | Home Assistant Core, externe Automatisierungen. |
| **Hardware-Anbindung** | Software-Adapter (für Modbus/REST/MQTT), die Hardware abstrahieren. | Die physische Hardware selbst (PV-Inverter, Speicher, Smart Meter, ASICs). |
| **Daten & UI** | Explain-Agent (On-Device), Logging/KPIs, Research-Toggle. | Browser (UI-Client), externe Dashboards, lokale Forecast-Dienste. |

---

## Datenflüsse: Was geht rein, was geht raus?

Wir betrachten die Blackbox als Funktion: $f(Input) = Output$.

### 📥 Externe Inputs (Was wir konsumieren)
Das System benötigt diese Daten, um Entscheidungen zu treffen:
* **Messdaten (Real-time):**
    * PV-Leistung, Netzimport/-export, Batteriespeicher-SoC, Temperaturen.
    * *Weg:* MQTT, Modbus TCP oder REST-Push.
* **Kontextdaten:**
    * Strompreise & Wetter-Forecasts (für Regeln R1/R4).
    * *Weg:* Lokale Datei oder lokaler Microservice.
* **User-Commands (Interaktion):**
    * Manuelle Overrides (z.B. "Boost jetzt!").
    * Research-Toggle (Umschalten des Logging-Modus).
    * UI-Feedback.
* **Health-Signale:**
    * Statusmeldungen der Broker oder Adapter (Heartbeats).

### 📤 Externe Outputs (Was wir produzieren)
Das sind die Ergebnisse unserer Verarbeitung:
* **Actuation (Steuerung):**
    * Befehle wie `start`, `stop` oder `set_power` an Miner oder Relais.
    * *Weg:* REST-Call oder MQTT-Publish.
* **Explainability (Erklärung):**
    * `DecisionEvents` angereichert mit `Reason`, `Trigger` und `Params`.
    * *Weg:* WebSocket Push oder REST-Abfrage.
* **State & Timeline (Visualisierung):**
    * Der aktuelle `EnergyState` und die Historie für das Frontend.
* **Research/Export (Wissenschaft):**
    * Export-Bundles für Replays (nur bei aktivem Opt-in).
    * *Format:* Parquet-Dateien oder JSON-Dumps.

---

## Vertragsartefakte (Contracts)

Wenn du BitGridAI integrieren willst, sind das deine technischen Anknüpfungspunkte. Diese Schnittstellen sind stabil definiert:

### 📡 MQTT Topics
Das "Nervensystem" für Echtzeitdaten:
* `energy/state/#` → Der aktuelle Zustand aller Messwerte (SSoT).
* `miner/cmd/set` → Schreibbefehle an die Mining-Hardware.
* `miner/state/#` → Rückmeldung der Miner (Hashrate, Temp).
* `explain/events/#` → Stream der Entscheidungsbegründungen.
* `health/#` → Systemstatus ("Lebenszeichen").

### 🌐 REST Endpunkte (Lokal)
Die API für UIs und Tools:
* `GET /state` → Hol den aktuellen Systemzustand.
* `GET /timeline` → Hol die Historie und Prognose.
* `GET /preview` → Was würde passieren, wenn...? (Simulation).
* `POST /override` → Übersteuere die Automatik manuell.
* `GET /research/export` → Lade Logs für die Forschung herunter.

### 💾 Dateien & Datenbanken
Die Persistenzschicht auf dem Datenträger:
* `data/bitgrid.sqlite` → Operationale Datenbank.
* `data/parquet/*.parq` → Langzeit-Archiv (komprimiert, append-only).
* `config/*.yaml` → Nutzerkonfiguration und Profile.
* `explain/*.json` → Textbausteine für den Explain-Agent.

---
> **Nächster Schritt:** Wir haben die Anschlüsse definiert. Jetzt öffnen wir das Gehäuse. Im nächsten Level schauen wir uns an, welche Komponenten im Inneren diese Daten verarbeiten.
>
> 👉 Weiter zu **[Level 2: Die Whitebox (Innenleben)](../052_whitebox/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](../README.md)**
