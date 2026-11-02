# Projektstatus — wo stehen wir?

Cross-Track-Orientierung über DEV, THESIS und SIM in ein bis zwei Minuten. Diese
Seite ersetzt keine der bestehenden Detail-Quellen (siehe Links je Track) — sie
zeigt nur, wo diese Quellen gerade stehen, damit niemand (Nutzer, Claude Code)
sie einzeln durchsuchen muss, um sich zu orientieren.

**Update-Ritual:** wird manuell am Ende relevanter Sessions aktualisiert — kein
Automatismus. Wenn diese Seite länger als ein paar Wochen nicht angefasst wurde,
ist sie wahrscheinlich veraltet: im Zweifel gegen `git log`, `PROJECT_STATE.md`
und die Track-Quellen unten verifizieren, nicht blind übernehmen.

&nbsp;

---

## Track 1 — DEV (System)

**Detail-Quelle:** `git log`, `git status` — das frühere
[`PROJECT_STATE.md`](../development/36_ai_tooling/neo/PROJECT_STATE.md) ist seit
22.07.2026 archiviert (gehörte zur alten ₿itsy-Dev-Rolle) und wird nicht mehr
gepflegt.

Architektur vollständig dokumentiert, alle acht `src/`-Module implementiert und
getestet. HA-Dashboard und Miner-MVP laufen produktiv.

**Letzter Commit:** `9d7ec97 feat: add device tracking and bitsy ki tab`

&nbsp;

---

## Track 2 — THESIS (Masterarbeit)

**Detail-Quelle:** `docs/thesis/` (lokal, gitignored, Overleaf-Sync) — nicht im
Obsidian-Vault, da nicht Teil des Sync-Scopes (siehe `scripts/sync_obsidian.py`).

**Zuletzt bearbeitet:** 2026-06-12 (Kapitel `04_system` in Version v11, `99_anhang/99h_systemdetails_v1`,
READMEs für Kapitel 05–08 angelegt) — seit einem Monat keine weitere Änderung.

**Bekannter offener Punkt (zu bestätigen, nicht frisch verifiziert):** Arbeitstitel-Sign-off
und Overleaf-Sync der v6-Outlines standen zuletzt offen.

&nbsp;

---

## Track 3 — SIM (Simulation & Studie)

**Detail-Quelle:** `src/sim/`, Studiendesign-Docs unter
[`docs/research/20_research_questions/`](../research/20_research_questions/README.md)

**Zuletzt bearbeitet:** 2026-06-25 (`study_scenarios_soc_band.py`).

**Studiendesign (aus Commits verifiziert):** A/B-Vertrauensvergleich, N=16 (8/8),
zwei Personas (energie, wärme) — `tech`-Persona aus dem Sampling entfernt.

&nbsp;

---

> 🏠 Zurück zur **[Hauptübersicht](../README.md)**
