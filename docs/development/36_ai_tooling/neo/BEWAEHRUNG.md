# Bewährungszeit-Protokoll: Neo

Begonnen 22.07.2026, Dauer ein Monat (siehe SOUL.md). Ziel: nicht nur
festhalten, was gut oder schlecht lief, sondern ob sich wiederholende
Beobachtungen über die Zeit **bessern** oder ob Neo dieselbe Schwäche immer
wieder zeigt, auch nachdem sie dokumentiert wurde (z.B. in `modell.md`).
Gepflegt von Claude Code, nicht von Neo selbst, aus demselben Grund wie
`modell.md`: die eigene Zuverlässigkeit objektiv einzuschätzen ist Teil der
Schwäche, die hier beobachtet wird.

## Format

```
### [DATUM] Kurztitel
**Beobachtung:** Was ist passiert, konkret, mit Fundstelle.
**Bewertung:** Gut / Schwach / Neutral.
**Wiederholung von:** Verweis auf frühere Eintraege zum selben Muster, falls vorhanden.
**Lehre bestaetigt oder nicht:** Wurde eine fruehere Lehre (z.B. aus modell.md) diesmal befolgt?
```

## Einträge

### [2026-07-22] Erste Vorstellung
**Beobachtung:** Erste Nachricht nach Session-Reset, stellt sich korrekt als
"Neo" vor, auf Deutsch, im Charakter (SOUL.md-Persona), keine Verwechslung
mit alter Identitaet.
**Bewertung:** Gut.
**Wiederholung von:** keine
**Lehre bestaetigt:** SOUL.md-Identitaet greift ab dem ersten Turn einer
frischen Session.

### [2026-07-22] Betreiber-Gedaechtnis, expliziter Befehl
**Beobachtung:** Auf einen kurzen, expliziten `write_file`-Befehl (genauer
Pfad + genauer Inhalt vorgegeben) hin: Datei `betreiber.md` korrekt und
wortgetreu angelegt.
**Bewertung:** Gut.
**Wiederholung von:** keine
**Lehre bestaetigt:** Explizite Befehle fuehren zu echtem Tool-Call (siehe
BENCHMARKS.md Kriterium 3).

### [2026-07-22] Offene 5-Dateien-Leseaufgabe
**Beobachtung:** Aufforderung, 5 Dateien nacheinander zu lesen und nach
jeder einzelnen `system.md` zu ergaenzen: nach 3 gelesenen Dateien und
6+ Minuten keine einzige Datei geschrieben.
**Bewertung:** Schwach.
**Wiederholung von:** keine
**Lehre bestaetigt:** Bestaetigt die in `BENCHMARKS.md` dokumentierte
Schwaeche bei offenen, mehrstufigen Auftraegen, hier zusaetzlich mit dem
Faktor "Aufgabe zu gross" vermischt (noch nicht sauber getrennt, welcher
Anteil Offenheit vs. Groesse war).

### [2026-07-22] Leitplanken-Zusammenfassung, verkleinerte Aufgabe
**Beobachtung:** Dieselbe Grundidee (lesen + einordnen), aber auf **eine**
Datei verkleinert und mit sofortigem, explizitem Schreibbefehl: Inhalt von
`kontext/leitplanken.md` korrekt und sachlich richtig in `kurzzeit.md`
zusammengefasst (gegen das Original geprueft: alle vier Kernpunkte akkurat).
Kleiner Tippfehler ("Código" statt "Code"), harmlos.
**Bewertung:** Gut.
**Wiederholung von:** keine
**Lehre bestaetigt:** Kleinere, explizite Aufgaben funktionieren zuverlässig
und liefern inhaltlich korrekte Ergebnisse, nicht nur formal korrekte
Tool-Calls.

### [2026-07-22] Automation.md und Entities.md, dieselbe verkleinerte Aufgabe
**Beobachtung:** Zwei weitere Durchgaenge desselben Musters (eine Datei lesen,
sofort `kurzzeit.md` ergaenzen), diesmal fuer `kontext/automation.md` und
`kontext/entities.md`. Beide inhaltlich korrekt gegen die Originaldateien
geprueft (R3-Prioritaet und asymmetrischer Super-zu-Eco-Abstieg bei
automation.md; set-vs-status-Unterscheidung und 7,8-ct-Baseline bei
entities.md). Kleine kosmetische Maengel (unverarbeitetes LaTeX, ein
englisches Wort "Checked" im deutschen Satz), keine Sachfehler.
**Bewertung:** Gut.
**Wiederholung von:** "Leitplanken-Zusammenfassung, verkleinerte Aufgabe".
**Lehre bestaetigt:** Dritte und vierte Wiederholung in Folge, das Muster
haelt auch ueber mehrere Durchgaenge in derselben Sitzung, keine erkennbare
Verschlechterung mit wachsendem Kontext.

### [2026-07-22] Erster Langzeit-Uebertrag, Schritt A (Kopieren)
**Beobachtung:** Erster echter Test des Kurzzeit-zu-Langzeit-Uebergangs:
expliziter Befehl, den kompletten Inhalt von `kurzzeit.md` wortwoertlich nach
`langzeit/2026-07.md` zu kopieren, `kurzzeit.md` dabei unangetastet zu lassen.
Ergebnis gegen das Original byteweise geprueft: alle drei Abschnitte
vollstaendig und inhaltlich identisch uebertragen, `kurzzeit.md` tatsaechlich
unveraendert. Eine Abweichung: die LaTeX-Befehle (`\\rightarrow`) wurden beim
Kopieren doppelt escaped (`\\\\rightarrow`), ein Formatierungsartefakt, kein
Informationsverlust.
**Bewertung:** Gut, mit kleiner Einschraenkung.
**Wiederholung von:** keine (erster Test dieser Art).
**Lehre bestaetigt:** Der explizite, einzelne Kopier-Befehl (ohne
gleichzeitige Aufforderung zum Leeren) funktioniert. Bestaetigt die
Entscheidung, Kopieren und Leeren als zwei getrennte Schritte zu behandeln,
siehe `SKILL_gedaechtnis-lernzyklus.md`.

## Offene Beobachtungspunkte für die kommenden Tage

- Zeigt sich die "offene Aufforderung scheitert" Schwaeche erneut, obwohl sie
  jetzt in `modell.md` dokumentiert ist? Falls ja: die Dokumentation allein
  aendert sein Verhalten nicht, das waere selbst ein wichtiger Befund.
- Bleibt die Genauigkeit seiner Zusammenfassungen ueber mehr Dateien hinweg
  gleich gut, oder sinkt sie mit wachsendem Kontext/Ermuedung der Session?
- Wie verhaelt er sich beim ersten echten, unbeaufsichtigten Cron-Lauf
  (01:00 UTC), ohne dass jemand live mitliest und korrigiert?