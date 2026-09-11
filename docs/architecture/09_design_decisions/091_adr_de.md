# 09.1 - Architektur-Entscheidungen (Kurzfassung)

Die DNA von BitGridAI.

Dieses Dokument dient als zentrale Ankerstelle für alle **Architecture Decision Records (ADRs)**. ADRs sind strukturierte Dokumente, die wichtige, strukturprägende Entscheidungen transparent, nachvollziehbar und mit ihrer ursprünglichen Begründung festhalten.

Die hier gesammelten Entscheidungen legen die Kernprinzipien von BitGridAI fest: **Lokalität, Determinismus, Erklärbarkeit** und **Nachhaltigkeit**.

<img src="../../media/architecture/09_design_decisions/bithamster_09.png" alt="Hamster tech" width="1000" />

&nbsp;

## ADR-Übersicht (Auszug)

Diese Tabelle fasst die wichtigsten, das System prägenden strategischen Entscheidungen zusammen:

| ADR | Entscheidung | Begründung | Querschnittliche Konzepte |
| :--- | :--- | :--- | :--- |
| **001 Local-First** | Das gesamte System läuft on-prem im lokalen Netzwerk. **Keine Cloud-Abhängigkeit.** | Maximaler **Datenschutz**, Autonomie bei Internetausfall (**Resilienz**). | Deployment, Privacy-by-Default |
| **002 MQTT-Bus** | MQTT wird als zentraler Event-/Command-Bus für State/Cmd/Events verwendet. | Erzeugt lose Kopplung (Hexagonal), ist leichtgewichtig und Industriestandard (IoT). | Whitebox, Logging & Tracing |
| **003 SQLite + Parquet**| Nutzung von SQLite für Laufzeit-Daten (Hot Data) und **Parquet** für Langzeit-Logs/Replay (Cold Data). | Portabel, wartungsarm (SQLite), **Auditierbar** und **effizient** für analytische Abfragen. | Persistenz, Testbarkeit |
| **004 Explainability-UI**| Die UI muss nicht nur den State, sondern auch die **Regel** (`R1-R5`), den **Trigger** und die **Timeline** zeigen. | Baut **Vertrauen** auf, ermöglicht Auditierung durch den Nutzer. | UI, Explainability |
| **005 Nachhaltigkeit** | Surplus und Preis werden als primäre Steuergrößen (R1, R4) etabliert. | Effizienz, Autarkie, Forschung. | Anforderungen, Regeln R1/R4 |
| **006 10-Min-BlockScheduler** | Die Entscheidungen der Regel-Engine werden an den festen Takt `block=floor(epoch/600)` gebunden. | **Stabilität**, Anti-Flapping (R5), Vereinfacht **Audit** und **Replay**. | Laufzeit, Testbarkeit |
| **007 Deterministische R1–R5** | Der Kern der Regel-Engine verzichtet auf Black-Box-ML-Modelle. | Garantiert **Testbarkeit** und **Erklärbarkeit** (R1–R5 sind Code, keine Blackbox). | Regeln, Testbarkeit |
| **008 EnergyState SSoT** | Der `EnergyState` ist die Single Source of Truth mit einem Schreiber (Core) und vielen Lesern. | Gewährleistet Konsistenz und vermeidet Race-Conditions. | Domain Models, Whitebox |
| **009 Deadband/Hysterese** | R5 erzwingt ein Haltefenster (D Blöcke) nach jedem Schaltvorgang. | Reduziert Flapping und schont die angeschlossene Hardware. | Regeln R5, Fehlerbehandlung |
| **010 Manual Override** | Ein manueller Eingriff erhält eine **Block-TTL** und wird als `manual_override` im Log gespeichert. | Garantiert **Nutzerkontrolle** ohne Policy-Drift. | Laufzeit, UI |
| **011 Lokale Forecasts** | R4 nutzt nur lokale Quellen, keine externen Cloud-APIs. | Reduzierte Abhängigkeit, erhöhte Ausfallsicherheit. | Regeln R4, Deployment |
| **012 Append-only + YAML-Version** | Logs und Configs werden mit Version/Hash gespeichert. | Garantiert **Reproducibility** und Auditierbarkeit. | Persistenz, Logging |
| **013 Lizenz AGPLv3** | Das Projekt wird unter der Affero General Public License Version 3 veröffentlicht. | Stellt Offenheit und die Verfügbarkeit des Codes für Forschung sicher. | Legal, Querschnitt |
| **014 Privacy by Default** | Keine Telemetrie, minimale Ports, lokale Datenhaltung. | Erfüllung der DSGVO-Prinzipien, Aufbau von Vertrauen. | Deployment, Privacy |
| **015 Safety First** | Kritische Regeln (R3/R2) erzwingen immer den Zustand **Stop → Safe** und brechen alle Overrides. | Absoluter Schutz der Hardware und des Hauses. | Regeln R2/R3, Fehlerbehandlung |
| **016 MQTT/REST Contract** | Topics/Endpoints sind im Vorfeld klar definiert und versioniert. | Stellt Interoperabilität und Testbarkeit sicher. | Whitebox, Integration |
| **017 KPIs als Ziele** | Die Systemwirkung wird über lokal gemessene KPIs (Grid Import ↓, Flapping Rate ↓) evaluiert. | **Evidenz** der Wirksamkeit statt Behauptung. | Testbarkeit, UI |
| **018 Energy-Path-Policies** | Die Opportunitätskosten (Export/Heat/Hodl) werden transparent geloggt. | Transparenz über die ökonomische Entscheidungsgrundlage. | Regeln, Logging |
| **019 PoW Telemetrie & Hash-Proof** | Pflichtwerte/Proben (Hash-Proof) werden vom Miner erfasst. | Sicherheit, Compliance und Forschung an der Effizienz. | Domain Models, Logging |
| **020 Engine-Strategie** | Der Python-Kern ist das **deterministische Entscheidungs-Modell** (per Replay studiert); **HA steuert live** und spiegelt den Kern eng. Keine zweite Voll-Engine pflegen. | Studie ist replay-basiert → Kern-Korrektheit zählt, nicht Live-Steuerung. Ein Live-Kern-Service würde die reale Anlage ohne XAI-Nutzen riskieren. | Whitebox, Determinismus, Studien-Validität |
| **021 Determinismus-Invariante erzwungen** | Die Kern-Invarianten (kein ML, kein Zufall, keine Importe aus oberen/seitlichen Layern in `src/core`) werden durch einen ausführbaren Architektur-Test (`tests/core/test_architecture.py`) in `make check` mechanisch geprüft. | Macht den wissenschaftlichen Kernanspruch (Determinismus, ADR 007) zu einem **fallierbaren CI-Gate** statt einer Prosa-Konvention. | Testbarkeit, Determinismus, Reproducibility |
| **022 OverrideStore-Port** | Die SQLite-Persistenz des OverrideHandler liegt hinter einem Port (`OverrideStore`, Protocol im Kern); die Implementierung (`SqliteOverrideStore`) lebt in `data/`. | Hält Persistenz/I-O aus dem deterministischen Kern (Hexagonal, ADR 002); `core/` importiert kein `sqlite3` mehr. | Whitebox, Hexagonal, Determinismus |
| **023 command_id als Surrogat-ID** | `Decision.command_id` ist Surrogat-/Idempotenz-ID (EventStore-PK + Aktor-Dedup), nicht Teil der Entscheidung; Vergabe an der Boundary (Runner), nicht im Kern. | Präzisiert den Determinismus-Scope: Semantik ist deterministisch, die ID ausgenommen; `uuid` verlässt den Kern. | Determinismus, Reproducibility, Replay |
| **024 Einmaliger externer Backfill (Hashrate)** | Für die Hashrate-Vorgeschichte vor dem lokal indizierten Zeitraum der self-hosted mempool.space-Instanz wird EINMALIG, manuell, blockchain.info als Fremdquelle gezogen (`scripts/backfill_hashrate_blockchain_info.py`) und als statische Seed-Datei committet. Der reguläre Betrieb (`src/data/btc_hashrate.py`) greift nie live auf blockchain.info zu. | Bewusste, eng begrenzte Ausnahme von ADR-001/011 (Local-First, keine externen Cloud-APIs): die lokale Alternative (mempool-Node auf `INDEXING_BLOCKS_AMOUNT`=-1 umkonfigurieren + reindizieren) ist unverhältnismäßig aufwendig für eine Kontext-Visualisierung. | Local-First (Ausnahme), Transparenz, Reproduzierbarkeit |
| **025 Live-Schaltschwellen: echte Hysterese + akku-reaktiver Notabstieg** | `mvp_auto.yaml` bekommt eigene Auf-/Abwärtsschwellen je Modus (statt geteilter Werte), der pauschale zeitbasierte Nachmittags-Cap ("P0a") entfällt zugunsten eines generalisierten akku-reaktiven Downgrades (R8), und die Stop-Regel wird gegen SoC-Sensor-Ausreißer debounced. Regeln umbenannt R1-R8. | Analyse (`scripts/analyze_mode_thresholds.py` gegen `data/bitgrid.db`, Mai-Aug 2026) zeigt: Super-Austritte waren zu ~94% SoC zeitpunkt- statt SoC-getrieben, der Cap verschenkte ≈3.209 TH-h Mining-Potenzial gegenüber ≈13-56 TH-h durch die separate SoC-Schwelle. | Regeln R1/R2/R5, Anti-Flapping, Autarkie vor Profitabilität (Winter-Stop unverändert konservativ) |

---

## ADR 020 — Engine-Strategie (Detail)

**Kontext.** Es existieren faktisch **zwei** Entscheidungs-Implementierungen: der
Python-Kern (`src/core/`, R1–R5, deterministisch, replay-fähig) und eine
**HA-Template-Nachbildung** (`configuration.yaml`: `bg_decision_*`, `r2_grid_import_ok`,
…). Der `ProductionRunner` (Kern live) ist gebaut, läuft aber nicht (`bg_runner_*`
unavailable) — gesteuert wird **live durch die HA-Templates**.

**Geprüfte Optionen.**
- **A — Voller Runner 24/7:** eigene Telemetrie-Topics, HA nur Aktuator. Hoher Aufwand + Risiko an der Live-Anlage.
- **B — Snapshot-Bridge:** HA-Snapshot (`bitgrid/rec/snapshot`) → kleiner Kern-Service → Entscheidung zurück → HA aktuiert; Template als Fallback. Elegant, mittleres Risiko.
- **C — Kern = Modell, HA steuert (gewählt):** Der Kern ist das *studierte* Artefakt; HA steuert live und spiegelt ihn eng. Gratuite Divergenz wird beseitigt, Rest dokumentiert.

**Entscheidung: Option C.** Begründung: Die Anwenderstudie läuft **per Replay des
Kerns** (offline, deterministisch) — entscheidend ist die **Korrektheit/Erklärbarkeit
des Kerns**, nicht dass er die reale Anlage steuert. Einen Live-Kern-Service
einzuführen, fügt der echten Energieanlage Ausfallrisiko hinzu, **ohne** den
XAI-Beitrag der Arbeit zu stärken.

**Konsequenzen.**
- Kern bleibt Single Source of Truth für **Entscheidungslogik** (Studie, Analyse, Replay).
- HA-Templates spiegeln den Kern **so eng wie möglich**; bei Regeländerungen werden beide angepasst (zuletzt: R2-Netto-Bezug in beiden).
- **Gratuite Divergenz wird beseitigt** (z. B. THROTTLE — wird als Eco-Modus *im Kern* erstklassig gemacht, damit beide Engines übereinstimmen; siehe Roadmap Phase 4).
- **Residuale Divergenz** (R4 Forecast, R5 Deadband sind im HA-Template nicht abgebildet) wird als **bekannte Limitation** dokumentiert (Kapitel 11 Risiken, FINDINGS).
- **B bleibt das spätere Upgrade**, falls die Arbeit „Kern steuert reale Anlage" behaupten soll.

**Update (Juni 2026) — Spiegelrichtung invertiert.** Die produktive Live-Steuerung läuft
faktisch über die SoC-Band-Automation `mvp_auto.yaml` (Betriebsmodi Eco/Standard/Super; Stop 50 % ·
Eco-Start 58 % · Standard 80–75 % · Super 90–85 %), **nicht** über die `bg_decision_*`-Core-Spiegel-Templates.
Diese Produktiv-Logik spiegelt den Kern (kW-Überschuss-R1) also *nicht*. Daraus folgt eine
Richtungsumkehr gegenüber der ursprünglichen Entscheidung:

- **Referenz ist künftig der Produktivbetrieb:** Das Energielabor (Bitaxe Gamma + NerdQaxe++) bildet
  die Avalon-Q-Steuerung **maßstabsgetreu** nach — SoC-Schwellen identisch (dimensionslos), nur die
  Leistung wird per Dreisatz auf die kleinen Miner skaliert. Das ist **keine** Divergenz, sondern ein
  verkleinertes Abbild (Skalierungstabelle: Thesis §4.6.7, Studie 2024d).
- **Kern-Angleichung (umgesetzt, additiv):** Der Kern unterstützt nun neben der Surplus-kW-Logik
  eine wählbare **SoC-Band-Strategie** (`RuleEngineConfig(strategy="soc_band")`, Modul
  `src/core/rules/r1_soc_band.py`), die das Produktiv-Schema nachbildet (Reserve-Stop 50 % · Eco 58 % ·
  Standard 80 % · Super 90 %; Mapping Eco→THROTTLE, Standard/Super→START, Modus in `params["mode"]`).
  **Default bleibt `"surplus"`** → die Studie läuft unverändert replay-basiert auf der Surplus-Logik,
  das eingefrorene Set S1–S10 bleibt unberührt. Tests: `tests/core/test_soc_band_strategy.py`.
- Die ursprüngliche Konsequenz „HA spiegelt den Kern" gilt damit nur noch für die `bg_decision_*`-Templates,
  nicht für die produktive SoC-Band-Automation. Die residuale R4/R5-Divergenz bleibt bis zur Kern-Angleichung bestehen.

**Update (Juni 2026) — R4 im SoC-Band-Modus + Priorität R5 > R4.** Die residuale
R4-Lücke (oben) wird additiv geschlossen, ohne den Surplus-Pfad oder das eingefrorene
Studien-Set zu berühren:

- **R4-Forecast-Veto, opt-in (`forecast_veto_enabled`, Default aus):** Im SoC-Band-Modus
  vetoed R4 ausschließlich den **PV-abhängigen Eco-Frischstart** (Miner aus → an), wenn die
  Prognose am Horizont unter `forecast_sustain_pv_kw` (Default 3,0 kW) liegt. Bei Standard/Super
  trägt die **Batteriereserve**, die PV-Prognose ist dort irrelevant — R4 greift nicht; ein
  laufender Miner wird nie von R4 gestoppt (R4 kann nur NOOP). Default aus, weil die reale
  Produktiv-Steuerung (`mvp_auto.yaml`) **keinen** Forecast nutzt; das Flag macht „R4 aktiv"
  zu einer *bewussten*, auditierbaren Entscheidung statt eines Datenzufalls.
- **Lokale, deterministische Forecast-Quelle (ADR 011):** `src/adapters/solar_forecast.py`
  berechnet die Klarhimmel-PV-Obergrenze rein aus der Sonnen-Geometrie (NOAA-Algorithmus),
  **ohne Netzzugriff** — der ADR-011-konforme Gegenpart zu den Cloud-Adaptern
  (`forecast.solar`/`open-meteo`). Reine Funktion von (Ort, Zeit, kWp) → der Entscheidungspfad
  bleibt replay-fähig.
- **Priorität R5 > R4 nachgezogen:** Reihenfolge ist nun `R3 > R2 > R5 > R4 > R1`. Ein
  Stabilitäts-Halt (Min-Runtime/-Pause, Deadband) schlägt das Prognose-Veto, sonst überstimmte
  die Prognose ein frisches Anti-Flapping-Fenster. Der Kern wertet R4 jetzt *nach* R5 aus
  (vorher: vorab berechnet, nachgelagert angewandt — gleiches Ergebnis, aber unklare Lesart).
- Tests: `tests/core/test_soc_band_strategy.py` (Veto/Nicht-Veto/Ordering),
  `tests/adapters/test_solar_forecast.py` (Geometrie/Determinismus).

---

## ADR 021 — Determinismus-Invariante maschinell erzwungen (Detail)

**Kontext.** Die Kern-Invariante „kein ML, kein RL, kein Zufall, keine Blackbox in
`src/core`" (ADR 007) war bisher nur als Prosa plus manuelles Review
abgesichert. In langen Agenten-Sessions ist genau das die Stelle, an der ein
versehentlicher `import torch` oder `from src.explain import …` unbemerkt in den Kern
leckt und den Determinismus-Anspruch der Arbeit aushöhlt.

**Entscheidung.** Ein ausführbarer AST-Test (`tests/core/test_architecture.py`) prüft
jede Datei unter `src/core/` und schlägt fehl bei: (1) Import aus
`explain`/`ui`/`adapters`/`sim`/`ha`, (2) Import eines ML-Frameworks (`sklearn`, `torch`,
`tensorflow`, `keras`, `xgboost`, `lightgbm`), (3) Nichtdeterminismus-Quelle (`random`,
`numpy.random`, `secrets`, inkl. aliasiertem `np.random.*`). Der Test läuft als Teil von
`make check` (CI).

**Verworfene Alternative.** `import-linter` (das NDepend-Pendant): scheidet aus, weil
sein Graph (grimp) externe Importe auf das Top-Level-Paket kollabiert und damit
`numpy.random` (verboten) nicht von `numpy` (für deterministische Mathematik erlaubt)
trennen kann. Der AST-Test ist zusätzlich dependency-frei und selbst inspizierbar (passt
zum No-Blackbox-Prinzip des Projekts). `import-linter` bliebe erst dann sinnvoll, wenn eine
volle Contract-Matrix über alle Schichten gebraucht wird.

**Konsequenzen.**
- Die Invariante ist jetzt **fallierbar**: ein Verstoß bricht CI, nicht erst ein Review.
- Der Test ist additiv, ändert keinen Produktivcode; `src/core/` ist beim Einführen bereits
  konform (3 Tests grün, Negativtest bestätigt das Greifen).
- **Erweitert (ADR 022/023):** Der Guard verbietet in `src/core/` zusätzlich `sqlite3`
  (Persistenz) und `uuid` (Identität). Die zuvor offene `uuid.uuid4()`-Frage ist mit ADR 023
  entschieden (Surrogat-ID, an der Boundary vergeben).
- **Bekannte Grenze:** Der Guard bleibt import- und zugriffsbasiert, kein Laufzeit-Beweis für
  Determinismus.

---

## ADR 022 — OverrideStore-Port: Persistenz aus dem Kern (Detail)

**Kontext.** Der `OverrideHandler` (`src/core/override_handler.py`) trug rohes SQL,
Tabellen-Schema-Wissen und `commit()`-Seiteneffekte direkt im Kern. Das widerspricht der
hexagonalen Architektur (ADR 002) und dem Anspruch eines persistenz-freien, deterministischen
Kerns: rohes SQL im „deterministischen Kern" ist ein angreifbarer Selbstwiderspruch.

**Entscheidung.** Ein Port `OverrideStore` (Protocol) wird im Kern definiert; der Handler hängt
nur an dieser Schnittstelle. Die SQLite-Implementierung (`SqliteOverrideStore`) zieht in die
data-Schicht (`src/data/override_store.py`). Ohne Store arbeitet der Handler rein in-memory
(deterministisch). Die Expiry/TTL-Logik bleibt Domäne im Kern; der Store ist reines CRUD plus
append-only-Log.

**Konsequenzen.**
- `src/core/` importiert kein `sqlite3` mehr; der Architektur-Guard (ADR 021) verbietet es nun.
- Verdrahtung in `main.py`/`production_runner.py`: `OverrideHandler(store=SqliteOverrideStore(conn))`. Der
  testbare `ProductionRunner` läuft per Default store-los (in-memory).
- Tests bleiben in der Aussage gleich; die DB-Persistenz-Tests injizieren jetzt den Store.

## ADR 023 — command_id als Surrogat-ID, Determinismus-Scope (Detail)

**Kontext.** `Decision.command_id` wurde im eingefrorenen Domänen-Objekt per `uuid.uuid4()`
erzeugt, die einzige Nichtdeterminismus-Quelle im Kern. Die command_id ist ihrer Funktion nach
aber eine **Surrogat-/Korrelations-ID**: Primary Key der `decision_events`-Tabelle und
Idempotenz-Schlüssel beim Aktuieren (`ActuationWriter`). Ihr Zweck ist Eindeutigkeit, nicht
Reproduzierbarkeit.

**Entscheidung.** command_id ist **nicht** Teil der deterministischen Entscheidung. Die Vergabe
wandert aus dem Kern an die Boundary (`new_command_id()` im Runner, nach `evaluate()`).
`Decision.command_id` ist nun `str | None` (Default None); der Kern produziert Entscheidungen
ohne ID. Der Determinismus-Anspruch wird präzise gefasst: deterministisch sind `action`,
`decision_code`, `reason`, `params`, `valid_until` (das, was Replay vergleicht); die
Surrogat-ID ist ausgenommen.

**Verworfene Alternative.** command_id deterministisch ableiten (z. B. aus `block_id`+`trigger`)
für byte-identisches Replay. Verworfen, weil mehrere `SAFETY_ASYNC`-Entscheidungen pro Block am
Primary Key kollidieren können; deterministische IDs wären hier riskanter, nicht sauberer, und
brächten keinen Mehrwert für den semantischen Replay-Vergleich.

**Konsequenzen.**
- `uuid` verlässt `src/core/`; der Architektur-Guard (ADR 021) verbietet es nun.
- Replay (`src/sim/replay.py`) ist nachweislich frei von uuid und vergleicht reine Semantik.
- Boundary-Vergabe in beiden Runnern; `ActuationWriter.new_command_id()` ist die einzige Quelle.

---

## ADR 024 — Einmaliger externer Backfill für Hashrate-Vorgeschichte (Detail)

**Kontext.** Der Hashrate-Chart im ₿itsy-Tab (`views/ki_hashrate.yaml`) soll die Netzwerk-
Hashrate wie den BTC-Preis als Log-Log-Chart seit Genesis zeigen. Die self-hosted
mempool.space-Instanz (`MEMPOOL_HOST`, bereits Quelle der Preishistorie, ADR-lose Praxis seit
`btc_power_law.py`) indiziert Hashrate/Difficulty aber nur für den Zeitraum, den ihr eigener
Node bereits verarbeitet hat (aktuell ≈ 1 Jahr, gesteuert über die Backend-Konfiguration
`INDEXING_BLOCKS_AMOUNT`) — kein Backfill seit Genesis wie bei der Preishistorie, die aus einem
extern gespeisten, aber lokal terminierten Feed kommt.

**Geprüfte Optionen.**
- **A — mempool-Node umkonfigurieren + reindizieren:** `INDEXING_BLOCKS_AMOUNT=-1` setzen und den
  Node die komplette Kette neu verarbeiten lassen. Bliebe vollständig local-first. Verworfen:
  unverhältnismäßiger Aufwand/Laufzeit auf der Gigi-Umbrel-Box für eine reine
  Kontext-Visualisierung, kein Bezug zur Last-/Mining-Steuerung.
- **B — Live-Fallback auf blockchain.info im laufenden Betrieb:** `btc_hashrate.py` ruft bei
  fehlender lokaler Historie live extern ab. Verworfen: verletzt ADR-001/011 dauerhaft, nicht nur
  einmalig — der reguläre Betrieb bekäme eine harte Cloud-Abhängigkeit.
- **C — Einmaliger manueller Backfill (gewählt):** ein separates, nicht in `src/data/`
  importiertes Skript (`scripts/backfill_hashrate_blockchain_info.py`) zieht die Vorgeschichte
  einmal von der öffentlichen, unauthentifizierten blockchain.info-Chart-API und schreibt eine
  statische Seed-Datei (`src/data/btc_hashrate_seed.json`, committet). Der reguläre Betrieb liest
  nur noch diese lokale Datei.

**Entscheidung: Option C.** `merge_with_seed()` bevorzugt bei Überschneidung immer die live von
mempool.space gemessenen Werte; der Seed deckt ausschließlich die Zeit davor ab. Die Karte zeigt
beide Quellen farblich getrennt (`own_measurement_since_days`), damit die Datenherkunft
transparent bleibt (kein Overstating der eigenen Messreihe).

**Konsequenzen.**
- Erster (und bewusst einziger) Punkt im Repo, an dem ein Skript direkt eine externe Cloud-API
  anspricht — klar isoliert in `scripts/`, nicht in `src/data/` oder `src/core/`.
- Die Trendlinie im Chart wird NICHT in die Zukunft projiziert (anders als beim Preis-Chart):
  bei der gefitteten Steigung (b≈9–10) würde schon eine Projektion von wenigen Jahren auf
  physikalisch unplausible EH/s-Werte führen. Die Regression ist rein deskriptiv über die
  Vergangenheit, kein etabliertes Modell wie die BTC-Preis-Power-Law-Heuristik.
- Bricht Option A (lokale Reindizierung) irgendwann durch, kann die Seed-Datei ersatzlos entfernt
  werden — `btc_hashrate.py` funktioniert auch ohne sie, dann nur mit dem lokal indizierten
  Zeitraum.

## ADR 025 — Live-Schaltschwellen: echte Hysterese + akku-reaktiver Notabstieg (Detail)

**Kontext.** Die Analyse in
[092_soc_saison_schwellen_vorschlag_de.md](./092_soc_saison_schwellen_vorschlag_de.md)
(23.08.2026, `scripts/analyze_mode_thresholds.py` gegen `data/bitgrid.db`) fand zwei
konkrete Ineffizienzen in `mvp_auto.yaml`: (1) `soc_super_off` griff versehentlich auf
`mvp_soc_std_pct` zurück statt eine eigene Schwelle zu haben — Super kollabierte beim
Runterschalten direkt auf Eco, ohne Standard-Zwischenschritt; (2) ein pauschaler,
zeitbasierter "Nachmittags-Cap" zwang Standard/Super unconditional auf Eco sobald die
Sonne den Zenit überschritt, unabhängig vom realen PV-Überschuss — 84-87% der
betroffenen Nachmittagsblöcke hatten noch genug Überschuss für Standard/Super. Zusätzlich
zeigte ein Live-Dashboard-Screenshot einen SoC-Sensor-Ausreißer (90%→0%→90% binnen
Minuten), gegen den die sicherheitskritische Stop-Regel keinen Schutz hatte.

**Geprüfte Optionen** für den Nachmittags-Cap:
- **A — PV-Überschuss-Schwelle als neuer, separater Mechanismus:** technisch sauber,
  aber verworfen: würde einen zweiten Mechanismus für dasselbe Problem einführen, wo
  bereits einer existiert (B).
- **B — Bestehenden akku-reaktiven Downgrade (`mvp_p3b`, bisher nur Super→Eco bei
  anhaltender Entladung >800W/5min) auf Standard generalisieren (gewählt).** Reagiert auf
  den echten Akku-Zustand statt die Uhrzeit, ist bereits produktiv erprobt für Super.

**Entscheidung: Option B**, plus:
- `mvp_soc_super_off_pct` (95%) und `mvp_soc_std_off_pct` (83%) als eigene, im Dashboard
  sichtbare/tunbare Schwellen statt geteilter Werte. Super fällt jetzt auf Standard, nicht
  mehr direkt auf Eco — echte Hysterese-Kaskade Super⇄Standard⇄Eco.
- R8 (vormals "P3b") generalisiert: zwei separate, tunbare Entladeschutz-Schwellen
  (`mvp_batt_discharge_super_downgrade_w` -800W, `mvp_batt_discharge_std_downgrade_w`
  -400W, je 5min sustained). Der pauschale Nachmittags-Cap ("P0a") entfällt ersatzlos.
- `binary_sensor.mvp_soc_kritisch_debounced` (4 Min. `delay_on`) debounced die
  Stop-Regel (R1) gegen kurze SoC-Sensor-Ausreißer.
- Alle Regeln in `mvp_auto.yaml` umbenannt von der gewachsenen P1/P1b/P2/P2.5/P3/P3.5/P4-
  Nummerierung auf eine durchgehende R1-R8-Folge (siehe Kommentare je Automation).
- Winter-Stop-Schwelle bewusst **nicht** abgesenkt oder verändert in dieser Runde
  (Autarkie-Vorrang, keine echten Winterdaten) — nur die o.g., datengestützten
  Sommer-Korrekturen wurden live umgesetzt.

**Konsequenzen.**
- `src/data/daily_kpi.py` (Z.41-47) hardcoded die alten SoC-Band-Grenzen als Literale —
  braucht ein Folge-Update, sonst beschreiben seine Aggregate eine Anlage, die es nicht
  mehr gibt (noch offen, nicht Teil dieser Änderung).
- Der Sensitivitäts-Sweep für `mvp_soc_super_off_pct` (95% vs. 92%/90%/88%) und die
  Entladeschutz-Schwelle für Standard (-400W, ohne Feldtest) sind gute erste Werte, aber
  über das Dashboard nachjustierbar, sobald reale Erfahrung vorliegt.
- Ein Implementierungsfehler während der Umsetzung (Debounce-Sensor registrierte sich
  unter `binary_sensor.mvp_soc_kritisch_debounced` statt der referenzierten
  `binary_sensor.mvp_soc_kritisch`, da HA die Entity-ID einmalig beim ersten Laden aus
  dem `name`-Feld ableitet und spätere Namensänderungen sie nicht mehr ändern) wurde
  binnen Minuten über die HA-API erkannt und behoben, bevor er sich auswirken konnte
  (beide Miner standen zum Zeitpunkt bereits sicherheitsbedingt in Standby).

## ADR 026 — energy_to_sats persistiert: Rohtabelle statt daily_kpi-Direkterweiterung (Detail)

**Kontext.** `012_quality_goals.md` definiert seit Projektbeginn das KPI-Ziel
"Energy-to-Sats-Effizienz ≥ 45 sats/kWh (7-Tage-Schnitt)", `05243_kpi_reporting.md` beschreibt
dafür bereits den Bauplan (Aggregator Job, Metric Catalog mit `energy_to_sats` als
Beispielmetrik) — beides nie umgesetzt. Bitcoin/Sats-Daten lebten bislang ausschließlich in
HA-YAML/JS (30-Tage-Rolling-Log in `views/mining_log.yaml`, danach weg), nie in `bitgrid.db`.
`EnergyState.mining_value_ct_kwh` erreicht zwar `src/core/`, wird aber von R1 bewusst nicht als
Start-Gate gelesen (Eigenverbrauch-vor-Einspeisung-Strategie, siehe R1-Docstring) und landet nie
in der DB (`state_store.py` filtert es sogar explizit aus dem INSERT).

**Geprüfte Optionen.**
- **A — `daily_kpi.py` fragt beim Neuberechnen live HA ab, kein Rohtabellen-Layer.** Verworfen:
  bricht die Grundinvariante von `daily_kpi` ("jede Zeile ist aus energy_states/miner_states
  reproduzierbar", `db.py`-Kommentar) — `rebuild()` liefe dann nicht mehr offline/replay-fähig,
  und `nightly.py` recomputed jede Nacht die komplette DB-Historie (`days_in_db()`), das würde
  jede Nacht einen HA-Livecall pro historischem Tag bedeuten.
- **B — Neue Rohdaten-Tabelle `bitcoin_daily_settlement`, `daily_kpi.py` liest daraus (gewählt).**
  Gleiche Trennung wie `energy_states`/`miner_states` (Rohfakt, `INSERT OR IGNORE`) vs. `daily_kpi`
  (reines Aggregat, `INSERT OR REPLACE`) — kein neues Muster, nur konsequent auf Bitcoin-Daten
  angewendet.
- **Direkter F2Pool-Zugriff statt über HA:** verworfen ohne eigene Option, weil `f2pool_api_token`
  gitignored ist und eine IP-Whitelist braucht, deren Verletzung (403) bereits einmal vier Wochen
  unbemerkt blieb (`packages/pool.yaml`-Kommentar zu `pool_ip_whitelist_changed`). Ein zweites
  Skript mit eigenem Secret/eigener Whitelist-Pflege dupliziert genau diese Fehlerquelle. HAs
  bereits autorisierte REST-API (Token, Watchdog, Push-Alarm) wird stattdessen wiederverwendet.
- **Tages-Zuordnung über `pool_btc_daily_log` statt `pool_settlement_history`:** verworfen als
  Primärquelle (bleibt Fallback). `pool_btc_daily_log` ist Berlin-lokal beschriftet (die
  schreibende HA-Automation nutzt `now()`, keine feste UTC-Zeitzone) und auf 10 Einträge
  gedeckelt. `sensor.pool_settlement_history` liefert dagegen `mining_extra.mining_date` als
  Unix-Zeitstempel, daraus lässt sich der UTC-Kalendertag exakt ableiten — dieselbe Umrechnung
  nutzt bereits `views/mining_log.yaml` fürs Dashboard.

**Entscheidung: Option B.** Neues Skript `src/data/pool_settlement_sync.py` (eigener,
unabhängiger Windows-Scheduled-Task ~04:00 lokal, NICHT im bestehenden `nightly_and_sync.py`-Lauf
um 00:20 — F2Pool verbucht Settlements erst gegen 02:00, ein 00:20-Lauf läse systematisch einen
Tag zu früh). `daily_kpi.compute_day()` liest `bitcoin_daily_settlement` und schreibt
`energy_to_sats = earned_btc * 1e8 / mining_kwh` in `daily_kpi`, `NULL` wenn keine Abrechnung
vorliegt oder `mining_kwh` 0 ist (keine erfundene Null). Neue View `v_energy_to_sats_7d` misst
das offizielle Ziel über echte Kalendertage, keine `ROWS BETWEEN`-Fensterfunktion (würde
stillschweigend über Lückentage hinwegmitteln).

**Konsequenzen.**
- Erster Punkt, an dem eine Bitcoin-Kennzahl aus `bitgrid.db` selbst (nicht nur HA-Dashboard)
  abfragbar ist — auch über `query_server.py`s `tage`-Werkzeug für den Nachtanalysten.
- `btc_eur_price_approx` ist bewusst nur Kontext (Kurs beim Sync-Lauf, ~04:00 des Folgetags),
  nicht Tagesdurchschnitt oder Eröffnungskurs — `energy_to_sats` selbst ist rein
  BTC-denominiert und hängt nicht von dieser Spalte ab.
- `pool_stale_pct` (Pool-seitige Stale-Rate) ist bewusst NICHT Teil von
  `bitcoin_daily_settlement`: es gibt aktuell keine Tages-Erfassungs-Automation dafür in HA, eine
  Spalte ohne Füllpfad wäre ein verstecktes Platzhalterfeld.
- `database_exploration/werkzeuge.md` im Obsidian-Vault (außerhalb des Repos) beschreibt
  `query_server.py`s Werkzeuge und muss außerhalb dieses Commits nachgezogen werden, sonst
  driftet die Doku vom tatsächlichen Tool-Set ab.

## ADR 027 — Saisonale SoC-Schwellen-Automatik, ganzjährig inkl. Winter (Detail)

**Kontext.** [092_soc_saison_schwellen_vorschlag_de.md](./092_soc_saison_schwellen_vorschlag_de.md)
(23.08.2026) hatte eine saisonale Anpassung der sechs Schaltschwellen (R1, R3-R7) vorgeschlagen,
aber Winter/Übergang bewusst **nicht** umgesetzt: keine echten Winter-Messdaten,
Autarkie-Vorrang, offene Frage 2 ("wie aggressiv im Winter?") blieb unbeantwortet, eigener
"vorsichtiger Mittelwert" des Autors dort war 68-70% Stop-SoC. In einer Folgesession
(26.08.2026) wurde gemeinsam mit Claude Code eine andere Herleitung für den nötigen
Nacht-Reservewert durchgerechnet: nicht "wie viele Grundlast-Stunden Spielraum hat der Miner
zwischen 100% und Stop" (Methode aus 092), sondern "welche Abend-SoC braucht es, damit die
Hausgrundlast allein bis zum Morgen nicht unter den 10%-Tiefentladeschutz-Boden fällt, plus 5%
Puffer" — dieselbe Formel-Struktur wie die Autarkie-Regel (R2) im Python-Kern (`rules.yaml`,
dort nur Thesis-Studienmodell, siehe ADR 020, läuft nicht auf dem echten Haus). Mit den
gemessenen Werten aus 092 (573 W Nacht-Grundlast, 12,5 kWh Kapazität) und der längsten Nacht je
Monat (Standort 48,1°N/11,6°O) ergibt diese Formel für Dezember ~88% Stop-SoC statt der in 092
vorsichtig geschätzten 68-70% — eine Differenz von rund 18-20 Prozentpunkten, die nicht
stillschweigend übernommen werden durfte.

**Geprüfte Optionen.**
- **A — 092-Kurs beibehalten: Winter/Übergang unverändert bei 60%, nur Anzeige "Projektion, keine
  Winterdaten" (von Claude Code empfohlen).** Verworfen vom Nutzer: die in dieser Session
  hergeleiteten Werte werden als wichtiger eingestuft als die frühere Vorsicht in 092.
- **B — Headroom-Formel aus 092 übernehmen, ganzjährig automatisch (kein 10%-Boden).** Nicht
  gewählt — nicht explizit ausgeschlossen, aber vom Nutzer nicht als Antwort gewählt.
- **C — Reserve-Formel (10%-Boden + 5%-Puffer, aus R2 übernommen), ganzjährig automatisch,
  inkl. Winter (gewählt).**

**Entscheidung: Option C.** Nutzer-Position wörtlich: "Die Erkenntnisse aus der Tabelle sind
wichtiger als ADR." Umsetzung:
- Neuer Helfer `input_number.mvp_night_baseload_w` (Start 573 W, manuell nachzupflegen) neben dem
  bereits bestehenden `battery_capacity_kwh` (12,5 kWh) — beide zusammen einzige manuelle
  Stellschrauben.
- Neuer Diagnose-Sensor `sensor.mvp_saison_status` (`mvp_auto.yaml`) zeigt Block
  ("Nur Eco" / "Eco + Standard" / "Voll") und die sechs abgeleiteten Zielwerte als Attribute.
- Neue Automation `mvp_saison_automatik` setzt `mvp_soc_stop_pct`/`mvp_soc_eco_start_pct`/
  `mvp_soc_std_off_pct`/`mvp_soc_std_pct`/`mvp_soc_super_off_pct`/`mvp_soc_super_pct` stündlich neu
  (plus bei HA-Start und bei Änderung der beiden Stellschrauben), rechnet die Formel unabhängig
  vom Anzeige-Sensor nach (keine Lesereihenfolge-Abhängigkeit). Feste Abstände zu den bisherigen
  Werten bleiben erhalten (+10/+23/+25/+35/+40 über Stop), auf 100% gekappt.
- Feste 12-Werte-Tabelle "längste Nacht je Monat" als astronomische Konstante für den Standort,
  keine Live-Berechnung über `sun.sun` (wäre präziser für den jeweiligen Tag, aber Nutzer-Vorgabe
  war explizit Monats-, nicht Tagesgranularität).
- Dashboard-Tab "Einstellungen": links neue Gruppe "Saisonale Automatik" mit den zwei
  Stellschrauben, rechts Status-Anzeige (Block, Ziel-Hausreserve diesen Monat).
- Mit den realen Werten (573 W/12,5 kWh statt der zuvor im Gespräch verwendeten Rundwerte
  550-600 W/13 kWh) verschiebt sich der Block-Split von der zuvor angenommenen 4-4-4-Aufteilung
  auf **Nur Eco: Jan/Feb/Okt/Nov/Dez, Eco+Standard: Mär/Apr/Aug/Sep, Voll: Mai/Jun/Jul**
  (5-4-3-Monate).

**Konsequenzen.**
- Widerspricht bewusst der in 092/ADR-025-Umfeld dokumentierten Vorsicht ("keine echten
  Winterdaten") — der Widerspruch ist hier dokumentiert, nicht stillschweigend übergangen.
  Sobald echte Winterdaten vorliegen (erster Winter mit Betrieb, siehe 092 Abschnitt 7), muss
  diese Entscheidung gegen die Messwerte geprüft werden, nicht nur gegen die Formel.
  Empfehlung an einen künftigen Reviewer (Codex oder Nachfolgemodell): genau das als offenen
  Prüfpunkt behandeln, nicht als erledigt.
- `mvp_soc_super_off_pct`/`mvp_soc_std_pct`/etc. sind ab jetzt **nicht mehr dauerhaft manuell
  pflegbar** — ein manueller Tap im Dashboard hält nur bis zum nächsten Stundenlauf der
  Automatik. Die einzigen noch wirksamen manuellen Stellschrauben sind Grundlast und Kapazität.
- `battery_min_soc_pct: 10.0` und `evening_soc_safety_margin_pct: 5.0` aus `rules.yaml` (R2,
  Kern/Thesis-Modell) sind jetzt implizit auch Annahme der Live-Automation — ob der reale
  SMA-Wechselrichter tatsächlich auf 10% Tiefentladeschutz konfiguriert ist, wurde in dieser
  Runde nicht verifiziert (siehe `battery_min_soc_pct`-Kommentar in `rules.yaml`: "Zielwert, dort
  einzustellen").
- `src/data/daily_kpi.py` hardcoded weiterhin die alten SoC-Band-Grenzen (60/70/85/100) als
  Literale (siehe bereits in ADR 025 als offen vermerkt) — mit monatlich wechselnden Schwellen ist
  dieser Drift jetzt zusätzlich verschärft, nicht nur saisonal statisch falsch. Weiterhin nicht
  Teil dieser Änderung.
- Deployment steht noch aus (`scripts/deploy_ha.sh --restart`), nicht Teil dieses Commits.

## ADR 028 — Saison-Automatik: dritte Kehrtwende, zurück zur Live-Formel (Detail)

**Kontext.** Innerhalb von 24 Stunden (26.-27.08.2026) wechselte die Herleitung der sechs
SoC-Schwellen dreimal: ADR 027 führte eine Live-Formel ein (Grundlast/Kapazität als
`input_number`, stündlich neu berechnet), wurde noch am selben Tag durch eine feste
12-Monats-Tabelle ersetzt (Nutzer-Zitat: "das ist die Tabelle die zählt" — die Live-Formel
hatte mit 600 W Grundlast Super im August komplett gesperrt, was der Nutzer nicht wollte),
und wird mit diesem ADR erneut auf eine Live-Formel zurückgedreht (Nutzer-Zitat: "die
nächtliche Grundlast soll die Automatik betreiben"). Diese Historie wird hier bewusst
festgehalten, nicht geglättet — sie zeigt, dass die zugrunde liegende Frage (soll ein
Wechsel der Annahme automatisch alle sechs Schwellen verschieben, oder soll ein Referenzwert
eingefroren werden) mehrfach hin und her abgewogen wurde, nicht dass eine Seite "falsch" war.

**Entscheidung: Live-Formel (wie ADR 027 vor der Tabellen-Revision), mit zwei Korrekturen
gegenüber der ursprünglichen ADR-027-Fassung:**
- **Trigger nicht mehr stündlich, sondern täglich** (`time_pattern: hours: 0, minutes: 10`)
  plus sofort bei Änderung der beiden Stellschrauben (`state`-Trigger) plus bei HA-Start.
  Nutzer-Begründung: "es reicht die 6 Schwellenwerte einmal zum Monatswechsel zu ändern" —
  die Nachtlänge (der einzige monatsabhängige Teil der Formel) ändert sich ohnehin nur an
  Monatsgrenzen, ein stündlicher Poll war unnötiger Zustands-Churn.
- **Tier-gegatete Erreichbarkeit in der Anzeige-Tabelle korrigiert:** die zwischenzeitliche
  feste Tabelle (ADR 027) zeigte "—" für eine ganze Stufe (z. B. Standard-Start UND
  Standard-Ende), sobald die Start-Schwelle über 100% lag, auch wenn die Ende-Schwelle für
  sich genommen noch unter 100% gelegen hätte. Die neu gebaute Live-Tabelle in Einstellungen
  hatte das anfangs pro Zelle unabhängig geprüft (ein Ende-Wert ohne erreichbaren Start-Wert
  wäre möglich gewesen) — gegen die per Hand bestätigte Referenztabelle getestet und auf
  Tier-Gating zurückkorrigiert (Ende folgt Start), damit beide Ansichten (Sensor-Attribute,
  Anzeige-Tabelle) dieselbe Logik wie die reale Automatik verwenden.
- **Whitespace-Bug aus der Fix-Tabellen-Ära behoben, nicht wiederholt:** einzelne
  `{% set %}`-Zeilen zwischen Markdown-Tabellenzeilen hinterließen Leerzeilen, die die
  GFM-Tabelle brachen (live bestätigt 27.08.2026 per Screenshot: Kopfzeile rendert, Datenzeilen
  erscheinen als literaler Text). HAs Jinja-Umgebung trimmt Block-Whitespace offenbar nicht wie
  angenommen. Fix: `namespace(rows=[])` sammelt vorgefertigte Zeilen-Strings, `{{ ns.rows |
  join('\n') }}` fügt sie mit echten (Daten-)Zeilenumbrüchen zusammen statt sich auf
  Template-Whitespace zu verlassen — funktioniert unabhängig von `trim_blocks`/`lstrip_blocks`,
  lokal mit beiden Einstellungen gegengetestet.

**Konsequenzen.**
- `mvp_night_baseload_w` (Default 550 W) und `battery_capacity_kwh` (bestehend, 12,5 kWh) sind
  wieder die einzigen beiden echten Stellschrauben, wieder sichtbar in Einstellungen links.
- Mit dem realen `battery_capacity_kwh` (12,5 statt der in der Referenztabelle verwendeten
  13 kWh) verschieben sich die Werte leicht gegenüber der Handrechnung von vorhin — z. B.
  August landet bei 550 W/12,5 kWh nur noch bei "Eco+Std" statt "Voll" (Super knapp über
  100% Rohwert). Das ist die korrekte, aktuelle Kapazität, keine neue Diskrepanz.
- Die separate 6-Gruppen-Übersicht auf dem Steuerung-Tab (ADR aus der Session vom 26.08.,
  tippbare Zeilen) ist von dieser Änderung nicht betroffen — sie liest die sechs
  `input_number.mvp_soc_*` live, unabhängig davon, ob eine feste Tabelle oder eine Formel sie
  zuletzt gesetzt hat.
- Falls diese Entscheidung noch einmal kippt: die feste Referenztabelle (550 W/13 kWh) bleibt
  als Git-Historie in diesem Dokument und im Diff auffindbar, nicht verloren.

---

## ADR 029 — Energy-to-Sats-Ziel: saisonal gestaffelt statt fest 45 sats/kWh (Detail)

**Kontext.** Das feste KPI-Ziel aus `012_quality_goals.md` (≥ 45 sats/kWh, ADR 026) war seit
Projektbeginn nie kalibriert worden. Am 31.08.2026 fiel auf: die Effizienz-Karte
(`views/stats_energy_to_sats.yaml`) zeigte nur 3 Tage Historie statt der erwarteten Woche —
Ursache war ein separater, an diesem Abend behobener Bug (die komplette HA-History-/
Settlement-Sync-Kette stand seit 25.08.2026 still, kein Scheduled Task ruft die Skripte auf).
Der Nachhol-Lauf lieferte 17 echte Tage (15.–31.08.2026), die zeigten: der reale
Tageswert liegt seit Wochen konstant bei ~118–137 sats/kWh, Faktor ~2,8 über dem "Ziel". Das
Ziel war also nie eine Herausforderung, sondern längst Vergangenheit — hätte man das ADR 026
kalibriert, wäre das früher aufgefallen.

**Datengrundlage (n=17, 15.–31.08.2026, `daily_kpi.energy_to_sats`).** Mittelwert 125,7,
Median 125,68, Populationsstandardabweichung 5,1 (≈4 % relative Streuung), Spanne 117,26–137,49.
Sehr geringe Streuung für n=17, aber: **alle 17 Tage liegen in einer einzigen Saison**
(August, laut `sensor.mvp_saison_status` mit den aktuellen Live-Werten `mvp_night_baseload_w`=
535 W / `battery_capacity_kwh`=12,5 kWh knapp im Tier "Voll", `hausreserve_pct` 59,9 % — siehe
ADR 027/028 für die Formel). Keine Winter-/Übergangsdaten vorhanden.

**Geprüfte Optionen.**
- **A — Fester Wert, nur die Zahl anheben (z. B. auf 120).** Verworfen: ignoriert, dass die
  erreichbare Effizienz je nach Saison-Tier (Voll/Eco+Standard/Nur Eco,
  `sensor.mvp_saison_status`) strukturell unterschiedlich ist — dieselbe Schwäche, die ADR 027/028
  bei den SoC-Schwellen bereits gegen einen unbegründeten festen Wert entschieden hat.
- **B — Saisonal gestaffelt, aus echten Monatsmessungen abgeleitet, sobald verfügbar.**
  Wissenschaftlich sauberste Option, aber aktuell nicht umsetzbar: nur ein Monat (August) hat
  echte Daten. Elf von zwölf Werten blieben auf unbestimmte Zeit beim alten 45er-Wert stehen
  (Nutzer-Rückfrage dazu ausdrücklich gestellt und **gegen** diese Option entschieden).
- **C — Saisonal gestaffelt, aus einem Effizienz-Modell hergeleitet, explizit als vorläufig
  markiert (gewählt).** Nutzer-Entscheidung 01.09.2026, nachdem A und B als Alternativen
  vorgelegt wurden.

**Modell (Option C).** `v_modus_effizienz` (DB-View) liefert je Miner/Modus das gemessene
W/TH-Verhältnis (Mittel beider Miner, 15.–31.08.2026): Eco 16,05, Standard 17,74, Super 18,79
W/TH. Daraus folgt: **Eco ist pro kWh effizienter als Super**, nicht umgekehrt — ein ASIC liefert
bei niedrigerer Taktung mehr Hashrate pro Watt (Standardverhalten bei Übertaktung, keine
Anomalie dieser Hardware). Für Pool-Mining gilt näherungsweise sats/kWh ∝ 1/(W/TH) bei
Netzwerk-Difficulty/Kurs als (kurzfristig) konstantem Faktor. Gewichtet man die drei Modi mit
dem tatsächlichen Zeitanteil in den 17 August-Tagen (Eco 37 %, Standard 55 %, Super 8 %) ergibt
sich ein Kalibrierungspunkt für das Tier "Voll". Die anderen beiden Tiers werden mit
vereinfachten, klar benannten Annahmen gewichtet (Nur Eco = 100 % Eco; Eco+Standard = 50/50 Eco/
Standard, kein Super) und relativ zum Voll-Tier skaliert:

| Tier (`sensor.mvp_saison_status`) | Monate (Formel aus ADR 028, `mvp_night_baseload_w`=535 W) | Modellfaktor ggü. Voll | Ziel (gerundet) |
| :--- | :--- | :--- | :--- |
| Voll | Mai–Aug | 1,00 (Kalibrierungspunkt, **gemessen**) | 125 sats/kWh |
| Eco + Standard | Mär, Apr, Sep | 1,018 (**modelliert**) | 130 sats/kWh |
| Nur Eco | Okt–Feb | 1,072 (**modelliert**) | 135 sats/kWh |

Gerundet auf 5er-Schritte, um keine Scheinpräzision vorzutäuschen — die Modellannahmen (feste
50/50-Gewichtung, Difficulty/Kurs als konstant über die 17 Tage) tragen keine zweite
Nachkommastelle.

**Bewusst NICHT im Modell erfasst — zwei zusätzliche, unabhängige Unsicherheitsquellen:**
1. **Netzwerk-Difficulty-Drift.** Globale Mining-Difficulty steigt strukturell mit der Zeit;
   bei gleicher eigener Hardware sinkt sats/kWh dadurch tendenziell über Monate, unabhängig von
   der Saison. In 17 Tagen nicht messbar, wirkt nur in eine Richtung (nach unten) — macht die
   Modell-Ziele für weiter in der Zukunft liegende Tiers (v. a. Winter) tendenziell zu optimistisch,
   nicht zu pessimistisch.
2. **August liegt an der Tier-Grenze**, nicht in der Mitte von "Voll" (`hausreserve_pct` 59,9 %
   von 60 % Cutoff). Juni/Juli hätten nach der Formel einen höheren Super-Zeitanteil als August —
   nach obigem Modell (Eco effizienter als Super) würde das den realen "Voll"-Wert eher noch
   unter 125 drücken, nicht darüber. Der gewählte Wert ist also eher konservativ hoch als
   zu niedrig angesetzt.

**Entscheidung.** `src/data/energy_to_sats_export.py` berechnet `target_sats_per_kwh` je nach
Kalendermonat des Exports (Tabelle oben, hartkodiert als `_SEASONAL_TARGETS`, kein Duplikat der
HA-Automatik — reine Anzeige, kein Steuerpfad). `views/stats_energy_to_sats.yaml` zeigt Wert und
Label dynamisch aus dem JSON-Artefakt statt hartkodiertem "45 sats/kWh"-Text.
`012_quality_goals.md` verweist auf dieses ADR statt einen Wert zu duplizieren.

**Konsequenzen.**
- **Ausdrücklich vorläufig:** Sobald ein Monat außerhalb "Voll" echte `energy_to_sats`-Daten
  hat, ersetzt der gemessene Wert die Modellschätzung für dessen Tier — dieser Abschnitt ist
  dann zu aktualisieren, nicht stillschweigend zu überschreiben (Historie bleibt im Diff sichtbar,
  gleiches Prinzip wie ADR 028).
- Die Tier-Grenzen selbst hängen an `mvp_night_baseload_w`/`battery_capacity_kwh` (ADR 028) —
  ändern sich diese Stellschrauben, verschieben sich auch die Monatszuordnungen in der Tabelle
  oben, nicht nur die SoC-Schwellen.
- Betrifft nur die Anzeige/das KPI-Ziel, keine Regel in `core/` — R1-R8 lesen `energy_to_sats`
  nicht als Steuersignal.

---
> **Nächster Schritt:** Die ADRs erklären das "Warum". Im nächsten Schritt betrachten wir die wichtigsten Qualitätsanforderungen im Detail.
>
> 👉 Weiter zu **[10 - Qualitätsszenarien](../10_quality_scenarios/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
