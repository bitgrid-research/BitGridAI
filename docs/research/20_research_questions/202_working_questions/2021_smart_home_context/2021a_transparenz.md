# 20.2.1.1 - SH-WQ1 - Verstehen der Entscheidung (Transparenz)

Ziel: Nutzer erkennen in unter 30 Sekunden, warum der Miner laeuft, pausiert oder stoppt, ohne nach Daten suchen zu muessen.

&nbsp;

## Nutzungskontext (Smart Home)

- Web-/App-Dashboard zu Hause; Blickdauer meist 30-60 Sekunden.
- Haeufiger Check: Mittag (PV hoch), Abend (Reserve greift), nach Wolke (Stabilisierung).
- Keine Bereitschaft fuer Fachbegriffe; Alltagssprache, ein Satz "Warum", ein Satz "Wann".

&nbsp;

## Proto-Persona

**Persona:** Lea Klar, 33  
**Rolle:** Haushaltsbetreiberin, Prosumer (PV + Miner)  
**Nutzungstyp:** Routine-Check mittags/abends  
**Technische Affinitaet:** mittel, keine Lust auf Fehlersuche  
**Primärer Nutzungskontext:** kurzer Blick auf Dashboard (30-60s) bei PV-Ueberschuss oder Reserve-Veto  
**Mentales Modell:** Automatik arbeitet regelbasiert; Reserve darf nicht verletzt werden; Mining ist nice-to-have  
**Ziel der Persona:** In einem Satz verstehen, warum der Miner laeuft/pausiert/stoppt und ob Eingriff noetig ist  
**Relevante Einschraenkungen:** Keine Zeit fuer Details; Fachbegriffe verwirrend; erwartet Klartext + Timer

&nbsp;

## Proto-Problem-Statement

- Dashboard zeigt nur Status (laeuft/pausiert), Grund und Prognose fehlen oder sind technisch.
- Reserve-Veto und Stabilisierung wirken wie Fehler, nicht wie Absicht.
- Folge: Zweifel an der Automatik, manuelle Eingriffe, Abschalten des Miners.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SH-ASSUM-TRAN-01 | Ein Satz "Warum" + ein Satz "Wann" reichen fuer Akzeptanz im Alltag. |
| SH-ASSUM-TRAN-02 | Alltagssprache wird schneller verstanden als Regel-/Technikbegriffe. |
| SH-ASSUM-TRAN-03 | Reserve-Veto wird akzeptiert, wenn Schwelle und Grund sichtbar sind. |
| SH-ASSUM-TRAN-04 | Countdown/naechster Check verhindert Fehlinterpretation als Fehler. |
| SH-ASSUM-TRAN-05 | Icon + sehr kurzer Text werden schneller wahrgenommen als Text allein. |

&nbsp;

## Kritische Annahme

- Ein Satz "Warum" + ein Satz "Wann" in Alltagssprache reichen aus, damit Nutzer die Entscheidung als absichtsvoll akzeptieren und seltener manuell eingreifen.

&nbsp;

## Abgeleitete Forschungsfrage

**Wie muessen Grund, Prognose und Reserve-Hinweis im Smart-Home-Dashboard dargestellt werden (Text + Icon), damit Nutzer die regelbasierte Entscheidung als absichtsvoll verstehen und seltener eingreifen?**

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|-------|-----------|-------|
| SH-TRAN-01 | Kernbotschaft | Reichen Grund + Startzeit fuer Verstaendnis? | ASSUM-01,02 |
| SH-TRAN-02 | Reserve-Sichtbarkeit | Wie zeigen wir das Veto der Haus-Reserve so, dass es akzeptiert wird? | ASSUM-03 |
| SH-TRAN-03 | Timing | Verhindert ein Countdown/naechster Check Fehlinterpretation als Fehler? | ASSUM-04 |
| SH-TRAN-04 | Darstellung | Welche Kombination aus Icon + Kurztext wird am schnellsten verstanden? | ASSUM-05 |

&nbsp;

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|---------|-------|
| EXP-SH-TRAN-01 | 30s Blicktest: Grund + Wann erfassbar? | Baseline-Verstaendnis |
| EXP-SH-TRAN-02 | A/B: Fachbegriff vs. Alltagssprache | Sprachverstaendnis |
| EXP-SH-TRAN-03 | Think-aloud bei Reserve-Veto | Mentales Modell |

&nbsp;

## UI-Prinzipien (abgeleitet aus Persona & WQ1)

- Warum + Wann immer gekoppelt: Kurzgrund + Start/Stopp-Zeit oder Countdown in einer Zeile.
- Alltagssprache statt Regel-Code: "Wartet auf stabilen PV-Ueberschuss" statt "R1 Stabilisierung".
- Reserve sichtbar machen: Schwelle oder Veto-Tag (R2) anzeigen, wenn Reserve blockiert.
- Multimodal kurz: Icon + ein Satz; Details hinter "Mehr" verstecken, nicht auf der Startkarte.
- Kein Blindflug: Naechster Check/Uhrzeit immer zeigen, damit Flapping als Stabilisierung lesbar ist.

&nbsp;

## Beobachtungspunkte

- Wie schnell wird der Grund genannt (Sekunden bis richtige Erklaerung)?
- Wird Reserve-Veto als Schutz statt als Fehler verstanden?
- Nutzen Nutzer den "Mehr"-Link oder reicht die Kurzinfo?

&nbsp;

## Artefakte / UI

- Status-Karte: Icon + Text "Grund" | "Weiter in/ab".
- Reserve-Hinweis: Tag/Badge "Haus-Reserve aktiv" + Schwellenwert.
- Optional: kleines Overlay-Chart mit aktueller Leistung vs. Schwelle (on demand).

&nbsp;

## Minimale UI-Elemente

| ID | Element |
|----|---------|
| UI-SH-TRAN-01 | Statuskarte mit Icon + Kurzgrund + Countdown/Startzeit. |
| UI-SH-TRAN-02 | Badge "Haus-Reserve aktiv" mit Schwellenwert. |
| UI-SH-TRAN-03 | Link/Knopf "Mehr" fuer Detail-Overlay (optional). |

&nbsp;

## Messkriterien (einfach)

- < 30s bis zur korrekten Nennung von Grund und Prognose.
- 80% interpretieren Reserve-Veto korrekt als Schutz.
- < 1 manuelle Intervention pro Woche wegen Unklarheit.

&nbsp;

## Zusammenfassung

Alltagssprache + Kurzgrund/Countdown machen die Entscheidung erfassbar, ein sichtbares Reserve-Badge entkraeftet Fehlinterpretationen, und ein optionales Detail-Overlay haelt die Startkarte schlank.

---

> **Naechster Schritt:** Als naechstes geht es um Kontrolle und Override.
>
> Weiter zu **[20.2.1.2 - SH-WQ2 - Kontrolle und Override](./2021b_kontrolle.md)**
>
> Zurueck zu **[20.2.1 - SH-CONTEXT - Smart-Home-Kontext](./README.md)**

