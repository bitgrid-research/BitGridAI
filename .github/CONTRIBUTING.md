# Mitarbeit an BitGridAI

Willkommen. Dieses Dokument beschreibt wie du als Mitarbeiter oder externer Beitragender ins Projekt einsteigst.

## Rollen

| Rolle | Schwerpunkt | Einstiegsdoku |
|---|---|---|
| HiWi 1 | Simulation, Rule-Engine, Infrastruktur | [onboarding_hiwi1.md](docs/development/30_setup/onboarding_hiwi1.md) |
| HiWi 2 | UI, Explainability, Personas | [onboarding_hiwi2.md](docs/development/30_setup/onboarding_hiwi2.md) |

## Schnellstart

```bash
# 1. Repo klonen
git clone <repo-url>
cd BitGridAI

# 2. Entwicklungsumgebung einrichten
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# 3. Vor jedem PR — muss grün sein
make check
```

## Die wichtigsten Regeln

**Architektur**
- `src/core/` ist der Entscheidungskern — kein ML, kein Zufall, keine Blackbox
- Schichttrennung ist absolut: `core/` importiert nichts aus `ui/`, `explain/` oder `adapters/`
- Neue Funktionen in `core/` brauchen immer Unit-Tests

**Git**
- Kein direkter Push auf `main` — immer PR
- Branches: `feature/`, `fix/`, `docs/`, `refactor/`, `chore/`
- Commits im [Conventional Commits](https://www.conventionalcommits.org)-Format
- Keine Secrets, keine IPs, keine echten Zugangsdaten im Code

**Qualität**
- `make check` muss lokal grün sein bevor ein PR geöffnet wird
- CI (GitHub Actions) muss grün sein bevor gemergt wird
- 1 Approval required

## Weiterführende Doku

| Thema | Datei |
|---|---|
| Architektur (arc42) | `docs/architecture/` |
| Workflow & Branching | `docs/development/32_workflow/README.md` |
| Komponenten & Module | `docs/development/33_components/README.md` |
| Testing | `docs/development/34_testing/README.md` |
| AI-Tooling (₿itsy, Claude) | `docs/development/36_ai_tooling/README.md` |
| Troubleshooting | `docs/development/37_troubleshooting/README.md` |
