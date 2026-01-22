# 20.2.1.1 - SH-WQ1 - Verstehen der Entscheidung (Transparenz)

Ziel: Nutzer erkennen in unter 30 Sekunden, warum der Miner läuft, pausiert oder stoppt, ohne nach Daten suchen zu müssen.

&nbsp;

## Nutzungskontext (Smart Home)

- Web-/App-Dashboard zu Hause; Blickdauer meist 30-60 Sekunden.
- Häufiger Check: Mittag (PV hoch), Abend (Reserve greift), nach Wolke (Stabilisierung).
- Keine Bereitschaft für Fachbegriffe; Alltagssprache, ein Satz "Warum", ein Satz "Wann".

&nbsp;

## Proto-Persona

**Persona:** Lea Klar, 33  
**Rolle:** Haushaltsbetreiberin, Prosumer (PV + Miner)  
**Nutzungstyp:** Routine-Check mittags/abends  
**Technische Affinität:** mittel, keine Lust auf Fehlersuche  
**Primärer Nutzungskontext:** kurzer Blick auf Dashboard (30-60s) bei PV-Überschuss oder Reserve-Veto  
**Mentales Modell:** Automatik arbeitet regelbasiert; Reserve darf nicht verletzt werden; Mining ist nice-to-have  
**Ziel der Persona:** In einem Satz verstehen, warum der Miner läuft/pausiert/stoppt und ob Eingriff nötig ist  
**Relevante Einschränkungen:** Keine Zeit für Details; Fachbegriffe verwirrend; erwartet Klartext + Timer

&nbsp;

## Synthetisches Interview (Lea Klar)

**Setting:** 20-min Remote-Interview, Kontext Smart-Home-Dashboard, kurzer Blick zwischendurch.  
**Ziel:** Pain Points, Verständnis, Sprache, Vertrauen.

**Interviewer:** Wann schaust du typischerweise ins Dashboard?  
**Lea:** Mittags, wenn die Sonne da ist, und abends, wenn wir kochen. Meist nur kurz aufs Handy, 30-60 Sekunden.

**Interviewer:** Was willst du in diesem kurzen Blick als erstes sehen?  
**Lea:** Warum der Miner läuft oder nicht. Ein Satz reicht. Und wann sich das ändert.

**Interviewer:** Was nervt dich aktuell am meisten?  
**Lea:** Der Grund fehlt oder ist so technisch, dass ich ihn nicht verstehe.

**Interviewer:** Was passiert, wenn du den Grund nicht sofort verstehst?  
**Lea:** Dann denke ich, etwas stimmt nicht, und ich schalte lieber manuell aus.

**Interviewer:** Welche Situationen wirken wie "Fehler", sind aber eigentlich normal?  
**Lea:** Wenn er kurz stoppt oder ständig an und aus geht. Das sieht für mich aus wie ein Problem.

**Interviewer:** Was fehlt dir in solchen Momenten?  
**Lea:** Ein klarer Hinweis, dass es Absicht ist, und wann wieder geprüft oder gestartet wird.

**Interviewer:** Welche Begriffe sind für dich schwierig?  
**Lea:** Alles, was nach Technik klingt. "Reserve-Veto", "Stabilisierung" - damit kann ich nichts anfangen.

**Interviewer:** Was wäre eine verständliche Formulierung?  
**Lea:** Alltagssprache. So wie: "Wartet auf stabilen Überschuss" oder "Reserve schützen".

**Interviewer:** Was heißt "Reserve schützen" für dich?  
**Lea:** Dass das Haus genug Strom behält. Ich will nicht, dass der Miner die Batterie leer zieht.

**Interviewer:** Wie erkennst du, dass die Reserve blockiert?  
**Lea:** Gar nicht. Wenn da nur "Pause" steht, weiß ich nicht, ob es gut oder schlecht ist.

**Interviewer:** Wie reagierst du auf Schwankungen, z. B. Wolken?  
**Lea:** Wenn es kurz stoppt, denke ich schnell an Fehler. Ein Hinweis "nächster Check in 3 Minuten" wäre gut.

**Interviewer:** Was ist der größte Schmerzpunkt beim Status "Pause"?  
**Lea:** Ich weiß nicht, ob es gleich weitergeht oder ob ich eingreifen muss.

**Interviewer:** Was würde dein Vertrauen erhöhen?  
**Lea:** Wenn die Erklärung immer gleich aufgebaut ist: warum und wann.

**Interviewer:** Was wäre für dich ein "gutes" Dashboard?  
**Lea:** Ein Satz warum, ein Satz wann. Ein kleines Symbol dazu. Mehr nicht.

**Interviewer:** Wann würdest du manuell eingreifen?  
**Lea:** Wenn ich das Gefühl habe, die Automatik versteht die Situation nicht.

&nbsp;

## Synthetische Persona (v0.1): Lea Klar

**Name / Archetyp:** Lea Klar - Kurzblick-Transparenz  
**Job-to-be-done:** In unter 30 Sekunden verstehen, warum der Miner läuft/pausiert/stoppt und wann sich der Status ändert.  
**Kontext (wo/wann/womit):** Zuhause, kurzer Blick am Handy, meist mittags/abends; 30-60 Sekunden.

**Ziele**
- Warum + wann in einem Blick verstehen.
- Vertrauen in die Automatik ohne manuelles Nachschauen.
- Haus-Reserve schützen, keine Fehlentscheidungen.

**Ängste / Risiken**
- Technische Begründungen wirken wie Fehlercodes.
- "Pause" ohne Grund löst Unsicherheit aus.
- Reserve könnte unbemerkt angegriffen werden.

**Heuristiken / Regeln**
- "Wenn ich es nicht verstehe, schalte ich lieber aus."
- "Wenn Reserve aktiv, muss es sichtbar sein."
- "Ein Satz warum + ein Satz wann reicht."

**Trigger & Breaking Points**
- Trigger: PV-Überschuss mittags, Abendbedarf, Leistungsschwankungen.
- Breaking Points: Status ohne Grund, kein nächster Check, technische Begriffe.

**Needs an Erklärung**
- Alltagssprache, ein Satz "Warum", ein Satz "Wann".
- Sichtbares Reserve-Badge mit Schwelle.
- Countdown oder nächster Check, damit Stopps nicht wie Fehler wirken.

**Evidenz (Interview)**
- "Warum der Miner läuft oder nicht. Ein Satz reicht. Und wann sich das ändert."
- "Der Grund fehlt oder ist so technisch, dass ich ihn nicht verstehe."
- "Dann denke ich, etwas stimmt nicht, und ich schalte lieber manuell aus."
- "Wenn er kurz stoppt oder ständig an und aus geht. Das sieht für mich aus wie ein Problem."
- "Gar nicht. Wenn da nur 'Pause' steht, weiß ich nicht, ob es gut oder schlecht ist."
- "Ein Hinweis 'nächster Check in 3 Minuten' wäre gut."
- "Ein Satz warum, ein Satz wann. Ein kleines Symbol dazu. Mehr nicht."

**Annahmen (zu prüfen)**
- Ein Icon + Kurztext wird schneller erfasst als Text allein.
- Details hinter "Mehr" reichen; die Startkarte bleibt minimal.

**Design-Implikationen**
- Statuskarte: Icon + Kurzgrund + Countdown/Startzeit in einer Zeile.
- Reserve-Badge sichtbar, wenn aktiv, mit Schwellenwert.
- Nächster Check/Uhrzeit immer anzeigen.

&nbsp;

## Proto-Problem-Statement

- Dashboard zeigt nur Status (läuft/pausiert), Grund und Prognose fehlen oder sind technisch.
- Reserve-Veto und Stabilisierung wirken wie Fehler, nicht wie Absicht.
- Folge: Zweifel an der Automatik, manuelle Eingriffe, Abschalten des Miners.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SH-ASSUM-TRAN-01 | Ein Satz "Warum" + ein Satz "Wann" reichen für Akzeptanz im Alltag. |
| SH-ASSUM-TRAN-02 | Alltagssprache wird schneller verstanden als Regel-/Technikbegriffe. |
| SH-ASSUM-TRAN-03 | Reserve-Veto wird akzeptiert, wenn Schwelle und Grund sichtbar sind. |
| SH-ASSUM-TRAN-04 | Countdown/nächster Check verhindert Fehlinterpretation als Fehler. |
| SH-ASSUM-TRAN-05 | Icon + sehr kurzer Text werden schneller wahrgenommen als Text allein. |

&nbsp;

## Kritische Annahme

- Ein Satz "Warum" + ein Satz "Wann" in Alltagssprache reichen aus, damit Nutzer die Entscheidung als absichtsvoll akzeptieren und seltener manuell eingreifen.

&nbsp;

## Abgeleitete Forschungsfrage

**Wie müssen Grund, Prognose und Reserve-Hinweis im Smart-Home-Dashboard dargestellt werden (Text + Icon), damit Nutzer die regelbasierte Entscheidung als absichtsvoll verstehen und seltener eingreifen?**

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|-------|-----------|-------|
| SH-TRAN-01 | Kernbotschaft | Reichen Grund + Startzeit für Verständnis? | ASSUM-01,02 |
| SH-TRAN-02 | Reserve-Sichtbarkeit | Wie zeigen wir das Veto der Haus-Reserve so, dass es akzeptiert wird? | ASSUM-03 |
| SH-TRAN-03 | Timing | Verhindert ein Countdown/nächster Check Fehlinterpretation als Fehler? | ASSUM-04 |
| SH-TRAN-04 | Darstellung | Welche Kombination aus Icon + Kurztext wird am schnellsten verstanden? | ASSUM-05 |

&nbsp;

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|---------|-------|
| EXP-SH-TRAN-01 | 30s Blicktest: Grund + Wann erfassbar? | Baseline-Verständnis |
| EXP-SH-TRAN-02 | A/B: Fachbegriff vs. Alltagssprache | Sprachverständnis |
| EXP-SH-TRAN-03 | Think-aloud bei Reserve-Veto | Mentales Modell |

&nbsp;

## UI-Prinzipien (abgeleitet aus Persona & WQ1)

- Warum + Wann immer gekoppelt: Kurzgrund + Start/Stopp-Zeit oder Countdown in einer Zeile.
- Alltagssprache statt Regel-Code: "Wartet auf stabilen PV-Überschuss" statt "R1 Stabilisierung".
- Reserve sichtbar machen: Schwelle oder Veto-Tag (R2) anzeigen, wenn Reserve blockiert.
- Multimodal kurz: Icon + ein Satz; Details hinter "Mehr" verstecken, nicht auf der Startkarte.
- Kein Blindflug: Nächster Check/Uhrzeit immer zeigen, damit Flapping als Stabilisierung lesbar ist.

&nbsp;

## Beobachtungspunkte

- Wie schnell wird der Grund genannt (Sekunden bis richtige Erklärung)?
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
| UI-SH-TRAN-03 | Link/Knopf "Mehr" für Detail-Overlay (optional). |

&nbsp;

## Messkriterien (einfach)

- < 30s bis zur korrekten Nennung von Grund und Prognose.
- 80% interpretieren Reserve-Veto korrekt als Schutz.
- < 1 manuelle Intervention pro Woche wegen Unklarheit.

&nbsp;

## Zusammenfassung

Alltagssprache + Kurzgrund/Countdown machen die Entscheidung erfassbar, ein sichtbares Reserve-Badge entkräftet Fehlinterpretationen, und ein optionales Detail-Overlay hält die Startkarte schlank.

---

> **Nächster Schritt:** Als nächstes geht es um Kontrolle und Override.
>
> 👉 Weiter zu **[20.2.1.2 - SH-WQ2 - Kontrolle und Override](./2021b_kontrolle.md)**
>
> 🔙 Zurück zu **[20.2.1 - SH-CONTEXT - Smart-Home-Kontext](./README.md)**
>
> 🏠 Zurück zu **[20.2 - WQ - Zentrale Arbeitsfragen](../README.md)**

