# 20.2.2.2 - AUTO-WQ2 - Kontrolle im Auto

Ziel: Fahrer kann mit 1-2 Aktionen eingreifen, ohne Ablenkung.

&nbsp;

## Proto-Problem-Statement

- Das System wartet auf PV oder günstigen Preis.
- Der Fahrer braucht aber manchmal sofortige Reichweite.
- Wenn der Override nicht sichtbar ist, entsteht Stress.

&nbsp;

## Proto-Persona

- Name: Felix FAHRER, 29
- NUTZER: Prosumer (E-Auto-Fahrer im HEMS)
- ROLLE: Fahrer, braucht schnellen Override im Fahrzeug
- Ausbildung/Hintergrund: technikaffin, ungeduldig
- Kontext: spontane Fahrt am Abend, Auto ist angesteckt
- Typische Aufgaben: "Jetzt laden" tippen, Bestätigung lesen
- Ziele: schnell Reichweite, kein Menü
- Frust/Probleme: zu viele Schritte, kleine Buttons
- Erwartungen an UI: grosser Button, kurze Bestätigung, 1-2 Aktionen

&nbsp;

## Proto-Journey (Kurz)

1) Felix sieht "Wartet auf PV".
2) Er tippt "Jetzt laden".
3) Das System bestätigt und startet.
4) Optional: Er beantwortet "Morgen zur Arbeit? Ja/Nein".

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| AUTO-ASSUM-CTRL-01 | Fahrer brauchen eine Ein-Klick-Aktion ("Jetzt laden") ohne Menüs. |
| AUTO-ASSUM-CTRL-02 | Bestätigungen müssen kurz sein und die Aktion sofort sichtbar machen. |
| AUTO-ASSUM-CTRL-03 | Override ist selten, aber in Stresssituationen entscheidend. |
| AUTO-ASSUM-CTRL-04 | Eine optionale Pendlerfrage darf nicht stören und muss in 1 Tap beantwortet sein. |
| AUTO-ASSUM-CTRL-05 | Sprachaktion kann sinnvoll sein, wenn Tippen ablenkt. |

&nbsp;

## Abgeleitete Forschungsfrage

Welche minimalen Eingriffe (One-Tap-Override, kurze Bestätigung, optionale Pendlerfrage/Voice) erlauben schnelle Kontrolle im Fahrzeug ohne Ablenkung?

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug (Annahmen) | ASSUM IDs |
|-----|-----|-----|-----|-----|
| AUTO-CTRL-01 | One-Tap | Reicht ein einzelner "Jetzt laden"-Button ohne Menüs? | Ein-Klick-Aktion | AUTO-ASSUM-CTRL-01, AUTO-ASSUM-CTRL-03 |
| AUTO-CTRL-02 | Rückmeldung | Welche Bestätigung macht den Start sofort sichtbar? | Bestätigungen müssen kurz sein | AUTO-ASSUM-CTRL-02 |
| AUTO-CTRL-03 | Pendlerfrage | Wie lässt sich die Pendlerfrage in einem Tap beantworten, ohne zu stören? | 1 Tap, nicht störend | AUTO-ASSUM-CTRL-04 |
| AUTO-CTRL-04 | Voice | Wann ist Sprachaktion hilfreicher als Tippen? | Sprachaktion reduziert Ablenkung | AUTO-ASSUM-CTRL-05 |

&nbsp;

## Erhebungsmethode (einfach)

| ID | Beschreibung |
|-----|--------------|
| EXP-AUTO-CTRL-01 | Szenario-Test im Stand (Parkmodus). |
| EXP-AUTO-CTRL-02 | Zeitmessung: Wie schnell wird die Aktion gefunden? |
| EXP-AUTO-CTRL-03 | Kurzes Interview danach. |

&nbsp;


## Leitfaden (8-10 Fragen)

1) Was würdest du hier als Erstes tun?
2) Findest du "Jetzt laden" sofort?
3) Ist der Knopf gross genug?
4) Brauchst du eine Bestätigung?
5) Welche Info brauchst du vor dem Start (Preis, Zeit)Ö
6) Ist die Frage "Morgen zur Arbeit?" hilfreich oder störend?
7) Würdest du lieber eine Sprachaktion nutzen?
8) Wie lange darf der Override gelten?
9) Wann würdest du die Automatik deaktivieren?
10) Was sollte noch einfacher werden?

&nbsp;

## UI für Dummies (Kindergartenfassung)

| ID | Element |
|-----|---------|
| UI-AUTO-CTRL-01 | Grosser Knopf "Jetzt laden". |
| UI-AUTO-CTRL-02 | Eine kurze Bestätigung: "OK, startet jetzt". |
| UI-AUTO-CTRL-03 | Eine Ja/Nein-Frage zur Pendlerfahrt. |
| UI-AUTO-CTRL-04 | Kein Untermenü, kein Scrollen. |


---

> **Nächster Schritt:** Als Nächstes geht es um Vertrauen und Reichweitenangst.
>
> 👉 Weiter zu **[20.2.2.3 - AUTO-WQ3 - Vertrauen und Reichweitenangst](./2022c_vertrauen.md)**
>
> 🔙 Zurück zu **[20.2.2 - AUTO-CONTEXT - Automotive-Kontext](./README.md)**
