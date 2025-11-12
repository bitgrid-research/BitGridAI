# 09 – Architekturentscheidungen / Architectural Decisions

## Überblick / Overview

Dieses Kapitel dokumentiert die zentralen Architekturentscheidungen von BitGridAI.
Jede Entscheidung wurde mit Blick auf **Nachvollziehbarkeit, Nachhaltigkeit und lokale Autonomie** getroffen.
Sie dient als Referenz für zukünftige Entwicklung, Forschung und Systemerweiterung.

> This chapter documents the key architectural decisions of BitGridAI.
> Each decision was made with a focus on **traceability, sustainability, and local autonomy**.
> It serves as a reference for future development, research, and system evolution.

---

## ADR-Format / Decision Record Format

Alle Architekturentscheidungen folgen dem ADR-Format (Architecture Decision Record):

1. **Kontext / Context** – Ausgangslage und Rahmenbedingungen
2. **Entscheidung / Decision** – gewählte Option
3. **Begründung / Rationale** – warum diese Entscheidung
4. **Alternativen / Alternatives** – verworfene Optionen
5. **Auswirkungen / Consequences** – erwartete Effekte

> All architectural decisions follow the ADR format:
>
> 1. **Context** – initial situation and constraints
> 2. **Decision** – chosen option
> 3. **Rationale** – reason for the choice
> 4. **Alternatives** – discarded options
> 5. **Consequences** – expected impact

---

## ADR-001 – Lokale Architektur

**Kontext:** Datenschutz, Resilienz und Energieeffizienz sind zentrale Anforderungen.
**Entscheidung:** BitGridAI wird vollständig lokal ausgeführt (kein Cloud-Backend).
**Begründung:** Maximale Datenhoheit, Energieautonomie und Nachvollziehbarkeit.
**Alternativen:** Hybrid- oder Cloud-System mit API-Anbindung.
**Auswirkungen:** Erhöhte Wartungsverantwortung lokal, aber volle Kontrolle durch Nutzer.

> **Context:** Privacy, resilience, and energy efficiency are core requirements.
> **Decision:** BitGridAI runs fully locally (no cloud backend).
> **Rationale:** Ensures full data sovereignty, energy autonomy, and transparency.
> **Alternatives:** Hybrid or cloud systems with API connection.
> **Consequences:** Increased local maintenance responsibility, but complete user control.

---

## ADR-002 – Nutzung von MQTT als Kommunikationsbus

**Kontext:** Geräte und Module sollen lose gekoppelt und erweiterbar sein.
**Entscheidung:** MQTT wird als zentrales Kommunikationsprotokoll verwendet.
**Begründung:** Asynchrone Kommunikation, standardisiert, leichtgewichtig.
**Alternativen:** REST-only Kommunikation oder proprietäre Protokolle.
**Auswirkungen:** Hohe Flexibilität, einfache Integration neuer Geräte.

> **Context:** Devices and modules should be loosely coupled and extensible.
> **Decision:** MQTT is chosen as the central communication protocol.
> **Rationale:** Asynchronous, standardized, lightweight communication.
> **Alternatives:** REST-only or proprietary protocols.
> **Consequences:** High flexibility and easy device integration.

---

## ADR-003 – SQLite als lokale Persistenzschicht

**Kontext:** System benötigt auditierbare, einfache Datenspeicherung ohne externe Abhängigkeiten.
**Entscheidung:** Verwendung von SQLite als persistente lokale Datenbank.
**Begründung:** Portabel, zuverlässig, wartungsarm, ideal für Edge-Systeme.
**Alternativen:** PostgreSQL, InfluxDB oder Cloud-basierte Speicherlösungen.
**Auswirkungen:** Keine Netzwerkabhängigkeit, einfache Backups, begrenzte Skalierbarkeit.

> **Context:** The system requires auditable, simple data storage without external dependencies.
> **Decision:** Use SQLite as the persistent local database.
> **Rationale:** Portable, reliable, low-maintenance, ideal for edge systems.
> **Alternatives:** PostgreSQL, InfluxDB, or cloud-based storage.
> **Consequences:** No network dependency, easy backups, limited scalability.

---

## ADR-004 – Erklärungsschnittstelle statt klassischem Dashboard

**Kontext:** Fokus auf Erklärbarkeit statt nur Visualisierung.
**Entscheidung:** Nutzung einer lokalen Erklärschnittstelle anstelle eines Dashboards.
**Begründung:** Priorisierung von Nutzerverständnis und Forschung zu HCI statt reiner UI.
**Alternativen:** Grafisch orientiertes Dashboard mit Fokus auf Performance.
**Auswirkungen:** Höherer semantischer Wert, geringerer visueller Overhead.

> **Context:** Focus on explainability rather than pure visualization.
> **Decision:** Use a local explanation interface instead of a dashboard.
> **Rationale:** Prioritize user understanding and HCI research over UI aesthetics.
> **Alternatives:** Graphical dashboards optimized for performance.
> **Consequences:** Higher semantic value, lower visual overhead.

---

## ADR-005 – Nachhaltigkeit als Steuergröße

**Kontext:** Energieeinsatz soll effizient, nachvollziehbar und an PV-Ertrag gekoppelt sein.
**Entscheidung:** Nachhaltigkeit wird als Parameter der Entscheidungslogik integriert.
**Begründung:** Ermöglicht energieadaptive Steuerung (z. B. Mining nur bei Überschuss).
**Alternativen:** Fixe Zeit- oder Regelprofile ohne Kontextbezug.
**Auswirkungen:** Reduzierter Energieverbrauch, dynamische Anpassung, Forschungspotenzial.

> **Context:** Energy usage should be efficient, traceable, and linked to PV output.
> **Decision:** Integrate sustainability as a parameter in decision logic.
> **Rationale:** Enables energy-adaptive control (e.g., mining only during surplus).
> **Alternatives:** Fixed time or rule profiles without context awareness.
> **Consequences:** Reduced energy use, dynamic adaptation, research potential.

---

## Zusammenfassung / Summary

Diese Architekturentscheidungen sichern die Grundwerte von BitGridAI:
**lokale Autonomie, Transparenz, Nachhaltigkeit und Erklärbarkeit.**
Sie bilden das Rückgrat der technischen und ethischen Ausrichtung des Projekts.

> These architectural decisions secure the core values of BitGridAI:
> **local autonomy, transparency, sustainability, and explainability.**
> They form the backbone of the project's technical and ethical orientation.
