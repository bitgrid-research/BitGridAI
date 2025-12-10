# 083 – User Interface / Explainability UI

TODO: Wie sieht BitGridAI für den Menschen aus? Übergreifende Prinzipien für Design, Usability und Frontend-Technologie.

> **Kurzüberblick:**  
> HCI ist Kern: **Explain → Act → Confirm**, „Warum jetzt?“, „Was-wäre-wenn?“, **Next-Block-Preview**, **Manual Override** (Block-TTL), **Timeline & KPIs**, alles **lokal** und **privacy-by-default**.

> **TL;DR (EN):**  
> Explainable, reversible, trust-building UI: why-now, what-if, next-block preview, block-scoped overrides, timeline/KPIs; local-only.

---

## Designziele

- Entscheidungen **verständlich** machen (Reason/Trigger/Parameter, Schwellen sichtbar).  
- **Manuelle Eingriffe** jederzeit, klar rücknehmbar (TTL bis Blockende).  
- **Feedback-Loops**: Bestätigung, Undo, Wirkung sichtbar.  
- **Research-Opt-in**: Toggle mit Datenscope-Hinweis; Export lokal.  
- **Accessibility**: Keyboard, ARIA, Kontrast, „Bewegung reduzieren“.

---

## UI-Bausteine (aus Kap. 12)

| Baustein | Zweck | Instrumentierung |
| --- | --- | --- |
| **Decision-Toast** | Sofort-Erklärung bei Aktion | Link zur Timeline, Event `toast_shown`. |
| **Why-Now? Panel** | Reason/Trigger/Params, R1–R5-Status | Snapshot-Export, Schwellen sichtbar. |
| **Next-Block Preview** | Vorschau + Confidence | Zeigt Forecast-Stabilität & Alternativen. |
| **Timeline** | Verlauf DecisionEvents/Overrides | Filter, Annotation, JSON/CSV-Export. |
| **Override-Chip** | Start/Stop/Level + TTL | Countdown, Policy-Rücksprung, Log `override_enter/exit`. |
| **Health-Banner** | Broker/Drift/Sensor-Stale | Runbook-Link, Severity-Icon. |
| **KPI-Widget** | Trust/Coverage/Flapping | Lokal berechnet, anonymisiert. |
| **Research-Toggle** | Opt-in/out | Audit-Log, Datenscope-Info. |

---

## Mikrotexte (Beispiele)

- **Start (R1):** „Start: Surplus 1.8 kW ≥ 1.5 kW, Preis 16 ct ≤ 18 ct. Deadband bis +2.“  
- **Stop (R2/R3):** „Stop: SoC 24 % ≤ 25 % (R2). Sicherheit geht vor.“  
- **Hold (R5):** „Stabilisierung aktiv (R5): bis Block +1.“  
- **Preview:** „Nächster Block: voraussichtlich weiterlaufen; Prognose stabil (R4).“

> Copy, icons, and patterns stay consistent to support trust and predictability.
