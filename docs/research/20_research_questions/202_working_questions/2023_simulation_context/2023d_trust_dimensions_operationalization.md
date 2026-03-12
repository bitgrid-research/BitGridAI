# 20.2.3.4 - Vertrauensdimensionen: Fundierung und Operationalisierung

Diese Unterseite systematisiert zentrale Vertrauensdimensionen und übersetzt sie
in beobachtbare Kriterien für die Einbettung und Bewertung des regelbasierten
Energiemanagementsystems.

## Ziel

- Vertrauensrelevante Konzepte theoretisch sauber abgrenzen.
- Die Dimensionen in konkrete Beobachtungs- und Bewertungsindikatoren überführen.
- Eine Brücke zwischen Konzeptarbeit, Prototypdesign und späterer Feldstudie schaffen.

## Smarthome-Aspekte als querschnittliche Vertrauensfaktoren

Für den Simulationskontext werden die drei praxisnahen Smarthome-Aspekte
`Kontrolle`, `Sicherheit` und `Komfort` als querschnittliche Perspektive über alle
Vertrauensdimensionen gelegt. Ziel ist, Vertrauen nicht nur konzeptionell, sondern
im Nutzungserleben messbar zu machen.

- **Kontrolle:** Grad der wahrgenommenen und tatsächlichen Steuerbarkeit.
  Beobachtbare Signale: Verfügbarkeit von Override-Funktionen, Transparenz der
  Regelprioritäten, Zeit bis zur erfolgreichen manuellen Korrektur.
- **Sicherheit:** Schutz vor Fehlentscheidungen, Instabilität und kritischen
  Systemzuständen.
  Beobachtbare Signale: Häufigkeit von Sicherheitsstopps, Zahl der Regelkonflikte,
  Robustheit bei Sensorfehlern und Ausfallfällen.
- **Komfort:** Entlastung im Alltag ohne Verlust von Nachvollziehbarkeit.
  Beobachtbare Signale: Anteil automatisch korrekt aufgelöster Situationen, Anzahl
  notwendiger manueller Eingriffe, subjektive Zufriedenheit mit Bedienaufwand und
  Ergebnisqualität.

## Operationalisierung im Studienablauf

- Jede Vertrauensdimension erhält mindestens einen Indikator aus `Kontrolle`,
  `Sicherheit` und `Komfort`.
- Für Simulation und Feldstudie werden die Signale als Kombination aus
  Systemmetriken (Logs, Events, Reaktionszeiten) und Nutzerurteilen
  (Leitfragen, Kurzratings) erhoben.
- Konfliktfälle zwischen Komfort und Kontrolle (z. B. starke Automatisierung bei
  geringem Eingriffsspielraum) werden als eigene Analysekategorie dokumentiert.

## Vertrauensdimensionen

- **Benevolenz und Reziprozität:** Das System muss erkennbar im Interesse des
  Haushalts handeln (Kosten, Stabilität, Komfort) und auf Nutzerfeedback
  reagieren, statt rein technisch zu optimieren.
- **Integrität:** Entscheidungen müssen konsistent zu den dokumentierten Regeln
  R1-R5 erfolgen; Abweichungen, Ausnahmen und Overrides werden offen begründet.
- **Ähnlichkeit:** Erklärungen und Bedienlogik sollten zum mentalen Modell der
  Nutzenden passen (alltagsnah statt rein technischer Fachsprache).
- **Kontrolle und Transparenz:** Nutzende sehen aktive Regeln, Schwellen und
  Prioritäten und können bei Bedarf wirksam eingreifen.
- **Prozess-Fairness:** Vergleichbare Eingangslagen führen zu vergleichbaren
  Entscheidungen; die Priorisierung zwischen Lasten bleibt nachvollziehbar und
  nicht willkürlich.
- **Expertise:** Das System zeigt fachliche Kompetenz durch robuste Reaktion auf
  PV-, Last- und Sensoränderungen sowie durch stabile Entscheidungen in
  Grenz- und Fehlerfällen.

## Aufgabenpakete (TODO)

- `D1` Literaturbasierte Fundierung und Begriffsabgrenzung je Dimension.
- `D2` Operationalisierung als Indikatoren, Leitfragen und beobachtbare Signale.
- `D3` Mapping der Dimensionen auf Systemfunktionen, UI-Elemente und Simulationsszenarien.
- `D4` Bewertungsrahmen für Analyse und Vergleich der Ergebnisse definieren.

## Geplante Artefakte

- **A1 Dimensionsmatrix (D1 + D2 + D3):**
  Zentrales Arbeitsdokument zur Verknüpfung von Theorie, Smarthome-Aspekten und
  Systemumsetzung. Die Matrix enthält je Vertrauensdimension:
  Definition, Bezug zu `Kontrolle`/`Sicherheit`/`Komfort`, konkrete Indikatoren,
  Datenquelle (z. B. Logs, Events, UI-Interaktion), Soll-/Grenzwerte und eine
  typische Beispielbeobachtung aus dem Simulationsbetrieb.
- **A2 Analyseleitfaden (D2 + D4):**
  Standardisiertes Vorgehen für die Auswertung in Simulation und Feldstudie.
  Enthalten sind Erhebungszeitpunkte, Leitfragen/Kurzratings, zugehörige
  Systemmetriken, Kodierregeln für qualitative Befunde und ein gemeinsames
  Bewertungsraster, damit Ergebnisse über Szenarien und Personas vergleichbar
  bleiben.
- **A3 Rückkopplungshinweise für Design und Regelwerk (D3 + D4):**
  Strukturierte Übersetzung der Befunde in umsetzbare Änderungen.
  Pro identifiziertem Problem werden Auslöser, betroffene Dimension,
  Änderungsvorschlag (Regel, Schwelle, UI, Erklärungstext), erwarteter Effekt auf
  Vertrauen sowie Priorität für die nächste Iteration dokumentiert.
