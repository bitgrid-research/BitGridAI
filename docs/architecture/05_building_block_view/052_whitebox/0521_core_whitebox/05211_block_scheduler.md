# 05.2.1.1 Block-Scheduler

Der Taktgeber des Systems.

Der Block-Scheduler erzwingt den **10-Minuten-Rhythmus**, triggert die Regel-Auswertung und sorgt mit `valid_until` dafür, dass Entscheidungen **ruhig bleiben** und nicht flappen.

&nbsp;

## Verantwortung

- Erzwingt feste Blockfenster (Default: 10 Minuten)
- Triggert die Rule Engine exakt einmal pro Block
- Setzt `valid_until` Deadbands zur Stabilisierung
- Entkoppelt Entscheidungslogik von Echtzeitrauschen

&nbsp;

## Struktur

- **Tick Manager**  
  Verwaltet `block_id`, `window_start` und `window_end`.

- **Trigger Dispatcher**  
  Startet die Rule Engine (synchron oder queued) und überwacht die Laufzeit.

- **Deadband Manager**  
  Berechnet `valid_until` je Entscheidungstyp (Hysterese, Mindesthaltezeit).

- **Clock Source**  
  Bevorzugt NTP-synchronisierte Systemuhr, Fallback auf Monotonic Clock.

&nbsp;

## Schnittstellen

**Provided**
- Block-Ticks (Event)
- `valid_until` Werte
- Scheduler-Health

**Required**
- Aktuelle Zeitquelle
- Konfiguration (Blockdauer, Grace Period)
- Rueckmeldung ueber Regel-Laufzeit (Timeboxing)

&nbsp;

## Ablauf (vereinfacht)

1. Alle `block_duration` erzeugt der Tick Manager ein neues Blockfenster  
   (`block_id`, `window_start`, `window_end`).
2. Der Trigger Dispatcher startet die Rule Engine und ueberwacht die Laufzeit.
3. Der Deadband Manager berechnet `valid_until` aus Entscheidungstyp und Hysterese-Regeln.
4. Tick- und Health-Events werden an Core, UI und Data publiziert.

&nbsp;

## Qualitaet und Betrieb

- **Timeboxing**  
  Regel-Auswertungen duerfen das Blockfenster nicht ueberschreiten.  
  Bei Ueberschreitung: Warnung und Fallback auf Safe Decision.

- **Flapping-Vermeidung**  
  Hysterese pro Aktionstyp, Mindesthaltezeiten ueber `valid_until`.

- **Resilienz**  
  Verpasste Ticks werden sofort nachgeholt (kein Drift),  
  jedoch ohne Mehrfach-Trigger.

---
> **Nächster Schritt:** Der Takt steht. Jetzt schauen wir,
> wie Messwerte und Forecasts zu einem konsistenten Zustand verschmelzen.
>
> 👉 Weiter zu **[5.2.1.2 Energy Context](./05212_energy_context.md)**
>
> 🔙 Zurück zu **[5.2.1 Core-Orchestrierung](./README.md)**
> 
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](..//../052_whitebox/README.md)** 

