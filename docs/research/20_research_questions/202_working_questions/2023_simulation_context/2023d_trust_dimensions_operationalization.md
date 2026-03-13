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


## Behavioral Influence (Verhaltensbeeinflussung)

Behavioral Influence beschreibt, wie Systementscheidungen, Erklaerungen und
UI-Impulse das Handeln der Nutzenden veraendern (z. B. Automatik aktiv lassen,
manuell eingreifen oder Sicherheitsgrenzen akzeptieren). Ziel ist
`kalibriertes Vertrauen`: Nutzende sollen angemessen folgen, nicht blind
zustimmen und auch nicht pauschal blockieren.

### Abgrenzung und Gestaltungsprinzipien

- **Unterstuetzung statt Manipulation:** Einfluss wird nur eingesetzt, um
  Sicherheit, Stabilitaet und alltagstaugliche Nutzung zu verbessern.
- **Entscheidungsfreiheit bleibt erhalten:** Jede verhaltensrelevante
  Empfehlung ist mit wirksamem `Override` kombinierbar.
- **Begruendungspflicht:** Hinweise enthalten mindestens `Warum`,
  `Risiko bei Nichtbefolgung` und `naechsten Pruefzeitpunkt`.
- **Proportionalitaet:** Intensitaet der Intervention folgt dem Risiko
  (`Info -> Warnung -> Sperre`), nicht technischen Detailpraeferenzen.

### Operationalisierung entlang Kontrolle, Sicherheit und Komfort

- **Kontrolle:**
  Anteil der Empfehlungen mit klarem Alternativpfad, Zeit bis zum erfolgreichen
  manuellen Eingriff, wahrgenommene Autonomie (Kurzrating 1-5).
- **Sicherheit:**
  Befolgungsrate sicherheitskritischer Hinweise, Anzahl riskanter Overrides
  gegen Sicherheitslogik, Veraenderung von Near-Miss-Ereignissen.
- **Komfort:**
  Reduktion unnoetiger manueller Eingriffe, Deaktivierungsquote der Automatik
  nach Hinweisen, subjektiver Entscheidungsaufwand.

### Messbare Kernindikatoren (D2)

| ID | Indikator | Datenquelle | Interpretation |
|----|-----------|-------------|----------------|
| BI-01 | Recommendation Acceptance Rate | Event-Logs (Empfehlung -> Aktion) | Nur positiv, wenn Sicherheitslage objektiv passt. |
| BI-02 | Safety Compliance Rate | Logs zu Safety-Hinweis/Override | Kernindikator fuer sicherheitsorientierten Einfluss. |
| BI-03 | Override Latency | UI-Interaktionslog | Zeigt, ob Eingriffe schnell und wirksam moeglich sind. |
| BI-04 | Reactance Rate | Zustandswechsel (z. B. Automatik aus nach Hinweis) | Fruehwarnsignal fuer bevormundend wirkende Kommunikation. |
| BI-05 | Calibrated Reliance | Verknuepfung aus Systemguete und Nutzerhandlung | Misst Angemessenheit statt blosser Zustimmung. |

### Bewertungslogik (D4)

- **Positiver Einfluss:**
  Sicherheitskritische Hinweise werden ueberwiegend befolgt; nicht-kritische
  Hinweise erzeugen keine hohe Reactance; Eingriffe sind gezielt statt impulsiv.
- **Kritischer Einfluss:**
  Hohe Zustimmung bei niedriger Transparenz (blinder Gehorsam), haeufige
  Deaktivierung nach Warnungen (Reaktanz), viele Overrides mit spaeteren
  Safety-Stopps (Fehlkalibrierung).
- **Auswertungsregel:**
  Komfortgewinne zaehlen nur dann als Erfolg, wenn `Sicherheit` stabil bleibt
  und `Kontrolle` nicht messbar sinkt.

### Umsetzung in Simulation und Feldstudie

- **Simulation (Lab):**
  A/B-Varianten fuer Hinweisgestaltung (`kurzer Grund` vs.
  `Grund + Prognose + Handlungsoption`) und Messung BI-01 bis BI-04 je
  Persona und Szenario.
- **Feldstudie:**
  Wochenweise Entwicklung von BI-05 (`Calibrated Reliance`) und qualitative
  Nachbefragung bei Extremwerten (sehr hohe Zustimmung oder hohe Reactance).
- **Rueckkopplung in Artefakte A1-A3:**
  Befunde werden als priorisierte Anpassungen fuer Regelwerk, UI-Texte und
  Eskalationslogik dokumentiert.
