# 05.2.4.2 Event/Log Store

Verantwortung: fuehrt append-only Logs fuer DecisionEvents, States und KPIs (Parquet/JSON), stellt Checksums/Versionierung fuer Replays und Audits bereit.

## Struktur

- **Ingest Writer:** schreibt Events/Stati in Files (Partitionierung nach Datum/Block).
- **Formatters:** Parquet/JSON Serializer mit Schema-Version.
- **Checksummer:** erzeugt Hash pro File/Batch; Metadaten fuer Verifikation.
- **Retention Manager:** verwaltet Aufbewahrungsregeln und Rotation.

## Schnittstellen

- **Provided:** Logfiles (Parquet/JSON), Metadaten/Hashes, Status/Errors bei Rotation.
- **Required:** DecisionEvents/States/KPIs, Speicherpfade, Retention-Policy.

## Ablauf (vereinfacht)

1) Events/States treffen ein -> Ingest Writer serialisiert (Parquet/JSON).  
2) Checksummer erzeugt Hash, legt Metadaten ab.  
3) Retention Manager rotiert/loescht gemaess Policy; meldet Health.  
4) UI/Export koennen Dateien lesen oder referenzieren.

## Qualitaet und Betrieb

- Append-only, keine stillen Mutationen; Hash pro File fuer Integritaet.  
- Rotation und Speichergrenzen konfigurierbar.  
- Lesepfade dokumentiert fuer Replays/Exports.

---
> Zurueck zu **[5.2.4.x Data und Research (Level 3)](./README.md)**  
> Zurueck zu **[5.2.4 Whitebox Data und Research](../0524_data_research_whitebox.md)**
