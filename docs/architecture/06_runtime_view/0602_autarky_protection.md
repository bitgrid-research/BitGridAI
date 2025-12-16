# 06.02 - Szenario: Autarkie-Schutz (Regel R2)

Das Haus hat Vorfahrt.

BitGridAI ist ein "Good Citizen" im Hausnetz. Das bedeutet: Wir klauen dem Haushalt keinen Strom. Regel **R2 (Autarkie)** ist der Wächter, der einschreitet, wenn der Hausakku leerläuft oder wir teuren Strom aus dem Netz ziehen müssten.

R2 hat eine **höhere Priorität** als R1. Selbst wenn Mining profitabel wäre (R1=True), kann R2 ein Veto einlegen ("Ja, aber wir haben keinen Strom übrig").

*(Platzhalter für ein Bild: Der Hamster stellt sich schützend vor die Hausbatterie und hält dem Miner ein Stoppschild hin.)*
![Hamster schützt die Batterie](../../media/pixel_art_hamster_battery_guard.png)

&nbsp;

## Der Ablauf (Sequenz)

1.  **Sensing:** Der Smart Meter meldet plötzlich hohen Netzbezug (jemand hat den Herd eingeschaltet) ODER der Batteriespeicher meldet einen niedrigen Ladestand (SoC).
2.  **Trigger:** Der 10-Minuten-Takt (oder ein Sofort-Interrupt bei kritischen Werten).
3.  **Evaluation (R2):**
    * Ist `grid_import > 500W`?
    * ODER ist `battery_soc < 20%`?
    * *Ergebnis:* **STOP MINING**.
4.  **Action:** Der Miner wird sanft heruntergefahren oder pausiert.
5.  **Explanation:**
    * `Reason`: "Priority to Household"
    * `Trigger`: "SoC 19% < 20% Limit"

&nbsp;

## Konfiguration (MVP)

| Parameter | Wert (Beispiel) | Beschreibung |
| :--- | :--- | :--- |
| `min_home_soc_pct` | **20 %** | Unterhalb dieses Ladestands darf nicht gemint werden, um Reserve für die Nacht zu lassen. |
| `max_grid_import_w` | **500 W** | Toleranzgrenze. Wenn wir mehr als das aus dem Netz ziehen, muss der Miner aus. |

---
> **Nächster Schritt:** Was ist, wenn nicht der Strom fehlt, sondern die Hardware glüht? Dann greift die höchste Instanz.
>
> 👉 Weiter zu **[06.03 Sicherheitsstopp (R3)](./0603_safety_stop.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
