# Onboarding HiWi 2 — UI, Explainability & Studie

Willkommen im BitGridAI-Projekt. Diese Seite führt dich durch den Einstieg in deinen Schwerpunkt: Benutzeroberfläche, erklärbare KI-Ausgaben und die zielgruppengerechte Aufbereitung der Erklärungen.

> **Hinweis zur Nutzerstudie:** Die Studie vergleicht nur zwei Erklärformate, **A (statischer Regeltext)** vs. **B (LLM-Erklärung in einer generischen Stimme)** — **ohne Personas**. Gemessen wird primär das **Nutzervertrauen** (FF1) und die **Güte** der LLM-Ausgaben (FF2). Die unten genannten „Zielgruppen" (Heimnutzer vs. Forscher, ₿itsy-Home/₿itsy-Study) betreffen die zielgruppengerechte UI-Gestaltung, **nicht** den Studien-Faktor.

---

## Dein Bereich im Repo

```
src/
├── ui/             ← Web-Interface, Dashboard, API-Endpunkte
├── explain/        ← Erklärungsschicht (KI erlaubt, read-only)
│   └──             ← Liest DecisionEvents, schreibt keine Entscheidungen
└── ha/
    └── config/
        └── bitgrid-dashboard.yaml   ← HA-Dashboard (Lovelace)
```

**Kernprinzip das du verstehen musst:**
Die KI in `src/explain/` darf nur **lesen und erklären** — niemals entscheiden oder schreiben. Der Entscheidungskern (`src/core/`) ist bewusst regelbasiert und KI-frei. Das ist kein Fehler, sondern das Forschungsdesign: Transparenz vor Komfort.

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

# 3. System starten (Simulation reicht zum Einstieg)
cp .env.example .env
cd src/ha && docker compose up -d
# HA erreichbar unter http://localhost:8123
```

---

## Erste Aufgaben (Vorschlag)

1. **HA-Dashboard verstehen** — `src/ha/config/bitgrid-dashboard.yaml` lesen, Dashboard im Browser erkunden
2. **DecisionEvent verstehen** — `src/core/models.py` lesen: was steckt in einem Event?
3. **Explain-Schicht erkunden** — `src/explain/` lesen: wie werden Events in Text übersetzt?
4. **Zielgruppen-Anforderungen ableiten** — Welche Infos braucht ein Heimnutzer vs. ein Forscher? (`₿itsy-Home` vs. `₿itsy-Study`) — eine UI-Frage, unabhängig vom Studien-A/B-Faktor

---

## Wichtige Konzepte

### Zielgruppen → Erklärungstiefe (₿itsy-Agenten)

| Agent / Zielgruppe | Modell | Erklärungstiefe |
|---|---|---|
| ₿itsy-Home (Heimnutzer) | Qwen3:4b | einfach, alltagsnah |
| ₿itsy-Study (Forscher) | Qwen3:14b | technisch, mit Parametern |

Beide lesen `DecisionEvents` read-only. Deine Aufgabe: herausarbeiten, was jede Zielgruppe braucht, und die UI entsprechend gestalten. Das ist eine Design-/UI-Frage und **getrennt** vom A/B-Vergleich der Studie (die Studie selbst nutzt für Gruppe B eine einzige generische Stimme).

### DecisionEvent — das zentrale Datenobjekt

Jede Systementscheidung erzeugt ein `DecisionEvent` mit:
- `action` — START / STOP / THROTTLE / NOOP
- `priority` — welche Regel hat entschieden (R1–R5)
- `reason` — maschinenlesbarer Code
- `explanation` — menschenlesbare Begründung
- `timestamp`, `energy_state` — Kontext

Das ist dein Rohmaterial für alle Visualisierungen und Erklärungen.

---

## Wichtige Make-Befehle

```bash
make check          # Pflicht vor jedem PR
make test-unit      # Tests für explain/, ui/
make fmt            # Autoformat
make up             # Docker Stack starten
make logs           # Container-Logs
```

---

## Ansprechpartner & Workflow

- Fragen zu Erklärbarkeit & KI-Agenten → `docs/development/36_ai_tooling/COLLABORATION.md`
- Workflow & Branching → `docs/development/32_workflow/README.md`
- PR öffnen → Checkliste im PR-Template ausfüllen, 1 Approval abwarten
