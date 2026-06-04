# S4 — Übertemperatur (R3, Safety schlägt alles) ⚑

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T1430", pv_power_w=4500, house_load_w=1500,
    surplus_kw=3.0, grid_import_w=0, battery_soc_pct=75.0,
    miner_temp_c=90.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=12.0, pv_forecast_kw=4.0, quality="ok",
)
# Engine-Input: last_action="START", blocks_since_last_change=6, autonomy="FULL"
```

- **Entscheidung:** `STOP_R3_OVERTEMP_T90` — obwohl R1 starten **würde**.
- **Lehrziel:** Sicherheit hat höchste Priorität und ist **nicht überstimmbar** (`allow_unsafe_override = False`).
- **Verständnisfrage:** „Bedingungen sind ideal — warum stoppt das System?"
- **Override-Aufgabe (Kandidat A):** Proband darf Erzwingen versuchen → korrektes Verhalten = akzeptieren. Forcierter Weiterlauf = **Misuse-Tendenz**.
- **Belegung:** **0×** real (Fault) → **Injektion** (`temp > 85 °C`).

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
