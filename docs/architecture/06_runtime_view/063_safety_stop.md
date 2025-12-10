# 06.3 – Runtime: Safety-Stop (R3)

TODO: Ein kritischer Ablauf. Was passiert, wenn ein Notfall eintritt (z.B. Hardwareausfall, Grenzwertüberschreitung)? Wie wird das System sicher in einen definierten Ruhezustand gebracht?

> **Kurzüberblick:**  
> **Thermo- oder SoC-Schutz** bricht jede Deadband, setzt **Stop → Safe** und erklärt Ursache & Wiederaufnahmeschwelle.

> **TL;DR (EN):**  
> Thermal or SoC guard overrides deadband, triggers **stop → safe**, explains cause and resume condition.

---

## Ablauf / Sequence (R3 Beispiel)

1. Sensor liefert `t_miner` ≥ `T_MAX`.  
2. **Energy Context** markiert State; **Rule Engine** wertet **R3** zuerst.  
3. **Actuation**: sofort `stop()`; Deadband ignoriert.  
4. **Explainability/UI**: Banner „Übertemperatur“ + Resume-Bedingung `t_miner ≤ T_RESUME`.  
5. **Logging**: DecisionEvent `reason=R3 over_temp`, KPI Safety-Hit.

## Ablauf / Sequence (R2 Beispiel)

1. SoC fällt unter `soc_stop_pct` (z. B. 35 %).  
2. **R2 Autarkie-Schutz** setzt `stop/hold`; Start erst bei `soc_resume_pct`.  
3. UI zeigt Hinweis „Autarkie-Schutz aktiv“; Deadband bleibt untergeordnet.

---

## Parameter (MVP)

- **R3**: `t_stop_c = 85`, `t_resume_c = 75`.  
- **R2**: `soc_stop_pct = 35`, `soc_resume_pct = 45`.  
- Safety hat Vorrang vor R1/R4/R5.
