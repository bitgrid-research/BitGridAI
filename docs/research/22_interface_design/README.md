# 22 - Interface Design

Dieses Kapitel uebersetzt die Forschungsfragen und Prinzipien in konkrete UI-Entscheidungen.
Es gibt zwei Auspraegungen: Smart-Home-Dashboard und Automotive-In-Car-UI.
Beide Varianten folgen derselben Logik (R1-R5), unterscheiden sich aber in Kontext, Aufmerksamkeit und Interaktion.

&nbsp;

## Inhalt dieses Kapitels

- **[22.1 - Smart-Home-Interface (Dashboard)](#221---smart-home-interface-dashboard)**
- **[22.2 - Automotive-Interface (In-Car-UI)](#222---automotive-interface-in-car-ui)**

&nbsp;

## 22.1 - Smart-Home-Interface (Dashboard)

### Zielbild

- Das Haus ist das Kontrollzentrum: Nutzer sehen Energiefluss und Entscheidung in einem Blick.
- Entscheidungen sind begruendet, nicht nur angezeigt ("Warum" vor "Was").
- Manuelle Kontrolle ist jederzeit moeglich, ohne die Automatik zu zerstoeren.

&nbsp;

### Designprinzipien

- **Erklaeren statt optimieren:** Primar geht es um Verstaendnis.
- **Ursache vor Aktion:** Grund + Ausloeser vor Statuswechsel.
- **Stabilitaet zeigen:** R5-Stabilitaetsfenster sichtbar machen.
- **Haus-Reserve schuetzen:** R2 wird als klare Grenze visualisiert.

&nbsp;

### Informationsarchitektur (Kernbereiche)

1) **Jetzt**: Live-Energiefluss (PV, Haus, Speicher, Miner, Netz).
2) **Entscheidung**: Aktuelle Aktion + begruendeter Grund.
3) **Kontrolle**: Override, Modi, Limits, Ruhezeiten.

&nbsp;

### Kern-Screens

- **Dashboard:** Energiefluss + Decision Card + Schnellaktionen.
- **Details Miner:** Temperatur, Leistung, Fehlerstatus, Historie.
- **Planung/Prognose:** 24h PV/Preis-Graph + geplante Mining-Fenster.
- **Einstellungen:** Haus-Reserve, Ruhezeiten, Modi (Eco, Ruhe, Max PV).

&nbsp;

### Interaktionen und Regeln

- **Warum?** Link oeffnet Regel-Details (R1-R5) mit Datenbasis.
- **Override:** Einmaliges "Sofort starten/pausieren" mit Timeout.
- **Stabilitaet:** Beim Start/Stop wird das Stabilitaetsfenster angezeigt.

&nbsp;

### Beispiel-Texts (Microcopy)

- "Miner startet: PV-Ueberschuss > 3 kW."
- "Miner pausiert: Haus-Reserve erreicht."
- "Miner bleibt aktiv bis 10:30 (Stabilitaetsfenster)."
- "Miner stoppt: Temperatur zu hoch."

&nbsp;

### Benoetigte Datenpunkte (UI-Sicht)

- PV-Leistung, Hauslast, Speicher-SoC, Netzbezug.
- Preisfenster und Forecast.
- Miner-Telemetrie (Status, Temperatur, Leistung).
- Aktiver Modus, Override-Status, Ruhezeiten.

&nbsp;

### Offene Fragen

- Welche Visualisierung erklaert den Energiefluss am schnellsten?
- Welche Detailtiefe ist im Alltag noch akzeptabel?
- Wie wird "zu viele Meldungen" vermieden, ohne Erklaerung zu verlieren?

&nbsp;

## 22.2 - Automotive-Interface (In-Car-UI)

### Zielbild

- Das Auto erklaert Ladeentscheidungen in 1-2 Sekunden Blickdauer.
- Proaktive, ruhige Kommunikation beim Anstecken.
- Eine klare Override-Aktion ohne lange Menues.

&nbsp;

### Designprinzipien

- **Glanceable:** Kurz, gross, eindeutig.
- **Warum + Wann:** Grund und Startzeitpunkt zuerst.
- **Minimaler Eingriff:** Ein Button, keine komplexen Settings.
- **Sicherheit:** Keine langen Interaktionen waehrend der Fahrt.

&nbsp;

### UI-Bausteine (Kernscreen)

- **Statuszeile:** "Verbunden mit Home Grid".
- **Grundsatzinfo:** "Warte auf PV-Ueberschuss" oder "Strompreis zu hoch".
- **Prognose:** "Start in ca. 20 Min".
- **Aktion:** "Sofort laden".
- **Optionaler Check:** "Faehst du morgen zur Arbeit?"

&nbsp;

### Interaktionen und Regeln

- **Beim Anstecken:** Sofortige Erklaerung + erwarteter Start.
- **Override:** Einmaliger Sofort-Start mit Kostenhinweis.
- **Pendler-Puffer:** Abfrage bei niedriger Reichweite oder Zeitdruck.

&nbsp;

### Beispielmeldungen (Persona)

- "Ich warte mit dem Laden, bis mehr Sonne da ist. Start voraussichtlich um 14:10."
- "Strom ist gerade teuer. Ich lade in 20 Minuten guenstiger."
- "Okay, ich lade jetzt mit Netzstrom. Das kostet heute etwa 2 Euro mehr."

&nbsp;

### Benoetigte Datenpunkte (UI-Sicht)

- Ladezustand, Ziel-SoC, Abfahrtszeit (optional).
- PV-Prognose, Preisfenster, Haus-Reserve-Status.
- Aktueller Regelzustand (R1-R5) und geplante Startzeit.

&nbsp;

### Offene Fragen

- Welche Erklaerungslaenge ist im Auto noch akzeptabel?
- Welche Trigger sind "proaktiv genug" ohne zu stoeren?
- Wie werden Konflikte zwischen Fahrerwunsch und Haus-Reserve vermittelt?

---

> **Naechster Schritt:** Das Interface-Design ist definiert.
> Im naechsten Kapitel wird der Evaluationsrahmen beschrieben.
>
> 👉 Weiter zu **[23 - Evaluationsrahmen](../evaluation_framework.md)**
>
> 🔙 Zurueck zu **[21 - BitGrid Prinzipien](../21_bitgrid_principles/README.md)**
>
> 🏠 Zurueck zur **[Hauptuebersicht](../../README.md)**
