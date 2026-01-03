# 20.2.2 - Automotive-Kontext

Der Automotive-Kontext fokussiert die Frage:
"Warum laedt mein Auto gerade - oder warum nicht - und wie erklaert mir das System die Entscheidung?"
Hier steht nicht die Optimierung im Vordergrund, sondern Verstaendnis, Vertrauen
und eine saubere, alltagstaugliche Erklaerung im Fahrzeug.

&nbsp;

## Zielbild

- Das Auto wird zum erklaerenden Akteur im Smart-Grid-Kontext.
- Entscheidungen aus dem HEMS werden transparent, kurz und proaktiv kommuniziert.
- Eine "Transparent Energy Persona" uebersetzt Regeln (R1-R5) in klare Alltagssprache.

&nbsp;

## Unterseiten (Template)

- **[20.2.2a - Verstehen der Ladeentscheidung](./2022a_transparenz.md)**
  - Warum laedt das Auto gerade oder warum nicht?
- **[20.2.2b - Kontrolle im Auto](./2022b_kontrolle.md)**
  - Kann der Fahrer einfach eingreifen?
- **[20.2.2c - Vertrauen und Reichweitenangst](./2022c_vertrauen.md)**
  - Fuehlt sich die Entscheidung im Auto sicher an?

&nbsp;

## Arbeitstitel (Auswahl)

- Designing Explainable Automotive Charging UIs
- Explainable Smart Charging im Automotive UI
- Gestaltung erklaerbarer Lade-Interfaces im Automobil
- Designing Explainable V2H Interfaces
- Reducing Range Anxiety through Interface Design

&nbsp;

## Kernproblem (kompakt)

- Auto ist angesteckt, laedt aber nicht.
- UI zeigt Status, aber keine Begruendung.
- Folge: Frust, Misstrauen, Reichweitenangst.

Design-Opportunity: Erklaerende Rueckmeldung im Auto-UI, die den Grund klar macht,
den naechsten Schritt nennt und optional Kontrolle anbietet.

&nbsp;

## Konzeptbausteine

### Transparent Energy Persona

- Tonalitaet: ruhig, hilfreich, vorausschauend.
- Prinzip: erst warum, dann was, dann wann.
- Keine Fachsprache ohne Nachfrage; kurz und "glanceable".

### Interaktionsprinzipien im Auto

- Blickdauer < 2 Sekunden.
- Proaktive Meldung beim Anstecken zu Hause.
- Einfache Override-Aktion ("Jetzt laden").
- Optionaler Pendler-Check: "Faehst du morgen zur Arbeit?"

&nbsp;

## User Journey (Kurzform)

1) Ankommen: Auto wird angesteckt, System entscheidet (z. B. Warten auf PV).
2) Erklaerung: Persona nennt Grund + erwarteten Startzeitpunkt.
3) Kontrolle: Nutzer kann einmalig ueberschreiben.
4) Ergebnis: Verstaendnis statt "Warum passiert nichts?".

&nbsp;

## UI-Kernscreen (Auto)

- Status: "Verbunden mit Home Grid".
- Grundsatzinfo: "Warte auf PV-Ueberschuss" oder "Strompreis zu hoch".
- Prognose: "Start in ca. 20 Min".
- Frage: "Faehst du morgen zur Arbeit?" (Ja/Nein).
- Override: "Sofort laden".

&nbsp;

## Beispielmeldungen (Persona)

- "Ich pausiere das Laden kurz, der Strom ist gerade teuer. In 20 Minuten wird er guenstiger."
- "Ich warte mit dem Laden, bis mehr Sonne da ist. Start voraussichtlich um 14:10."
- "Der Pendler-Puffer ist gesichert. Ich lade nur bis 40%, den Rest spaeter mit PV."
- "Okay, ich lade jetzt mit Netzstrom. Das kostet heute etwa 2 Euro mehr."

&nbsp;

## Technischer Rahmen (Skizze)

- Das Auto ist eine steuerbare Last im BitGridAI-Controller.
- Entscheidungen kommen regelbasiert (R1-R5) und werden erklaert.
- Uebertragung ins Auto-UI via MQTT, lokale LLM-Logik fuer Sprache.

Beispiel Topics:
- `bitgrid/decision/reason` -> "Warte auf PV-Ueberschuss > 3 kW"
- `bitgrid/prediction` -> "Ladestart voraussichtlich in 10 Min"

&nbsp;

## Annahmen und Risiken

- Annahme: Nutzer wollen verstehen, nicht optimieren.
- Annahme: Lokales LLM ist verfuegbar (Privacy).
- Risiko: Zu viele Meldungen nerven.
- Risiko: Falsches Timing wirkt bevormundend.

&nbsp;

## Offene Fragen

- Welche Erklaerungslaenge ist im Auto noch verstaendlich?
- Welche Trigger sind "proaktiv genug" ohne zu stoeren?
- Welche Visualisierung ersetzt komplexe Diagramme?

---

> **Naechster Schritt:** Danach folgen die Kontext- und Diskussionsfragen,
> die den Ansatz reflektieren und abgrenzen.
>
> ?? Weiter zu **[20.3 - Kontext- und Diskussionsfragen](../../203_discussion_questions/README.md)**
>
> ?? Zurueck zu **[20.2 - Zentrale Arbeitsfragen](../README.md)**
>
> ?? Zurueck zur **[Hauptuebersicht](../../../../README.md)**
