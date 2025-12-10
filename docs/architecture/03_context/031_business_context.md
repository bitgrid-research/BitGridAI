# 03.1 Fachlicher Kontext (Business Context)

Wer redet hier mit wem?

Bevor wir Kabel ziehen, müssen wir verstehen, welche Akteure ein Interesse an **BitGridAI** haben und welche Informationen fließen müssen. Hier betrachten wir das System als "Blackbox" in seiner natürlichen Umgebung.

Wir fragen uns: Welche Ereignisse von außen wecken das System auf? Und wen informiert das System, wenn es fertig ist?

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster steht am Gartenzaun und unterhält sich mit seinen Nachbarn: Einer Person (Nutzer), einer Sonne (Wetter) und einem Strommast (Netz).)*
![Hamster und die Nachbarn](../media/pixel_art_hamster_neighbors.png)

## Die fachlichen Nachbarn

Wir interagieren mit fünf Hauptakteuren. Die folgende Tabelle zeigt, was diese Nachbarn von uns erwarten und was sie uns liefern:

| Kommunikationspartner | Was kommt rein? (Input) | Was geht raus? (Output) | Beziehung & Beschreibung |
| :--- | :--- | :--- | :--- |
| **Der Prosumer (Nutzer) 🏠** | **Ziele & Befehle:** <br>• Präferenzen (z.B. "Auto morgen früh voll")<br>• Manuelle Overrides ("Boost jetzt!")<br>• Config-Updates | **Transparenz:** <br>• Echtzeit-Dashboard (Flows)<br>• Erklärungen ("Warum läuft der Miner?")<br>• Warnungen (Alerts) | Der Mensch, dem das Haus gehört. Er will Komfort und Rendite, aber keine Arbeit. Er ist der "Chef", dessen Befehle (Overrides) Vorrang vor der Automatik haben. |
| **Die Umwelt (Wetter & Zeit) ☀️** | **Fakten:** <br>• Globalstrahlung (Sonne)<br>• Außentemperatur<br>• Zeit (Block-Takt) | *– (Nichts)* | Der wichtigste externe Taktgeber. Die Sonne diktiert die Produktion, die Zeit diktiert den 10-Minuten-Block. Wir können die Umwelt nicht beeinflussen, nur auf sie reagieren. |
| **Das Öffentliche Stromnetz (Grid) ⚡** | **Energie:** <br>• Netzstrom (bei Mangel)<br>• Dynamische Preise (optional) | **Energie & Entlastung:** <br>• Überschuss-Einspeisung<br>• Netzdienliches Verhalten (Peak Shaving) | Der "Puffer". BitGridAI versucht, die Interaktion mit dem Netz zu minimieren (Autarkie) oder zu optimieren (günstig laden), aber das Netz ist der Fallback für die Versorgungssicherheit. |
| **Der Mining-Pool ⛏️** | **Arbeitspakete:** <br>• Stratum Jobs (Difficulty) | **Rechenleistung (Hashes):** <br>• Validierte Shares (Proof-of-Work) | **Wichtig:** BitGridAI steuert nur die Hardware. Die finanzielle Belohnung (Payout) erfolgt vom Pool *direkt* an das Wallet des Nutzers (Non-Custodial). Wir liefern Shares, der Pool liefert Sats (an den Nutzer). |
| **Forschung & Wissenschaft 🎓** | *– (Nichts im Betrieb)* | **Daten:** <br>• Anonymisierte Logs (Parquet)<br>• Replay-Exports | Passiver Konsument. Wenn der Nutzer zustimmt (Opt-in), werden hochauflösende, bereinigte Daten für wissenschaftliche Auswertungen bereitgestellt. |

## Externe Auslöser (Business Events)

Wann muss BitGridAI aktiv werden? Wir unterscheiden drei Arten von Ereignissen:

1.  **Zeit-Trigger (Der Herzschlag):**
    * Alle 10 Minuten startet ein neuer **Block**. Das System wacht auf, liest Sensoren, berechnet die Strategie und setzt die Aktoren neu. (Das ist der Standard-Modus).

2.  **Daten-Trigger (Die Veränderung):**
    * **Wetterumschwung:** Eine dicke Wolke zieht auf → PV-Leistung bricht ein → System muss im nächsten Block reagieren (z.B. Miner stoppen).
    * **Preisänderung:** Der dynamische Stromtarif wird günstiger → Strategie ändert sich auf "Laden".

3.  **Nutzer-Trigger (Der Eingriff):**
    * **Override:** Der Nutzer drückt "E-Auto jetzt laden". Das System bricht den aktuellen Plan sofort ab (unterbricht ggf. den 10-Min-Takt oder wartet auf das nächste Fenster, je nach Prio) und führt den Befehl aus.

---
> **Nächster Schritt:** Wir kennen die Akteure. Jetzt schauen wir unter die Haube: Über welche Leitungen und Protokolle sprechen wir mit ihnen?
>
> 👉 Weiter zu **[03.2 Technischer Kontext](./032_technical_context.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
