# 05.2.4.1 - Baustein: Operational DB

Der aktuelle Zustand – zuverlässig festgehalten.

Die Operational DB speichert alles, was **für den laufenden Betrieb relevant** ist:
aktuelle Zustände, aktive Overrides, Konfigurationen und Zeitgrenzen (TTLs).

Sie ist **kein Langzeitarchiv** und kein Analyse-Store.  
Sie ist der **stabile Arbeitsspeicher auf Platte** – lokal, konsistent und berechenbar.

*(Platzhalter für ein Bild: Der Hamster sitzt an einem Schreibtisch mit einem dicken Buch.
Auf dem Buch steht „SQLite“. Daneben eine Uhr (TTL) und ein Häkchen „ACID“.)*  
![Hamster an der Operational DB](../media/pixel_art_operational_db.png)

&nbsp;

## Verantwortung

- Persistenz aktueller Systemzustände
- Speicherung von Konfigurationen, Overrides und TTLs
- Konsistente Reads für Core, UI und Preview
- Sichere Grundlage für Neustarts und Recovery

&nbsp;

## Struktur

- **Schema Core**  
  Tabellen für:
  - State-Snapshots  
  - Konfigurationen  
  - Overrides  
  - Schedules / TTLs

- **Integrity Guard**  
  ACID-Transaktionen, Foreign Keys und SQLite-Pragmas
  für Konsistenz und Haltbarkeit.

- **Migration Layer**  
  Versionierte Migrationen (SQL/DDL),
  ausgeführt kontrolliert beim Start.

- **Access Layer**  
  Ausschließlich lokaler Zugriff, kein Remote-Zugriff.  
  Bevorzugtes Isolationsniveau: `READ_COMMITTED`.

&nbsp;

## Schnittstellen

**Provided**
- Konsistente Reads für Core, UI und Preview
- Writes für laufenden Betrieb (State, Overrides, Config)

**Required**
- State- und DecisionEvent-Writes
- Config- und Policy-Updates
- Versionsinformationen für Migrationen

&nbsp;

## Ablauf (vereinfacht)

1) Core oder UI schreibt aktualisierte States, Overrides oder Konfigurationen.  
2) Integrity Guard sichert ACID-Eigenschaften und setzt Durability-Pragmas.  
3) Leser (UI, Preview) erhalten konsistente Snapshots.  
4) Migrationen werden versioniert vor oder beim Start ausgeführt.

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Local-only**  
  Keine Netzfreigabe, keine Remote-Zugriffe.

- **Konsistenz vor Geschwindigkeit**  
  Durability und WAL-Verhalten konfigurierbar,
  bewusst kein „Best-Effort“-Speichern.

- **Recovery-fähig**  
  Regelmäßige Backups empfohlen,
  Restore- und Recovery-Szenarien testbar.
  
---
> **Nächster Schritt:**  
> Der laufende Betrieb ist abgesichert – Zustände, Konfigurationen und Overrides
> überleben Neustarts und bleiben konsistent.
>
> Im nächsten Baustein wechseln wir von „aktueller Zustand“ zu **historischer Wahrheit**:
> ein unveränderlicher Event- und Log-Store, der Replays, Audits und Analysen ermöglicht.
>
> 👉 Weiter zu **[5.2.4.2 - Baustein: Event / Log Store](./05242_event_log_store.md)**
>
> 🔙 Zurück zu **[5.2.4 - Whitebox: Data und Research](./README.md)**
>
> 🔙 Zurück zu **[5.2 - Level-2-Whiteboxes](../README.md)**

