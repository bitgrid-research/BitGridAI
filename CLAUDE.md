# CLAUDE.md – BitGridAI

## Projekt

BitGridAI ist ein **local-first, deterministisches Energiemanagementsystem** für Prosumer mit PV, Batteriespeicher und flexiblen Lasten (Bitcoin-Mining als Beispiel-Last).

Kernprinzip: Jede Entscheidung ist regelbasiert, nachvollziehbar und replay-fähig.
Kein ML im Entscheidungskern. Kein Cloud-Backhaul. Keine Blackboxes.

## Sprache

- **Docs (Markdown):** Deutsch
- **Code, Kommentare, Type Hints:** Englisch
- **Commits:** Englisch, Conventional Commits Format

## Architektur

```
src/
├── core/           ← Entscheidungskern (deterministisch, NIEMALS ML hier)
│   ├── rules/      ← R1–R5: Profitabilität, Autarkie, Sicherheit, Prognose, Stabilität
│   ├── block_scheduler.py
│   ├── energy_context.py
│   ├── rule_engine.py
│   ├── override_handler.py
│   └── models.py
├── adapters/       ← Hardware & externe Systeme (Shelly, MQTT, Modbus, Forecast)
├── explain/        ← Erklärungsschicht (KI erlaubt, read-only auf DecisionEvents)
├── ops/            ← Observability, Config, Feature Flags, Auth
├── data/           ← Persistenz, Event-Log, KPI-Reporting, Export/Replay
├── ui/             ← Web-UI
├── ha/             ← Home Assistant Integration
└── sim/            ← Simulation & Testszenarien
```

**Schichtentrennung ist absolut:**
`core/` hat keinen Import von `explain/`, `ui/` oder `adapters/`.
Adapter schreiben nicht in `core/`-Strukturen.

## Wichtige Regeln

### Was nie passiert
- Kein ML, kein Zufall, keine Blackbox in `src/core/`
- Keine Cloud-Dependencies (auch nicht "nur für Dev")
- Keine externen APIs ohne lokale Alternative
- Kein Commit direkt auf `main` — immer PR
- Keine destruktiven Aktionen ohne Bestätigung
- Kein `--no-verify` bei Git Hooks

### Code-Qualität
- Formatter: `black src/ tests/`
- Linter + Typen: `mypy src/ --strict`
- Tests vor jedem PR: `make check`
- Neue Funktionen in `core/` brauchen Unit-Tests

## HA Deploy — Pflichtablauf

**Immer so deployen, nie abkürzen:**

```bash
# Nur geänderte Dateien deployen + graceful restart
bash scripts/deploy_ha.sh --restart

# Alles deployen (nach größeren Änderungen)
bash scripts/deploy_ha.sh --all --restart
```

### Regeln

1. **Immer `--restart` mitgeben** — sonst lädt HA die neuen Dateien nicht
2. **Niemals `docker restart` direkt aufrufen** — killt SMA WebConnect-Sessions hart → alle SMA-Sensoren zeigen 0W bis Sessions expiren (~15 min)
3. **Nie mehrfach hintereinander restarten** — jeder harte Restart verbraucht eine SMA-Session (Limit: 4)
4. **`.template` und `.example` Dateien nie deployen** — `deploy_ha.sh` filtert sie bereits heraus; nie manuell per `scp` oder `--all` ohne das Script deployen
5. **`HA_TOKEN` in `.env` muss gesetzt sein** — sonst fällt das Script auf `docker restart` zurück (siehe Regel 2)

### Was deployed wird

| Pfad | Inhalt |
|---|---|
| `src/ha/config/configuration.yaml` | Template-Sensoren, Regellogik, MQTT |
| `src/ha/config/ui-lovelace.yaml` | Dashboard |
| `src/ha/config/packages/*.yaml` | Miner, Stats, Automations, Pool |
| `src/ha/config/automations.yaml` | HA-Automationen |
| `src/ha/config/custom_components/` | Custom Integrations |
| `src/ha/config/www/` | Frontend-Assets |

### SMA-Session-Problem (Notfall)

Symptom: PV, Haus, Netzbezug zeigen 0W nach Restart.
Ursache: SMA WebConnect hat Session-Limit erreicht.
Fix: In HA-UI → **Settings → Devices & Services → pysmaplus → ⋮ → Reload** (kein Neustart nötig)

## Dev-Commands

```bash
make check        # fmt + lint + test (vor jedem PR)
make test         # alle Tests mit Coverage
make test-unit    # nur Unit-Tests (core, ops, explain, data)
make test-replay  # Replay-Tests
make fmt          # black formatieren
make lint         # black check + mypy
make build        # Docker bauen
make up / down    # Docker Compose
make logs         # Container-Logs
```

## Commits (Conventional Commits)

```
feat: add solar forecast integration
fix: correct SoC threshold in R2
docs: update arc42 chapter 05 building blocks
test: add unit tests for rule engine dispatch
refactor: extract energy context builder
chore: update dependencies
```

## Architektur-Docs

arc42-Struktur in `docs/architecture/` (Kapitel 01–12).
Nummerierungsschema: `01_`, `011_`, `0521_` etc. — immer einhalten.

Vor Architekturänderungen: relevantes arc42-Kapitel lesen.
Entscheidungen anhand der 6 Qualitätsziele begründen:
Transparenz · Autonomie · Nachhaltigkeit · Vorhersagbarkeit · Sicherheit · Reproduzierbarkeit

## KI-Agenten im Projekt

| Agent | Läuft auf | Modell | Rolle |
|---|---|---|---|
| Claude Code | Dev-Rechner (VSCode) | Claude Sonnet 4.6 | Code, Tests, Docs |
| ₿itsy-Dev | Umbrel (`umbrel.local:18789`) | Qwen3:14b | arc42-Review, Hintergrundanalyse |
| ₿itsy-Home | Umbrel | Qwen3:4b | Erklärung für Heimnutzer |
| ₿itsy-Study | Umbrel | Qwen3:14b | Erklärung für Forscher |

₿itsy-Dev ist der technische Sparringspartner für Architekturentscheidungen.
₿itsy-Home und ₿itsy-Study haben **keinen Schreibzugriff** — nur read-only auf DecisionEvents.

Mehr dazu: `docs/development/36_ai_tooling/COLLABORATION.md`

## Zusammenarbeit mit ₿itsy-Dev

₿itsy-Dev analysiert das Repo eigenständig und schreibt Befunde nach:
`docs/development/36_ai_tooling/bitsy-dev/FINDINGS.md`

**Nach jedem Fix aus FINDINGS.md:**
1. Status in FINDINGS.md aktualisieren: `Offen` → `Erledigt`
2. Kurze Notiz hinzufügen: was wurde geändert, welche Datei
3. Committen — ₿itsy-Dev liest den neuen Stand beim nächsten Heartbeat

**Findings prüfen bevor sie umgesetzt werden:**
- ₿itsy-Dev arbeitet auf einer Kopie (Umbrel) — Pfade können abweichen
- Befund immer gegen den tatsächlichen Repo-Stand verifizieren
- Bei Falsch-Positiven: Status → `Falsch-Positiv` mit Begründung

Format für Status-Updates in FINDINGS.md:
```
**Status:** Erledigt — `pfad/zur/datei.md` angepasst (Claude Code, YYYY-MM-DD)
**Status:** Falsch-Positiv — Datei existiert, anderes Namensschema (Claude Code, YYYY-MM-DD)
```
