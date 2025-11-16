# 08 – Querschnittliche Konzepte / Crosscutting Concepts

> **Kurzüberblick:**
>
> Systemweite Leitplanken: **Erklärbarkeit**, **Datentransparenz**, **Nachhaltigkeit**, **Sicherheit & Autonomie**, **menschzentrierte Interaktion** – alles **lokal**, nachvollziehbar, ohne Cloud. Mechanismen: Reasons/Trigger/Parameter, append-only Logs (SQLite/JSON), Deadband/Hysterese, lokale Auth & Offline-Fallback, Overrides & Research-Mode.

> **TL;DR (EN):**
>
> System-wide guardrails: **explainability**, **data transparency**, **sustainability**, **security & autonomy**, **human-centered interaction** – all **local**, auditable, no cloud. Mechanisms: reasons/trigger/parameters, append-only logs (SQLite/JSON), deadband/hysteresis, local auth & offline fallback, overrides & research mode.

---

## Überblick / Overview

Dieses Kapitel beschreibt die systemweit geltenden Konzepte und Prinzipien von BitGridAI. Sie sind unabhängig von spezifischen Modulen und stellen sicher, dass das System **nachvollziehbar, sicher und nachhaltig** bleibt – über Architekturgrenzen hinweg.

> This chapter defines the system-wide concepts and principles of BitGridAI. They apply across all modules and ensure that the system remains **traceable, secure, and sustainable** beyond architectural boundaries.

---

## Erklärbarkeit / Explainability

BitGridAI integriert **Explainable AI (XAI)** und HCI-Prinzipien direkt in die Steuerlogik. Jede Entscheidung wird kontextualisiert, begründet und über die Erklärschnittstelle sichtbar gemacht. Damit werden Aktionen **nicht nur automatisiert, sondern auch verständlich**.

> BitGridAI integrates **Explainable AI (XAI)** and HCI principles directly into its control logic. Every decision is contextualized, justified, and made visible through the explanation interface. This ensures that actions are **not only automated but also understandable**.

**Kernmechanismen:**

* Automatische Generierung von Entscheidungsbegründungen
* Visuelle Hervorhebung von Regelkonflikten
* Zeitliche Rückverfolgung (Decision History)
* Nutzungsschnittstelle für Feedback und Override

> **Core mechanisms:**
>
> * Automatic generation of decision rationales
> * Visual highlighting of rule conflicts
> * Temporal traceability (decision history)
> * User interface for feedback and override

---

## Datentransparenz / Data Transparency

Daten werden lokal verarbeitet und in nachvollziehbarer Form gespeichert. Jede Änderung ist versioniert, jede Entscheidung mit Eingangsparametern verknüpft. Logs sind lesbar, exportierbar und können für Forschung oder Auditierung anonymisiert geteilt werden.

> Data is processed locally and stored in a traceable format. Every change is versioned and each decision is linked to its input parameters. Logs are human-readable, exportable, and can be anonymized for research or auditing.

**Kernmechanismen:**

* Lokale Speicherung in SQLite / JSON
* Versionierung und Checksums
* Audit-Trail für Entscheidungen
* Transparente Datenstrukturen ohne Blackboxes

> **Core mechanisms:**
>
> * Local storage via SQLite / JSON
> * Versioning and checksums
> * Decision audit trail
> * Transparent data structures without black boxes

---

## Nachhaltigkeit / Sustainability

Nachhaltigkeit ist kein Nebeneffekt, sondern Bestandteil der Systemlogik. BitGridAI priorisiert **Energieeffizienz und Ressourcenschonung** auf allen Ebenen: Hardware, Software und Entscheidungskette. Das System nutzt PV-Überschuss intelligent, reduziert Energieverbrauch und fördert lokale Resilienz.

> Sustainability is not a side effect but a design principle. BitGridAI prioritizes **energy efficiency and resource awareness** across hardware, software, and decision-making layers. The system intelligently utilizes PV surplus, reduces consumption, and enhances local resilience.

**Kernmechanismen:**

* Dynamische Steuerung nach Energieangebot
* Effiziente Lastverteilung (Load Shifting)
* Nutzung von Low-Power-Devices
* Monitoring von Energieverbrauch und CO₂-Einsparung

> **Core mechanisms:**
>
> * Dynamic control based on energy availability
> * Efficient load shifting
> * Use of low-power devices
> * Monitoring of energy use and CO₂ savings

---

## Bitcoin ist Zeit / Bitcoin as Time

BitGridAI interpretiert Bitcoin als **zeitbasierte Energieaustauschschicht**: Durch den 10-Minuten-Blocktakt entsteht ein natürlicher Rhythmus für lokale Automatisierung. Entscheidungen orientieren sich daher an Blockfenstern und nutzen Deadbands, um unnötige Schaltzyklen zu vermeiden.

> BitGridAI treats Bitcoin as a **time-denominated energy exchange layer**. The 10-minute block cadence becomes a natural rhythm for local automation, so decisions align with block windows and apply deadbands to avoid unnecessary switching.

**Kernmechanismen:**

* Block-aligned Scheduler (10-Minuten-Fenster für Start/Stop)
* Zeithomogene Explainability-Logs (Entscheidungen nach Blockzeit)
* Korrelation von Energieprofilen mit Mempool-/Difficulty-Signalen

> **Core mechanisms:**
>
> * Block-aligned scheduler (10-minute start/stop windows)
> * Time-homogeneous explainability logs (decisions tagged by block time)
> * Correlating energy profiles with mempool/difficulty signals

---

## Hodl als Energiespeicher / Hodl as Energy Reserve

Überschussenergie kann in Form von **selbst geminten Satoshis „gehodlt“** werden. Das System bietet Policies, die entscheiden, ob Energie sofort als Wärme/Verbrauch genutzt oder in Bitcoin umgewandelt und langfristig gehalten wird.

> Surplus energy may be “hodled” as self-mined satoshis. Policies decide whether energy is spent immediately (heat/consumption) or converted into bitcoin as a long-term local reserve.

**Kernmechanismen:**

* Energy-to-Value Tracking (kWh → sats) für Transparenz
* Wallet-agnostische Accounting-Schnittstelle (nur Hash-/Proof-Logs)
* Forschungskanal für Vergleich „hodl vs. sofortige Nutzung“

> **Core mechanisms:**
>
> * Energy-to-value tracking (kWh → sats) for transparency
> * Wallet-agnostic accounting interface (hash/proof logs only)
> * Research hooks comparing “hodl vs. immediate consumption”

---

## Opportunitätskosten / Energy Opportunity Cost

BitGridAI berücksichtigt energetische **Opportunitätskosten** als konzeptionelles Prinzip: jede Kilowattstunde PV-Überschuss kann **exportiert** oder **lokal genutzt** werden (z. B. Mining, Wärme, Speicherung). Die Steuerlogik bewertet diese Alternativen transparent und regelbasiert, ohne Black-Box-Optimierer.

> BitGridAI incorporates **energy opportunity cost** as a conceptual principle: each kilowatt-hour of PV surplus can be **exported** or **used locally** (e.g., mining, heat, storage). The control logic evaluates these alternatives transparently and rule-based, without black-box optimizers.

**Kernmechanismen:**

* Vergleich von lokalem Nutzen vs. Einspeise-Erlös (implizit über Preis/Schwellen in R1)
* Priorisierung von Autarkie und Sicherheit (R2/R3 vor Opportunitätskosten)
* Berücksichtigung der Zeitpräferenz durch Blocktakt & Deadband (Stabilität statt Reaktiv-Flapping)
* Optionale „Energy Path Policies“: *Export bevorzugt*, *Lokalverbrauch bevorzugt*, *Adaptiv*
* Transparente Darstellung: UI zeigt, welche Alternative nicht gewählt wurde und warum

> **Core mechanisms:**
>
> * Comparing local value vs. export revenue (implicitly via price/thresholds in R1)
> * Giving priority to autonomy and safety (R2/R3 over opportunity cost)
> * Incorporating time preference via block cadence & deadband (stability over reactive flapping)
> * Optional „energy path policies“: *export-first*, *local-first*, *adaptive*
> * Transparent UI feedback: showing which option was **not** chosen – and why

---

## Blockchain-Trilemma / Blockchain Trilemma

BitGridAI orientiert sich am **Trilemma aus Dezentralisierung, Sicherheit und Skalierbarkeit**. Lokale Steuerung bevorzugt Dezentralisierung & Sicherheit, akzeptiert bewusst begrenzte Skalierung (nur Haushaltslast) und nutzt modulare Schnittstellen statt globaler Cloud-Kontrolle.

> BitGridAI follows the **decentralization–security–scalability trilemma**. Local control favors decentralization and security, deliberately limiting scale to the household scope while exposing modular interfaces instead of global cloud control.

**Kernmechanismen:**

* Lokale Validierung aller Sensor-/Aktordaten
* Modulgrenzen mit klar definierten APIs statt zentraler Broker
* Messgrößen für Sicherheit (Thermal, Deadband) höher priorisiert als Durchsatz

> **Core mechanisms:**
>
> * Local validation of all sensor/actuator data
> * Module boundaries with clear APIs instead of central brokers
> * Safety metrics (thermal, deadband) take precedence over throughput

---

## Sicherheit und Autonomie / Security and Autonomy

Sicherheit wird nicht durch Cloud-Dienste, sondern durch **lokale Isolation und Ownership** erreicht. Nutzer behalten die Kontrolle über alle Daten, Schlüssel und Automatisierungsregeln. Der Betrieb ist offline-fähig, resilient und unabhängig von Dritten.

> Security is achieved not through cloud services but through **local isolation and user ownership**. Users retain full control over all data, keys, and automation rules. The system operates offline, resiliently, and independently of third parties.

**Kernmechanismen:**

* Lokale Authentifizierung
* Kein externer Datenverkehr
* Verschlüsselte Logs (optional)
* Notfallmodus bei Netzwerkverlust

> **Core mechanisms:**
>
> * Local authentication
> * No external data traffic
> * Optional encrypted logs
> * Fallback mode in case of network loss

---

## Proof-of-Work als Energieschnittstelle / Proof-of-Work as Energy Interface

Proof-of-Work transformiert elektrische Energie in einen unumkehrbaren Hash-Beitrag. BitGridAI behandelt Miner daher wie **deterministische Energiesenken** mit messbarem Nutzen (Hashrate) und strengen Sicherheitsgrenzen.

> Proof-of-Work turns electrical energy into an irreversible hash contribution. BitGridAI thus treats miners as **deterministic energy sinks** with measurable benefit (hash rate) and strict safety limits.

**Kernmechanismen:**

* Telemetrie für Hashrate, Effizienz (J/TH) und Temperatur im Explainability-Layer
* R3/R4-Regeln überwachen thermische Sicherheit und Forecast-Pläne für PoW-Lasten
* Fail-safe Shutdowns (Stop → Safe) koppeln Mining-Prozesse an Energieverfügbarkeit

> **Core mechanisms:**
>
> * Telemetry for hash rate, efficiency (J/TH), and temperature in the explainability layer
> * R3/R4 rules supervise thermal safety and forecast plans for PoW loads
> * Fail-safe shutdowns (stop → safe) tie mining processes to energy availability

---

## Human-Centered Interaction / Menschzentrierte Interaktion

Alle Schnittstellen sind so gestaltet, dass sie **Kontrolle, Verständnis und Vertrauen** fördern. Statt Blackbox-Automation bietet BitGridAI erklärbare, dialogfähige Interaktion – als Grundlage für Akzeptanz und Forschung.

> All interfaces are designed to foster **control, understanding, and trust**. Instead of black-box automation, BitGridAI enables explainable, dialog-oriented interaction – the foundation for acceptance and research.

**Kernmechanismen:**

* Transparente Benutzerführung
* Adaptive Informationsdichte je nach Nutzungskontext
* Interaktive Erklärungen („Warum diese Aktion?“)
* Forschungsmodus zur Beobachtung und Evaluation

> **Core mechanisms:**
>
> * Transparent user guidance
> * Adaptive information density based on context
> * Interactive explanations (“Why this action?”)
> * Research mode for observation and evaluation

---

## Zusammenfassung / Summary

Die querschnittlichen Konzepte bilden das Fundament von BitGridAI: **Erklärbarkeit, Transparenz, Nachhaltigkeit, Sicherheit und menschzentrierte Gestaltung**. Sie gewährleisten, dass technologische Entscheidungen stets mit ökologischen und ethischen Prinzipien im Einklang stehen.

> The crosscutting concepts form the foundation of BitGridAI: **explainability, transparency, sustainability, security, and human-centered design.** They ensure that technological decisions remain aligned with ecological and ethical principles.

*Weiter mit **[09 Designentscheidungen / Design Decisions](./09_design_decisions.md)**.*
