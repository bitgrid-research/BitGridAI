# SH-WQ3 - Vertrauen und Sicherheit (Haus-Reserve)

Ziel: Nutzer sieht klar, dass genug Energie für das Haus bleibt.

&nbsp;

## Proto-Problem-Statement

- Nutzer hat Angst, dass Mining die Hausversorgung gefährdet.
- Die Haus-Reserve ist unsichtbar oder zu technisch.
- Folge: Nutzer stoppt Mining dauerhaft.

&nbsp;

## Proto-Persona

- Name: Hanna HAUSHALT, 41
- NUTZER: Prosumer (PV + Speicher + Miner)
- ROLLE: Haushaltsverantwortliche, prüft die Haus-Reserve
- Ausbildung/Hintergrund: bürotauglich, wenig Zeit
- Kontext: morgens und abends, will Hausreserve sicher sehen
- Typische Aufgaben: Reserve pflegen, Puffer prüfen, Hausstatus checken
- Ziele: Grundversorgung sichern, keine Überraschung
- Frust/Probleme: Reserve unklar; keine Sicherheit sichtbar
- Erwartungen an UI: klare Reserveanzeige, "Haus gesichert: Ja/Nein"

&nbsp;

## Proto-Journey (Kurz)

1) Hanna legt eine Haus-Reserve fest.
2) Das UI zeigt den gesperrten Bereich.
3) Sie sieht "Haus gesichert: Ja".
4) Sie lässt die Automatik laufen.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SH-ASSUM-TRUST-01 | Eine sichtbare Haus-Reserve ist der zentrale Vertrauensanker. |
| SH-ASSUM-TRUST-02 | "Haus gesichert: Ja/Nein" ist für Laien klarer als Detailwerte. |
| SH-ASSUM-TRUST-03 | Nutzer wollen einen einstellbaren Puffer, greifen aber selten in Details ein. |
| SH-ASSUM-TRUST-04 | Eine einfache Visualisierung reduziert Unsicherheit schneller als Diagramme. |
| SH-ASSUM-TRUST-05 | Wenn die Reserve unklar ist, stoppen Nutzer Mining langfristig. |

&nbsp;

## Abgeleitete Forschungsfrage

Wie muss die Haus-Reserve im Smart-Home-UI visualisiert und formuliert werden, damit Nutzer die Versorgungssicherheit sofort erkennen, Vertrauen aufbauen und die Automatik laufen lassen?

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug (Annahmen) | ASSUM IDs |
|-----|-----|-----|-----|-----|
| SH-TRUST-01 | Kernbotschaft | Reicht "Haus gesichert: Ja/Nein" als primäre Aussage oder braucht es Prozentwerte? | Ja/Nein klarer als Detailwerte | SH-ASSUM-TRUST-02, SH-ASSUM-TRUST-01 |
| SH-TRUST-02 | Visualisierung | Welche Darstellungsform (Balken, Batterie, Text) reduziert Unsicherheit am stärksten? | Einfache Visualisierung statt Diagramme | SH-ASSUM-TRUST-04 |
| SH-TRUST-03 | Einstellbarkeit | Wie viel Kontrolle über die Reserve wird tatsächlich genutzt? | Puffer einstellbar, Details selten genutzt | SH-ASSUM-TRUST-03 |
| SH-TRUST-04 | Verhalten | Wie beeinflusst Reserve-Transparenz die Bereitschaft, Mining laufen zu lassen? | Unklare Reserve -> Mining stoppen | SH-ASSUM-TRUST-05 |

&nbsp;

## Erhebungsmethode (einfach)

| ID | Beschreibung |
|-----|--------------|
| EXP-SH-TRUST-01 | A/B-Test zweier Puffer-Darstellungen (Balken vs. Text). |
| EXP-SH-TRUST-02 | Verständnis-Check: "Was ist gesichert?" |
| EXP-SH-TRUST-03 | Kurzes Interview zu Vertrauen. |

&nbsp;


## Leitfaden (8-10 Fragen)

1) Siehst du auf den ersten Blick, ob das Haus sicher ist?
2) Was bedeutet der markierte Bereich?
3) Wieviel Prozent bleiben dem Haus sicher?
4) Fühlst du dich mit dieser Reserve sicher?
5) Was würde dich noch beruhigen?
6) Würdest du die Reserve selber einstellen?
7) Wann würdest du die Reserve ignorieren?
8) Vertraust du dem System, wenn der Miner läuft?
9) Welche Anzeige ist für dich klarer: Balken oder Text?
10) Was fehlt dir, damit du der Automatik traust?

&nbsp;

## UI für Dummies (Kindergartenfassung)

| ID | Element |
|-----|---------|
| UI-SH-TRUST-01 | Batterie mit zwei Farben: "Reserve" und "Frei für Miner". |
| UI-SH-TRUST-02 | Grosser Text: "Haus gesichert: Ja/Nein". |
| UI-SH-TRUST-03 | Ein Satz: "Haus-Reserve = 30%". |
| UI-SH-TRUST-04 | Ein Knopf: "Reserve ändern". |
| UI-SH-TRUST-05 | Kein Detail-Graph. |


---

> **Nächster Schritt:** Danach geht es weiter mit dem Automotive-Kontext.
>
> 👉 Weiter zu **[AUTO-CONTEXT - Automotive-Kontext](../2022_automotive_context/README.md)**
>
> 🔙 Zurück zu **[SH-CONTEXT - Smart-Home-Kontext](./README.md)**
