# 10.1 - Quality Tree / Qualitätsbaum

Die relevanten Qualitätsmerkmale für BitGridAI.

Der Qualitätsbaum stellt sicher, dass wir bei der Entwicklung und dem Testen keinen wichtigen Aspekt vergessen. Er spiegelt die Hauptziele wider: **Sicherheit, Transparenz und nachhaltige Autonomie.**

*(Platzhalter für ein Bild: Eine Mindmap-ähnliche Darstellung des Qualitätsbaumes mit "BitGridAI" in der Mitte und den sechs Hauptästen.)*
![Mindmap des Qualitätsbaumes](../../media/pixel_art_hamster_quality_tree.png)

&nbsp;

## Strukturierte Übersicht (Hierarchie)

Die Qualitätsmerkmale sind in sechs Hauptkategorien unterteilt, die unsere Architekturentscheidungen (09.1 ADRs) direkt widerspiegeln.

### 1. Transparenz & Erklärbarkeit (Explainability)
* **Grundprinzip:** Entscheidungen müssen jederzeit nachvollziehbar sein.
    * `Reason/Trigger/Params`: Jede Entscheidung muss Begründung, Auslöser und verwendete Parameter loggen.
    * `Timeline & Next-Block-Preview`: Die UI muss den historischen Verlauf und die **erwartete** Aktion im nächsten Block zeigen.
    * `Explain-Agent on-device`: Die KI-gestützte Erklärung muss lokal ohne Cloud-Anbindung funktionieren.

### 2. Autonomie & Privacy
* **Grundprinzip:** Kontrolle und Datenhoheit bleiben beim Nutzer.
    * `Local-first`: 100% on-prem-Betrieb (ADR 001).
    * `keine Telemetrie`: Null Cloud-Backhaul (ADR 014).
    * `minimale Ports, lokale Auth`: Reduzierte Angriffsfläche, Authentifizierung erfolgt lokal.

### 3. Nachhaltigkeit (Sustainability / Economic Viability)
* **Grundprinzip:** Optimierung der Energiepfade und des wirtschaftlichen Nutzens.
    * `Surplus/Preis-Steuerung (R1/R4)`: Priorisierung der Miner-Aktivität nach PV-Überschuss und idealen Preis-Zyklen.
    * `Hodl/Heat/Export-Policies`: Transparente Entscheidung über Opportunitätskosten (ADR 018).

### 4. Vorhersagbarkeit & Stabilität
* **Grundprinzip:** Das System muss verlässlich und frei von Flapping sein.
    * `10-Min-BlockScheduler, Deadband (R5)`: Fester Takt und Halteschwellen verhindern unnötige Schaltzyklen (ADR 006, 009).
    * `deterministische R1–R5`: Regeln sind Code, nicht ML-Black-Box, daher immer testbar und vorhersehbar (ADR 007).

### 5. Sicherheit (Safety & Resilience)
* **Grundprinzip:** Schutz der Hardware und des Hauses.
    * `Thermo/SoC-Schutz (R3/R2)`: Sofortiger **STOP** bei kritischen Schwellen.
    * `Stop → Safe bei Fehlern`: Fail-Safe-Zustand wird immer gewählt.
    * `Fail-Safe bei Fehlern`: Graceful Degradation (08.5).

### 6. Reproduzierbarkeit & Erweiterbarkeit
* **Grundprinzip:** Das System muss auditierbar, wartbar und anpassbar sein.
    * `Append-only Logs, Replay`: …
    * `Adapter-Architektur`: …
    * `Self-contained Deploy`: Ein Host, ein Stack, klare Backups (Kap. 07).

 ### 7. Performance & Ressourceneffizienz
* **Grundprinzip:** Entscheidungen müssen rechtzeitig und Edge-tauglich erfolgen.
    * `Block-Tick < 300 ms`: Regel-Auswertung innerhalb eines festen Zeitbudgets.
    * `Edge-tauglich`: CPU-/RAM-Verbrauch geeignet für Raspberry Pi / NUC.
    * `No Busy Loops`: Ereignis- und blockgetriebene Verarbeitung.


---
> **Nächster Schritt:** Wir prüfen diese Qualitätsmerkmale anhand konkreter Nutzungsszenarien.
>
> 👉 Weiter zu **[102 Qualitätsszenarien](../10_quality_scenarios/102_quality_scenarios)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
