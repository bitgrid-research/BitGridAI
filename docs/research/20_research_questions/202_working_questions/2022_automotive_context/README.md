# 20.2.2 - Automotive-Kontext

Der Automotive-Kontext fokussiert die Frage:
"Warum lädt mein Auto gerade - oder warum nicht - und wie erklärt mir das System die Entscheidung?"
Hier steht nicht die Optimierung im Vordergrund, sondern Verständnis, Vertrauen
und eine saubere, alltagstaugliche Erklärung im Fahrzeug.

&nbsp;

## Zielbild

- Das Auto wird zum erklärenden Akteur im Smart-Grid-Kontext.
- Entscheidungen aus dem HEMS werden transparent, kurz und proaktiv kommuniziert.
- Eine "Transparent Energy Persona" übersetzt Regeln (R1-R5) in klare Alltagssprache.

&nbsp;

## Unterseiten (Template)

- **[20.2.2a - Verstehen der Ladeentscheidung](./2022a_transparenz.md)**
  - Warum lädt das Auto gerade oder warum nicht?
- **[20.2.2b - Kontrolle im Auto](./2022b_kontrolle.md)**
  - Kann der Fahrer einfach eingreifen?
- **[20.2.2c - Vertrauen und Reichweitenangst](./2022c_vertrauen.md)**
  - Fühlt sich die Entscheidung im Auto sicher an?

&nbsp;

## Arbeitstitel (Auswahl)

- Designing Explainable Automotive Charging UIs
- Explainable Smart Charging im Automotive UI
- Gestaltung erklärbarer Lade-Interfaces im Automobil
- Designing Explainable V2H Interfaces
- Reducing Range Anxiety through Interface Design

&nbsp;

## Kernproblem (kompakt)

- Auto ist angesteckt, lädt aber nicht.
- UI zeigt Status, aber keine Begründung.
- Folge: Frust, Misstrauen, Reichweitenangst.

Design-Opportunity: Erklärende Rückmeldung im Auto-UI, die den Grund klar macht,
den nächsten Schritt nennt und optional Kontrolle anbietet.

&nbsp;

## Konzeptbausteine

### Transparent Energy Persona

- Tonalität: ruhig, hilfreich, vorausschauend.
- Prinzip: erst warum, dann was, dann wann.
- Keine Fachsprache ohne Nachfrage; kurz und "glanceable".

### Interaktionsprinzipien im Auto

- Blickdauer < 2 Sekunden.
- Proaktive Meldung beim Anstecken zu Hause.
- Einfache Override-Aktion ("Jetzt laden").
- Optionaler Pendler-Check: "Fähst du morgen zur Arbeit?"

&nbsp;

## User Journey (Kurzform)

1) Ankommen: Auto wird angesteckt, System entscheidet (z. B. Warten auf PV).
2) Erklärung: Persona nennt Grund + erwarteten Startzeitpunkt.
3) Kontrolle: Nutzer kann einmalig überschreiben.
4) Ergebnis: Verständnis statt "Warum passiert nichts?".

&nbsp;

## UI-Kernscreen (Auto)

- Status: "Verbunden mit Home Grid".
- Grundsatzinfo: "Warte auf PV-Überschuss" oder "Strompreis zu hoch".
- Prognose: "Start in ca. 20 Min".
- Frage: "Fähst du morgen zur Arbeit?" (Ja/Nein).
- Override: "Sofort laden".

&nbsp;

## Beispielmeldungen (Persona)

- "Ich pausiere das Laden kurz, der Strom ist gerade teuer. In 20 Minuten wird er günstiger."
- "Ich warte mit dem Laden, bis mehr Sonne da ist. Start voraussichtlich um 14:10."
- "Der Pendler-Puffer ist gesichert. Ich lade nur bis 40%, den Rest später mit PV."
- "Okay, ich lade jetzt mit Netzstrom. Das kostet heute etwa 2 Euro mehr."

&nbsp;

## Technischer Rahmen (Skizze)

- Das Auto ist eine steuerbare Last im BitGridAI-Controller.
- Entscheidungen kommen regelbasiert (R1-R5) und werden erklärt.
- Übertragung ins Auto-UI via MQTT, lokale LLM-Logik für Sprache.

Beispiel Topics:
- `bitgrid/decision/reason` -> "Warte auf PV-Überschuss > 3 kW"
- `bitgrid/prediction` -> "Ladestart voraussichtlich in 10 Min"

&nbsp;

## Annahmen und Risiken

- Annahme: Nutzer wollen verstehen, nicht optimieren.
- Annahme: Lokales LLM ist verfügbar (Privacy).
- Risiko: Zu viele Meldungen nerven.
- Risiko: Falsches Timing wirkt bevormundend.

&nbsp;

## Offene Fragen

- Welche Erklärungslänge ist im Auto noch verständlich?
- Welche Trigger sind "proaktiv genug" ohne zu stören?
- Welche Visualisierung ersetzt komplexe Diagramme?

---

> **Nächster Schritt:** Danach folgen die Kontext- und Diskussionsfragen,
> die den Ansatz reflektieren und abgrenzen.
>
> 👉 Weiter zu **[20.3 - Kontext- und Diskussionsfragen](../../203_discussion_questions/README.md)**
>
> 🔙 Zurück zu **[20.2 - Zentrale Arbeitsfragen](../README.md)**
>
> 🔙 Zurück zur **[Hauptübersicht](../../../../README.md)**
