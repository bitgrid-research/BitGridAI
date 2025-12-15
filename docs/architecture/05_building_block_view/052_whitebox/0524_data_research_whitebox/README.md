# 05.2.4 Whitebox Data und Research

Scope: Persistenz, Audit-Trail, KPIs und Export-Funktion fuer Replays/Research unter Opt-in-Governance.

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **Operational DB** | SQLite fuer aktuelle Zustaende, Konfigurationen, TTLs. | ACID, lokale Files `data/bitgrid.sqlite`. |
| **Event/Log Store** | Append-only Parquet/JSON fuer DecisionEvents, States, KPIs. | Versioniert, Hash/Checksum pro File. |
| **KPI/Reporting** | Aggregiert Kennzahlen (z.B. kWh->Sats, Verfuegbarkeit). | Batch- oder on-demand; schreibt in Parquet/JSON. |
| **Export/Replay Service** | Erstellt signierte Export-Bundles fuer Forschung. | Opt-in gesteuert; liefert Hash und Manifest. |

## Level-3-Details

- [5.2.4.1 Operational DB](./0524_data_research_whitebox/05241_operational_db.md)
- [5.2.4.2 Event/Log Store](./0524_data_research_whitebox/05242_event_log_store.md)
- [5.2.4.3 KPI/Reporting](./0524_data_research_whitebox/05243_kpi_reporting.md)
- [5.2.4.4 Export/Replay Service](./0524_data_research_whitebox/05244_export_replay.md)

## Schnittstellen

- **Provided:** Logs und KPIs (Dateien, optional REST `/research/export`), Health/Storage-Metriken, Replay-Bundles.
- **Required:** DecisionEvents/States aus Core/UI, Speicherkapazitaet, Opt-in-Flags und Export-Auftraege.

## Hauptdatenfluesse

1) DecisionEvents/States -> Event Store -> KPIs/Aggregationen.  
2) KPIs -> UI/Reports -> optional Export.  
3) Export-Auftrag -> Export-Service -> ZIP/Parquet-Bundle + Hash.

## Qualitaets- und Betriebsaspekte

- Append-only fuer Nachvollziehbarkeit; keine stillen Mutationen.  
- Speichergrenzen und Retention-Policy konfigurierbar.  
- Exporte sind optional, standardmaessig lokal verbleibend.

---
> Zurueck zu **[5.2 Level-2-Whiteboxes](./README.md)**  
> Zurueck zu **[5.1 Whitebox Gesamtsystem](../051_blackbox/051_blackbox.md)**
