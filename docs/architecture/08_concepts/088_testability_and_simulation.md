# 8.8 - Testbarkeit, Simulation & Replays

Härtetest ohne Hardware.

BitGridAI agiert in der realen Welt: mit Wechselrichtern, Batterien und potenziell heißen Minern.  
Physische Tests sind teuer, langsam und riskant – und für viele Szenarien schlicht nicht praktikabel.

Daher ist es ein fundamentales architektonisches Ziel, dass **das gesamte System ohne physische Hardware lauffähig, testbar und überprüfbar ist**.  
Möglich wird dies durch:
- die strikte Trennung von Core und Adaptern (hexagonale Architektur),
- deterministische Regeln (R1–R5),
- immutable Zustände und blockbasierten Takt.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster testet ein komplexes System in einer Sandkasten-Simulation, während echte Hardware sicher im Hintergrund bleibt.)*
![Hamster führt Simulation durch](../../media/pixel_art_hamster_simulation.png)

&nbsp;

## Ziel: Deterministische Entscheidungen

Grundprinzip:
> **Eine Entscheidung ist nur dann vertrauenswürdig, wenn sie reproduzierbar ist.**

Testbarkeit in BitGridAI bedeutet:
- gleiche Eingaben → gleiche Entscheidungen,
- klare Trennung von Logik und Umwelt,
- überprüfbares Verhalten auch lange nach dem Live-Betrieb.

Determinismus ist kein Test-Feature, sondern ein **Architekturversprechen**.

&nbsp;

## Testarten & Ebenen

Dank der klaren Trennung von Logik und I/O können verschiedene Testebenen systematisch eingesetzt werden:

| Testart | Gegenstand | Ziel |
|------|-----------|------|
| **Unit-Tests** | Regeln R1–R5, Schwellen, Prioritäten, Hysterese | Korrektheit der Kernlogik (z.B. Vorrang R3 vor R2/R1) |
| **Integrationstests** | Schnittstellen (MQTT, REST), Adapter-Anbindung | Korrekte Systemreaktionen auf externe Signale |
| **Replay-Tests** | Historische Zustands- & Entscheidungsdaten | **Reproduzierbarkeit** vergangener Entscheidungen |
| **Policy- & A/B-Tuning** | Deadbands, Forecast-Margen, Strategien | Vergleich neuer Regelparameter gegen Baselines |

Diese Ebenen bauen aufeinander auf und adressieren jeweils unterschiedliche Risiken.

&nbsp;

## Simulation

Simulation ersetzt reale Umwelt durch kontrollierte Datenquellen.

Typische Simulationsinhalte:
- PV-Erzeugungsprofile
- Strompreisverläufe
- Batterie- und Lastmodelle
- Adapter- und Sensor-Ausfälle

Simulationen sind:
- reproduzierbar,
- zeitlich steuerbar,
- frei kombinierbar.

Sie ermöglichen Tests von:
- Grenz- und Extremfällen,
- seltenen Fehlerzuständen,
- neuen Regelparametern – ohne reale Hardware zu gefährden.

&nbsp;

## Replays (Audit & Forschung)

Replays sind ein zentrales Werkzeug für Qualitätssicherung und Audit.

Ein Replay:
- nutzt historische Zustandsdaten,
- spielt diese deterministisch erneut ab,
- erzeugt Entscheidungen und Events neu.

Replays dienen:
- Regressionstests nach Code- oder Config-Änderungen,
- Analyse vergangener Entscheidungen,
- Vergleich alternativer Strategien.

Replays sind strikt **read-only** und beeinflussen niemals das Live-System.

&nbsp;

## Fault Injection & Robustheit

Zur gezielten Überprüfung von Fail-safe- und Degradationslogik werden Fehler bewusst simuliert, z.B.:

- ausbleibende Sensordaten,
- Adapter- oder Broker-Ausfälle,
- Übertemperatur-Szenarien.

Ziel ist nicht das „Durchhalten um jeden Preis“, sondern:
- korrektes Umschalten in Safe- oder Stop-Zustände,
- klare Events und Erklärungen,
- kontrollierte Recovery-Pfade.

Diese Tests validieren direkt die Prinzipien aus Kapitel 8.6.

&nbsp;

## Bewertung & Erfolgskriterien (KPIs)

Die Wirkung von Tests, Simulationen und Regelanpassungen wird über messbare Kennzahlen bewertet:

| KPI | Ziel | Zweck |
|----|------|------|
| **Decision Latency** | niedrig | Performance des Cores |
| **Explanation Latency** | niedrig | UX-Qualität |
| **Thermal Incidents** | 0 | Safety-Garantie |
| **Flapping Rate** | sinkend | Wirksamkeit von R5 |
| **Grid Import** | minimiert | Ökonomischer Erfolg |
| **Explainability Coverage** | 100 % | Auditierbarkeit |

KPIs verbinden technische Qualität mit realer Systemwirkung.

&nbsp;

## Testbarkeit & Betrieb

Testbarkeit ist Voraussetzung für sicheren Betrieb:

- Updates werden erst nach erfolgreichen Replays freigegeben,
- neue Konfigurationen können vorab simuliert werden,
- Rollbacks basieren auf bekannten, geprüften Zuständen.

Damit bildet Testbarkeit die Brücke zwischen Entwicklung und Betrieb.

&nbsp;

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete Testframeworks oder CLI-Tools,
- CI/CD-Implementierungen,
- detaillierte Testskripte.

Diese gehören in Entwickler- oder Betriebsdokumentation.

&nbsp;

## Zusammenfassung

Testbarkeit, Simulation und Replays stellen sicher, dass BitGridAI:
- zuverlässig weiterentwickelt werden kann,
- Entscheidungen überprüfbar bleiben,
- Vertrauen durch Wiederholbarkeit entsteht.

BitGridAI wird nicht nur betrieben –  
es wird **bewiesen**.

---

> **Nächster Schritt:**  
> Wenn Qualität geprüft ist, stellt sich die Frage nach kontrollierter Auslieferung.  
> Im nächsten Kapitel betrachten wir die **Build-, Update- & Release-Prinzipien**.
>
> 👉 Weiter zu **[8.9 Build-, Update- & Release-Prinzipien](./089_build_and_release.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
