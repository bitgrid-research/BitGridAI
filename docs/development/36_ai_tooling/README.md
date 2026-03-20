# 36 – AI-Agenten & Tooling

BitGridAI wird mit KI-Unterstützung gebaut — aber nach klaren Regeln.

Zwei Agenten arbeiten zusammen, jeder mit eigenem Kontext, eigener Rolle und eigenen Grenzen.
**₿itsy** lebt auf dem Umbrel-Server. **Claude Code** läuft in VSCode auf dem Entwicklungsrechner.
Beide kennen die Projektprinzipien. Beide dürfen widersprechen.

> **Wichtig:** KI unterstützt — sie entscheidet nicht.
> Architekturprinzipien, Red Lines und Qualitätsziele gelten für Agenten genauso wie für Code.

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
│  ₿itsy-Home · ₿itsy-Study                           │
│  lesen Events → erzeugen Text → niemals steuern      │
└──────────────────────────────────────────────────────┘
```

**Die Linie ist absolut:** Kein KI-Agent hat Schreibzugriff auf Aktoren,
Regeln oder Override-Endpunkte. Auch nicht auf Bitte des Nutzers.

&nbsp;

## Vier Agenten, drei Rollen

```
Entwicklungsrechner                  Umbrel Server (LAN)
┌──────────────────┐     ┌───────────────────────────────────────────┐
│  Claude Code     │     │  ₿itsy-Dev     (bitsy-dev/)               │
│  (VSCode)        │◄────►│  Projektassistent, arc42, Entwicklung     │
│  Code · Docs     │     │  Modell: Qwen3:14b                        │
└──────────────────┘     ├───────────────────────────────────────────┤
                         │  ₿itsy-Home    (bitsy-home/)              │
                         │  Erklärung für Heimnutzer                 │
                         │  Modell: Qwen3:4b  (schnell)              │
                         ├───────────────────────────────────────────┤
                         │  ₿itsy-Study   (bitsy-study/)             │
                         │  Erklärung für Forscher & Studie          │
                         │  Modell: Qwen3:14b (präzise)              │
                         └───────────────────────────────────────────┘
```

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

### Kontext-Dateien

Claude Code liest automatisch:

```
CLAUDE.md          ← Projektweite Instruktionen (falls vorhanden)
docs/              ← Architektur, Forschung, Entwicklungs-Docs
src/               ← vollständiger Quellcode
```

&nbsp;

---

## ₿itsy-Dev — Projektassistent für Entwicklung

Läuft auf Umbrel, kennt das Projekt von Grund auf.
Technischer Sparringspartner, kein Ja-Sager. Prüft Vorschläge gegen Projektprinzipien.

**Workspace:** `docs/development/36_ai_tooling/bitsy-dev/`

```
bitsy-dev/
├── SOUL.md           ← Werte, Stil, Domainwissen, BP-01–BP-21
├── IDENTITY.md       ← Name, Zweck, Grenzen
├── USER.md           ← Wer der Entwickler ist, wie er denkt
├── AGENTS.md         ← Session-Startup, Heartbeat-Regeln, Red Lines
├── TOOLS.md          ← IPs, Ports, Pfade, Modelle
├── PROJECT_STATE.md  ← Aktueller Stand des Repos (gepflegt)
├── BOOTSTRAP.md      ← Einmalig: Initialisierung
├── HEARTBEAT.md      ← Aktuelle Aufgaben für den nächsten Heartbeat
└── MEMORY.md         ← Langzeit-Gedächtnis (nur Main-Session)
```

**Session-Startup:**
```
1. SOUL.md          → wer bin ich?
2. USER.md          → wen helfe ich?
3. PROJECT_STATE.md → wo stehen wir?
4. memory/HEUTE.md  → was war gestern?
5. MEMORY.md        → (nur Main-Session) Langzeitkontext
```

**Modell:** Qwen3:14b — kein Cloud-Backhaul, keine Telemetrie.

&nbsp;

---

## ₿itsy-Home — Erklärung für Heimnutzer

Erklärt dem Prosumer was das System gerade tut und warum.
Kein Jargon. Kurze Sätze. Zahlen mit Einheit.
**Kein Schreibzugriff. Keine Aktorbefehle.**

**Workspace:** `docs/development/36_ai_tooling/bitsy-home/`

```
bitsy-home/
├── SOUL.md       ← Ton, Grenzen, Beispielantworten
├── IDENTITY.md   ← Zweck, Modell, Datenquellen
├── USER.md       ← Der Heimnutzer — was er will, wie er denkt
├── AGENTS.md     ← Session-Startup, erlaubte Endpunkte, Red Lines
├── TOOLS.md      ← API-Endpunkte (read-only), Modell
└── BOOTSTRAP.md  ← Einmalig: Initialisierung
```

**Datenquellen (read-only):**
- `GET /state` — aktueller EnergyState
- `GET /timeline` — letzte Entscheidungsblöcke
- `GET /preview` — nächster Block (Prognose)

**Modell:** Qwen3:4b — schnell, ressourcenschonend für Erkläraufgaben.

&nbsp;

---

## ₿itsy-Study — Erklärung für Forscher & Studie

Unterstützt Studienteilnehmer und Forscher beim Verstehen von Systementscheidungen,
KPIs und Szenarien. Strukturiert, neutral, quellengenau.
**Kein Schreibzugriff. Keine Aktorbefehle.**

**Workspace:** `docs/development/36_ai_tooling/bitsy-study/`

```
bitsy-study/
├── SOUL.md       ← Ton, Grenzen, Beispiele für beide Zielgruppen
├── IDENTITY.md   ← Zweck, Modell, Datenquellen
├── USER.md       ← Studienteilnehmer vs. Forscher — unterschiedliche Bedürfnisse
├── AGENTS.md     ← Session-Startup, Opt-in-Prüfung, Red Lines
├── TOOLS.md      ← API-Endpunkte inkl. /research/export, Export-Format
└── BOOTSTRAP.md  ← Einmalig: Initialisierung
```

**Datenquellen (read-only):**
- `GET /state`, `GET /timeline`, `GET /preview`
- `GET /research/export` — nur bei aktivem Opt-in

**Export-Bundle enthält:** `decisions.parquet`, `states.parquet`, `kpis.json`, `manifest.json`

**Modell:** Qwen3:14b — für präzise Auswertung und strukturierte Outputs.

&nbsp;

---

## Vergleich der drei ₿itsy-Varianten

| | ₿itsy-Dev | ₿itsy-Home | ₿itsy-Study |
|--|-----------|-----------|------------|
| **Zielgruppe** | Entwickler | Heimnutzer | Forscher + Teilnehmer |
| **Ton** | technisch, direkt | klar, alltagsnah | neutral, strukturiert |
| **Kennt Codebase** | ja | nein | nein |
| **Kennt arc42** | ja | nein | nein |
| **Langzeitgedächtnis** | ja (MEMORY.md) | nein | nein |
| **Datenzugang** | Repo, Git, Docs | /state, /timeline, /preview | + /research/export |
| **Schreibzugriff** | Docs, Code (auf Anfrage) | **keiner** | **keiner** |
| **Aktorzugriff** | **keiner** | **keiner** | **keiner** |
| **Modell** | Qwen3:14b | Qwen3:4b | Qwen3:14b |

&nbsp;

---

## Zusammenspiel aller Agenten

| Situation | Claude Code | ₿itsy-Dev | ₿itsy-Home | ₿itsy-Study |
|-----------|------------|-----------|-----------|------------|
| Feature implementieren | schreibt Code + Tests | prüft Architekturfit | — | — |
| Docs ausarbeiten | schreibt Markdown | reviewed Konsistenz | — | — |
| Nutzer fragt warum Miner läuft | — | — | erklärt in Klartext | — |
| Forscher analysiert Szenario B | — | — | — | zeigt DecisionEvents, KPIs |
| Studienteilnehmer fragt nach KPIs | — | — | — | erklärt Autarkie-Quote |
| Architekturentscheidung | zeigt arc42-Kapitel | empfiehlt anhand BP | — | — |

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
| Claude Code | Claude Sonnet (Anthropic) | Dev-Rechner | nein (API) |
| ₿itsy | Qwen3:14b | Umbrel (lokal) | **ja** |

₿itsy läuft vollständig offline — auch wenn kein Internet verfügbar ist.
Claude Code benötigt die Anthropic API — für Code-Arbeit am Dev-Rechner ist das der Trade-off.

&nbsp;

---

## Erweiterbarkeit

Neue Agenten oder Modelle lassen sich über OpenClaw hinzufügen.
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
