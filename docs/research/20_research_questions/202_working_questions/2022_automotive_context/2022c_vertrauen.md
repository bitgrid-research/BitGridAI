# 20.2.2.3 - AUTO-WQ3 - Vertrauen und Reichweitenangst

Ziel: Fahrer sieht klar, dass genug Reichweite für morgen bleibt.

&nbsp;

## Proto-Problem-Statement

- Das Auto dient als Speicher für das Haus (V2H).
- Fahrer hat Angst, dass der Akku am Morgen zu leer ist.
- Ohne klare Anzeige entsteht Reichweitenangst.

&nbsp;

## Proto-Persona

- Name: Petra PENDLER, 36
- NUTZER: Prosumer (Pendlerin, lädt zu Hause und Arbeit)
- ROLLE: Fahrerin, will Reichweiten-Garantie im Auto-UI
- Ausbildung/Hintergrund: bürotauglich, plant den Tag
- Kontext: pendelt, lädt zu Hause und bei der Arbeit
- Typische Aufgaben: "Bereit für morgen" checken, Arbeitsweg bestätigen
- Ziele: sicher zur Arbeit kommen, ohne ständig zu prüfen
- Frust/Probleme: unklare Reserve, unsicherer Puffer
- Erwartungen an UI: klare Pufferanzeige, Ja/Nein zur Pendlerfahrt

&nbsp;

## Proto-Journey (Kurz)

1) Petra kommt heim und steckt an.
2) Das Display zeigt "Puffer gesichert".
3) Sie sieht "Bereit für morgen: Ja".
4) Sie lässt die Automatik laufen.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| AUTO-ASSUM-TRUST-01 | Reichweitenangst sinkt, wenn ein sicherer Puffer klar ausgewiesen ist. |
| AUTO-ASSUM-TRUST-02 | "Bereit für morgen: Ja/Nein" ist schneller erfassbar als Prozentwerte. |
| AUTO-ASSUM-TRUST-03 | Nutzer erwarten, dass V2H den Pendlerpuffer nie unterschreitet. |
| AUTO-ASSUM-TRUST-04 | Eine einfache Batterievisualisierung ist verständlicher als Diagramme. |
| AUTO-ASSUM-TRUST-05 | Wenn der Puffer unklar ist, deaktivieren Nutzer die Automatik. |

&nbsp;

## Abgeleitete Forschungsfrage

Wie muss der Pendler-Puffer im Auto-UI angezeigt werden (Ja/Nein, Prozent, Batterie), damit Fahrer Reichweitenangst verlieren, den Puffer verstehen und der V2H-Logik vertrauen?

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug (Annahmen) | ASSUM IDs |
|-----|-----|-----|-----|-----|
| AUTO-TRUST-01 | Kernbotschaft | Ist "Bereit für morgen: Ja/Nein" schneller verständlich als Prozentwerte? | Ja/Nein schneller erfassbar | AUTO-ASSUM-TRUST-02, AUTO-ASSUM-TRUST-01 |
| AUTO-TRUST-02 | Visualisierung | Welche Darstellung (Batterie vs Text) erzeugt das höchste Sicherheitsgefühl? | Batterievisualisierung verständlicher | AUTO-ASSUM-TRUST-04 |
| AUTO-TRUST-03 | Puffer-Regel | Wie muss kommuniziert werden, dass der Pendlerpuffer nie unterschritten wird? | Erwartung: nie unterschreiten | AUTO-ASSUM-TRUST-03 |
| AUTO-TRUST-04 | Verhalten | Wie beeinflusst die Pufferanzeige die Bereitschaft, die Automatik aktiviert zu lassen? | Unklarer Puffer -> Automatik aus | AUTO-ASSUM-TRUST-05 |

&nbsp;

## Erhebungsmethode (einfach)

| ID | Beschreibung |
|-----|--------------|
| EXP-AUTO-TRUST-01 | Szenario-Interview mit zwei UI-Varianten (Text vs. Batterie). |
| EXP-AUTO-TRUST-02 | Verständnis-Check: "Wie viel ist sicher?" |
| EXP-AUTO-TRUST-03 | Kurze Skala: "Wie sicher fühlst du dich?" |

&nbsp;


## Leitfaden (8-10 Fragen)

1) Siehst du sofort, ob du morgen fahren kannst?
2) Was bedeutet "Puffer gesichert" für dich?
3) Wie viel Prozent bleiben dir sicher?
4) Fühlst du dich mit dieser Anzeige beruhigt?
5) Was würde dich noch beruhigen?
6) Würdest du den Puffer selber einstellen?
7) Vertraust du dem System, wenn es entlädt?
8) Welche Anzeige ist klarer: Batterie oder Text?
9) Wann würdest du die Automatik ausschalten?
10) Was fehlt, damit du dich sicher fühlst?

&nbsp;

## UI für Dummies (Kindergartenfassung)

| ID | Element |
|-----|---------|
| UI-AUTO-TRUST-01 | Batterie mit zwei Farben: "Sicher" und "Frei". |
| UI-AUTO-TRUST-02 | Grosser Text: "Bereit für morgen: Ja/Nein". |
| UI-AUTO-TRUST-03 | Ein Satz: "Sicherer Puffer = 30%". |
| UI-AUTO-TRUST-04 | Ein Knopf: "Arbeitsweg ändern". |


---

> **Nächster Schritt:** Danach folgen die Kontext- und Diskussionsfragen.
>
> 👉 Weiter zu **[20.3 - DQ - Kontext- und Diskussionsfragen](../../203_discussion_questions/README.md)**
>
> 🔙 Zurück zu **[20.2.2 - AUTO-CONTEXT - Automotive-Kontext](./README.md)**
