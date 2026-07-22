# Neo — Nachtforscher

Neo ist der nächtliche Analyse-Agent im BitGridAI-Projekt. Er läuft lokal auf
Umbrel (`192.168.178.96:18790`, Hermes Agent) auf Basis von `gemma4:e4b`
(Ollama, `192.168.178.104`) und liest jede Nacht per Cron (01:00 UTC) die
Energie-/Mining-Fakten des Tages, sucht Muster und schreibt höchstens drei
falsifizierbare Hypothesen nach `nachtberichte/`. Claude Code prüft die
Berichte und übernimmt geprüfte Erkenntnisse in den Obsidian-Vault.

Diese Instanz hieß bis zum 22.07.2026 **₿itsy-Dev** und war als
Repo-/arc42-Review-Assistent gedacht (siehe `FINDINGS.md`, seit 28.06.2026
inaktiv). Der Umbau auf eine schmalere, konkretere Rolle ist in
`IDENTITY.md` dokumentiert.

## Live-Konfiguration vs. dieser Ordner

Die tatsächlich deployte Konfiguration (`SOUL.md`, `config.yaml`,
`cron/jobs.json`) liegt auf dem Umbrel-Server, nicht im Repo — Hermes Agent
speichert sie dort, nicht git-versioniert. **Dieser Ordner ist der
Design-/Änderungsverlauf**, kein automatischer Spiegel: `SOUL.md` hier wird
manuell nachgezogen, wenn die Live-Version geändert wird.

```
neo/
├── SOUL.md           ← Identität, Charakter, Regeln (Stand 22.07.2026)
├── IDENTITY.md       ← Name, Zweck, Grenzen, Vorgeschichte (₿itsy-Dev → Neo)
├── USER.md           ← Wer der Betreiber ist, wie er denkt
├── TOOLS.md          ← IPs, Ports, Mounts, Modellwahl-Begründung
├── DESCRIPTION.md    ← Discord-Bot-Kurzbeschreibung (Portal-Spiegel)
├── BENCHMARKS.md     ← Modell-Kriterien + Ergebnis-Historie (lebendiges Protokoll)
├── BEWAEHRUNG.md     ← Bewährungszeit-Protokoll: was Neo gut/schlecht macht, über die Zeit
├── SKILL_gedaechtnis-lernzyklus.md  ← Spiegel des deployten Hermes-Skills (siehe unten)
├── FINDINGS.md       ← ARCHIVIERT: alte ₿itsy-Dev-Repo-Befunde
└── PROJECT_STATE.md  ← ARCHIVIERT: Repo-Snapshot zur Zeit von ₿itsy-Dev
```

## Hermes-Skill: Gedächtnis-Lernzyklus

Live deployt unter `/opt/data/skills/note-taking/gedaechtnis-lernzyklus/SKILL.md`
(Hermes-Container, `hermes skills list` zeigt ihn `enabled`). Formalisiert das am
22.07.2026 mehrfach verifizierte Muster "eine Datei lesen, sofort schreiben" für
`kurzzeit.md`, plus den zweigeteilten, verlustfreien Übergang nach
`langzeit/JJJJ-MM.md` (Kopieren und Leeren sind zwei getrennte, von GiGi/Claude
Code bestätigte Schritte, nie einer). Lokaler Spiegel:
[`SKILL_gedaechtnis-lernzyklus.md`](./SKILL_gedaechtnis-lernzyklus.md), kein
automatischer Sync bei künftigen Live-Änderungen.

## Gedächtnis in Obsidian

Neo hat einen eigenen, beschreibbaren Ordner `memory_neo/` im Obsidian-Vault
(read-write gemountet, getrennt vom read-only `database_exploration/`).
Struktur und Regeln (BELEGT vs. GEDANKE) stehen in `SOUL.md`.

## Werkzeuge & Diagnose

Reproduzierbare Tests/Diagnose für diese Instanz liegen im Repo, nicht hier:

```
scripts/bench_model.py           Modell-Kandidat gegen 7 Kriterien pruefen (siehe BENCHMARKS.md)
scripts/diagnose_nachtforscher.py  Chronologie aller Cron-Versuche + aktive Config
scripts/watch_nachtforscher.py     Phasengenauer Live-Status eines laufenden Cron-Laufs
scripts/reset_neo_session.py       Erzwingt frische SOUL.md in laufenden Chat-Sessions
```

Kriterien, Begründung und Ergebnis-Historie aller getesteten Modelle:
[`BENCHMARKS.md`](./BENCHMARKS.md).

Mehr zum Kollaborationsprotokoll: [`../COLLABORATION.md`](../COLLABORATION.md)
