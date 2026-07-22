# 36 – AI-Agenten & Tooling

BitGridAI wird mit KI-Unterstützung gebaut — aber nach klaren Regeln.

**Real und aktiv sind genau zwei Agenten:** **Claude Code** (VSCode,
Entwicklungsrechner) und **Neo** (Hermes Agent auf Umbrel, nächtliche
Energie-Musteranalyse). Alles andere in diesem Ordner — ₿itsy-Home,
₿itsy-Study, DEV-BitHamster — sind Personas, die entworfen, aber **nie
deployt** wurden (Archiv weiter unten). Verschlankt am 22.07.2026, um Docs und
Realität wieder deckungsgleich zu machen.

> **Wichtig:** KI unterstützt — sie entscheidet nicht.
> Architekturprinzipien, Red Lines und Qualitätsziele gelten für Agenten genauso wie für Code.

**Wie beide zusammenarbeiten:** [`COLLABORATION.md`](./COLLABORATION.md)

&nbsp;

## Architektur: KI nur in der Erklärungsschicht

```
┌──────────────────────────────────────────────────────┐
│  STEUERUNG  (niemals KI)                             │
│  core/ → R1–R5 → Decision → Aktoren                 │
│  deterministisch · regelbasiert · replay-fähig       │
└───────────────────────┬──────────────────────────────┘
                        │ DecisionEvent (read-only)
                        ▼
┌──────────────────────────────────────────────────────┐
│  ERKLÄRUNGSSCHICHT  (KI erlaubt)                     │
│  Neo — liest Fakten, sucht Muster, schreibt          │
│  Hypothesen, steuert nie                             │
└──────────────────────────────────────────────────────┘
```

**Die Linie ist absolut:** Kein KI-Agent hat Schreibzugriff auf Aktoren,
Regeln oder Override-Endpunkte. Auch nicht auf Bitte des Nutzers.

&nbsp;

## Zwei Agenten, real im Einsatz

```
Entwicklungsrechner                  Haupt-Umbrel (LAN)
┌──────────────────┐     ┌───────────────────────────────────────────┐
│  Claude Code     │     │  Neo — Nachtforscher    (neo/)            │
│  (VSCode)        │◄────►│  Naechtliche Energie-/Mining-Analyse       │
│  Code · Docs     │     │  Modell: gemma4:e4b (Ollama, lokal)       │
└──────────────────┘     └───────────────────────────────────────────┘
```

Neo lief bis zum 22.07.2026 unter dem Namen ₿itsy-Dev als
Repo-/arc42-Review-Assistent (siehe `neo/FINDINGS.md`, seit 28.06.2026
inaktiv gewesen). Gleiche Hermes-Agent-Instanz, neue, schmalere Rolle.

&nbsp;

---

## Claude Code — der Coding-Assistent

Claude Code ist die VSCode-Extension für alle aktiven Entwicklungsaufgaben.

### Was Claude Code macht

| Aufgabe | Wie |
|---------|-----|
| Code schreiben & refactoren | direkt in der IDE, kennt den vollen Repo-Kontext |
| Dokumentation ausarbeiten | Markdown-Dateien in `docs/` schreiben und pflegen |
| Tests generieren | Unit-Tests aus bestehenden Klassen und Interfaces |
| Commit-Nachrichten | Conventional-Commit-Format aus dem Diff |
| PR-Beschreibungen | Zusammenfassung von Änderungen + Motivation |
| Code-Review-Vorbereitung | Schichtregeln, Type Hints, fehlende Docstrings prüfen |
| Architektur-Queries | Kapitel aus `docs/architecture/` direkt lesen und erklären |

### Was Claude Code nicht macht

- Keine Deployment-Entscheidungen ohne Bestätigung
- Keine Änderungen an `main` ohne PR
- Keine Cloud-Abhängigkeiten in den Code einführen
- Keine Blackbox-AI in `src/core/` — der Entscheidungskern bleibt deterministisch

### Workspace

**Workspace:** `docs/development/36_ai_tooling/claude-code/`

```
claude-code/
├── README.md     ← Tool-Überblick, Aufgaben, Zusammenspiel mit ₿itsy
└── SKILL.md      ← Slash Commands & Projekt-Skills, typische Workflows
```

### Kontext-Dateien

Claude Code liest automatisch:

```
CLAUDE.md          ← Projektweite Instruktionen (Repo-Root)
docs/              ← Architektur, Forschung, Entwicklungs-Docs
src/               ← vollständiger Quellcode
```

### UI-Design-Workflow

Google Stitch → `design.md` → Claude Code setzt um: [`stitch-ui/README.md`](./stitch-ui/README.md)

&nbsp;

---

## Neo — Nachtforscher

Läuft auf Umbrel (Hermes Agent), analysiert nachts per Cron (01:00 UTC) die
Energie-/Mining-Fakten des Tages und schreibt höchstens drei falsifizierbare
Hypothesen. Kein Ja-Sager, aber auch kein Repo-Reviewer mehr: diese Instanz
hieß bis 22.07.2026 ₿itsy-Dev und machte arc42-/Code-Reviews (archiviert,
siehe unten), die Rolle wurde bewusst verschmälert.

**Workspace:** `docs/development/36_ai_tooling/neo/`

```
neo/
├── README.md         ← Überblick, Live-Config vs. dieser Ordner
├── SOUL.md            ← Identität, Charakter, Regeln (Spiegel der Live-Version)
├── IDENTITY.md        ← Name, Zweck, Grenzen, Vorgeschichte (₿itsy-Dev → Neo)
├── USER.md            ← Wer der Betreiber ist, wie er denkt
├── TOOLS.md            ← IPs, Ports, Mounts, Modellwahl-Begründung
├── FINDINGS.md         ← ARCHIVIERT: alte ₿itsy-Dev-Repo-Befunde (bis 28.06.2026)
└── PROJECT_STATE.md    ← ARCHIVIERT: Repo-Snapshot zur Zeit von ₿itsy-Dev
```

**Lesereihenfolge pro Nacht** (im Vault, nicht in diesem Ordner):
`00_START_HIER.md` → `kontext/leitplanken.md` → `kontext/automation.md` →
`kontext/entities.md` → `kontext/architektur_rahmen.md` → `kontext/*.md` (Rest) →
`bestaetigt/README.md` → Tagesbericht.

**Modell:** `gemma4:e4b` — kein Cloud-Backhaul, keine Telemetrie. Begründung
der Modellwahl (gegen `qwen3:30b`, `llama3.1:8b` getestet): `neo/TOOLS.md`.

**Eigenes Gedächtnis:** `memory_neo/` im Obsidian-Vault, read-write, getrennt
vom read-only Wissensordner. Struktur und Regeln (BELEGT vs. GEDANKE):
`neo/SOUL.md`.

&nbsp;

---

## Archiv: entworfen, nie deployt

Drei weitere Personas wurden für dieses Projekt konzipiert, laufen aber nicht
und liefen nie als eigene Dienste. Sie bleiben als Design-Referenz im Repo,
nicht als aktives Tooling:

| Persona | Gedacht für | Workspace | Status |
|---|---|---|---|
| ₿itsy-Home | Erklärung für Heimnutzer (Klartext, keine Aktorbefehle) | `bitsy-home/` | nie deployt |
| ₿itsy-Study | Erklärung für Forscher & Studienteilnehmer, inkl. Export | `bitsy-study/` | nie deployt |
| DEV-BitHamster | Solar-Mining-Analyse auf eigener Umbrel-Instanz | `hermes-bithamster/` | nie deployt, Infra (`.62`) existiert nicht mehr |

Falls eine dieser Rollen später gebraucht wird: das Workspace-Schema
(`SOUL.md`, `IDENTITY.md`, `TOOLS.md`) ist bereits vollständig entworfen, nur
nicht ans Netz gebracht.

&nbsp;

---

## Prompt-Konventionen

### Sprache

- **Docs:** Deutsch — immer
- **Code & Kommentare:** Englisch — immer
- **Commits:** Englisch (Conventional Commits)
- **Agenten-Kommunikation:** Deutsch wenn der Nutzer auf Deutsch schreibt

### Strukturhilfen für bessere Ergebnisse

```
# Kontext mitgeben
"Schau dir Kapitel 05.2.1 an — wie sollte die Rule Engine-Schnittstelle aussehen?"

# Scope eingrenzen
"Nur src/core/ — kein Refactoring außerhalb"

# Prinzip nennen wenn relevant
"Deterministisch muss es bleiben — kein ML im Core"

# Erwartetes Format nennen
"Conventional Commit Nachricht für diesen Diff"
```

### Red Lines — was KI in diesem Projekt nie tut

| Verboten | Warum |
|---------|-------|
| Blackbox-ML in `src/core/` | Deterministisch-Prinzip (BP-08) |
| Cloud-Dependencies vorschlagen | Local-First (BP-01, BP-02) |
| Externe APIs ohne lokale Alternative | Vendor Lock-In (BP-02) |
| Telemetrie oder Tracking | Privacy by Default (BP-05) |
| Commits auf `main` ohne Review | Git-Workflow (Kapitel 32) |
| Destructive Commands ohne Bestätigung | Safety-Grundregel |

&nbsp;

---

## Modelle & Infrastruktur

| Agent | Modell | Läuft auf | Offline-fähig |
|-------|--------|-----------|--------------|
| Claude Code | Claude Opus 4.8 (Anthropic) | Dev-Rechner | nein (API) |
| Neo | `gemma4:e4b` (Ollama) | Haupt-Umbrel (lokal) | **ja** |

Neo läuft vollständig offline — auch wenn kein Internet verfügbar ist.
Claude Code benötigt die Anthropic API — für Code-Arbeit am Dev-Rechner ist das der Trade-off.

&nbsp;

---

## Erweiterbarkeit

Neue Agenten oder Modelle lassen sich über Hermes Agent hinzufügen.
Das Workspace-Schema (`SOUL.md`, `AGENTS.md`, `TOOLS.md`) ist portierbar —
ein neuer Agent für eine spezifische Aufgabe (z.B. Research-Analyse) bekommt denselben Rahmen.

---

> **Nächster Schritt:** Tooling verstanden.
> Zum Abschluss: Troubleshooting — was tun wenn's hakt.
>
> 👉 Weiter zu **[37 – Troubleshooting & FAQ](../37_troubleshooting/README.md)**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
