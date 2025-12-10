# 08.7 Testbarkeit & Simulation

Härtetest ohne Hardware.

Da wir in der realen Welt agieren, können wir nicht ständig mit echten Wechselrichtern und heißen Minern testen. Die Kosten und die Zeit für physische Tests wären immens.

Daher ist es ein fundamentales architektonisches Ziel, dass das **gesamte System ohne physische Hardware lauffähig und testbar** ist. Die strikte Anwendung der **Hexagonalen Architektur** (Trennung von Core und Adaptern) und das Prinzip der **deterministischen Regeln (R1–R5)** sind hier unsere wichtigsten Werkzeuge.

*(Platzhalter für ein Bild: Ein Hamster sitzt vor einem Monitor, auf dem ein kompliziertes Sequenzdiagramm zu sehen ist, und führt mit einem kleinen Roboter-Hamster im Sandkasten einen Test durch.)*
![Hamster führt Simulation durch](../../media/pixel_art_hamster_simulation.png)

## 1. Test-Arten & Determinismus

Dank der strikten Trennung und der regelbasierten Logik können wir verschiedene Test-Level effektiv anwenden:

| Test-Art | Gegenstand | Ziel |
| :--- | :--- | :--- |
| **Unit-Tests** | Regeln R1–R5, Schwellen, Hysterese, Prioritäten. | Prüfen der Kernlogik: Muss `R3 > R2 > R5 > R1/R4` gelten? Funktioniert der Schwellwert für 1.5 kW? |
| **Integrationstests** | MQTT Topics, REST Endpunkte, Adapter-Logik. | Prüfen der Schnittstellen: Führt `POST /override` zu einem `DecisionEvent` im UI? |
| **Replay-Tests** | Gespeicherte Parquet/SQLite-Logs. | **Reproduzierbarkeit.** Abspielen historischer Daten in Echtzeit oder beschleunigt (`--speed 10x`) und Vergleichen der Entscheidungen. |
| **A/B-Tuning** | Deadband-Längen, Forecast-Margins. | Vergleichen neuer **Policies** (z.B. neue Deadband-Länge) gegen eine Baseline (Historie) zur KPI-Optimierung. |

## 2. Der Replay-Runner (Audit & Forschung) 🎓

Dies ist das mächtigste Werkzeug, um die Determinismus-Anforderung zu prüfen.

* **Werkzeug:** `bitgrid-replay` CLI.
* **Funktion:** Nimmt ein Bundle aus historischen Parquet-Logs (`--state data/parquet/*.parq`) und einer Konfigurationsdatei (`--config config/rules.yaml`) entgegen und füttert den `Rule Engine Core` damit.
* **Audit:** Wenn ein Replay mit alten Logs und alter Config **nicht** die exakt gleichen `DecisionEvents` ergibt, ist ein Fehler im Code vorhanden.

## 3. Werkzeuge und Fault-Injection

Um das System unter Stress zu setzen, nutzen wir gezielte Fehler-Injektionen:

* **Fault-Injection:** Simulierte Ausfälle, die zu einem Notfall (R3) führen sollen.
    * *Beispiele:* `Sensor-Stale` (Datenfluss stoppt), `Broker-Down` (MQTT bricht zusammen), simulierte `Heat-Events`.
    * *Zweck:* Verifizieren, dass der **Circuit-Breaker** und die Not-Stopp-Kette korrekt greifen (siehe Runbooks in 08.5).
* **Feature-Flags:** Policies können zur Laufzeit über Feature-Flags im UI oder in der Config umgeschaltet werden (z.B. `r4_enabled=false`), um die Wirkung einzelner Regeln zu isolieren.

## 4. Erfolgskriterien (KPIs)

Die Wirkung der Tests und des Tunings messen wir über Kennzahlen:

| KPI | Zielwert | Zweck |
| :--- | :--- | :--- |
| **Decision Latency** | < 300 ms | Zeit zwischen Block-Tick und finaler Entscheidung (Performance des Cores). |
| **Explanation Latency** | < 2 s | Zeit zwischen `DecisionEvent` und der fertigen Text-Erklärung im UI (UX). |
| **Thermal Incidents** | 0 | Nach Updates oder neuen Konfigurationen darf R3 nicht ausgelöst werden. |
| **Flapping Rate (↓)** | Rückgang ggü. Baseline | Misst die Effizienz von R5. Hohe Rate $\rightarrow$ schlechte Stabilität. |
| **Grid Import (↓)** | Minimierung | Ökonomischer Erfolg. Wie gut nutzt das System den PV-Überschuss? |
| **Explanation Coverage** | 100 % | Jedes `DecisionEvent` muss einen gültigen `Reason` und `Trigger` enthalten (Auditierbarkeit). |

---
> **Nächster Schritt:** Wir können das System entwickeln, testen und simulieren. Nun fehlt nur noch der Weg in die Produktion.
>
> 👉 Weiter zu **[08.8 Build- & Release-Management](./088_build_managment.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
