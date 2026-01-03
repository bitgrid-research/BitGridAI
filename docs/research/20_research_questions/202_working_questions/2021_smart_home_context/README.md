# 20.2.1 - Smart-Home-Kontext

Der Smart-Home-Kontext beschreibt den Kern von BitGridAI:
PV-Ueberschuss steuert Mining als flexible Last.
Ziel ist nicht nur Optimierung, sondern eine verstaendliche,
alltagstaugliche Erklaerung der Entscheidungen im lokalen Dashboard.

&nbsp;

## Zielbild

- Das Haus ist das Kontrollzentrum: Nutzer sehen, was passiert und warum.
- Entscheidungen werden als klare Gruende, Trigger und Parameter erklaert.
- Die Haus-Reserve (R2) ist sichtbar und nachvollziehbar.
- Automatisierung fuehlt sich wie Unterstuetzung an, nicht wie Kontrollverlust.

&nbsp;

## Unterseiten

- **[20.2.1a - Verstehen der Entscheidung](./2021a_transparenz.md)**
  - Warum laeuft, pausiert oder stoppt der Miner?
- **[20.2.1b - Kontrolle und Override](./2021b_kontrolle.md)**
  - Kann der Nutzer Mining schnell stoppen/starten?
- **[20.2.1c - Vertrauen und Sicherheit](./2021c_vertrauen.md)**
  - Ist die Haus-Reserve sichtbar und vertrauenswuerdig?

&nbsp;

## Kernproblem (Smart Home)

- PV-Ueberschuss schwankt staendig, Mining ist flexibel.
- Ohne Erklaerung wirkt das Verhalten des Systems willkuerlich.
- Nutzer sehen nur Status ("Miner an/aus"), aber keine Begruendung.

Design-Opportunity: Ein Dashboard, das Energiefluesse visualisiert
und Entscheidungen transparent erklaert.

&nbsp;

## System-Logik und Datenbasis (Gehirn)

Eingangsdaten:
- PV-Leistung, Prognose, erwarteter Ueberschuss.
- Hausverbrauch, Grundlast, Speicher-SoC.
- Netzpreis und Einspeisetarif (optional).
- Miner-Telemetrie: Temperatur, Leistung, Heartbeat.
- Nutzerpraeferenzen: Ruhezeiten, max Netzbezug, Override-Timeout.

Regel-Logik (R1-R5):
1) R1: Start Mining bei PV-Ueberschuss und guenstigen Bedingungen.
2) R2: Haus-Reserve schuetzt die Grundversorgung (Veto gegen Mining).
3) R3: Safety Stop bei Temperatur oder Fehlern.
4) R4: Forecast-Logik vermeidet unnoetige Starts.
5) R5: Stabilitaet verhindert Flapping (Start/Stop im Minutenrhythmus).

&nbsp;

## User Story (Wochenend-Szenario)

Mittag: PV-Ueberschuss steigt, der Miner startet automatisch.
Eine Wolke zieht durch: R5 haelt den Miner stabil statt hart zu stoppen.
Abends sinkt der Ueberschuss: R2 greift, der Miner pausiert.
Der Nutzer sieht klar, warum und wann der Miner wieder startet.

&nbsp;

## UI-Konzept: Web-Dashboard (Kontrollzentrum)

### Dashboard

- Energiefluss-Visualisierung: Haus, PV, Speicher, Miner, Netz mit aktiven Flusslinien.
- Status-Karten:
  - Miner: Status, Leistung, Temperatur.
  - Haus: Grundlast, Haus-Reserve "gesichert: Ja/Nein".
  - Preis: aktueller kWh-Preis (gruen, wenn guenstig).
  - Aktion: "Miner starten" oder "Miner pausieren".

### Automatik und Grenzen (Einstellungen)

- Haus-Reserve: gesperrter Bereich fuer die Grundversorgung.
- Ruhezeiten: Zeitfenster ohne Mining (z. B. nachts).
- Modi:
  - Eco-Optimiert (Standard)
  - Ruhe priorisiert
  - Maximaler Eigenverbrauch

### Forecast- und Preisvorschau

- 24h-Graph: PV-Prognose + Preisfenster.
- Geplante Mining-Fenster als Balken.

&nbsp;

## Beispiel-Erklaerungen im Dashboard

- "Miner startet: PV-Ueberschuss > 3 kW."
- "Miner pausiert: Haus-Reserve erreicht."
- "Miner stoppt: Temperatur zu hoch."
- "Miner bleibt aktiv bis 10:30 (Stabilitaetsfenster)."

&nbsp;

## Technischer Rahmen (Skizze)

- BitGridAI trifft regelbasierte Entscheidungen (R1-R5).
- Entscheidungen werden als Gruende und Prognosen ausgegeben.
- Kommunikation ins UI via MQTT oder lokale API.

Beispiel Topics:
- `bitgrid/decision/reason` -> "Start Mining: PV-Ueberschuss > 3 kW"
- `bitgrid/prediction` -> "Naechster Check in 10 Min"

&nbsp;

## Datenmodell (Entwurf)

```json
{
  "user_id": "user_123",
  "home_setup": {
    "pv_peak_power_kw": 10.5,
    "battery_storage_home_kwh": 8.0,
    "base_load_avg_kw": 0.4
  },
  "energy_context": {
    "pv_kw": 3.6,
    "load_kw": 1.2,
    "grid_kw": 0.0,
    "storage_soc_percent": 55
  },
  "miner_status": {
    "state": "PAUSED",
    "power_kw": 0.0,
    "chip_temp_c": 62,
    "last_heartbeat_sec": 12
  },
  "energy_market": {
    "current_grid_price": 0.32,
    "feed_in_tariff": 0.08,
    "forecast_low_price_window": "2023-10-29T14:00:00"
  },
  "decision": {
    "action": "START_MINING",
    "reason": "PV_Ueberschuss",
    "valid_until": "2023-10-29T14:10:00"
  }
}
```

&nbsp;

## Annahmen und Risiken

- Nutzer wollen verstehen, nicht optimieren.
- Lokales LLM und lokale Datenhaltung sind verfuegbar (Privacy).
- Zu viele Meldungen koennen nerven.
- Falsches Timing der Meldung kann bevormundend wirken.

&nbsp;

## Offene Fragen

- Welche Visualisierung erklaert Mining am schnellsten?
- Welche Begruendung ist kurz und trotzdem hilfreich?
- Wie viel Kontrolle braucht der Nutzer im Alltag wirklich?

---

> **Naechster Schritt:** Starte mit den Unterseiten des Smart-Home-Kontexts.
>
> -> Weiter zu **[20.2.1a - Verstehen der Entscheidung](./2021a_transparenz.md)**
>
> -> Weiter zu **[20.2.1b - Kontrolle und Override](./2021b_kontrolle.md)**
>
> -> Weiter zu **[20.2.1c - Vertrauen und Sicherheit](./2021c_vertrauen.md)**
>
> -> Weiter zu **[20.2.2 - Automotive-Kontext](../2022_automotive_context/README.md)**
>
> <- Zurueck zu **[20.2 - Zentrale Arbeitsfragen](../README.md)**
>
> <- Zurueck zur **[Hauptuebersicht](../../../../README.md)**
