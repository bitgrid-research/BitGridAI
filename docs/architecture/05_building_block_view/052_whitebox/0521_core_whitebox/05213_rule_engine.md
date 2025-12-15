# 05.2.1.3 Rule Engine

Verantwortung: bewertet Regeln R1-R5 deterministisch gegen den aktuellen `EnergyState`, erzeugt `Decision` und `DecisionEvent` inkl. Begruendung (reason, trigger, params).

## Struktur

- **Rule Evaluators:** je Regel R1-R5 (Start, Autarkie, Safety, Forecast, Deadband/Stabilitaet).
- **Priorizer:** ordnet Ergebnisse nach Safety > Autarkie > Stabilitaet > Optimierung.
- **Conflict Resolver:** kombiniert/neutralisiert konkurrierende Aktionen, setzt Fallbacks.
- **Decision Builder:** erzeugt `Decision` (Aktor-Kommandos) und `DecisionEvent` (mit gueltigem `valid_until`).

## Schnittstellen

- **Provided:** `Decision`, `DecisionEvent` (reason/trigger/params/valid_until), Evaluations-Logs pro Regel.
- **Required:** aktueller `EnergyState`, `valid_until` Vorschlag vom Scheduler, Regelkonfiguration (Schwellen, Deadbands), Overrides (falls aktiv).

## Ablauf (vereinfacht)

1) Rule Evaluators pruefen R1-R5 gegen `EnergyState`, liefern Vorschlaege mit Scores.  
2) Priorizer sortiert Vorschlaege, eliminiert verbotene Kombinationen (Safety first).  
3) Conflict Resolver erzeugt eine konsistente Zielaktion (z.B. Start, Stop, Limit).  
4) Decision Builder baut `Decision` fuer Adapter + `DecisionEvent` fuer UI/Data/Explain.

## Qualitaet und Betrieb

- Deterministisch: gleiche Inputs erzeugen gleiche Decision; Zufall ausgeschlossen.  
- Safety: Regel R3 darf jede andere Regel ueberstimmen; bei Unklarheit -> Stop/Safe.  
- Nachvollziehbarkeit: jede Entscheidung hat reason/trigger/params; Logging ist Pflicht.

---
> Zurueck zu **[5.2.1.x Core-Orchestrierung (Level 3)](./README.md)**  
> Zurueck zu **[5.2.1 Core-Orchestrierung](../0521_core_whitebox.md)**
