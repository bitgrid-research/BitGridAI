## 02.1 – Technische Randbedingungen (Technical Constraints)

Willkommen auf dem Boden der Tatsachen.  
Hier steht, was **nicht verhandelbar** ist – der Rahmen, in den BitGridAI hineingeschraubt wird.

Diese Einschränkungen ergeben sich aus Kellerrealität, Local-First-Vision und externen Vorgaben.  
Die Architektur muss **innerhalb dieser Grenzen** die bestmögliche Lösung liefern. Punkt.

<img src="../../media/bithamster_technical.png" alt="Hamster tech" width="1000" />

## Die Liste der harten Fakten

| ID | Randbedingung | Beschreibung & Motivation |
| :-- | :-- | :-- |
| **TC-1** | **Deployment-Ziel: Edge Device** | Läuft auf günstiger Commodity-Hardware im lokalen Netz.<br>Beispiele: Raspberry Pi, Intel NUC, Thin Clients.<br>Konsequenz: Begrenzte CPU/RAM/Abwärme → Effizienz ist Pflicht. |
| **TC-2** | **Fester Technologie-Stack** | Kernlogik in **Python**, Transport via **MQTT**, Integration häufig über **Home Assistant**.<br>Ausschließlich Open Source, keine proprietären Services. |
| **TC-3** | **Vorgegebene Persistenz** | Operationale Daten in **SQLite**, Historie und Logs als **Parquet** (append-only).<br>Ziel: Deterministische Performance und Reproduzierbarkeit. |
| **TC-4** | **Offline-First-Betrieb** | Keine Internetverbindung erforderlich für Regelung, Sicherheit oder lokales UI.<br>Cloud optional; keine verpflichtende Telemetrie nach außen. |
| **TC-5** | **Multi-Protokoll-Anforderung** | Unterstützung für **Modbus TCP**, **MQTT** und **REST/HTTP** zur Anbindung von Wechselrichtern, Zählern und Wallboxen. |
| **TC-6** | **On-Device-AI-Inferenz** | Prognosen und Explain-Agent laufen lokal, optimiert für CPU-Inferenz auf Edge-Geräten.<br>Keine Cloud-KI-APIs. |
| **TC-7** | **Lokale Sicherheit & Authentifizierung** | Authentifizierung lokal (z. B. über Home-Assistant-User), minimale offene Ports,<br>keine Abhängigkeit von externen Identity-Providern. |

---

> Nächster Schritt: Technik ist das eine – aber wer zahlt, und wann muss es fertig sein?
>
> Im nächsten Abschnitt folgen die organisatorischen Leitplanken.
>
> 👉 Weiter zu **[02.2 – Organisatorische Randbedingungen](./022_organizational_constraints.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
