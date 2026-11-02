# Datenrettung PV-Ertrag 23.-25.09.2026

## Anlass

Vom **23.09.2026 01:47** bis **25.09.2026 12:20** (Lokalzeit) hat Home Assistant
keine Daten des PV-Wechselrichters (Sunny Tripower, SN 3012953672) erfasst. Der
pysmaplus-Config-Entry steckte in `ConfigEntryState.FAILED_UNLOAD`, alle 28
Entities des Geräts waren `unavailable`.

Die Anlage lief in dieser Zeit normal weiter. Verloren ging nur die Erfassung.

## Was in dieser Zeit falsch aufgezeichnet wurde

Nicht als Lücke, sondern **als Messwert 0 W**. Der Template-Sensor
`sensor.pv_power_w` ist mit `availability: "true"` und `| float(0)` definiert:
er meldet sich als verfügbar und wandelt `unavailable` in `0.0`. Alle
abgeleiteten Größen (Integral, Tages-kWh, Autarkiegrad, MQTT-Snapshots) haben
daher drei Tage lang echte Nullen aufgezeichnet statt fehlender Werte.

## Quelle dieser Rettung

Das **5-Minuten-Ertragslog des Wechselrichters selbst**, ausgelesen über
WebConnect (`/dyn/getLogger.json`, Key 28672) am 25.09.2026. Lokale Quelle, kein
Sunny Portal, kein Cloud-Zugriff. Das Gerät führt dieses Log unabhängig von
Home Assistant, es war vom Ausfall nicht betroffen.

Gegengeprüft mit dem Tageslog des Geräts (Key 28704), das dieselben Tagessummen
liefert.

## Ergebnis

| Tag | echter Ertrag | von HA erfasst |
|---|---|---|
| 22.09.2026 | 37,967 kWh | 38,349 kWh (Kontrolltag) |
| 23.09.2026 | **40,106 kWh** | 0 |
| 24.09.2026 | **25,766 kWh** | 0 |
| 25.09.2026 | 17,968 kWh (bis 13:00) | erst ab 12:20 |

Fehlbetrag in der HA-Bilanz: **rund 66 kWh** für den 23. und 24.09., plus der
Vormittag des 25.09.

## Validierung

Der 22.09. ist Kontrolltag: HA hat ihn vollständig erfasst, das Gerätelog
ebenfalls. Abweichung 38,349 gegen 37,967 kWh, also **1,0 %**. Die Differenz ist
erwartbar, weil HA über Momentanwerte trapezförmig integriert, während das
Gerätelog einen echten Zählerstand fortschreibt. Die Zählerstandsmethode ist die
genauere von beiden.

Weitere Prüfungen: 1021 Messpunkte ohne Zeitlücke, keine negativen Zählerdeltas,
Maximalleistung 7500 W (anlagenplausibel).

## Limitationen

- **Rekonstruktion, keine Originalmessung.** Bei jeder Verwendung als solche
  kennzeichnen.
- Die Werte sind **5-Minuten-Mittel** aus Zählerdifferenzen, keine
  Momentanleistungen. Kurze Spitzen sind geglättet.
- Nur der **Tripower** (PV). Hauslast, Netzbezug und SoC für diesen Zeitraum
  sind damit **nicht** rekonstruiert, sie hingen an anderen Signalen.
- Die Spalte `avg_power_w` ist abgeleitet (`delta_wh * 3600 / dt`), nicht gemessen.

## Datei

`2026-09-22_25_pv_tripower_5min.csv`

| Spalte | Bedeutung |
|---|---|
| `ts_local` | Zeitstempel, lokale Zeit (CEST) |
| `unix` | Zeitstempel, Unix-Epoch |
| `meter_wh` | Zählerstand des Wechselrichters in Wh (kumulativ) |
| `delta_wh` | Zuwachs gegenüber dem vorigen Messpunkt |
| `avg_power_w` | daraus abgeleitete mittlere Leistung im Intervall |

## Korrektur der HA-Zähler am 25.09.2026

Beim Nachtragen zeigte sich, dass die Zielzähler unabhängig vom Ausfall falsch
standen. Gegengerechnet wurde mit dem Tageslog des Wechselrichters (Key 28704,
Zeitraum 30.12.2025 bis 25.09.2026, 269 Tageseinträge).

| Entity | vorher | nachher | Begründung |
|---|---|---|---|
| `input_number.pv_kwh_ytd` | 7.081,633 | **10.103,791** | echter Jahresertrag 2026 bis Ende 24.09. |
| `input_number.pv_kwh_mtd` | 6.940,942 | **890,805** | echter Septemberertrag bis Ende 24.09. |
| `input_number.pv_energy_midnight` | 7.625,074 | **7.610,675** | Baseline so verschoben, dass `pv_energy_daily` den vollen 25.09. zeigt statt erst ab 12:20 |

Der heutige Ertrag ist in MTD und YTD bewusst **nicht** enthalten: den addiert
die Automation `stats_accumulate_ytd` um 00:00:03 selbst, sonst zählte er doppelt.

Kontrolle nach der Korrektur: `sensor.pv_energy_daily` = 19,128 kWh gegen
19,127 kWh laut Zählerstand, Abweichung 1 Wh.

### Warum die Zähler falsch standen

Vermutlich derselbe Mechanismus wie beim Ausfall selbst. `pv_energy_daily` ist
`Integral minus Baseline`. Fällt die Baseline durch `| float(0)` einmal auf 0,
etwa weil ein `input_number` nach einem Neustart nicht wiederhergestellt wurde,
dann ist der "Tagesertrag" an diesem Tag der komplette Integralstand, also rund
6.900 kWh. Genau diese Größenordnung steckte in MTD. Das ist eine Vermutung,
nicht belegt: `input_number` ist vom Recorder ausgeschlossen, es gibt also keine
Historie, an der man es nachweisen könnte.

Monatswerte 2026 laut Wechselrichter, als Referenz für künftige Prüfungen:

| Monat | kWh | Monat | kWh |
|---|---|---|---|
| Januar | 175,285 | Juni | 1.631,611 |
| Februar | 318,783 | Juli | 1.769,547 |
| März | 964,383 | August | 1.371,871 |
| April | 1.465,634 | September (bis 24.) | 890,805 |
| Mai | 1.515,872 | | |
