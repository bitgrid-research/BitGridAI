# 8.1 - Fachliche Modelle (Domain Models)

Eine gemeinsame Sprache.

BitGridAI ist ein entscheidendes System.  
Damit Entscheidungen nachvollziehbar, testbar und reproduzierbar bleiben, benötigt das System eine **klar definierte fachliche Sprache**, die von allen Bausteinen identisch verstanden wird.

Dieses Kapitel beschreibt die **zentralen Domänenkonzepte** von BitGridAI.  
Sie bilden das gemeinsame Vokabular für Core, Adapter, Regelwerk, UI, Logging und Replays.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster steht vor einer Tafel mit klar beschrifteten Begriffen wie „EnergyState“, „Rule“, „Decision“. Er zeigt mit einem Zeigestock darauf.)*  
![Hamster erklärt die Domänensprache](../../media/bithamster_08.png)

&nbsp;

## Ziel des Domänenmodells

Das Domänenmodell verfolgt drei übergeordnete Ziele:

- **Eindeutigkeit:**  
  Jeder zentrale Begriff hat genau eine fachliche Bedeutung.

- **Konsistenz:**  
  Dieselben Konzepte werden in allen Komponenten identisch verwendet.

- **Entkopplung:**  
  Fachliche Begriffe sind unabhängig von Protokollen, UI, Persistenz oder Deployment.

Das Domänenmodell ist damit **keine API-Spezifikation** und **kein Datenbankschema**, sondern die **fachliche Grundlage** aller technischen Entscheidungen.

&nbsp;

## Zentrale Domänenkonzepte

### Nutzer (User)

Ein *Nutzer* ist die Instanz, die:
- Präferenzen festlegt,
- Autonomie-Stufen wählt,
- manuelle Overrides auslöst.

Der Nutzer ist nicht zwingend eine konkrete Person, sondern die **Quelle intentionaler Entscheidungen**.

**Grundsatz:**  
Nutzerentscheidungen können Optimierungsregeln übersteuern, jedoch niemals Sicherheitsregeln (R3).

&nbsp;

### Energiequelle (Energy Source)

Eine *Energiequelle* beschreibt die Herkunft verfügbarer Energie, z.B.:
- Photovoltaik
- Netz
- Speicher (Batterie)

Energiequellen liefern Messwerte, treffen jedoch **keine Entscheidungen**.

&nbsp;

### Verbraucher / Flexible Last (Consumer)

Ein *Verbraucher* ist eine steuerbare Last, z.B.:
- Miner
- Heizstab
- andere flexible Verbraucher

Verbraucher führen Entscheidungen aus (Start, Stop, Safe), treffen sie aber nicht selbst.

&nbsp;

### Messwert (Measurement)

Ein *Messwert* beschreibt einen beobachteten Zustand zu einem Zeitpunkt *t*, z.B.:
- Leistung
- Temperatur
- Preis
- Ladezustand

**Wichtige Eigenschaften:**
- immer zeitlich gebunden,
- kann fehlen oder ungültig sein,
- wird niemals implizit geschätzt.

Fehlende Messwerte sind ein **expliziter Zustand** und beeinflussen Entscheidungen (siehe Kap. 8.6).

&nbsp;

### Zustand (EnergyState)

Der `EnergyState` ist die **Single Source of Truth** zur Laufzeit.

Er umfasst:
- aktuelle Messwerte,
- abgeleitete Kontexte (z.B. Forecasts),
- Betriebsmodi (Autonomie-Stufe, Overrides),
- Safety- und Degradationszustände.

**Prinzip:**  
Der EnergyState ist logisch **unveränderlich**.  
Ein Zustand beschreibt immer genau einen Zeitpunkt und wird niemals nachträglich modifiziert.

Dieses Prinzip ist Grundlage für:
- deterministisches Verhalten,
- Replay-Fähigkeit,
- nachvollziehbare Entscheidungen.

&nbsp;

### Regel (Rule)

Eine *Regel* beschreibt **warum** eine Entscheidung getroffen wird.

Beispiele:
- R1: Profitabilität
- R2: Autarkie
- R3: Sicherheit
- R4: Forecast
- R5: Stabilität

Regeln:
- bewerten den aktuellen EnergyState,
- erzeugen Entscheidungsbeiträge,
- können priorisiert oder überstimmt werden – mit Ausnahme von R3 (Safety).

&nbsp;

### Entscheidung (Decision)

Eine *Entscheidung* ist das Ergebnis der Regelbewertung.

Sie besteht aus:
- einer Aktion (z.B. Start, Stop, Hold),
- einer oder mehreren Begründungen,
- dem relevanten Kontext.

Entscheidungen sind:
- erklärbar,
- logbar,
- reproduzierbar.

&nbsp;

### Explain Session

Eine *Explain Session* verbindet technische Entscheidungen mit menschenlesbaren Erklärungen.

Sie referenziert:
- den relevanten EnergyState,
- die zugehörige Entscheidung,
- eine verständliche Begründung für den Nutzer.

Explain Sessions sind stets **read-only** und verändern niemals den Systemzustand.

&nbsp;

## Modellgrenzen & Abgrenzungen

Bewusst **nicht Teil** des Domänenmodells sind:

- Protokolle (MQTT, REST)
- UI-spezifische Konzepte
- Persistenzformate
- Hardware- oder Hersteller-IDs

Diese Aspekte binden sich an das Domänenmodell an, definieren es aber nicht.

&nbsp;

## Auswirkungen auf das Gesamtsystem

Das Domänenmodell wirkt systemweit:

- **Core:**  
  Regeln operieren ausschließlich auf Domänenkonzepten.

- **Adapter:**  
  Übersetzen externe Signale in Domänenobjekte.

- **UI:**  
  Visualisiert Zustände und Entscheidungen in Domänensprache.

- **Logging & Replays:**  
  Nutzen identische Begriffe für Nachvollziehbarkeit und Analyse.

&nbsp;

## Zusammenfassung

Die fachlichen Modelle bilden das **semantische Fundament** von BitGridAI.

Sie stellen sicher, dass:
- alle Komponenten dieselbe Sprache sprechen,
- Entscheidungen erklärbar bleiben,
- Verhalten reproduzierbar und überprüfbar ist.

Ohne ein klares Domänenmodell gäbe es Optimierung – aber kein Verständnis.

---

> **Nächster Schritt:** Sicherheit ist die Voraussetzung jeder Entscheidung.  
> Im nächsten Abschnitt betrachten wir das **Sicherheits- & Vertrauenskonzept**.
>
> 👉 Weiter zu **[8.2 - Sicherheits- & Vertrauenskonzept](./082_security_and_trust.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
