# SH-WQ1 - Verstehen der Entscheidung (Transparenz)

Ziel: Der Nutzer versteht in einfachen Worten, warum der Miner läuft, pausiert oder stoppt.

&nbsp;

## Proto-Problem-Statement

- Das Dashboard zeigt nur "Miner läuft" oder "pausiert".
- Der Nutzer weiss nicht, ob das Absicht oder ein Fehler ist.
- Folge: Weniger Vertrauen und häufigere Eingriffe.

&nbsp;

## Proto-Persona

- Name: Nina NUTZER, 33
- NUTZER: Prosumer (Privathaushalt mit PV + Miner)
- ROLLE: Haushaltsbetreiberin, nutzt das Smart-Home-Dashboard
- Ausbildung/Hintergrund: kaufmännisch, technikoffen
- Kontext: tagsüber zu Hause, prüft PV- und Miner-Status
- Typische Aufgaben: Status lesen, Grund prüfen, Start/Stop verstehen
- Ziele: PV-Überschuss nutzen, keine Netzlast erzeugen
- Frust/Probleme: Miner steht trotz Sonne; Begründung zu technisch
- Erwartungen an UI: ein Satz "Warum", ein Satz "Wann", klare Vorhersage

&nbsp;

## Proto-Journey (Kurz)

1) Nina sieht: Sonne da, Miner steht.
2) Die App zeigt "Wartet auf stabilen Überschuss".
3) Sie tippt auf den Status und sieht den Grund.
4) Sie entscheidet: warten oder "Jetzt starten".

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SH-ASSUM-TRAN-01 | Nutzer entscheiden anhand kurzer Gründe, ob sie warten oder manuell starten. |
| SH-ASSUM-TRAN-02 | Ein Satz "Warum" plus eine klare Startprognose reduziert Nachfragen und Eingriffe. |
| SH-ASSUM-TRAN-03 | Nutzer bauen ein mentales Modell, wenn Grund und Datenbasis sichtbar sind. |
| SH-ASSUM-TRAN-04 | Erklärungen müssen in Alltagssprache sein; Fachbegriffe erzeugen Verwirrung. |
| SH-ASSUM-TRAN-05 | Die Datenbasis ist verlässlich genug, um Entscheidungen in Echtzeit zu erklären. |

&nbsp;

## Abgeleitete Forschungsfrage

Wie kann das Smart-Home-Dashboard Entscheidungsgrund, Datenbasis und Startprognose in Alltagssprache so darstellen, dass Nutzer die Entscheidung schnell verstehen, ein mentales Modell der Energieflüsse aufbauen und seltener eingreifen?

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug (Annahmen) | ASSUM IDs |
|-----|-----|-----|-----|-----|
| SH-TRAN-01 | Kurzgrund + Startzeit | Welche Kombination aus Grund und Startprognose reicht, damit Nutzer die Entscheidung ohne Nachfragen verstehen? | Kurzer Grund + Startprognose reduziert Eingriffe | SH-ASSUM-TRAN-01, SH-ASSUM-TRAN-02 |
| SH-TRAN-02 | Datenbasis | Welche Datenpunkte müssen sichtbar sein, damit ein mentales Modell der Energieflüsse entsteht? | Datenbasis sichtbar -> mentales Modell | SH-ASSUM-TRAN-03 |
| SH-TRAN-03 | Sprache | Welche Formulierungen in Alltagssprache vermeiden Fachbegriffe und bleiben verständlich? | Alltagssprache, Fachbegriffe verwirren | SH-ASSUM-TRAN-04 |
| SH-TRAN-04 | Aktualität | Wie aktuell und verlässlich muss die Anzeige sein, damit Erklärungen glaubwürdig bleiben? | Echtzeit und Verlässlichkeit | SH-ASSUM-TRAN-05 |

&nbsp;

## Erhebungsmethode (einfach)

| ID | Beschreibung |
|-----|--------------|
| EXP-SH-TRAN-01 | Kurztest mit Papier-UI oder Klick-Dummy (6-8 Personen, 20-30 Min). |
| EXP-SH-TRAN-02 | Think-aloud: Nutzer sagt laut, was er versteht. |
| EXP-SH-TRAN-03 | Erfolgskriterium: Nutzer kann den Grund in eigenen Worten wiedergeben. |

&nbsp;


## Leitfaden (8-10 Fragen)

1) Was glaubst du, passiert gerade?
2) Warum läuft der Miner jetzt nicht?
3) Welche Info fehlt dir, um sicher zu sein?
4) Ist der Grund in einem Satz für dich klar?
5) Was würdest du jetzt tun: warten oder starten?
6) Welche Stelle im UI hat dir am meisten geholfen?
7) Was ist dir wichtiger: Energie sparen oder sofort starten?
8) Wie würdest du den Grund einem Freund erklären?
9) Welche Worte sind zu technisch?
10) Was würdest du am Text ändern, damit es einfacher ist?

&nbsp;

## UI für Dummies (Kindergartenfassung)

| ID | Element |
|-----|---------|
| UI-SH-TRAN-01 | Grosse Ampel: "Miner läuft" / "Pausiert" / "Stoppt". |
| UI-SH-TRAN-02 | Ein Satz "Warum". |
| UI-SH-TRAN-03 | Ein Satz "Wann geht es weiter". |
| UI-SH-TRAN-04 | Ein Knopf "Mehr Info". |
| UI-SH-TRAN-05 | Ein Knopf "Jetzt starten". |


---

> **Nächster Schritt:** Als Nächstes geht es um Kontrolle und Override.
>
> 👉 Weiter zu **[SH-WQ2 - Kontrolle und Override](./2021b_kontrolle.md)**
>
> 🔙 Zurück zu **[SH-CONTEXT - Smart-Home-Kontext](./README.md)**
