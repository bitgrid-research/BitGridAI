# 20.2.3.3 - SIM-WQ3 - Vertrauen durch physische Rueckmeldung (Trust)

Ziel: Physische Signale lassen das Lab als sicher, absichtsvoll und beherrschbar wirken.

&nbsp;

## Nutzungskontext (Lab)

- Tisch-Setup mit Fokus auf Rueckmeldung bei kritischen Ereignissen (Safety-Stop, Reserve-Veto, Hitze, Netz-Ausfall).
- Dauer: 6-8 Minuten mit 2-3 provozierten Stoerungen.
- Beobachtung: Fuehlt sich das System wie ein gesteuertes Labor an oder wie ein unberechenbares Bastelsetup?

&nbsp;

## Proto-Persona

**Persona:** Vera Vertrauen, 45  
**Rolle:** Sicherheitsbewusste Teilnehmerin, skeptisch gegenueber Automatik  
**Nutzungstyp:** Kurzer Test mit provozierten Safety-Events (6-8 Min)  
**Technische Affinitaet:** gering bis mittel; braucht klare Signale, keine Fachsprache  
**Primärer Nutzungskontext:** Beobachtet Safety-Stop, Reserve-Veto, Hitze-Event; hoert/fühlt Signale  
**Mentales Modell:** Safety muss als kontrollierte Sequenz erlebbar sein; System darf nach Stop nicht "tot" wirken  
**Ziel der Persona:** Erkennen, dass Schutzlogik aktiv ist und Neustart planbar erfolgt  
**Relevante Einschraenkungen:** Alarmmuede bei schrillen Tönen; vertraut nur physischen Signalen + klarer Textzusage

&nbsp;

## Proto-Problem-Statement

- Safety-Stop loest aus, aber Teilnehmende wissen nicht, ob das System noch unter Kontrolle ist.
- Akustische Warnungen wirken wie Fehlalarme, wenn sie nicht mit einer klaren Info gekoppelt sind.
- Folge: Unsicherheit, ob man eingreifen oder warten soll; Zweifel an der Zuverlaessigkeit.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SIM-ASSUM-VER-01 | Eine klare Reihenfolge der Signale (Sound -> LED -> Text) vermittelt Kontrolle besser als gleichzeitige Reize. |
| SIM-ASSUM-VER-02 | Ein kurzer "System steht sicher"-Heartbeat nach einem Stop reduziert Angst vor Haenger/Crash. |
| SIM-ASSUM-VER-03 | Physische Rueckmeldung (Vibration/LED Puls) direkt am betroffenen Modul steigert Vertrauen mehr als nur Display-Text. |
| SIM-ASSUM-VER-04 | Transparente Wiederanlauf-Information ("Pruefe in 02:00 neu") verhindert panisches Eingreifen. |

&nbsp;

## Kritische Annahme

- Eine geordnete Signal-Sequenz plus Heartbeat nach Stop reicht aus, um kritische Stopps als kontrollierte Safety statt als Fehler einzuordnen.

&nbsp;

## Abgeleitete Forschungsfrage

**Wie kombinieren wir Sound, Licht, Vibration und Text, damit kritische Stopps als kontrollierte Sicherheitsmassnahme und nicht als Fehler wahrgenommen werden?**

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|-------|-----------|-------|
| SIM-VER-01 | Signal-Abfolge | Welche Sequenz (Sound -> LED -> Text) wird als ruhig und kontrolliert wahrgenommen? | ASSUM-01 |
| SIM-VER-02 | Heartbeat | Braucht es einen kurzen Heartbeat nach Stop, um Vertrauen in den sicheren Zustand zu halten? | ASSUM-02 |
| SIM-VER-03 | Lokal vs. zentral | Wirkt lokale Rueckmeldung am Modul staerker als Anzeige nur am zentralen Display? | ASSUM-03 |
| SIM-VER-04 | Wiederanlauf | Wie klar muss der Neustart-Prozess kommuniziert werden, um panische Eingriffe zu vermeiden? | ASSUM-04 |

&nbsp;

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|---------|-------|
| EXP-SIM-VER-01 | Safety-Stop-Demo mit variierender Signal-Sequenz. | Wahrnehmung Kontrolle vs. Fehler |
| EXP-SIM-VER-02 | Heartbeat-Test: LED-Puls vs. kein Puls nach Stop. | Restunsicherheit messen |
| EXP-SIM-VER-03 | Lokal-vs-Display: Feedback nur am Modul vs. nur am Display vs. kombiniert. | Vertrauen und Klarheit |

&nbsp;

## UI-Prinzipien (abgeleitet aus Persona & WQ3)

- Signal-Abfolge entlastet: kurzer, tiefer Ton -> LED -> Text, keine gleichzeitige Reizuhr.
- Nach dem Stop lebt das System: Heartbeat (leises Klick/LED-Puls) bis zur naechsten Pruefung.
- Lokal vor zentral: Rueckmeldung direkt am ausgeloesten Modul, Display nur als Erklaerung.
- Wiederanlauf planbar machen: Timer/Uhrzeit fuer naechste Pruefung oder Neustart immer zeigen.
- Warnfarben und Lautstaerke sparsam: tief/kurz statt schrill, um Vertrauen statt Alarm zu erzeugen.

&nbsp;

## Beobachtungspunkte

- Wird der Stop als Schutzmassnahme oder als Defekt eingeordnet?
- Reicht ein Heartbeat, um "System lebt noch" zu signalisieren?
- Fuehrt ein klarer Wiederanlauf-Timer zu weniger Eingriffen?

&nbsp;

## Artefakte / UI

- Signal-Sequenz: kurzer, tiefer Ton -> LED pulsierend rot -> Text: "Safety-Stop, pruefe neu in 02:00".
- Heartbeat nach Stop: leises Klick/Puls alle 10s, LED pulsiert gruen, kein Buzzer.
- Modul-Feedback: Vibrationsmotor oder lokale LED an der ausgeloesten Komponente.

&nbsp;

## Minimale UI-Elemente

| ID | Element |
|----|---------|
| UI-SIM-VER-01 | Signal-Sequenz: kurzer Ton -> LED rot pulsierend -> Text. |
| UI-SIM-VER-02 | Heartbeat-Anzeige nach Stop (leiser Klick/LED-Puls). |
| UI-SIM-VER-03 | Restart-Timer/naechste Pruefzeit sichtbar. |

&nbsp;

## Messkriterien (einfach)

- 80% ordnen den Stop als "kontrollierte Safety" ein (nicht als Defekt).
- < 1 unnoetiger Eingriff (Reset/Knopf) pro Person nach Safety-Stop.
- Heartbeat wird in < 5 Sekunden bemerkt und als beruhigend bewertet.

&nbsp;

## Zusammenfassung

Sequenzierte Signale, ein sichtbarer Heartbeat und ein klarer Wiederanlauf-Timer lassen Safety-Stopps kontrolliert wirken und reduzieren unnoetige Eingriffe.

---

> **Naechster Schritt:** Zurueck zum Ueberblick des Simulation-Lab-Kontexts.
>
> Zurueck zu **[20.2.3 - SIM-CONTEXT - Simulation-Lab-Kontext](./README.md)**
>
> Zurueck zu **[20.2 - WQ - Zentrale Arbeitsfragen](../README.md)**

