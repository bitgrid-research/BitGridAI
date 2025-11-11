# 08 – Querschnittliche Konzepte / Crosscutting Concepts

## Überblick / Overview

Dieses Kapitel beschreibt die systemweit geltenden Konzepte und Prinzipien von BitGridAI.
Sie sind unabhängig von spezifischen Modulen und stellen sicher, dass das System **nachvollziehbar, sicher und nachhaltig** bleibt – über Architekturgrenzen hinweg.

> This chapter defines the system-wide concepts and principles of BitGridAI.
> They apply across all modules and ensure that the system remains **traceable, secure, and sustainable** beyond architectural boundaries.

---

## Erklärbarkeit / Explainability

BitGridAI integriert **Explainable AI (XAI)** und HCI-Prinzipien direkt in die Steuerlogik.
Jede Entscheidung wird kontextualisiert, begründet und über die Erklärschnittstelle sichtbar gemacht.
Damit werden Aktionen **nicht nur automatisiert, sondern auch verständlich**.

> BitGridAI integrates **Explainable AI (XAI)** and HCI principles directly into its control logic.
> Every decision is contextualized, justified, and made visible through the explanation interface.
> This ensures that actions are **not only automated but also understandable**.

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

Daten werden lokal verarbeitet und in nachvollziehbarer Form gespeichert.
Jede Änderung ist versioniert, jede Entscheidung mit Eingangsparametern verknüpft.
Logs sind lesbar, exportierbar und können für Forschung oder Auditierung anonymisiert geteilt werden.

> Data is processed locally and stored in a traceable format.
> Every change is versioned and each decision is linked to its input parameters.
> Logs are human-readable, exportable, and can be anonymized for research or auditing.

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

Nachhaltigkeit ist kein Nebeneffekt, sondern Bestandteil der Systemlogik.
BitGridAI priorisiert **Energieeffizienz und Ressourcenschonung** auf allen Ebenen: Hardware, Software und Entscheidungskette.
Das System nutzt PV-Überschuss intelligent, reduziert Energieverbrauch und fördert lokale Resilienz.

> Sustainability is not a side effect but a design principle.
> BitGridAI prioritizes **energy efficiency and resource awareness** across hardware, software, and decision-making layers.
> The system intelligently utilizes PV surplus, reduces consumption, and enhances local resilience.

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

## Sicherheit und Autonomie / Security and Autonomy

Sicherheit wird nicht durch Cloud-Dienste, sondern durch **lokale Isolation und Ownership** erreicht.
Nutzer:innen behalten die Kontrolle über alle Daten, Schlüssel und Automatisierungsregeln.
Der Betrieb ist offline-fähig, resilient und unabhängig von Dritten.

> Security is achieved not through cloud services but through **local isolation and user ownership**.
> Users retain full control over all data, keys, and automation rules.
> The system operates offline, resiliently, and independently of third parties.

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

## Human-Centered Interaction / Menschzentrierte Interaktion

Alle Schnittstellen sind so gestaltet, dass sie **Kontrolle, Verständnis und Vertrauen** fördern.
Statt Blackbox-Automation bietet BitGridAI erklärbare, dialogfähige Interaktion – als Grundlage für Akzeptanz und Forschung.

> All interfaces are designed to foster **control, understanding, and trust**.
> Instead of black-box automation, BitGridAI enables explainable, dialog-oriented interaction – the foundation for acceptance and research.

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

Die querschnittlichen Konzepte bilden das Fundament von BitGridAI:
**Erklärbarkeit, Transparenz, Nachhaltigkeit, Sicherheit und menschzentrierte Gestaltung**.
Sie gewährleisten, dass technologische Entscheidungen stets mit ökologischen und ethischen Prinzipien im Einklang stehen.

> The crosscutting concepts form the foundation of BitGridAI:
> **explainability, transparency, sustainability, security, and human-centered design.**
> They ensure that technological decisions remain aligned with ecological and ethical principles.
