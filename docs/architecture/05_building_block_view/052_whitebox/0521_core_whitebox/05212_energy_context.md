# 05.2.1.2 Energy Context

Verantwortung: konsolidiert Telemetrie und Forecasts zum `EnergyState` (Single Source of Truth), validiert Einheiten und Zeitstempel, stellt Snapshots fuer Regel- und Preview-Pfade bereit.

## Struktur

- **Input Normalizer:** wandelt Rohdaten in SI-Einheiten, prueft Plausibilitaet.
- **State Builder:** fuehrt Werte zusammen (PV, Last, Netz, Speicher, Temperaturen, Preise, Forecasts).
- **Completeness Guard:** erzwingt Mindest-Signale pro Block (z.B. Grid + PV + Miner-Temp), markiert fehlende Daten.
- **Snapshot Cache:** stellt letztes konsistentes `EnergyState` fuer Rule Engine und Preview bereit.

## Schnittstellen

- **Provided:** `EnergyState` Snapshots, Fehler/Warnings bei fehlenden/inkonsistenten Daten, Metadaten (Quelle, Zeitbasis).
- **Required:** Telemetrie aus Adaptern (PV, Meter, Storage, Miner), Forecast/Preise, Einheiten-Profile (Device Profiles), Zeitquelle.

## Ablauf (vereinfacht)

1) Eingangsdaten treffen ein (MQTT/REST/Modbus) -> Input Normalizer wandelt und stempelt.  
2) State Builder aggregiert Werte, berechnet abgeleitete Groessen (z.B. `surplus_kw`).  
3) Completeness Guard prueft Pflichtfelder; bei Luecken: Status=degraded, optional Halten des letzten guten Wertes.  
4) Snapshot Cache liefert konsistenten `EnergyState` an Rule Engine, UI/Explain und Logging.

## Qualitaet und Betrieb

- Einheitensicherheit: alle internen Werte in SI; Ablehnung oder Korrektur mit Flag bei Abweichung.  
- Zeitkonsistenz: maximaler Drift zwischen Eingaben konfigurierbar; sonst Degradation/Fail-safe.  
- Nachvollziehbarkeit: jedes Feld traegt Quelle und Timestamp fuer Audits/Replays.

---
> Zurueck zu **[5.2.1.x Core-Orchestrierung (Level 3)](./README.md)**  
> Zurueck zu **[5.2.1 Core-Orchestrierung](../0521_core_whitebox.md)**
