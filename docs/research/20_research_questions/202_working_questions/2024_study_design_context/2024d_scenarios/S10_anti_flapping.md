# S10 — Anti-Flapping / Deadband (R5, Stabilität)

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T1100", pv_power_w=2700, house_load_w=1500,
    surplus_kw=1.2, grid_import_w=0, battery_soc_pct=78.0,
    miner_temp_c=48.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=12.0, pv_forecast_kw=3.0, quality="ok",
)
# Engine-Input: last_action="START", blocks_since_last_change=1, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R5_MIN_RUNTIME_NOT_REACHED` (erst 1 Block seit Start < min_runtime 3)
- **Lehrziel:** `NOOP` heißt „**keine Änderung**" — der Miner läuft trotz kurzem Überschuss-Dip (1,2 kW) weiter; R5 verhindert Hektik-Schalten.
- **Verständnisfrage:** „Der Überschuss ist kurz gefallen — warum schaltet das System nicht sofort ab?"
- **Realer Beispielblock:** 29.05. 07:10 · +3,08 kW, gerade gestartet (391× in 11 Tagen, Subtypen DEADBAND/MIN_RUNTIME).

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
