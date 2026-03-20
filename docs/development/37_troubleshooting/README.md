# 37 – Troubleshooting & FAQ

Etwas läuft nicht. Hier findest du schnell die Ursache.

**Schnell-Diagnose zuerst → dann gezielt in den passenden Abschnitt.**

&nbsp;

---

## F — Schnell-Diagnose

Wenn unklar ist, wo das Problem liegt, diese Checks der Reihe nach:

```bash
# 1. Stack-Status
docker compose ps

# 2. Logs der letzten 5 Minuten
docker compose logs --since=5m

# 3. Health-Endpunkt
curl -s http://localhost:8080/health

# 4. MQTT-Bus aktiv?
mosquitto_sub -h localhost -t "bitgridai/#" -v -C 5

# 5. Speicherplatz
df -h ./data ./logs

# 6. Git-Status
git status
```

| Symptom | Wahrscheinlichster Abschnitt |
|---------|------------------------------|
| Stack startet nicht | [A – Setup & Umgebung](#a--setup--umgebung) |
| Core trifft falsche Decisions | [C – Core & Regeln](#c--core--regeln) |
| MQTT-Nachrichten fehlen | [B – Stack & Laufzeit](#b--stack--laufzeit) |
| Tests schlagen fehl | [D – Tests & CI](#d--tests--ci) |
| ₿itsy antwortet nicht | [E – ₿itsy / OpenClaw](#e--bitsy--openclaw) |

&nbsp;

---

## A — Setup & Umgebung

### SSH: `Permission denied (publickey)`

```bash
# Schlüssel im Agenten?
ssh-add -l

# Falls leer:
ssh-add ~/.ssh/id_ed25519

# Schlüssel auf dem Gerät hinterlegt?
ssh -v user@umbrel.local 2>&1 | grep "Offering"
```

Wenn der Schlüssel nicht akzeptiert wird: [30.1 – SSH Setup](../30_setup/ssh_windows_setup.md) erneut durchlaufen.

&nbsp;

### `umbrel.local` nicht auflösbar

```bash
# IP-Adresse direkt verwenden
ssh user@192.168.1.x

# mDNS-Dienst prüfen (Windows)
Get-Service -Name "Bonjour Service"
```

Alternativ: statische IP im Router vergeben und in `~/.ssh/config` eintragen.

&nbsp;

### Docker Desktop startet nicht / `docker compose` nicht gefunden

- WSL 2 aktiviert? → `wsl --status`
- Docker Desktop läuft? → Taskleiste prüfen
- Nach Installation: Neustart erforderlich

```bash
docker --version && docker compose version
```

&nbsp;

### Python venv wird nicht aktiviert (Windows)

```powershell
# Execution Policy blockiert?
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Dann erneut:
.venv\Scripts\activate
```

&nbsp;

### `.env` fehlt beim Stack-Start

```bash
cp .env.example .env
# .env mit eigenen Werten befüllen
```

`docker compose` bricht ohne `.env` nicht ab — aber Variablen fehlen dann zur Laufzeit.
Symptom: Core startet, findet aber Broker-Adresse nicht.

&nbsp;

---

## B — Stack & Laufzeit

### MQTT-Broker ausgefallen

**Symptom:** Core loggt `Connection refused` oder `offline hold active`.

```bash
# Broker-Container läuft?
docker compose ps bitgrid-mqtt

# Neustart
docker compose restart bitgrid-mqtt

# Logs prüfen
docker compose logs bitgrid-mqtt --tail=50
```

Core geht automatisch in **„offline hold"**: letzte bekannte Decision bleibt aktiv.
Kein Safety-Verlust, aber keine neuen Entscheidungen bis zur Wiederverbindung.

&nbsp;

### Storage läuft voll

**Symptom:** Low-Disk-Alarm im Health-Feed oder `No space left on device` im Log.

```bash
# Speicherverbrauch prüfen
du -sh ./data/* ./logs/*

# Alte Parquet-Dateien rotieren (gemäß Retention-Policy in config.yaml)
# Oder manuell:
ls -lth ./logs/*.parquet | tail -20
```

Retention-Policy in `config/retention.yaml` anpassen — nie manuell Dateien löschen
ohne Backup.

&nbsp;

### Zeitdrift erkannt

**Symptom:** Core loggt `clock drift detected`, Block-Scheduler hält 1 Block.

```bash
# Systemzeit prüfen
date

# NTP-Status (Linux)
timedatectl status

# NTP neu synchronisieren
sudo systemctl restart systemd-timesyncd
```

Core re-synct automatisch nach 1 Block. Wenn Drift > 30 s: NTP-Konfiguration prüfen.

&nbsp;

### Thermal-Alarm — R1 stoppt Miner

**Symptom:** Miner inaktiv, Decision zeigt `rule=R1_SAFETY`, `trigger=overtemp`.

Das ist kein Fehler — das ist das System das korrekt funktioniert.

```bash
# Aktuellen EnergyState prüfen
curl -s http://localhost:8080/state | jq '.battery_temp_c, .miner_temp_c'
```

Ursachen:
- Lüfter blockiert oder ausgefallen
- Raumtemperatur zu hoch
- Temperatur-Schwellwert in `config/rules.yaml` zu niedrig konfiguriert

Miner startet automatisch wieder, sobald Temperatur unter Schwellwert fällt und
der nächste Block ausgewertet wird.

&nbsp;

### Core startet, trifft aber keine Decisions

```bash
# EnergyState vollständig?
curl -s http://localhost:8080/state | jq '.pv_power_w, .battery_soc_pct, .grid_power_w'
```

Wenn Felder `null`: Telemetry Ingest hat keine Daten.
→ Adapter-Verbindung prüfen, Device Profile laden, MQTT-Topics prüfen.

&nbsp;

---

## C — Core & Regeln

### Decision ändert sich unerwartet nach Update

Replay-Test läuft lassen:

```bash
pytest tests/replay/ -v \
  --replay-data=data/logs/last_30_days.parquet \
  --expected-decisions=data/logs/decisions_reference.parquet
```

Wenn Replay abweicht: das Update hat das Regelverhalten verändert.
Entweder Rollback oder bewusste Anpassung des Reference-Bundles.

&nbsp;

### Override läuft nicht ab

**Symptom:** Manueller Eingriff aktiv, obwohl TTL abgelaufen sein sollte.

```bash
# Aktiven Override prüfen
curl -s http://localhost:8080/state | jq '.active_override'
```

Mögliche Ursachen:
- Systemzeit wurde zurückgestellt (→ Zeitdrift-Problem)
- TTL-Wert in `config/rules.yaml` zu groß gesetzt
- Override wurde ohne TTL ausgelöst (unbefristeter Override)

Manuell beenden:
```bash
curl -X DELETE http://localhost:8080/override
```

&nbsp;

### Deadband schwingt trotzdem (Flapping)

**Symptom:** Miner wechselt häufig zwischen aktiv/inaktiv, `valid_until` wird ignoriert.

```bash
# Flapping-KPI prüfen
curl -s http://localhost:8080/kpi | jq '.flapping_count_24h'
```

Ursachen:
- Deadband-Schwellwert zu niedrig in `config/rules.yaml`
- PV-Signal rauscht stark (Sensor-Kalibrierung)
- Block-Scheduler-Takt wurde verändert

Lösung: Deadband-Wert erhöhen, Replay A/B-Test mit neuem Wert.

&nbsp;

### Regel R2 (Autarkie) greift obwohl Batterie voll ist

```bash
curl -s http://localhost:8080/state | jq '.battery_soc_pct, .autarky_threshold'
```

SoC-Wert und konfigurierten Schwellwert vergleichen.
Wenn SoC-Sensor falsche Werte liefert: Device Profile und Adapter-Kalibrierung prüfen.

&nbsp;

---

## D — Tests & CI

### Replay-Test schlägt fehl

```
AssertionError: decision.action mismatch
  expected: START_MINER
  got:      STOP_MINER
```

Das ist der wichtigste Hinweis: **das Regelverhalten hat sich verändert**.

1. War die Änderung beabsichtigt? → Reference-Bundle aktualisieren, Änderung dokumentieren
2. War sie unbeabsichtigt? → Commit-History prüfen, Rollback oder Fix

&nbsp;

### mypy schlägt fehl

```bash
# Alle Fehler ausgeben
mypy src/ --strict 2>&1 | head -40
```

Häufigste Ursachen:

| Fehler | Lösung |
|--------|--------|
| `Missing return type annotation` | Rückgabetyp ergänzen |
| `Incompatible types` | Type Hint oder Logik korrigieren |
| `Module has no attribute` | Import prüfen, ggf. Stub fehlt |
| `error: Cannot find implementation` | `py.typed` Marker fehlt im Paket |

&nbsp;

### Black-Diff bei `--check`

```bash
# Was würde Black ändern?
black --diff src/

# Einfach anwenden
black src/ tests/
```

Black hat keine Konfiguration — kein Diskutieren, einfach laufen lassen.

&nbsp;

### Coverage unter Schwelle

```bash
# Wo fehlt Coverage?
pytest tests/ --cov=src --cov-report=term-missing 2>&1 | grep "MISS"
```

Fehlende Coverage in `src/core/` ist ein Red Flag — dort sollte ≥ 90 % erreicht werden.
Fixture aus `src/sim/` nutzen statt neue Testdaten erfinden.

&nbsp;

### Docker-Build schlägt fehl in CI

```bash
# Lokal nachstellen
docker build -t bitgrid-core:test -f src/core/Dockerfile . 2>&1 | tail -30
```

Häufig: fehlende System-Dependencies im Dockerfile, oder `requirements.txt` nicht aktuell.

&nbsp;

---

## E — ₿itsy / OpenClaw

### Agent antwortet nicht

```bash
# OpenClaw läuft?
curl -s http://umbrel.local:18789/health

# Umbrel-Dienst prüfen
ssh bitgrid "docker ps | grep openclaw"
```

&nbsp;

### Falsches Modell geladen

In OpenClaw-Einstellungen prüfen:

| Workspace | Erwartetes Modell |
|-----------|------------------|
| `bitsy-dev` | `qwen3:14b` |
| `bitsy-home` | `qwen3:4b` |
| `bitsy-study` | `qwen3:14b` |

Wenn das falsche Modell aktiv ist: in der OpenClaw-Oberfläche manuell wechseln.

&nbsp;

### Workspace nicht initialisiert (₿itsy kennt das Projekt nicht)

`BOOTSTRAP.md` prüfen — falls noch vorhanden, wurde der erste Start nicht abgeschlossen.
Datei manuell durchlaufen lassen oder Agent neu starten mit BOOTSTRAP-Anweisung.

&nbsp;

### ₿itsy-Home / Study schreibt trotzdem Aktorbefehle vor

Das ist ein Konfigurationsfehler im SOUL.md oder AGENTS.md des Workspaces.

Sofortmaßnahme: Session beenden.
Dann `SOUL.md` und `AGENTS.md` des betroffenen Workspaces prüfen —
die Red Lines müssen explizit stehen:

```
- Keine Aktorbefehle. Niemals.
- Kein POST /override. Kein POST /cmd.
```

&nbsp;

### MEMORY.md wächst zu groß (₿itsy-Dev)

```bash
wc -l docs/development/36_ai_tooling/bitsy-dev/MEMORY.md
```

Wenn > 200 Zeilen: destillieren. Tagesnotizen in `memory/` lesen,
das wirklich Wichtige in MEMORY.md behalten, den Rest archivieren oder löschen.

&nbsp;

---

> **Endstation.**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
