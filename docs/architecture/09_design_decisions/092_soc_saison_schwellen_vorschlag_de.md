# 09.2 — Saisonale Miner-Schaltschwellen (Eco/Standard/Super)

> **Status 23.08.2026: die Sommer-Korrekturen (Abschnitt 4a/4b/4c) sind live umgesetzt
> und deployed** — siehe [ADR 025](./091_adr_de.md#adr-025--live-schaltschwellen-echte-hysterese--akku-reaktiver-notabstieg-detail).
> Die saisonale Schwellen-Tabelle (Abschnitt 5, Übergang/Winter) bleibt Projektion und
> ist **nicht** umgesetzt — offene Fragen 2-3 unten sind weiterhin ungeklärt. Winter-Stop
> wurde bewusst NICHT verändert (Autarkie-Vorrang, keine echten Winterdaten).
>
> **Update 26.08.2026: diese Vorsicht wurde in [ADR 027](./091_adr_de.md#adr-027--saisonale-soc-schwellen-automatik-ganzjährig-inkl-winter-detail)
> bewusst revidiert.** Statt der Headroom-Methode oben (Abschnitt 3.6) kommt dort eine andere
> Formel zum Einsatz (10%-Tiefentladeschutz-Boden + 5%-Puffer, aus R2/`rules.yaml` übernommen),
> die für Dezember ~88% Stop-SoC statt der hier vorsichtig geschätzten 68-70% ergibt — eine
> automatische, ganzjährige Anpassung ist seither live-Automation (`mvp_saison_automatik`),
> **weiterhin ohne echte Winter-Messdaten.** Offene Frage 2 unten ist damit nicht beantwortet,
> nur überstimmt. Abschnitt 5 (Tabelle) und Abschnitt 9 Frage 2 bleiben als historischer Kontext
> stehen, sind aber nicht mehr die geltende Konfiguration.

## 1. Kontext

Die reale Miner-Schaltung läuft nicht über den Python-Kern (`src/core/rules`, laut
[ADR 020](./091_adr_de.md) nur Thesis-Studienmodell), sondern komplett über die
HA-Automation `src/ha/config/packages/mvp_auto.yaml` (zwei Watchdogs,
`mvp_miner1_watchdog`/`mvp_miner2_watchdog`). Ziel dieses Vorschlags: mehr Mining-Ertrag
aus PV-Überschuss und Akku-Puffer, ohne neues Flapping, mit eigenen
Schwellenwert-Ideen für alle vier Jahreszeiten. Bestätigtes Prinzip für Zielkonflikte:
**Autarkie vor Mining-Ertrag** (R2 vor R1), falls beides nicht gleichzeitig geht.

## 2. Datengrundlage & Methode

Alle Zahlen unten stammen aus `scripts/analyze_mode_thresholds.py` (neu, read-only,
`sqlite3 ... mode=ro`), Lauf gegen `data/bitgrid.db` am 23.08.2026:

```
python scripts/analyze_mode_thresholds.py --out report.md
```

**Zeitraum:** 25.05.–23.08.2026, 10-Minuten-Blöcke. **Lücke:** Juni fehlt komplett (0
Zeilen), Mai nur 3 Tage (ab 25.05.). Effektiv nutzbare Monate: Mai (Teilmonat), Juli,
August — alles Sommer. **Für Herbst, Winter und Frühling existiert keine einzige echte
Telemetrie-Zeile.** Jede Zahl für diese drei Jahreszeiten unten ist eine begründete
Projektion (Tageslängen-Verhältnis), keine Passung an Messwerte — siehe Konfidenz-Spalte
in Abschnitt 5.

## 3. Kernbefunde

### 3.1 Reales Effizienzprofil (aus `v_modus_effizienz`, kombiniert über beide Miner)

| Modus | Watt Ø | TH/s Ø | W/TH |
|---|---:|---:|---:|
| Eco | 863 | 53,3 | 16,2 |
| Standard | 1408 | 79,2 | 17,8 |
| Super | 1721 | 92,5 | 18,6 |

Effizienz fällt mit steigendem Modus (deckt sich mit der Web-Recherche zu Avalon Q) —
das ist die reale Grundlage für die Aussage "Eco ist der sparsamste Modus, Super der
durchsatzstärkste, aber ineffizienteste".

### 3.2 Flapping ist häufiger als die erste Schätzung nahelegte — Korrektur

Die erste grobe Schätzung dieser Session (6/9 Flap-Backs) war ein Spot-Check ohne
präzise Methodik. Die saubere Neuberechnung (Lauf-längen-kodierte Segmente,
A→B→A mit B ≤ 60 Min.) ergibt:

| Miner | Gesamt-Wechsel | Flap-Backs (≤60 Min.) | Anteil |
|---|---:|---:|---:|
| miner1 | 306 | **23** | 7,5% |
| miner2 | 297 | **30** | 10,1% |

Das ist kein dramatisches Flapping, aber auch nicht vernachlässigbar — die frühere
Einschätzung "kein großes Problem" wird hiermit korrigiert (Nachprüfen statt
Übernehmen). `blocks_switch_mismatch`/`switch_mismatches` (Summe je 1 im ganzen
Zeitraum) misst etwas anderes (`workmode_set != workmode_status`, also
Kommando-vs-Hardware-Verzögerung) und darf nicht als Flapping-Beleg zitiert werden —
das war in der bisherigen Recherche unklar getrennt.

**Wahrscheinlicher Mechanismus:** P0a (Nachmittags-Cap) und P1 (Stop) laufen beide
**ohne Cooldown**, per Design ("Sicherheit vor Cooldown"). Genau das öffnet die Tür für
kurze Auf-Ab-Auf-Sequenzen, wenn ein Trigger kurz an- und wieder abspringt — exakt das
Muster, das der SoC-Sensor-Ausreißer im Nutzer-Screenshot zeigt (90%→0%→90% binnen
Minuten). Das stützt Verbesserung (c) in Abschnitt 4.

### 3.3 Der Nachmittags-Cap ist der mit Abstand größte Hebel

Für Blöcke nach dem wahren (astronomisch berechneten) Sonnenmittag, in denen
`pv_power_w - house_load_w` einen höheren Modus getragen hätte als tatsächlich lief
(Miner 1):

| Monat | Verschenkt Wh | Verschenkt TH-h |
|---|---:|---:|
| 2026-05 | 4.094 | 187,0 |
| 2026-07 | 33.287 | 1.429,0 |
| 2026-08 | 36.404 | 1.593,5 |
| **Summe** | **73.785 Wh** | **3.209,5 TH-h** |

Kontrafaktische Schätzung auf Basis der realisierten SoC-Trajektorie (keine
Batteriedynamik-Neusimulation — wenn der Miner tatsächlich mehr gezogen hätte, wäre die
SoC-Kurve selbst anders verlaufen; das ist eine obere Näherung, kein exakter Wert).

### 3.4 Super-Austritte sind überwiegend zeitpunkt-, nicht SoC-getrieben

Überraschender Befund: die SoC bei Super-Austritt liegt im Schnitt bei **94,2%**
(miner1, n=26) bzw. 97,9% (miner2) — weit über der aktuellen `soc_super_off`-Schwelle
von 85%. Das bedeutet: **die meisten realen Super→Eco-Wechsel werden nicht durch den
SoC-Schwellenwert ausgelöst, sondern durch den zeitbasierten Nachmittags-Cap (P0a)**,
der unabhängig vom SoC feuert. Das erklärt auch, warum der Sensitivitäts-Sweep für eine
eigene `soc_super_off`-Schwelle (Abschnitt 3.5) vergleichsweise kleine Zahlen liefert:
das SoC-Kollaps-Problem ist real, aber der Nachmittags-Cap dominiert das Bild um rund
zwei Größenordnungen (3.209 TH-h vs. 13–56 TH-h). **Priorität für die Umsetzung, falls
nur eine Änderung zuerst kommt: der Nachmittags-Cap, nicht `soc_super_off`.**

### 3.5 Sensitivitäts-Sweep `soc_super_off`

| Kandidat | Gewonnene TH-h (miner1, ganzer Zeitraum) |
|---:|---:|
| 88% | 0,0 |
| 90% | 13,0 |
| 92% | 13,0 |
| 95% | **56,2** |

95% liefert den größten (wenn auch absolut kleinen) Zugewinn unter den getesteten
Kandidaten.

### 3.6 Nächtliche Grundlast & Batteriepuffer

Grundlast 22–06 Uhr lokal (Sommer, `quality='ok'`): Ø **573 W**, Median 559 W (deckt
sich exakt mit der unabhängigen Grundlast-Abfrage aus dem vorherigen Analyseschritt
dieser Session). Nutzbare Akkukapazität: **12,5 kWh** (gemessen, Kommentar in
`mvp_auto.yaml`).

| Stop-Schwelle | Reserve-Band oberhalb der Schwelle, ausgedrückt in Grundlast-Stunden |
|---:|---:|
| 60% (aktuell) | 8,7 h |
| 65% | 7,6 h |
| 68% | 7,0 h |
| 70% | 6,5 h |

**Lesart, wichtig:** das ist nicht "wie lange hält das Haus nachts durch" (das Haus
zieht auch unterhalb der Stop-Schwelle weiter aus dem Akku, bis zu einem tieferen,
hier nicht bekannten Boden) — es ist "wie viele Stunden Grundlast-äquivalente Energie
gibt der aktuelle Stop-Wert dem Mining zum Verbrauch frei, bevor gestoppt wird". Bei
60% deckt dieses Band ziemlich genau eine Sommernacht (8h Fenster 22–06 Uhr) — wenig
Sicherheitsmarge, wenn die Winter-Grundlast höher liegt (Heizung) oder mehrere
sonnenarme Tage hintereinander kommen.

### 3.7 Monatstrend (empirischer Anker für die Saison-Extrapolation)

| Monat | Tage | Std-Überschuss-Stunden/Tag Ø | Super-Überschuss-Stunden/Tag Ø |
|---|---:|---:|---:|
| 2026-05 | 3 | 3,44 | 3,28 |
| 2026-07 | 25 | 7,20 | 6,71 |
| 2026-08 | 13 | 7,68 | 5,26 |

August zeigt schon leicht weniger Super-Stunden als Juli trotz mehr Standard-Stunden —
ein erstes, schwaches Signal für den einsetzenden saisonalen Rückgang nach der
Sommersonnenwende, bei sehr kleiner Stichprobe nicht überzubewerten.

**Tageslängen-Verhältnis** (eigene Berechnung, NOAA-Sonnenstandsformel, Standort
48,1°N/11,6°O): Sommer (Mitte Juli) 15,5 h Tageslicht, Übergang (Äquinoktien) 12,0 h,
Winter (Sonnenwende) 8,17 h. Verhältnis Übergang/Sommer ≈ 0,77, Winter/Sommer ≈ 0,53.
**Wichtige Einschränkung:** diese Verhältnisse basieren nur auf der Tageslänge
(Elevation > 0°), nicht auf der Einstrahlungsintensität pro Stunde — im Winter steht die
Sonne auch während der Tageslichtstunden viel flacher, plus üblicherweise mehr
Bewölkung. Die tatsächlichen Winter-Überschuss-Stunden liegen also wahrscheinlich noch
**unter** der linearen Tageslängen-Projektion, nicht darüber. Die Projektion unten ist
damit eher eine optimistische Obergrenze als ein Erwartungswert.

Projiziert (Sommer-Referenz: Juli+August gewichtet, 7,36 Std-Stunden/Tag,
6,21 Super-Stunden/Tag):

| Saison | Verhältnis | Std-Stunden/Tag (projiziert) | Super-Stunden/Tag (projiziert) |
|---|---:|---:|---:|
| Übergang | 0,77 | ~5,7 | ~4,8 |
| Winter | 0,53 | ~3,9 | ~3,3 |

## 4. Vorgeschlagene Änderungen an der Schaltlogik (Empfehlung, nicht umgesetzt)

### a) Nachmittags-Cap: von starr auf überschuss-reaktiv umstellen (höchste Priorität, siehe 3.3/3.4)

**Grundlage:** `mvp_p3b_pv_reactive_downgrade` existiert bereits, ist produktiv erprobt,
löst Super→Eco bei anhaltender Batterie-Entladung (>800 W, 5 Min., `for:`-Trigger,
Cooldown-Bypass) aus — unabhängig von der Uhrzeit. Genau dieses Muster fehlt für
Standard und wird stattdessen durch den blinden Azimut-Trigger (P0a) ersetzt.
**Empfehlung:** `mvp_p3b` generalisieren (auch Standard abdecken, mit eigenem, ggf.
schnellerem Schwellwert/Dauer), P0a auf einen reinen Fail-Safe-Zweig verengen (nur wenn
`sun.sun`-Azimut tatsächlich `unknown` ist). **Verworfene Alternative:** ein
komplett neuer `binary_sensor` nach dem Muster von `raumtemperatur_zu_heiss` —
technisch sauber, aber verworfen, weil er einen zweiten Mechanismus für dasselbe
Problem einführt ("schlankes Produkt").

### b) `soc_super_off` bekommt eine eigene Schwelle (niedrigere Priorität als a)

**Grundlage:** aktuell identisch mit `soc_std_on` (85%) statt eigenem Helfer →
Super kollabiert direkt auf Eco, Standard-Zwischenschritt entfällt. Das war laut
Code-Kommentar am 19.07.2026 eine bewusste Entscheidung ("Eco zieht weniger, der Akku
trägt das Mining länger und effizienter bis zur Hausreserve") — richtig für das
damalige Ziel (Akku-Laufzeit), aber im Widerspruch zum neuen Ziel ("mehr aus der
Leistung"). **Empfehlung:** eigener Helfer `mvp_soc_super_off_pct`, Kandidat 95%
(bester Sweep-Wert, Abschnitt 3.5); P3-Zielaktion wechselt von `Eco` auf `Standard`,
P3.5 bleibt einziger Weg weiter runter zu Eco → echte Hysterese-Kaskade
Super⇄Standard⇄Eco. **Das revidiert die 19.07.-Entscheidung, kehrt sie nicht
stillschweigend um** — siehe offene Frage 1.

### c) Debounce für die sicherheitskritische Stop-Regel (P1)

**Grundlage:** P1 (SoC < Stop → Standby) hat aktuell kein `for:` und keinen Cooldown
("Sicherheit geht vor"). Das ist richtig für echte Notfälle, aber ungeschützt gegen
kurze Sensor-Ausreißer wie im Screenshot. **Empfehlung:** eine kurze Sustained-Bedingung
(z.B. 2 aufeinanderfolgende Kontrollzyklen, ~4 Min. bei 2-Min-Takt) NUR für P1, ohne die
Reaktionszeit auf einen echten Tiefstand relevant zu verzögern. **Verworfene
Alternative:** SoC-Signal glätten (gleitender Mittelwert) — verworfen, weil das die
Reaktionszeit auf einen echten, schnellen Tiefstand unnötig global verzögert, statt nur
das Ausreißer-Problem gezielt zu adressieren.

## 5. Saisonale Schwellen-Tabelle (Vorschlag)

| | Eco-Start | Standard-Start | Standard-Off | Super-Start | Super-Off (neu) | Stop |
|---|---:|---:|---:|---:|---:|---:|
| **Sommer** (datengestützt) | 70% | 85% | 83% | 100% | 95% | 60% |
| **Übergang** (Projektion) | 65–70%¹ | 82–85%¹ | 83% | 100% | 95% | 62–63%¹ |
| **Winter** (Projektion, Autarkie-Vorrang bestätigt) | unverändert² | unverändert² | 83% | unverändert² | 95% | **68–70%¹** |

¹ Kandidaten-Spannen, keine Einzelwerte — hängen von Faktoren ab, die diese Session
nicht kennt (siehe offene Fragen 2–3). ² Bewusst unverändert gelassen: keine
Validierungsdaten für eine Absenkung im Winter, siehe Abschnitt 3.7 (Projektion ist
eher optimistisch als konservativ) — Empfehlung ist, den ersten echten Winter zu
protokollieren statt zu raten (siehe Abschnitt 7).

**Miner 2:** hat keine Super-Stufe (`mvp_miner2_super_lockout`) — die Tabelle gilt für
ihn nur bis Standard, unabhängig von der Saison.

**Warum kein 4-Wege-Split (Frühling/Herbst getrennt):** beide Jahreszeiten haben bei den
Äquinoktien nahezu identische Tageslänge (12,00 h vs. 12,08 h) — ein eigener Zahlensatz
würde unbelegte Präzision vortäuschen. Der einzige plausible Unterschied
(Herbst-Dunst/Bewölkung vs. klarerer Frühling) ist mit dieser Datenlage nicht
quantifizierbar — offene Frage 3.

## 6. YAML-Diff-Skizze (nicht angewendet, nur zur Veranschaulichung)

```yaml
# Neu: eigene Super-Off-Schwelle statt Wiederverwendung von mvp_soc_std_pct
mvp_soc_super_off_pct:
  name: "Super-Ausstieg SoC (%)"
  min: 50
  max: 100
  step: 1
  mode: box
  initial: 95        # Kandidat aus Sweep (Abschnitt 3.5), zu bestätigen
  icon: mdi:battery-80

# variables-Block der Watchdogs (Z.314-330 / Z.629-645):
# soc_super_off: "{{ states('input_number.mvp_soc_super_off_pct') | float(95) }}"
# (statt: "{{ states('input_number.mvp_soc_std_pct') | float(85) }}")

# P3-Aktion (Z.464-486): Ziel Standard statt Eco
#   action: select.select_option
#   data:
#     option: Standard   # statt: Eco

# P0a (Z.403-433): auf Fail-Safe verengen — nur wenn Azimut tatsaechlich unknown
#   condition: template
#   value_template: "{{ state_attr('sun.sun', 'azimuth') is none }}"
# (ersetzt die bisherige "azimuth >= 180"-Bedingung; die eigentliche
#  Abwaerts-Logik wandert in eine generalisierte mvp_p3b-Variante fuer Standard)
```

## 7. Fehlende Telemetrie für die nächste (saisonale) Optimierung

**Update 23.08.2026, nachträglich behoben:** sechs der ursprünglich fehlenden Signale
sind jetzt in `data/bitgrid.db` nachgerüstet und rückwirkend befüllt (Migration +
Backfill über die volle HA-History, `purge_keep_days: 365`):

- **`battery_power_w`**: der Sensor selbst hat NIE HA-History (Recorder-Exclude,
  "aus Rohdaten rekonstruierbar") — verifiziert, 0 Punkte über jeden getesteten
  Zeitraum. Stattdessen aus den beiden tatsächlich aufgezeichneten SMA-Rohsensoren
  nachgerechnet (`sma_storage_battery_power_charge_total` − `..._discharge_total`,
  siehe `configuration.yaml` Z.552-565). **5069/5069 Blöcke befüllt** (voller
  Datensatz-Zeitraum).
- **`cloud_coverage_pct`, `outdoor_temp_c`, `outdoor_humidity_pct`, `sun_azimuth_deg`,
  `sun_elevation_deg`**: existieren in HA (`sensor.cloud_coverage`,
  `sensor.outdoor_temperature`, `sensor.outdoor_humidity`, `sensor.sun_azimuth`,
  `sensor.sun_elevation`), History aber erst ab Anfang Juli 2026 (Integration wurde
  später eingerichtet, nicht seit Mai). **4821/5069 Blöcke befüllt**, echte Lücke
  Mai–Juni davor, keine erfundenen Werte. Das beantwortet die Frühling-vs-Herbst-Frage
  aus Abschnitt 5 ab dem nächsten Durchlauf tatsächlich mit Messdaten (Bewölkung),
  nicht nur mit der Tageslänge.
- **`heizung_energy_kwh_today`**: separate Heizungsenergie (`sensor.heizung_energy_daily`,
  getrennt vom Heizstab/AC-ELWA), History erst ab Mitte Juli. **2816/5069 Blöcke
  befüllt.** Hilft bei der Winter-Grundlast-Schätzung (Abschnitt 3.6), ersetzt aber
  keine Wärmepumpen-Leistungsmessung, falls eine existiert — das wurde nicht separat
  geprüft.

**Weiterhin offen, nicht behoben:**
- **`decision_events`/`kpi_log`** loggen seit 02.07.2026 gar nicht mehr (Job-Ausfall).
- **`daily_kpi`/`daily_miner_kpi`** haben nur 41/82 Tage von ~90 möglichen — die
  nächtliche Aggregation läuft nicht jede Nacht durch.

Beide sind Pipeline-/Job-Probleme, keine fehlenden Signale — brauchen eine eigene
Fehlersuche (warum läuft der nächtliche Job nicht durch), kein Schema-Update.

## 8. Konsequenzen

`src/data/daily_kpi.py` (Z.41-47) hardcoded die SoC-Band-Grenzen (60/70/85/100) als
Literale mit dem Kommentar "wer hier andere Grenzen setzt, beschreibt eine Anlage, die
es nicht gibt." Jede Schwellenänderung (erst recht eine saisonabhängige) macht diese
Aggregate sonst still falsch. Braucht ein Folge-Update, sobald etwas aus diesem
Vorschlag tatsächlich umgesetzt wird — nicht Teil dieser Runde.

## 9. Offene Fragen an den Nutzer

1. **19.07.-Entscheidung revidieren?** Soll Super wieder über Standard abwärts laufen
   (Änderung b), oder bleibt der direkte Sprung auf Eco bestehen? Meine Position: ja,
   revidieren — der ursprüngliche Grund (Akku-Laufzeit) gilt weiter, aber schwächer als
   das neue Ziel, zumal Abschnitt 3.4 zeigt, dass der Effekt ohnehin klein ist verglichen
   mit (a).
2. **Wie aggressiv im Winter?** Die Stop-Schwelle 68–70% hängt vom tatsächlichen
   Winter-Hausverbrauch ab (Heizungsart) — den kenne ich nicht. Ohne diese Information
   ist 68% mein vorsichtiger Mittelwert, keine belastbare Empfehlung.
3. **Frühling/Herbst doch trennen?** Falls eine begründete Vermutung besteht, dass
   Herbst bei euch spürbar diesiger/bewölkter ist als Frühling — das würde einen
   eigenen (niedrigeren) Herbst-Zahlensatz rechtfertigen, auch ohne Messdaten.
4. **Schwellwert/Dauer für die neue Standard-Nachmittagsregel** (Änderung a): anders als
   bei Super (800 W/5 Min., real erprobt) gibt es dafür noch keinen eingespielten Wert.
5. **`mvp_soc_super_off_pct` = 95%?** Aus dem Sweep der beste Kandidat, aber knapp vor
   dem Super-Start (100%) — schmales Band. Soll das so übernommen werden, oder eher ein
   Kompromiss (z.B. 92%) mit etwas mehr Sicherheitsabstand?

## 10. Verworfene Gesamt-Alternative

Eine ML-/Prognose-basierte Steuerung (z.B. gelerntes Modell für "wird die Sonne in
2h noch reichen") wurde nicht in Betracht gezogen — verstößt gegen das Kernprinzip
(kein ML im Entscheidungspfad, auch nicht in HA). Jede Verbesserung hier bleibt
deterministisch: feste Schwellen, feste Zeitfenster, feste Tageslängen-Berechnung.

---

**Rückfrage:** Der überraschendste Befund dieser Analyse ist, dass Super-Austritte
überwiegend zeitpunkt- statt SoC-getrieben sind (Ø 94,2% SoC bei Austritt). Was würde
diesen Befund widerlegen — anders gesagt: welches Muster in den Live-Logs würde dich
überzeugen, dass der Nachmittags-Cap doch nicht der Hauptverursacher ist?
