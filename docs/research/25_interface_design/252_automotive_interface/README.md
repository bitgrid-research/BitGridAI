# 25.2 - Automotive-Interface (In-Car-UI)

### Zielbild

- Das Auto erklärt Ladeentscheidungen in 1-2 Sekunden Blickdauer.
- Proaktive, ruhige Kommunikation beim Anstecken.
- Eine klare Override-Aktion ohne lange Menüs.

&nbsp;

### Designprinzipien

- **Glanceable:** Kurz, gross, eindeutig.
- **Warum + Wann:** Grund und Startzeitpunkt zuerst.
- **Minimaler Eingriff:** Ein Button, keine komplexen Settings.
- **Sicherheit:** Keine langen Interaktionen während der Fahrt.

&nbsp;

### UI-Bausteine (Kernscreen)

- **Statuszeile:** "Verbunden mit Home Grid".
- **Grundsatzinfo:** "Warte auf PV-Überschuss" oder "Strompreis zu hoch".
- **Prognose:** "Start in ca. 20 Min".
- **Aktion:** "Sofort laden".
- **Optionaler Check:** "Fährst du morgen zur Arbeit?"

&nbsp;

### Interaktionen und Regeln

- **Beim Anstecken:** Sofortige Erklärung + erwarteter Start.
- **Override:** Einmaliger Sofort-Start mit Kostenhinweis.
- **Pendler-Puffer:** Abfrage bei niedriger Reichweite oder Zeitdruck.

&nbsp;

### Beispielmeldungen (Persona)

- "Ich warte mit dem Laden, bis mehr Sonne da ist. Start voraussichtlich um 14:10."
- "Strom ist gerade teuer. Ich lade in 20 Minuten günstiger."
- "Okay, ich lade jetzt mit Netzstrom. Das kostet heute etwa 2 Euro mehr."

&nbsp;

### Benötigte Datenpunkte (UI-Sicht)

- Ladezustand, Ziel-SoC, Abfahrtszeit (optional).
- PV-Prognose, Preisfenster, Haus-Reserve-Status.
- Aktueller Regelzustand (R1-R5) und geplante Startzeit.

&nbsp;

### Offene Fragen

- Welche Erklärungslänge ist im Auto noch akzeptabel?
- Welche Trigger sind "proaktiv genug" ohne zu stören?
- Wie werden Konflikte zwischen Fahrerwunsch und Haus-Reserve vermittelt?

---

> **Nächster Schritt:** Das Automotive-Interface ist beschrieben.
> Im nächsten Kapitel folgen die Szenarien & Use Cases.
>
> 👉 Weiter zu **[26 - Szenarien & Use Cases](../../26_scenarios_and_use_cases/README.md)**
>
> 🔙 Zurück zu **[25 - Interface Design](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**