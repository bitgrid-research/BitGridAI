# 10 – Qualitätsszenarien / Quality Scenarios

## Überblick / Overview

Dieses Kapitel beschreibt die Qualitätsszenarien, die das Verhalten und die Stabilität von BitGridAI in realen Betriebssituationen definieren.
Sie dienen zur Überprüfung, ob die Systemarchitektur die angestrebten Qualitätsziele – **Transparenz, Erklärbarkeit, Nachhaltigkeit und Resilienz** – erfüllt.

> This chapter defines the quality scenarios that describe BitGridAI’s behavior and stability under real-world operating conditions.
> They verify whether the architecture achieves its core quality goals – **transparency, explainability, sustainability, and resilience**.

---

## Zielqualitäten / Quality Attributes

| Qualität                | Beschreibung                                                     |
| ----------------------- | ---------------------------------------------------------------- |
| **Transparenz**         | Alle Systementscheidungen sind nachvollziehbar und begründet.    |
| **Erklärbarkeit**       | Nutzer verstehen Systemverhalten in Echtzeit.              |
| **Nachhaltigkeit**      | Energieverbrauch wird an erneuerbare Erzeugung angepasst.        |
| **Datenschutz**         | Keine externen Datenströme, vollständige lokale Kontrolle.       |
| **Resilienz**           | System bleibt auch bei Teilausfällen funktionsfähig.             |
| **Erweiterbarkeit**     | Neue Module können ohne Eingriff in Kernlogik integriert werden. |
| **Benutzbarkeit (HCI)** | Interfaces fördern Vertrauen, Kontrolle und Verständnis.         |

> | Quality             | Description                                                    |
> | ------------------- | -------------------------------------------------------------- |
> | **Transparency**    | All system decisions are traceable and justified.              |
> | **Explainability**  | Users understand system behavior in real time.                 |
> | **Sustainability**  | Energy use adapts to renewable generation.                     |
> | **Privacy**         | No external data streams; full local control.                  |
> | **Resilience**      | System remains operational despite partial failures.           |
> | **Extensibility**   | New modules can be integrated without changing the core logic. |
> | **Usability (HCI)** | Interfaces foster trust, control, and understanding.           |

---

## Szenario 1 – Transparente Entscheidungsbegründung

**Auslöser:** Änderung der PV-Leistung.
**Erwartetes Verhalten:** System aktualisiert Entscheidung und generiert automatisch eine Erklärung.
**Qualitätsziel:** Nachvollziehbare Logik und visuelle Rückmeldung für Nutzer.

> **Trigger:** Change in PV output.
> **Expected Behavior:** System updates decision and automatically generates an explanation.
> **Quality Goal:** Traceable logic and visual user feedback.

---

## Szenario 2 – Energieadaptive Steuerung

**Auslöser:** PV-Erzeugung fällt unter vordefinierten Schwellenwert.
**Erwartetes Verhalten:** System reduziert Last (z. B. Mining pausieren) und dokumentiert Grund.
**Qualitätsziel:** Energieeffizienz und nachhaltige Nutzung.

> **Trigger:** PV generation drops below threshold.
> **Expected Behavior:** System reduces load (e.g., pauses mining) and logs rationale.
> **Quality Goal:** Energy efficiency and sustainable operation.

---

## Szenario 3 – Lokale Fehlertoleranz

**Auslöser:** Verlust der Netzwerkverbindung oder MQTT-Broker-Ausfall.
**Erwartetes Verhalten:** Core arbeitet im Offline-Modus weiter; Logs werden lokal zwischengespeichert.
**Qualitätsziel:** Resilienz und autarke Funktionsfähigkeit.

> **Trigger:** Network connection loss or MQTT broker failure.
> **Expected Behavior:** Core continues in offline mode; logs are buffered locally.
> **Quality Goal:** Resilience and autonomous operation.

---

## Szenario 4 – Nutzerfeedback und Override

**Auslöser:** Nutzer lehnt automatische Entscheidung ab.
**Erwartetes Verhalten:** System akzeptiert Override, speichert Feedback und passt Regelmodell an.
**Qualitätsziel:** Erklärbarkeit, Vertrauen, lernfähige Interaktion.

> **Trigger:** User rejects automatic decision.
> **Expected Behavior:** System accepts override, stores feedback, and adapts rule model.
> **Quality Goal:** Explainability, trust, adaptive interaction.

---

## Szenario 5 – Erweiterung durch neues Modul

**Auslöser:** Integration eines neuen Sensors oder Verbrauchertyps.
**Erwartetes Verhalten:** Neues Modul wird per MQTT registriert und in Core integriert, ohne Neustart.
**Qualitätsziel:** Erweiterbarkeit und Modularität.

> **Trigger:** Addition of a new sensor or load type.
> **Expected Behavior:** New module registers via MQTT and integrates into core without restart.
> **Quality Goal:** Extensibility and modularity.

---

## Bewertung / Evaluation Criteria

| Kriterium                       | Metrik / Beobachtung                      | Zielwert     |
| ------------------------------- | ----------------------------------------- | ------------ |
| **Erklärzeit**                  | Zeit zwischen Entscheidung und Erklärung  | < 2 Sekunden |
| **Energieeffizienz**            | Anteil der Betriebszeit mit PV-Überschuss | > 70%        |
| **Systemverfügbarkeit**         | Betriebszeit ohne kritische Fehler        | > 99%        |
| **Datenschutzprüfung**          | Externe Verbindungen erkannt              | 0            |
| **Nutzerakzeptanz (HCI-Tests)** | Subjektive Zufriedenheit (Likert-Skala)   | > 4/5        |

> | Criterion                       | Metric / Observation                   | Target      |
> | ------------------------------- | -------------------------------------- | ----------- |
> | **Explanation Latency**         | Time between decision and explanation  | < 2 seconds |
> | **Energy Efficiency**           | Operating time with PV surplus         | > 70%       |
> | **System Availability**         | Runtime without critical failure       | > 99%       |
> | **Privacy Check**               | External connections detected          | 0           |
> | **User Acceptance (HCI Tests)** | Subjective satisfaction (Likert scale) | > 4/5       |

---

## Zusammenfassung / Summary

Die Qualitätsszenarien bilden die Grundlage für kontinuierliche Evaluation und Verbesserung.
Sie gewährleisten, dass BitGridAI nicht nur **funktional korrekt**, sondern auch **vertrauenswürdig, effizient und nachvollziehbar** arbeitet.

> The quality scenarios serve as the basis for continuous evaluation and improvement.
> They ensure that BitGridAI operates not only **functionally correctly** but also **trustworthy, efficient, and explainable**.
