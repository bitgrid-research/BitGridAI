# 8.4 - Explainability & Transparenz

Verstehen ist Vertrauen.

BitGridAI trifft autonome Entscheidungen, die für Nutzer reale Auswirkungen haben:  
Energieflüsse ändern sich, Hardware startet oder stoppt, Kosten entstehen oder werden vermieden.  
Damit diese Entscheidungen akzeptiert und kontrolliert werden können, müssen sie **verständlich und nachvollziehbar** sein.

Dieses Kapitel beschreibt die **systemweiten Prinzipien der Explainability und Transparenz** in BitGridAI.  
Explainability ist dabei kein UI-Feature, sondern ein **architektonisches Grundprinzip**, das alle Bausteine betrifft.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster erklärt einem anderen Hamster mit einer kleinen Tafel, warum ein Schalter auf „ON“ steht. Ein Sprechblasen-Symbol mit „Warum?“ schwebt darüber.)*  
![Hamster erklärt eine Entscheidung](link_zum_explain_hamster.png)

&nbsp;

## Ziel der Explainability

Explainability in BitGridAI verfolgt drei zentrale Ziele:

1. **Nachvollziehbarkeit**  
   Nutzer sollen verstehen können, *warum* eine Entscheidung getroffen wurde.

2. **Überprüfbarkeit**  
   Entscheidungen müssen auch nachträglich analysierbar und reproduzierbar sein.

3. **Vertrauensbildung**  
   Transparente Entscheidungen schaffen Akzeptanz für Automatisierung.

Explainability bedeutet nicht, dass das System *immer* tut, was der Nutzer erwartet – sondern dass es **erklärt, warum es anders handelt**.

&nbsp;

## Grundprinzipien

Die Explainability folgt systemweit klaren Leitlinien:

- **Warum vor Was**  
  Jede relevante Aktion ist mit einer Begründung verknüpft.

- **Entscheidung ≠ Erklärung**  
  Technische Entscheidungslogik und menschliche Erklärung sind getrennt.

- **Read-only**  
  Erklärungen verändern niemals den Systemzustand.

- **Deterministisch**  
  Gleiche Eingaben führen zu gleichen Erklärungen.

- **Kontextsensitiv**  
  Erklärungen beziehen sich auf den konkreten Zustand zum Entscheidungszeitpunkt.

&nbsp;

## Explainability im Entscheidungsprozess

Explainability ist Teil jeder Entscheidung.

Eine Entscheidung umfasst:
- die ausgeführte Aktion,
- die beteiligten Regeln,
- die auslösenden Faktoren.

Diese Informationen werden systematisch erfasst und stehen für:
- UI-Anzeigen,
- Logs,
- Replays,
- Research-Auswertungen
zur Verfügung.

&nbsp;

## Explain Session

Eine **Explain Session** ist der formale Rahmen für eine Erklärung.

Sie referenziert:
- den relevanten `EnergyState`,
- die zugehörige Entscheidung,
- den Kontext der Nutzeranfrage (z.B. „Warum läuft der Miner gerade?“).

Explain Sessions sind:
- zeitlich gebunden,
- unveränderlich,
- eindeutig referenzierbar.

Sie dienen als Brücke zwischen technischer Logik und menschlichem Verständnis.

&nbsp;

## Ebenen der Erklärung

BitGridAI unterscheidet bewusst mehrere Erklärungsebenen:

### Kurzform (UI)

- kompakte, verständliche Aussage
- z.B. „PV-Überschuss ausreichend, Batterie über Mindestwert“

### Detailansicht

- beteiligte Regeln
- relevante Messwerte
- Grenzwerte und Schwellen

### Technische Sicht (Audit / Replay)

- vollständige Entscheidungs- und Zustandsdaten
- geeignet für Analyse und Forschung

Der Nutzer entscheidet, **wie tief** er einsteigen möchte.

&nbsp;

## Explainability & Autonomie

Explainability ist unabhängig vom Autonomie-Level:

- im manuellen Modus erklärt das System Vorschläge,
- im vollautomatischen Modus erklärt es getroffene Entscheidungen,
- bei Overrides erklärt es, warum bestimmte Aktionen blockiert wurden (z.B. Safety).

Mehr Autonomie erfordert **mehr**, nicht weniger Transparenz.

&nbsp;

## Explainability & Sicherheit

Sicherheitsentscheidungen sind besonders erklärungsbedürftig.

Grundsätze:
- Safety-Eingriffe werden immer explizit signalisiert,
- Gründe sind klar benannt (z.B. „Temperaturgrenze überschritten“),
- es gibt keine stillen Stops.

Explainability ersetzt keine Sicherheitsmaßnahmen, macht sie aber **verständlich**.

&nbsp;

## Technische Unabhängigkeit

Explainability ist:
- unabhängig von UI-Technologie,
- unabhängig von konkreten LLMs,
- unabhängig vom Deployment-Modell.

Ob Erklärungen durch Templates, Regeln oder Sprachmodelle erzeugt werden, ist eine Implementierungsentscheidung – das Prinzip bleibt gleich.

&nbsp;

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete Prompt-Templates
- UI-Layouts oder Texte
- Implementierungsdetails des Explain-Agents

Diese Details gehören in Entwicklungs- oder UI-Dokumentation.

&nbsp;

## Zusammenfassung

Explainability ist ein zentrales Qualitätsmerkmal von BitGridAI.

Sie stellt sicher, dass:
- Entscheidungen nachvollziehbar sind,
- Automatisierung kontrollierbar bleibt,
- Vertrauen entstehen kann, ohne Kontrolle abzugeben.

BitGridAI entscheidet nicht im Verborgenen – es erklärt sich.

---

> **Nächster Schritt:** Entscheidungen brauchen nicht nur Transparenz, sondern auch klare Grenzen menschlicher Kontrolle.  
> Im nächsten Abschnitt betrachten wir **Autonomie, HCI & menschliche Kontrolle**.
>
> 👉 Weiter zu **[8.5 - Autonomie, HCI & menschliche Kontrolle](./085_autonomy_and_hci.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
