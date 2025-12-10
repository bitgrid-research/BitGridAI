# 081 – Domain Models / Datenmodelle

TODO: Unsere gemeinsame Sprache. Wie definieren wir zentrale Begriffe wie "Nutzer", "Energiequelle" oder "Messwert" im Code, damit alle dasselbe darunter verstehen?

> **Kurzüberblick:**  
> **EnergyState** als Single Source of Truth, **DecisionEvent** für jede Aktion, **ExplainSession** für Microcopy, **Override** und **ResearchToggle** als Kontrollobjekte.

> **TL;DR (EN):**  
> **EnergyState** (SSoT), **DecisionEvent** per action, **ExplainSession** for microcopy, **Override/ResearchToggle** for control.

---

## Kernobjekte / Core Objects

| Objekt | Felder (Auszug) | Zweck |
| --- | --- | --- |
| **EnergyState** | `ts`, `block_id`, `p_pv_kw`, `p_load_kw`, `surplus_kw`, `soc_pct`, `t_miner_c`, `price_ct_kwh`, `forecast_surplus_kw[0..5]`, `grid_import_kw`, `grid_export_kw` | Schreibgeschützter SSoT aus dem Energy Context. |
| **DecisionEvent** | `id`, `block_id`, `action (start|stop|hold|set_level)`, `reason (R1-R5|manual_override|safety)`, `trigger`, `params`, `valid_until`, `override_ttl`, `preferred_path` | Ergebnis der Regelengine; treibt UI, Logging, Research. |
| **Override** | `origin`, `action`, `ttl_blocks`, `created_at`, `note` | Temporärer manueller Eingriff bis Blockende/TTL. |
| **ExplainSession** | `id`, `decision_id`, `block_id`, `prompt_version`, `result_text_de/en`, `confidence`, `type (live|what_if)`, `valid_until` | Persistente Microcopy/Simulation; versioniert. |
| **ResearchToggleState** | `enabled`, `actor`, `ts`, `justification` | Nachweis für DSGVO-konformes Opt-in. |

> Canonical data model keeps units explicit (kW, °C, %, ¢ct) and ties UI/research back to decisions.

---

## Events (Auszug)

- `EnergyStateChangedEvent` – neues Mess-/Forecast-Frame.  
- `DecisionEvent` – Aktion + Reason/Trigger/Params.  
- `DeadbandActivatedEvent` – Stabilisierung aktiv.  
- `ResearchToggleChanged`, `ExplainSessionCreated`.

> Event catalogue aligns adapters, UI, and research tooling.
