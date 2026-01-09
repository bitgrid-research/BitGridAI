# 20.2.2.1 – AUTO-WQ1 – Transparenz der Ladeentscheidung

## Ziel
Fahrende verstehen innerhalb von **2 Sekunden**, warum das Fahrzeug lädt oder nicht lädt.

---

## Relevante Persona (HCI-Modell)

**Persona:** Fiona Fokus  
**Rolle:** Fahrerin im Smart-Home- und HEMS-Kontext  
**Nutzungstyp:** Routine-Nutzung  
**Technische Affinität:** gering bis mittel  
**Primärer Nutzungskontext:** Ankunft zu Hause, geringe Aufmerksamkeit  
**Mentales Modell:**  
- Das System regelt Ladeentscheidungen autonom im Hintergrund  
- Statusanzeigen dienen als kurze Bestätigung, nicht als Analysewerkzeug

**Ziel der Persona:**  
Die Ladeentscheidung kurz einordnen können, ohne weitere Interaktion oder Nachdenken.

**Relevante Einschränkungen:**  
- Sehr begrenzte kognitive Kapazität im Nutzungsmoment  
- Keine Bereitschaft zur Interpretation technischer Begriffe  
- Fahrzeug-UI ist der primäre (und oft einzige) Informationskanal

---

## Proto-Problem-Statement (aus Persona-Sicht)

- Das Fahrzeug zeigt Ladezustände wie „Nicht laden“ oder „Wartet“, ohne Begründung.
- Fiona kann nicht erkennen, ob es sich um eine bewusste Entscheidung oder einen Fehler handelt.
- Fehlende Erklärung erzeugt Unsicherheit und mentale Nacharbeit.
- Das System wird als intransparent wahrgenommen.

---

## Nutzungskontext (WQ1-relevant)

- Nutzung erfolgt beiläufig (Abstellen, Einstecken, kurzer Blick).
- Blickdauer auf das Display beträgt maximal wenige Sekunden.
- Es besteht kein Wunsch nach technischer Detailtiefe.
- Informationen müssen ohne aktive Interaktion verständlich sein.

---

## Proto-Journey (Kurzfassung)

1. Fiona stellt das Fahrzeug ab und steckt es an.  
2. Das System entscheidet, den Ladevorgang zu verzögern oder zu pausieren.  
3. Das Fahrzeug-UI zeigt einen Lade-Status.  
4. Fiona versucht, die Situation kurz einzuordnen.  
5. Ohne Erklärung bleibt Unsicherheit bestehen.

**Ziel der Journey:**  
Den Ladezustand **sofort verstehen** und den mentalen Übergang in den Feierabend ermöglichen.

---

## Zentrale Annahmen (WQ1 – Transparenz)

| ID | Annahme |
|----|--------|
| AUTO-ASSUM-TRAN-01 | Fiona hat maximal 2 Sekunden Aufmerksamkeit für Ladeinformationen. |
| AUTO-ASSUM-TRAN-02 | Ein klar formulierter Grund plus eine Startzeit reichen aus, um die Entscheidung zu akzeptieren. |
| AUTO-ASSUM-TRAN-03 | Ohne Erklärung interpretiert Fiona „Nicht laden“ als Fehler. |
| AUTO-ASSUM-TRAN-04 | Icons in Kombination mit sehr kurzem Text werden schneller verstanden als Text allein. |
| AUTO-ASSUM-TRAN-05 | Eine optionale Voice-Bestätigung kann visuelle Informationen unterstützen, ohne zusätzliche Interaktion zu erfordern. |

---

## Abgeleitete Forschungsfrage

**Wie kann das Fahrzeug-UI Ladeentscheidungen für eine Routine-Nutzerin mit geringer Aufmerksamkeit so erklären (Text, Icon, optional Voice),  
dass sie die Entscheidung in unter 2 Sekunden versteht und nicht als Fehler interpretiert?**

---

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|------|----------|------|
| AUTO-TRAN-01 | Aufmerksamkeit | Welche Textlänge ist innerhalb von 2 Sekunden erfassbar? | ASSUM-01 |
| AUTO-TRAN-02 | Informationsgehalt | Reichen Grund + Startzeit für Akzeptanz aus? | ASSUM-02, 03 |
| AUTO-TRAN-03 | Darstellung | Was ist schneller verständlich: Icon + Text oder nur Text? | ASSUM-04 |
| AUTO-TRAN-04 | Modalität | Wann unterstützt eine kurze Voice-Ansage das Verständnis, ohne zu stören? | ASSUM-05 |

---

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|--------|------|
| EXP-AUTO-TRAN-01 | 2-Sekunden-Blicktest | Erfassbarkeit prüfen |
| EXP-AUTO-TRAN-02 | A/B-Vergleich | Text vs. Icon + Text |
| EXP-AUTO-TRAN-03 | Kurzinterview | Interpretation und Sicherheit |

---

## UI-Prinzipien (abgeleitet aus Persona & WQ1)

- **Warum + Wann**, nicht nur Status
- Maximal **ein Satz**
- Keine Fachbegriffe
- Sofort visuell erfassbar
- Keine zusätzliche Interaktion erforderlich

---

## Minimale UI-Elemente

| ID | Element |
|----|--------|
| UI-AUTO-TRAN-01 | Status-Icon (z. B. Stecker + Uhr) |
| UI-AUTO-TRAN-02 | Eine Zeile mit Ladegrund |
| UI-AUTO-TRAN-03 | Eine Zeile mit prognostizierter Startzeit |
| UI-AUTO-TRAN-04 | Optional: ein kurzer Voice-Satz |

---

## Zusammenfassung

Die Persona dient hier nicht der Illustration, sondern der **Operationalisierung von Aufmerksamkeit, Nutzungskontext und mentalem Modell**.  
Transparenz wird dadurch mess- und gestaltbar.

---
---

> **Nächster Schritt:** Als Nächstes geht es um Kontrolle im Auto.
>
> 👉 Weiter zu **[20.2.2.2 - AUTO-WQ2 - Kontrolle im Auto](./2022b_kontrolle.md)**
>
> 🔙 Zurück zu **[20.2.2 - AUTO-CONTEXT - Automotive-Kontext](./README.md)**
