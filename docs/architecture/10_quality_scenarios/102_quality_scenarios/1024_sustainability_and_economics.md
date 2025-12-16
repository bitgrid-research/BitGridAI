# 10.2.4 - Nachhaltigkeit & Wirtschaftlichkeit

Energie sinnvoll nutzen.

BitGridAI steuert flexible Lasten nicht zum Selbstzweck.  
Jede Aktivität verbraucht Energie, erzeugt Kosten oder schafft Wert.  
Dieses Qualitätsszenario beschreibt, wie BitGridAI **ökologisch sinnvoll und wirtschaftlich rational** handelt – transparent, nachvollziehbar und ohne versteckte Externalitäten.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster sitzt an einer Waage. Auf der einen Seite Sonne, Batterie und Wärme; auf der anderen Seite Münzen und ein Blitzsymbol. Die Waage ist im Gleichgewicht.)*

---

## Qualitätsziel

**Maximierung des Gesamtnutzens bei minimaler Belastung von Netz, Umwelt und Hardware.**

Das System soll:
- vorhandenen Überschuss bevorzugt nutzen,
- teuren oder schädlichen Energiebezug vermeiden,
- Entscheidungen wirtschaftlich begründen können.

---

## Kontext

- BitGridAI läuft local-first ohne Cloud (Kap. 07)
- Entscheidungen basieren auf deterministischen Regeln (R1–R5)
- Strompreise und Wetterprognosen stehen lokal zur Verfügung (R4)
- Nutzer kann Prioritäten setzen (Profil, Policies)

---

## Szenario E-1: PV-Überschuss vorhanden

**Stimulus:**  
PV-Erzeugung übersteigt Hausverbrauch und Mindest-SoC ist erreicht.

**Quelle:**  
EnergyState / PV-Adapter

**Umgebung:**  
Normal- oder Vollautomatikbetrieb

**Erwartete Systemreaktion:**
- Mining oder flexible Last wird gestartet (R1)
- Kein Netzbezug
- Entscheidung wird als „Überschussnutzung“ erklärt

**Akzeptanzkriterien:**
- Netzbezug bleibt bei 0 kW
- Entscheidung ist nachvollziehbar begründet
- Akku-Grenzen werden eingehalten

---

## Szenario E-2: Niedriger Strompreis ohne PV

**Stimulus:**  
Strompreis fällt unter konfigurierten Schwellenwert.

**Quelle:**  
Preis-Forecast (R4)

**Umgebung:**  
Profit-orientiertes Profil

**Erwartete Systemreaktion:**
- Mining kann gestartet werden, **wenn** Autarkie-Regeln nicht verletzt werden
- Entscheidung ist explizit als Opportunitätsentscheidung markiert
- UI zeigt Preisbezug und Kostenabschätzung

**Akzeptanzkriterien:**
- Entscheidung ist optional und profilabhängig
- Kosten/Nutzen-Verhältnis ist sichtbar
- Keine Verletzung von R2 (Autarkie)

---

## Szenario E-3: Konkurrenz um Energie (Haus vs. Miner)

**Stimulus:**  
Hauslast steigt, Akku-SoC nähert sich Mindestgrenze.

**Quelle:**  
EnergyState

**Umgebung:**  
Laufender Mining-Betrieb

**Erwartete Systemreaktion:**
- Mining-Leistung wird reduziert oder gestoppt
- Hausversorgung hat Vorrang (R2 > R1)
- Entscheidung wird als Schutz der Autarkie erklärt

**Akzeptanzkriterien:**
- Kein kritischer SoC-Unterschritt
- Keine Netzlastspitzen
- Klare Priorisierung im Explain-Event

---

## Szenario E-4: Nutzer fragt „Lohnt sich das?“

**Stimulus:**  
Nutzer öffnet Explain- oder KPI-Ansicht.

**Quelle:**  
UI

**Umgebung:**  
Beliebiger Modus

**Erwartete Systemreaktion:**
- Anzeige von Ertrag, Kosten und Opportunitätskosten
- Erklärung der aktuellen Strategie (z.B. eco vs. profit)
- Darstellung alternativer Optionen (Preview)

**Akzeptanzkriterien:**
- Wirtschaftliche Kennzahlen sind verständlich
- Entscheidungen sind nicht „magisch“
- Nutzer kann Strategie bewusst anpassen

---

## Messbare Qualitätsmerkmale

| Merkmal | Ziel |
|------|------|
| Netzbezug bei PV-Überschuss | ≈ 0 |
| Autarkie-Verletzungen | 0 |
| Wirtschaftliche Transparenz | 100 % |
| Erklärte Entscheidungen | 100 % |
| Nutzer-Strategie-Kohärenz | hoch |

---

## Bezug zur Architektur

- **Regel R1 (Profit):** Kap. 06.1
- **Regel R2 (Autarkie):** Kap. 06.2
- **Regel R4 (Forecast):** Kap. 06.4 / 06.12
- **Explainability:** Kap. 08.4
- **Profile & Policies:** Kap. 08.5

---

## Zusammenfassung

Nachhaltigkeit ist kein Nebenprodukt, sondern **eine bewusste Entscheidung**.

BitGridAI:
- nutzt Energie dann, wenn sie sinnvoll verfügbar ist,
- vermeidet Kosten und Risiken,
- und macht wirtschaftliche Abwägungen transparent und nachvollziehbar.

---

> **Nächster Schritt:**  
> Wirtschaftlichkeit braucht eine solide technische Basis – besonders in kritischen Situationen.
>
> 👉 Weiter zu **[10.2.5 Safety – Schutz von Hardware & Infrastruktur](../1025_safety,md)** docs/architecture/10_quality_scenarios/102_quality_scenarios/1025_safety,md
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
