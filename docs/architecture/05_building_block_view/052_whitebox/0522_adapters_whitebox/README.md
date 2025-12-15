# 05.2.2 Whitebox Adapter & Feld-I/O

Die Brücke zur realen Welt.

Diese Whitebox kapselt die **sichere, entkoppelte Anbindung der Feldgeräte**:
PV-Wechselrichter, Speicher, Smart Meter und Miner.

Sie spricht die Sprache der Hardware –  
und übersetzt sie in eine Form, die der Core versteht.

*(Platzhalter für ein Bild: Der Hamster steht zwischen Kabeln, Steckern und Funkwellen. Auf der einen Seite Geräte-Symbole (PV, Batterie, Miner), auf der anderen Seite saubere Events, die Richtung Core fließen.)*
![Hamster verbindet Feldgeräte](../media/pixel_art_adapter_field_io.png)

---

## Scope

- Anbindung von Feldgeräten über **MQTT, REST und Modbus**
- Entkopplung von Hardware und Fachlogik
- Übersetzung externer Protokolle in **interne Events**
- Ausführung von Core-Kommandos mit Rückmeldung

---

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **Telemetry Ingest** | Liest MQTT/REST/Modbus, normalisiert Einheiten, leitet an den Core weiter. | Retained MQTT-Topics, Zeitstempel-Normalisierung. |
| **Actuation Writer** | Nimmt Kommandos vom Core an und schreibt sie auf Geräte. | Idempotent, mit `command_id` zur Korrelation. |
| **Health Monitor** | Überwacht Heartbeats pro Gerät und Protokoll. | Meldet Status über `health/#`. |
| **Device Profiles** | Gerätespezifische Eigenheiten (Skalierung, Limits, Features). | Versioniert in `config/*.yaml`. |

---

## Level-3-Details

- **[5.2.2.1 Telemetry Ingest](./05221_telemetry_ingest.md)**  
- **[5.2.2.2 Actuation Writer](./05222_actuation_writer.md)**  
- **[5.2.2.3 Health Monitor](./05223_health_monitor.md)**  
- **[5.2.2.4 Device Profiles](./05224_device_profiles.md)**

---

## Schnittstellen

**Provided**
- Messwerte (`sensor/#`, `meter/#`)
- Health-Status (`health/#`)
- Aktor-Quittungen (`miner/state/#`)
- Fehler- und Warn-Events

**Required**
- Hardware-Protokolle (MQTT-Broker, Modbus TCP, REST)
- Kommandos aus dem Core (`miner/cmd/set`, REST)
- Konfigurationsprofile (`config/*.yaml`)

---

## Hauptdatenflüsse

1. **Geräte → Adapter → Core**  
   Telemetrie fließt ein und aktualisiert den `EnergyState`.

2. **Core → Adapter → Geräte**  
   Decisions werden als konkrete Kommandos umgesetzt.

3. **Health → Core / UI**  
   Heartbeats und Fehlerzustände sichern den Betrieb ab.

---

## Qualitäts- und Betriebsaspekte

- **Lose Kopplung**  
  Ein Adapter-Crash blockiert den Core nicht. Neustart jederzeit möglich.

- **Einheitenklarheit**  
  Nach innen ausschließlich SI-Einheiten; Mapping über Device Profiles.

- **Safety**  
  Harte Grenzwerte für Leistung und Temperatur pro Gerät.

---
> **Nächster Schritt:** Die Leitungen sitzen. Jetzt geben wir dem System ein Gesicht und eine Stimme:
> UI, Erklärungen und kontrollierte Eingriffe.
>
> 👉 Weiter zu **[5.2.3 UI & Explainability](../0523_ui_explain_whitebox/README.md)**
>
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](./README.md)**
> 
> 🔙 Zurück zu **[5.1 Whitebox Gesamtsystem](../051_blackbox/051_blackbox.md)**
