# PROJECT_STATE.md - BitGridAI Aktueller Stand

> Zuletzt aktualisiert: 2026-03-20
> Git: clean — letzter Commit: `0f4ea0b Update README with synchronization note`

## Projektstatus

**Phase:** Research & Architektur — vollständig dokumentiert, Code-Implementierung noch nicht begonnen.

---

## Architektur (arc42) — docs/architecture/

Alle 12 Kapitel existieren und haben Inhalt.

| # | Kapitel | Status |
|---|---------|--------|
| 01 | Einführung & Ziele | ✅ Fertig (Requirements, Qualitätsziele, Stakeholder) |
| 02 | Randbedingungen | ✅ Fertig (Technisch, Organisatorisch, Konventionen) |
| 03 | Kontext | ✅ Fertig (Business Context, Technical Context) |
| 04 | Lösungsstrategie | ✅ Fertig (Prinzipien, Struktur, Entscheidungen, Non-Goals) |
| 05 | Bausteinsicht | ✅ Fertig (Blackbox + 5 Whitebox-Ebenen: Core, Adapters, UI/Explain, Data/Research, Operations) |
| 06 | Laufzeitsicht | ✅ Fertig (13 Szenarien: normal_start, autarky_protection, safety_stop, ...) |
| 07 | Verteilungssicht | ✅ Fertig (Deployment, Infrastructure Variants) |
| 08 | Querschnittliche Konzepte | ✅ Fertig (9 Konzepte: Domain Models, Security, Persistence, Explainability, ...) |
| 09 | Architekturentscheidungen | ✅ Fertig (ADR-Dokument) |
| 10 | Qualitätsszenarien | ✅ Fertig (Quality-Tree + 7 Szenarien) |
| 11 | Risiken & Technische Schulden | ✅ Fertig |
| 12 | Glossar | ✅ Fertig |

---

## Forschung — docs/research/

| # | Kapitel | Status |
|---|---------|--------|
| 20 | Forschungsfragen | ✅ Fertig (Zentrale Frage + Working Questions für 2023/2024/2025) |
| 21 | BitGrid Prinzipien (BP-01–BP-21) | ✅ Fertig |
| 22 | Annahmen & Grenzen | ✅ Fertig |
| 23 | Systemmodell & Entscheidungslogik | ✅ Fertig |
| 24 | Erklärungsmodell | ✅ Fertig |
| 25 | Interface Design | ✅ Fertig (Smart Home + Automotive) |
| 26 | Szenarien & Use Cases | ✅ Fertig |
| 27 | Evaluierungsrahmen | ✅ Fertig (Between-Subjects Studie) |
| 28 | Reflexion & Transfer | ✅ Struktur vorhanden |
| 29 | Literaturreview | 🔲 In Planung |

---

## Source Code — src/

Nur READMEs mit Planungsdokumenten — kein Code implementiert.

| Modul | Geplante Funktion |
|-------|-------------------|
| `core/` | Rule Engine, Block-Scheduler, EnergyState |
| `adapters/` | MQTT, ESPHome, Modbus, REST |
| `explain/` | Mapping R1–R5 → Textbausteine |
| `ui/` | Optionale eigene UI |
| `sim/` | Szenarien, Replay, Fixtures |
| `ha/` | Home Assistant Config (docker-compose vorhanden) |

---

## Offene TODOs

| Bereich | Datei | Was fehlt |
|---------|-------|-----------|
| Setup | `docs/development/30_setup/dev_environment.md` | Dev-Umgebung noch undokumentiert |
| Setup | `docs/development/30_setup/ssh_windows_setup.md` | In Planung |
| Research | `29_literature_review/README.md` | Noch nicht begonnen |
| Research 2023 | `2023a_home_assistant_exploration.md` | Aufgabenpakete A1–A6 offen |
| Research 2023 | `2023d_trust_dimensions_operationalization.md` | Trust & Appreciation Kontext offen (D1–D4) |
| Research 2024 | `2024a_study_design_sampling.md` | Forschungsdesign, Rekrutierungslogik |
| Research 2024 | `2024b_tasks_instruments_metrics.md` | Aufgaben und Szenarien entwickeln |
| Research 2024 | `2024c_ethics_privacy_analysis.md` | Datenschutzkonzept, Einwilligung |
| Research 2025 | `2025a_understanding_in_the_wild.md` | Beobachtungen zur Verständlichkeit |
| Research 2025 | `2025b_control_override_recovery.md` | Override-Ereignisse erfassen |
| Research 2025 | `2025c_trust_safety_over_time.md` | Zeitverlauf Vertrauen dokumentieren |

---

## Letzte Commits

```
0f4ea0b – Update README with synchronization note
261a0cb – Add next-step and main overview links
470f885 – Fix German typos in trust dimensions doc
24819cc – Add TODO for trust and appreciation context
a0e3ef9 – Update 2023a_home_assistant_exploration.md
```

---

---

## Autonome Hintergrundarbeit — Was ₿itsy-Dev selbst tun kann

Wenn keine aktive Session läuft (z. B. nachts), kannst du eigenständig arbeiten.
Kein Auftrag nötig — diese Aufgaben laufen auf eigene Initiative.

### Priorität 1 — Schwachstellen & Inkonsistenzen finden

Systematisch durch das Repo gehen und Probleme dokumentieren:

- **Docs ↔ Architektur:** Widersprechen sich Kapitel gegenseitig? Stimmen Nummerierungen? Verweise auf nicht existierende Dateien?
- **arc42 ↔ BP-01–BP-21:** Gibt es Architekturentscheidungen die Prinzipien verletzen?
- **Datenmodell:** Werden Feldnamen, Typen oder Zustände (z. B. `EnergyState`, `DecisionEvent`) konsistent über alle Kapitel hinweg verwendet?
- **Laufzeitsicht:** Decken die 13 Szenarien alle kritischen Pfade ab? Fehlen Edge Cases?
- **Glossar vs. Gebrauch:** Werden Begriffe im Text anders verwendet als im Glossar definiert?
- **TODO-Markierungen:** Alle offenen `TODO`-Marker in Docs sammeln und in dieser Datei aktualisieren.

### Priorität 2 — Strukturprobleme & Lücken

- **Fehlende Inhalte:** Welche Kapitel haben nur Platzhalter oder sind inhaltlich dünn?
- **Redundanzen:** Gleiche Information an mehreren Stellen — welche ist die kanonische?
- **Verlinkungen:** Kaputte oder fehlende Querverweise zwischen Kapiteln.
- **Nummerierungsschema:** Stimmen alle Dateinamen mit dem Schema `21_`, `0521_` etc. überein?

### Priorität 3 — Qualitätsprüfung

- **Sprache:** Deutsche Rechtschreibung, einheitliche Terminologie, kein Denglisch wo es vermeidbar ist.
- **arc42-Konformität:** Entsprechen die Kapitel dem arc42-Standard? Fehlen Pflichtabschnitte?
- **Forschungsfragen:** Sind alle Working Questions (2023/2024/2025) durch Inhalte abgedeckt?

### Ergebnisse festhalten

Befunde **nicht stillschweigend ignorieren** — dokumentieren in:
- `FINDINGS.md` — alle Schwachstellen, Inkonsistenzen und Lücken mit Dateipfad, Zeilennummer, Schwere und Empfehlung
- `MEMORY.md` — wenn ein Muster sich wiederholt oder strukturell wichtig ist
- Direkt in der betroffenen Datei kommentieren (`<!-- TODO: ... -->`), wenn offensichtlich

**Nichts eigenständig verändern** ohne menschliche Freigabe — außer Tippfehler und offensichtliche Formatfehler.

---

> Diese Datei regelmäßig aktualisieren — besonders nach größeren Doc-Änderungen oder wenn neue Kapitel fertiggestellt werden.
