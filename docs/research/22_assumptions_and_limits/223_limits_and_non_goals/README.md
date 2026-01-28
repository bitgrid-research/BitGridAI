# 22.3 – Grenzen & Nicht-Ziele

Dieses Unterkapitel grenzt den **Untersuchungsrahmen bewusst ein** und benennt explizit jene Aspekte, die **nicht Gegenstand** dieser Arbeit sind.  
Die Klarstellung dieser Grenzen ist notwendig, um die **Aussagekraft der Ergebnisse korrekt einzuordnen** und Fehlinterpretationen zu vermeiden.

&nbsp;

## Abgrenzung des Untersuchungsrahmens

Die Arbeit untersucht die **Gestaltung erklärbarer, stabiler Entscheidungslogik** für ein lokales Energiemanagementsystem unter realistischen Alltagsbedingungen.  
Nicht betrachtet werden hingegen:

- globale oder systemübergreifende Optimierungen über mehrere Haushalte oder Netze hinweg,
- hochfrequente Echtzeitregelungen im Millisekundenbereich,
- vollständige physikalische Modellierungen aller Energieflüsse.

Der Fokus liegt bewusst auf einem **überschaubaren, deterministischen System**, dessen Verhalten für Nutzer:innen nachvollziehbar bleibt.

&nbsp;

## Nicht-Ziele für das Systemverhalten

Für das untersuchte System gelten folgende explizite Nicht-Ziele:

- **Keine Maximierung wirtschaftlicher Kennzahlen**  
  Ziel ist nicht die Ermittlung maximal möglicher Erträge oder Einsparungen, sondern ein **vertretbares, ruhiges und erklärbares Verhalten**.
- **Keine aggressive oder opportunistische Steuerung**  
  Kurzfristige Vorteile (z. B. durch häufiges Schalten) werden zugunsten von Systemstabilität, Hardware-Schonung und Nutzervertrauen bewusst vermieden.
- **Keine selbstlernenden Online-Optimierungen**  
  Das System passt seine Entscheidungslogik nicht autonom während des Betriebs an.
- **Keine Blackbox-Entscheidungen**  
  Jede Entscheidung – einschließlich bewussten Nicht-Handelns – muss regelbasiert erklärbar bleiben.

Damit wird ein Systemverhalten angestrebt, das **vorhersehbar, konservativ und kontrollierbar** ist.

&nbsp;

## Nicht-Ziele für die Evaluation

Auch für die Evaluation der Konzepte gelten klare Abgrenzungen:

- **Keine Bewertung langfristiger ökonomischer oder ökologischer Gesamteffekte**  
  Aussagen zur CO₂-Reduktion, Netzdienlichkeit oder Wirtschaftlichkeit erfolgen nur indirekt.
- **Keine statistisch repräsentativen Nutzerstudien**  
  Die Arbeit zielt auf konzeptionelle und qualitative Erkenntnisse, nicht auf breite quantitative Generalisierung.
- **Keine Benchmarking-Studien gegen kommerzielle Systeme**  
  Der Fokus liegt auf der internen Konsistenz und Nachvollziehbarkeit des entworfenen Ansatzes.
- **Keine Validierung durch reale Hardware-Langzeittests**  
  Die Ergebnisse basieren auf Modellierung, Szenarien und prototypischen Implementationen.

Diese Einschränkungen dienen dazu, die Evaluation auf jene Aspekte zu konzentrieren, die **für erklärbare Entscheidungslogik und UX-relevante Systemruhe** zentral sind.


---

> **Nächster Schritt:** Im nächsten Kapitel wird das Systemmodell beschrieben.
>
> 👉 Weiter zu **[23 - Systemmodell & Entscheidungslogik](../../23_system_model_and_decision_logic/README.md)**
>
> 🔙 Zurück zu **[22 - Annahmen & Grenzen](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
