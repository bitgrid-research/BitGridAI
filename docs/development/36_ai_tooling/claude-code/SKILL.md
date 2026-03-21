# SKILL.md – Claude Code Skills & Slash Commands

## Eingebaute Commands

| Command | Zweck |
|---|---|
| `/commit` | Staged Änderungen analysieren und Conventional-Commit erstellen |
| `/review-pr [Nr]` | GitHub-PR reviewen |
| `/clear` | Konversationshistorie leeren |
| `/help` | Hilfe zu Claude Code |
| `/fast` | Fast Mode umschalten |

&nbsp;

## Projekt-Skills

| Skill | Befehl | Wann nutzen |
|---|---|---|
| **simplify** | `/simplify` | Nach Implementierung: Code auf Qualität, Wiederverwendung und Effizienz prüfen |
| **loop** | `/loop [interval] [command]` | Wiederkehrende Aufgabe auf Intervall, z. B. `/loop 5m /simplify` |
| **update-config** | `/update-config` | `settings.json` anpassen — Hooks, Permissions, Env-Variablen |
| **keybindings-help** | `/keybindings-help` | Tastenkombinationen in `~/.claude/keybindings.json` anpassen |
| **claude-api** | `/claude-api` | Apps mit Claude API / Anthropic SDK bauen |

&nbsp;

## Typische Workflows

### Neues Feature
```
1. Passendes arc42-Kapitel lesen (docs/architecture/)
2. Code schreiben (src/core/ oder src/adapters/)
3. Unit-Tests schreiben (tests/)
4. /simplify — Qualitätsprüfung
5. make check — fmt + lint + test
6. /commit — Conventional Commit
```

### Dokumentation aktualisieren
```
1. Bestehendes Kapitel lesen
2. Markdown schreiben (Deutsch, arc42-Struktur, Nummerierungsschema einhalten)
3. /commit mit `docs:` Prefix
```

### PR vorbereiten
```
1. make check — alles grün?
2. /commit — alle Änderungen committen
3. /review-pr — oder manuell: Diff + Motivation zusammenfassen
```

&nbsp;

## Gedächtnis

Claude Code hat projektübergreifendes Gedächtnis:

```
C:\Users\giber\.claude\projects\m--DEV-BitGridAI\memory\
```

Enthält: User-Präferenzen, Feedback, Projektkontext aus vergangenen Sessions.
Wird automatisch in relevante Sessions geladen.
