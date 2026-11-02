# 20.2.4.2 - SD-WQ2 - Aufgaben, Instrumente und Messlogik (v1)


## Messgrößen

- **Primäre AV — Nutzervertrauen (12–84):** Automation Trust Scale (Jian 2000), auf die gesehene Variante, vor dem Reveal (between).
- **Within (H2):** Forced-Choice (A/B) + 7-stufiges Vergleichsrating je verglichenem Szenario, nach dem Reveal (alle N = 16).
- **FF2 — Güte:** objektive Faithfulness (`study_faithfulness.py`) + verblindetes 2-Rater-Rubrik-Rating (Korrektheit, Vollständigkeit, Klarheit, je 0–2; Halluzinations-Flag), Interrater-κ.
- **Optional/Nebenmaße:** SUS, Raw NASA-TLX; behaviorale Override-/Verhaltensspur.

## Instrumente

- Demographie + Vorwissen (Technikaffinität, BTC-Vorwissen) als deskriptive Kovariate; **keine** Persona-Steuerung.
- Offener Vertrauens-Frageleitfaden: „Hast du vertraut? · bei welchen Entscheidungen mehr/weniger? · haben die Texte das Vertrauen beeinflusst? · gab es einen unglaubwürdigen Text?“ (audioaufgezeichnet).
- Within-Vergleichsbogen (Forced-Choice + Rating + offene Begründung).
- Systemlogs (DecisionEvents, Override-Ereignisse, Template-Fallbacks).

## Messlogik

- **Primärtest (H1, between):** Mann-Whitney-U (einseitig) auf das Vertrauen, Gruppe A (n = 8) vs. B (n = 8); Welch-/t-Test bei erfüllten Voraussetzungen (Shapiro-Wilk, Levene). Effektgröße r (bzw. Cohen's *d*) + 95 %-KI.
- **Within (H2):** Binomial-/Vorzeichentest auf Forced-Choice; Wilcoxon gegen die Mitte 4.
- **Güte (FF2):** Faithfulness-Raten + Rubrik-Mittelwerte + Interrater-κ; Kalibrierung Vertrauen × Güte.
- **Pilot:** 2–3 Probedurchläufe zur Kalibrierung von Trust-/Within-Bogen, Güte-Rubrik und Szenario-Timing.

---

> **Nächster Schritt:** [20.2.4.3 - SD-WQ3 - Ethik, Datenschutz und Analyseplan](./2024c_ethics_privacy_analysis.md)
>
> Zurück zu **[20.2.4 - SD-CONTEXT](./README.md)**
>
> Zurück zur **[Hauptübersicht](../../../../README.md)**
