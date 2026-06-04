# S2 — Kein Überschuss (R1, NOOP)

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T0700", pv_power_w=1700, house_load_w=1300,
    surplus_kw=0.4, grid_import_w=0, battery_soc_pct=30.0,
    miner_temp_c=30.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=18.0, pv_forecast_kw=3.0, quality="ok",
)
# Engine-Input: last_action=None, blocks_since_last_change=0, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R1_INSUFFICIENT_SURPLUS` (0,4 kW < 1,5 kW)
- **Lehrziel:** Ohne ausreichenden Überschuss kein Mining — die Hauslast hat Vorrang.
- **Verständnisfrage:** „Die Sonne ist doch schon da — warum passiert nichts?"
- **Realer Beispielblock:** 02.06. 07:00 · **+1,48 kW** (knapp < 1,5) · SoC 22 % (20× in 11 Tagen).

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
