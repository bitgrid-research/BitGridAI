# 7.1 - Deployment (Docker-first, Umbrel-ready)

Ein klarer Startpunkt.

BitGridAI wird primär als **lokales Edge-System** betrieben.  
Das System läuft als **Docker-Compose-Stack** auf einem zentralen Host im Heimnetz (LAN).  
Dasselbe Deployment kann optional später **ohne Codeänderungen** als **Umbrel-App** verpackt werden.

Der Betrieb ist bewusst:
- **local-first**
- **offline-fähig**
- **deterministisch**
- **ohne Cloud-Abhängigkeiten**

Home Assistant und weitere Systeme sind **sekundäre Teilnehmer**, keine Betriebsabhängigkeiten.

![Hamster beim lokalen Deployment](../../media/architecture/07_deployment_view/bithamster_07.png)

&nbsp;

## Kurzüberblick

- **Primärer Betrieb:** Docker Compose auf einem Edge Host im LAN  
- **Optionales Packaging:** Umbrel App (gleiche Container, gleiche Volumes)  
- **Kommunikation:** MQTT + REST, ausschließlich lokal  
- **Externe Systeme:** Home Assistant (lesen + begrenztes Schreiben), Research Nodes (Export/Replay)  
- **Kein WAN-Zwang, keine Cloud**

&nbsp;

## Zielbild: Compose als Basis, Umbrel als Packaging

Das Deployment folgt dem Prinzip:  
**Ein Stack – ein Ort – klare Schnittstellen.**

+-------------------------------------------------------------+

Heimnetz / LAN (kein WAN)
Edge Host (Docker / Compose)

- bitgrid-mqtt (Mosquitto)
- bitgrid-core (Rules, Scheduler, Adapter, API + UI im selben Prozess)


--> MQTT Topics (state/#, cmd/#, explain/#)

Optionale Peers im LAN
- Home Assistant (MQTT + REST, begrenzt)
- Research Node (Exports, Replays, read-only)
- Miner / Inverter / Sensorik (über Adapter)
  
+-------------------------------------------------------------+
  
Ziel ist **ein einziger, klar definierter Deployment-Punkt**, der:
- einfach aufgesetzt,
- leicht gesichert,
- und gut erklärbar ist.

&nbsp;

## Deployment-Ziele

Das Deployment verfolgt folgende Leitziele:

- **Local-first:**  
  Alle Daten, Modelle und Entscheidungen verbleiben auf dem Host.

- **Einfaches Rollout:**  
  Ein Docker-Compose-Bundle mit zwei Kerndiensten:
  `mqtt`, `core` (REST-API und UI laufen im selben Prozess wie das Regelwerk).

- **Packaging ohne Umbau:**  
  Umbrel nutzt exakt dieselben Container und Volumes.

- **Sichere Öffnung:**  
  UI nur über Proxy; MQTT nur bei Bedarf für HA oder externe Adapter.

- **Deterministische Updates:**  
  Updates erfolgen kontrolliert, mit Replay-Prüfung (siehe Kapitel 06.11).

- **Fail-safe by Design:**  
  Sicherheitsregel R3 greift unabhängig vom Containerzustand.

&nbsp;

## Artefakt-zu-Knoten-Zuordnung  
*(Bausteinsicht → Container → Host)*

| Baustein (Kap. 5) | Container / Service | Knoten | Persistenz |
|------------------|---------------------|--------|------------|
| Core / Rules     | `bitgrid-core`      | Edge Host | `./config`, `./data`, `./logs` |
| Adapter / Module | Teil von `core`     | Edge Host | `./config` |
| UI / Explain     | Teil von `core` (gemeinsamer Prozess) | Edge Host | build-/cache-basiert |
| Datenhaltung     | gemountet in `core` | Edge Host | SQLite / Parquet |
| MQTT-Bus         | `bitgrid-mqtt`      | Edge Host | `./mqtt/*` |

Optional (Umbrel):
- identische Container
- Volumes unter `/umbrel/app-data/bitgrid/*`

&nbsp;
## Primärer Betrieb: Docker Compose im LAN

### Kerndienste

| Service | Aufgabe | Exponierung |
|-------|--------|-------------|
| `bitgrid-mqtt` | Messaging (State, Commands, Explain) | intern; optional LAN |
| `bitgrid-core` | Regelwerk R1–R5, Scheduler, REST-API **und UI** (ein Prozess) | API/UI über Port 8080 |

**Netz:** internes Docker-Netz (`bitgrid_net`)  
**Startreihenfolge:** MQTT → Core  
**Ressourcen:** Ziel ≥ 4 vCPU / 4 GB RAM (LLM quantisiert, edge-tauglich)

&nbsp;

## Option: Umbrel-App Packaging

Umbrel ist **reines Packaging**, kein neues Deployment-Modell.

- **Manifest:** beschreibt App, Icon, Proxy-Ziel, Backups
- **Images:** identisch zu Compose
- **Datenpfade:** `/umbrel/app-data/bitgrid/*`
- **Proxy:** UI hinter Umbrel-Reverse-Proxy
- **MQTT:** intern; optional LAN-Freigabe für HA

Build- und Release-Logik bleibt identisch:
> Compose testen → Replay prüfen → paketieren.

&nbsp;

## Sekundäre Anbindungen

### Home Assistant

- **MQTT:** Lesen von States, optionales Senden von Kommandos
- **REST:** begrenzte Schreibzugriffe (`/override`, `/research/export`)
- **Sicherheit:** Authentifiziert, rate-limitiert (Kap. 06.12)
- **Rolle:** Assistenzsystem, kein Kontrollzentrum

### Research Node

- Holt Exporte
- Führt Replays lokal aus
- Kein permanenter Zugriff auf das Live-System

&nbsp;

## Datenpfade & Backups

| Pfad | Inhalt | Empfehlung |
|----|-------|-----------|
| `./config` | Konfiguration, Tokens, Flags | täglich |
| `./data` | SQLite (Hot), Parquet (Cold) | täglich + vor Updates |
| `./logs` | Safety-, Decision-, Explain-Events | rotierend |
| `./mqtt` | Broker-Daten | optional |

Backups erfolgen **lokal** (NAS/USB).  
Keine Cloud-Synchronisation ohne explizites Opt-in.

&nbsp;

## Zusammenfassung

Kapitel 7.1 definiert BitGridAI als **klar abgegrenztes, lokales Deployment**:

- ein Host
- ein Stack
- klare Schnittstellen
- keine versteckten Abhängigkeiten

Docker Compose ist die **technische Basis**, Umbrel eine **optionale Verpackung**.  
Der Betrieb bleibt transparent, kontrollierbar und sicher.

---
> **Nächster Schritt:** Das Basis-Deployment ist klar.  
> Jetzt betrachten wir, **wie sich diese Architektur auf unterschiedliche Infrastruktur- und Betriebsvarianten ausdehnen lässt**.
>
> 👉 Weiter zu **[7.2 - Infrastruktur & Umgebungen](./072_infrastructure_variants.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
