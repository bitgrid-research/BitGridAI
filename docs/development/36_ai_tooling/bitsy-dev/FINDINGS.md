# FINDINGS.md – Schwachstellen & Analysebefunde

> Autonome Hintergrundanalyse von ₿itsy-Dev.
> Neue Befunde oben eintragen — älteste unten.

---

## Format

```
### [DATUM] [BEREICH] Kurztitel
**Datei:** `pfad/zur/datei.md` (Zeile X)
**Problem:** Was genau stimmt nicht?
**Schwere:** Kritisch / Mittel / Niedrig
**Empfehlung:** Was sollte getan werden?
**Status:** Offen / In Bearbeitung / Erledigt
```

---

<!-- Befunde hier eintragen -->

### [2026-06-03] [CORE] R2 Netzbezug-Veto bei 3-Phasen-Schieflage (Fehlauslösung)
**Datei:** `src/core/rules/r2_autarky.py` (max_grid_import_w) + Quelle `sensor.sma_storage_metering_power_absorbed`
**Problem:** R2 stoppt den Miner, obwohl das Haus **netto stark einspeist**. In allen
12 realen S8-Blöcken (24.–31.05.) lief gleichzeitig Bezug **und** Einspeisung
(z. B. 31.05. 13:20: PV 7439 W, Bezug 1057 W, **Einspeisung 4981 W**, SoC 99 %).
`metering_power_absorbed` zählt phasenweisen Bezug → bei 3-Phasen-Schieflage >500 W
trotz Netto-Einspeisung. R2 stoppt das Mining damit **mitten in der Mittagssonne**.
**Schwere:** Mittel–Kritisch (unnötige Mining-Ausfälle bei maximalem Überschuss)
**Empfehlung:** R2-Netzkriterium auf **Netto-Bezug** umstellen (`absorbed - supplied`,
bzw. `grid_import_w - grid_export_w`) statt rohem `metering_power_absorbed`.
**Status:** Erledigt — Core (`r2_autarky.py`: Netto-Bezug + Test) und HA-Template
(`r2_grid_import_ok`: import − export) gefixt; reale S8-Blöcke lösen R2 nicht mehr
fälschlich aus (Claude Code, 2026-06-03)

### [2026-06-03] [ADAPTER] R4-Forecast inaktiv in Produktion
**Datei:** `sensor.pv_forecast_kw` (forecast.solar) → `src/core/rules/r4_forecast.py`
**Problem:** `sensor.pv_forecast_kw` ist live **`unavailable`** → R4 erhält keinen
Forecast → legt **nie** ein Veto ein. S9 (Forecast-Block) tritt real nie auf; es
existiert nur im Replay über den Perfect-Foresight-Proxy. forecast.solar-Integration
offline/fehlkonfiguriert.
**Schwere:** Mittel
**Empfehlung:** forecast.solar-Integration prüfen (Lat/Lon/kWp aus `.env`), Sensor
wieder verfügbar machen; dann historisch aufzeichnen (für reale S9-Belege).
**Status:** Erledigt — HA-nativ via Open-Meteo (`packages/forecast.yaml`: command_line-Sensor
+ Publish-Automation → `bitgrid/forecast/pv_kw`), kein externer Adapter-Prozess (ADR 020).
`sensor.pv_forecast_kw` wieder verfügbar (live verifiziert); aktualisiert stündlich,
Standort als Helper (raus aus Git) (Claude Code, 2026-06-03)

### [2026-06-03] [ADAPTER] Kein Strompreis-Feed (R1-Preisprüfung inert)
**Datei:** R1 `price_max_ct_kwh` — keine `energy_price`-Entity in HA
**Problem:** Es existiert kein Strompreis-Sensor (nur `sensor.btc_eur_price`). R1
erhält `energy_price = None` → Preisprüfung nie aktiv. S1/S3 ruhen rein auf dem
modellierten Tarif; **S3 ist real unmöglich**.
**Schwere:** Mittel
**Empfehlung:** aWATTar-Preissensor anlegen (`.env`: `PRICE_SOURCE=awattar`, kein Key)
→ R1-Preislogik real + aufzeichenbar.
**Status:** Offen

### [2026-06-03] [DATA] Override- & Entscheidungs-Reason nicht aufgezeichnet
**Datei:** `src/ha/config/configuration.yaml` (recorder.exclude.domains: input_*)
**Problem:** Override-State und Decision-Reason/-Explanation liegen in `input_*`-Entities,
die der Recorder ausschließt → **keine Historie** für Override-Angemessenheit (Studien-AV)
oder Erklärungstexte. `sensor.bg_decision_code` selbst wird aufgezeichnet.
**Schwere:** Mittel
**Empfehlung:** Teilweise adressiert — Recording-Snapshot (`recording.yaml`) um
`decision`/`reason`/`override` erweitert (forward-looking JSONL). Für die Haupt-DB
ggf. `sensor.`-Spiegel der Override-/Reason-Entities anlegen.
**Status:** Erledigt — `sensor.`-Spiegel (`packages/audit_mirrors.yaml`:
`override_active_log`, `override_action_log`, `decision_reason_log`,
`decision_explanation_log`) landen in der 365-Tage-DB; zusätzlich im Recording-Snapshot.
Override-Angemessenheit damit historisch auswertbar (Claude Code, 2026-06-03)

### [2026-06-03] [SECURITY] Reale lokale IP / Geräte-Identifier in Git
**Datei:** mehrere (siehe unten)
**Problem:** Der Heizstab-Entity-Name (AC ELWA 2) enthielt die lokale Geräte-IP
und war in mehreren Dateien eingecheckt. Verstößt gegen die Projektregel
„echte IPs/Netzwerktopologie nie in Git". Zusätzlich in `2023b_sim.md`:
SMA-Seriennummern und Shelly-Geräte-IDs (MAC-artig). Ebenso die SMA-Seriennummern
in den Kern-Entity-IDs (`sensor.sn_<serial>_*`) quer durch die HA-Config.
**Schwere:** Mittel
**Empfehlung:**
- Python-Tooling: erledigt — Entity über `BITGRID_HEIZSTAB_ENTITY` (.env) konfigurierbar.
- `2023b_sim.md`: IP, SMA-Seriennummern und Shelly-Geräte-IDs maskiert.
- HA-Config: IP-Präfix aus der Heizstab-Entity entfernt (→ `ac_elwa_2_*`) in
  `configuration.yaml` + `bitgrid-dashboard.yaml`.
- HA-Config: SMA-Serial-Präfixe umbenannt (`sn_<serial>_*` → `sma_tripower_*` /
  `sma_storage_*`) in `configuration.yaml`, `bitcoin.yaml`, `sma_watchdog.yaml`.
**Live-Migration ausgeführt:** 13 HA-Entities via `scripts/ha_rename_entities.py`
umbenannt (6 referenzierte + 7 Heizstab), Config deployt + grazil neugestartet,
verifiziert (`sensor.pv_power_w` liest `sma_tripower_pv_power`). ~137 weitere
SMA-Telemetrie-Sensoren bewusst belassen (nicht in Git, nicht referenziert; Rename
würde Energy-Dashboard/Statistik riskieren). Details: `docs/development/30_setup/ha_entity_rename.md`.
**Status:** Erledigt — IP/Serials aus allen Git-Dateien entfernt; referenzierte Live-Entities umbenannt + deployt + verifiziert (Claude Code, 2026-06-03)

### [2026-06-03] [CORE] THROTTLE: Divergenz zwischen Kern und HA-Template
**Datei:** `src/ha/config/configuration.yaml` (Z. 552, 554) vs. `src/core/rules/*` + `src/core/rule_engine.py`
**Problem:** Der deterministische Kern erzeugt **nie** `THROTTLE` — keine Regel R1–R5
gibt es zurück, `actuation_writer.py` behandelt es wie `NOOP`. Das HA-Template
**erzeugt** `THROTTLE` jedoch (bei laufendem Miner unter Soft-Min bzw. verletzter
Profitabilität). Wo der Kern `NOOP`/`NOOP_R1_INSUFFICIENT_SURPLUS` liefert, drosselt
HA aktiv. Damit weicht das real ausgespielte Verhalten vom replaybaren Kern ab —
ein Determinismus-/Reproduzierbarkeitsproblem (betrifft auch die Studie, die laut
2024a den Kern repliziert).
**Schwere:** Mittel
**Empfehlung:** Kern und HA angleichen — entweder `THROTTLE` als echte Regel-Aktion
im Kern implementieren **oder** aus dem HA-Template entfernen.
**Status:** Großteils erledigt — THROTTLE ist im **Kern** erstklassig (R1-Drei-Band:
marginaler Überschuss → Eco-Modus, `THROTTLE_R1_SURPLUS_THROTTLE`, 3 Tests) und im
**Rule Lab** gespiegelt (live verifiziert). **Offen:** Prod-Template `bg_decision_action`
erzeugt THROTTLE noch mit anderer Semantik (laufender Miner unter Soft-Limit) →
Reconciliation als separate Live-Änderung; residual in arc42 Kap. 11 (Claude Code, 2026-06-03)
