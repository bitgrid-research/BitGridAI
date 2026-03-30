# Onboarding HiWi 1 — Simulation & Systementwicklung

Willkommen im BitGridAI-Projekt. Diese Seite führt dich durch den Einstieg in deinen Schwerpunkt: lokale Systeminfrastruktur, Simulationsszenarien und Rule-Engine.

---

## Dein Bereich im Repo

```
src/
├── core/           ← Rule-Engine, Entscheidungslogik (R1–R5)
│   ├── rules/      ← Einzelregeln — hier wirst du viel arbeiten
│   ├── rule_engine.py
│   ├── block_scheduler.py
│   └── models.py
├── sim/            ← Simulationsszenarien, CSV-Loader, MQTT-Recorder
├── ops/            ← Logging, Feature Flags, Observability
├── data/           ← Event-Log, KPI, Replay
├── adapters/       ← Hardware-Anbindung (Miner, Modbus, MQTT, Forecast)
└── ha/             ← Home Assistant Integration (Docker, YAML-Packages)
```

**Tabu ohne Rücksprache:** Alles was du in `src/core/` änderst hat direkte Auswirkung auf das Entscheidungsverhalten des Systems. Neue Funktionen brauchen immer Unit-Tests.

---

## Einrichten

```bash
# 1. Repo klonen und Umgebung einrichten
git clone <repo-url>
cd BitGridAI
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# 2. Prüfen ob alles funktioniert
make check                       # muss grün sein

# 3. HA-Stack lokal starten
cp .env.example .env             # .env mit deinen Werten befüllen
bash src/ha/generate_ha_packages.sh   # Miner-YAML aus .env generieren
cd src/ha && docker compose up -d
```

---

## Erste Aufgaben (Vorschlag)

1. **Simulationsszenarien verstehen** — `src/sim/` lesen, ein bestehendes Szenario durchlaufen lassen
2. **Rule-Engine nachvollziehen** — `tests/core/` lesen, alle Unit-Tests ausführen (`make test-unit`)
3. **Ein Szenario erweitern** — z.B. Temperaturverlauf ergänzen oder neuen Edge-Case abdecken
4. **Replay-Test schreiben** — `tests/replay/` als Vorlage nutzen

---

## Wichtige Make-Befehle

```bash
make check          # Pflicht vor jedem PR
make test-unit      # nur core, ops, data, sim
make test-replay    # Replay-Tests
make fmt            # Autoformat
make lint           # black + mypy
make up             # Docker Stack starten
make logs           # Container-Logs
```

---

## Architekturprinzip das du kennen musst

`src/core/` ist **deterministisch und replay-fähig**. Das bedeutet:
- Gleicher Input → immer gleicher Output
- Kein ML, kein Zufall, keine externen Calls
- Jede Entscheidung wird als `DecisionEvent` geloggt und kann später exakt wiederholt werden

Wenn du eine Regel änderst, muss der zugehörige Replay-Test weiterhin grün bleiben — oder du aktualisierst ihn bewusst mit Begründung.

---

## Ansprechpartner & Workflow

- Fragen zur Architektur → ₿itsy-Dev (`docs/development/36_ai_tooling/`)
- Workflow & Branching → `docs/development/32_workflow/README.md`
- PR öffnen → Checkliste im PR-Template ausfüllen, 1 Approval abwarten
