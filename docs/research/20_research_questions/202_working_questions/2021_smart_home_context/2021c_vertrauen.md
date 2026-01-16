# 20.2.1.3 - SH-WQ3 - Vertrauen und Sicherheit (Haus-Reserve)

Ziel: Nutzer sehen in einem Blick, dass die Haus-Reserve garantiert bleibt und Mining die Grundversorgung nicht gefährdet.

&nbsp;

## Nutzungskontext (Smart Home)

- Morgen-/Abend-Check im Dashboard: Reicht Energie für Haushalt heute/nacht?
- Geringe Bereitschaft zu rechnen; erwartet wird eine Ja/Nein-Aussage und klarer Puffer.
- Sensibel für Risiko: Reserve darf nicht durch Automatik angekratzt werden.

&nbsp;

## Proto-Persona

**Persona:** Clara Reserve, 41  
**Rolle:** Haushaltsverantwortliche, Priorität Versorgungssicherheit  
**Nutzungstyp:** Kurzer Morgen-/Abend-Check, seltene Einstellungen  
**Technische Affinität:** gering bis mittel, keine Lust auf Prozentrechnen  
**Primärer Nutzungskontext:** Blick auf Reserve vor/nach Tageslauf; will Ja/Nein-Aussage  
**Mentales Modell:** Reserve ist unantastbar; Mining darf nur oberhalb des Puffers laufen  
**Ziel der Persona:** In einem Blick sehen, dass Haus gesichert ist und Automatik vertrauenswürdig bleibt  
**Relevante Einschränkungen:** Keine Zeit für Diagramme; reagiert sensibel auf Risiko; will einfache Zusage

&nbsp;

## Proto-Problem-Statement

- Haus-Reserve unsichtbar oder technisch; Nutzer sieht nicht, was gesichert ist.
- Mining-Entscheidungen werden als Risiko für Haushalt interpretiert.
- Folge: Mining wird dauerhaft gestoppt oder Automatik deaktiviert.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SH-ASSUM-TRUST-01 | Eine klar markierte Haus-Reserve ist der zentrale Vertrauensanker. |
| SH-ASSUM-TRUST-02 | "Haus gesichert: Ja/Nein" ist schneller erfassbar als Prozentwerte oder Diagramme. |
| SH-ASSUM-TRUST-03 | Nutzer wollen Puffer einstellen können, nutzen aber selten Feinjustierung. |
| SH-ASSUM-TRUST-04 | Einfache Visualisierung (Balken/Batterie) reduziert Unsicherheit schneller als Charts. |
| SH-ASSUM-TRUST-05 | Transparente Zusage "Reserve wird nicht unterschritten" hält Automatik aktiv. |

&nbsp;

## Kritische Annahme

- Eine klare Aussage "Haus gesichert: Ja/Nein" mit sichtbar gesperrter Reserve reicht aus, um Vertrauen zu halten und Mining nicht vorsorglich zu stoppen.

&nbsp;

## Abgeleitete Forschungsfrage

**Wie müssen Haus-Reserve und Sicherheitszusagen im Smart-Home-UI dargestellt werden (Text, Visualisierung, Zusage), damit Nutzer Vertrauen in die Automatik behalten und Mining nicht vorsorglich stoppen?**

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|-------|-----------|-------|
| SH-TRUST-01 | Kernbotschaft | Reicht "Haus gesichert: Ja/Nein" als Primaraussage? | ASSUM-02 |
| SH-TRUST-02 | Visualisierung | Welche Darstellung (Balken/Batterie/Text) senkt Unsicherheit am stärksten? | ASSUM-04 |
| SH-TRUST-03 | Einstellbarkeit | Welche minimale Puffer-Einstellung wird genutzt/verstanden? | ASSUM-03 |
| SH-TRUST-04 | Regeltransparenz | Wie kommunizieren wir, dass Reserve nie unterschritten wird? | ASSUM-05 |

&nbsp;

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|---------|-------|
| EXP-SH-TRUST-01 | A/B: Ja/Nein vs. Prozent/Balken. | Botschaftsklarheit |
| EXP-SH-TRUST-02 | Puffer-Set-Test: Wird Standard-Puffer akzeptiert? | Einstellbarkeit |
| EXP-SH-TRUST-03 | Vertrauenscheck nach Mining-Start. | Vertrauen/Sicherheit |

&nbsp;

## UI-Prinzipien (abgeleitet aus Persona & WQ3)

- Sicherheitszusage vor Detail: Primar "Haus gesichert: Ja/Nein" + kurzer Grund.
- Puffer sichtbar und gesperrt: Markierter Reserve-Bereich (Balken/Batterie) mit Wert.
- Regelklarheit: Satz "Reserve wird nicht unterschritten"; Mining-Entscheidungen referenzieren R2.
- Wenig Zahlen: Prozent nur optional; Fokus auf Klartext und Farbcodierung.
- Einstellbar, aber simpel: Standard-Puffer, Schieberegler optional, keine komplizierten Dialoge.

&nbsp;

## Beobachtungspunkte

- Wird "Haus gesichert" in < 5 Sekunden erkannt?
- Wird die Reserve als unantastbar verstanden?
- Führt eine klare Zusage zu weniger manuellen Stopps?

&nbsp;

## Artefakte / UI

- Reserve-Karte: Balken/Batterie mit Bereich "Haus-Reserve" vs. "frei für Miner".
- Text: "Haus gesichert: Ja/Nein" + "Reserve = X kWh / X%" (optional).
- Hinweis: "Mining stoppt, falls Reserve unterschritten würde".
- Button: "Reserve ändern" (einfacher Slider, Standardwert markiert).

&nbsp;

## Minimale UI-Elemente

| ID | Element |
|----|---------|
| UI-SH-TRUST-01 | Reserve-Karte mit Balken/Batterie, Bereich "Haus-Reserve" klar markiert. |
| UI-SH-TRUST-02 | Textzeile "Haus gesichert: Ja/Nein" + Reserve-Wert (optional). |
| UI-SH-TRUST-03 | Hinweis "Reserve wird nicht unterschritten; Mining stoppt falls nötig". |
| UI-SH-TRUST-04 | Einfacher Slider/Presets zur Puffer-Anpassung. |

&nbsp;

## Messkriterien (einfach)

- 80% können Reserve-Bedeutung in eigenen Worten erklären.
- < 1 manueller Stopp pro Woche wegen Sicherheitszweifel.
- Standard-Puffer wird von > 70% unverändert gelassen.

&nbsp;

## Zusammenfassung

Eine Ja/Nein-Sicherheitsaussage, ein klar markierter Reserve-Bereich und eine einfache Anpassung halten das Vertrauen hoch und verhindern vorsorgliche Stopps der Automatik.

---

> **Nächster Schritt:** Danach geht es weiter mit dem Automotive-Kontext.
>
> 👉 Weiter zu **[20.2.2 - AUTO-CONTEXT - Automotive-Kontext](../2022_automotive_context/README.md)**
>
> 🔙 Zurück zu **[20.2.1 - SH-CONTEXT - Smart-Home-Kontext](./README.md)**
>
> 🏠 Zurück zu **[20.2 - WQ - Zentrale Arbeitsfragen](../README.md)**
