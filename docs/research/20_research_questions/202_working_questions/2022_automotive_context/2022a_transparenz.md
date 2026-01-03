# AUTO-WQ1 - Verstehen der Ladeentscheidung

Ziel: Fahrer versteht in 2 Sekunden, warum das Auto lädt oder nicht.

&nbsp;

## Proto-Problem-Statement

- Das Auto zeigt nur "Nicht laden".
- Der Fahrer weiss nicht, ob das Absicht oder ein Fehler ist.
- Folge: Frust und Misstrauen.

&nbsp;

## Proto-Persona

- Name: Fiona FAHRER, 42
- NUTZER: Prosumer (E-Auto-Fahrerin im HEMS)
- ROLLE: Fahrerin, sieht die Kurzinfo im Auto-UI
- Ausbildung/Hintergrund: nicht technisch, will einfache Sprache
- Kontext: kommt abends nach Hause, wenig Zeit
- Typische Aufgaben: kurzer Blick aufs Display, ggf. Voice bestätigen
- Ziele: schnell verstehen, dann einfach loslassen
- Frust/Probleme: "Nicht laden" ohne Grund
- Erwartungen an UI: 1 Satz Grund + Startzeit, optional Voice

&nbsp;

## Proto-Journey (Kurz)

1) Fiona steckt das Auto an.
2) Das Display zeigt Grund und Startzeit.
3) Eine Voice-Ansage sagt einen Satz.
4) Fiona versteht und geht rein.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| AUTO-ASSUM-TRAN-01 | Fahrer haben maximal 2 Sekunden Aufmerksamkeit; Texte müssen extrem kurz sein. |
| AUTO-ASSUM-TRAN-02 | Ein Grund plus Startzeit reicht, um die Entscheidung zu akzeptieren. |
| AUTO-ASSUM-TRAN-03 | Ohne Erklärung wird "Nicht laden" als Fehler interpretiert. |
| AUTO-ASSUM-TRAN-04 | Icons plus kurzer Text sind schneller als nur Text. |
| AUTO-ASSUM-TRAN-05 | Eine optionale Voice-Ansage kann die visuelle Info bestätigen. |

&nbsp;

## Abgeleitete Forschungsfrage

Wie kann das Auto-UI Gründe und Startzeit so kurz und klar kommunizieren (Text, Icon, optional Voice), dass Fahrer die Entscheidung in unter 2 Sekunden verstehen und nicht als Fehler interpretieren?

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug (Annahmen) | ASSUM IDs |
|-----|-----|-----|-----|-----|
| AUTO-TRAN-01 | Textlänge | Welche maximale Textlänge ist im 2-Sekunden-Blick verständlich? | Aufmerksamkeit < 2 Sekunden | AUTO-ASSUM-TRAN-01 |
| AUTO-TRAN-02 | Inhalt | Reicht Grund + Startzeit oder braucht es zusätzliche Information? | Grund + Startzeit reicht | AUTO-ASSUM-TRAN-02, AUTO-ASSUM-TRAN-03 |
| AUTO-TRAN-03 | Darstellung | Was ist schneller: Icon + kurzer Text oder nur Text? | Icons plus Text sind schneller | AUTO-ASSUM-TRAN-04 |
| AUTO-TRAN-04 | Voice | Wann verbessert eine kurze Voice-Ansage das Verständnis, ohne zu stören? | Optionale Voice kann bestätigen | AUTO-ASSUM-TRAN-05 |

&nbsp;

## Erhebungsmethode (einfach)

| ID | Beschreibung |
|-----|--------------|
| EXP-AUTO-TRAN-01 | Blick-Test mit 2-Sekunden-Regel. |
| EXP-AUTO-TRAN-02 | A/B-Vergleich kurzer Texte und Icons. |
| EXP-AUTO-TRAN-03 | Kurze Nachfrage: "Was passiert und warum?" |

&nbsp;


## Leitfaden (8-10 Fragen)

1) Was ist dein erster Eindruck?
2) Warum lädt das Auto gerade nicht?
3) Welche Worte waren zu lang?
4) Welche Info hat dir gefehlt?
5) Erinnerst du dich an die Startzeit?
6) Würdest du eine Voice-Ansage wollen?
7) Wenn ja, wie kurz soll sie sein?
8) Welche Darstellung ist am klarsten: Icon, Text, beides?
9) Wann würdest du eine Meldung wegdrücken?
10) Was würde dich beruhigen?

&nbsp;

## UI für Dummies (Kindergartenfassung)

| ID | Element |
|-----|---------|
| UI-AUTO-TRAN-01 | Grosses Symbol (Stecker + Haus). |
| UI-AUTO-TRAN-02 | Eine Zeile Grund. |
| UI-AUTO-TRAN-03 | Eine Zeile "Start in X Min". |
| UI-AUTO-TRAN-04 | Ein Knopf "Jetzt laden". |
| UI-AUTO-TRAN-05 | Optional: 1 Satz Voice. |


---

> **Nächster Schritt:** Als Nächstes geht es um Kontrolle im Auto.
>
> 👉 Weiter zu **[AUTO-WQ2 - Kontrolle im Auto](./2022b_kontrolle.md)**
>
> 🔙 Zurück zu **[AUTO-CONTEXT - Automotive-Kontext](./README.md)**
