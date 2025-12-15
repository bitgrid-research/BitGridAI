# 05.2.2.2 Actuation Writer

Verantwortung: nimmt Kommandos aus dem Core entgegen und schreibt sie auf Geraete (REST/MQTT/Modbus). Stellt Idempotenz, Quittungen und Limits sicher.

## Struktur

- **Command Router:** entscheidet Transport (MQTT/REST/Modbus) je Geraet/Profil.
- **Limiter/Safety Guard:** prueft Leistungs- und Temperatur-Limits vor dem Senden.
- **Idempotency Layer:** versieht Kommandos mit `command_id`, dedupliziert Wiederholungen.
- **Ack Tracker:** wartet auf Bestaetigung/Telemetry-Aenderung und korreliert per `command_id`.

## Schnittstellen

- **Provided:** Kommandos an Geraete, Quittungen/Status (z.B. `miner/state/#`), Fehlermeldungen bei Limits/Transportfehlern.
- **Required:** Core-Decision mit `command_id`, Device Profiles (Limits, Endpoints), Zugang zu Broker/REST/Modbus.

## Ablauf (vereinfacht)

1) Command Router erhaelt `Decision` -> waehlt Transport.  
2) Limiter prueft Werte; bei Verstoss Abbruch mit Fehler.  
3) Idempotency Layer setzt/prueft `command_id`, sendet Kommando.  
4) Ack Tracker lauscht auf Quittung/State-Aenderung -> meldet an Core/UI/Data.

## Qualitaet und Betrieb

- Idempotent pro `command_id`; Wiederholungen ohne Doppelwirkung.  
- Timeout und Retry mit Backoff; nach Grenzwertverletzung sofortiger Abort.  
- Telemetrie-basierte Quittung bevorzugt gegenueber reinem Transport-Ack.

---
> Zurueck zu **[5.2.2.x Adapter und Feld-I/O (Level 3)](./README.md)**  
> Zurueck zu **[5.2.2 Whitebox Adapter und Feld-I/O](../0522_adapters_whitebox.md)**
