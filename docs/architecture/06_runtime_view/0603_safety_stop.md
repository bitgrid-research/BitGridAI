# 06.03 Szenario: Sicherheitsstopp (Safety Stop - R3)

Die Notbremse.

Während sich BitGridAI normalerweise gemütlich im 10-Minuten-Takt bewegt, gibt es Situationen, die keinen Aufschub dulden. Regel **R3 (Thermal & Safety)** ist der Schutzengel der Hardware.

Sie überwacht kritische Systemparameter in Echtzeit. Wenn eine rote Linie überschritten wird, wartet das System nicht auf den nächsten Block, sondern zieht sofort den Stecker.

*(Platzhalter für ein Bild: Der Hamster in Feuerwehrmontur steht vor einem rauchenden Server-Rack und haut mit einem großen Hammer auf einen roten "NOT-AUS"-Knopf.)*
![Hamster drückt Not-Aus](../../media/pixel_art_hamster_emergency.png)

## Kurzüberblick

> **Der Ablauf in Kürze:**
> Kritischer Grenzwert (Temp/Heartbeat) verletzt → **Sofortiger Interrupt** (umgeht Takt) → **R3 feuert** → Hard Stop → **Lockout-Modus** aktiviert.

> **TL;DR (EN):**
> Critical threshold breached → Immediate interrupt (bypassing scheduler) → R3 fires → Hard stop → System enters lockout mode.

---

## Sequenzdiagramm (Der Notfall)

Hier sehen wir, wie die synchrone Abarbeitung durch ein asynchrones Event unterbrochen wird.

```mermaid
sequenceDiagram
    participant Hardware as 🔥 Miner/Sensor
    participant Watchdog as 🐕 SafetyWatchdog (R3)
    participant SSoT as 🧠 EnergyState
    participant Sched as ⏱️ BlockScheduler
    participant Actuator as 🔌 Adapter/Relais
    participant UI as 🖥️ UI/User

    Note over Hardware, Watchdog: Asynchrone Überwachung
    Hardware->>Watchdog: Temp = 82°C (Critical!)
    
    critical R3 INTERRUPT
        Note over Watchdog, Actuator: R3 umgeht den Scheduler!
        Watchdog->>Watchdog: Check: 82°C > 80°C Limit?
        Watchdog->>Actuator: IMMEDIATE STOP COMMAND
        Actuator->>Hardware: Power OFF
    end

    Watchdog->>SSoT: Set State = ERROR / SAFE_MODE
    Watchdog->>UI: Alert: "Overheating! Stopped."
    
    Note over Sched: 3 Minuten später...
    Sched->>SSoT: Trigger Next Block?
    SSoT-->>Sched: Denied (System is in Safe Mode)
````
    
## Detaillierte Prozessschritte

### 1. Überwachung (Der Watchdog) 🐕
Im Gegensatz zu den Regel-Geschwistern (R1, R2, R4, R5), die friedlich schlafen, bis der Scheduler sie alle 10 Minuten weckt, schläft R3 nie.
* **Mechanismus:** Ein separater Hintergrundprozess (Thread oder Service) überwacht kontinuierlich die Telemetrie-Daten der Hardware.
* **Frequenz:** Prüfung erfolgt im Sekunden-Takt (z.B. alle 5s).

### 2. Auslösung (Der Alarm) 🚨
Sobald ein definierter Grenzwert verletzt wird, wird der Prozess zur "Fast Lane".
* **Trigger A (Hitze):** `chip_temp > max_chip_temp_c`. Die Hardware kocht.
* **Trigger B (Verbindungsverlust):** Seit $X$ Sekunden keine Daten vom Miner (`last_heartbeat > comm_timeout`). Wir fliegen blind – das ist verboten.
* **Trigger C (Externer Not-Aus):** Ein User drückt den "Emergency Button" im UI oder Home Assistant.

### 3. Reaktion (Der Kill Switch) ⚡
R3 kennt keine Diskussion und keine "Deadbands".
* **Immediate Action:** Der `Actuation Adapter` sendet sofort den Befehl `STOP` an die API. Parallel wird (falls vorhanden) das smarte Relais (Smart Plug) hart ausgeschaltet.
* **Scheduler Bypass:** R3 ignoriert alle laufenden "Valid-Until"-Timer. Sicherheit sticht Stabilität.
* **User Alert:** Eine Push-Notification ("🔥 Overheat Alert") geht raus.

### 4. Lockout (Safe Mode) 🔒
Nach dem Crash ist vor dem Start – aber nicht sofort.
* **Zustandswechsel:** Der `EnergyState` wechselt auf `ERROR` oder `SAFE_MODE`.
* **Konsequenz:** In diesem Zustand ignoriert die Rule Engine alle Start-Versuche durch R1 (Profitability).
* **Reset:** Das System bleibt gesperrt, bis:
    1.  Die "Cool-down"-Zeit (`safety_lockout_min`) abgelaufen ist.
    2.  UND der Fehlergrund verschwunden ist (Temp < Limit - Hysterese).
    3.  (Optional) Ein Admin den Fehler manuell quittiert.

---

## Wichtige Konfigurations-Parameter (MVP)

Sicherheit ist nicht verhandelbar, aber konfigurierbar. Diese Werte schützen die Investition:

| Parameter | Wert (Beispiel) | Beschreibung |
| :--- | :--- | :--- |
| `max_chip_temp_c` | **80°C** | Absolute Obergrenze. Ein Grad mehr, und der Miner steht. |
| `comm_timeout_sec` | **60 Sek** | "Dead Man's Switch". Wenn wir solange nichts vom Gerät hören, gehen wir vom Schlimmsten aus (Lüfterausfall/Absturz) $\rightarrow$ Stop. |
| `safety_lockout_min` | **60 Min** | Mindest-Wartezeit nach einem Not-Stopp ("Abkühlphase"), bevor ein automatischer Neustart überhaupt erst wieder versucht wird. |

---
> **Nächster Schritt:** Sicherheit ist gewährleistet. Jetzt machen wir das System schlau. Wir schauen nicht nur auf das "Jetzt", sondern auch in die Zukunft.
>
> 👉 Weiter zu **[06.4 Prognose-Optimierung (R4)](./064_forecast_control.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
