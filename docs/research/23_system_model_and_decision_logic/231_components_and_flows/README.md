# 23.1 – Komponenten & Datenflüsse (konzeptionell)

Dieses Unterkapitel beschreibt die **zentralen konzeptionellen Komponenten** des Systems sowie die **Datenflüsse zwischen ihnen**.
Der Fokus liegt auf der **logischen Struktur** des Systems und der klaren Trennung von Wahrnehmung, Bewertung und Steuerung – unabhängig von konkreten technischen Implementierungen.

&nbsp;

## Energiequellen und -senken

Das System betrachtet Energieflüsse in abstrahierter Form als **Quellen** und **Senken**, die innerhalb eines lokalen Energiesystems miteinander interagieren.

### Energiequellen

* **Photovoltaik (PV)**
  Primäre, volatile Energiequelle mit tages- und wetterabhängiger Erzeugung.
* **Netzbezug (sekundär)**
  Externe Energiequelle, die nur implizit betrachtet wird (z. B. zur Bewertung von Autarkie oder Schutzmechanismen).

### Energiesenken

* **Haushaltslasten**
  Nicht steuerbare Grundlasten.
* **Flexible Lasten** (z. B. Miner)
  Steuerbare Verbraucher, deren Betrieb zeitlich verschoben oder begrenzt werden kann.
* **Energiespeicher**
  Batterie als temporäre Senke (Laden) und Quelle (Entladen), mit expliziten Schutzgrenzen.

Energiequellen und -senken werden nicht direkt gekoppelt, sondern über **Zustands- und Entscheidungslogik vermittelt**.

&nbsp;

## Zustandsdaten

Zur Beschreibung des Systemzustands werden **explizite Zustands- und Telemetriedaten** angenommen, die regelmäßig aktualisiert werden, aber nicht direkt zu Aktionen führen.

### Zentrale Zustandsgrößen

* **Energetische Zustände**

  * PV-Leistung / Überschuss
  * Hauslast
  * Netzbezug / Einspeisung
* **Speicherzustände**

  * Ladezustand des Speichers (SoC)
* **Geräte- und Sicherheitszustände**

  * Betriebszustand steuerbarer Lasten
  * Temperatur- oder Health-Indikatoren
* **Kontextdaten (optional)**

  * Strompreise
  * Wetterinformationen (z. B. DWD Open Data)
  * Sonnenstand (deterministisch berechnet)

Diese Zustandsdaten bilden die **Wahrnehmungsebene** des Systems und werden als Input für die regelbasierte Bewertung verwendet.

&nbsp;

## Steuerpfade für Entscheidungen

Die Steuerung des Systems erfolgt nicht kontinuierlich, sondern über **klar definierte Entscheidungs- und Steuerpfade**.

### Konzeptioneller Entscheidungsfluss

```
Zustandsdaten
   ↓
Regelbewertung (R1–R5)
   ↓
Entscheidung (diskret, blockbasiert)
   ↓
Steueraktion (optional)
   ↓
Aktualisierter Systemzustand
```

### Charakteristika der Steuerpfade

* **Entkopplung von Messung und Aktion**
  Messwerte führen nicht unmittelbar zu Schaltvorgängen.
* **Diskrete Entscheidungen**
  Entscheidungen werden in festen Zeitintervallen getroffen.
* **Asymmetrische Eingriffe**
  Sicherheitsrelevante Eingriffe können Entscheidungen übersteuern.
* **Bewusstes Nicht-Handeln**
  Das Ausbleiben einer Aktion (`NOOP`) ist ein expliziter Teil des Steuerpfads.

Diese Struktur stellt sicher, dass das System **ruhig, nachvollziehbar und erklärbar** agiert, auch bei schwankenden Eingangsgrößen.

&nbsp;

## Zusammenfassung

Die konzeptionellen Komponenten und Datenflüsse bilden die Grundlage für:

* eine klare Trennung von Energiefluss und Entscheidungslogik,
* stabile und reproduzierbare Systemzustände,
* sowie eine Entscheidungsfindung, die sich für Nutzer:innen erklären lässt.

Auf dieser Basis werden im nächsten Unterkapitel die **konkreten Entscheidungsregeln und Auslöser** beschrieben.


---

> **Nächster Schritt:** Im nächsten Unterkapitel folgen die Entscheidungsregeln.
>
> 👉 Weiter zu **[23.2 - Entscheidungsregeln & Auslöser](../232_decision_rules_and_triggers/README.md)**
>
> 🔙 Zurück zu **[23 - Systemmodell & Entscheidungslogik](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
