# 22.2 – Annahmen zur Systemumgebung & Datenlage

Dieses Unterkapitel beschreibt die **technischen und datenbezogenen Annahmen**, unter denen das untersuchte System konzipiert, implementiert und evaluiert wird.  
Ziel ist es, den **Systemrahmen klar zu begrenzen** und gleichzeitig die Voraussetzungen für **Nachvollziehbarkeit, Reproduzierbarkeit und Erklärbarkeit** offenzulegen.

&nbsp;

## Lokale Ausführung und Verarbeitung

Für die betrachtete Systemumgebung wird angenommen:

- Das System wird **vollständig lokal ausgeführt** („Local First“), ohne zwingende Abhängigkeit von Cloud-Backends.
- Entscheidungen werden **on-device** getroffen; externe Dienste (z. B. Wetter- oder Preisdaten) sind optional und nicht essenziell.
- Die Systemarchitektur ist so gestaltet, dass sie auch bei **temporärem Ausfall externer Datenquellen** funktionsfähig bleibt.
- Datenverarbeitung, Entscheidungslogik und Logging erfolgen innerhalb eines **kontrollierten, transparenten Systems**.

Diese Annahme dient der Reduktion von Komplexität, der Verbesserung der Datenhoheit sowie der Sicherstellung erklärbarer Entscheidungsprozesse.

&nbsp;

## Verfügbare Zustands- und Telemetriedaten

Die Arbeit geht von einer **begrenzten, aber stabilen Datenbasis** aus.  
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

Optionale Datenquellen wie **Strompreise** oder **Wetterprognosen** können in die Entscheidungsfindung einbezogen werden, werden jedoch als **unsicher und nicht deterministisch** betrachtet und dienen primär der Stabilisierung von Entscheidungen, nicht als alleinige Auslöser.


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
