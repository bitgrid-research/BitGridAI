# 32 – Workflow & Branching

Wie arbeiten wir täglich mit Git? Wo landet welcher Code? Und wie sehen gute Commit-Nachrichten aus?

Dieses Kapitel beschreibt den vollständigen Entwicklungsablauf –
vom ersten Branch bis zum Merge auf `main`.

&nbsp;

## Branch-Strategie

BitGridAI nutzt ein einfaches **Feature-Branch-Modell**:

```
main
 └── feature/rule-engine-deadband
 └── fix/mqtt-reconnect-loop
 └── docs/chapter-33-components
 └── refactor/energy-state-dataclass
 └── chore/update-dependencies
```

| Branch-Typ | Präfix | Wann |
|------------|--------|------|
| Neue Funktion | `feature/` | Neue Fähigkeit, neues Modul |
| Bugfix | `fix/` | Fehlerkorrektur |
| Dokumentation | `docs/` | Nur Doku-Änderungen |
| Refactoring | `refactor/` | Umstrukturierung ohne Verhaltensänderung |
| Wartung | `chore/` | Dependencies, Tooling, CI |

**Regeln:**
- Direkte Pushes auf `main` sind **verboten**
- Jeder Branch hat genau **einen klaren Zweck**
- Branches leben kurz – lieber klein und oft als groß und selten

&nbsp;

## Typischer Entwicklungszyklus

```
1.  main aktualisieren
    git checkout main && git pull

2.  Feature-Branch anlegen
    git checkout -b feature/mein-feature

3.  Entwickeln, testen, committen
    (mehrere kleine Commits)

4.  Vor dem PR: main rebasen
    git fetch origin
    git rebase origin/main

5.  Push & Pull Request öffnen
    git push -u origin feature/mein-feature

6.  Review → Merge → Branch löschen
```

&nbsp;

## Conventional Commits

Commit-Nachrichten folgen dem [Conventional Commits](https://www.conventionalcommits.org)-Standard.
Das macht den Verlauf maschinell auswertbar und für Menschen lesbar.

### Format

```
<typ>(<scope>): <kurze Beschreibung>

[optionaler Body]

[optionaler Footer, z.B. BREAKING CHANGE: ...]
```

### Typen

| Typ | Wann |
|-----|------|
| `feat` | Neue Funktion |
| `fix` | Bugfix |
| `docs` | Nur Dokumentation |
| `refactor` | Umstrukturierung, kein neues Verhalten |
| `test` | Tests hinzugefügt oder geändert |
| `chore` | Tooling, Dependencies, CI |
| `perf` | Performance-Verbesserung |
| `style` | Formatierung, kein inhaltlicher Unterschied |

### Scopes (Modulbezug)

| Scope | Zugehöriges Modul |
|-------|------------------|
| `core` | `src/core/` |
| `adapters` | `src/adapters/` |
| `explain` | `src/explain/` |
| `data` | `src/data/` |
| `sim` | `src/sim/` |
| `ops` | `src/ops/` |
| `ui` | `src/ui/` |
| `ha` | `src/ha/` |
| `docs` | `docs/` |
| `ci` | Pipeline, Docker, Tooling |

### Beispiele

```bash
# Neue Funktion
feat(core): add deadband stability check to rule engine

# Bugfix mit Scope
fix(adapters): resolve MQTT reconnect loop on broker restart

# Dokumentation
docs(development): elaborate chapter 32 workflow and branching

# Refactoring
refactor(core): convert EnergyState to dataclass

# Breaking Change
feat(core)!: replace rule priority list with weighted scoring

BREAKING CHANGE: Rule R1-R5 priority config format changed.
See migration guide in docs/development/37_troubleshooting/
```

&nbsp;

## Pull Request Prozess

### PR öffnen

Ein guter PR ist **klein, fokussiert und selbsterklärend**.

**Titel:** Corresponding Conventional Commit — z.B. `feat(core): add deadband stability check`

**Beschreibung enthält:**
- Was wurde geändert und warum?
- Welche Architekturentscheidung steckt dahinter (falls relevant)?
- Wie wurde getestet?
- Breaking Changes?

### Review-Checkliste

Vor dem Merge prüfen:

- [ ] Tests vorhanden und grün
- [ ] Schichtregeln eingehalten (kein `adapters/` → DB, kein `core/` → `ui/`)
- [ ] Type Hints vollständig
- [ ] Docstrings für öffentliche Klassen/Funktionen
- [ ] Keine hardcodierten Pfade, Ports oder Secrets
- [ ] `docker compose up` bricht nicht

### Merge-Strategie

**Squash & Merge** für Feature-Branches — ein sauberer Commit auf `main` pro Feature.

```
# Ergebnis auf main:
feat(core): add deadband stability check to rule engine (#42)
```

&nbsp;

## Täglicher Git-Workflow (Kurzreferenz)

```bash
# Neuen Branch starten
git checkout main && git pull
git checkout -b feature/mein-feature

# Änderungen committen
git add src/core/rule_engine.py tests/core/test_rule_engine.py
git commit -m "feat(core): add deadband stability check"

# Mehrere Commits im Laufe des Tages — kein Problem
git commit -m "test(core): add edge case for zero surplus"
git commit -m "docs(core): update rule_engine docstring"

# Vor dem PR: auf Stand bringen
git fetch origin
git rebase origin/main

# Push
git push -u origin feature/mein-feature
```

&nbsp;

## Was Claude Code dabei übernimmt

Claude Code (siehe [36 – AI-Agenten & Tooling](../36_ai_tooling/README.md)) unterstützt aktiv im Workflow:

| Aufgabe | Claude Code hilft mit |
|---------|-----------------------|
| Branch benennen | Schlägt Präfix + beschreibenden Namen vor |
| Commit-Nachrichten | Generiert Conventional-Commit-Format aus Diff |
| PR-Beschreibung | Fasst Änderungen und Motivation zusammen |
| Review-Vorbereitung | Prüft Schichtregeln, Type Hints, fehlende Tests |

&nbsp;

## Häufige Fehler

| Fehler | Konsequenz | Besser |
|--------|-----------|--------|
| Direkt auf `main` committen | Verlauf unklar, kein Review | Feature-Branch anlegen |
| Branch zu lange leben lassen | Große Merge-Konflikte | Täglich `rebase origin/main` |
| Kryptische Commits (`fix stuff`) | Verlauf unlesbar | Conventional Commits nutzen |
| Zu viele Änderungen in einem PR | Review-Last, schwer rückrollbar | Einen klaren Scope pro PR |
| Secrets in `.env` eingecheckt | Sicherheitsrisiko | `.env` ist in `.gitignore` |

---

> **Nächster Schritt:** Workflow klar.
> Jetzt schauen wir uns an, wie die einzelnen Module intern aufgebaut sind.
>
> 👉 Weiter zu **[33 – Komponenten & Module](../33_components/README.md)**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
