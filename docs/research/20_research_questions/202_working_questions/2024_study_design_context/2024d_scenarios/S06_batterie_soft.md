# S6 — Batterie-Schutz, Soft-Min (R2 vor R1) ⚑

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T0900", pv_power_w=3800, house_load_w=1300,
    surplus_kw=2.5, grid_import_w=0, battery_soc_pct=55.0,
    miner_temp_c=30.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=14.0, pv_forecast_kw=3.5, quality="ok",
)
# Engine-Input: last_action=None, blocks_since_last_change=0, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R2_SOC_SOFT_MIN` (55 % im Soft-Band 50–58 %; kein **neuer** Start, Akku lädt erst über 58 % nach)
- **Lehrziel:** Autarkie vor Profit — R2 schlägt R1, obwohl Überschuss vorhanden ist.
- **Verständnisfrage:** „Überschuss ist da — warum startet der Miner nicht?"
- **Diskriminierend:** trennt R2-Verständnis vom reinen „Überschuss = Start"-Modell.
- **Realer Beispielblock:** 02.06. 05:50 · **+2,70 kW**. ⚠️ Realblock-SoC (vormals 14 % = Soft unter 10/20) liegt unter den neuen 50/58 im **Hard**-Bereich — Häufigkeiten soft/hard gegen die neuen Schwellen neu auszuzählen.

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
