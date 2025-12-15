# 05.2.4.2 Event / Log Store

Die unveränderliche Erinnerung.

Der Event / Log Store ist das **Gedächtnis ohne Vergessen**.  
Hier wird festgehalten, **was tatsächlich passiert ist** – nicht als aktueller Zustand,
sondern als **lückenlose, append-only Historie**.

Er bildet die Grundlage für:
Replays, Audits, Analysen und Forschung.

Was hier liegt, wird **nicht überschrieben**.  
Nur gelesen, geprüft und nachvollzogen.

*(Platzhalter für ein Bild: Der Hamster schreibt Einträge in ein großes, gebundenes Logbuch.
Jede Seite trägt einen Zeitstempel und ein kleines Schloss. Daneben liegen Parquet-Dateien
und ein Prüfsummen-Stempel.)*
![Hamster im Event-Archiv](../media/pixel_art_event_log_store.png)

&nbsp;

## Verantwortung

- Append-only Speicherung von:
  - `DecisionEvents`
  - State-Snapshots
  - KPIs
- Sicherstellung von Integrität durch Hashes und Versionierung
- Grundlage für Replays, Audits und Exporte
- Verwaltung von Retention und Speichergrenzen

&nbsp;

## Struktur

- **Ingest Writer**  
  Schreibt Events und States fortlaufend in Dateien,  
  partitioniert nach Datum und Block-ID.

- **Formatters**  
  Serialisieren Daten nach **Parquet** (primär) oder **JSON**  
  inklusive expliziter Schema-Versionen.

- **Checksummer**  
  Erzeugt Hashes pro Datei oder Batch und speichert Metadaten
  zur späteren Verifikation.

- **Retention Manager**  
  Setzt Aufbewahrungsregeln durch (Rotation, Löschung, Archivierung)
  und meldet Status an Observability.

&nbsp;

## Schnittstellen

**Provided**
- Logdateien (Parquet / JSON)
- Metadaten inkl. Hashes und Schema-Versionen
- Status- und Fehler-Events bei Rotation oder Grenzwerten

**Required**
- `DecisionEvents`, States und KPIs
- Konfigurierte Speicherpfade
- Retention- und Aufbewahrungsregeln

&nbsp;

## Ablauf (vereinfacht)

1) DecisionEvents, States oder KPIs treffen ein.  
2) Ingest Writer serialisiert sie und schreibt append-only in Dateien.  
3) Checksummer erzeugt Hashes und persistiert Metadaten.  
4) Retention Manager prüft Speichergrenzen und rotiert bei Bedarf.  
5) UI, Replay- oder Export-Services lesen die Dateien **read-only**.

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Append-only**  
  Keine Updates, keine stillen Änderungen, keine „Korrekturen im Nachhinein“.

- **Integrität**  
  Jede Datei ist über Hashes überprüfbar – Audit- und Research-fähig.

- **Langzeitstabilität**  
  Klare Dateiformate, versionierte Schemas, dokumentierte Lesepfade.

- **Kontrolliert**  
  Retention-Policies verhindern unkontrolliertes Wachstum.

---
> **Nächster Schritt:**  
> Ereignisse und Zustände sind jetzt dauerhaft und überprüfbar gespeichert.
> Doch rohe Daten allein reichen nicht aus.
>
> Im nächsten Baustein verdichten wir diese Historie zu **Kennzahlen**:
> Auswertung, Aggregation und Reporting für Transparenz und Forschung.
>
> 👉 Weiter zu **[5.2.4.3 KPI / Reporting](./05243_kpi_reporting.md)**
>
> 🔙 Zurück zu **[5.2.4 Data und Research](./README.md)**
>
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](../README.md)**
