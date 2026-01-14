# 20.2.1.2 - SH-WQ2 - Kontrolle und Override (Handlungsfreiheit)

Ziel: Nutzer koennen mit einem Schritt eingreifen, verstehen Grenzen und behalten die Automatik als Standardmodus.

&nbsp;

## Nutzungskontext (Smart Home)

- Dashboard/App zu Hause; Nutzung oft situativ (Ruhebedarf, Besuch, Lautstaerke, Strompreis).
- Schnellreaktion erwartet: ein Tap/Klick, klare Dauer, Rueckgaengig moeglich.
- Eingriffe sollen das System nicht destabilisieren (Stabilisierung/Reserve bleibt aktiv).

&nbsp;

## Proto-Persona

**Persona:** Tom Direkt, 38  
**Rolle:** Haushaltsbetreiber, entscheidet situativ (Ruhe, Besuch, Preis)  
**Nutzungstyp:** Ad-hoc-Eingriffe, seltene Einstellungen  
**Technische Affinitaet:** pragmatisch, wenig Geduld fuer Menues  
**Primärer Nutzungskontext:** Abends/bei Stoerung; will in < 3 Sekunden eingreifen  
**Mentales Modell:** Automatik laeuft im Hintergrund, Override ist oberste Prioritaet; Reserve und Stabilisierung duerfen ihn nicht ausbremsen ohne Grund  
**Ziel der Persona:** Sofortiger Stop/Start mit klarer Dauer und Folgen, ohne die Automatik abzuschalten  
**Relevante Einschraenkungen:** Keine Zeit fuer Erklaerungen; hasst Button-Mashing; akzeptiert Verlust, wenn klar benannt

&nbsp;

## Proto-Problem-Statement

- Override-Knopf versteckt oder erfordert mehrere Schritte; Wirkung unklar.
- Reserve-Veto oder Stabilisierung blockiert Override ohne Erklaerung.
- Folge: Gefuehl von Kontrollverlust, mehrfaches Druecken, Abschalten der Automatik.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SH-ASSUM-CTRL-01 | Ein grosser, sichtbarer Override reicht, wenn Dauer und Wirkung sofort bestaetigt werden. |
| SH-ASSUM-CTRL-02 | Blockaden (Reserve/Stabilisierung/Safety) werden akzeptiert, wenn Grund + Restzeit angezeigt werden. |
| SH-ASSUM-CTRL-03 | Nutzer akzeptieren Ertragsverlust, wenn er als Folge kurz genannt wird. |
| SH-ASSUM-CTRL-04 | Haptische/visuelle Rueckmeldung direkt auf dem Button senkt erneutes Druecken. |
| SH-ASSUM-CTRL-05 | Automatik bleibt aktiv, wenn ein Rueckgaengig/TIMER sichtbar ist. |

&nbsp;

## Kritische Annahme

- Ein sofort sichtbarer Override mit Rueckmeldung + Timer reduziert Kontrollverlust und verhindert, dass Nutzer die Automatik komplett deaktivieren.

&nbsp;

## Abgeleitete Forschungsfrage

**Wie muss Override (Sichtbarkeit, Rueckmeldung, Dauer, Folgenhinweis) gestaltet sein, damit Smart-Home-Nutzer Kontrolle erleben, ohne die Automatik zu deaktivieren?**

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|-------|-----------|-------|
| SH-CTRL-01 | Sichtbarkeit | Wie gross/platziert muss der Override-Button sein, damit er in < 3 Sekunden gefunden wird? | ASSUM-01 |
| SH-CTRL-02 | Rueckmeldung | Welche Kombination aus Button-Feedback + Text bestaetigt Eingriffe am schnellsten? | ASSUM-04 |
| SH-CTRL-03 | Sperren erklaeren | Wie erklaeren wir Blockaden (Reserve/Stabilisierung/Safety), damit kein Button-Mashing entsteht? | ASSUM-02 |
| SH-CTRL-04 | Folgenhinweis | Welcher kurze Hinweis zu Ertragsverlust reicht, ohne zu nerven? | ASSUM-03 |
| SH-CTRL-05 | Dauer | Welche vordefinierten Zeitraeume (z. B. 30/60/120 Min) werden akzeptiert? | ASSUM-05 |

&nbsp;

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|---------|-------|
| EXP-SH-CTRL-01 | Zeitmessung: Override finden und druecken. | Sichtbarkeit |
| EXP-SH-CTRL-02 | Blockade-Szenario: Reserve aktiv; beobachte Button-Mashing. | Sperren-Verstaendnis |
| EXP-SH-CTRL-03 | Kurzinterview: Ertragsverlust-Hinweis verstanden? | Folgenakzeptanz |

&nbsp;

## UI-Prinzipien (abgeleitet aus Persona & WQ2)

- Override first: grosser Primarbutton (Start/Stop/Override) auf der Status-Karte.
- Sofortige Rueckmeldung: Button-Zustand + Text "Eingriff angenommen" + Dauer/Timer.
- Blockaden erklaeren: Grund + Restzeit; nie still ignorieren.
- Alternativen anbieten: "Last senken" oder "Automatik prueft in XX:XX neu" statt nur Verbot.
- Automatik sichtbar lassen: Anzeige "Automatik aktiv" + Rueckgaengig in Reichweite.

&nbsp;

## Beobachtungspunkte

- Zeit bis zum Finden/Druecken des Override.
- Anzahl erneuter Klicks bis Blockade verstanden ist.
- Akzeptanz von Restzeit/Timer bei blockiertem Override.

&nbsp;

## Artefakte / UI

- Primarbutton: "Miner stoppen" / "Jetzt starten" mit Zustand (aktiviert/gesperrt).
- Timer/Badge: "Gilt fuer 60 Min" + Countdown.
- Blockade-Banner: "Reserve aktiv, naechster Versuch in 03:00".
- Hinweis: "Ertrag -X%, Automatik bleibt aktiv".

&nbsp;

## Minimale UI-Elemente

| ID | Element |
|----|---------|
| UI-SH-CTRL-01 | Primarbutton "Miner stoppen/Starten" mit aktiv/gesperrt-Zustand. |
| UI-SH-CTRL-02 | Timer-Badge "Gilt fuer XX Min" + Countdown. |
| UI-SH-CTRL-03 | Blockade-Banner mit Grund + Restzeit. |
| UI-SH-CTRL-04 | Rueckgaengig/Automatik-weiter-Schalter. |

&nbsp;

## Messkriterien (einfach)

- < 3 Sekunden bis zum Finden des Overrides.
- < 2 erneute Klicks bei blockiertem Override.
- 80% akzeptieren Standard-Dauer (z. B. 60 Min) ohne Anpassung.

&nbsp;

## Zusammenfassung

Sichtbarer Primarbutton, sofortige Rueckmeldung und erklaerte Sperren halten das Kontrollgefuehl hoch; ein Timer und Rueckgaengig-Option sichern, dass die Automatik als Standard erhalten bleibt.

---

> **Naechster Schritt:** Danach geht es um Vertrauen und Haus-Reserve.
>
> Weiter zu **[20.2.1.3 - SH-WQ3 - Vertrauen und Sicherheit](./2021c_vertrauen.md)**
>
> Zurueck zu **[20.2.1 - SH-CONTEXT - Smart-Home-Kontext](./README.md)**
