# 08.4 Plausibilitäts- & Validitätsprüfungen

Vertrauen ist gut, Kontrolle ist besser.

In unserem System ist die Qualität der Entscheidungen direkt von der Qualität der Sensordaten abhängig (**GIGO: Garbage In, Garbage Out**). Nur valide Mess- und Prognosedaten dürfen in den **EnergyState** und damit in die Regel-Engine (R1–R5) einfließen.

Daher gibt es eine dedizierte **Validierungs-Schicht** direkt hinter den Adaptern, die jeden Input lokal prüft.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster steht vor einem komplexen Datenfilter, der fehlerhafte Werte aussortiert und nur saubere Datenpakete durchlässt.)*
![Hamster prüft Datenfilter](../../media/pixel_art_hamster_data_filter.png)

## Das Validitäts-Prinzip

Die Validierung erfolgt, bevor die Daten den `EnergyState` (SSoT) erreichen. Das Ziel ist es, den Core mit der bestmöglichen, bereinigten Version der Realität zu versorgen.

### Die zentralen Checks

1.  **Sensor-Stale & Lücken:**
    * **Prüfung:** Sind alle kritischen Messwerte (PV, Grid, SoC) in den letzten $X$ Sekunden eingegangen?
    * **Maßnahme:** Fehlt ein Frame oder ist er zu alt, wird der gesamte State als **unsicher** markiert. Die Regel-Engine wird angewiesen, den Status **HOLD** zu wählen, statt eine Aktion (START) auszuführen. Das UI zeigt einen `Health-Banner`.

2.  **Range-Prüfungen (Grenzen):**
    * **Prüfung:** Liegt der Wert im physikalisch oder vertraglich erlaubten Bereich?
    * **Beispiele:** `soc_pct` muss zwischen 0.0 und 100.0 liegen. `t_miner_c` darf 100°C nicht überschreiten.
    * **Maßnahme:** Out-of-Range-Werte werden gekappt oder verworfen.

3.  **Hysterese (Ping-Pong-Vermeidung):**
    * **Prüfung:** Nutzen wir Hysterese, um den "Ping-Pong-Effekt" um Schwellenwerte zu vermeiden?
    * **Beispiele:** Wir stoppen das Mining bei `soc_stop_pct = 25%`, dürfen aber erst bei `soc_resume_pct = 30%` wieder starten. Dies gilt auch für Temperatur-Limits (`t_stop_c / t_resume_c`).

4.  **Forecast-Qualität (Confidence):**
    * **Prüfung:** Wie verlässlich ist die Prognose, die R4 nutzen soll?
    * **Maßnahme:** Der Forecast-Dienst muss eine `forecast_confidence` (z.B. $\ge 0.7$) liefern, sonst wird die Prognose verworfen und R4 ignoriert (wir handeln nur nach Ist-Werten R1/R2).

5.  **Adapter-Heartbeat (Liveness):**
    * **Prüfung:** Melden die Adapter (MQTT, Modbus) regelmäßig ihre Liveness?
    * **Maßnahme:** Bei Ausbleiben eines Heartbeats (> 60s) wird ein **Circuit-Breaker** im Actuation-Pfad aktiviert und das System geht in den `ERROR`-Zustand über (siehe R3).

6.  **Config-Schema:**
    * **Prüfung:** Die `config.yaml` muss beim Start gegen ein striktes Schema validiert werden.
    * **Transparenz:** Die Konfiguration wird gehasht und die Version ist im UI sichtbar, um Nachvollziehbarkeit zu gewährleisten ("Welche Regeln galten, als X passierte?").

## Auswirkungen auf den `EnergyState` und die Regeln

Die Validierung hält den deterministischen Regelpfad (R1–R5) sauber und vorhersehbar.

* **Stabilität (R5):** Ein ungültiger oder unsicherer `EnergyState` verstärkt die Entscheidung von R5, den Zustand zu halten (`HOLD`), statt unnötige Schaltvorgänge auszulösen.
* **Safety Stop (R3):** Das Versagen des `Adapter-Heartbeat` führt direkt zur Notfallbehandlung von R3, da wir die Basis für jede sichere Steuerung verloren haben.

## Spezifische Validierungsregeln

| Messwert | Regel | Maßnahme bei Verletzung |
| :--- | :--- | :--- |
| **`p_grid_kw`** | Muss kleiner sein als `grid_cap_kw` und im erwarteten Bereich der Zählertoleranz liegen. | Kappen auf Max-Wert (Hard Limit). |
| **`p_pv_kw`** | Muss $\leq$ Nennleistung der Anlage sein. Plausibilitäts-Check: Ist es Nacht? Dann muss der Wert nahe Null sein. | Verwerfen (Nachts > 500W ist Sensor-Fehler). |
| **`soc_pct`** | Muss in $[0.0, 100.0]$ sein. | Kappen auf 0.0 oder 100.0. |

---
> **Nächster Schritt:** Wir wissen, wie wir Daten sicher bekommen. Aber was, wenn die Software selbst Fehler macht oder eine unerwartete Ausnahme auftritt?
>
> 👉 Weiter zu **[08.5 Fehler- & Ausnahmebehandlung](./085_error_and_exception_handling.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
