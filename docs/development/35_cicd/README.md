# 35 – CI/CD & Deployment

BitGridAI ist ein lokales Edge-System – kein Cloud-Dienst.
Das prägt, wie wir bauen, prüfen und deployen:

- kein erzwungener Push in externe Registries
- kein Rolling-Deployment über Kubernetes
- stattdessen: **kontrollierbarer, nachvollziehbarer Update-Prozess mit Replay-Absicherung**

&nbsp;

## Pipeline-Übersicht

```
Commit auf Feature-Branch
        │
        ▼
┌───────────────────┐
│  Lokale Checks    │  black · mypy · pytest · replay
└───────────────────┘
        │ PR öffnen
        ▼
┌───────────────────┐
│  CI-Pipeline      │  automatisch bei PR / Merge
│  (GitHub Actions) │  lint · type-check · test · build
└───────────────────┘
        │ Merge auf main
        ▼
┌───────────────────┐
│  Image bauen      │  docker build + tag
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Replay-Prüfung   │  ← kritischer Gate vor Deploy
└───────────────────┘
        │ grün
        ▼
┌───────────────────┐
│  Deploy auf       │  docker compose pull + up -d
│  Edge Node        │
└───────────────────┘
```

&nbsp;

## Lokale Checks (vor dem Push)

Diese Checks laufen lokal bevor ein PR geöffnet wird.
Sie sind identisch mit der CI-Pipeline — kein "works on my machine".

```bash
# Formatierung
black --check src/ tests/

# Typen
mypy src/ --strict

# Tests + Coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Replay-Prüfung (vor größeren Änderungen am Core)
pytest tests/replay/ -v
```

Alles in einem Befehl:

```bash
make check
# oder ohne Makefile:
black --check src/ tests/ && mypy src/ --strict && pytest tests/ -v --cov=src
```

&nbsp;

## CI-Pipeline (GitHub Actions)

Die Pipeline läuft automatisch bei jedem PR und bei jedem Merge auf `main`.

### Stages

```yaml
# .github/workflows/ci.yml  (Entwurf)

jobs:
  lint:
    - black --check src/ tests/

  typecheck:
    - mypy src/ --strict

  test:
    - pytest tests/unit/ tests/integration/ -v --cov=src
    - pytest tests/replay/ -v          # Replay immer dabei

  build:
    - docker build -t bitgrid-core .
    - docker build -t bitgrid-ui ./ui
```

### Gate-Regeln

| Stage | Muss grün sein für... |
|-------|----------------------|
| lint | ...PR-Merge möglich |
| typecheck | ...PR-Merge möglich |
| test (unit + integration) | ...PR-Merge möglich |
| replay | ...Merge auf `main` möglich |
| build | ...Image-Freigabe |

Kein Merge ohne grüne Replay-Tests.

&nbsp;

## Docker-Images

BitGridAI besteht aus drei Kerndiensten.
Jeder Service hat sein eigenes Image.

| Service | Image | Aufgabe |
|---------|-------|---------|
| `bitgrid-mqtt` | `eclipse-mosquitto:latest` | MQTT-Broker (kein eigener Build) |
| `bitgrid-core` | `bitgrid-core:<tag>` | Regelwerk, Scheduler, API |
| `bitgrid-ui` | `bitgrid-ui:<tag>` | Web-Frontend, Explain-Agent |

### Tagging-Schema

```
bitgrid-core:latest          ← aktuellster stabiler Stand
bitgrid-core:0.3.1           ← semantisches Versions-Tag
bitgrid-core:main-a3f92c     ← Branch + Commit-SHA (für Debugging)
```

### Build

```bash
# Core bauen
docker build -t bitgrid-core:0.3.1 -f src/core/Dockerfile .

# UI bauen
docker build -t bitgrid-ui:0.3.1 -f src/ui/Dockerfile .

# Beide zusammen (via Compose)
docker compose build
```

&nbsp;

## Replay-Prüfung vor dem Deploy

Das ist der wichtigste Gate im Update-Prozess.

**Warum:** Refactoring, Regeländerungen oder neue Dependencies können das Entscheidungsverhalten subtil verändern — ohne dass Unit-Tests es merken. Der Replay-Test erkennt das.

```bash
# Replay-Bundle aus data/logs/ laden und durch neues Image laufen lassen
pytest tests/replay/ \
  --replay-data=data/logs/last_30_days.parquet \
  --expected-decisions=data/logs/decisions_reference.parquet \
  -v
```

**Ergebnis:**
- ✅ Gleiche Decisions → Deploy freigegeben
- ❌ Abweichung → Deploy geblockt, Ursache analysieren

Dokumentierte Verhaltensänderungen (z.B. neue Regel) werden als neues Reference-Bundle eingecheckt.

&nbsp;

## Deployment auf den Edge Node

### Standard: Standalone auf einem Host

```bash
# Auf dem Edge Node (via SSH)
ssh bitgrid

# Neue Images ziehen
cd /opt/bitgridai
docker compose pull

# Replay-Prüfung (nochmals lokal auf dem Node)
docker compose run --rm bitgrid-core pytest tests/replay/ -v

# Dienste neu starten (Volumes bleiben erhalten!)
docker compose up -d

# Status prüfen
docker compose ps
docker compose logs -f --tail=50
```

**Wichtig: Volumes werden nie gelöscht.**
`./config`, `./data`, `./logs` bleiben immer erhalten.

### docker-compose.yml (Entwurf)

```yaml
services:
  bitgrid-mqtt:
    image: eclipse-mosquitto:latest
    volumes:
      - ./mqtt:/mosquitto/data
    restart: unless-stopped

  bitgrid-core:
    image: bitgrid-core:latest
    depends_on: [bitgrid-mqtt]
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    env_file: .env
    restart: unless-stopped

  bitgrid-ui:
    image: bitgrid-ui:latest
    depends_on: [bitgrid-core]
    ports:
      - "127.0.0.1:8080:8080"   # nur lokal, kein direkter WAN-Zugang
    restart: unless-stopped

networks:
  default:
    name: bitgrid_net
```

Startreihenfolge: **mqtt → core → ui**

&nbsp;

## Umbrel-Packaging (optional)

Umbrel ist reines Packaging — keine neue Architektur, keine neuen Images.

```
Compose testen → Replay prüfen → umbrel-app.yml schreiben → paketieren
```

| Unterschied zu Standalone | Umbrel |
|--------------------------|--------|
| Datenpfade | `/umbrel/app-data/bitgrid/*` statt `./` |
| UI-Proxy | hinter Umbrel Reverse Proxy |
| Images | identisch |
| Volumes | identisch (andere Basis-Pfade) |

&nbsp;

## Betriebsvarianten

| Variante | Wann | Besonderheit |
|----------|------|-------------|
| **Standalone** | Standard, Einzelhaushalt | Ein Host, alles ko-lokalisiert |
| **Distributed** | Größere Installation | Adapter auf separatem Gateway |
| **Umbrel** | Umbrel-Nutzer | Gleiche Images, Umbrel-Proxy |
| **Hybrid** | Forschung | Opt-in Datenexport, kein Rückkanal |

Alle Varianten nutzen dasselbe Update-Modell.

&nbsp;

## Rollback

Wenn ein Deploy schiefläuft:

```bash
# Vorheriges Image-Tag wieder aktivieren
# docker-compose.yml: image: bitgrid-core:0.3.0

docker compose up -d

# Oder direkt via Tag
docker compose pull bitgrid-core:0.3.0
BITGRID_CORE_TAG=0.3.0 docker compose up -d
```

**Volumes bleiben immer erhalten** — ein Rollback des Images reicht.
Datenbankmigrationen werden, falls nötig, explizit und rückwärtskompatibel geschrieben.

&nbsp;

## Monitoring nach dem Deploy

```bash
# Alle Dienste laufen?
docker compose ps

# Logs der letzten 10 Minuten
docker compose logs --since=10m

# Health-Endpunkt prüfen
curl http://localhost:8080/health

# MQTT-Bus aktiv?
mosquitto_sub -h localhost -t "bitgridai/#" -v
```

---

> **Nächster Schritt:** Stack läuft, Deploy abgesichert.
> Jetzt: KI-Werkzeuge und wie Claude Code in den Workflow integriert ist.
>
> 👉 Weiter zu **[36 – AI-Agenten & Tooling](../36_ai_tooling/README.md)**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
