# 05.2.2.1 Telemetry Ingest

Die Sinnesorgane des Systems.

Der Telemetry Ingest nimmt **Messdaten aus der realen Welt** entgegen und macht sie
für den Core nutzbar.  
Er übersetzt Rohsignale in **saubere, zeitlich konsistente Werte** – bevor irgendeine
Regel sie sieht.

*(Platzhalter für ein Bild: Der Hamster trägt eine Schutzbrille und sortiert Messwerte
durch Trichter. Links kommen chaotische Zahlen aus Kabeln, rechts fallen saubere
SI-Werte mit Zeitstempel heraus.)*
![Hamster verarbeitet Telemetrie](../media/pixel_art_telemetry_ingest.png)

---

## Verantwortung

- Entgegennahme von Telemetrie aus Feldgeräten (MQTT / REST / Modbus)
- Normalisierung aller Werte auf SI-Einheiten
- Harmonisierung von Zeitstempeln
- Weiterleitung **konsistenter Messwerte** an den Core

---

## Struktur

- **MQTT / REST / Modbus Reader**  
  Abonniert Topics, pollt Endpoints oder liest Register.

- **Unit Normalizer**  
  Konvertiert Rohdaten in SI-Einheiten (kW, V, A, °C, Wh) und markiert Abweichungen.

- **Timestamp Harmonizer**  
  Gleicht Zeitbasis ab, korrigiert leichte Abweichungen oder verwirft Ausreißer.

- **Publisher to Core**  
  Schreibt normalisierte Daten in den Core-State-Kanal.

---

## Schnittstellen

**Provided**
- Normalisierte Messwerte (`sensor/#`, `meter/#`)
- Status- und Warnmeldungen bei Inkonsistenzen

**Required**
- Broker- oder Endpoint-Zugriff
- Device Profiles (Mapping, Skalierung)
- Zeitquelle

---

## Ablauf (vereinfacht)

1. Reader erfasst Rohwerte → Unit Normalizer wendet Device Profiles an.  
2. Timestamp Harmonizer prüft Zeitdrift; bei Grenzverletzung Warnung oder Drop.  
3. Publisher sendet normalisierte Payloads an den Core (`EnergyState`-Update).  
4. Optional: Ack- oder Health-Flag pro Quelle.

---

## Qualität und Betrieb

- **Einheitensicherheit**  
  Nach innen ausschließlich SI-Einheiten; Fehlmessungen werden markiert, nicht still korrigiert.

- **Zeitkonsistenz**  
  Retained MQTT-Topics für schnellen Start, jedoch mit Altersgrenze.

- **Robustheit**  
  Rate-Limits gegen Datenfluten; Backpressure bei Broker-Ausfall (optionale Persistenz).

---
> **Nächster Schritt:** Die Daten sind sauber.  
> Jetzt müssen Entscheidungen **wirklich** in die Welt geschrieben werden.
>
> 👉 Weiter zu **[5.2.2.2 Actuation Writer](./05222_actuation_writer.md)**
>
> 🔙 Zurück zu **[5.2.2 Adapter & Feld-I/O](./README.md)**
> 
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](..//../052_whitebox/README.md)** 
