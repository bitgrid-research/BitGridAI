# 02.1 - Technische Randbedingungen (Technical Constraints)

Willkommen auf dem Boden der Tatsachen. Hier steht, was nicht verhandelbar ist – der Rahmen, in den wir BitGridAI hineinschrauben muessen.

Diese Einschraenkungen kommen aus Kellerrealitaet, Local-First-Vision oder externen Vorgaben. Unsere Architektur muss innerhalb dieser Grenzen die beste Loesung finden, Punkt.

<img src="../../media/bithamster_technical.png" alt="Hamster tech" width="1000" />

## Die Liste der harten Fakten

| ID | Randbedingung | Beschreibung & Motivation |
| :--- | :--- | :--- |
| **TC-1** | **Deployment Target: Edge Device** | Laeuft auf guenstiger Commodity-Hardware im lokalen Netz.<br>Beispiele: Raspberry Pi, Intel NUC, Thin Clients.<br>Konsequenz: CPU/RAM/Abwaerme sind knapp, Effizienz ist Pflicht. |
| **TC-2** | **Zwingender Technologie-Stack** | Kern in **Python**, Transport via **MQTT**, Einbindung oft ueber **Home Assistant**.<br>Nur Open Source, keine proprietaeren Services. |
| **TC-3** | **Vorgegebene Persistenz** | Operationale Daten in **SQLite**, Historie/Logs als **Parquet** (append-only).<br>Ziel: Performance und Reproduzierbarkeit. |
| **TC-4** | **Offline-First Betrieb** | Keine Internetverbindung noetig fuer Regelung, Sicherheit, lokales UI.<br>Cloud ist optional; keine Telemetrie nach aussen. |
| **TC-5** | **Protokoll-Zoo Pflicht** | Muss Modbus TCP, MQTT und REST/HTTP sprechen, um Wechselrichter, Zaehler, Wallboxen anzubinden. |
| **TC-6** | **On-Device AI Inference** | Prognosen und Explain-Agent laufen lokal, optimiert fuer CPU-Inferenz auf Edge-Geraeten.<br>Keine Cloud-KI-APIs. |
| **TC-7** | **Lokale Sicherheit & Auth** | Auth lokal (z.B. via Home-Assistant-User), minimale offene Ports, keine Abhaengigkeit von externen Providern. |

---
> Nächster Schritt: Technik ist das eine, aber wer zahlt und wann muss es fertig sein?
> 
> Im nächsten Abschnitt kommen die organisatorischen Leitplanken.
> 
> 👉 Weiter zu **[02.2 - Organisatorische Randbedingungen](./022_organizational_constraints.md)**
> 
> 🔙 Zurück zur **[Kapiteluebersicht](./README.md)**
