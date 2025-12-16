# 10.2 – Qualitätsszenarien (Auszug)

Das Herzstück der Qualitätskontrolle.

Qualitätsszenarien sind **konkrete, überprüfbare Tests**, mit denen wir nachweisen, dass die Architektur von **BitGridAI** die geforderten Qualitätsmerkmale tatsächlich erfüllt.  
Sie übersetzen abstrakte Ziele (z.B. Sicherheit, Transparenz, Stabilität) in **messbare Situationen mit klaren Akzeptanzkriterien**.

Dieses Kapitel ist bewusst **szenariengetrieben** aufgebaut:  
Jede Seite beschreibt **ein Qualitätsmerkmal**, abgeleitet aus dem Qualitätsbaum (Kap. 10.1) und den Architekturentscheidungen (Kap. 09).

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster prüft eine Checkliste mit Häkchen bei „Safety“, „Stability“, „Explainability“.)*
![Übersicht der Qualitätsszenarien](../../media/pixel_art_hamster_scenario_test.png)

&nbsp;

## Überblick: Qualitätsszenarien nach arc42

Die Szenarien sind **in derselben Reihenfolge** strukturiert wie der Qualitätsbaum:

| Nr. | Qualitätsmerkmal | Dokument |
|---|---|---|
| **10.2.1** | Transparenz & Erklärbarkeit | 👉 **[1021_explainability.md](./1021_explainability.md)** |
| **10.2.2** | Autonomie & Privacy | 👉 **[1022_autonomy_and_privacy.md](./1022_autonomy_and_privacy.md)** |
| **10.2.3** | Vorhersagbarkeit & Stabilität | 👉 **[1023_predictability_and_stability.md](./1023_predictability_and_stability.md)** |
| **10.2.4** | Nachhaltigkeit & Ökonomie | 👉 **[1024_sustainability_and_economics.md](./1024_sustainability_and_economics.md)** |
| **10.2.5** | Sicherheit (Safety & Resilience) | 👉 **[1025_safety.md](./1025_safety.md)** |
| **10.2.6** | Reproduzierbarkeit & Erweiterbarkeit | 👉 **[1026_reproducibility_and_extensibility.md](./1026_reproducibility_and_extensibility.md)** |
| **10.2.7** | Performance & Ressourceneffizienz | 👉 **[1027_performance_and_efficiency.md](./1027_performance_and_efficiency.md)** |

Jedes Dokument folgt demselben Muster:
- Qualitätsziel  
- Kontext  
- Konkrete Szenarien (Stimulus → Reaktion)  
- Messbare Akzeptanzkriterien  
- Bezug zu Regeln (R1–R5), Architektur- und Laufzeitsichten  

&nbsp;

## Szenarien-Index (Kurzreferenz)

Die folgende Tabelle dient als **Querindex** über alle Qualitätsszenarien hinweg.  
Die detaillierte Beschreibung befindet sich jeweils im verlinkten Dokument.

| ID | Szenario | Zielqualität | Referenz |
|---|---|---|---|
| **S1** | Transparente Begründung (R1) | Explainability | 1021 |
| **S2** | Energieadaptive Steuerung | Nachhaltigkeit | 1024 |
| **S3** | MQTT / Broker Down | Resilienz | 1025 |
| **S4** | Manueller Override mit TTL | Autonomie | 1022 |
| **S6** | Safety-Stop bei Übertemperatur | Sicherheit | 1025 |
| **S7** | Autarkie-Schutz (SoC) | Sicherheit / Autonomie | 1022, 1025 |
| **S8** | Deadband-Stabilität | Vorhersagbarkeit | 1023 |
| **S9** | Prognose-Start (R4) | Vorhersagbarkeit | 1023 |
| **S11** | Hodl-Entscheidung | Nachhaltigkeit / Traceability | 1024, ADR 018 |
| **S12** | PoW-Telemetrie & Compliance | Sicherheit | 1025 |

&nbsp;

## Einordnung

Diese Qualitätsszenarien sind:
- **architekturrelevant** (kein Testplan, sondern Qualitätsnachweis),
- **deterministisch prüfbar** (Replay-fähig),
- und direkt mit Regeln (R1–R5), ADRs und Laufzeitszenarien verknüpft.

Sie bilden die Grundlage für:
- Architektur-Reviews,
- Regressionstests nach Änderungen,
- und die Bewertung, ob BitGridAI „gut genug“ ist.

---

> **Nächster Schritt:**  
> Wir kennen jetzt die Zielqualität und ihre Prüfungen.  
> Als Nächstes betrachten wir die **Risiken und technischen Schulden**, die sich aus dieser Architektur ergeben.
>
> 👉 Weiter zu **[11 Risiken & Technische Schulden](../11_risks_and_technical_debt/README.md)**  
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
