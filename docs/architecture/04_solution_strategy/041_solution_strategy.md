# 04.1 Die grundlegende Strategie

Wie knacken wir die Nuss?

Um unsere ambitionierten Ziele (Transparenz, Autonomie, Sicherheit) unter den harten technischen Randbedingungen zu erreichen, setzen wir auf eine Architektur, die **Modularität, Local-First** und **Erklärbarkeit** radikal kombiniert.

Wir bauen kein "Smart Home Spielzeug", sondern eine wissenschaftliche Plattform für reproduzierbare Energie-Optimierung.

![Hamster erklärt die Strategie](link_zum_strategie_bild.png)

## Kurzüberblick

> **Die Strategie in einem Satz:**
> Wir steuern Energieflüsse durch deterministische Regeln (**R1–R5**) in einem **10-Minuten-Takt**, erklären jede Entscheidung via **On-Device Agent** und speichern alles manipulationssicher für die Forschung (**Parquet/Replay**). Keine Cloud.

---

## Unsere Architekturprinzipien

Diese sechs Prinzipien leiten jede Zeile Code in BitGridAI:

1.  **Trennung von Verantwortlichkeiten (Separation of Concerns) 🧩**
    Logik, Hardware-Adapter und Erklärungsschicht sind strikt getrennt. Ein neuer Wechselrichter-Typ erfordert keine Änderung an der Regel-Engine.
2.  **Transparenz zuerst (Transparency First) 🔍**
    Jede Aktion liefert zwingend `Reason`, `Trigger` und `Parameter`. Nutzer sehen eine Timeline und eine Vorschau ("Preview").
3.  **Lokal statt Cloud (Local-First) 🏠**
    Daten und Modelle bleiben auf der Nutzerhardware. Wir optimieren für Datenschutz und Resilienz, nicht für Cloud-Abos.
4.  **Echtzeit-Erklärbarkeit (Real-time Explainability) 🗣️**
    Ein lokaler "Explain-Agent" (kleines Sprachmodell oder Template-Engine) übersetzt technische Zustände in verständliche Sprache – direkt auf dem Gerät.
5.  **Nachhaltigkeit als Steuergröße 🌱**
    PV-Überschuss und Strompreis steuern die Last. Ein "Deadband" glättet die Entscheidungen, um Hardware zu schonen.
6.  **Forschungs- & Replay-Fähigkeit 🎓**
    Über einen "Research-Toggle" können erweiterte Datenexporte aktiviert werden. Logs sind so strukturiert, dass Szenarien exakt wiederholt ("Replay") werden können.

---

## Die 4 Technologischen Säulen

### 1. Der deterministische Kern (Core Logic) ⚙️
Statt einer Black-Box-KI nutzen wir eine transparente Regel-Engine in Python.
* **Logik:** Die Regeln **R1–R5** (Start, Autarkie, Thermo, Prognose, Stabilität) entscheiden.
* **Taktung:** Ein **BlockScheduler** erzwingt den 10-Minuten-Rhythmus (angelehnt an Bitcoin).
* **Policy:** Die "Hodl-Policy" entscheidet, wann Mining wirtschaftlicher ist als Einspeisen.

### 2. Hexagonale Kommunikation (Ports & Adapters) 🔌
Der Kern spricht nicht direkt mit Geräten.
* **Technik:** Asynchrone Kopplung via **MQTT** und **REST**.
* **Adapter:** Übersetzen spezifische Geräte-Sprachen (Modbus, API) in interne Events.

### 3. Daten & Logging (The Memory) 💾
Wir speichern Daten so, dass sie wissenschaftlich nutzbar sind.
* **Operationale Daten:** Liegen im **SQLite** (schnell, relational).
* **Historische Daten:** Werden im **Parquet**-Format (effizient, spaltenbasiert) gespeichert.
* **Integrität:** Das Logging ist "Append-only" – einmal geschrieben, wird nichts mehr gelöscht. Configs sind versionierte YAML-Dateien.

### 4. Explainability Layer (The Voice) 💬
Die Brücke zum Menschen.
* **UI:** Zeigt Timeline, Energieflüsse und Eingriffsmöglichkeiten.
* **On-Device Agent:** Generiert "Microcopy" (kurze Erklärtexte) und ermöglicht "Was-wäre-wenn"-Simulationen ohne Cloud-Verbindung.

---

## Warum machen wir das so? (Rationale)

* **Lokal-First** garantiert Datenschutz und Betriebssicherheit (auch ohne Internet).
* **Deterministische Regeln (R1-R5)** sind im Gegensatz zu reinen ML-Modellen testbar, beweisbar und für den Nutzer nachvollziehbar.
* **Der 10-Minuten-Takt** bringt Ruhe ins System und verhindert nervöses Schalten ("Flapping").
* **Replays & Parquet** machen BitGridAI zu einem ernsthaften Werkzeug für die Forschung, da Ergebnisse wissenschaftlich überprüft werden können.

---
> **Nächster Schritt:** Strategie verstanden? Gut. Dann zoomen wir jetzt rein und schauen uns an, aus welchen konkreten Bausteinen das System besteht.
>
> 👉 Weiter zu **[05 Bausteinsicht](../05_building_block_view/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
