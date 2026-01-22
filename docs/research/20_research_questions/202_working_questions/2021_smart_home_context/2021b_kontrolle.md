# 20.2.1.2 - SH-WQ2 - Kontrolle und Override (Handlungsfreiheit)

Ziel: Nutzer können mit einem Schritt eingreifen, verstehen Grenzen und behalten die Automatik als Standardmodus.

&nbsp;

## Nutzungskontext (Smart Home)

- Dashboard/App zu Hause; Nutzung oft situativ (Ruhebedarf, Besuch, Lautstärke, Strompreis).
- Schnellreaktion erwartet: ein Tap/Klick, klare Dauer, Rückgängig möglich.
- Eingriffe sollen das System nicht destabilisieren (Stabilisierung/Reserve bleibt aktiv).

&nbsp;

## Proto-Persona

**Persona:** Tom Direkt, 38  
**Rolle:** Haushaltsbetreiber, entscheidet situativ (Ruhe, Besuch, Preis)  
**Nutzungstyp:** Ad-hoc-Eingriffe, seltene Einstellungen  
**Technische Affinität:** pragmatisch, wenig Geduld für Menüs  
**Primärer Nutzungskontext:** Abends/bei Störung; will in < 3 Sekunden eingreifen  
**Mentales Modell:** Automatik läuft im Hintergrund, Override ist oberste Priorität; Reserve und Stabilisierung dürfen ihn nicht ausbremsen ohne Grund  
**Ziel der Persona:** Sofortiger Stop/Start mit klarer Dauer und Folgen, ohne die Automatik abzuschalten  
**Relevante Einschränkungen:** Keine Zeit für Erklärungen; hasst Button-Mashing; akzeptiert Verlust, wenn klar benannt

&nbsp;

## Synthetisches Interview (Tom Direkt)

**Setting:** 20-min Remote-Interview, Kontext Smart-Home-Dashboard, situativer Eingriff.  
**Ziel:** Pain Points, Kontrolle, Erwartung an Override.

**Interviewer:** Wann greifst du in die Automatik ein?  
**Tom:** Meist abends, wenn es laut wird, Besuch da ist oder wenn der Preis hochgeht. Dann will ich sofort reagieren.

**Interviewer:** Was ist dann das Wichtigste im Interface?  
**Tom:** Ein klarer, großer Button. Ich will nicht suchen.

**Interviewer:** Was nervt dich aktuell am meisten?  
**Tom:** Wenn ich drücke und nichts passiert. Dann klicke ich nochmal und nochmal.

**Interviewer:** Was erwartest du nach einem Klick?  
**Tom:** Eine klare Bestätigung: "Stopp aktiv" und wie lange das gilt.

**Interviewer:** Was passiert, wenn der Override blockiert wird?  
**Tom:** Dann fühle ich mich ausgebremst. Ich will wissen warum und wie lange.

**Interviewer:** Welche Gründe sind für dich akzeptabel?  
**Tom:** Reserve okay, aber dann bitte klar sagen: "Reserve aktiv, in 5 Minuten wieder möglich."

**Interviewer:** Wie wichtig ist dir die Dauer?  
**Tom:** Sehr wichtig. Ich will nicht, dass es ewig so bleibt. 30 oder 60 Minuten reicht mir.

**Interviewer:** Was ist für dich zu viel Information?  
**Tom:** Lange Texte oder versteckte Menüs. Ich will eine Entscheidung, keine Recherche.

**Interviewer:** Wie gehst du mit Ertragsverlust um?  
**Tom:** Ist mir egal, wenn ich weiß, was es kostet. Ein kurzer Hinweis reicht.

**Interviewer:** Was wäre der schlimmste Moment für einen Umweg?  
**Tom:** Wenn ich gerade in der Küche stehe oder Besuch da ist. Dann zählt jede Sekunde.

**Interviewer:** Wann würdest du die Automatik komplett abschalten?  
**Tom:** Wenn ich das Gefühl habe, ich habe keine Kontrolle und es ignoriert mich.

**Interviewer:** Was würde dein Vertrauen erhöhen?  
**Tom:** Wenn jeder Eingriff sofort sichtbar bestätigt wird und ich ihn schnell rückgängig machen kann.

&nbsp;

## Synthetische Persona (v0.1): Tom Direkt

**Name / Archetyp:** Tom Direkt - Schnell-Override  
**Job-to-be-done:** In einer Störungssituation den Miner sofort stoppen/starten, mit klarer Dauer und ohne die Automatik abzuschalten.  
**Kontext (wo/wann/womit):** Zuhause, meist abends; kurzer Blick am Handy; wenige Sekunden Zeit.

**Ziele**
- In < 3 Sekunden eingreifen (Start/Stop) mit sichtbarer Bestätigung.
- Kontrolle behalten, Automatik nur temporär übersteuern.
- Dauer und Folgen des Overrides sofort sehen.

**Ängste / Risiken**
- Override wirkt blockiert oder ohne Feedback.
- Mehrfaches Klicken ohne klare Wirkung.
- Keine Angabe zu Grund und Restzeit bei Sperre.

**Heuristiken / Regeln**
- "Wenn ich drücke, muss sofort etwas passieren."
- "Wenn blockiert, will ich Grund + Restzeit."
- "Wenn ich mich ignoriert fühle, schalte ich die Automatik aus."

**Trigger & Breaking Points**
- Trigger: Ruhebedarf (Abend, Besuch), Preis-Spitzen, unerwartete Last.
- Breaking Points: kein Feedback nach Klick, Sperre ohne Erklärung, zu viele Schritte.

**Needs an Erklärung**
- Kurz und direkt am Button: Status + Timer.
- Blockaden: Grund + Restzeit.
- Ertragsverlust: ein kurzer Hinweis reicht.

**Evidenz (Interview)**
- "Dann will ich sofort reagieren."
- "Ein klarer, großer Button. Ich will nicht suchen."
- "Wenn ich drücke und nichts passiert. Dann klicke ich nochmal und nochmal."
- "Eine klare Bestätigung: 'Stopp aktiv' und wie lange das gilt."
- "Reserve okay, aber dann bitte klar sagen: 'Reserve aktiv, in 5 Minuten wieder möglich.'"
- "Ist mir egal, wenn ich weiß, was es kostet. Ein kurzer Hinweis reicht."
- "Wenn ich das Gefühl habe, ich habe keine Kontrolle und es ignoriert mich."
- "Wenn jeder Eingriff sofort sichtbar bestätigt wird und ich ihn schnell rückgängig machen kann."

**Annahmen (zu prüfen)**
- Nutzt ein sekundäres Gerät (z. B. Wand-Tablet) für schnelle Eingriffe.
- Bevorzugt vordefinierte Dauern statt freier Eingabe.

**Design-Implikationen**
- Primarbutton auf der Status-Karte, groß und eindeutig.
- Bestätigungstext + Timer direkt am Button.
- Blockade-Banner mit Grund und Restzeit.

&nbsp;

## Proto-Problem-Statement

- Override-Knopf versteckt oder erfordert mehrere Schritte; Wirkung unklar.
- Reserve-Veto oder Stabilisierung blockiert Override ohne Erklärung.
- Folge: Gefühl von Kontrollverlust, mehrfaches Drücken, Abschalten der Automatik.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SH-ASSUM-CTRL-01 | Ein großer, sichtbarer Override reicht, wenn Dauer und Wirkung sofort bestätigt werden. |
| SH-ASSUM-CTRL-02 | Blockaden (Reserve/Stabilisierung/Safety) werden akzeptiert, wenn Grund + Restzeit angezeigt werden. |
| SH-ASSUM-CTRL-03 | Nutzer akzeptieren Ertragsverlust, wenn er als Folge kurz genannt wird. |
| SH-ASSUM-CTRL-04 | Haptische/visuelle Rückmeldung direkt auf dem Button senkt erneutes Drücken. |
| SH-ASSUM-CTRL-05 | Automatik bleibt aktiv, wenn ein Rückgängig/TIMER sichtbar ist. |

&nbsp;

## Kritische Annahme

- Ein sofort sichtbarer Override mit Rückmeldung + Timer reduziert Kontrollverlust und verhindert, dass Nutzer die Automatik komplett deaktivieren.

&nbsp;

## Abgeleitete Forschungsfrage

**Wie muss Override (Sichtbarkeit, Rückmeldung, Dauer, Folgenhinweis) gestaltet sein, damit Smart-Home-Nutzer Kontrolle erleben, ohne die Automatik zu deaktivieren?**

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|-------|-----------|-------|
| SH-CTRL-01 | Sichtbarkeit | Wie groß/platziert muss der Override-Button sein, damit er in < 3 Sekunden gefunden wird? | ASSUM-01 |
| SH-CTRL-02 | Rückmeldung | Welche Kombination aus Button-Feedback + Text bestätigt Eingriffe am schnellsten? | ASSUM-04 |
| SH-CTRL-03 | Sperren erklären | Wie erklären wir Blockaden (Reserve/Stabilisierung/Safety), damit kein Button-Mashing entsteht? | ASSUM-02 |
| SH-CTRL-04 | Folgenhinweis | Welcher kurze Hinweis zu Ertragsverlust reicht, ohne zu nerven? | ASSUM-03 |
| SH-CTRL-05 | Dauer | Welche vordefinierten Zeiträume (z. B. 30/60/120 Min) werden akzeptiert? | ASSUM-05 |

&nbsp;

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|---------|-------|
| EXP-SH-CTRL-01 | Zeitmessung: Override finden und drücken. | Sichtbarkeit |
| EXP-SH-CTRL-02 | Blockade-Szenario: Reserve aktiv; beobachte Button-Mashing. | Sperren-Verständnis |
| EXP-SH-CTRL-03 | Kurzinterview: Ertragsverlust-Hinweis verstanden? | Folgenakzeptanz |

&nbsp;

## UI-Prinzipien (abgeleitet aus Persona & WQ2)

- Override first: großer Primarbutton (Start/Stop/Override) auf der Status-Karte.
- Sofortige Rückmeldung: Button-Zustand + Text "Eingriff angenommen" + Dauer/Timer.
- Blockaden erklären: Grund + Restzeit; nie still ignorieren.
- Alternativen anbieten: "Last senken" oder "Automatik prüft in XX:XX neu" statt nur Verbot.
- Automatik sichtbar lassen: Anzeige "Automatik aktiv" + Rückgängig in Reichweite.

&nbsp;

## Beobachtungspunkte

- Zeit bis zum Finden/Drücken des Override.
- Anzahl erneuter Klicks bis Blockade verstanden ist.
- Akzeptanz von Restzeit/Timer bei blockiertem Override.

&nbsp;

## Artefakte / UI

- Primarbutton: "Miner stoppen" / "Jetzt starten" mit Zustand (aktiviert/gesperrt).
- Timer/Badge: "Gilt für 60 Min" + Countdown.
- Blockade-Banner: "Reserve aktiv, nächster Versuch in 03:00".
- Hinweis: "Ertrag -X%, Automatik bleibt aktiv".

&nbsp;

## Minimale UI-Elemente

| ID | Element |
|----|---------|
| UI-SH-CTRL-01 | Primarbutton "Miner stoppen/Starten" mit aktiv/gesperrt-Zustand. |
| UI-SH-CTRL-02 | Timer-Badge "Gilt für XX Min" + Countdown. |
| UI-SH-CTRL-03 | Blockade-Banner mit Grund + Restzeit. |
| UI-SH-CTRL-04 | Rückgängig/Automatik-weiter-Schalter. |

&nbsp;

## Messkriterien (einfach)

- < 3 Sekunden bis zum Finden des Overrides.
- < 2 erneute Klicks bei blockiertem Override.
- 80% akzeptieren Standard-Dauer (z. B. 60 Min) ohne Anpassung.

&nbsp;

## Zusammenfassung

Sichtbarer Primarbutton, sofortige Rückmeldung und erklärte Sperren halten das Kontrollgefühl hoch; ein Timer und Rückgängig-Option sichern, dass die Automatik als Standard erhalten bleibt.

---

> **Nächster Schritt:** Danach geht es um Vertrauen und Haus-Reserve.
>
> 👉 Weiter zu **[20.2.1.3 - SH-WQ3 - Vertrauen und Sicherheit](./2021c_vertrauen.md)**
>
> 🔙 Zurück zu **[20.2.1 - SH-CONTEXT - Smart-Home-Kontext](./README.md)**
>
> 🏠 Zurück zu **[20.2 - WQ - Zentrale Arbeitsfragen](../README.md)**
