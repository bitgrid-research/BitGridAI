# 05.2.4.3 - Baustein: KPI / Reporting

Vom Ereignis zur Erkenntnis.

Der KPI- und Reporting-Baustein verdichtet rohe Ereignisse
zu **verständlich messbaren Kennzahlen**.
Er beantwortet nicht *was passiert ist* –  
sondern **wie gut das System arbeitet**.

Hier entstehen Zahlen wie:
- Energie → Ertrag  
- Stabilität → Ruhe  
- Entscheidungen → Wirkung  

Ohne Interpretation, ohne Schönfärbung.  
Nur reproduzierbare Fakten.


![Hamster berechnet Kennzahlen](../../../../media/architecture/05_building_block_view/bithamster_052.png)

&nbsp;

## Verantwortung

- Aggregation von KPIs aus Events und States
- Zentrale Definition von Kennzahlen und Formeln
- Bereitstellung für UI, Reports und Exporte
- Optionales Erkennen von Auffälligkeiten über Schwellwerte

&nbsp;

## Struktur

- **Aggregator Jobs**  
  Periodische oder on-demand Jobs zur KPI-Berechnung
  (zeitlich entkoppelt vom Core).

- **Metric Catalog**  
  Definierte Kennzahlen mit:
  - Formel  
  - Einheit  
  - Version  
  (z.B. `energy_to_sats`, `uptime_pct`, `deadband_hit_rate`).

- **Writer**  
  Persistiert KPI-Resultate als Parquet/JSON  
  und optional als Snapshot für schnelle UI-Zugriffe.

- **Alert Hooks**  
  Prüfen KPIs gegen optionale Schwellen
  (Qualität, Stabilität, Auffälligkeiten).

&nbsp;

## Schnittstellen

**Provided**
- KPI-Dateien (Parquet / JSON)
- Optionale REST/WS-Feeds für UI und Reports
- Alerts bei Grenzwertverletzungen

**Required**
- Event- und State-Logs
- Zeitbasis und Block-Informationen
- Konfiguration für Intervalle, Formeln und Schwellen

&nbsp;

## Ablauf (vereinfacht)

1) Aggregator Job liest Events und States aus dem Log Store.  
2) Kennzahlen werden gemäß Metric Catalog berechnet.  
3) Writer speichert KPI-Ergebnisse und aktualisiert Snapshots.  
4) Alert Hooks prüfen Schwellwerte und melden Auffälligkeiten.  
5) UI, Reports oder Export-Services konsumieren KPI-Daten read-only.

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Konsistenz**  
  Einheitliche Formeln und Einheiten; Metric Catalog ist versioniert.

- **Reproduzierbarkeit**  
  Gleiche Inputs → gleiche KPIs.  
  Ideal für Replays und Forschung.

- **Ressourcenschonend**  
  KPI-Jobs laufen außerhalb des Entscheidungs-Takts.

- **Trennung von Bewertung und Steuerung**  
  KPIs informieren – sie steuern nichts.

- **Sichtbarer Aufzeichnungsstatus**  
  `src/data/recording_status.py` prüft nächtlich, ob die Kette
  HA-Recorder → `ha_history_sync` → `bitgrid.db` noch Daten liefert, und schreibt
  das Ergebnis als lokales JSON-Artefakt (`www/recording_status.json`). Das Modul
  öffnet die Datenbank nur lesend. Die Karte „Datenaufzeichnung" im Tab
  Einstellungen zeigt das Artefakt an und prüft sein Alter selbst gegen die
  aktuelle Uhrzeit: bleibt der Job aus, wird die Anzeige rot (Totmann-Prinzip).  
  Grenze der Aussage: 144 Blöcke pro Tag heißt vollständig übertragen, nicht
  lückenlos gemessen. Der Sync füllt Ausfälle von Home Assistant mit dem letzten
  Wert auf, solche Blöcke sind in der Datenbank derzeit nicht von gemessenen
  unterscheidbar (offener Punkt am Resampler).

---
> **Nächster Schritt:**  
> Kennzahlen sind berechnet und verständlich aufbereitet.
> Jetzt bleibt noch die kontrollierte Weitergabe nach außen.
>
> 👉 Weiter zu **[5.2.4.4 - Baustein: Export / Replay Service](./05244_export_replay.md)**
>
> 🔙 Zurück zu **[5.2.4 - Whitebox: Data und Research](./README.md)**
>
> 🔙 Zurück zu **[5.2 - Level-2-Whiteboxes](../README.md)**
