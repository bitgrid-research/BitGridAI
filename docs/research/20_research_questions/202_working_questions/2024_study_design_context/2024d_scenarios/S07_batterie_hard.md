# S7 — Batterie-Notstopp, Hard-Min (R2, aktiver Stopp)

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T1630", pv_power_w=1200, house_load_w=1400,
    surplus_kw=-0.2, grid_import_w=200, battery_soc_pct=9.0,
    miner_temp_c=55.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=20.0, pv_forecast_kw=1.5, quality="ok",
)
# Engine-Input: last_action="START", blocks_since_last_change=6, autonomy="FULL"
```

- **Entscheidung:** `STOP_R2_SOC_HARD_MIN` (9 % ≤ 10 %; Miner lief auf Akku, Netzbezug noch < 500 W)
- **Lehrziel:** Unterschied Soft-Min (kein Neustart) vs. Hard-Min (**laufenden Miner stoppen**).
- **Verständnisfrage:** „Worin unterscheidet sich dieser Stopp von dem heute Morgen (S6)?"
- **Realer Beispielblock:** 02.06. 04:20 · **SoC 5 %** · Nacht (32× in 11 Tagen).

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
