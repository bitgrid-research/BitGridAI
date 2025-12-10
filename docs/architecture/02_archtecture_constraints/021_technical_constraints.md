# 021 – Technische Rahmenbedingungen / Technical Constraints

TODO: Harte Fakten zur Technik. Welche Hardware ist vorgegeben? Welche Betriebssysteme oder externen APIs müssen wir zwingend nutzen?

# 02.1 Technische Randbedingungen (Technical Constraints)

Willkommen auf dem Boden der Tatsachen.

Hier listen wir die technischen Vorgaben auf, die für **BitGridAI** "in Stein gemeißelt" sind. Diese Einschränkungen sind nicht verhandelbar. Sie ergeben sich aus der physischen Realität im Keller des Nutzers, der definierten Produktvision ("Local-First") oder externen Standards, denen wir uns beugen müssen.

Unsere Architektur muss innerhalb dieser Grenzen eine optimale Lösung finden.

## Die Liste der harten Fakten

| ID | Randbedingung | Beschreibung & Motivation |
| :--- | :--- | :--- |
| **TC-1** | **Deployment Target: Edge Device** 🍓 | Das gesamte System muss auf handelsüblicher, günstiger ("Commodity") Hardware im lokalen Netzwerk laufen. <br>**Beispiele:** Raspberry Pi 4/5, Intel NUC, Odroid oder vergleichbare Mini-PCs.<br>**Konsequenz:** Wir haben begrenzte Ressourcen (CPU, RAM, Abwärme) im Vergleich zur Cloud. Die Software muss effizient sein. |
| **TC-2** | **Betrieb ohne Internet (Offline-First)** 🛡️ | Eine aktive Internetverbindung ist *keine* Voraussetzung für den Kernbetrieb (Regelung, Sicherheit, lokales UI).<br>**Motivation:** Maximale Resilienz und Autarkie. Wenn das Internet ausfällt, muss das Haus weiter intelligent gesteuert werden. Cloud-Dienste sind nur "Nice-to-have" Add-ons (z.B. für externe Updates). |
| **TC-3** | **Heterogene Geräte-Landschaft (Protokoll-Zoo)** 🗣️ | Wir können uns die Hardware der Nutzer nicht aussuchen. Das System muss zwingend die gängigsten Industrieprotokolle sprechen, um mit Wechselrichtern, Zählern und Wallboxen zu kommunizieren.<br>**Pflicht-Protokolle:** Modbus TCP (Industriestandard), MQTT (IoT-Standard), REST/HTTP (moderne APIs), EEBUS (optional, aber wichtig für E-Mobilität). |
| **TC-4** | **On-Device AI Inference** 🧠 | Das KI-Modell für die Prognosen (Wetter/Verbrauch) muss lokal auf dem Edge Device ausgeführt werden (Inferenz).<br>**Konsequenz:** Wir können keine riesigen LLMs oder Cloud-KI-APIs nutzen. Die Modelle müssen klein, quantisiert (z.B. TensorFlow Lite, ONNX Runtime) und auf CPU-Inferenz optimiert sein. |
| **TC-5** | **Mining-Hardware Schnittstelle** ⛏️ | Die Ansteuerung der Bitcoin-Miner (ASICs) muss über deren native Schnittstellen erfolgen.<br>**Vorgabe:** Nutzung von Standard-Management-APIs der Miner (oft proprietäre REST/JSON-APIs oder SSH-Befehle) sowie des Stratum-Protokolls zur Überwachung der Hashrate. Das System muss einen harten "Power Switch" oder eine dynamische Drosselung (sofern vom Miner unterstützt) umsetzen können. |
| **TC-6** | **Container-basierte Laufzeitumgebung** 🐳 | Um die Installation auf verschiedenen Linux-basierten Host-Systemen (z.B. Raspbian, Ubuntu, umbrelOS) zu gewährleisten, wird die Auslieferung als Docker-Container (oder kompatibel, z.B. Podman) vorausgesetzt.<br>**Motivation:** Reproduzierbarkeit und einfacheres "Plug & Play" Deployment für den Endanwender. |
---
---

> **Kurzüberblick:**  
> **Local-first**, **Open-Source-Stack**, deterministische **R1–R5**, **10-Min-Blocktakt**, Explainability & Logging als Pflicht, keine Cloud-Abhängigkeiten.

> **TL;DR (EN):**  
> Local-first, open-source, deterministic rules (R1–R5) on a 10-minute cadence; explainability + logging mandatory; no cloud dependencies.

---

| Bereich | Beschreibung |
| --- | --- |
| **Lokale Ausführung** | Alle Verarbeitung auf Nutzerhardware (Pi/NUC/ThinClient); offline-fähig. |
| **Open-Source-Stack** | Python, MQTT, Home Assistant, SQLite/Parquet; keine proprietären Services. |
| **Modularität** | Erweiterbar über lokale Adapter (MQTT/REST/Modbus) ohne Kernlogik zu ändern. |
| **Single Source of Truth** | **EnergyState** als einziger Schreiber für Messwerte, Prognosen, Preise, SoC, Temperaturen. |
| **Deterministische Regelengine** | **R1–R5** ohne Black-Box-ML im Regelpfad; Priorität R3>R2>R5>R1/R4. |
| **Block-Scheduler** | Entscheidungen im **10-Minuten-Takt**; `valid_until`-Deadbands für Stabilität. |
| **Explain-Agent (On-Device LLM)** | Microcopy & What-if lokal; keine Cloud-Abfragen. |
| **Safety & Fail States** | Harte Limits (SoC/Temperatur) → **Stop → Safe**; kein OC/UV am Miner. |
| **Logging & KPIs** | Append-only (SQLite/Parquet/JSON); Research-Toggle steuert Export/Replay. |
| **Security/Privacy** | Keine Telemetrie nach außen; minimale Ports; lokale Auth (z. B. HA-User). |

> Local execution, FOSS stack, modular adapters, EnergyState as SSoT, deterministic R1–R5, 10-min scheduler, on-device explain agent, safety-first, append-only logging, privacy-by-default.
