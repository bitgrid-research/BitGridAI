# 30.2 – Entwicklungsumgebung

Dieses Kapitel beschreibt, wie du BitGridAI lokal zum Laufen bringst –
vom ersten `git clone` bis zum laufenden Docker-Stack.

Das Ziel: eine **einheitliche, reproduzierbare Umgebung**, die sich auf jedem
Entwicklungsrechner gleich verhält und keine Cloud-Abhängigkeiten hat.

&nbsp;

## Voraussetzungen

Folgende Tools müssen installiert sein, bevor es losgeht:

| Tool | Version | Wozu |
|------|---------|------|
| **Python** | 3.11+ | Kernlogik, Tests, Tooling |
| **Docker Desktop** (Win) / Docker Engine (Linux) | aktuell | Stack lokal starten |
| **Git** | aktuell | Repository-Zugriff |
| **VSCode** | aktuell | Entwicklungsumgebung |
| **Claude Code** (VSCode Extension) | aktuell | KI-gestütztes Entwickeln |

### Python installieren (Windows)

```powershell
# Empfehlung: via winget
winget install Python.Python.3.11

# Oder direkt von python.org herunterladen
# https://python.org/downloads/
```

Version prüfen:

```bash
python --version
# Python 3.11.x
```

### Docker Desktop installieren

Docker Desktop für Windows benötigt WSL 2 als Backend.

```powershell
# WSL 2 installieren
wsl --install

# Docker Desktop herunterladen und installieren
# https://docs.docker.com/desktop/install/windows-install/
```

Nach dem Neustart prüfen:

```bash
docker --version
docker compose version
```

&nbsp;

## Repository klonen

```bash
git clone <repo-url> BitGridAI
cd BitGridAI
```

> Repo-URL: im internen Projektbereich (TOOLS.md) oder beim Projektverantwortlichen erfragen.

&nbsp;

## Python-Umgebung einrichten

BitGridAI nutzt eine **virtuelle Umgebung**, um Abhängigkeiten sauber zu isolieren.

```bash
# Virtuelle Umgebung anlegen
python -m venv .venv

# Aktivieren
# Windows:
.venv\Scripts\activate
# Linux / WSL:
source .venv/bin/activate

# Abhängigkeiten installieren (sobald requirements.txt vorhanden)
pip install -r requirements.txt
```

Die virtuelle Umgebung ist in `.gitignore` eingetragen – sie wird nicht ins Repository eingecheckt.

&nbsp;

## Docker-Stack lokal starten

BitGridAI läuft als Docker-Compose-Stack mit drei Kerndiensten:

| Service | Aufgabe |
|---------|---------|
| `bitgrid-mqtt` | MQTT-Broker (Mosquitto) |
| `bitgrid-core` | Regelwerk, Scheduler, API |
| `bitgrid-ui` | Visualisierung & Kontrolle |

```bash
# Stack starten
docker compose up -d

# Logs verfolgen
docker compose logs -f

# Stack stoppen
docker compose down
```

Startreihenfolge automatisch: MQTT → Core → UI.

&nbsp;

## VSCode einrichten

### Empfohlene Extensions

| Extension | Zweck |
|-----------|-------|
| **Claude Code** | KI-gestütztes Entwickeln (docs, code, tests) |
| **Python** (Microsoft) | Syntax, Linting, Debugging |
| **Remote - SSH** (Microsoft) | Direkt auf Edge-Gerät entwickeln |
| **Docker** (Microsoft) | Container-Verwaltung in der IDE |
| **YAML** (Red Hat) | Docker-Compose- und Config-Dateien |

### Workspace öffnen

```bash
# Aus dem Projektverzeichnis heraus:
code .
```

VSCode erkennt den Workspace automatisch und schlägt empfohlene Extensions vor
(sofern `.vscode/extensions.json` gepflegt ist).

&nbsp;

## Konfiguration & Umgebungsvariablen

Lokale Konfiguration erfolgt über eine `.env`-Datei im Projektstamm.
Eine Vorlage liegt unter `.env.example`:

```bash
cp .env.example .env
# .env mit eigenen Werten befüllen (Gerätadressen, Ports etc.)
```

> `.env` ist in `.gitignore` eingetragen – niemals einchecken.

&nbsp;

## Schnellcheck: Alles läuft?

```bash
# Python-Umgebung aktiv?
python --version

# Docker läuft?
docker compose ps

# SSH zum Edge-Gerät?
ssh bitgrid "echo OK"
```

Wenn alle drei Befehle sauber antworten, ist die Umgebung bereit.

&nbsp;

## Ressourcen-Empfehlungen

BitGridAI ist für Edge-Hardware ausgelegt, läuft aber auch lokal komfortabel:

| Ressource | Minimum | Empfohlen |
|-----------|---------|-----------|
| CPU | 2 Kerne | 4+ Kerne |
| RAM | 4 GB | 8 GB (LLM quantisiert) |
| Disk | 10 GB | 20 GB |

---

> 👉 Weiter zu **[31 – Projektstruktur](../31_project_structure/README.md)**
>
> 🔙 Zurück zu **[30 – Setup & Umgebung](./README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
