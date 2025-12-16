# 06.01 - Szenario: Normaler Start (Regel R1)

Der Klassiker: Die Sonne scheint, der Miner läuft.

Dies ist der "Happy Path" von BitGridAI. Wir beschreiben hier den Standard-Ablauf, bei dem das System einen PV-Überschuss erkennt und basierend auf Regel **R1 (Profitability)** entscheidet, das Mining zu starten.

Hier greifen alle Zahnräder ineinander: Sensoren, State, Scheduler, Regeln und Aktoren.

*(Platzhalter für ein Bild: Die Sonne scheint auf das Haus, die Batterien sind grün, und der Hamster legt gut gelaunt den großen Hebel auf "ON".)*
![Hamster startet das Mining](../../media/pixel_art_hamster_mining_start.png)

&nbsp;

## Sequenzdiagramm (Der Ablauf)

Wie wird aus Sonnenstrahlen Hashrate?

```mermaid
sequenceDiagram
    participant PV as ☀️ PV/Sensor
    participant MQTT as 📡 MQTT/Adapter
    participant SSoT as 🧠 EnergyState
    participant Sched as ⏱️ BlockScheduler
    participant Rules as 📜 RuleEngine (R1)
    participant Miner as ⛏️ Miner/Adapter
    participant UI as 🖥️ UI/User

    Note over PV, UI: 1. Sensing & State Update
    PV->>MQTT: Publish 4000W Power
    MQTT->>SSoT: Update p_pv_kw=4.0
    SSoT->>SSoT: Recalc Surplus (avg)

    Note over Sched, Rules: 2. Scheduling (New Block)
    Sched->>Sched: Wait for 10-Min Tick
    Sched->>Rules: Trigger Eval (Block #N)

    Note over Rules: 3. Decision (R1)
    Rules->>SSoT: Get State (Surplus & Price)
    Rules->>Rules: Check: Surplus > 1.5kW AND Price < 18ct?
    Rules-->>Rules: YES -> Action: START

    Note over Rules, Miner: 4. Actuation & Explanation
    Rules->>Miner: CMD: start / set_power
    Rules->>UI: DecisionEvent (Reason: "Surplus high")
    
    Note right of UI: Toast: "Mining started via R1"
    Note right of UI: Preview: "Valid for next 10 mins"
````

&nbsp;

## Wichtige Konfigurations-Parameter (MVP)

Damit dieser Ablauf funktioniert, sind folgende Schwellenwerte im System hinterlegt:

| Parameter | Wert (Beispiel) | Beschreibung |
| :--- | :--- | :--- |
| `surplus_min_kw` | **1.5 kW** | Mindest-Überschuss (gleitender Durchschnitt), damit R1 feuert. |
| `price_max_ct_kwh` | **18 ct/kWh** | Die "Schmerzgrenze" beim Strompreis. Darüber bleibt der Miner aus. |
| `min_runtime_blocks` | **2 Blöcke** | (20 Min) Mindestlaufzeit nach Start, um die Hardware zu schonen (Short-Cycling-Schutz). |
| `deadband_hold_blocks` | **2 Blöcke** | (20 Min) Nach dem Einschalten wird dieser Zustand "festgehalten" (siehe Regel R5), um Flapping zu verhindern. |

&nbsp;

---
> **Nächster Schritt:** Das war der Idealfall bei schönem Wetter. Aber was passiert, wenn plötzlich eine kritische Grenze überschritten wird?
>
> 👉 Weiter zu **[06.2 Autarkie-Schutz (R2)](./062_autarky_protection.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
