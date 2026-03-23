# 34 – Tests & Qualitätssicherung

BitGridAI steuert Energie, Wärme und Hardware.
Fehler haben physische Konsequenzen – deshalb ist Qualitätssicherung kein Anhang, sondern Teil der Architektur.

Das Fundament: **Determinismus**. Gleicher Input → gleicher Output.
Das macht den Core besonders gut testbar – und Replays zum mächtigsten Werkzeug im Testprozess.

&nbsp;

## Teststrategie — die Pyramide

```
           ┌─────────────────────┐
           │   End-to-End        │  ← Stack läuft, Szenario durchgespielt
           ├─────────────────────┤
           │   Replay-Tests      │  ← historische Events → gleiche Decision
           ├─────────────────────┤
           │   Integrationstests │  ← Module zusammen, echte Protokolle
           ├─────────────────────┤
           │   Unit-Tests        │  ← einzelne Funktionen, isoliert
           └─────────────────────┘
               viele  →  wenige
```

| Ebene | Was wird getestet | Werkzeug | Wo |
|-------|------------------|----------|----|
| **Unit** | einzelne Funktionen, Klassen | `pytest` | `tests/` |
| **Integration** | Module zusammen, MQTT, SQLite | `pytest` + `testcontainers` | `tests/integration/` |
| **Replay** | historische Events → identische Decision | `pytest` + `sim/` | `tests/replay/` |
| **End-to-End** | vollständiger Stack, Szenarien | `pytest` + Docker Compose | `tests/e2e/` |

&nbsp;

## Unit-Tests

`src/core/` ist der ideale Ausgangspunkt: **kein I/O, kein Netzwerk, kein Zustand außer Input**.
Jede Funktion ist isoliert testbar.

### Struktur

```
tests/
├── core/
│   ├── test_rule_engine.py
│   ├── test_block_scheduler.py
│   ├── test_energy_context.py
│   └── test_override_handler.py
├── adapters/
│   ├── test_telemetry_ingest.py
│   └── test_actuation_writer.py
├── explain/
│   └── test_explain_agent.py
├── data/
│   └── test_event_log_store.py
└── ops/
    └── test_config_loader.py
```

### Beispiel: Rule Engine

```python
def test_safety_rule_overrides_optimisation():
    """R1 (Safety) muss R4 (Optimierung) immer überstimmen."""
    state = EnergyState(
        battery_temp_c=62.0,   # über Schwelle → Safety greift
        pv_surplus_w=800.0,
        grid_price=0.04,
    )
    decision = rule_engine.evaluate(state)

    assert decision.rule == "R1_SAFETY"
    assert decision.action == "STOP_MINER"


def test_deadband_prevents_flapping():
    """Zwei identische States innerhalb des Blockfensters → gleiche Decision."""
    state = EnergyState(pv_surplus_w=450.0, ...)
    d1 = rule_engine.evaluate(state)
    d2 = rule_engine.evaluate(state)  # selber Block, kein Reload

    assert d1.valid_until == d2.valid_until
    assert d1.action == d2.action
```

### Kritische Unit-Test-Szenarien

| Szenario | Warum kritisch |
|----------|---------------|
| R1 Safety überstimmt alle anderen Regeln | Harte Sicherheitsanforderung |
| R2 Autarkie schlägt R4 Optimierung | Prioritätsreihenfolge muss stimmen |
| Deadband hält Decision stabil | Kein Flapping, Hardware-Schonung |
| Override mit TTL läuft korrekt ab | Manuelle Eingriffe müssen sich selbst beenden |
| `EnergyState` mit unvollständigen Messwerten | Graceful Degradation, kein Absturz |
| Block-Tick-Auswertung ≤ 300 ms | Performance-Anforderung aus dem Qualitätsbaum |

&nbsp;

## Integrationstests

Testen das Zusammenspiel von Modulen mit echten Protokollen –
aber kontrolliert, ohne physische Hardware.

### MQTT-Integration

```python
@pytest.fixture
def mqtt_broker():
    """Startet einen echten Mosquitto-Container für den Test."""
    with MosquittoContainer() as broker:
        yield broker

def test_telemetry_ingest_updates_energy_state(mqtt_broker):
    """Veröffentlichtes MQTT-Topic aktualisiert den EnergyState."""
    ingest = TelemetryIngest(broker_url=mqtt_broker.url)
    mqtt_broker.publish("bitgridai/home/inverter/sma1/active_power_w", 750)

    state = ingest.get_current_state()
    assert state.pv_power_w == 750.0
```

### SQLite-Integration

```python
def test_decision_event_persisted(tmp_path):
    """DecisionEvent wird vollständig in SQLite geschrieben."""
    db = OperationalDB(path=tmp_path / "test.sqlite")
    event = DecisionEvent(rule="R2", action="CHARGE_BATTERY", ...)

    db.write(event)
    loaded = db.get_latest_event()

    assert loaded.rule == "R2"
    assert loaded.action == "CHARGE_BATTERY"
```

&nbsp;

## Replay-Tests

Das mächtigste Werkzeug im BitGridAI-Testprozess.

**Idee:** Historische `DecisionEvents` aus `data/logs/` erneut durch den Core laufen lassen –
das Ergebnis muss identisch sein.

```
Historische Events (Parquet)
        │
        ▼
    sim/replay.py       ← lädt Events, simuliert Zustand
        │
        ▼
    core/rule_engine    ← wertet aus
        │
        ▼
    Erwartete Decision  ← muss mit Original übereinstimmen
```

### Wann Replay-Tests laufen

- **Vor jedem Merge auf `main`** — sichert, dass Refactoring das Verhalten nicht verändert
- **Vor Updates** — bevor ein neues Image deployed wird (→ [Kapitel 35 – CI/CD](../35_cicd/README.md))
- **Nach Regeländerungen** — explizite Verifikation der neuen Entscheidungslogik

```python
def test_replay_produces_identical_decisions(historical_events):
    """Replay historischer Events muss exakt gleiche Decisions liefern."""
    for recorded in historical_events:
        replayed = rule_engine.evaluate(recorded.state)
        assert replayed.action == recorded.decision.action
        assert replayed.rule == recorded.decision.rule
```

&nbsp;

## Qualitätsgates

Alle Gates laufen automatisch — lokal und im CI.

### Formatierung — Black

```bash
black --check src/ tests/
```

Kein Spielraum für Diskussionen über Formatierung.
Black entscheidet. Immer.

### Typen — mypy

```bash
mypy src/ --strict
```

Strikte Typisierung ist Pflicht (Konvention aus [02.3](../../architecture/02_architecture_constraints/023_conventions.md)).
Jede Funktionssignatur braucht vollständige Type Hints.

### Tests & Coverage — pytest

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

| Modul | Ziel-Coverage |
|-------|--------------|
| `core/` | **≥ 90 %** — deterministisch, kein I/O |
| `adapters/` | ≥ 70 % |
| `explain/` | ≥ 70 % |
| `data/` | ≥ 75 % |
| `ops/` | ≥ 65 % |

### Alles zusammen

```bash
# Vollständiger Qualitätscheck vor einem PR
black --check src/ tests/
mypy src/ --strict
pytest tests/ -v --cov=src
```

&nbsp;

## Testdaten & Fixtures

### `sim/` als Testdaten-Quelle

`src/sim/` stellt **vordefinierte Szenarien** bereit, die in Tests direkt nutzbar sind:

| Fixture | Beschreibung |
|---------|-------------|
| `sunny_day_surplus` | PV-Überschuss 800 W, Batterie 60 %, grid-Preis niedrig |
| `battery_critical` | SoC unter Schwelle → R2 Autarkie greift |
| `overheating` | Temperatur > 60 °C → R1 Safety greift |
| `no_pv_night` | Nacht, kein PV, Miner läuft auf Grid |
| `manual_override_active` | Laufender Override mit TTL = 25 min |

### Konfigurations-Fixtures

Konfigurationen für Tests liegen unter `tests/fixtures/config/` –
immer als vollständige, valide YAML-Dateien.

&nbsp;

## Verbotenes in Tests

| Verboten | Warum | Stattdessen |
|---------|-------|------------|
| Echte Hardware ansprechen | Nicht reproduzierbar | MQTT-Container, Mocks |
| Auf `data/` des Live-Systems zugreifen | Seiteneffekte | `tmp_path`-Fixtures |
| `time.sleep()` | Langsam und flaky | `freezegun` oder Mock-Clock |
| Zufallswerte ohne Seed | Nicht deterministisch | Feste Fixtures |
| Netzwerkanfragen nach außen | Offline-Umgebung | `httpx` mit `respx`-Mock |

&nbsp;

## Qualitätsmerkmale aus dem Qualitätsbaum — wie wir sie testen

| Qualitätsmerkmal | Wie getestet |
|-----------------|-------------|
| Safety (R1 greift immer) | Unit: Temperatur-/SoC-Schwellen-Tests |
| Determinismus | Replay-Tests: gleicher Input → gleicher Output |
| Stabilität / kein Flapping | Unit: Deadband hält Decision stabil |
| Block-Tick < 300 ms | Performance-Test mit `pytest-benchmark` |
| Explainability | Unit: jeder `DecisionEvent` hat `reason`, `trigger`, `params` |
| Append-only Logs | Integration: kein UPDATE/DELETE in SQLite/Parquet |
| Graceful Degradation | Unit: fehlende Messwerte → Safe-State, kein Absturz |

---

> **Nächster Schritt:** Tests grün. Jetzt reden wir darüber, wie der Code automatisch gebaut, geprüft und deployed wird.
>
> 👉 Weiter zu **[35 – CI/CD & Deployment](../35_cicd/README.md)**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
