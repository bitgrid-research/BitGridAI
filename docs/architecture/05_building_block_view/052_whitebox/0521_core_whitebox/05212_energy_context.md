# 05.2.1.2 Energy Context

Die Quelle der Wahrheit.

Der Energy Context konsolidiert Telemetrie und Forecasts zum **`EnergyState`** – der **Single Source of Truth** im System.  
Er sorgt dafür, dass Regeln, Vorschauen und Replays **auf konsistenten, validierten Daten** arbeiten.

*(Platzhalter für ein Bild: Der Hamster sitzt an einem großen Tisch voller Messgeräte. Pfeile führen von PV, Batterie, Stromzähler und Wetterdaten in ein einziges, ordentlich beschriftetes Kästchen: „EnergyState“.)*
![Hamster sammelt Messwerte](../media/pixel_art_energy_context.png)


---

## Verantwortung

- Konsolidiert alle Messwerte und Prognosen
- Normalisiert Einheiten und Zeitstempel
- Erzwingt Mindest-Vollständigkeit pro Block
- Liefert konsistente Snapshots für Regeln und Previews

---

## Struktur

- **Input Normalizer**  
  Wandelt Rohdaten in SI-Einheiten, prüft Plausibilität und versieht sie mit Zeitstempeln.

- **State Builder**  
  Führt Werte zusammen (PV, Last, Netz, Speicher, Temperaturen, Preise, Forecasts)  
  und berechnet abgeleitete Größen (z.B. `surplus_kw`).

- **Completeness Guard**  
  Erzwingt Pflichtsignale pro Block (z.B. Grid + PV + Miner-Temp).  
  Markiert fehlende Daten und setzt den Status auf *degraded*.

- **Snapshot Cache**  
  Hält das letzte konsistente `EnergyState` für Rule Engine, Preview und Explain bereit.

---

## Schnittstellen

**Provided**
- `EnergyState` Snapshots
- Warnings und Errors bei fehlenden oder inkonsistenten Daten
- Metadaten (Quelle, Zeitbasis, Qualität)

**Required**
- Telemetrie aus Adaptern (PV, Meter, Storage, Miner)
- Forecasts und Preise
- Geräte- und Einheitenprofile
- Zeitquelle

---

## Ablauf (vereinfacht)

1. Eingangsdaten treffen ein (MQTT / REST / Modbus).  
   Der Input Normalizer wandelt, prüft und stempelt.
2. Der State Builder aggregiert Werte und berechnet abgeleitete Größen.
3. Der Completeness Guard prüft Pflichtfelder.  
   Bei Lücken: Status *degraded*, optional Halten des letzten gültigen Werts.
4. Der Snapshot Cache liefert einen konsistenten `EnergyState` an  
   Rule Engine, UI/Explain und Logging.

---

## Qualität und Betrieb

- **Einheitensicherheit**  
  Alle internen Werte in SI. Abweichungen werden markiert oder verworfen.

- **Zeitkonsistenz**  
  Maximaler Drift zwischen Eingaben ist konfigurierbar.  
  Überschreitung führt zu Degradation oder Fail-safe.

- **Nachvollziehbarkeit**  
  Jedes Feld trägt Quelle und Timestamp – audit- und replayfähig.

---
> **Nächster Schritt:** Die Daten stehen. Jetzt wird entschieden.
>
> 👉 Weiter zu **[5.2.1.3 Rule Engine](./05213_rule_engine.md)**
>
> 🔙 Zurück zu **[5.2.1 Core-Orchestrierung](./README.md)**
> 
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](..//../052_whitebox/README.md)** 

