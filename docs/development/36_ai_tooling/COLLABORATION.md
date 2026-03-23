# Zusammenarbeit: KI-Team – ₿itsy-Dev, Claude Code & Stitch

Das KI-Team besteht aus drei Agenten mit klar getrennten Rollen.
Der gemeinsame Kanal für Code & Architektur: **`bitsy-dev/FINDINGS.md`** im Git-Repo.
Design-Übergabe via **`src/ui/design.md`** (Stitch → Claude Code).

&nbsp;

## Rollen

| | ₿itsy-Dev | Claude Code | Stitch |
|---|---|---|---|
| **Läuft auf** | Umbrel (LAN, offline-fähig) | Dev-Rechner (VSCode, API) | stitch.withgoogle.com (Cloud, via MCP) |
| **Modell** | Qwen3:14b (lokal) | Claude Sonnet 4.6 (Anthropic) | Google Stitch |
| **Arbeitet** | autonom, im Hintergrund | auf direkten Auftrag | auf direkten Auftrag |
| **Stärke** | Repo-Analyse, arc42-Konsistenz, Langzeitgedächtnis | Implementierung, Tests, Docs schreiben | UI/UX Design, Design-System, Komponenten |
| **Schreibt in** | `FINDINGS.md`, `MEMORY.md`, `memory/` | Code, Docs, `FINDINGS.md` (Status) | `src/ui/design.md` (Export oder MCP) |
| **Kein Zugriff auf** | — | — | `core/`, keine Entscheidungslogik |

&nbsp;

## Workflow

```
₿itsy-Dev                         FINDINGS.md                    Claude Code
    │                                   │                              │
    │── analysiert Repo ────────────────►│ [Offen]                      │
    │                                   │◄─────────────────────────────│ liest beim nächsten Auftrag
    │                                   │                              │── verifiziert gegen Repo
    │                                   │                              │── fixt Problem
    │                                   │── [Erledigt / Falsch-Positiv]◄│
    │◄── Heartbeat: liest Status ───────│                              │
    │── Folgeanalyse wenn nötig ────────►│                              │
```

**Der Entwickler vermittelt:** Ein kurzer Hinweis ("schau dir die neuen Findings an") reicht —
Claude Code liest `FINDINGS.md` direkt, kein Copy-Paste nötig.

&nbsp;

## Stitch → Claude Code: Design-Übergabe

```
Stitch (Design-Prompt)
    │── generiert Screens + Design System
    │── exportiert design.md
    │        Option A: Copy/Paste → src/ui/design.md
    │        Option B: Stitch MCP → Claude Code liest direkt
    ▼
Claude Code
    │── liest src/ui/design.md
    │── implementiert UI in src/ui/
    └── ergänzt design.md bei neuen Komponenten
```

**Regel:** Stitch entwirft nur — `core/` und Entscheidungslogik sind tabu.
Feature-Drift prüfen: Stitch erfindet manchmal Features, die im Backend nicht existieren.

&nbsp;

## FINDINGS.md — das geteilte Protokoll

### ₿itsy-Dev schreibt (neue Findings)

```markdown
### [DATUM] [BEREICH] Kurztitel
**Datei:** `pfad/zur/datei.md` (Zeile X)
**Problem:** Was genau stimmt nicht?
**Schwere:** Kritisch / Mittel / Niedrig
**Empfehlung:** Was sollte getan werden?
**Status:** Offen
```

### Claude Code antwortet (Status-Update)

```markdown
**Status:** Erledigt — `pfad/zur/datei.md` angepasst (Claude Code, YYYY-MM-DD)
**Status:** Falsch-Positiv — Datei existiert, anderes Namensschema (Claude Code, YYYY-MM-DD)
**Status:** In Bearbeitung — größere Änderung, läuft (Claude Code, YYYY-MM-DD)
```

&nbsp;

## Schweregrade & Eskalation

| Schwere | Bedeutung | Wer handelt |
|---|---|---|
| **Kritisch** | Architekturprinzip verletzt, Datenverlust möglich | Sofort zum Entwickler — nicht eigenständig fixen |
| **Mittel** | Inkonsistenz, fehlendes Kapitel, falscher Link | Claude Code auf Hinweis des Entwicklers |
| **Niedrig** | Tippfehler, Formatierung, Stil | ₿itsy-Dev kann direkt korrigieren |

&nbsp;

## Wichtige Regeln

**₿itsy-Dev:**
- Findings immer mit Pfad, Zeile und konkretem Befund dokumentieren
- Nichts eigenständig ändern außer Tippfehler und offensichtliche Formatfehler
- Erledigte Findings beim nächsten Heartbeat prüfen — Folgeanalyse anstoßen wenn nötig

**Claude Code:**
- Findings vor Umsetzung immer gegen den tatsächlichen Repo-Stand verifizieren
- ₿itsy-Dev läuft auf Umbrel — Pfade oder Konventionen können von seiner Perspektive abweichen
- Nach jedem Fix: Status in FINDINGS.md aktualisieren und committen
- Falsch-Positive nicht ignorieren — mit Begründung markieren, damit ₿itsy-Dev dazulernt

&nbsp;

## Dateien im Überblick

```
36_ai_tooling/
├── COLLABORATION.md              ← dieses Dokument
├── claude-code/
│   ├── README.md                 ← Claude Code Tool-Überblick
│   └── SKILL.md                  ← Slash Commands & Workflows
├── stitch-ui/
│   ├── README.md                 ← Stitch Workflow-Guide (Design → Code)
│   └── DESIGN.md                 ← Stitch-Prompt für BitGridAI UI
└── bitsy-dev/
    ├── FINDINGS.md               ← geteilter Kanal: Befunde & Status
    ├── MEMORY.md                 ← ₿itsy-Dev Langzeitgedächtnis
    ├── PROJECT_STATE.md          ← Projektstatus + Hintergrundagenda
    ├── AGENTS.md                 ← ₿itsy-Dev Session & Heartbeat Regeln
    ├── COMMANDS.md               ← Slash Commands (/full-review etc.) + Trigger-Flag-Protokoll
    └── HEARTBEAT.md              ← aktive Checkliste + Trigger Flags (z. B. FULL_REVIEW_REQUESTED)
```
