# 04.1 Leitende Architekturprinzipien

Willkommen bei den Grundsätzen.

In diesem Kapitel geht es nicht um Klassen, Protokolle oder Datenformate – sondern um Haltung. Die hier beschriebenen Prinzipien sind die **Spielregeln**, nach denen BitGridAI entworfen wird. Sie sind nicht verhandelbar und prägen jede größere Architekturentscheidung.

Wenn Kapitel 2 die äußeren Leitplanken beschreibt, dann definieren diese Prinzipien die **innere Logik** des Systems.

*(Platzhalter für ein Bild: Der Hamster steht vor einem Regelwerk an der Wand – ein paar klare Symbole, keine tausend Bulletpoints.)*

---

## Local First – Energie entscheidet lokal

BitGridAI folgt konsequent dem Prinzip **Local First**.

Alle relevanten Daten, Zustände und Entscheidungen verbleiben auf der lokalen Infrastruktur des Nutzers. Es gibt keine zwingende Cloud-Abhängigkeit, keinen externen Kontrollpunkt und keinen versteckten Datenabfluss.

**Warum?**

Energie ist physisch. Sie entsteht, fließt und wird verbraucht vor Ort. Entscheidungen über diese Energie müssen dort getroffen werden, wo sie wirkt.

Local First bedeutet konkret:

* Betrieb auch ohne Internetverbindung
* Volle Datensouveränität beim Nutzer
* Vorhersagbares Verhalten ohne externe Abhängigkeiten

Cloud-Dienste sind damit kein Fundament, sondern – wenn überhaupt – optionale Erweiterungen.

---

## Ereignisorientierung – Reaktion statt Dauerfeuer

BitGridAI ist ereignisgetrieben aufgebaut.

Statt permanent Zustände zu pollen oder „live nachzuregeln“, reagiert das System auf klar definierte Ereignisse: neue Messwerte, Zeitfenster, Nutzerinteraktionen oder Regelentscheidungen.

Ein fester **10-Minuten-Takt** strukturiert diese Ereignisse zusätzlich.

**Warum?**

* Ursache und Wirkung bleiben nachvollziehbar
* Entscheidungen werden ruhiger und stabiler
* Hardware wird geschont (kein Flapping)

Das System verhält sich dadurch weniger wie ein nervöser Regler – und mehr wie ein planender Operator.

---

## Explainability – Vertrauen ist kein Nebenprodukt

Automatisierung ohne Erklärung ist keine Hilfe, sondern ein Risiko.

Explainability ist bei BitGridAI kein nachträglich aufgesetztes UI-Feature, sondern ein **architektonisches Prinzip**. Jede relevante Entscheidung ist erklärbar.

Das bedeutet:

* Jede Aktion kennt ihren Auslöser
* Jede Entscheidung verweist auf eine Regel
* Jeder Effekt lässt sich zeitlich nachvollziehen

Der Nutzer sieht nicht nur *was* passiert, sondern *warum* es passiert.

Das schafft Vertrauen – und ermöglicht bewusstes Eingreifen.

---

## Determinismus – keine Black Box

Im Kern von BitGridAI stehen **deterministische Regeln** statt undurchsichtiger Black-Box-Modelle.

Regeln sind explizit formuliert, testbar und reproduzierbar. Gleiche Eingaben führen zu gleichen Entscheidungen.

**Warum?**

* Entscheidungen lassen sich prüfen und erklären
* Fehler können systematisch analysiert werden
* Szenarien sind reproduzierbar (Replay)

Maschinelles Lernen kann punktuell unterstützen, ersetzt aber nicht den regelbasierten Kern.

---

## Trennung von Verantwortung – Klarheit vor Cleverness

BitGridAI trennt strikt zwischen:

* fachlicher Entscheidungslogik
* technischer Anbindung von Geräten
* Interaktion mit Nutzer und Forschung

Kein Wechselrichter kennt Regeln. Keine Regel kennt Modbus. Keine UI entscheidet über Energieflüsse.

**Warum?**

* Änderungen bleiben lokal begrenzt
* Komponenten bleiben austauschbar
* Das System bleibt langfristig wartbar

Diese Trennung ist der Schlüssel dafür, dass BitGridAI wachsen kann, ohne an Komplexität zu ersticken.

---

## Einordnung

Diese Prinzipien sind bewusst knapp gehalten. Sie dienen als Referenzpunkt für alle folgenden Kapitel:

* In **04.2** werden sie in eine grobe Systemstruktur übersetzt.
* In **Kapitel 5** zeigen sich ihre Auswirkungen auf konkrete Bausteine.
* In **Kapitel 6** werden sie im Laufzeitverhalten sichtbar.

---

> **Nächster Schritt:** Aus Prinzipien wird Struktur. Im nächsten Kapitel betrachten wir die **grobe Systemstruktur** von BitGridAI.
>
> 👉 Weiter zu **[04.2 Grobe Systemstruktur](./042_structure.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
