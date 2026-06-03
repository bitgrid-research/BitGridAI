# 20.2.4.4 - SD-WQ4 - Szenarien für Simulation und Studie (v1)

Zehn deterministische Szenarien, eingebettet in **einen zusammenhängenden Mining-Tag**.
Jedes Szenario ist ein 10-Minuten-Block mit vollständig spezifiziertem `EnergyState`,
sodass der Entscheidungskern per **Replay** exakt reproduzierbar denselben
`decision_code` erzeugt (vgl. Standardisierung in [2024a](./2024a_study_design_sampling.md)).

## Designprinzipien

1. **Ein Lehrziel pro Szenario** — sauber zuordenbar zum Regelverständnis-Score (0–12, siehe [2024b](./2024b_tasks_instruments_metrics.md)).
2. **Reproduzierbar** — definierter `EnergyState` + Engine-Inputs → deterministischer `decision_code`.
3. **Diskriminierend** — die kontraintuitiven Fälle (S3, S6, S9) trennen statische von persona-adaptiver Erklärung.
4. **Vollständige Abdeckung** — alle Regeln R1–R5 **und** die Prioritätskette R3 > R2 > R4 > R5 > R1.
5. **Zentralkonzept „Steuern statt Einspeisen"** wird mehrfach berührt (S1, S3, S8).

Alle Werte beziehen sich auf die Default-Schwellen der `RuleEngineConfig`:
`surplus_min 1,5 kW · price_max 25 ct · soc_soft 20 % · soc_hard 10 % · max_grid_import 500 W · max_temp 85 °C · comm_timeout 60 s · min_predicted_surplus 2,0 kW · price_spike 30 ct · deadband 2 · min_runtime 3 · min_pause 2`.

---

## Datengrundlage: echte HA-Daten statt erfundener Zahlen

Die unten gezeigten `EnergyState`-Werte sind **provisorische Platzhalter**. Die
finalen Szenarien werden aus **realen Home-Assistant-Messdaten** belegt, damit
die Studie mit realistischen Zahlen arbeitet. Pipeline (Details:
[`src/sim/real_data_export.md`](../../../../../src/sim/real_data_export.md)):

1. **Export** — reale Tage aus der HA-SQLite-DB → 10-Min-Block-CSV (`ha_export_scenario.py`).
2. **Augment** — die drei nicht-historischen Signale deterministisch ergänzen (`src/sim/augment.py`):
   - **Preis** (`energy_price_ct_kwh`) — dokumentiertes **Tarifmodell** (Tageszeit-Bänder: günstiger PV-Mittag ~13 ct, teure Abend-Spitze ~29 ct).
   - **Forecast** (`pv_forecast_kw`) — **Perfect-Foresight**: Mittel der tatsächlich gemessenen PV der nächsten ~1 h.
   - **Heartbeat** (`miner_heartbeat_age_sec`) — Default 5 s; für S5 als Fault injiziert.
3. **Mine** — je Szenario einen repräsentativen realen Block mit Herkunft auswählen (`src/sim/scenario_miner.py`).

**Real gemessen:** PV, Hauslast, Netzbezug/-einspeisung, SoC, Miner-Temp/-Power
(→ S1, S2, S6, S7, S8, S10 direkt aus Realdaten).
**Augmentiert:** Preis (S3), Forecast (S9).
**Injiziert:** Übertemperatur (S4), Comm-Timeout (S5) — treten in normalen Daten nicht auf.

> Jedes finalisierte Szenario erhält eine **Herkunftszeile** (Quelltag + Blockindex),
> sodass real vs. augmentiert vs. injiziert transparent bleibt.

---

## IST-Zustand: Belegung aus Realdaten (Stand 2026-06-03)

**Datenbasis:** 6 reale Tage **2026-05-28 – 2026-06-02**, via HA History-API
exportiert (`scripts/ha_history_export.py`), je **144/144 Blöcke befüllt**
(~60 000 Rohpunkte/Tag), augmentiert mit Tarif + Perfect-Foresight.

> **Wichtige Einschränkung (Retention):** Der HA-Recorder hält nur **~6–10 Tage**
> Detaildaten (10-Min-Auflösung). Ältere/saisonale Detaildaten existieren **nicht**
> (nur stündliche Langzeit-Statistik). Für saisonale Abdeckung muss die
> Recorder-Retention erhöht und über Monate aufgezeichnet werden.

Über die 6 Tage gemined (deterministischer Replay des Kerns), repräsentativer
realer Block je Szenario:

| ID | Szenario | Vorkommen (6 Tage) | Realer Beispielblock | Status |
|---|---|---|---|---|
| **S1** | Klarer Start | 77× | 01.06. 12:50 · Überschuss **+7,82 kW** · SoC 98 % · 13 ct | ✅ real |
| **S2** | Kein Überschuss | 18× | 02.06. 07:00 · **+1,48 kW** (knapp < 1,5) · SoC 22 % | ✅ real |
| **S6** | Batterie-Schutz (soft) | 74× | 02.06. 05:50 · **+2,70 kW** aber **SoC 14 %** | ✅ real |
| **S7** | Batterie-Notstopp (hard) | 14× | 02.06. 04:20 · **SoC 5 %** · Nacht | ✅ real |
| **S8** | Wolke → Netzbezug | 11× | 31.05. 12:30 · **Netzbezug 1057 W** (SoC 99 %) | ✅ real ¹ |
| **S9** | Forecast blockiert | 426× | 01.06. 15:30 · jetzt **+3,59 kW**, Prognose **1,99 kW** | ✅ real |
| **S10** | Anti-Flapping | 244× | 30.05. 12:00 · +7,56 kW, gerade gestartet | ✅ real |
| **S3** | Sonne, aber Preis hoch | **0×** | — tritt mit aktuellem Tarif nicht auf ² | ⚠ konstruieren |
| **S4** | Übertemperatur | **0×** | — Fault, kein Realvorkommen | 🔧 Injektion |
| **S5** | Kommunikationsausfall | **0×** | — Fault, kein Realvorkommen | 🔧 Injektion |

¹ Reale S8-Treffer sind überwiegend **transiente Netzbezugs-Spitzen** (auch bei
voller Batterie/Sonne), nicht der Lehrbuch-Fall „Wolke → Einbruch". Selbst ein
realistischer IST-Befund: echte Messdaten sind verrauschter als das Narrativ.

² Die Abend-Hochpreiszeit (17–21 h, ~29 ct) fällt mit **fallender PV-Prognose**
zusammen → **R4 greift vor R1** (wird zu S9). Mit dem aktuellen Tarifmodell ist S3
daher real nicht erreichbar (siehe „Was fehlt").

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
| B7 | 14:30 | S4 Übertemperatur | R3 | `STOP_R3_OVERTEMP_T90` |
| B8 | 15:00 | S5 Kommunikationsausfall | R3 | `STOP_R3_COMM_TIMEOUT_AGE75` |
| B9 | 16:30 | S7 Batterie-Notstopp (hard) | R2 | `STOP_R2_SOC_HARD_MIN` |
| B10 | 17:30 | S3 Sonne, aber Preis hoch | R1 | `NOOP_R1_PRICE_TOO_HIGH` |

> **Narrativ:** Sonnenaufgang ohne Überschuss → Akku lädt erst nach (Schutz) → klarer Mining-Start → kurzer Wolkenschatten, System bleibt stabil → dicke Wolke zwingt zum Stopp → erholtes PV, aber Front im Anflug → Nachmittagshitze und Comm-Glitch → später Akku-Notstopp → Abend-Preisspitze.

---

## S1 — Klarer Start (R1, Happy Path)

```python
EnergyState(
    block_id="2026-06-15T1030", pv_power_w=4500, house_load_w=1500,
    surplus_kw=3.0, grid_import_w=0, battery_soc_pct=80.0,
    miner_temp_c=45.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=12.0, pv_forecast_kw=4.0, quality="ok",
)
# Engine-Input: last_action="STOP", blocks_since_last_change=5, autonomy="FULL"
```

- **Entscheidung:** `START_R1_SURPLUS_OK`
- **Lehrziel:** Grundprinzip — überschüssige PV wird in die flexible Last **gesteuert**, statt sie einzuspeisen.
- **Verständnisfrage:** „Warum läuft der Miner jetzt an?"
- **Persona:** Energie-Optimierer (Eigenverbrauchsquote), Bitcoin-Nerd (Hashrate aus Sonne).
- **Override-Eignung:** gering (System verhält sich erwartungskonform).

## S2 — Kein Überschuss (R1, NOOP)

```python
EnergyState(
    block_id="2026-06-15T0700", pv_power_w=1700, house_load_w=1300,
    surplus_kw=0.4, grid_import_w=0, battery_soc_pct=30.0,
    miner_temp_c=30.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=18.0, pv_forecast_kw=3.0, quality="ok",
)
# Engine-Input: last_action=None, blocks_since_last_change=0, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R1_INSUFFICIENT_SURPLUS` (0,4 kW < 1,5 kW)
- **Lehrziel:** Ohne ausreichenden Überschuss kein Mining — die Hauslast hat Vorrang.
- **Verständnisfrage:** „Die Sonne ist doch schon da — warum passiert nichts?"

## S3 — Sonne, aber Preis zu hoch (R1, kontraintuitiv) ⚑

```python
EnergyState(
    block_id="2026-06-15T1730", pv_power_w=4000, house_load_w=1500,
    surplus_kw=2.5, grid_import_w=0, battery_soc_pct=70.0,
    miner_temp_c=40.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=28.0, pv_forecast_kw=2.5, quality="ok",
)
# Engine-Input: last_action="STOP", blocks_since_last_change=5, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R1_PRICE_TOO_HIGH` (28 ct > 25 ct; Preis bewusst < 30 ct, damit R4 *nicht* greift)
- **Lehrziel:** Opportunitätskosten — bei hohem Marktpreis lohnt **Einspeisen mehr als Selbstverbrauch**. Profitabilität ist nicht nur „Sonne da/nicht da".
- **Verständnisfrage:** „Die Sonne scheint und der Akku ist voll — warum mint das System trotzdem nicht?"
- **Diskriminierend:** Hier zahlt sich persona-adaptive Erklärung am stärksten aus.

## S4 — Übertemperatur (R3, Safety schlägt alles) ⚑

```python
EnergyState(
    block_id="2026-06-15T1430", pv_power_w=4500, house_load_w=1500,
    surplus_kw=3.0, grid_import_w=0, battery_soc_pct=75.0,
    miner_temp_c=90.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=12.0, pv_forecast_kw=4.0, quality="ok",
)
# Engine-Input: last_action="START", blocks_since_last_change=6, autonomy="FULL"
```

- **Entscheidung:** `STOP_R3_OVERTEMP_T90` — obwohl R1 starten **würde**.
- **Lehrziel:** Sicherheit hat höchste Priorität und ist **nicht überstimmbar** (`allow_unsafe_override = False`).
- **Verständnisfrage:** „Bedingungen sind ideal — warum stoppt das System?"
- **Override-Aufgabe (Kandidat A):** Proband darf Erzwingen versuchen → korrektes Verhalten = akzeptieren. Forcierter Weiterlauf = **Misuse-Tendenz**.

## S5 — Kommunikationsausfall (R3, Comm-Timeout)

```python
EnergyState(
    block_id="2026-06-15T1500", pv_power_w=4200, house_load_w=1500,
    surplus_kw=2.7, grid_import_w=0, battery_soc_pct=72.0,
    miner_temp_c=50.0, miner_heartbeat_age_sec=75.0,
    energy_price_ct_kwh=13.0, pv_forecast_kw=3.5, quality="warn",
    missing_signals=("miner_heartbeat",),
)
# Engine-Input: last_action="START", blocks_since_last_change=2, autonomy="FULL"
```

- **Entscheidung:** `STOP_R3_COMM_TIMEOUT_AGE75` (75 s > 60 s)
- **Lehrziel:** Bei Verbindungsverlust wird sicherheitshalber gestoppt — kein Steuern „blind".
- **Verständnisfrage:** „Was bedeutet es, wenn das System den Miner nicht mehr ‚hört'?"

## S6 — Batterie-Schutz, Soft-Min (R2 vor R1) ⚑

```python
EnergyState(
    block_id="2026-06-15T0900", pv_power_w=3800, house_load_w=1300,
    surplus_kw=2.5, grid_import_w=0, battery_soc_pct=18.0,
    miner_temp_c=30.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=14.0, pv_forecast_kw=3.5, quality="ok",
)
# Engine-Input: last_action=None, blocks_since_last_change=0, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R2_SOC_SOFT_MIN` (18 % ≤ 20 %; kein **neuer** Start, Akku lädt erst nach)
- **Lehrziel:** Autarkie vor Profit — R2 schlägt R1, obwohl Überschuss vorhanden ist.
- **Verständnisfrage:** „Überschuss ist da — warum startet der Miner nicht?"
- **Diskriminierend:** trennt R2-Verständnis vom reinen „Überschuss = Start"-Modell.

## S7 — Batterie-Notstopp, Hard-Min (R2, aktiver Stopp)

```python
EnergyState(
    block_id="2026-06-15T1630", pv_power_w=1200, house_load_w=1400,
    surplus_kw=-0.2, grid_import_w=200, battery_soc_pct=9.0,
    miner_temp_c=55.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=20.0, pv_forecast_kw=1.5, quality="ok",
)
# Engine-Input: last_action="START", blocks_since_last_change=6, autonomy="FULL"
```

- **Entscheidung:** `STOP_R2_SOC_HARD_MIN` (9 % ≤ 10 %; Miner lief auf Akku, Netzbezug noch < 500 W)
- **Lehrziel:** Unterschied Soft-Min (kein Neustart) vs. Hard-Min (**laufenden Miner stoppen**).
- **Verständnisfrage:** „Worin unterscheidet sich dieser Stopp von dem heute Morgen (S6)?"

## S8 — Wolke zwingt zum Stopp (R2, Netzbezug-Limit) ⚑

```python
EnergyState(
    block_id="2026-06-15T1230", pv_power_w=800, house_load_w=1500,
    surplus_kw=-0.7, grid_import_w=700, battery_soc_pct=55.0,
    miner_temp_c=50.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=15.0, pv_forecast_kw=3.0, quality="ok",
)
# Engine-Input: last_action="START", blocks_since_last_change=5, autonomy="FULL"
```

- **Entscheidung:** `STOP_R2_GRID_IMPORT_EXCEEDED` (700 W > 500 W; SoC 55 % → weder soft noch hard)
- **Lehrziel:** **Nie aus dem Netz minen** — verstärkt „Steuern statt Einspeisen" aus Gegenrichtung.
- **Verständnisfrage:** „Der Akku ist halb voll — warum reicht das nicht, um weiterzulaufen?"
- **Autonomie-Variante:** Im `SEMI`-Modus wird dieser R2-STOP zu `NOOP` (nur R3 darf stoppen) → testet Verständnis der Autonomiestufen.

## S9 — Forecast blockiert Start (R4, vorausschauend) ⚑

```python
EnergyState(
    block_id="2026-06-15T1330", pv_power_w=3700, house_load_w=1500,
    surplus_kw=2.2, grid_import_w=0, battery_soc_pct=60.0,
    miner_temp_c=45.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=16.0, pv_forecast_kw=1.2, quality="ok",
)
# Engine-Input: last_action="STOP", blocks_since_last_change=4, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R4_FORECAST_PV_INSUFFICIENT` (Prognose 1,2 kW < 2,0 kW; R5-Deadband inaktiv, daher greift das R4-Veto nach R5)
- **Lehrziel:** Vorausschau — kein Start kurz vor einem PV-Einbruch (vermeidet kurze Laufzeit / Flapping).
- **Verständnisfrage:** „Jetzt ist Überschuss da — warum wartet das System?"
- **Override-Aufgabe (Kandidat B):** „Die Sonne scheint doch!" → Override zu START technisch erlaubt. Begründetes Akzeptieren = Vertrauen; blindes Übersteuern = **Disuse/Misuse**.

## S10 — Anti-Flapping / Deadband (R5, Stabilität)

```python
EnergyState(
    block_id="2026-06-15T1100", pv_power_w=2700, house_load_w=1500,
    surplus_kw=1.2, grid_import_w=0, battery_soc_pct=78.0,
    miner_temp_c=48.0, miner_heartbeat_age_sec=5.0,
    energy_price_ct_kwh=12.0, pv_forecast_kw=3.0, quality="ok",
)
# Engine-Input: last_action="START", blocks_since_last_change=1, autonomy="FULL"
```

- **Entscheidung:** `NOOP_R5_MIN_RUNTIME_NOT_REACHED` (erst 1 Block seit Start < min_runtime 3)
- **Lehrziel:** `NOOP` heißt „**keine Änderung**" — der Miner läuft trotz kurzem Überschuss-Dip (1,2 kW) weiter; R5 verhindert Hektik-Schalten.
- **Verständnisfrage:** „Der Überschuss ist kurz gefallen — warum schaltet das System nicht sofort ab?"

---

## Nutzung in beiden Tracks (Studie ≠ Simulation)

Die 10 Szenarien sind bewusst **unabhängige, kontrollierte Replay-Vektoren**
(Charakter von Unit-Test-Fixtures): jeder Block isoliert genau eine Regel.
Das ist methodisch erwünscht — es erlaubt die **saubere Attribution** im
Regelverständnis-Score. Der „Mining-Tag" ist eine **didaktische Rahmung** für
die Probanden, **keine** durchgängige physikalische Batteriesimulation. Ein
einziger kontinuierlicher SoC-Pfad kann S6 (18 %), S7 (9 %-Crash) und S3
(intaktes Abend-SoC 70 %) nicht physikalisch verbinden — und soll es nicht.

| Aspekt | **Studie** (WQ1–WQ3) | **Simulation** (SIM-Track) |
|---|---|---|
| Datenquelle | 10 isolierte Vektoren, Replay des Kerns | durchgängige Tageskurve (unten) |
| Ziel | saubere Regel-Attribution, Verständnis-Score | Realismus, Verhalten über Zeit |
| Reihenfolge | **fix chronologisch** (s. u.) | physikalisch fortlaufend |
| S4/S5/S7 | reguläre Items | **Fault-/Stress-Injektion** (kein PV/SoC-Folgewert) |

### Reihenfolge in der Studie — Entscheidung: fix chronologisch

- **Begründung Standardisierung:** [2024a](./2024a_study_design_sampling.md) schreibt eine *identische, gescriptete Szenario-Abfolge für alle Probanden* vor. Eine Randomisierung würde diese Standardisierung brechen.
- **Didaktisches Scaffolding:** Die Abfolge steigt bewusst von einfach (S1/S2) zu kontraintuitiv (S3/S9) — entspricht dem natürlichen Lernpfad.
- **Kein Confound für den A/B-Vergleich:** Da die Reihenfolge über *beide* Bedingungen (statisch vs. adaptiv) **konstant** ist, sind etwaige Reihenfolge-/Lerneffekte für beide Gruppen gleich und confounden den Between-Subjects-Vergleich nicht.
- **Limitation (offen dokumentiert):** Der absolute Verständnis-Score ist durch die feste Reihenfolge nicht von einem reinen Lerneffekt trennbar — bewertet wird der *Gruppenunterschied*, nicht der Absolutwert. Timing der Abfolge wird im Pilot (2–3 Durchläufe, s. [2024b](./2024b_tasks_instruments_metrics.md)) kalibriert.

## Kontinuierliche Simulations-Tageskurve (SIM-Track)

Für den Simulations-Track eine *physikalisch fortlaufende* SoC/PV-Kurve (≈5 kWp,
sonniger Tag mit Wolkendurchzug). Daraus entstehen die SoC/PV/Preis-getriebenen
Szenarien **natürlich**; S4/S5/S7 werden als Störereignisse injiziert.

| Zeit | PV [W] | Last [W] | SoC [%] | natürliche Entscheidung | ≈ Szenario |
|---|---|---|---|---|---|
| 06:30 | 600 | 1300 | 22 | `NOOP_R1_INSUFFICIENT_SURPLUS` | — |
| 07:00 | 1700 | 1300 | 23 | `NOOP_R1_INSUFFICIENT_SURPLUS` | **S2** |
| 08:30 | 3200 | 1300 | 19 | `NOOP_R2_SOC_SOFT_MIN` (Akku lädt) | — |
| 09:00 | 3800 | 1300 | 18 | `NOOP_R2_SOC_SOFT_MIN` | **S6** |
| 10:00 | 4300 | 1500 | 65 | (Übergang — SoC erholt sich) | — |
| 10:30 | 4500 | 1500 | 80 | `START_R1_SURPLUS_OK` | **S1** |
| 11:00 | 2700 | 1500 | 82 | `NOOP_R5_MIN_RUNTIME_NOT_REACHED` | **S10** |
| 12:30 | 800 | 1500 | 55 | `STOP_R2_GRID_IMPORT_EXCEEDED` | **S8** |
| 13:30 | 3700 | 1500 | 60 | `NOOP_R4_FORECAST_PV_INSUFFICIENT` | **S9** |
| 16:00 | 3500 | 1500 | 70 | `START_R1_SURPLUS_OK` | — |
| 17:30 | 4000 | 1500 | 70 | `NOOP_R1_PRICE_TOO_HIGH` (Preis 28 ct) | **S3** |
| 19:00 | 400 | 1300 | 40 | `NOOP_R1_INSUFFICIENT_SURPLUS` | — |

> **Caveat:** Die Spalte „natürliche Entscheidung" nennt das *dominante erwartete*
> Ergebnis pro Block. Die genaue Dynamik bei *laufendem* Miner (Netzbezug vs.
> Akku-Entladung, SoC-Verlauf) löst der Simulator auf — die Kurve ist eine
> Skizze zur Veranschaulichung, kein verifizierter Block-für-Block-Replay.

**Injizierte Störereignisse** (nicht aus PV/SoC ableitbar):

- **S4 Übertemperatur** — Lüfterausfall/Hitzestau, z. B. um 14:30 auf den Lauf aus dem 16:00-Slot vorgezogen.
- **S5 Kommunikationsausfall** — Heartbeat-Verlust, unabhängig vom Energiezustand.
- **S7 Hard-Min-Crash** — nur auf einem **separaten, stark bewölkten Tag**, an dem der Miner über Stunden aus dem Akku läuft (Netzbezug < 500 W), bis SoC ≤ 10 %.

## THROTTLE — bewusst außerhalb v1 (mit Befund) ⚠

Kein Szenario erzeugt `THROTTLE`, weil der **deterministische Kern es nicht erzeugt**:
keine Regel R1–R5 gibt `THROTTLE` zurück, das `Decision`-Modell reserviert das
Literal nur, und [`actuation_writer.py`](../../../../src/adapters/actuation_writer.py) behandelt es wie `NOOP`.

**Befund (Divergenz Kern ↔ HA):** Das HA-Template
[`configuration.yaml`](../../../../src/ha/config/configuration.yaml) (Z. 552/554) **erzeugt** sehr wohl
`THROTTLE` — bei laufendem Miner unter Soft-Min bzw. bei verletzter
Profitabilität. Wo der Python-Kern `NOOP` (Soft-Min) bzw.
`NOOP_R1_INSUFFICIENT_SURPLUS` liefert, drosselt das HA-Template aktiv.

→ **Konsequenz:** Solange Kern und HA divergieren, wäre ein THROTTLE-Szenario
*nicht* reproduzierbar replaybar und würde das Studienergebnis verfälschen.
Vor einem möglichen 11. Szenario muss der Kern angeglichen werden (THROTTLE
entweder im Kern implementieren **oder** aus dem HA-Template entfernen). Bis
dahin: außerhalb Scope v1. Diese Inkonsistenz ist ein Architektur-/Determinismus-
Punkt für Codex-/₿itsy-Dev-Review.

---

## Bezug zur Auswertung

- **Verständnis-Score (0–12):** Progression Basis (S1/S2) → Priorität R2>R1 (S6/S7) → kontraintuitiv (S3/S9) → Safety-Sonderrolle (S4/S5). Die mit ⚑ markierten Szenarien sind die diskriminierenden Items.
- **Override-Angemessenheit:** beobachtet an S4 (Safety, nicht überstimmbar → Misuse-Test) und S9 (Forecast, überstimmbar → Disuse/Misuse-Test).
- **Persona-Adaptivität (Gruppe B):** S3, S6, S9 erfordern je nach Persona (Energie-Optimierer / Wärme-Nutzer / Bitcoin-Nerd) unterschiedliche Begründungstiefe.
- **Replay:** Die 10 Blöcke werden als gescriptete Sequenz aus dem deterministischen Kern eingespielt — identisch für alle Probanden (siehe [2024a](./2024a_study_design_sampling.md)).

---

> **Nächster Schritt:** Zurück zu **[20.2.4 - SD-CONTEXT](./README.md)**
>
> Zurück zur **[Hauptübersicht](../../../../README.md)**
