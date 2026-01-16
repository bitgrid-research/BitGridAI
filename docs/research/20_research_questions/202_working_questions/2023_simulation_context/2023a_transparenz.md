# 20.2.3.1 - SIM-WQ1 - Sichtbarkeit der Entscheidungslogik (Transparenz)

Ziel: Teilnehmende erkennen im Lab-Setup in unter 60 Sekunden, warum das System schaltet.

&nbsp;

## Nutzungskontext (Lab)

- Tischsimulation mit PV-Simulator, Haus-Reserve, Miner-Attrappe und Last-Schaltern.
- Relais-Klicks, LEDs und ein kleines Status-Display spiegeln die Regel-Engine (R1-R5).
- Beobachtungsdauer pro Person: 5-8 Minuten, davon 2 Minuten Hands-on ohne Erklärung.

&nbsp;

## Proto-Persona

**Persona:** Tessa Test, 29  
**Rolle:** Interessierte Besucherin, will Logik erleben, nicht konfigurieren  
**Nutzungstyp:** Kurzbesuch im Lab, 5-8 Minuten Hands-on  
**Technische Affinität:** tech-offen, aber kein HEMS-Fachwissen  
**Primärer Nutzungskontext:** Beobachtet Relais/LEDs, provoziert Schaltpunkte (Reserve, Prognose)  
**Mentales Modell:** Regeln müssen sichtbar/hörbar sein; Reserve ist eine Sperre, kein Fehler  
**Ziel der Persona:** Schnell verstehen, warum das System schaltet und ob es absichtsvoll ist  
**Relevante Einschränkungen:** Begrenzte Zeit/Aufmerksamkeit; interpretiert Zufallsgeräusche als Fehler, wenn Text fehlt

&nbsp;

## Proto-Problem-Statement

- Das Lab schaltet (Relais-Klick, LED-wechsel) ohne sofort sichtbare Begründung.
- Teilnehmende können Reserve, Prognose und Stabilisierung nicht auseinanderhalten.
- Folge: Sie halten die Automatik für willkürlich oder defekt.

&nbsp;

## Annahmen

| ID | Annahme |
|----|---------|
| SIM-ASSUM-TRAN-01 | Ein einziger Blick auf LED-Farben + Kurztext reicht, um den Grund der Aktion zu erkennen. |
| SIM-ASSUM-TRAN-02 | Akustische Signale (Klick/Buzzer) müssen mit einem Text-Overlay gekoppelt sein, sonst wirken sie zufällig. |
| SIM-ASSUM-TRAN-03 | Die Haus-Reserve (R2) wird erst verstanden, wenn ihr Schwellwert sichtbar und provozierbar ist. |
| SIM-ASSUM-TRAN-04 | Ein Countdown oder "nächster Check" reduziert Fehlinterpretation als Fehler. |

&nbsp;

## Kritische Annahme

- Multimodal gekoppelte Signale (LED + Kurztext + Countdown) reichen aus, um Schaltentscheidungen als absichtsvoll wahrzunehmen und nicht als Fehlfunktion.

&nbsp;

## Abgeleitete Forschungsfrage

**Wie müssen LED-Codierung, Relais-Sounds und Kurztexte kombiniert werden, damit Teilnehmende im Lab die regelbasierte Entscheidung (Start/Pause/Stop) als absichtsvoll und nachvollziehbar wahrnehmen?**

&nbsp;

## Teilfragen

| ID | Fokus | Teilfrage | Bezug |
|----|-------|-----------|-------|
| SIM-TRAN-01 | Multimodalität | Welche Kombination aus LED-Farbe + Kurztext wird am schnellsten verstanden? | ASSUM-01 |
| SIM-TRAN-02 | Reserve-Sichtbarkeit | Wie zeigen wir R2 so, dass ihr Veto nachvollziehbar wird? | ASSUM-03 |
| SIM-TRAN-03 | Timing | Reicht ein Countdown/"nächster Check", um Flapping als Stabilisierung zu erklären? | ASSUM-04 |
| SIM-TRAN-04 | Audio-Signal | Wann hilft ein Relais/Buzzer-Sound, wann stört er? | ASSUM-02 |

&nbsp;

## Erhebungsmethoden

| ID | Methode | Zweck |
|----|---------|-------|
| EXP-SIM-TRAN-01 | 60s Blind-Observation: Was glaubt die Person passiert? | Baseline-Verständnis |
| EXP-SIM-TRAN-02 | Think-aloud bei provozierten Schaltpunkten (Reserve-Kante, Prognose-Wechsel). | Mentales Modell |
| EXP-SIM-TRAN-03 | Mini-Interview: Begründung in eigenen Worten wiedergeben. | Recall + Klarheit |

&nbsp;

## UI-Prinzipien (abgeleitet aus Persona & WQ1)

- Warum + Wann immer gekoppelt: Kurzgrund + nächster Check/Timer in einer Zeile.
- Farb- und Text-Codierung deckungsgleich: Grün = Start, Gelb = Stabilisieren, Rot = Veto/Stop.
- Multimodal gekoppelt: Relais-Klick/Buzzer nur zusammen mit sichtbarem Kurztext.
- Schwelle sichtbar machen: Reserve/Veto als Linie oder Wert zeigen und provozierbar halten.
- Kein Blindflug: Countdown oder Uhrzeit immer eingeblendet, damit Flapping als Stabilisierung lesbar bleibt.

&nbsp;

## Beobachtungspunkte

- Wie schnell wird der Grund genannt (Sekunden bis richtige Erklärung)?
- Wird Reserve-Veto als Sicherheit oder als Fehler interpretiert?
- Welche Elemente werden zuerst angeschaut (LED, Display, Sound)?

&nbsp;

## Artefakte / UI

- Status-Display mit Zeile: "Grund: <Text> | Weiter in: <Zeit>".
- LED-Schema: Grün = Start, Gelb = stabilisieren, Rot = Veto/Stop.
- Kleines Overlay-Chart mit Schwelle und aktuellem Wert (nur auf Wunsch anzeigen).

&nbsp;

## Minimale UI-Elemente

| ID | Element |
|----|---------|
| UI-SIM-TRAN-01 | Status-Display: Grund + Countdown/nächster Check. |
| UI-SIM-TRAN-02 | LED-Set: Grün/Gelb/Rot synchron zum Text. |
| UI-SIM-TRAN-03 | Provozierbare Schwellenanzeige (Reserve-Linie/Wert). |

&nbsp;

## Messkriterien (einfach)

- < 60s bis zur korrekten Nennung des aktuellen Grundes.
- 80% der Teilnehmenden können Reserve-Veto in eigenen Worten erklären.
- Weniger als 1 falsche Fehlinterpretation pro Person nach 5 Minuten.

&nbsp;

## Zusammenfassung

Kurzer Grund + Countdown, synchronisierte LED-Codes und sichtbare Schwellen machen die Lab-Entscheidung als regelbasiert erkennbar; ein Overlay bleibt optional für tieferes Verständnis.

---

> **Nächster Schritt:** Als nächstes geht es um Eingriff und Override im Lab.
>
> 👉 Weiter zu **[20.2.3.2 - SIM-WQ2 - Eingriff und Override im Labor](./2023b_kontrolle.md)**
>
> 🔙 Zurück zu **[20.2.3 - SIM-CONTEXT - Simulation-Lab-Kontext](./README.md)**
>
> 🏠 Zurück zu **[20.2 - WQ - Zentrale Arbeitsfragen](../README.md)**
