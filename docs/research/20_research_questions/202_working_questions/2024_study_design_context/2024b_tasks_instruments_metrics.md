# 20.2.4.2 - SD-WQ2 - Aufgaben, Instrumente und Messlogik (v1)


## Messgrößen

- **Primäre AV — Regelverständnis-Score (0–12):** aus den offenen Fragen, bewertet von zwei Ratern nach Rubrik (R1–R5, Priorisierung, Zentralkonzept „Steuern statt Einspeisen“); Interrater-Reliabilität als Cohen's κ.
- **Sekundär — Override-Angemessenheit:** kategorial (angemessen / Disuse-Tendenz / Misuse-Tendenz) aus einer beobachteten Override-Aufgabe.
- **Optional — Vertrauen:** Automation Trust Scale, einmalig; ggf. SUS / Raw NASA-TLX.

## Instrumente

- Demographie + **Nutzertyp-Einstufung** (steuert in Gruppe B den Persona-Typ energie/waerme); Vorwissen separat als deskriptive Kovariate.
- Offener Frageleitfaden: „Wie funktioniert das System? · Erwartungen? · wichtigste Einflussregeln? · Warum Steuern statt Einspeisen?“ (audioaufgezeichnet).
- Systemlogs (DecisionEvents, Override-Ereignisse, Template-Fallbacks).

## Messlogik

- **Statistik:** t-Test für unabhängige Stichproben (einseitig) auf den Regelverständnis-Score; Cohen's *d* + 95 %-KI. Primärvergleich Gruppe A (n = 8) vs. gepoolte Gruppe B (n = 8); der Vergleich der 2 Persona-Typen (energie/waerme, n = 4 je Typ) ist explorativ/deskriptiv (ungerichtet).
- **Voraussetzungsprüfung:** Shapiro-Wilk (Normalverteilung), Levene (Varianzhomogenität) → Welch- bzw. Mann-Whitney-U-Test als Fallback.
- **Pilot:** 2–3 Probedurchläufe zur Kalibrierung von Rubrik und Szenario-Timing.

---

> **Nächster Schritt:** [20.2.4.3 - SD-WQ3 - Ethik, Datenschutz und Analyseplan](./2024c_ethics_privacy_analysis.md)
>
> Zurück zu **[20.2.4 - SD-CONTEXT](./README.md)**
>
> Zurück zur **[Hauptübersicht](../../../../README.md)**
