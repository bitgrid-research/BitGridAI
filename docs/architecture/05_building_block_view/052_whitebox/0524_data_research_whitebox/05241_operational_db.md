# 05.2.4.1 Operational DB

Verantwortung: speichert aktuelle Zustaende, Konfigurationen, TTLs und Metadaten fuer laufenden Betrieb in SQLite.

## Struktur

- **Schema Core:** Tabellen fuer State-Snapshots, Config, Overrides, Schedules.
- **Integrity Guard:** ACID-Transaktionen, Foreign Keys, pragma fuer Durability.
- **Migration Layer:** versionierte Migrationen (z.B. SQL/DDL Files).
- **Access Layer:** lokaler Zugriff, kein Remote; bevorzugt READ_COMMITTED.

## Schnittstellen

- **Provided:** konsistente Reads fuer Core/UI/Preview; Writes fuer laufenden Betrieb.
- **Required:** DecisionEvents/State-Writes, Config/Policy Updates, Migrationen.

## Ablauf (vereinfacht)

1) Core/UI schreiben aktualisierte State/Override/Config.  
2) Integrity Guard stellt ACID sicher, setzt pragmas.  
3) Reader (UI/Preview) bekommt konsistente Snapshots.  
4) Migrations laufen versioniert vor Start.

## Qualitaet und Betrieb

- Nur lokal, keine Netzfreigabe.
- Durability vs. Performance konfigurierbar (WAL/Sync).
- Regelmaessige Backups; Recover-Test.

---
> Zurueck zu **[5.2.4.x Data und Research (Level 3)](./README.md)**  
> Zurueck zu **[5.2.4 Whitebox Data und Research](../0524_data_research_whitebox.md)**
