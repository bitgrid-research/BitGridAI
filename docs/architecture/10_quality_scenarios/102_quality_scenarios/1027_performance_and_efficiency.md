# 10.2.7 Performance & Ressourceneffizienz

Schnell genug. Nicht schneller.

BitGridAI läuft auf **Edge-Hardware** und steuert reale Energieflüsse.  
Performance ist daher kein Selbstzweck und kein Benchmark-Wettbewerb, sondern eine **harte Qualitätsanforderung**:  
Entscheidungen müssen **rechtzeitig, vorhersagbar und ressourcenschonend** erfolgen – auch unter Last.

Dieses Qualitätsszenario beschreibt, wie BitGridAI **reaktionsfähig bleibt, ohne die Hardware zu überfordern oder Stabilität zu opfern**.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster sitzt vor einer Stoppuhr und einem kleinen Einplatinencomputer. Auf der Uhr steht „< 300 ms“, auf dem Rechner „Edge“. Der Hamster wirkt entspannt.)*

---

## Qualitätsziel

**Zeitlich deterministische Entscheidungen bei minimalem Ressourcenverbrauch.**

Das System soll:
- innerhalb fester Zeitbudgets entscheiden,
- auch auf schwacher Hardware stabil laufen,
- und Nebenfunktionen (UI, Explainability, Logging) strikt vom Entscheidungsweg entkoppeln.

---

## Kontext

- Deployment auf Edge-Hosts (Raspberry Pi, NUC, VM) – Kap. 07
- Blockbasierter Entscheidungszyklus (10-Min-Takt) – Kap. 06
- Deterministische Regeln R1–R5
- Explainability und UI laufen parallel zum Core

---

## Szenario P-1: Regulärer Block-Tick unter Normal-Last

**Stimulus:**  
Ein neuer Block-Tick wird ausgelöst.

**Quelle:**  
BlockScheduler

**Umgebung:**  
Normalbetrieb mit aktiver Sensorik und UI

**Erwartete Systemreaktion:**
- Rule Engine evaluiert alle relevanten Regeln
- DecisionEvent wird erzeugt oder bewusst nicht erzeugt
- Ergebnis wird veröffentlicht (MQTT / UI)

**Akzeptanzkriterien:**
- Entscheidungsdauer < **300 ms**
- Keine Blockierung durch UI oder Logging
- CPU-Spike bleibt kurzzeitig

---

## Szenario P-2: Explainability-Anfrage während Entscheidungsphase

**Stimulus:**  
Nutzer fragt im UI: „Warum läuft der Miner gerade?“

**Quelle:**  
UI / Explain-Agent

**Umgebung:**  
Parallel zum Block-Tick

**Erwartete Systemreaktion:**
- Explainability nutzt gespeicherte DecisionEvents
- Core-Entscheidungslogik wird **nicht** verzögert
- Antwort erfolgt asynchron

**Akzeptanzkriterien:**
- Core-Latenz unverändert
- Explain-Latenz < **2 s**
- Keine Locks auf dem EnergyState

---

## Szenario P-3: Hohe Ereignisdichte (Sensor-Rauschen)

**Stimulus:**  
Viele Telemetrie-Updates in kurzer Zeit.

**Quelle:**  
Sensoren / Adapter

**Umgebung:**  
Instabile Umweltbedingungen

**Erwartete Systemreaktion:**
- Ereignisse werden aggregiert oder gepuffert
- Keine sofortigen Regel-Neuberechnungen
- Entscheidung erfolgt erst beim nächsten Block

**Akzeptanzkriterien:**
- Keine Busy-Loops
- Kein CPU-Dauerlastzustand
- Entscheidung bleibt blockbasiert

---

## Szenario P-4: Ressourcenknappheit auf dem Host

**Stimulus:**  
Hohe CPU- oder RAM-Auslastung auf dem Edge-Host.

**Quelle:**  
Betriebssystem

**Umgebung:**  
Nebenprozesse aktiv (Backups, UI, Research)

**Erwartete Systemreaktion:**
- Core behält Priorität
- Nicht-kritische Dienste dürfen verzögern
- Keine unkontrollierten Neustarts oder Timeouts

**Akzeptanzkriterien:**
- Core bleibt reaktionsfähig
- Keine Entscheidung wird ausgelassen
- System degradiert kontrolliert

---

## Messbare Qualitätsmerkmale

| Merkmal | Ziel |
|------|------|
| Block-Tick-Latenz | < 300 ms |
| Explain-Latenz | < 2 s |
| Dauerhafte CPU-Last | niedrig / stabil |
| Busy-Loops | 0 |
| Core-Blockierung durch UI | 0 |

---

## Bezug zur Architektur

- **BlockScheduler:** Kap. 06
- **Entkopplung Core/UI:** Kap. 05
- **Explainability:** Kap. 08.4
- **Logging & Monitoring:** Kap. 08.7
- **Deployment (Edge):** Kap. 07

---

## Zusammenfassung

Performance ist dann gut, wenn sie **nicht auffällt**.

BitGridAI:
- entscheidet im festen Zeitrahmen,
- nutzt Ressourcen bewusst sparsam,
- und bleibt auch auf kleiner Hardware stabil und zuverlässig.

---
> **Nächster Schritt:**  
> Alle Qualitätsmerkmale sind nun vollständig beschrieben und durch Szenarien abgesichert.
>
> 👉 Zurück zur **[11 - Risiken & Technische Schulden](../../11_risks_and_technical_debt)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
