# 38 - Umsetzungs-Roadmap: Ökonomie, Engine-Konsistenz & Studienreife

Reihenfolge, in der die offenen Punkte angegangen werden — mit Begründung,
Abhängigkeiten und Definition-of-Done je Phase. Ziel: ein **valider, konsistenter**
Systemzustand, auf dem die Anwenderstudie (siehe
[`20.2.4 SD-CONTEXT`](../../research/20_research_questions/202_working_questions/2024_study_design_context/README.md))
sauber aufsetzen kann.

## Leitprinzipien

1. **Determinismus zuerst** — der Python-Kern bleibt die einzige Entscheidungsautorität; keine Logik-Duplikate driften lassen.
2. **Echt vor modelliert** — augmentierte Signale (Preis/Forecast) durch reale ersetzen, bevor die Studie darauf baut.
3. **Validität vor Politur** — System-Befunde (R2-Fehlauslösung, Engine-Divergenz) korrigieren, bevor Szenarien eingefroren werden.
4. **Wissenschaftliche Sauberkeit** — Limitationen offen; Hypothesen/Analyseplan vor Datenerhebung (kein HARKing).

## Status

- ✅ **Phase 1 — Ökonomie als ANZEIGE (nicht als Gate):** Mining-Wert-Sensoren live (`sensor.mining_value_ct_kwh`, `mining_vs_feedin_ct_kwh`, `mining_recommendation`) im `economics`-Package; konfigurierbare Effizienz/Reward/Tarif. **R1-Gate bewusst zurückgebaut** (`mining_value` ist nur geloggte Anzeige) → Strategie **Eigenverbrauch vor Einspeisung**: Überschuss wird gemint, auch wenn marginal unrentabel.
- ✅ **Phase 5 (vorgezogen) — S1–S10 in HA:** Szenario-Package `packages/sim_scenarios.yaml` (10 Skripte auf den isolierten `lab_*`-Inputs) + Dashboard-View „Szenarien" (Buttons + Live-Lab-Entscheidung + Erklärung). **7/10 live verifiziert** identisch zum Kern; **S3/S9/S10 fallen durch** (R4/R5/Break-Even nur im Kern) → Engine-Divergenz im Dashboard sichtbar.
- ✅ **Prod-Simulation-Seite repariert:** fehlende Sim-Inputs (`miner_temp_c`, `heartbeat_age_sec`, `miner_power_w`, `battery_power_w`, `miner_relay_sim`) als `packages/sim_inputs.yaml`; Sim-Branches für `miner_max_chip_temp_c` + neuer `sensor.miner_heartbeat_age_sec`; falsche Dashboard-Sensornamen korrigiert, defektes Test-Protokoll getrimmt. Kein „Entität nicht gefunden" mehr.
- ✅ **Phase 2 — R2 Netto-Bezug-Fix:** Core + HA-Template auf `import − export`; behebt die S8-Fehlauslösung (Miner-Stopp bei Mittagssonne). 314 Tests grün, Live verifiziert.
- ✅ **Architektur-Weiche entschieden — Option C (ADR 020):** Kern = studiertes Entscheidungs-Modell, HA steuert live + spiegelt. Residuale Divergenz (R4/R5) als Limitation in arc42 Kap. 11.
- ✅ **Phase 4 — THROTTLE = Eco-Modus (Kern + Lab):** R1-Drei-Band (`<0,8` NOOP · `0,8–1,5` THROTTLE · `≥1,5` START); Lab gespiegelt + live verifiziert. 317 Tests grün. Prod-Template-Abgleich offen.
- ✅ **Phase 3 — Echte Signale:** Forecast HA-nativ via Open-Meteo (`pv_forecast_kw` wieder verfügbar, stündlich, kein externer Prozess); Override/Reason als `sensor.`-Spiegel in der 365-Tage-DB.
- ✅ Datenpipeline (API-Export, Augment, Mine), 11 Tage Detail + 23 Tage Tageslog, Recording erweitert & dauerhaft an.

> **Ökonomischer IST-Befund:** Bei Difficulty 138,96 T und BTC 53.435 € bringt der
> Avalon Q (18,6 J/TH) nur **~5,42 ct/kWh** — **unter** der Einspeisevergütung (7,8 ct).
> Die Anzeige sagt also ehrlich „aktuell unrentabel", das System mint aber dennoch
> (Eigenverbrauch/Wärme/Dataset). Effizienz ist tunbar (`input_number.miner_efficiency_j_th`).

## Getroffene Entscheidungen

| Thema | Entscheidung |
|---|---|
| Break-Even / Mining-Wert | **Nur Anzeige** (Monitoring), **kein Start-Gate** — Eigenverbrauch vor Einspeisung |
| Einspeisevergütung | **7,8 ct/kWh** als Referenz für die Rentabilitäts-Anzeige |
| THROTTLE-Divergenz | Im **Core** als **Eco-Modus** implementieren (Avalon-Q-Modi) |
| R4-Forecast | **forecast.solar reaktivieren** (echter `pv_forecast_kw`) |
| Saison-Bias | **Forward-Record + synthetische** 4-Jahreszeiten-Profile |

## Architektur-Weiche — ENTSCHIEDEN: Option C (ADR 020)

**Kern = deterministisches Entscheidungs-Modell (per Replay studiert); HA steuert
live und spiegelt den Kern eng.** Keine zweite Voll-Engine; Snapshot-Bridge (B)
bleibt späteres Upgrade. Details: [ADR 020](../../architecture/09_design_decisions/091_adr_de.md).

> **Konsequenz für die Roadmap:** Gratuite Divergenz beseitigen — **THROTTLE als
> Eco-Modus im Kern** erstklassig machen (Phase 4), dann stimmt HA überein.
> **Residuale Divergenz** (R4/R5 nicht im HA-Template) als bekannte Limitation
> dokumentieren. Bei jeder Regeländerung **beide Engines** anpassen (zuletzt R2-Netto).

---

## Phasen in Reihenfolge

### Phase 1 — Ökonomie als Anzeige (Monitoring, kein Gate)
*Strategie:* **Eigenverbrauch vor Einspeisung** — Starts entscheiden rein über
Überschuss (R1). Die Rentabilität (Mining-Wert vs. Einspeisevergütung) ist nur
**Anzeige**, damit man sieht „lohnt es sich jetzt?", ohne dass es das Mining bremst.

- [x] **1a** R1-Gate zurückgebaut — Überschuss-getrieben; `mining_value` nur geloggt.
- [x] **1b** Mining-Wert-Sensoren live (`economics.yaml`): `mining_value_ct_kwh`, `mining_vs_feedin_ct_kwh`, `mining_recommendation`; Effizienz/Reward/Tarif konfigurierbar.
- [ ] **1c** Dashboard-Karte „Rentabilität": Effizienz (J/TH) · Mining-Wert · Einspeisevergütung · rentabel jetzt? + Tages-€-Vergleich (Einspeisung vs. Mining).
- [ ] **1d** Rentabilitäts-Anzeige in [`2024d_scenarios/`](../../research/20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/README.md) dokumentieren (ökonomischer IST-Befund ~5,42 ct < 7,8 ct). S3 bleibt die `PRICE_TOO_HIGH`-Szene (feuert ohne Preis-Feed nicht) — **getrennt** von der Rentabilitäts-Anzeige.
- **DoF:** Anzeige zeigt korrekt rentabel/unrentabel; €-Tagesvergleich sichtbar.

### Phase 2 — System-Fix: R2 Netto-Bezug (S8-Fehlauslösung) ✅
*Warum:* Echter Bug — R2 stoppte bei Netto-Einspeisung (3-Phasen-Schieflage, 12/12 reale S8-Blöcke).

- [x] **Core** `r2_autarky.py`: Netto-Bezug (`grid_import_w − grid_export_w`) + Test `test_net_export_does_not_trigger_grid_stop`.
- [x] **HA-Template** `r2_grid_import_ok`: `import − export` → Live-System stoppt nicht mehr falsch (verifiziert `on`).
- [x] FINDINGS geschlossen.
- [ ] **Folge für die Studie:** die 12 realen S8-Blöcke waren Schieflage → feuern nun nicht mehr. **S8 braucht jetzt einen echten Netto-Bezug-Block (Wolke) — vermutlich Injektion** (wie S4/S5). Override-Ground-Truth ist nun sauber (S8-Stopp legitim → Override unangemessen).
- **DoF:** ✅ Test + Live-Verifikation; offen nur die S8-Szenario-Neubelegung.

### Phase 3 — Echte Signale statt Augmentierung ✅
*Warum hier:* Entfernt Validitätsbedrohungen für S9 (Forecast) und das Erklär-Material.

- [x] **3a** Forecast HA-nativ via **Open-Meteo** (`packages/forecast.yaml`: command_line-Sensor + Publish-Automation → `bitgrid/forecast/pv_kw`). `sensor.pv_forecast_kw` wieder verfügbar (live `0,54 kW`), stündlich, kein externer Prozess (ADR 020), Standort als Helper (raus aus Git).
- [x] **3b** Override + Decision-Reason als `sensor.`-Spiegel (`packages/audit_mirrors.yaml`) → in der 365-Tage-DB.
- [x] **3c** `pv_forecast_kw` + Decision/Reason/Override bereits im Recording-Snapshot.
- *Hinweis:* Dynamischer **Strompreis-Feed** durch die Break-Even-Anzeige **entbehrlich**.
- **DoF:** ✅ `pv_forecast_kw` verfügbar; Override/Reason historisch abfragbar.

### Phase 4 — THROTTLE = Eco-Modus im Core ✅ (Kern + Lab)
*Warum hier:* Vereinheitlicht Core ↔ HA gemäß ADR 020.

- [x] **Design:** `THROTTLE` = Avalon-Q-Eco-Modus, Auslöser = **marginaler Überschuss** (Drei-Band-R1: `< 0,8` NOOP · `0,8–1,5` THROTTLE · `≥ 1,5` START). Deterministisch, kein Running-State nötig.
- [x] **Kern:** `r1_profitability.py` Drei-Band + `surplus_throttle_min_kw` in `RuleEngineConfig`; 3 Tests; 317 grün.
- [x] **Rule Lab gespiegelt:** `lab_r1_result` Drei-Band + Eco-Erklärung; live verifiziert (1,0 kW → `THROTTLE_R1_SURPLUS_THROTTLE`).
- [ ] **Prod-Template-Abgleich (offen):** `bg_decision_action` erzeugt THROTTLE noch mit *anderer* Semantik (laufender Miner unter Soft-Limit) statt marginalem Überschuss → bewusste Live-Decision-Änderung, separat. Bis dahin residual (Kap. 11).
- **DoF:** ✅ Kern + Lab deckungsgleich; Prod-Template-Reconciliation als Folgeschritt.

### Phase 5 — Szenarien in HA + Divergenz-Test ✅
*Warum hier:* Nach Break-Even + THROTTLE spiegelt die HA-Darstellung die **finale** Logik;
liefert zugleich den Konsistenz-Check HA ↔ Kern.

- [x] **S1–S10 in HA** (`packages/sim_scenarios.yaml`, auf den isolierten `lab_*`-Inputs) + Dashboard-View „Szenarien" (Buttons + Live-Lab-Entscheidung + Erklärung).
- [x] **Divergenz-Test live:** 7/10 identisch zum Kern; S3/S9/S10 fallen durch (R4/R5/Break-Even nur im Kern) → Divergenz sichtbar.
- [x] **Prod-Simulation-Seite repariert** (`sim_inputs.yaml` + Sim-Branches Temp/Heartbeat + Dashboard-Refs) — keine „Entität nicht gefunden" mehr.
- **DoF:** ✅ S1–S10 in HA auslösbar; Dashboard intakt; Lab = Kern (7/10), Rest dokumentiert.

### Phase 6 — Saison gegen den Bias
*Warum hier:* Forward-Record läuft bereits; Synthetik blockiert frühere Phasen nicht.

- [ ] Synthetische 4-Jahreszeiten-Profile (PV/Last/SoC) im SIM-Track, klar markiert.
- [ ] Forward-Record-Monitoring (Recorder 365 d, Snapshot aktiv).
- **DoF:** je Jahreszeit ein repräsentatives Profil; Saison-Bias in `2024d` adressiert.

### Phase 7 — Studienreife (Forschungsschicht)
*Warum zuletzt:* Setzt korrektes System + reale Signale + finale Szenarien voraus.
**Scope:** Die **10 Szenarien** (S1–S10) sind das Studien-Set — kein 11. (THROTTLE) nötig.

**Bereits gebaut (vorhandene Infrastruktur):**
- ✅ **A/B-Erklärungsmotor** `ExplainAgent`: Gruppe A = statische Bausteine (`text_blocks.yaml`), Gruppe B = LLM persona-adaptiv (3 Personas energie/waerme/tech) via `OLLAMA_HOST`.
- ✅ **Statistik-Auswertung** `study_analysis.py` (Mann-Whitney-U, Effektgröße r, N) + Probanden-Schema (`participants.csv`) + Research-Export (Parquet).

**Noch offen:**
- [x] **Freeze-Gerüst gebaut:** `src/sim/study_freeze.py` + `study_scenarios.py` → `src/sim/study_set/S<n>.json` (State + Kern-Entscheidung + Gruppe-A-Text + Gruppe-B-Slots je Persona). **10/10 verifiziert** (Kern == erwarteter Code), Tests grün.
- [ ] **Gruppe B anbinden:** `OLLAMA_HOST` auf den **externen Ollama-Rechner** setzen (Nutzer) → `python -m src.sim.study_freeze` füllt die Persona-Slots **und friert sie ein** (ausfallsicher + reproduzierbar). **Ohne das kein A/B-Kontrast.**
- [ ] **LLM-Faithfulness-Check** (unabhängig vom Nutzer) — sonst Confound Stil↔Korrektheit. **Zentraler Validitäts-Hebel.**
- [ ] **Text-Bausteine ergänzen** (THROTTLE neu) für volle Code-Abdeckung Gruppe A.
- [ ] **Rubrik (0–12) + Interrater-κ** im Pilot kalibrieren; **Override-Ground-Truth** je Szenario (inkl. korrigiertem S8).
- [ ] **Erkenntnisziele + Hypothesen + Pre-Registration**; **Ethikantrag**.
- **DoF:** Gruppe B live (externes Ollama); eingefrorenes 10er-Set; faithfulnessgeprüfte Erklärungen; vorregistrierte Hypothesen; reliable Rubrik.

### Phase 8 — Produktisierung (Ausblick: von der Forschung zum Unternehmen)

*Vision:* Aus der Studie Wissen ableiten und BitGridAI später zu einem Produkt
machen. Der verkaufbare Kern ist **deterministische, auditierbare Steuerung +
erklärbare KI** — der Gegenentwurf zur ML-Blackbox, attraktiv für vertrauens-/
regulierungssensible B2B-Kunden (Energiegenossenschaften, Gewerbe mit flexiblen Lasten).

**Schon template-förmig vorhanden (Wiederverwendung einplanen):**

| Baustein | Heute | Produkt-Template |
|---|---|---|
| **Erklär-Bausteine** `text_blocks.yaml` | decision_code → Text (DE) | White-Label-Erklärpakete je Kunde / Sprache |
| **Persona-Prompts** `_PERSONA_INSTRUCTIONS` | 3 Personas (energie/waerme/tech) | Zielgruppen-Templates, erweiterbar je Segment |
| **Szenario-Bibliothek** S1–S10 | Studien-Stimuli | **Commissioning-Test:** „verhält sich diese Anlage korrekt?" je Neuinstallation |
| **Regel-/Config** `RuleEngineConfig` + `.env.example` | ein Standort | **Site-Profile** (Multi-Tenant): je Anlage ein Config-Profil |
| **HA-Packages** `economics/forecast/audit_mirrors/…` | modulare YAMLs | **Deployment-Module** für neue Standorte |
| **KPI + Auswertung** `study_analysis.py`, KPI-Sensoren | Studie | **Reporting/Audit-Feature** (die Auditierbarkeits-USP) |

**Jetzt schon template-mäßig einplanbar (kostet wenig, zahlt später):**

- [ ] **Site-Profil-Template:** Standort/kWp/Miner-Specs/Schwellen/Persona als *ein* parametrierbares Profil (lat/lon/kWp sind bereits Helper) → Multi-Tenant-Readiness.
- [ ] **Last-Typ entkoppeln:** „Miner" ist nur ein Beispiel einer flexiblen Last → Template für Last-Typen (Miner/Wärme/EV/Wärmepumpe). Die `waerme`-Persona deutet den breiteren Markt schon an.
- [ ] **Erklärpaket-Template:** `text_blocks` + Persona + Sprache als austauschbares „Pack" pro Kunde.
- [ ] **Onboarding-Replay:** das 10-Szenarien-Set als automatisierter Abnahme-/Selbsttest jeder Installation.
- [ ] **Auditierbarer Export:** DecisionEvents + KPI als kundenvorzeigbares Report-Artefakt.

> **Wichtig:** Phase 8 ist **Ausblick**, kein aktiver Arbeitsblock — aber die obigen
> Punkte beeinflussen schon jetzt Design-Entscheidungen (z. B. Helper statt Hardcode,
> modulare Packages), damit die spätere Produktisierung kein Rewrite wird.

---

## Abhängigkeiten (Kurzform)

```
Phase 1 ✅ Ökonomie-Anzeige (Break-Even = Monitor, kein Gate)
Phase 2 ✅ R2 Netto-Fix          ─▶ S8-Override-Ground-Truth sauber (7)
Phase 3 ✅ Forecast + Audit      ─▶ S9 real, Override historisch (7)
ADR 020 ✅ ─▶ Phase 4 ✅ THROTTLE ─▶ Phase 5 ✅ HA-Szenarien + Divergenz-Test
Phase 6 ⏳ Saisons (forward + synthetisch)
Phase 7 ⏳ Studienreife: externes Ollama (Gruppe B) + Set einfrieren + Faithfulness + Rubrik
Phase 8 🔭 Produktisierung (Ausblick)
```

## Risiken / kritische Punkte

- **Engine-Divergenz** ist systemisch — solange zwei Engines existieren, drohen weitere Drifts. Architektur-Weiche nicht vertagen.
- **S8-Override-Coding** kippt, wenn R2-Fix (Phase 2) nicht vor der Studie steht.
- **Faithfulness** der LLM-Erklärung ist die zentrale unkontrollierte Variable — ohne unabhängigen Check ist der A/B-Vergleich konfundiert.
- **Gruppe B hängt am externen Ollama-Rechner** (`OLLAMA_HOST`) — Erreichbarkeit/Latenz/Modell-Konsistenz sicherstellen; bei Ausfall fällt `ExplainAgent` auf Template zurück → A/B-Kontrast verschwindet. Für die Studie: Erklärungen **vorab generieren + einfrieren** (nicht live je Proband), das eliminiert Ausfall- *und* Determinismus-Risiko.
- **N = 20** → nur große Effekte; Studie primär hypothesen-generierend, Triangulation > p-Wert.

## Bezug zur Studie

Die Phasen 2–5 stellen sicher, dass die Probanden das **echte, konsistente**
Systemverhalten sehen (kein Engine-Confound, keine Fehlauslösung, reale Signale).
Phase 7 macht daraus ein **vorregistriertes, faithfulnessgeprüftes** Design. Erst
dann ist „Verbessert persona-adaptive LLM-Erklärung Verständnis **und** angemessene
Verlässlichkeit?" sauber beantwortbar.
