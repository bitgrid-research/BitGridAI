# Claude Code

Claude Code ist die VSCode-Extension für alle aktiven Entwicklungsaufgaben in BitGridAI.
Läuft auf dem Dev-Rechner. Kennt das vollständige Repo. Arbeitet auf direkten Auftrag.

**Modell:** Claude Sonnet 4.6 (Anthropic API) — nicht offline-fähig

&nbsp;

## Konfiguration

Claude Code liest bei jeder Session automatisch:

```
CLAUDE.md       ← Projektweite Instruktionen (Repo-Root)
docs/           ← Architektur, Forschung, Entwicklungs-Docs
src/            ← vollständiger Quellcode
```

Die `CLAUDE.md` im Repo-Root enthält: Projektkontext, Schichtregeln, Dev-Commands,
Commit-Konventionen und Red Lines — alles was Claude Code über BitGridAI wissen muss.

&nbsp;

## Aufgaben

| Aufgabe | Wie |
|---|---|
| Code schreiben & refactoren | direkt in der IDE, voller Repo-Kontext |
| Tests generieren | Unit-Tests aus Klassen und Interfaces |
| Docs schreiben | Markdown in `docs/`, Deutsch, arc42-Struktur |
| Commit-Nachrichten | Conventional Commits aus dem Diff |
| PR-Beschreibungen | Zusammenfassung + Motivation |
| Code-Review | Schichtregeln, Typen, Testabdeckung prüfen |
| arc42-Queries | Kapitel direkt lesen und erklären |

&nbsp;

## Was Claude Code nicht tut

- Kein Deployment ohne Bestätigung
- Kein Commit auf `main` ohne PR
- Keine Cloud-Dependencies einführen
- Kein ML in `src/core/` — der Kern bleibt deterministisch
- Keine destruktiven Aktionen ohne ausdrückliche Bestätigung

&nbsp;

## Verfügbare Skills

Slash Commands und projektspezifische Skills: siehe [`SKILL.md`](./SKILL.md)

&nbsp;

## Zusammenspiel mit ₿itsy-Dev

| Situation | Claude Code | ₿itsy-Dev |
|---|---|---|
| Feature implementieren | schreibt Code + Tests | prüft Architekturfit |
| Docs ausarbeiten | schreibt Markdown | reviewed Konsistenz |
| arc42-Frage | liest Kapitel direkt | Langzeitkontext + MEMORY.md |
| Findings bewerten | direkt prüfen | bewertet nach Projektprinzipien |
