# 04.3 Zentrale Architekturentscheidungen

Bewusste Weichenstellungen.

Architektur entsteht nicht zufällig. Sie ist das Ergebnis von Entscheidungen – und von dem Mut, **eine Richtung einzuschlagen und andere bewusst nicht**.

In diesem Kapitel halten wir die **zentralen Architekturentscheidungen** von **BitGridAI** fest. Nicht im Sinne eines vollständigen Entscheidungsarchivs, sondern als nachvollziehbare Sammlung derjenigen Weichenstellungen, die den Charakter des Systems maßgeblich prägen.

Wir beantworten hier die Frage:

> **Warum haben wir uns genau so entschieden – und nicht anders?**

*(Platzhalter für ein Bild: Der Hamster steht an einer Weggabelung. Schilder zeigen verschiedene Optionen, einer ist klar markiert.)*

---

## Entscheidung 1: Local-First statt Cloud-Zentralisierung

**Entscheidung:**
BitGridAI wird konsequent **lokal** betrieben. Es gibt keine verpflichtende Cloud-Anbindung.

**Begründung:**

* Energiedaten sind hochsensibel.
* Der Betrieb muss auch ohne Internet stabil funktionieren.
* Forschung erfordert Kontrolle über Daten und Reproduzierbarkeit.

**Konsequenz:**

* Höhere Anforderungen an lokale Hardware
* Kein „Cloud-Komfort“, aber maximale Autonomie

---

## Entscheidung 2: Deterministische Regeln statt Black-Box-KI

**Entscheidung:**
Zentrale Entscheidungen werden durch **explizite Regeln (R1–R5)** getroffen – nicht durch selbstlernende Black-Box-Modelle.

**Begründung:**

* Entscheidungen müssen erklärbar und testbar sein.
* Nutzer sollen verstehen können, *warum* etwas passiert.
* Forschung verlangt Nachvollziehbarkeit statt statistischer Wahrscheinlichkeiten.

**Konsequenz:**

* Höherer initialer Modellierungsaufwand
* Dafür maximale Transparenz und Stabilität

---

## Entscheidung 3: Ereignisgetriebene Architektur mit Block-Takt

**Entscheidung:**
BitGridAI arbeitet **ereignisgetrieben**, getaktet durch einen festen **10-Minuten-BlockScheduler**.

**Begründung:**

* Verhindert nervöses Schalten („Flapping“)
* Macht Systemverhalten vorhersagbar
* Ermöglicht klare Replays und Simulationen

**Konsequenz:**

* Entscheidungen sind nicht „sofort“, sondern bewusst rhythmisiert
* Mehr Ruhe für Hardware und Nutzer

---

## Entscheidung 4: Strikte Trennung von Core und Adaptern

**Entscheidung:**
Fachlogik (Core) und Gerätekommunikation (Adapter) sind strikt getrennt.

**Begründung:**

* Hardware ändert sich schneller als Logik
* Testbarkeit des Cores ohne reale Geräte
* Austauschbarkeit von Komponenten

**Konsequenz:**

* Mehr Schnittstellen
* Weniger implizite Abhängigkeiten

---

## Entscheidung 5: Explainability als Pflicht, nicht als Feature

**Entscheidung:**
Jede Entscheidung muss erklärbar sein. Explainability ist **kein Add-on**, sondern Teil der Kernarchitektur.

**Begründung:**

* Vertrauen entsteht durch Verständnis
* Eingriffe ohne Erklärung führen zu Akzeptanzproblemen
* Forschung benötigt semantische Einordnung von Daten

**Konsequenz:**

* Zusätzliche Architekturkomponenten (Explain-Agent)
* Klar definierte Decision-Events mit Metadaten

---

## Entscheidung 6: Append-only Logging & Replay-Fähigkeit

**Entscheidung:**
Logs werden **append-only** gespeichert und sind replay-fähig.

**Begründung:**

* Manipulationssicherheit
* Wissenschaftliche Nachvollziehbarkeit
* Exakte Wiederholung von Szenarien

**Konsequenz:**

* Höherer Speicherbedarf
* Dafür maximale Transparenz und Analysefähigkeit

---

## Einordnung (arc42)

Dieses Kapitel dokumentiert **bewusste Architekturentscheidungen** und ihre Begründungen.

Es ergänzt:

* **04.1 Leitende Architekturprinzipien** (Haltung)
* **04.2 Grobe Systemstruktur** (Form)

Detaillierte Auswirkungen einzelner Entscheidungen werden in späteren Kapiteln vertieft (Bausteinsicht, Laufzeitsicht, Qualitätsszenarien).

---

> **Nächster Schritt:** Nicht alles, was denkbar ist, gehört ins System. Im nächsten Kapitel halten wir fest, **was BitGridAI bewusst nicht sein will**.
>
> 👉 Weiter zu **[4.4 Abgrenzungen & bewusste Nicht-Ziele](./044_non_goals.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
