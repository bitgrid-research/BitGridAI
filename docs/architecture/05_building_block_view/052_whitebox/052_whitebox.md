# 05.2 Die System-Whitebox

Deckel auf! Willkommen im Maschinenraum.

In Level 1 haben wir BitGridAI als geschlossenen Kasten betrachtet. Jetzt schauen wir hinein.
Hier zerlegen wir das System in seine Software-Module. Unsere Architektur ist **Local-First** und **deterministisch**. Das bedeutet: Der Kern entscheidet nach festen Regeln (R1–R5), während KI-Komponenten ("Explain-Agent") nur beobachtend zur Seite stehen.

*(Platzhalter für ein Bild: Ein Diagramm der inneren Struktur. Im Zentrum der "Core" (Regelwerk & State), drumherum die "Modules" (Adapter), und an der Seite die "Data"-Tanks. Der Hamster prüft die Leitungen.)*
![Hamster im Maschinenraum](../../media/pixel_art_whitebox_internal.png)

## Hauptkomponenten (Main Components)

Wir organisieren den Code in klare Verantwortungsbereiche. Diese Struktur findest du auch direkt im Source-Code wieder:

| Modul / Pfad | Komponente | Verantwortung & Details |
| :--- | :--- | :--- |
| **`core/energy_context`** | **The State (SSoT)** 🧠 | Verwaltet den `EnergyState`. Konsolidiert alle Eingangsdaten (Messwerte, Forecasts, Preise, Thermo-Daten). Ist die einzige Quelle der Wahrheit für Entscheidungen. |
| **`core/block_scheduler`** | **The Clock** ⏱️ | Der Taktgeber. Erzwingt den **10-Minuten-Rhythmus**. Verwaltet das Zeitfenster und vergibt `valid_until` (Deadband), um das System zu beruhigen. |
| **`core/rule_engine`** | **The Brain** ⚙️ | Die deterministische Logik. Prüft Regeln R1–R5 (Start, Autarkie, Thermo, Forecast, Stabilität).<br>**Priorität:** `R3 (Safety) > R2 (Autarkie) > R5 (Anti-Flap) > R1/R4 (Optimierung)`. |
| **`modules/`** | **The Adapters** 🔌 | Die Verbindung zur Hardware. Enthält spezifische Implementierungen für PV, Smart Meter, Batteriespeicher und Miner (via MQTT, REST oder Modbus). |
| **`ui/`** | **The Face** 🖥️ | Stellt das Web-Interface bereit. Beinhaltet den WebSocket/REST-Layer für Live-Daten, die Timeline-Visualisierung, Previews und manuelle Overrides. |
| **`explain/`** | **The Voice** 🗣️ | Ein lokaler "Explain-Agent" (On-Device LLM oder Templates). Erzeugt Microcopy ("Warum passiert das?") und "Was-wäre-wenn"-Szenarien. **Wichtig:** Read-only Zugriff auf den Regelpfad (darf nicht steuern!). |
| **`data/`** | **The Memory** 💾 | Kümmert sich um Persistenz. Speichert Operational Data (SQLite) und Langzeit-Logs (Parquet/JSON) für KPIs und Replays. |
| **`research/`** | **The Lab** 🎓 | Tools für den Daten-Export und Replay-Funktionen. Verwaltet die Opt-in-Governance (Datenschutz). |

---

## Interne Datenflüsse (Internal Flows)

Wie fließt eine Information durch diese Bausteine?

1.  **Sensing:** `modules/` (Adapter) lesen Hardware-Daten $\rightarrow$ Schreiben in `core/energy_context` (Update EnergyState).
2.  **Scheduling:** `core/block_scheduler` triggert neuen Block $\rightarrow$ Weckt `core/rule_engine`.
3.  **Deciding:** `core/rule_engine` prüft Regeln (R1–R5) gegen EnergyState $\rightarrow$ Erzeugt `Decision` & `DecisionEvent`.
4.  **Actuating:** `Decision` geht an `modules/` (Miner/Relais schalten) + `DecisionEvent` geht an `ui/` (Anzeige) und `data/` (Log).
5.  **Explaining:** `explain/` analysiert den State $\rightarrow$ Erzeugt `ExplainSession` $\rightarrow$ Geht an `ui/` (User Info).
6.  **Feedback:** User macht Override/Research-Toggle $\rightarrow$ Geht an `core/rule_engine` $\rightarrow$ Feedback an `ui/`.

---

## Zentrale Datenmodelle

Damit die Module sich verstehen, nutzen sie definierte Datenstrukturen:

### `EnergyState` (Das Abbild der Realität)
* `ts, block_id`: Zeitstempel und Takt-ID.
* `p_pv_kw, p_load_kw, surplus_kw`: Aktuelle Leistungswerte.
* `soc_pct`: Batterieladestand.
* `t_miner_c`: Kritische Temperatur.
* `price_ct_kwh`: Dynamischer Strompreis.
* `grid_import/export_kw`: Netzfluss.

### `DecisionEvent` (Das Ergebnis)
* `action`: Was wurde getan? (z.B. `START_MINING`).
* `reason`: Warum? (Text-ID oder Code).
* `trigger`: Welcher Wert hat es ausgelöst? (z.B. `surplus > 3000`).
* `params`: Mit welchen Parametern? (z.B. `power_limit=2000W`).
* `valid_until`: Wie lange gilt das mindestens? (Deadband).

---

## Querschnittliche Konzepte (Cross-Cutting)

Diese Prinzipien gelten für *alle* Module in der Whitebox:

* **Explainability by Design:** Kein `DecisionEvent` darf den Kern verlassen, ohne `reason`, `trigger` und `params` gefüllt zu haben.
* **Safety First:** Die Regeln R3 (Thermo) und R2 (Autarkie-Schutz) dürfen jederzeit Deadbands brechen. Ein Fehler führt immer zu **Stop $\rightarrow$ Safe**.
* **Determinismus:** Gleicher Input muss im `core` immer zum exakt gleichen Output führen. Das ermöglicht Tests und Replays.
* **Privacy-by-Default:** Telemetrie verlässt das Modul `research/` nur bei explizitem Opt-in.

---
> **Nächster Schritt:** Wir kennen jetzt die Bausteine und ihre Schnittstellen. Aber wie "tanzen" sie zusammen? Im nächsten Kapitel bringen wir Leben in die Bude und schauen uns die dynamischen Abläufe an.
>
> 👉 Weiter zu **[06 Laufzeitsicht](../../06_runtime_view/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](../README.md)**
