# 02.1 Technische Randbedingungen (Technical Constraints)

Willkommen auf dem Boden der Tatsachen.

Hier listen wir die technischen Vorgaben auf, die für **BitGridAI** "in Stein gemeißelt" sind. 

Diese Einschränkungen sind nicht verhandelbar. Sie ergeben sich aus der physischen Realität im Keller des Nutzers, der definierten Produktvision ("Local-First") oder externen Standards, denen wir uns beugen müssen.

Unsere Architektur muss innerhalb dieser Grenzen eine optimale Lösung finden.

![Hamster lötet im Keller am Edge-Device](link_zu_image_40.png)

## Die Liste der harten Fakten

| ID | Randbedingung | Beschreibung & Motivation |
| :--- | :--- | :--- |
| **TC-1** | **Deployment Target: Edge Device** 🍓 | Das gesamte System muss auf handelsüblicher, günstiger ("Commodity") Hardware im lokalen Netzwerk laufen. <br>**Vorgegebene Beispiele:** Raspberry Pi, Intel NUC oder ThinClients.<br>**Konsequenz:** Begrenzte Ressourcen (CPU, RAM, Abwärme). Die Software muss effizient sein. |
| **TC-2** | **Zwingender Technologie-Stack** 🛠️ | Die Kernentwicklung ist auf einen spezifischen Open-Source-Stack festgelegt.<br>**Vorgabe:** Die Implementierung erfolgt primär in **Python**. Die Kommunikation läuft über **MQTT**. Die Integration in das Heimnetzwerk erfolgt (oft) über **Home Assistant**. Es dürfen keine proprietären Services genutzt werden. |
| **TC-3** | **Vorgegebene Persistenz-Technologie** 💾 | Die Art und Weise, wie Daten gespeichert werden, ist festgelegt, um Performance und Reproduzierbarkeit zu sichern.<br>**Vorgabe:** Operationale Daten (z.B. der EnergyState) landen in **SQLite**. Historische Daten und Logs für Analysen werden im **Parquet**-Format (Append-only) gespeichert. |
| **TC-4** | **Betrieb ohne Internet (Offline-First)** 🛡️ | Eine aktive Internetverbindung ist *keine* Voraussetzung für den Kernbetrieb (Regelung, Sicherheit, lokales UI).<br>**Motivation:** Maximale Resilienz und Autarkie. Cloud-Dienste sind nur optionale Add-ons. Es findet keine Telemetrie nach außen statt. |
| **TC-5** | **Heterogene Geräte-Landschaft (Protokoll-Zoo)** 🗣️ | Das System muss zwingend die gängigsten Industrieprotokolle sprechen, um mit Wechselrichtern, Zählern und Wallboxen zu kommunizieren.<br>**Pflicht-Protokolle:** Modbus TCP, MQTT, REST/HTTP. |
| **TC-6** | **On-Device AI Inference** 🧠 | Das KI-Modell für Prognosen und der "Explain-Agent" (On-Device LLM) müssen lokal ausgeführt werden.<br>**Konsequenz:** Keine Nutzung von Cloud-KI-APIs. Modelle müssen für CPU-Inferenz auf Edge-Geräten optimiert sein. |
| **TC-7** | **Lokale Sicherheit & Auth** 🔒 | Sicherheit darf nicht von externen Providern abhängen.<br>**Vorgabe:** Die Authentifizierung erfolgt lokal (z.B. über vorhandene Home Assistant User). Es werden nur minimale Netzwerk-Ports nach außen geöffnet. |

---

> **Nächster Schritt:** Technik ist das eine, aber wer bezahlt das Ganze und wann muss es fertig sein? Im nächsten Abschnitt schauen wir uns die organisatorischen Rahmenbedingungen an.
>
> 👉 Weiter zu **[02.2 Organisatorische Randbedingungen](./022_organizational_constraints.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
