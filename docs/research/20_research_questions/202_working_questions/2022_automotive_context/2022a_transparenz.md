# 20.2.2.1 – AUTO-WQ1 – Transparenz der Ladeentscheidung

## Ziel
Fahrende erkennen in unter **2 Sekunden**,  
dass es sich um eine **absichtsvolle, regelbasierte Entscheidung** des Systems handelt  
– und nicht um einen Fehler oder Verbindungsabbruch.

---

## Relevante Persona (HCI-Modell)

**Persona:** Fiona Fokus  
**Rolle:** Fahrerin im Smart-Home- und HEMS-Kontext  
**Nutzungstyp:** Routine-Nutzung  
**Technische Affinität:** gering bis mittel  
**Primärer Nutzungskontext:** Ankunft zu Hause, geringe Aufmerksamkeit  
**Mentales Modell:**  
- Das System regelt Ladeentscheidungen autonom im Hintergrund.  
- Das Fahrzeug-UI dient als kurzer Bestätigungsblick, nicht als Analysewerkzeug.  

**Ziel der Persona:**  
Die Ladeentscheidung sofort einordnen können, um das Thema „Auto“ mental abzuschließen.

**Relevante Einschränkungen:**  
- Sehr begrenzte kognitive Kapazität im Nutzungsmoment  
- Keine Bereitschaft zur Interpretation technischer Begriffe  
- Fahrzeug-UI ist der primäre (und oft einzige) Informationskanal  

---

## Proto-Problem-Statement (WQ1 – Transparenz)

- Statusanzeigen wie „Wartet“ oder „Pausiert“ sind nicht selbsterklärend.  
- Ohne expliziten Grund wird der Zustand als **Fehler** statt als **bewusste Systementscheidung** interpretiert.  
- Fehlende Prognose („Wann geht es weiter?“) erzeugt mentale Restunsicherheit.  
- Technische Begriffe oder mehrzeilige Texte überfordern im Ankunftskontext.  
- Das mentale Modell bleibt: *„Das System macht irgendetwas im Hintergrund, ich weiß nicht was.“*

**Zentrale Einsicht:**  
Fehlende Erklärung wird kognitiv als Störung interpretiert – nicht als Optimierung.

---

## Nutzungskontext (WQ1-relevant)

- Nutzung erfolgt beiläufig (Ankommen, Aussteigen, Einstecken).  
- Blickdauer auf das Display: maximal 1–2 Sekunden.  
- Kein Wunsch nach technischer Tiefe oder Interaktion.  
- Information muss ohne Nachdenken und ohne Kontextwissen verständlich sein.

---

## Proto-Journey (Kurzfassung)

1. Fiona kommt nach Hause und parkt.  
2. Sie steckt das Ladekabel an.  
3. Das System verzögert oder pausiert den Ladevorgang.  
4. Das Fahrzeug-UI zeigt einen Status.  
5. Fiona wirft einen kurzen Blick und will die Situation einordnen.

**Ziel der Journey:**  
Den Ladezustand sofort als **absichtsvoll und korrekt** verstehen und den mentalen Übergang in den Feierabend ermöglichen.

---

## Zentrale Annahmen (WQ1 – Transparenz)

| ID | Annahme |
|----|--------|
| AUTO-ASSUM-TRAN-01 | Fiona hat maximal 2 Sekunden Aufmerksamkeit für Ladeinformationen. |
| AUTO-ASSUM-TRAN-02 | Ein klar formulierter Satz mit **Grund + Startzeit** reicht für Akzeptanz. |
| AUTO-ASSUM-TRAN-03 | Ohne Erklärung wird „Nicht laden“ als Systemfehler interpretiert. |
| AUTO-ASSUM-TRAN-04 | Icon + sehr kurzer Text werden schneller verstanden als Text allein. |
| AUTO-ASSUM-TRAN-05 | Eine optionale Voice-Ansage kann visuelle Information bestätigen, nicht ersetzen. |
| AUTO-ASSUM-TRAN-06 | Alltagssprache reduziert kognitive Last gegenüber technischen Begriffen. |

---

## Abgeleitete Forschungsfrage (WQ1)

**Wie kann das Fahrzeug-UI Gründe und Startzeit so kurz und alltagssprachlich kommunizieren (Text, Icon, optional Voice),  
dass Routine-Fahrende die Ladeentscheidung in unter 2 Sekunden  
als absichtsvolle, regelbasierte Systementscheidung verstehen und nicht als Fehler interpretieren?**

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
| EXP-AUTO-TRAN-03 | Kurzinterview | Interpretation und mentale Sicherheit |

---

## UI-Prinzipien (abgeleitet aus Persona & WQ1)

- **Warum + Wann**, nicht nur Status  
- Maximal **ein Satz**  
- Alltagssprache statt Systemjargon  
- Struktur: **Warum → Was passiert → Wann**  
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

Die Persona dient hier der **Operationalisierung von Aufmerksamkeit, Nutzungskontext und mentalem Modell**.  
Transparenz bedeutet nicht Detailtiefe, sondern die sofortige Wahrnehmung von **Absicht statt Fehler**.

Ein erklärender UI-Satz ersetzt technische Systemzustände durch eine verständliche Alltagsübersetzung der Regelentscheidung.

---

> **Nächster Schritt:** Als Nächstes geht es um Kontrolle im Auto.
>
> 👉 Weiter zu **[20.2.2.2 - AUTO-WQ2 - Kontrolle im Auto](./2022b_kontrolle.md)**
>
> 🔙 Zurück zu **[20.2.2 - AUTO-CONTEXT - Automotive-Kontext](./README.md)**
