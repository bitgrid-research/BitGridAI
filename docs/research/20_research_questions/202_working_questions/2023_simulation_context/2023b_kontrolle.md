# 20.2.3.2 - SIM-WQ2 - Eingriff und Override im Labor (Kontrolle)

Ziel: Teilnehmende koennen eingreifen, verstehen Grenzen und bringen das System nicht aus der Stabilitaet.

&nbsp;

## Nutzungskontext (Lab)

- Gleiches Tisch-Setup, jetzt mit Fokus auf Eingriffsschaltern (Start/Stop, Override, Reserve-Bypass).
- Zeit: 8-10 Minuten inkl. provozierter Stoerungen (Lastsprung, Preiswechsel, Temperatur-Alarm).
- Beobachtung: Wann greifen Menschen ein, wann warten sie? Wie interpretieren sie Sperren?

&nbsp;

## Proto-Persona

**Persona:** Sam Steuerbar, 37  
**Rolle:** Technikoffener Teilnehmer, will Wirkung von Eingriffen fuehlen  
**Nutzungstyp:** Aktive Hands-on-Phase (8-10 Min) mit provozierten Stoerungen  
**Technische Affinitaet:** mittel, aber wenig Geduld fuer Unklarheit  
**Primärer Nutzungskontext:** Drueckt Schalter (Override/Bypass), beobachtet LEDs/Buzzer, erwartet Sofortwirkung  
**Mentales Modell:** Eingriff muss sofort sichtbar sein; wenn blockiert, braucht er Grund + Timer  
**Ziel der Persona:** Kontrolle erleben ohne System zu zerstoeren; verstehen, warum ein Eingriff geblockt wird  
**Relevante Einschraenkungen:** Neigt zu Button-Mashing bei fehlender Rueckmeldung; akzeptiert Sperren nur mit Alternativen

&nbsp;

## Proto-Problem-Statement

- Override-Knopf wird gedrueckt, aber das System startet nicht (Reserve-Veto oder Stabilisierung aktiv).
- Teilnehmende wissen nicht, ob ihr Eingriff angekommen ist oder von der Logik ueberschrieben wurde.
- Folge: Gefuehl von Kontrollverlust, mehrfaches Druecken, potenzielle Instabilitaet.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SIM-ASSUM-KONT-01 | Ein klares "Eingriff angenommen" + "aber blockiert wegen <Grund>" reduziert Frust. |
| SIM-ASSUM-KONT-02 | Ein Zeitfenster (z. B. 5 Minuten Stabilisierung) wird akzeptiert, wenn es sichtbar abgezaehlt wird. |
| SIM-ASSUM-KONT-03 | Haptische Rueckmeldung (LED/Click) direkt am Schalter ist noetig, nicht nur am Display. |
| SIM-ASSUM-KONT-04 | Ein hartes Sicherheits-Veto (R2) wird akzeptiert, wenn eine alternative Aktion angeboten wird (z. B. Wartezeit oder Last verschieben). |

&nbsp;

## Kritische Annahme

- Sichtbarer Button-Feedback + erklaerte Blockaden mit Timer verhindern Button-Mashing und halten die Regel-Engine stabil.

&nbsp;

## Abgeleitete Forschungsfrage

**Wie muessen Eingriff, Rueckmeldung und Sperren gestaltet sein, damit Lab-Teilnehmende Kontrolle erleben, ohne die Regel-Engine zu destabilisieren?**

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|-------|-----------|-------|
| SIM-KONT-01 | Rueckmeldung | Welche Kombination aus haptisch (LED/Klick) und Text bestaetigt Eingriffe am schnellsten? | ASSUM-03 |
| SIM-KONT-02 | Sperren erklaeren | Wie erklaeren wir Blockaden (Reserve/Safety/Stabilisierung), sodass kein "Button-Mashing" entsteht? | ASSUM-01, 02 |
| SIM-KONT-03 | Alternativen | Welche Ersatzaktion beruhigt: Timer, Vorschlag "Last senken", oder "spaeter erneut versuchen"? | ASSUM-04 |
| SIM-KONT-04 | Zeitfenster | Wie lang darf ein Stabilisations-Timer sein, bevor er als Kontrollverlust erlebt wird? | ASSUM-02 |

&nbsp;

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|---------|-------|
| EXP-SIM-KONT-01 | Eingriffstest: Start erzwingen waehrend Reserve aktiv. | Effekt der Rueckmeldung |
| EXP-SIM-KONT-02 | Button-Mashing-Check: Wie oft wird gedrueckt, bis Grund verstanden ist? | Frustindikator |
| EXP-SIM-KONT-03 | Alternativen-Test: Timer vs. Vorschlag Last senken. | Akzeptanz der Sperre |

&nbsp;

## UI-Prinzipien (abgeleitet aus Persona & WQ2)

- Eingriff sofort sichtbar machen: LED/Klick am Schalter + Text-Bestaetigung auf dem Display.
- Blockaden immer begruenden: Grund + Restzeit/Timer, kein stummes Ignorieren.
- Alternativen anbieten statt nur verbieten: z. B. Last senken oder naechster Versuch automatisch.
- Harter Safety-Stopp klar abheben: Rot + kurzer Text, Override blockiert, Timer bis Freigabe sichtbar.
- Stabilisierung transparent halten: Gelb + Countdown, damit kein Button-Mashing entsteht.

&nbsp;

## Beobachtungspunkte

- Wie oft wird in 2 Minuten gedrueckt, bis der Grund verstanden ist?
- Reicht LED/Buzzer am Schalter als Feedback oder braucht es Text?
- Wird eine Sperre eher akzeptiert, wenn ein Countdown sichtbar ist?

&nbsp;

## Artefakte / UI

- Schalter mit integrierter LED (gruen = angenommen, rot = blockiert, gelb = warten/TX stabilisieren).
- Status-Zeile: "Eingriff angenommen, blockiert: Reserve aktiv, naechster Versuch in 03:00".
- Optionaler Vorschlag: "Last -500W, dann Start moeglich".

&nbsp;

## Minimale UI-Elemente

| ID | Element |
|----|---------|
| UI-SIM-KONT-01 | Schalter mit LED/Buzzer fuer sofortiges Feedback. |
| UI-SIM-KONT-02 | Statuszeile mit Blockadegrund + Restzeit. |
| UI-SIM-KONT-03 | Alternative-Aktion-Hinweis (Last senken/Auto-Retry). |

&nbsp;

## Messkriterien (einfach)

- < 2 Eingriffsversuche im Schnitt, bis Blockade verstanden ist.
- 80% akzeptieren Stabilisierungstimer bis 5 Minuten ohne Frustkommentar.
- < 10 Sekunden bis zu sichtbarer Rueckmeldung nach Knopfdruck.

&nbsp;

## Zusammenfassung

Klares Schalter-Feedback, transparente Blockadegruende mit Timer und eine Alternative statt nur "verboten" halten Kontrolle erfahrbar, ohne die Lab-Logik auszuschalten.

---

> **Naechster Schritt:** Danach folgt Vertrauen durch physische Rueckmeldung.
>
> Weiter zu **[20.2.3.3 - SIM-WQ3 - Vertrauen durch physische Rueckmeldung](./2023c_vertrauen.md)**
>
> Zurueck zu **[20.2.3 - SIM-CONTEXT - Simulation-Lab-Kontext](./README.md)**
