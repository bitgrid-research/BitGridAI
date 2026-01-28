# 22.2 – Annahmen zur Systemumgebung & Datenlage

Dieses Unterkapitel beschreibt die **technischen und datenbezogenen Annahmen**, unter denen das untersuchte System konzipiert, implementiert und evaluiert wird.  
Ziel ist es, den **Systemrahmen klar zu begrenzen** und gleichzeitig die Voraussetzungen für **Nachvollziehbarkeit, Reproduzierbarkeit und Erklärbarkeit** offenzulegen.

&nbsp;

## Lokale Ausführung und Verarbeitung

Für die betrachtete Systemumgebung wird angenommen:

- Das System wird **vollständig lokal ausgeführt** („Local First“), ohne zwingende Abhängigkeit von Cloud-Backends.
- Entscheidungen werden **on-device** getroffen; externe Datenquellen dienen ausschließlich der Kontextanreicherung.
- Die Systemarchitektur bleibt auch bei **temporärem Ausfall externer Datenquellen** funktionsfähig.
- Datenverarbeitung, Entscheidungslogik und Logging erfolgen innerhalb eines **kontrollierten, transparenten Systems**.

Diese Annahme reduziert Systemkomplexität, verbessert Datenhoheit und unterstützt erklärbare Entscheidungsprozesse.

&nbsp;

## Verfügbare Zustands- und Telemetriedaten

Die Arbeit geht von einer **begrenzten, aber robusten Datenbasis** aus.  
Als verfügbar werden insbesondere folgende Daten angenommen:

- **Energiebezogene Messwerte**
  - PV-Leistung bzw. PV-Überschuss
  - Hauslast
  - Netzbezug und Einspeisung
- **Speicherbezogene Zustände**
  - Ladezustand des Speichers (State of Charge, SoC)
- **Geräte- und Systemzustände**
  - Betriebszustände angeschlossener Lasten
  - Sicherheits- und Gesundheitsindikatoren (z. B. Temperatur)

Diese Messwerte bilden die Grundlage für die unmittelbare Entscheidungsfindung und werden als **zuverlässiger als externe Prognosen** betrachtet.

&nbsp;

## Wetterdaten ohne API-Key (DWD Open Data)

Für wetterbasierte Kontextinformationen wird angenommen:

- Wetterdaten werden aus **DWD Open Data** bezogen, **ohne API-Key** und ohne proprietäre Schnittstellen.
- Der Abruf erfolgt **periodisch** (z. B. alle 30–60 Minuten), da meteorologische Modelle keine hochfrequente Aktualisierung erfordern.
- Wetterdaten werden als **stabilisierendes Signal** genutzt (z. B. zur Einschätzung von Prognosegüte), nicht als alleiniger Trigger für Aktorentscheidungen.

Diese Annahme unterstützt Reproduzierbarkeit, reduziert externe Abhängigkeiten und hält die IO- und Rechenlast gering.

&nbsp;

## Deterministische Sonnenstandsberechnung

Der Sonnenstand wird als **vollständig deterministisch berechenbar** angenommen und benötigt keine externen Datenquellen:

- Grundlage sind lokale Eingaben wie **Zeitstempel**, **geografische Position** (Breiten- und Längengrad) und optional die Höhe.
- Die Berechnung liefert u. a. **Sonnenhöhe (Elevation)** und **Azimut**.
- Der Sonnenstand dient als **strukturelles Gate** (z. B. „unter Mindesthöhe keine Starts“), um Fehlstarts in Dämmerungsphasen zu vermeiden und die Systemruhe zu erhöhen.

Im Zusammenspiel mit Wetterdaten bildet der Sonnenstand eine robuste, ausfallsichere Basis:  
Der Sonnenstand liefert die **tageszeitliche Struktur**, während Wetterdaten kurzfristige Unsicherheiten (z. B. Bewölkung) abbilden.

&nbsp;

## Regelbasierte und nachvollziehbare Logik

Für die Entscheidungsfindung wird angenommen:

- Das System folgt einer **regelbasierten, deterministischen Logik**.
- Alle Regeln, Zustände und Entscheidungsparameter sind:
  - explizit modelliert,
  - intern zugänglich,
  - vollständig loggbar.
- Entscheidungen werden in **diskreten Zeitintervallen** (z. B. blockbasiert) getroffen, nicht kontinuierlich.
- Neben expliziten Aktionen wird auch **bewusstes Nicht-Handeln** als Entscheidung erfasst und dokumentiert.

Diese Annahmen bilden die Grundlage für eine **transparente Analyse von Systemverhalten** sowie für spätere, offline durchgeführte Optimierungen, ohne die Nachvollziehbarkeit der Entscheidungen zu beeinträchtigen.


---

> **Nächster Schritt:** Es folgen die Grenzen und Nicht-Ziele.
>
> 👉 Weiter zu **[22.3 - Grenzen & Nicht-Ziele](../223_limits_and_non_goals/README.md)**
>
> 🔙 Zurück zu **[22 - Annahmen & Grenzen](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
