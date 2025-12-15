# 05.2.2.1 Telemetry Ingest

Verantwortung: nimmt Telemetrie aus Feldgeraeten entgegen (MQTT/REST/Modbus), normalisiert Einheiten, stempelt Zeit und leitet konsistente Werte an den Core weiter.

## Struktur

- **MQTT/REST/Modbus Reader:** abonniert bzw. pollt Topics/Endpoints/Registers.
- **Unit Normalizer:** konvertiert in SI-Einheiten (kW, V, A, C, Wh), markiert Abweichungen.
- **Timestamp Harmonizer:** gleicht Zeitbasis ab, korrigiert oder verwirft alte/zu neue Werte.
- **Publisher to Core:** schreibt normalisierte Daten in den Core-State-Kanal.

## Schnittstellen

- **Provided:** normalisierte Messwerte (MQTT `sensor/#`, `meter/#`), Status/Warnungen bei Inkonsistenzen.
- **Required:** Broker/Endpoint-Zugriff, Device Profiles (Mapping/Skalierung), Zeitquelle.

## Ablauf (vereinfacht)

1) Reader erfasst Rohwerte -> Unit Normalizer wendet Profile an.  
2) Timestamp Harmonizer prueft Drift; bei Grenzverletzung Warnung/Drop.  
3) Publisher sendet normalisierte Payload an Core (`EnergyState` Update).  
4) Optional: Ack/Health-Flag pro Quelle.

## Qualitaet und Betrieb

- Nur SI-Einheiten nach innen; Fehlmessungen werden markiert statt still korrigiert.  
- Retained MQTT-Topics fuer schnellen Start; dennoch mit Altersgrenze.  
- Rate-Limits gegen Fluten; Backpressure bei Broker-Ausfall (Persistenz optional).

---
> Zurueck zu **[5.2.2.x Adapter und Feld-I/O (Level 3)](./README.md)**  
> Zurueck zu **[5.2.2 Whitebox Adapter und Feld-I/O](../0522_adapters_whitebox.md)**
