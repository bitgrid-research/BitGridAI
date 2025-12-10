# 08.5 Fehler- & Ausnahmebehandlung

Wenn es knallt: Ruhe bewahren.

Fehler sind unvermeidlich, besonders im Zusammenspiel mit heterogener Hardware (Modbus, APIs, Netzwerk). Unser Ziel ist es nicht, Fehler zu verhindern, sondern sicherzustellen, dass sie **niemals** zu einem unsicheren Zustand führen oder das gesamte System zum Absturz bringen.

Das zentrale Prinzip ist **Graceful Degradation**: Das System muss in einen sicheren, erklärbaren Zustand übergehen und dort verharren, bis der Fehler behoben ist. Verfügbarkeit tritt hinter die Sicherheit zurück.

*(Platzhalter für ein Bild: Ein Hamster sitzt im Kontrollraum, der gerade einen roten Alarm zeigt. Der Hamster trägt eine Weste mit der Aufschrift "Keep Calm and Log It" und leitet den Fehler in ein separates Log um.)*
![Hamster behandelt Fehler](../../media/pixel_art_hamster_error_handling.png)

## 1. Das Fehlermanagement-Muster

Alle Fehler werden zentral behandelt und führen zu einem dieser definierten Zustände:

| Fehlertyp | Betroffene Komponente | Reaktion | Priorität |
| :--- | :--- | :--- | :--- |
| **Kritisch** | Hardware (R3), Adapter-Heartbeat | **Safety Stop** (R3), Circuit-Breaker, System-Lockout. | Höchste |
| **Degradiert** | Sensor-Stale, Zeitdrift, Forecast-Qualität | **Block Hold** (R5), Ignoriere Start-Befehle (R1), UI-Warnung. | Hoch |
| **Transient** | MQTT-Verbindung, REST-Timeout | **Retry** mit exponentiellem Backoff, Log-Eintrag. | Mittel |
| **Logisch** | Inkonsistente Daten, ungültige Config | **Frame verwerfen**, Letzten konsistenten State halten, Log-Eintrag. | Niedrig |

---

## 2. Patterns aus der Laufzeitsicht (Die Abwehrmechanismen)

Diese spezifischen Mechanismen stellen sicher, dass Fehler zu sicheren, erklärbaren Zuständen führen:

* **Adapterfehler & Circuit-Breaker:** Wenn ein Hardware-Adapter (z.B. Modbus Poller) nach mehreren **Retries** (mit exponentiellem Backoff) fehlschlägt, wird er über den **Circuit-Breaker** (Leistungsschutzschalter-Muster) temporär deaktiviert. Er wird erst nach Ablauf einer Wartezeit wieder reaktiviert. Führt der Fehler zur Persistenz (Datenkorruption), ist der Übergang zu **Stop $\rightarrow$ Safe** nötig.
* **Sensor-Stale:** Führt ein Fehler im Sensorpfad zu veralteten Daten, wird der `EnergyState` als unsicher markiert. Die Regel-Engine (R1) wird instruiert, nur **HOLD** oder **STOP** zu wählen, **niemals START** (Graceful Degradation).
* **Zeitdrift:** Ein kritischer Versatz der Systemzeit (z.B. > 5s Skew zur NTP-Zeit) führt zu einem 1 Block **HOLD**. Es erfolgt ein erzwungener NTP Re-Sync. Das ist wichtig, da der **BlockScheduler** auf der Wanduhr basiert.
* **Safety-Übersteuerung:** Kritische Fehler (Thermo/SoC-Limits) führen über die Regel R3 sofort zum **Stop**. Dies ignoriert alle Deadbands und Overrides.

## 3. Diagnose & Runbook-Hinweise

Jeder Fehler muss protokollierbar und nachstellbar sein (**Traceability**). Die Logs verweisen auf definierte Abläufe im Runbook (die aus Risikokapitel 10/11 stammen).

| Hinweis | Beschreibung | Zweck |
| :--- | :--- | :--- |
| **RB-01 Deadband-Tuning** | Flapping-Raten (wie oft R5 eingriff) per Replay prüfen und Schwellen anpassen. | Proaktive Stabilitätsverbesserung. |
| **RB-02 Safety Stop Drill** | Simulierte Überhitzung (Fault-Injection) auslösen und verifizieren, dass das korrekte `DecisionEvent R3` mit UI-Alarm ausgelöst wird. | Verifikation der Sicherheitskette. |
| **RB-03 Drift Recovery** | Skew der Systemzeit simulieren und beobachten, ob der `BlockScheduler` in den Hold-Mode geht und korrekt re-synchronisiert. | Verifikation der Zeitstabilität. |
| **RB-04 Explain Audit** | `DecisionEvents` und `ExplainSessions` über das `/research/export` Bundle prüfen. | Überprüfung der Transparenz (Wurde der Fehler richtig erklärt?). |

---
> **Nächster Schritt:** Wir können Fehler behandeln. Jetzt müssen wir sicherstellen, dass wir auch im Normalbetrieb wissen, was passiert ist.
>
> 👉 Weiter zu **[08.6 Logging & Tracing](./086_logging_and_tracing.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
