# S3 — Sonne, aber Preis zu hoch (R1, kontraintuitiv) ⚑

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T1730", pv_power_w=4000, house_load_w=1500,
    surplus_kw=2.5, grid_import_w=0, battery_soc_pct=70.0,
    miner_temp_c=40.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=28.0, pv_forecast_kw=2.5, quality="ok",
)
# Engine-Input: last_action="STOP", blocks_since_last_change=5, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R1_PRICE_TOO_HIGH` (28 ct > 25 ct; Preis bewusst < 30 ct, damit R4 *nicht* greift)
- **Lehrziel:** Opportunitätskosten — bei hohem Marktpreis lohnt **Einspeisen mehr als Selbstverbrauch**. Profitabilität ist nicht nur „Sonne da/nicht da".
- **Verständnisfrage:** „Die Sonne scheint und der Akku ist voll — warum mint das System trotzdem nicht?"
- **Diskriminierend:** kontraintuitives Item, gut geeignet für den Within-Vergleich des Vertrauens (statisch vs. LLM).
- **Belegung:** **0×** real — tritt mit aktuellem Tarif nicht auf (Abend-Hochpreis kollidiert mit fallender PV-Prognose → R4 greift vor R1). **Konstruktion nötig.**

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
