# 012 – Qualitätsziele / Quality Goals

TODO: Worauf legen wir besonderen Wert? (z.B. Benutzerfreundlichkeit, Effizienz, Zuverlässigkeit).

> **Kurzüberblick:**  
> Transparenz, Autonomie, Nachhaltigkeit, Vorhersagbarkeit, Sicherheit, Reproduzierbarkeit – alle lokal und erklärbar.

> **TL;DR (EN):**  
> Transparency, autonomy, sustainability, predictability, safety, reproducibility—all local and explainable.

---

## Ziele / Goals

| Qualität | Beschreibung |
|---|---|
| **Transparenz** | Jede Entscheidung enthält Reason/Trigger/Parameter; Explainability-UI + versionierte Texte. |
| **Autonomie** | Vollständig lokal-first, keine Cloud- oder API-Abhängigkeiten; Offline-Modus möglich. |
| **Nachhaltigkeit** | PV-Überschuss konsequent nutzen (Mining/Heat/Hodl), Deadband glättet Flapping. |
| **Vorhersagbarkeit** | 10-Min-Blocktakt + deterministische Regeln (**R1–R5**) machen Verhalten antizipierbar. |
| **Sicherheit** | SoC-/Thermo-Schutz (**R2/R3**), Stop → Safe, klar getrennte Fail-States. |
| **Reproduzierbarkeit** | Standardisierte Datenformate (SQLite/Parquet/JSON) und Replays für Forschung/Tests. |

> | Quality | Description |
> |---|---|
> | **Transparency** | Decisions carry reason/trigger/params; explainability UI + versioned microcopy. |
> | **Autonomy** | Fully local-first; no cloud/API dependency; offline-capable. |
> | **Sustainability** | Use PV surplus via controlled flexible loads; deadband smooths flapping. |
> | **Predictability** | 10-minute cadence + deterministic **R1–R5**. |
> | **Safety** | SoC/thermal guards (**R2/R3**), stop → safe, explicit fail states. |
> | **Reproducibility** | Standardised data formats and replays for research/tests. |

---

## Messgrößen (KPIs) / Measures

- **Grid-Import-Reduktion** ggü. Baseline (Target ~25 %).  
- **Flapping-Rate** Start/Stop-Wechsel pro Tag (Target ≤ 2).  
- **Explanation Coverage** ≥ 98 % Decisions mit Reason/Trigger/Params.  
- **Trust-Score** ≥ 4/5 (Likert, Prosumer-Studie).  
- **Thermal Incidents** = 0 ungeplante Übertemperaturen.

> Grid import drop, low flapping, high explanation coverage, trust score ≥ 4/5, zero thermal incidents.
