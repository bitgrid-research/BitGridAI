# 05.2.4.3 KPI/Reporting

Verantwortung: aggregiert Kennzahlen (z.B. kWh->Sats, Verfuegbarkeit, Deadband-Hit-Rate) aus Events/States und stellt sie fuer UI/Reports/Export bereit.

## Struktur

- **Aggregator Jobs:** periodische oder on-demand Jobs fuer KPIs.  
- **Metric Catalog:** definierte Kennzahlen mit Formeln/Einheiten.  
- **Writer:** persistiert KPI-Resultate (Parquet/JSON) und optional DB-Snapshots.  
- **Alert Hooks:** optionale Schwellwerte fuer Health/Qualitaet.

## Schnittstellen

- **Provided:** KPI-Dateien, optional REST/WS-Feed an UI/Reports, Alerts.  
- **Required:** Event/State-Logs, Zeitbasis, Konfiguration fuer KPI-Intervalle und Schwellen.

## Ablauf (vereinfacht)

1) Aggregator liest Events/States -> berechnet Kennzahlen laut Metric Catalog.  
2) Writer speichert KPIs (Parquet/JSON) und stellt Snapshots bereit.  
3) Alert Hooks pruefen Schwellwerte -> melden an UI/Health.  
4) UI/Export konsumiert KPI-Daten fuer Anzeige/Bundle.

## Qualitaet und Betrieb

- Konsistente Einheiten und Formeln; versionierter Metric Catalog.  
- Resource-Aware: Jobs laufen zeitlich entkoppelt vom Core-Takt.  
- Wiederholbare Berechnungen fuer Replays (gleiche Inputs -> gleiche KPIs).

---
> Zurueck zu **[5.2.4.x Data und Research (Level 3)](./README.md)**  
> Zurueck zu **[5.2.4 Whitebox Data und Research](../0524_data_research_whitebox.md)**
