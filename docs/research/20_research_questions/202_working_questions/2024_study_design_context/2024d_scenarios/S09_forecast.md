# S9 — Forecast blockiert Start (R4, vorausschauend) ⚑

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T1330", pv_power_w=3700, house_load_w=1500,
    surplus_kw=2.2, grid_import_w=0, battery_soc_pct=60.0,
    miner_temp_c=45.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=16.0, pv_forecast_kw=1.2, quality="ok",
)
# Engine-Input: last_action="STOP", blocks_since_last_change=4, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R4_FORECAST_PV_INSUFFICIENT` (Prognose 1,2 kW < 2,0 kW; R5-Deadband inaktiv, daher greift das R4-Veto nach R5)
- **Lehrziel:** Vorausschau — kein Start kurz vor einem PV-Einbruch (vermeidet kurze Laufzeit / Flapping).
- **Verständnisfrage:** „Jetzt ist Überschuss da — warum wartet das System?"
- **Override-Aufgabe (Kandidat B):** „Die Sonne scheint doch!" → Override zu START technisch erlaubt. Begründetes Akzeptieren = Vertrauen; blindes Übersteuern = **Disuse/Misuse**.
- **Realer Beispielblock:** 26.05. 15:30 · jetzt **+3,72 kW**, Prognose **1,76 kW** (822× in 11 Tagen; davon ~20 echte Tages-Lehrfälle).

> **Hinweis:** In der Produktion ist `sensor.pv_forecast_kw` aktuell `unavailable`
> → R4 vetoiert real nicht; S9 existiert nur im Replay (Perfect-Foresight-Proxy).
> forecast.solar reaktivieren (Roadmap Phase 3).

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
