# 25.1 - Smart-Home-Interface (Dashboard)

### Zielbild

- Das Haus ist das Kontrollzentrum: Nutzer sehen Energiefluss und Entscheidung in einem Blick.
- Entscheidungen sind begründet, nicht nur angezeigt ("Warum" vor "Was").
- Manuelle Kontrolle ist jederzeit möglich, ohne die Automatik zu zerstören.

&nbsp;

### Designprinzipien

- **Erklären statt optimieren:** Primar geht es um Verständnis.
- **Ursache vor Aktion:** Grund + Auslöser vor Statuswechsel.
- **Stabilität zeigen:** R5-Stabilitätsfenster sichtbar machen.
- **Haus-Reserve schützen:** R2 wird als klare Grenze visualisiert.

&nbsp;

### Informationsarchitektur (Kernbereiche)

1) **Jetzt**: Live-Energiefluss (PV, Haus, Speicher, Miner, Netz).
2) **Entscheidung**: Aktuelle Aktion + begründeter Grund.
3) **Kontrolle**: Override, Modi, Limits, Ruhezeiten.

&nbsp;

### Kern-Screens

- **Dashboard:** Energiefluss + Decision Card + Schnellaktionen.
- **Details Miner:** Temperatur, Leistung, Fehlerstatus, Historie.
- **Planung/Prognose:** 24h PV/Preis-Graph + geplante Mining-Fenster.
- **Einstellungen:** Haus-Reserve, Ruhezeiten, Modi (Eco, Ruhe, Max PV).

&nbsp;

### Interaktionen und Regeln

- **Warum?** Link öffnet Regel-Details (R1-R5) mit Datenbasis.
- **Override:** Einmaliges "Sofort starten/pausieren" mit Timeout.
- **Stabilität:** Beim Start/Stop wird das Stabilitätsfenster angezeigt.

&nbsp;

### Beispiel-Texts (Microcopy)

- "Miner startet: PV-Überschuss > 3 kW."
- "Miner pausiert: Haus-Reserve erreicht."
- "Miner bleibt aktiv bis 10:30 (Stabilitätsfenster)."
- "Miner stoppt: Temperatur zu hoch."

&nbsp;

### Benötigte Datenpunkte (UI-Sicht)

- PV-Leistung, Hauslast, Speicher-SoC, Netzbezug.
- Preisfenster und Forecast.
- Miner-Telemetrie (Status, Temperatur, Leistung).
- Aktiver Modus, Override-Status, Ruhezeiten.

&nbsp;

### Offene Fragen

- Welche Visualisierung erklärt den Energiefluss am schnellsten?
- Welche Detailtiefe ist im Alltag noch akzeptabel?
- Wie wird "zu viele Meldungen" vermieden, ohne Erklärung zu verlieren?

---

> **Nächster Schritt:** Das Smart-Home-Interface ist beschrieben.
> Im nächsten Unterkapitel folgt das Automotive-Interface.
>
> 👉 Weiter zu **[25.2 - Automotive-Interface (In-Car-UI)](../252_automotive_interface/README.md)**
>
> 🔙 Zurück zu **[25 - Interface Design](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**