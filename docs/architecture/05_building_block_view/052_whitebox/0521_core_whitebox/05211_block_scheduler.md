# 05.2.1.1 Block-Scheduler

Verantwortung: erzwingt den 10-Minuten-Takt (Blockfenster), triggert Regel-Auswertungen, setzt `valid_until` Deadbands und entkoppelt Flapping.

## Struktur

- **Tick Manager:** verwaltet Block-ID und Fenstergrenzen.
- **Trigger Dispatcher:** loest die Rule Engine aus (synchron oder queued).
- **Deadband Manager:** berechnet `valid_until` fuer Decisions (Hysterese).
- **Clock Source:** bevorzugt NTP-synchronisierte Systemuhr, faellt auf Monotonic Clock zurueck.

## Schnittstellen

- **Provided:** Block-Ticks (Event), `valid_until` Werte, Scheduler-Health.
- **Required:** aktuelle Zeitquelle, Konfiguration (Blockdauer, Grace Period), Rueckmeldung ueber Regel-Laufzeit (fur Timeboxing).

## Ablauf (vereinfacht)

1) Alle `block_duration` (Default 10 min) erzeugt Tick Manager ein neues Fenster (`block_id`, `window_start`, `window_end`).  
2) Trigger Dispatcher startet Rule Engine; ueberwacht Laufzeit.  
3) Deadband Manager berechnet `valid_until` aus Entscheidungstyp und Hysterese-Regeln.  
4) Scheduler publiziert Tick- und Health-Events an Core/UI/Data.

## Qualitaet und Betrieb

- Timeboxing: Regel-Laufzeit darf das Fenster nicht ueberschreiten; sonst Warnung und Fallback auf Safe Decision.  
- Flapping-Vermeidung: Hysterese pro Aktionstyp, minimale Haltezeiten ueber `valid_until`.  
- Resilienz: Verpasstes Tick-Event fuehrt zu sofortigem Nachholen (kein Drift), aber ohne Mehrfach-Trigger.

---
> Zurueck zu **[5.2.1.x Core-Orchestrierung (Level 3)](./README.md)**  
> Zurueck zu **[5.2.1 Core-Orchestrierung](../0521_core_whitebox.md)**
