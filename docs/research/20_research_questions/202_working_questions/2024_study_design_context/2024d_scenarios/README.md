# 20.2.4.4 - SD-WQ4 - Szenarien für Simulation und Studie (v1)

Zehn deterministische Szenarien, eingebettet in **einen zusammenhängenden Mining-Tag**.
Jedes Szenario ist ein 10-Minuten-Block mit vollständig spezifiziertem `EnergyState`,
sodass der Entscheidungskern per **Replay** exakt reproduzierbar denselben
`decision_code` erzeugt (vgl. Standardisierung in [2024a](../2024a_study_design_sampling.md)).

> **Jedes Szenario hat eine eigene Datei** (Überblick unten). Diese README bündelt
> Datengrundlage, IST-Zustand und Methodik.

## Szenario-Übersicht

| ID | Szenario | Regel | Erwartete Entscheidung | Belegung | Datei |
|---|---|---|---|---|---|
| **S1** | Klarer Start | R1 | `START_R1_SURPLUS_OK` | ✅ 123× | [S01](./S01_klarer_start.md) |
| **S2** | Kein Überschuss | R1 | `NOOP_R1_INSUFFICIENT_SURPLUS` | ✅ 20× | [S02](./S02_kein_ueberschuss.md) |
| **S3** ⚑ | Sonne, aber Preis hoch | R1 | `NOOP_R1_PRICE_TOO_HIGH` | ⚠ konstruieren | [S03](./S03_preis_zu_hoch.md) |
| **S4** ⚑ | Übertemperatur | R3 | `STOP_R3_OVERTEMP` | 🔧 Injektion | [S04](./S04_uebertemperatur.md) |
| **S5** | Kommunikationsausfall | R3 | `STOP_R3_COMM_TIMEOUT` | 🔧 Injektion | [S05](./S05_kommunikationsausfall.md) |
| **S6** ⚑ | Batterie-Schutz (soft) | R2 | `NOOP_R2_SOC_SOFT_MIN` | ✅ 184× | [S06](./S06_batterie_soft.md) |
| **S7** | Batterie-Notstopp (hard) | R2 | `STOP_R2_SOC_HARD_MIN` | ✅ 32× | [S07](./S07_batterie_hard.md) |
| **S8** ⚑ | Wolke → Netzbezug | R2 | `STOP_R2_GRID_IMPORT_EXCEEDED` | 🔧 Injektion ¹ | [S08](./S08_netzbezug.md) |
| **S9** ⚑ | Forecast blockiert | R4 | `NOOP_R4_FORECAST_PV_INSUFFICIENT` | ✅ 822× | [S09](./S09_forecast.md) |
| **S10** | Anti-Flapping | R5 | `NOOP_R5_MIN_RUNTIME_NOT_REACHED` | ✅ 391× | [S10](./S10_anti_flapping.md) |

⚑ = diskriminierende Items (kontraintuitiv). ¹ S8 nach R2-Netto-Fix neu zu belegen (siehe IST-Zustand).

## Designprinzipien

1. **Ein Lehrziel pro Szenario** — sauber zuordenbar zum Regelverständnis-Score (0–12, siehe [2024b](../2024b_tasks_instruments_metrics.md)).
2. **Reproduzierbar** — definierter `EnergyState` + Engine-Inputs → deterministischer `decision_code`.
3. **Diskriminierend** — die kontraintuitiven Fälle (S3, S6, S9) trennen statische von persona-adaptiver Erklärung.
4. **Vollständige Abdeckung** — alle Regeln R1–R5 **und** die Prioritätskette R3 > R2 > R4 > R5 > R1.
5. **Zentralkonzept „Steuern statt Einspeisen"** wird mehrfach berührt (S1, S3, S8).

Alle Werte beziehen sich auf die Default-Schwellen der `RuleEngineConfig`:
`surplus_min 1,5 kW · price_max 25 ct · soc_soft 58 % · soc_hard 50 % · max_grid_import 500 W · max_temp 85 °C · comm_timeout 60 s · min_predicted_surplus 2,0 kW · price_spike 30 ct · deadband 2 · min_runtime 3 · min_pause 2`.

### Realbetrieb → Energielabor (maßstabsgetreue Nachbildung) + Kern (offen)

**Ziel:** Das **Energielabor** bildet den **Realbetrieb maßstabsgetreu** nach — die kleinen
Labor-Miner (**Bitaxe Gamma, NerdQaxe++**) ahmen die Steuerung der **2× Avalon Q** nach:
dasselbe **SoC-Band-Schema** mit denselben **Betriebsmodi** (Eco/Standard/Super). Die
**SoC-Schwellen (50/58/80/90 %) bleiben identisch** (dimensionslos); nur die **Leistungswerte**
werden vom kW-Bereich der Avalon Q auf den Watt-Bereich der Lab-Miner **heruntergerechnet** —
stufenweise über die drei Modi.

Der **deterministische Kern** (`RuleEngineConfig`, identisch im HA-„Rule Lab" `rule_lab.yaml`)
nutzt für die Studie weiterhin die **kW-Überschuss-Logik** (R1, Default `strategy="surplus"`);
die **Hausreserve** ist dabei auf die Produktivwerte vereinheitlicht (R2: `soc_hard` 50 % /
`soc_soft` 58 %), weil 10–20 % nicht über die Nacht reichen. Eine wählbare **SoC-Band-Strategie**
(`strategy="soc_band"`, `r1_soc_band.py`) bildet das Produktiv-Schema zusätzlich nach (ADR 020).
Gegenüberstellung der Werte:

| Parameter | **Realbetrieb** (`mvp_auto`) | Core/Studie (`RuleEngineConfig`) |
|---|---|---|
| Stop-/Standby-SoC | **50 %** (Hausreserve) | `soc_hard` 50 % |
| Eco-Start-SoC | **58 %** | `soc_soft` 58 % (kein-Neustart-Veto) |
| Standard-Start/-Stop | **80 / 75 %** | — |
| Super-Start/-Stop | **90 / 85 %** | — |
| Start-Trigger | **SoC ≥ 58 % UND PV ≥ 6000 W** | Überschuss ≥ 1,5 kW (R1) |
| Throttle/Eco | Modus „Eco" (Std+Super derzeit Testmodus gesperrt) | THROTTLE 0,8–1,5 kW |
| Temp-Drosselung | **112 °C** (→Standard), Lockout 95 °C, Raum 31 °C | `max_temp` 85 °C (R3) |
| Netz-/Akku-Veto | Akku-Abgabe < **−800 W** / 5 min → Super→Eco | `max_grid_import` 500 W netto |
| Takt / Cooldown | **2 min** / **1 h**; PV-Bypass ab 15 min | Block 10 min, min_runtime/pause 3/2 |
| Nacht-Sperre | **22:00–06:00** | — |
| Batterie | **10 kWh** | — |

> **Einordnung:** Lab und Realbetrieb sollen **strukturgleich** sein (gleiche Steuerung, nur
> leistungsskaliert) — keine bewusste Divergenz, sondern ein verkleinertes Abbild. Die
> SoC-Schwellen sind **1:1** übernommen, die Leistungs- und PV-Schwellen sind der **einzige**
> skalierte Anteil. Der **Kern** unterstützt das SoC-Band-Schema inzwischen **additiv** als wählbare
> Strategie (`RuleEngineConfig(strategy="soc_band")`); Default bleibt die Surplus-kW-Logik, daher läuft
> die Studie weiterhin replay-basiert darauf (Frozen-Set S1–S10 unberührt).

**Stufen-Skalierung (Dreisatz — Avalon-Q-Modi als Anteil vom Maximum):**

| Modus | Anteil | Avalon Q | Bitaxe Gamma | NerdQaxe++ |
|---|---|---|---|---|
| Eco | 47,8 % | 800 W | ~8,6 W | ~36 W |
| Standard | 77,7 % | 1300 W | ~14,0 W | ~59 W |
| Super | 100 % | 1674 W | ~18 W | ~76 W |
| *Hashrate (Super)* | — | 90 TH/s | 1,2 TH/s | 4,8 TH/s |

> **TODO (nach Realtest):** Sobald die drei Stufen auf Bitaxe/NerdQaxe programmiert und getestet
> sind, die **real gemessenen Werte je Stufe** eintragen — **Hashrate (TH/s)** und **Spannung (V)**
> sowie die tatsächliche Leistung (W). Die Lab-Maxima 18 W / 76 W sind nur Stock-Referenz; Eco/Standard
> sind daraus per Dreisatz abgeleitet und nach der Messung zu ersetzen.

---

## Datengrundlage: echte HA-Daten statt erfundener Zahlen

Die `EnergyState`-Spezifikationen je Szenario-Datei zeigen die **Regel-Logik**; die
**realen Belegungen mit echten Zahlen** stehen im Abschnitt IST-Zustand. Pipeline
(Details: [`src/sim/real_data_export.md`](../../../../../../src/sim/real_data_export.md)):

1. **Export** — reale Tage als 10-Min-Block-CSV. **Genutzt:** HA History-**API** über VPN (`scripts/ha_history_export.py`, kein scp nötig). Alternativ aus der HA-SQLite-DB (`ha_export_scenario.py`).
2. **Augment** — die drei nicht-historischen Signale deterministisch ergänzen (`src/sim/augment.py`):
   - **Preis** (`energy_price_ct_kwh`) — dokumentiertes **Tarifmodell** (Tageszeit-Bänder).
   - **Forecast** (`pv_forecast_kw`) — **Perfect-Foresight**: Mittel der gemessenen PV der nächsten ~1 h.
   - **Heartbeat** (`miner_heartbeat_age_sec`) — Default 5 s; für S5 als Fault injiziert.
3. **Mine** — je Szenario einen repräsentativen realen Block mit Herkunft auswählen (`src/sim/scenario_miner.py`).

---

## IST-Zustand: Belegung aus Realdaten (Stand 2026-06-03)

**Datenbasis (Detail):** **11 reale Tage 2026-05-24 – 2026-06-03**, via HA
History-API exportiert, je **144/144 Blöcke befüllt** (~60 000 Rohpunkte/Tag),
augmentiert mit Tarif + Perfect-Foresight.

**Datenbasis (Langzeit-Kontext, Tageslog):** **23 Tage 2026-04-20 – 2026-06-03**
aus `/config/mining_log.csv` (per `sensor.mining_log_history` API-lesbar):

- Mining-Stunden/Tag: min 3,2 · **Ø 9,2** · max 12,1 — **0 Tage ohne Mining**
- Energie/Tag: min 5,8 · **Ø 20,2** · max 28,6 kWh (Σ **466 kWh** / 23 Tage)
- Betriebsmodi gesamt: eco 150 h · standard 8 h · super 56 h

> **Einschränkung (Retention & Statistik):** Detaildaten nur **~11 Tage** (10-Min).
> Stündliche Langzeit-Statistik für `pv_power_w` bis ~02.04., **aber `battery_soc_pct`
> und `grid_import_w` haben keine Statistik** → ältere SoC-/Netz-Szenarien nicht
> rekonstruierbar. Für saisonale Abdeckung: Retention + `state_class` (siehe „Was fehlt").

Vorkommen + illustrativer realer Block je Szenario stehen in der
[Szenario-Übersicht](#szenario-übersicht) oben bzw. der jeweiligen Szenario-Datei.

¹ **S8 war eine R2-Fehlauslösung — jetzt gefixt.** Alle 12 ursprünglichen S8-Blöcke
waren 3-Phasen-Schieflage (gleichzeitig Bezug *und* Einspeisung). **Behoben:** R2
(Core + HA) prüft nun **Netto-Bezug** (`import − export`). Folge: diese Blöcke feuern
nicht mehr → echter S8 (genuiner Netto-Bezug) selten → **Injektion**. Override-Ground-Truth
jetzt sauber (Stopp legitim → Übersteuern = Misuse).

² S3: Abend-Hochpreis fällt mit fallender PV-Prognose zusammen → R4 greift vor R1 →
real nicht erreichbar.

### Ökonomie-Monitor (Anzeige, kein Entscheidungs-Gate)

Die Break-Even-Bewertung gegen die Einspeisevergütung (**7,8 ct/kWh**) ist bewusst
**reine Anzeige** — sie steuert die Starts **nicht**. Strategie: **Eigenverbrauch vor
Einspeisung**. IST-Befund (Avalon Q, 18,6 J/TH, Difficulty 138,96 T, BTC ~53 k€):
Mining ≈ **5,5 ct/kWh < 7,8 ct** → „unrentabel", das System mint dennoch. Wertvoll
für die Studie: erklärt *transparent*, warum gemint wird, ohne die Regelentscheidung
zu verzerren. Live-Sensoren: `mining_value_ct_kwh`, `mining_vs_feedin_ct_kwh`,
`mining_recommendation`.

---

## Tageskurve (Überblick)

| Block | Zeit | Szenario | Regel | Entscheidung |
|---|---|---|---|---|
| B1 | 07:00 | S2 Kein Überschuss | R1 | `NOOP_R1_INSUFFICIENT_SURPLUS` |
| B2 | 09:00 | S6 Batterie-Schutz (soft) | R2 | `NOOP_R2_SOC_SOFT_MIN` |
| B3 | 10:30 | S1 Klarer Start | R1 | `START_R1_SURPLUS_OK` |
| B4 | 11:00 | S10 Anti-Flapping | R5 | `NOOP_R5_MIN_RUNTIME_NOT_REACHED` |
| B5 | 12:30 | S8 Wolke → Netzbezug | R2 | `STOP_R2_GRID_IMPORT_EXCEEDED` |
| B6 | 13:30 | S9 Forecast blockiert | R4 | `NOOP_R4_FORECAST_PV_INSUFFICIENT` |
| B7 | 14:30 | S4 Übertemperatur | R3 | `STOP_R3_OVERTEMP` |
| B8 | 15:00 | S5 Kommunikationsausfall | R3 | `STOP_R3_COMM_TIMEOUT` |
| B9 | 16:30 | S7 Batterie-Notstopp (hard) | R2 | `STOP_R2_SOC_HARD_MIN` |
| B10 | 17:30 | S3 Sonne, aber Preis hoch | R1 | `NOOP_R1_PRICE_TOO_HIGH` |

> **Narrativ:** Sonnenaufgang ohne Überschuss → Akku lädt erst nach → klarer Mining-Start → kurzer Wolkenschatten, System bleibt stabil → dicke Wolke zwingt zum Stopp → erholtes PV, aber Front im Anflug → Nachmittagshitze und Comm-Glitch → später Akku-Notstopp → Abend-Preisspitze.

---

## Nutzung in beiden Tracks (Studie ≠ Simulation)

Die 10 Szenarien sind bewusst **unabhängige, kontrollierte Replay-Vektoren**
(Unit-Test-Fixtures): jeder Block isoliert genau eine Regel → **saubere Attribution**
im Verständnis-Score. Der „Mining-Tag" ist eine **didaktische Rahmung**, keine
durchgängige Batteriesimulation.

| Aspekt | **Studie** (WQ1–WQ3) | **Simulation** (SIM-Track) |
|---|---|---|
| Datenquelle | 10 isolierte Vektoren, Replay des Kerns | durchgängige Tageskurve |
| Ziel | saubere Regel-Attribution, Verständnis-Score | Realismus, Verhalten über Zeit |
| Reihenfolge | **fix chronologisch** | physikalisch fortlaufend |
| S4/S5/S7 | reguläre Items | **Fault-/Stress-Injektion** |

### Reihenfolge in der Studie — Entscheidung: fix chronologisch

- **Standardisierung:** [2024a](../2024a_study_design_sampling.md) schreibt eine identische, gescriptete Abfolge vor — Randomisierung würde sie brechen.
- **Didaktisches Scaffolding:** einfach (S1/S2) → kontraintuitiv (S3/S9).
- **Kein Confound:** Reihenfolge über beide Bedingungen konstant → Reihenfolge-/Lerneffekte gleich.
- **Limitation:** Absolutscore nicht vom Lerneffekt trennbar → bewertet wird der *Gruppenunterschied*. Timing im Pilot kalibrieren ([2024b](../2024b_tasks_instruments_metrics.md)).

## THROTTLE — jetzt Kern-Aktion (Eco-Modus)

`THROTTLE` ist seit Roadmap Phase 4 eine **erstklassige Kern-Aktion**: R1 nutzt ein
**Drei-Band** nach Überschuss — `< 0,8 kW` NOOP · `0,8–1,5 kW` **THROTTLE** (Avalon-Q-Eco-Modus)
· `≥ 1,5 kW` START (`THROTTLE_R1_SURPLUS_THROTTLE`). **Kern + Rule Lab** stimmen überein
(live verifiziert). Damit ist ein **11. Szenario (marginaler Überschuss → Eco)** möglich.
**Residual:** Das Prod-HA-Template erzeugt THROTTLE noch mit anderer Semantik
(laufender Miner unter Soft-Limit) → Reconciliation offen (arc42 Kap. 11, ADR 020).

---

## Bezug zur Auswertung

- **Verständnis-Score (0–12):** Progression Basis (S1/S2) → Priorität R2>R1 (S6/S7) → kontraintuitiv (S3/S9) → Safety-Sonderrolle (S4/S5). ⚑ = diskriminierende Items.
- **Override-Angemessenheit:** beobachtet an S4 (Safety, nicht überstimmbar → Misuse-Test) und S9 (Forecast, überstimmbar → Disuse/Misuse-Test).
- **Persona-Adaptivität (Gruppe B):** S3, S6, S9 erfordern je nach Persona unterschiedliche Begründungstiefe.
- **Replay:** Die 10 Blöcke werden als gescriptete Sequenz aus dem deterministischen Kern eingespielt — identisch für alle Probanden.

---

## Was fehlt für die Studie (Stand 2026-06-03)

### Szenarien-/Datenseite

- [x] **7/10 Szenarien** real belegt (S1, S2, S6, S7, S9, S10 + S8 vor R2-Fix).
- [ ] **S3 (Preis-Veto)** real nicht erreichbar → anderes Tarifprofil **oder** als konstruiertes Item kennzeichnen.
- [ ] **S4/S5 (Faults)** + **S8 (echter Netto-Bezug)** brauchen **Injektion** (`state_injector.py`).
- [ ] **Repräsentanten final fixieren + einfrieren** (`scenario_miner --freeze-dir`).
- [x] **Datenbasis ausgebaut** (11 Tage Detail + 23 Tage Tageslog) + **Recording erweitert & dauerhaft an**.

### System-/Konsistenzseite (siehe FINDINGS)

- [x] **R2-Netto-Bezug-Fix** (Core + HA) → S8-Fehlauslösung behoben.
- [x] **THROTTLE** als Eco-Modus im Kern + Lab (Prod-Template-Abgleich offen).
- [x] **R4-Forecast reaktiviert:** HA-nativ via Open-Meteo → `sensor.pv_forecast_kw` wieder verfügbar (stündlich). S9 läuft damit künftig auch live, nicht nur im Replay.
- [ ] **Kein Strompreis-Feed** → R1-Preisprüfung inert (S3 real). *(Hinweis: für die Steuerung durch Break-Even-Anzeige ersetzt.)*
- [x] **Override/Reason aufgezeichnet:** `sensor.`-Spiegel in der 365-Tage-DB (`audit_mirrors.yaml`).
- [ ] **Residuale Engine-Divergenz** (R4/R5 nicht im HA-Template) — bekannte Limitation (arc42 Kap. 11, ADR 020).

> **Saison-Bias (Validität):** Alle 11 Detail-Tage sind Spätfrühling. Häufigkeiten (S9 822×, S2 20×) sommer-spezifisch. **Überbrückt** durch synthetische 4-Jahreszeiten-Profile (`src/sim/synth_seasons.py` — Winter START=0 … Sommer START=14); reale Saisons folgen über Monate (Forward-Record läuft).

### Studiendurchführung (aus 2024a–c)

- [ ] **Erklärtexte** Gruppe A (statisch) vs. B (persona-adaptiv, LLM) je Szenario.
- [ ] **Rubrik (0–12) + Interrater-κ** kalibrieren.
- [ ] **Override-Aufgabe** operationalisieren (S4 Misuse-, S9 Disuse-Test).
- [ ] **Ethikantrag-Status** klären.

---

> **Nächster Schritt:** Zurück zu **[20.2.4 - SD-CONTEXT](../README.md)**
>
> Zurück zur **[Hauptübersicht](../../../../../README.md)**
