# S1 — Klarer Start (R1, Happy Path)

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T1030", pv_power_w=4500, house_load_w=1500,
    surplus_kw=3.0, grid_import_w=0, battery_soc_pct=80.0,
    miner_temp_c=45.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=12.0, pv_forecast_kw=4.0, quality="ok",
)
# Engine-Input: last_action="STOP", blocks_since_last_change=5, autonomy="FULL"
```

- **Entscheidung:** `START_R1_SURPLUS_OK`
- **Lehrziel:** Grundprinzip — überschüssige PV wird in die flexible Last **gesteuert**, statt sie einzuspeisen.
- **Verständnisfrage:** „Warum läuft der Miner jetzt an?"
- **Persona:** Energie-Optimierer (Eigenverbrauchsquote), Bitcoin-Nerd (Hashrate aus Sonne).
- **Override-Eignung:** gering (System verhält sich erwartungskonform).
- **Realer Beispielblock:** 01.06. 12:50 · Überschuss **+7,82 kW** · SoC 98 % · 13 ct (123× in 11 Tagen).

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
