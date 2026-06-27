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
- Verdrahtung in `main.py`/`runner.py`: `OverrideHandler(store=SqliteOverrideStore(conn))`. Der
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
> **Nächster Schritt:** Die ADRs erklären das "Warum". Im nächsten Schritt betrachten wir die wichtigsten Qualitätsanforderungen im Detail.
>
> 👉 Weiter zu **[10 - Qualitätsszenarien](../10_quality_scenarios/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
