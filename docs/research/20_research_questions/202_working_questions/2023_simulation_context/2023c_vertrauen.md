# 20.2.3.3 - SIM-WQ3 - Vertrauen durch physische Rückmeldung (Trust)

Ziel: Physische Signale lassen das Lab als sicher, absichtsvoll und beherrschbar wirken.

&nbsp;

## Nutzungskontext (Lab)

- Tisch-Setup mit Fokus auf Rückmeldung bei kritischen Ereignissen (Safety-Stop, Reserve-Veto, Hitze, Netz-Ausfall).
- Dauer: 6-8 Minuten mit 2-3 provozierten Störungen.
- Beobachtung: Fühlt sich das System wie ein gesteuertes Labor an oder wie ein unberechenbares Bastelsetup?

&nbsp;

## Proto-Persona

**Persona:** Vera Vertrauen, 45  
**Rolle:** Sicherheitsbewusste Teilnehmerin, skeptisch gegenüber Automatik  
**Nutzungstyp:** Kurzer Test mit provozierten Safety-Events (6-8 Min)  
**Technische Affinität:** gering bis mittel; braucht klare Signale, keine Fachsprache  
**Primärer Nutzungskontext:** Beobachtet Safety-Stop, Reserve-Veto, Hitze-Event; hört/fühlt Signale  
**Mentales Modell:** Safety muss als kontrollierte Sequenz erlebbar sein; System darf nach Stop nicht "tot" wirken  
**Ziel der Persona:** Erkennen, dass Schutzlogik aktiv ist und Neustart planbar erfolgt  
**Relevante Einschränkungen:** Alarmmüde bei schrillen Tönen; vertraut nur physischen Signalen + klarer Textzusage

&nbsp;

## Proto-Problem-Statement

- Safety-Stop löst aus, aber Teilnehmende wissen nicht, ob das System noch unter Kontrolle ist.
- Akustische Warnungen wirken wie Fehlalarme, wenn sie nicht mit einer klaren Info gekoppelt sind.
- Folge: Unsicherheit, ob man eingreifen oder warten soll; Zweifel an der Zuverlässigkeit.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SIM-ASSUM-VER-01 | Eine klare Reihenfolge der Signale (Sound -> LED -> Text) vermittelt Kontrolle besser als gleichzeitige Reize. |
| SIM-ASSUM-VER-02 | Ein kurzer "System steht sicher"-Heartbeat nach einem Stop reduziert Angst vor Hänger/Crash. |
| SIM-ASSUM-VER-03 | Physische Rückmeldung (Vibration/LED Puls) direkt am betroffenen Modul steigert Vertrauen mehr als nur Display-Text. |
| SIM-ASSUM-VER-04 | Transparente Wiederanlauf-Information ("Prüfe in 02:00 neu") verhindert panisches Eingreifen. |

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
| SIM-VER-03 | Lokal vs. zentral | Wirkt lokale Rückmeldung am Modul stärker als Anzeige nur am zentralen Display? | ASSUM-03 |
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
- Nach dem Stop lebt das System: Heartbeat (leises Klick/LED-Puls) bis zur nächsten Prüfung.
- Lokal vor zentral: Rückmeldung direkt am ausgelösten Modul, Display nur als Erklärung.
- Wiederanlauf planbar machen: Timer/Uhrzeit für nächste Prüfung oder Neustart immer zeigen.
- Warnfarben und Lautstärke sparsam: tief/kurz statt schrill, um Vertrauen statt Alarm zu erzeugen.

&nbsp;

## Beobachtungspunkte

- Wird der Stop als Schutzmassnahme oder als Defekt eingeordnet?
- Reicht ein Heartbeat, um "System lebt noch" zu signalisieren?
- Führt ein klarer Wiederanlauf-Timer zu weniger Eingriffen?

&nbsp;

## Artefakte / UI

- Signal-Sequenz: kurzer, tiefer Ton -> LED pulsierend rot -> Text: "Safety-Stop, prüfe neu in 02:00".
- Heartbeat nach Stop: leises Klick/Puls alle 10s, LED pulsiert grün, kein Buzzer.
- Modul-Feedback: Vibrationsmotor oder lokale LED an der ausgelösten Komponente.

&nbsp;

## Minimale UI-Elemente

| ID | Element |
|----|---------|
| UI-SIM-VER-01 | Signal-Sequenz: kurzer Ton -> LED rot pulsierend -> Text. |
| UI-SIM-VER-02 | Heartbeat-Anzeige nach Stop (leiser Klick/LED-Puls). |
| UI-SIM-VER-03 | Restart-Timer/nächste Prüfzeit sichtbar. |

&nbsp;

## Messkriterien (einfach)

- 80% ordnen den Stop als "kontrollierte Safety" ein (nicht als Defekt).
- < 1 unnötiger Eingriff (Reset/Knopf) pro Person nach Safety-Stop.
- Heartbeat wird in < 5 Sekunden bemerkt und als beruhigend bewertet.

&nbsp;

## Zusammenfassung

Sequenzierte Signale, ein sichtbarer Heartbeat und ein klarer Wiederanlauf-Timer lassen Safety-Stopps kontrolliert wirken und reduzieren unnötige Eingriffe.

---

> **Nächster Schritt:** Zurück zum Überblick des Simulation-Lab-Kontexts.
>
> 🔙 Zurück zu **[20.2.3 - SIM-CONTEXT - Simulation-Lab-Kontext](./README.md)**
>
> 🏠 Zurück zu **[20.2 - WQ - Zentrale Arbeitsfragen](../README.md)**

