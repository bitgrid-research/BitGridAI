# 05.2.2 Whitebox Adapter und Feld-I/O

Scope: sichere, entkoppelte Anbindung der Feldgeraete (PV, Speicher, Smart Meter, Miner) ueber MQTT/REST/Modbus. Uebersetzt Protokolle in interne Events und nimmt Kommandos entgegen.

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **Telemetry Ingest** | Liest MQTT/REST/Modbus, normalisiert Einheiten, leitet an Core weiter. | Retained MQTT-Topics, Zeitstempel-Normalisierung. |
| **Actuation Writer** | Nimmt Kommandos vom Core an und schreibt sie auf Geraete (REST/MQTT). | Idempotent, mit `command_id` fuer Korrelation. |
| **Health Monitor** | Heartbeats pro Geraet/Protokoll; meldet Ausfaelle an Core/UI. | Liefert Status auf `health/#`. |
| **Device Profiles** | Spezifika pro Hersteller (Skalierung, Limits, Features). | Versioniert, liegt in `config/*.yaml`. |

## Level-3-Details

- [5.2.2.1 Telemetry Ingest](./0522_adapters_whitebox/05221_telemetry_ingest.md)
- [5.2.2.2 Actuation Writer](./0522_adapters_whitebox/05222_actuation_writer.md)
- [5.2.2.3 Health Monitor](./0522_adapters_whitebox/05223_health_monitor.md)
- [5.2.2.4 Device Profiles](./0522_adapters_whitebox/05224_device_profiles.md)

## Schnittstellen

- **Provided:** Messwerte (MQTT `sensor/#`, `meter/#`), Health (`health/#`), Aktor-Quittungen (`miner/state/#`), Fehler-Events.
- **Required:** Hardware-Protokolle (MQTT-Broker, Modbus TCP, REST), Kommandos aus dem Core (`miner/cmd/set`, REST), Konfigurationsprofile.

## Hauptdatenfluesse

1) Geraete -> Adapter -> MQTT/REST -> Core (`EnergyState` Update).  
2) Core-Decision -> Actuation Writer -> Geraet -> Quittung/Telemetry-Update.  
3) Heartbeats -> Health Monitor -> `health/#` -> Core/UI.

## Qualitaets- und Betriebsaspekte

- Lose Kopplung: Adapter crash darf Core nicht blockieren; Neustartfaehig.  
- Einheitenklarheit: nur SI-Einheiten nach innen; Mapping in Device Profiles.  
- Safety: harte Limits auf Leistungs- und Temperaturwerten pro Geraet.

---
> Zurueck zu **[5.2 Level-2-Whiteboxes](./README.md)**  
> Zurueck zu **[5.1 Whitebox Gesamtsystem](../051_blackbox/051_blackbox.md)**
