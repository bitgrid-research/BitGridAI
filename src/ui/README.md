# src/ui

Optionale eigene UI — falls nicht ausschließlich Home Assistant genutzt wird.

Die primäre UI läuft über `src/ha/` (HA-Dashboards). Eine eigene UI macht Sinn für Einbettung in andere Systeme, mobile Web-Apps oder ein Forschungs-Interface mit tieferer Explain-Darstellung.

Die UI darf nur lesen und Override-Kommandos senden — sie verändert nie direkt `EnergyState` oder Entscheidungen.

---

## Verzeichnisstruktur (geplant)

```
ui/
├── api.py                 # REST-API (FastAPI) — State, Decision, Override
├── static/                # JS/CSS für Web-Frontend
├── templates/             # HTML-Templates (Jinja2 o.ä.)
└── __init__.py
```

---

## API-Vertrag (`api.py`)

Drei Endpunkte — mehr braucht die UI nicht:

### `GET /state`

```json
{
  "block_id": "2024-01-15T10:00:00",
  "pv_power_w": 3200,
  "house_load_w": 800,
  "surplus_kw": 2.4,
  "battery_soc_pct": 80,
  "miner_temp_c": 42,
  "quality": "ok",
  "missing_signals": []
}
```

### `GET /decision`

```json
{
  "action": "START",
  "decision_code": "START_R1_SURPLUS_OK",
  "short": "Überschuss verfügbar",
  "long": "PV-Leistung übersteigt Hausverbrauch um 2.4 kW.",
  "valid_until": "2024-01-15T10:20:00Z",
  "rule_states": {
    "R1": "ok", "R2": "ok", "R3": "ok", "R4": "ok", "R5": "ok"
  }
}
```

### `POST /override`

```json
// Request
{ "action": "STOP", "duration_min": 30 }

// Response — Erfolg
{ "accepted": true, "command_id": "uuid-...", "valid_until": "...", "message": "Override akzeptiert" }

// Response — Ablehnung (R3 aktiv)
{ "accepted": false, "reason": "R3_SAFETY_ACTIVE — Override nicht erlaubt" }
```

---

## Konventionen

**Read-only bis auf Override:** Die UI ändert nie `EnergyState`, Config oder Regeln direkt. Nur Overrides über den definierten Endpunkt.

**Auth:** Bearer-Token-Auth. `auth_enabled` Feature-Flag in `ops/config/feature_flags.yaml`.

**Rate-Limiting:** Override-Endpunkt: max. 10 Requests/Minute pro Client.

**Kein Business-Logic:** Die API ist eine dünne Schicht über `core/` und `data/`. Keine Regel-Auswertung in `api.py`.

---

## Nächste Schritte

- [ ] Scope-Entscheidung: Eigene Web-UI oder nur HA-Dashboard?
- [ ] Falls ja: `api.py` mit den drei Endpunkten (FastAPI)
- [ ] Auth-Middleware (Token-Validierung)
- [ ] Rate-Limiting für Override-Endpunkt
