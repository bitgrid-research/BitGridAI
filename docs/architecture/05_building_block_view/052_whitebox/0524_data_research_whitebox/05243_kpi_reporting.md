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

*(Platzhalter für ein Bild: Der Hamster steht vor Diagrammen und Balken.
Er hält einen Taschenrechner, daneben Pfeile von Events zu KPIs wie
„kWh → Sats“, „Uptime“, „Deadband-Hit-Rate“.)*
![Hamster berechnet Kennzahlen](../../../../media/bithamster_052.png)

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
