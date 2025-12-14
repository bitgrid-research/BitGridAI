# 04.2 Grobe Systemstruktur

Vom Plan zur Form.

Nachdem wir die **architektonischen Grundpfeiler** festgelegt haben, stellt sich die nächste logische Frage:  
Wie übersetzen wir diese Haltung in eine **tragfähige Struktur**, die langfristig stabil bleibt?

Dieses Kapitel beschreibt die **grobe Systemstruktur** von **BitGridAI**.  

Noch ohne Klassen, noch ohne Implementierungsdetails – aber klar genug, um zu verstehen, **welche großen Teile es gibt**, **welche Verantwortung sie tragen** und **wie sie zusammenwirken**.

Wir beantworten hier bewusst nicht die Frage *„Wie ist etwas implementiert?“*, sondern:

> **Wo gehört etwas grundsätzlich hin – und wo ganz bewusst nicht?**

*(Platzhalter für ein Bild: Der Hamster steht vor einem Bauplan. Große Blöcke sind eingezeichnet, verbunden durch dicke Pfeile. Keine Schrauben, keine Kabel – nur Struktur.)*

---

## Die Idee hinter der Struktur

BitGridAI folgt einer einfachen, aber strengen Ordnung:

* **Ein klarer Kern**, der entscheidet  
* **Klare Ränder**, die messen, handeln oder erklären  
* **Keine Querverbindungen**, die Verantwortung verwischen  

Diese Ordnung ist kein Selbstzweck.  
Sie ist die direkte Konsequenz aus unseren Grundpfeilern:

Local First, Transparenz, Determinismus und Forschungsfähigkeit erzwingen eine Architektur, die **ruhig**, **nachvollziehbar** und **robust** ist – auch dann, wenn das System wächst.

---

## Die vier strukturellen Ebenen – Überblick

Auf hoher Ebene lässt sich BitGridAI in vier klar abgegrenzte Ebenen gliedern.  
Jede Ebene hat eine eindeutige Rolle – und kennt ihre Grenzen.

| Ebene | Rolle im System | Verantwortlichkeiten | Bewusste Abgrenzung |
| :--- | :--- | :--- | :--- |
| **Entscheidungskern (Core)** ⚙️ | Das Herz des Systems. Trifft fachliche Entscheidungen. | • Lesen des `EnergyState`<br>• Zeitliche Taktung (BlockScheduler)<br>• Auswertung der Regeln (R1–R5)<br>• Erzeugen von DecisionEvents | • Steuert keine Geräte<br>• Spricht keine Protokolle<br>• Kennt keine UI |
| **Adapter-Schicht (Ports & Adapters)** 🔌 | Übersetzer zwischen System und Außenwelt. | • Lesen externer Messwerte<br>• Übersetzen von Protokollen (Modbus, MQTT, REST)<br>• Umsetzen von Entscheidungen in Befehle | • Keine Fachlogik<br>• Keine Regeln<br>• Keine Entscheidungen |
| **Interaktionsschicht (Explain & Control)** 🖥️ | Schnittstelle zum Menschen. | • Visualisierung von Zuständen und Flüssen<br>• Erklärung von Entscheidungen<br>• Entgegennahme von Overrides und Previews | • Trifft keine Energieentscheidungen<br>• Verändert den Core nicht direkt |
| **Gedächtnisschicht (Data & Research)** 💾 | Nachvollziehbarkeit und Forschung. | • Operative Speicherung (Hot Data)<br>• Historische Logs (Cold Data)<br>• Replays und KPI-Berechnung | • Keine Steuerung<br>• Kein Eingriff in den Betrieb |

---

## Bewusste Trennlinien

Die Stabilität der Struktur entsteht durch klare Grenzen:

* Der **Core** kennt keine Hardware.  
* Adapter kennen keine Regeln.  
* Die UI erklärt, entscheidet aber nicht.  
* Forschung liest Daten – sie steuert nichts.  

Diese Trennlinien sind **absichtlich streng**.  

Sie verhindern implizite Abhängigkeiten und sorgen dafür, dass BitGridAI wartbar bleibt – auch dann, wenn neue Geräte, Regeln oder Auswertungen hinzukommen.


---

> **Nächster Schritt:** Die Struktur steht. Jetzt zoomen wir weiter hinein und betrachten die einzelnen Bausteine im Detail.
>
> 👉 Weiter zu **[4.3 Zentrale Architekturentscheidungen](./043_decisions.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
