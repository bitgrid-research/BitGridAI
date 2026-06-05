# S8 — Wolke zwingt zum Stopp (R2, Netzbezug-Limit) ⚑

> Teil der **[Szenarien-Übersicht](./README.md)**

```python
EnergyState(
    block_id="2026-06-15T1230", pv_power_w=800, house_load_w=1500,
    surplus_kw=-0.7, grid_import_w=700, battery_soc_pct=65.0,
    miner_temp_c=50.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=15.0, pv_forecast_kw=3.0, quality="ok",
)
# Engine-Input: last_action="START", blocks_since_last_change=5, autonomy="FULL"
```

- **Entscheidung:** `STOP_R2_GRID_IMPORT_EXCEEDED` (700 W > 500 W; SoC 65 % > 58 % → SoC-Reserve nicht aktiv, Netzbezug isoliert)
- **Lehrziel:** **Nie aus dem Netz minen** — verstärkt „Steuern statt Einspeisen" aus Gegenrichtung.
- **Verständnisfrage:** „Der Akku ist gut gefüllt — warum reicht das nicht, um weiterzulaufen?"
- **Autonomie-Variante:** Im `SEMI`-Modus wird dieser R2-STOP zu `NOOP` (nur R3 darf stoppen) → testet Verständnis der Autonomiestufen.

> **Wichtig (R2-Fix):** R2 prüft jetzt **Netto-Bezug** (`import − export`). Die 12
> ursprünglich gemineten S8-Blöcke waren 3-Phasen-Schieflage (Bezug *und*
> Einspeisung gleichzeitig) → **Fehlauslösung, jetzt behoben**, sie feuern nicht mehr.
> Der echte S8 (genuiner Netto-Bezug > 500 W bei laufendem Miner) ist im Sommer
> selten → **Injektion nötig**. Override-Ground-Truth jetzt sauber: Stopp legitim →
> Übersteuern = **Misuse**.

---
> Zurück zur **[Szenarien-Übersicht](./README.md)**
