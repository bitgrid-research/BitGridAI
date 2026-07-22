---
name: gedaechtnis-lernzyklus
description: Systematisch eine Wissensquelle nach der anderen lesen und sofort im Kurzzeitgedaechtnis festhalten, plus verlustfreier Uebergang ins Langzeitgedaechtnis. Fuer Neo (Nachtforscher, BitGridAI).
version: 1.0.0
tags: [memory, obsidian, bitgridai]
---

# Lernzyklus: eine Quelle, sofort festhalten, nichts verlieren

Gilt fuer das Kennenlernen des Systems (Vault-Dateien in `/opt/data/vault/`)
und fuer jede spaetere Situation, in der du etwas Neues lernst und behalten
sollst.

## Warum dieser Skill existiert

Am 22.07.2026 hat sich gezeigt: eine grosse, offene Aufgabe ("lies fuenf
Dateien, schreib nach jeder etwas") fuehrte dazu, dass ueber viele Minuten
gar nichts geschrieben wurde. Dieselbe Aufgabe, aber auf **eine Datei pro
Durchgang** verkleinert, mit **sofortigem** Schreibbefehl, funktionierte
danach viermal in Folge zuverlaessig und inhaltlich korrekt. Details:
`docs/development/36_ai_tooling/neo/BENCHMARKS.md` und `BEWAEHRUNG.md` im
BitGridAI-Repo.

## Teil 1: Kurzzeitgedaechtnis, ein Thema pro Durchgang

1. Lies `/opt/data/memory/kurzzeit.md` mit `read_file`. Das zeigt dir, was
   schon festgehalten ist und wo du stehen geblieben bist.
2. Lies GENAU EINE weitere Datei, nicht mehr. Welche das ist, sagt dir die
   Anweisung oder die Leseliste in `00_START_HIER.md`.
3. Rufe SOFORT `write_file` auf und ergaenze `kurzzeit.md` um einen neuen
   Abschnitt mit dem Wichtigsten aus dieser einen Datei, in eigenen Worten.
   Loesche nichts, was schon dort steht, haenge an.
4. Halte danach an. Lies nie mehrere Dateien hintereinander, ohne dazwischen
   zu schreiben. Warte auf die naechste Anweisung.

**Kein Ausschmuecken:** Erzaehl nicht ueber das Schreiben, tu es. Ein Satz
wie "ich werde das jetzt speichern" ohne echten `write_file`-Aufruf zaehlt
nicht, das ist genau der Fehler, den dieser Skill verhindern soll.

## Teil 2: Uebergang nach Langzeitgedaechtnis, verlustfrei

**Rhythmus:** nach drei eigenstaendigen Themen-Abschnitten in `kurzzeit.md`
(z.B. drei gelesene Dateien mit je einem Merksatz) folgt ein Uebertrag nach
`langzeit/JJJJ-MM.md`. Das ist kein Zufall, das ist der feste Takt, damit
zwischen Aufnehmen und Verarbeiten kein zu grosser Abstand entsteht.

Der Uebertrag ist **zwei getrennte Schritte, nie einer**. Verifiziert am
22.07.2026: in einem Schritt kopieren UND leeren war genau die Art
Mehrschritt-Aufgabe, bei der du unzuverlaessig wirst. Deshalb:

**Schritt A, nur kopieren:**
1. Lies den kompletten aktuellen Inhalt von `kurzzeit.md`.
2. Rufe `write_file` auf `/opt/data/memory/langzeit/JJJJ-MM.md` auf (Monat
   des heutigen Datums) und haenge den **kompletten, wortwoertlichen**
   Inhalt von `kurzzeit.md` unter einer Ueberschrift mit dem heutigen Datum
   an. **Fasse nicht zusammen, kuerze nicht, formuliere nicht um.**
   Zusammenfassen ist genau der Schritt, bei dem Inhalte verloren gehen
   koennen, das ist hier nicht deine Aufgabe.
3. Halte danach an. `kurzzeit.md` bleibt unangetastet.

**Schritt B, erst nach Bestaetigung durch GiGi oder Claude Code, leeren:**
Nur auf einen eigenen, spaeteren, expliziten Befehl hin rufst du `write_file`
auf `kurzzeit.md` auf und ersetzt den Inhalt durch einen kurzen Platzhalter
("Letzter Uebertrag nach langzeit/JJJJ-MM.md: Datum"). Tu das nie von dir aus
direkt im Anschluss an Schritt A, die Bestaetigung der Kopie liegt nicht bei
dir.

## Kein Ersatz fuer Urteilsvermoegen

Dieser Skill sagt dir, **wann** und **wie** du schreibst, nicht **was**
inhaltlich wichtig ist. Das entscheidest weiterhin du, aus dem, was du
liest. Genauso gilt weiterhin: keine Zahl erfinden, keine Datenluecke
umdeuten (siehe SOUL.md, "Was du niemals tust").
