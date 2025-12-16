# 10.2 - Qualitätsszenarien (Auszug)

Das Herzstück der Qualitätskontrolle.

Qualitätsszenarien sind spezifische, nachvollziehbare Tests, die beweisen, dass die Architektur die gestellten Anforderungen erfüllt. Jedes Szenario prüft eine kritische Eigenschaft (z.B. Sicherheit, Transparenz) und hat messbare Erfolgskriterien.

*(Platzhalter für ein Bild: Eine Tabelle oder ein Flussdiagramm, das die Szenarien S6 (Safety Stop) und S8 (Deadband) als kritische Prüfpunkte hervorhebt.)*
![Übersicht der Qualitätsszenarien](../../media/pixel_art_hamster_scenario_test.png)

&nbsp;

## Szenarien-Tabelle

| ID | Szenario | Zielqualität | Getestete Regel | Antwort/Maß |
| :--- | :--- | :--- | :--- | :--- |
| **S1** | **Transparente Begründung (R1)** | Explainability | R1, UI | `DecisionEvent` im UI: Reason/Trigger/Params sichtbar; Explanation Latency < 2s. |
| **S2** | **Energieadaptive Steuerung** | Nachhaltigkeit | R1, R4 | Miner muss bei Surplus/Preis unter Schwelle stoppen. KPI: Flapping Rate ↓ ggü. Baseline. |
| **S3** | **MQTT/Broker Down** | Resilienz | R3, 08.5 | Adapterfehler führt zu **hold** + Offline-Puffer. System bleibt operational (Availability > 99 %). |
| **S4** | **Manueller Override** | HCI/Autonomie | R5, 06.6 | Start/Stop mit TTL (Block-Dauer); **Auto-Rollback** zum Auto-Mode am Blockende. |
| **S6** | **Safety-Stop (Temp)** | Sicherheit | R3 (Critical) | **Sofortiger Stop** bei Temperaturüberschreitung; Deadband (R5) wird ignoriert; KPI: Thermal Incidents = 0. |
| **S7** | **Autarkie-Schutz (SoC)** | Sicherheit/Autonomie | R2 (Veto) | **Stop/Block** bei Low SoC (z.B. 20 %). Resume erfolgt mit **Hysterese** (z.B. erst bei 30 %). |
| **S8** | **Deadband-Stabilität** | Vorhersagbarkeit | R5 | Miner muss nach Start/Stop für D Blöcke (z.B. 20 Min) den Zustand halten. KPI: Switches/h sinken. |
| **S9** | **Prognose-Start (R4)** | Vorhersagbarkeit | R4 | Start wird nur bei stabiler Forecast-Confidence (z.B. > 0.7) zugelassen, sonst Veto. |
| **S11** | **Hodl-Entscheidung** | Nachhaltigkeit/Traceability | 09.1 ADR 018 | Wenn `preferred_path=hodl` aktiv, muss der gewählte Energiepfad und die ökonomische Größe (`sats_per_kWh`) transparent im Log gespeichert werden. |
| **S12** | **PoW-Telemetrie & Sicherheit** | Sicherheit/Compliance | R3, R1 | Reaktion <2s auf Effizienz/Temp-Abweichung; Hashprobe (Nachweis der Arbeit) muss in den Logs (Parquet) enthalten sein. |

> Vollständige Details & Runbooks (inkl. detaillierter Schritte zur Durchführung der Szenarien) finden sich im nachfolgenden Dokument.

---
> **Nächster Schritt:** Wir haben die gewünschte Qualität definiert. Jetzt betrachten wir die Risiken, die diese Architektur mit sich bringt.
>
> 👉 Weiter zu **[11 Risiken und Technischer Schulden](../11_risks_and_technical_debt/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
