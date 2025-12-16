# 10.2.1 - Transparenz & Erklärbarkeit (Explainability)

Keine Entscheidung ohne Warum.

BitGridAI trifft Entscheidungen, die reale Auswirkungen haben:  
Energieflüsse, Hardwarezustände, Kosten.  
Damit Nutzer dem System vertrauen können, müssen diese Entscheidungen **jederzeit nachvollziehbar, erklärbar und überprüfbar** sein.

Dieses Qualitätsszenario beschreibt, wie BitGridAI Transparenz sicherstellt – nicht als Zusatzfunktion, sondern als **architektonisches Grundprinzip**.

Grundsatz:
> **Was nicht erklärt werden kann, darf nicht automatisch entscheiden.**

(Platzhalter für ein Bild: Ein Pixel-Art-Hamster mit Lupe und Klemmbrett steht vor einem Entscheidungsdiagramm. Sprechblase: „Darum habe ich das so gemacht.“)

&nbsp;

## Qualitätsziel

**Jede automatische Entscheidung ist für den Nutzer verständlich erklärbar**,  
inklusive Auslöser, Regelbasis und relevanter Grenzwerte.

&nbsp;

## Kontext

- Regelbasierte Entscheidungen (R1–R5) im Block-Takt (Kap. 06)
- Entscheidungen werden als `DecisionEvent` persistiert
- Explainability erfolgt **on-device**, ohne Cloud-Abhängigkeit
- UI zeigt Zustand, Historie und Prognose an (Kap. 08.3)

&nbsp;

## Szenario E-1: Nutzer fragt „Warum läuft der Miner gerade?“

**Stimulus:**  
Der Nutzer stellt im UI eine Explain-Anfrage.

**Quelle:**  
Benutzeroberfläche / Explain-UI

**Betriebszustand:**  
Mining aktiv (halb- oder vollautomatischer Modus)

**Erwartete Systemreaktion:**
- Identifikation des aktuell wirksamen `DecisionEvent`
- Erzeugung einer Explain-Session mit:
  - angewendeter Regel (z.B. R1, R4)
  - auslösenden Messwerten
  - relevanten Schwellenwerten
- Ausgabe einer verständlichen, menschenlesbaren Erklärung

**Akzeptanzkriterien:**
- Erklärung innerhalb von **≤ 2 Sekunden**
- Bezug auf konkrete Messwerte und Regeln
- Keine generischen oder ausweichenden Antworten

&nbsp;

## Szenario E-2: Entscheidung wird automatisch geändert

**Stimulus:**  
System stoppt Mining aufgrund veränderter Bedingungen (z.B. sinkender PV-Überschuss).

**Quelle:**  
Rule Engine

**Betriebszustand:**  
Automatikbetrieb

**Erwartete Systemreaktion:**
- Neues `DecisionEvent` wird erzeugt
- Explain-Daten (Reason, Trigger, Parameter) werden persistiert
- UI aktualisiert Timeline und zeigt Ursache der Änderung

**Akzeptanzkriterien:**
- Jede Zustandsänderung ist erklärbar
- Historische Entscheidungen bleiben abrufbar
- Ursache ist eindeutig identifizierbar

&nbsp;

## Szenario E-3: Vorschau auf die nächste Entscheidung

**Stimulus:**  
Der Nutzer betrachtet die „Next-Block-Preview“ im UI.

**Quelle:**  
UI / Explain-Agent

**Betriebszustand:**  
Beliebig

**Erwartete Systemreaktion:**
- Simulation der nächsten Regelbewertung
- Anzeige der **erwarteten** Aktion inkl. Begründung
- Kennzeichnung als Prognose, nicht als Entscheidung

**Akzeptanzkriterien:**
- Klare Trennung zwischen Ist-Entscheidung und Vorschau
- Vorschau basiert auf aktuellen Daten und aktiver Konfiguration
- Keine verdeckten Automatismen

&nbsp;

## Messbare Qualitätsmerkmale

| Merkmal | Ziel |
|-------|------|
| Erklärungsabdeckung | 100 % aller DecisionEvents |
| Explain-Latenz | ≤ 2 s |
| Cloud-Abhängigkeit | 0 |
| Verweis auf Regel & Trigger | immer vorhanden |

&nbsp;

## Bezug zur Architektur

- **Explain-Agent & UI:** Kap. 08.3 / 08.4  
- **DecisionEvent-Modell:** Kap. 08.1  
- **Replay & Audit:** Kap. 08.8  
- **ADRs:** Explainability on-device (Kap. 09)

&nbsp;

## Zusammenfassung

Explainability ist kein UI-Gimmick, sondern **Voraussetzung für Autonomie**.

BitGridAI:
- trifft nur erklärbare Entscheidungen,
- macht Gründe sichtbar statt sie zu verstecken,
- und ermöglicht Vertrauen durch Transparenz.

---

> **Nächster Schritt:**  
> Transparenz schafft Vertrauen – echte Kontrolle entsteht jedoch erst,
> wenn der Nutzer entscheiden darf, **wer die Kontrolle hat**.
>
> 👉 Weiter zu **[10.2.2 - Autonomie & Privacy](./1022_autonomy_and_privacy.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
