# 05.2.2.2 - Baustein: Actuation Writer

Die ausführende Hand.

Der Actuation Writer setzt Entscheidungen des Cores **kontrolliert und sicher**
in reale Aktionen um.  
Er spricht mit Geräten, achtet auf Limits – und sorgt dafür, dass ein Kommando
**genau einmal** wirkt.

*(Platzhalter für ein Bild: Der Hamster hält eine Fernbedienung mit beschrifteten
Knöpfen „Start“, „Stop“, „Limit“. Über den Knöpfen sitzen kleine Sicherheitssiegel
und ein Häkchen „Ack received“.)*
![Hamster sendet Kommandos](../media/pixel_art_actuation_writer.png)

&nbsp;

## Verantwortung

- Entgegennahme von Kommandos aus dem Core
- Auswahl des passenden Transportwegs (MQTT / REST / Modbus)
- Durchsetzung von Leistungs- und Sicherheitslimits
- Idempotente Ausführung und saubere Quittierung

&nbsp;

## Struktur

- **Command Router**  
  Entscheidet anhand von Device Profiles, welcher Transport genutzt wird.

- **Limiter / Safety Guard**  
  Prüft Leistungs-, Temperatur- und Gerätegrenzen vor dem Senden.

- **Idempotency Layer**  
  Versehen von Kommandos mit `command_id`, Deduplikation von Wiederholungen.

- **Ack Tracker**  
  Wartet auf Bestätigung oder Zustandsänderung und korreliert per `command_id`.

&nbsp;

## Schnittstellen

**Provided**
- Kommandos an Geräte
- Quittungen und Status-Updates (z.B. `miner/state/#`)
- Fehlermeldungen bei Limit- oder Transportverstößen

**Required**
- Core-Decisions mit `command_id`
- Device Profiles (Limits, Endpoints)
- Zugriff auf Broker / REST / Modbus

&nbsp;

## Ablauf (vereinfacht)

1. Command Router erhält `Decision` → wählt Transport.
2. Limiter prüft Zielwerte; bei Verstoß Abbruch mit Fehler.
3. Idempotency Layer prüft/setzt `command_id` und sendet das Kommando.
4. Ack Tracker wartet auf Quittung oder Telemetrie-Änderung und meldet zurück an Core, UI und Data.

&nbsp;

## Qualität und Betrieb

- **Idempotenz**  
  Gleiche `command_id` führt nie zu Doppelwirkungen.

- **Robustheit**  
  Timeout und Retry mit Backoff; bei Grenzwertverletzung sofortiger Abort.

- **Verlässliche Rückmeldung**  
  Telemetrie-basierte Quittung wird bevorzugt gegenüber reinem Transport-Ack.

---
> **Nächster Schritt:** Befehle sind angekommen.  
> Jetzt müssen wir überwachen, **ob alles lebt und erreichbar bleibt**.
>
> 👉 Weiter zu **[5.2.2.3 Health Monitor](./05223_health_monitor.md)**
>
> 🔙 Zurück zu **[5.2.2 Adapter & Feld-I/O](./README.md)**
> 
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](..//../052_whitebox/README.md)** 

