# 30.0 – Schnelleinstieg

Du willst sofort loslegen? Hier ist alles in **5 Minuten**.

---

## 1 — Repository klonen

```powershell
git clone <repo-url> BitGridAI
cd BitGridAI
```

> Repo-URL beim Projektverantwortlichen erfragen oder im internen Projektbereich nachschlagen.

&nbsp;

## 2 — Python-Umgebung einrichten

```powershell
# Virtuelle Umgebung anlegen und aktivieren
python -m venv .venv
.venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install -r requirements.txt
```

&nbsp;

## 3 — Tests laufen lassen

```powershell
pytest tests/
```

Erwartetes Ergebnis:

```
50 passed in 0.16s
```

Wenn alle Tests grün sind: Umgebung ist korrekt eingerichtet.

&nbsp;

## 4 — Simulation starten (ohne Hardware)

```powershell
# SH-1: Stabiler PV-Überschuss — Entscheidungen live verfolgen
$env:PYTHONPATH = "."; python -m src.sim.runner `
  --scenario src/sim/scenarios/sh1_stable_surplus.csv `
  --speed 60

# SH-4: Übertemperatur — R3-Safety-Stop beobachten
$env:PYTHONPATH = "."; python -m src.sim.runner `
  --scenario src/sim/scenarios/sh4_safety_overtemp.csv `
  --speed 60
```

**Was du siehst:**

```json
{"block": 1, "action": "START", "code": "START_R1_SURPLUS_OK", "surplus_kw": 2.4}
{"block": 2, "action": "NOOP",  "code": "NOOP_R5_MIN_RUNTIME_NOT_REACHED"}
{"block": 3, "action": "NOOP",  "code": "NOOP_R5_DEADBAND_ACTIVE"}
```

&nbsp;

## 5 — Docker-Stack starten (optional)

```powershell
# .env aus Vorlage anlegen
Copy-Item .env.example .env
# .env mit eigenen Werten befüllen (Adressen, Ports)

# Stack starten
docker compose up -d

# Status prüfen
docker compose ps

# Stack stoppen
docker compose down
```

&nbsp;

---

## Alles auf einmal — Qualitätscheck vor dem ersten PR

```powershell
make check
```

Entspricht:

```powershell
black --check src/ tests/   # Formatierung
mypy src/ --strict           # Typen
pytest tests/ -v --cov=src   # Tests + Coverage
```

&nbsp;

---

## Wo weiterlesen?

| Thema | Dokument |
|-------|----------|
| Vollständiges Setup (Python, Docker, VSCode) | [30.2 – Entwicklungsumgebung](./dev_environment.md) |
| SSH zum Edge-Gerät | [30.1 – SSH Setup](./ssh_windows_setup.md) |
| Projektstruktur & Module | [31 – Projektstruktur](../31_project_structure/README.md) |
| Git-Workflow & Branch-Strategie | [32 – Workflow](../32_workflow/README.md) |
| Wo fange ich im Code an? | [src/README.md](../../../src/README.md) — Abschnitt „Wo anfangen?" |

---

> 🔙 Zurück zu **[30 – Setup & Umgebung](./README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
