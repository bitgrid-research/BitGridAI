# 24.2 – Ableitung von Regeln zu erklärbaren Aussagen

Dieses Unterkapitel beschreibt, **wie Regel- und Systemzustände systematisch in verständliche Aussagen übersetzt werden**.
Ziel ist es, eine **deterministische, konsistente und überprüfbare Übersetzung** von interner Entscheidungslogik in menschlich lesbare Erklärungen zu ermöglichen.

Die Ableitung folgt festen Mustern und vermeidet freie, kontextabhängige Interpretation.

&nbsp;

## Grundprinzip der Ableitung

Die Übersetzung von Regeln zu Aussagen folgt drei Grundprinzipien:

1. **Determinismus**
   Gleiche Regelzustände führen stets zu gleichen Aussagen.
2. **Transparenz**
   Jede Aussage lässt sich eindeutig auf Regeln und Zustände zurückführen.
3. **Reduktion**
   Es werden nur jene Informationen verbalisiert, die für das Verständnis der Entscheidung notwendig sind.

Die Ableitung erfolgt **nach der Entscheidung**, nicht während der Entscheidungsfindung.

&nbsp;

## Mapping von Regel-IDs zu Textbausteinen

Jede Entscheidungsregel (R1–R5) wird mit einem **festen Satz von Textbausteinen** verknüpft.
Diese Bausteine sind sprachlich neutral formuliert und frei von UI-spezifischen Annahmen.

### Beispielhaftes Regel–Text-Mapping

| Regel-ID | Regelzustand | Textbaustein                     |
| -------- | ------------ | -------------------------------- |
| R1       | erfüllt      | "Energiebedingungen erfüllt"     |
| R1       | blockiert    | "Unzureichender Überschuss"      |
| R2       | soft         | "Speicherreserve wird geschont"  |
| R2       | hard         | "Speicherreserve unterschritten" |
| R3       | override     | "Sicherheitsgrenze erreicht"     |
| R4       | blockiert    | "Prognose instabil"              |
| R5       | aktiv        | "Ruhezeit aktiv"                 |

Das Mapping stellt sicher, dass **Regelwissen explizit und wiederverwendbar** bleibt.

&nbsp;

## Kontextabhängige Formulierungen

Die finalen Aussagen entstehen durch **Kombination der Textbausteine mit Entscheidung und Kontext**.

Dabei wird zwischen verschiedenen Entscheidungstypen unterschieden:

### Start-Entscheidungen

Beispiel:

> "Start erlaubt: Energiebedingungen erfüllt und Speicherreserve ausreichend."

### Stop-Entscheidungen

Beispiel:

> "Stopp ausgelöst: Speicherreserve unterschritten."

### Bewusstes Nicht-Handeln (NOOP)

Beispiel:

> "Keine Aktion: Ruhezeit aktiv, obwohl Energiebedingungen erfüllt sind."

Der Kontext bestimmt **Reihenfolge und Gewichtung**, nicht jedoch den semantischen Inhalt der Bausteine.

&nbsp;

## Konsistente Terminologie

Für die Ableitung gilt eine **strikte terminologische Konsistenz**:

* interne Regelbegriffe werden **einheitlich** übersetzt,
* gleiche Sachverhalte werden nicht mit wechselnden Begriffen beschrieben,
* negative Entscheidungen werden aktiv formuliert (z. B. "Keine Aktion" statt "Nicht gestartet").

Beispiele konsistenter Terminologie:

* "Keine Aktion" statt wechselnder Verneinungen,
* "Ruhezeit" statt Deadband/Timeout/Mindestpause,
* "Sicherheitsgrenze" statt wechselnder Hardwarebegriffe.

Diese Konsistenz ist Voraussetzung für Vertrauen und Lernbarkeit.

&nbsp;

## Zusammensetzen einer vollständigen Erklärung

Eine vollständige Erklärung wird algorithmisch zusammengesetzt aus:

1. **Entscheidung** (Wirkung)
2. **Primärem Regelbaustein** (Hauptgrund)
3. **Sekundären Regelbausteinen** (Kontext)
4. **Relevanten Datenpunkten** (optional)

### Beispiel

Regelzustände:

* R1: erfüllt
* R2: erfüllt
* R3: erfüllt
* R4: blockiert
* R5: aktiv

Abgeleitete Aussage:

> "Keine Aktion: Prognose instabil und Ruhezeit aktiv, obwohl Energiebedingungen erfüllt sind."

Die Struktur bleibt unabhängig vom Ausgabekanal erhalten.

&nbsp;

## Einordnung

Die hier beschriebene Ableitung bildet das **Bindeglied zwischen Entscheidungslogik und Erklärungsmodell**.
Sie stellt sicher, dass Erklärungen nicht ad hoc entstehen, sondern **formal, reproduzierbar und überprüfbar** sind.

Im nächsten Unterkapitel wird gezeigt, **wie diese Erklärungen konsistent zwischen Logs und UI verwendet werden**.



---

> **Nächster Schritt:** Im nächsten Unterkapitel folgt die Konsistenzprüfung.
>
> 👉 Weiter zu **[24.3 - Konsistenz zwischen Logs und UI-Begründung](../243_log_ui_consistency/README.md)**
>
> 🔙 Zurück zu **[24 - Erklärungsmodell](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
