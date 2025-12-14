# 04.2 Grobe Systemstruktur

Vom Plan zur Form.

Nachdem wir die **architektonischen Grundpfeiler** definiert haben, geht es nun einen Schritt weiter: Wie übersetzen wir diese Haltung in eine **tragfähige Gesamtstruktur**?

Dieses Kapitel beschreibt die **grobe Systemstruktur** von **BitGridAI**. Noch ohne Klassen, noch ohne Details – aber klar genug, um zu verstehen, *welche großen Bausteine es gibt*, *welche Verantwortung sie tragen* und *wie sie zusammenspielen*.

Wir beantworten hier nicht die Frage *"Wie ist etwas implementiert?"*, sondern:

> **Wo gehört etwas grundsätzlich hin – und wo bewusst nicht?**

*(Platzhalter für ein Bild: Der Hamster steht vor einem Bauplan. Große Blöcke sind eingezeichnet, verbunden durch dicke Pfeile. Keine Schrauben, keine Kabel – nur Struktur.)*

---

## Die Idee hinter der Struktur

BitGridAI folgt einer einfachen, aber strengen Ordnung:

* **Ein klarer Kern**, der entscheidet
* **Klare Ränder**, die messen, handeln oder erklären
* **Keine Querverbindungen**, die Verantwortung verwischen

Diese Struktur ist kein Selbstzweck. Sie ist die direkte Konsequenz aus unseren Grundpfeilern:
Local-First, Transparenz, Determinismus und Forschungsfähigkeit erzwingen eine Architektur, die **ruhig**, **nachvollziehbar** und **robust** ist.

---

## Die vier strukturellen Ebenen

Auf grober Ebene lässt sich BitGridAI in vier Schichten gliedern. Jede Schicht hat eine klar definierte Rolle – und kennt ihre Grenzen.

### 1. Der Entscheidungskern (Core)

Das Herz des Systems.

Hier werden **keine Geräte gesteuert**, **keine Protokolle gesprochen** und **keine UI-Details verarbeitet**. Der Core kennt nur:

* den aktuellen Zustand (`EnergyState`)
* die Zeit (BlockScheduler)
* die Regeln (R1–R5)

Seine Aufgabe ist es, aus einem gegebenen Zustand eine **deterministische Entscheidung** abzuleiten.

> Der Core *denkt* – er handelt nicht selbst.

---

### 2. Die Adapter-Schicht (Ports & Adapters)

Die Übersetzer zur realen Welt.

Adapter sprechen die Sprache der Geräte und Dienste:
Modbus, MQTT, REST, APIs, Dateien.

Ihre Aufgabe ist es:

* externe Signale in **interne Events** zu übersetzen
* Entscheidungen des Cores in **konkrete Befehle** zu überführen

Adapter enthalten **keine Fachlogik**. Sie wissen *wie* man etwas sagt – nicht *warum*.

---

### 3. Die Interaktionsschicht (Explain & Control)

Die Schnittstelle zum Menschen.

Diese Ebene macht Entscheidungen **sichtbar**, **verständlich** und **beeinflussbar**:

* Visualisierung von Zuständen und Flüssen
* Erklärung von Entscheidungen („Warum läuft der Miner?“)
* kontrollierte Eingriffe (Overrides, Preview)

Wichtig: Auch hier wird **nicht entschieden**. Eingriffe werden als Events an den Core zurückgespielt.

---

### 4. Die Gedächtnisschicht (Data & Research)

Was passiert ist, bleibt nachvollziehbar.

Diese Ebene speichert:

* operative Zustände (für den laufenden Betrieb)
* historische Daten (für Analyse und Forschung)

Append-only, versioniert und reproduzierbar.

> Ohne Gedächtnis keine Wissenschaft.

---

## Bewusste Trennlinien

Die grobe Struktur lebt von klaren Grenzen:

* Der **Core** kennt keine Hardware.
* Adapter kennen keine Regeln.
* Die UI erklärt, entscheidet aber nicht.
* Forschung liest Daten – sie steuert nichts.

Diese Trennungen sind absichtlich streng. Sie verhindern implizite Abhängigkeiten und machen das System langfristig wartbar.

---

## Einordnung (arc42)

Dieses Kapitel beschreibt die **strategische Systemstruktur**:

* grobe Aufteilung
* Verantwortlichkeiten
* Abhängigkeiten auf hoher Ebene

Konkrete Module, Klassen und Laufzeitdetails folgen erst in den nächsten Kapiteln:

* **Kapitel 5 – Bausteinsicht** (Was genau gibt es?)
* **Kapitel 6 – Laufzeitsicht** (Wie arbeitet das System im Betrieb?)

---

> **Nächster Schritt:** Die Struktur steht. Jetzt zoomen wir weiter hinein und betrachten die einzelnen Bausteine im Detail.
>
> 👉 Weiter zu **[4.3 Zentrale Architekturentscheidungen](./043_decisions.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
