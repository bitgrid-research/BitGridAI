# 085 – Fehler- & Ausnahmebehandlung / Error & Exception Handling

TODO: Wenn es knallt: Wie fangen wir Fehler einheitlich ab, ohne dass das System abstürzt, und wie informieren wir den Nutzer (oder das Log)?

> **Kurzüberblick:**  
> Fehler führen zu **sicheren, erklärbaren Zuständen**: Sensor-Stale → hold, Adapterfehler → Retry/Circuit-Breaker, Safety-Stop bei kritischen Werten, Zeitdrift → Block-Hold & Re-Sync.

> **TL;DR (EN):**  
> Errors degrade to safe, explainable states: stale → hold, adapter retry/breaker, safety stop on critical values, time drift → hold + re-sync.

---

## Patterns (aus Laufzeitsicht)

- **Sensor-Stale** → State markieren, **hold** statt **start**; UI-Warnung.  
- **Adapterfehler** → Retry mit Backoff; bei Persistenz → **stop → safe**.  
- **Zeitdrift** → 1 Block **hold**, NTP re-sync; Hinweis im UI.  
- **Inkonsistente Daten** → Frame verwerfen; letzten konsistenten State halten.  
- **Thermo/SoC – Safety** → sofortiger **stop**, Deadband ignorieren (R3/R2).  
- **Health-Monitor** sammelt Broker/Adapter/Sensor-Status → Health-Banner + Logs.

---

## Runbook-Hinweise (aus Kap. 10/11)

- **RB-01 Deadband-Tuning**: Flapping-Raten per Replay prüfen, Regeln anpassen.  
- **RB-02 Safety Stop Drill**: Fault-Injection → DecisionEvent `R3` + UI-Alarm verifizieren.  
- **RB-03 Drift Recovery**: `ntpctl skew` simulieren, Hold & Re-Sync beobachten.  
- **RB-04 Explain Audit**: `/research/export` → Coverage prüfen.  
- **RB-05 Forecast Disable**: `r4_enabled=false` setzen, Replay „forecast-storm“.

> Exception handling always favours safety and traceability over availability.
