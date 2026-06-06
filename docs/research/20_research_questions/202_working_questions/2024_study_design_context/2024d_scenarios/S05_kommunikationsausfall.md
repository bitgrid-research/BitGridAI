# S5 — Kommunikationsausfall (R3, Comm-Timeout)

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T1500", pv_power_w=4200, house_load_w=1500,
    surplus_kw=2.7, grid_import_w=0, battery_soc_pct=72.0,
    miner_temp_c=50.0, miner_heartbeat_age_sec=75.0,
    energy_price_ct_kwh=13.0, pv_forecast_kw=3.5, quality="warn",
    missing_signals=("miner_heartbeat",),
)
# Engine-Input: last_action="START", blocks_since_last_change=2, autonomy="FULL"
```

- **Entscheidung:** `STOP_R3_COMM_TIMEOUT` (75 s > 60 s)
- **Lehrziel:** Bei Verbindungsverlust wird sicherheitshalber gestoppt — kein Steuern „blind".
- **Verständnisfrage:** „Was bedeutet es, wenn das System den Miner nicht mehr ‚hört'?"
- **Belegung:** **0×** real (Fault) → **Injektion** (`heartbeat_age > 60 s`).

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
