# 10.2.2 - Autonomie & Privacy

Kontrolle bleibt beim Menschen.

BitGridAI ist kein autonomes System im luftleeren Raum.  
Es handelt im Auftrag des Nutzers – und nur innerhalb klar definierter Grenzen.  
Autonomie dient dem **Komfort**, nicht der Entmündigung. Privacy ist **Grundannahme**, kein Feature.

Dieses Qualitätsszenario beschreibt, wie BitGridAI Entscheidungshoheit verteilt,  
wie Nutzereingriffe priorisiert werden und wie Datenhoheit konsequent gewahrt bleibt.

![Mindmap des Qualitätsbaumes](../../../media/architecture/10_quality_scenarios/bithamster_10.png)

&nbsp;

## Qualitätsziel

**Maximale Selbstbestimmung bei voller Datensouveränität**,  
ohne Sicherheitsrisiken oder versteckte Abhängigkeiten.

Der Nutzer entscheidet:
- *wie viel* Autonomie das System haben darf,
- *wann* eingegriffen wird,
- *welche Daten* das System verlassen dürfen (oder nicht).

&nbsp;

## Kontext

- Autonomie-Stufen 0–3 sind definiert (Kap. 06.7)
- Overrides sind zeitlich begrenzt (Kap. 06.6)
- Safety (R3) ist niemals übersteuerbar
- System läuft local-first ohne Cloud-Zwang (Kap. 07)
- Exporte und Research sind Opt-in (Kap. 06.11)

&nbsp;

## Szenario A-1: Nutzer wählt Autonomie-Stufe

**Stimulus:**  
Der Nutzer ändert die Autonomie-Stufe im UI.

**Quelle:**  
UI / Settings

**Umgebung:**  
Normalbetrieb

**Erwartete Systemreaktion:**
- Neue Autonomie-Stufe wird im `EnergyState` gesetzt
- Regel-Engine berücksichtigt die neue Entscheidungshoheit ab dem nächsten Block
- Aktiver Modus ist im UI jederzeit sichtbar

**Akzeptanzkriterien:**
- Wechsel ohne Neustart möglich
- Kein verdeckter Systemmodus
- Aktive Stufe ist eindeutig erkennbar

&nbsp;

## Szenario A-2: Manueller Override durch den Nutzer

**Stimulus:**  
Der Nutzer erzwingt START oder STOP.

**Quelle:**  
UI / API (`/override`)

**Umgebung:**  
Assistiert, halb- oder vollautomatisch

**Erwartete Systemreaktion:**
- Override hat Vorrang vor Optimierungsregeln (R1, R4, R5)
- Override ist **zeitlich begrenzt (TTL)**
- Safety-Regel R3 bleibt aktiv

**Akzeptanzkriterien:**
- Override endet automatisch
- Override ist im UI sichtbar
- Keine dauerhafte Deaktivierung der Automatik möglich

&nbsp;

## Szenario A-3: Schutz der Privatsphäre (Default-Verhalten)

**Stimulus:**  
System läuft im Normalbetrieb.

**Quelle:**  
Systemstart / Laufzeit

**Umgebung:**  
Local Edge System

**Erwartete Systemreaktion:**
- Keine Daten verlassen das lokale Netz
- Keine Telemetrie, kein Cloud-Backhaul
- Alle Modelle und Erklärungen laufen on-device

**Akzeptanzkriterien:**
- 0 ausgehende Datenverbindungen ohne Opt-in
- Netzwerkverkehr ist auditierbar
- System bleibt funktionsfähig ohne Internet

&nbsp;

## Szenario A-4: Expliziter Research-Export (Opt-in)

**Stimulus:**  
Der Nutzer triggert einen Export.

**Quelle:**  
UI / API (`/research/export`)

**Umgebung:**  
Manueller Eingriff

**Erwartete Systemreaktion:**
- Prüfung des Research-Opt-ins
- Export nur der explizit gewählten Daten
- Erstellung von Manifest + Hash
- Kein automatischer Upload

**Akzeptanzkriterien:**
- Export ohne Opt-in nicht möglich
- Export ist nachvollziehbar und reproduzierbar
- Replay erfolgt read-only

&nbsp;

## Messbare Qualitätsmerkmale

| Merkmal | Ziel |
|------|------|
| Übersteuerbarkeit der Autonomie | 100 % nutzergetrieben |
| Cloud-Abhängigkeit | 0 |
| Override-TTL | immer aktiv |
| Opt-in-Abdeckung bei Exporten | 100 % |
| Privacy-Leaks | 0 |

&nbsp;

## Bezug zur Architektur

- **Autonomie-Stufen:** Kap. 06.7
- **Manual Override:** Kap. 06.6
- **Deployment:** Kap. 07
- **Export & Replay:** Kap. 06.11
- **Security & Access Control:** Kap. 08.7

&nbsp;

## Zusammenfassung

BitGridAI ist **autonom, aber nicht eigenmächtig**.

- Der Nutzer behält die Kontrolle.
- Daten bleiben lokal.
- Autonomie ist ein einstellbarer Komfortmodus – kein Kontrollverlust.

---

> **Nächster Schritt:**  
> Autonomie darf nicht zu Instabilität führen.
>
> 👉 Weiter zu **[10.2.3 - Vorhersagbarkeit & Stabilität](./1023_predictability_and_stability.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
