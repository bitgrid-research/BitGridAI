# Zusammenarbeit: KI-Team – Neo, Claude Code & Stitch

Das KI-Team besteht aus drei Agenten mit klar getrennten Rollen.
Der gemeinsame Kanal für Neos Beobachtungen: **`nachtberichte/`** auf dem Umbrel-Server.
Design-Übergabe via **`src/ui/design.md`** (Stitch → Claude Code).

&nbsp;

## Rollen

| | Neo | Claude Code | Stitch |
|---|---|---|---|
| **Läuft auf** | Hermes-Agent auf Umbrel `.96:18790`, Modell von Ollama `.104` | Dev-Rechner (VSCode, API) | stitch.withgoogle.com (Cloud, via MCP) |
| **Modell** | `gemma4:e4b` (lokal auf `.104`) | Claude Opus 4.8 (Anthropic) | Google Stitch |
| **Arbeitet** | autonom, nachts (Cron 01:00 UTC) | auf direkten Auftrag | auf direkten Auftrag |
| **Stärke** | Muster-/Optimierungsanalyse in Energie-/Miningdaten | Implementierung, Tests, Docs schreiben | UI/UX Design, Design-System, Komponenten |
| **Schreibt in** | `nachtberichte/`, eigener Ordner `memory_neo/` | Code, Docs, Vault (nach Prüfung) | `src/ui/design.md` (Export oder MCP) |
| **Kein Zugriff auf** | `core/`, Vault (read-only), keine Konfiguration | — | `core/`, keine Entscheidungslogik |

&nbsp;

## Workflow: Neo → Claude Code

```
Neo                              nachtberichte/                  Claude Code
    │                                   │                              │
    │── liest Fakten + Vault ──────────►│                              │
    │── schreibt Hypothesen ───────────►│ JJJJ-MM-TT_hypothesen.md     │
    │                                   │◄─────────────────────────────│ liest, prüft gegen Repo/Anlage
    │                                   │                              │── übernimmt Geprüftes in Vault
    │                                   │                              │   (bestaetigt/ oder kontext/*.md)
    │                                   │                              │── baut Werkzeugwünsche
    │◄── liest übernommenes Wissen beim nächsten Lauf aus dem Vault ───│
```

**Der Betreiber vermittelt:** ein kurzer Hinweis reicht — Claude Code liest den
Bericht in `nachtberichte/` direkt, kein Copy-Paste nötig.

Neos eigenes Gedächtnis (`memory_neo/`, Obsidian) ist getrennt davon: dort
sammelt er selbst Zwischenstände (`kurzzeit.md`), Langzeit-Erkenntnisse
(`langzeit/JJJJ-MM.md`) und offene Gedanken (`gedanken.md`) über Nächte und
Neustarts hinweg. Details: [`neo/SOUL.md`](./neo/SOUL.md).

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

## nachtberichte/JJJJ-MM-TT_hypothesen.md — das geteilte Protokoll

### Neo schreibt (pro Nacht, höchstens drei)

```markdown
### Hypothese N
**Beobachtung:** was in den Fakten auffiel, mit Beleg (Datei/Abschnitt)
**Hypothese:** vermutete Ursache oder Optimierungspotenzial
**Änderung:** konkreter Vorschlag
**Erwarteter Effekt:** was sich ändern sollte
**Falsifikation:** unter welcher Bedingung die Hypothese widerlegt wäre
**Status:** Offen
```

Kein belastbarer Fund ist ein vollwertiges Ergebnis: dann schreibt Neo genau
einen Satz statt eine erzwungene Hypothese.

### Claude Code antwortet (nach Prüfung)

Übernommenes Wissen wandert in den Vault (`bestaetigt/README.md` oder eine
passende `kontext/*.md`-Datei), damit Neo es beim nächsten Lauf liest und
nicht erneut vorschlägt. Abgelehntes bleibt in `nachtberichte/` mit kurzer
Begründung, warum es nicht übernommen wurde.

&nbsp;

## Schweregrade & Eskalation

| Einordnung | Bedeutung | Wer handelt |
|---|---|---|
| **Sicherheitsrelevant** | Hypothese berührt Temperatur-/Netzschutz | Sofort prüfen, nicht auf den nächsten Zyklus warten |
| **Optimierung** | Mehr Sats/Tag ohne Zielkonflikt (siehe `kontext/architektur_rahmen.md`) | Claude Code prüft im normalen Rhythmus |
| **Zielkonflikt** | Mehr Sats, aber auf Kosten von Transparenz/Sicherheit/Vorhersagbarkeit | Mit dem Betreiber besprechen, nicht automatisch übernehmen |

&nbsp;

## Wichtige Regeln

**Neo:**
- Jede Zahl braucht eine Fundstelle (Faktenbericht oder Werkzeug-Antwort)
- Nichts eigenständig ändern — kein Terminal, keine Konfiguration, kein HA-Token
- Werkzeugwunsch statt Schätzung, wenn eine Abfrage fehlt

**Claude Code:**
- Hypothesen vor Übernahme immer gegen den tatsächlichen Repo-/Anlagenstand verifizieren
- Nach jeder SOUL.md-/Config-Änderung: Hermes neu starten **und**
  `scripts/reset_neo_session.py --yes` ausführen (sonst laufen bestehende
  Chat-Sessions mit der alten, gecachten Identität weiter)
- Abgelehnte Vorschläge nicht ignorieren — mit Begründung markieren

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
└── neo/
    ├── README.md                 ← Überblick, Live-Config vs. dieser Ordner
    ├── SOUL.md                   ← Spiegel der live deployten Identität/Regeln
    ├── IDENTITY.md                ← Name, Zweck, Grenzen, Vorgeschichte (₿itsy-Dev → Neo)
    ├── USER.md                    ← wer der Betreiber ist, wie er denkt
    ├── TOOLS.md                   ← IPs, Ports, Mounts, Modellwahl-Begründung
    ├── DESCRIPTION.md              ← Discord-Bot-Kurzbeschreibung (Portal-Spiegel)
    ├── FINDINGS.md                ← ARCHIVIERT: alte ₿itsy-Dev-Repo-Befunde
    └── PROJECT_STATE.md           ← ARCHIVIERT: Repo-Snapshot zur Zeit von ₿itsy-Dev
```
