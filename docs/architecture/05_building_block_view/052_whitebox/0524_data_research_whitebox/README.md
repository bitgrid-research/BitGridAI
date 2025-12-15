# 05.2.4 Whitebox Data und Research

Das Gedächtnis des Systems.

Diese Whitebox bündelt alles, was **bleiben**, **nachvollziehbar** und **auswertbar** sein muss:
Persistenz, Audit-Trail, KPIs und Exporte für Forschung und Replays.

Nichts davon ist Selbstzweck.  
Alles folgt einem Prinzip: **Was entschieden wurde, muss später erklärbar und reproduzierbar sein.**

*(Platzhalter für ein Bild: Der Hamster sitzt in einem Archiv.
Um ihn herum Ordner, Parquet-Dateien und ein Notizblock mit Diagrammen.)*
![Hamster im Datenarchiv](../media/pixel_art_data_research.png)

---

## Scope

- Lokale Persistenz für Betrieb und Analyse
- Append-only Audit-Trail für Entscheidungen und Zustände
- KPI-Berechnung für Transparenz und Forschung
- Export- und Replay-Funktion **nur mit explizitem Opt-in**

---

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **Operational DB** | SQLite für aktuelle Zustände, Konfigurationen und TTLs. | ACID, lokale Datei `data/bitgrid.sqlite`. |
| **Event / Log Store** | Append-only Speicherung von DecisionEvents, States und KPIs. | Parquet/JSON, versioniert, Hash/Checksum pro Datei. |
| **KPI / Reporting** | Aggregiert Kennzahlen (z.B. kWh → Sats, Verfügbarkeit). | Batch- oder on-demand, schreibt nach Parquet/JSON. |
| **Export / Replay Service** | Erstellt signierte Export-Bundles für Forschung. | Opt-in gesteuert, liefert Hash + Manifest. |

---

## Level-3-Details

- [5.2.4.1 Operational DB](./05241_operational_db.md)
- [5.2.4.2 Event / Log Store](./05242_event_log_store.md)
- [5.2.4.3 KPI / Reporting](./05243_kpi_reporting.md)
- [5.2.4.4 Export / Replay Service](./05244_export_replay.md)

---

## Schnittstellen

**Provided**
- Logs und KPIs (Dateien, optional REST `POST /research/export`)
- Health- und Storage-Metriken
- Replay- und Export-Bundles

**Required**
- DecisionEvents und States aus Core/UI
- Verfügbarer lokaler Speicher
- Opt-in-Flags und Export-Aufträge

---

## Hauptdatenflüsse

1) DecisionEvents / States → Event Store → KPI-Aggregationen  
2) KPIs → UI / Reports → optionaler Export  
3) Export-Auftrag → Export Service → Parquet/ZIP-Bundle + Hash + Manifest  

---

## Qualitäts- und Betriebsaspekte

- **Append-only:** keine stillen Änderungen, volle Nachvollziehbarkeit.  
- **Local-first:** Daten verbleiben standardmäßig auf dem System.  
- **Governance:** Exporte nur bei aktivem Opt-in.  
- **Kontrolliert:** Speichergrenzen und Retention-Policies konfigurierbar.

---
> **Nächster Schritt:** Daten sind gespeichert und erklärbar.  
> Jetzt sichern wir den Betrieb ab: Zugriff, Konfiguration und Beobachtbarkeit.
>
> 👉 Weiter zu **[5.2.5 Operations (Security, Config & Observability)](../0525_operations_whitebox/README.md)**
>
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](./README.md)**
> 
> 🔙 Zurück zu **[5.1 Whitebox Gesamtsystem](../051_blackbox/051_blackbox.md)**

