# 22 - Annahmen & Grenzen

Dieses Kapitel beschreibt die expliziten Annahmen, unter denen die im Rahmen dieser Arbeit getroffenen Aussagen gelten, und grenzt den Untersuchungsrahmen bewusst ein.
Ziel ist es, die Übertragbarkeit der Ergebnisse realistisch einzuordnen und implizite Erwartungen transparent zu machen.

&nbsp;

## Annahmen zum Nutzungskontext

Die Arbeit geht von zwei primären Nutzungskontexten aus:

- **Smart-Home-Dashboard** (z. B. Tablet, Wanddisplay, Weboberfläche)
- **Automotive In-Car-UI** (z. B. Begleitansicht im Fahrzeug)

Für beide Kontexte wird angenommen:

- Die **Zielgruppe verfügt nicht über vertiefte Energie- oder Systemexpertise**.  
  Entscheidungen müssen daher **erklärbar** sein, bevor sie als „optimal“ wahrgenommen werden.
- Die Nutzung erfolgt über **kurze, wiederkehrende Interaktionen**, nicht über permanente Beobachtung.  
  Das System muss auch ohne aktive Aufmerksamkeit **vorhersehbar und ruhig** bleiben.
- Vertrauen entsteht primär durch **Stabilität, Nachvollziehbarkeit und Zurückhaltung**, nicht durch maximale Reaktivität.

Daraus folgt, dass **Systemruhe** und **Erklärbarkeit von Nicht-Aktionen** (z. B. bewusstes Nicht-Schalten) höher priorisiert werden als kurzfristige Effizienzgewinne.

&nbsp;

## Annahmen zur Systemumgebung & Datenlage

Die betrachtete Systemarchitektur basiert auf folgenden Annahmen:

- **Lokale Ausführung („Local First“) ohne Cloud-Backend**  
  Alle Entscheidungen werden on-device getroffen; externe Dienste sind optional und nicht vorausgesetzt.
- **Begrenzte, aber robuste Datenbasis**  
  Verfügbare Messwerte sind:
  - PV-Leistung / Überschuss
  - Hauslast
  - Speicher-SoC
  - Netzbezug / Einspeisung  
  Optional können Strompreise oder Wetterprognosen einbezogen werden, sind jedoch **keine Voraussetzung**.
- **Deterministische Entscheidungslogik**  
  Regeln, Zustände und Entscheidungsparameter sind intern verfügbar, explizit modelliert und vollständig loggbar.
- **Blockbasierte Zeitstruktur**  
  Entscheidungen werden in festen Zeitintervallen (z. B. 10-Minuten-Blöcken) getroffen, nicht kontinuierlich.

Diese Annahmen ermöglichen eine **reproduzierbare Analyse** von Entscheidungen und deren Begründungen, auch über längere Zeiträume hinweg.

&nbsp;

## Grenzen & Nicht-Ziele

Die Arbeit grenzt sich bewusst von folgenden Zielsetzungen ab:

- **Keine Aussage zur maximalen Wirtschaftlichkeit oder globalen Netzoptimierung**  
  Es wird nicht untersucht, wie viel Ertrag theoretisch maximal möglich wäre, sondern wie Entscheidungen **vertretbar, stabil und erklärbar** getroffen werden können.
- **Keine vollumfängliche Produkt-UX**  
  Die dargestellten Interfaces und Zustände sind als **prototypische Leitlinien** zu verstehen, nicht als marktreife Designs.
- **Keine vollständige Abdeckung aller Geräteklassen und Lastprofile**  
  Der Fokus liegt auf einem exemplarischen Szenario (flexible Last), nicht auf universeller Übertragbarkeit.
- **Keine selbstlernenden oder adaptiven Online-Systeme**  
  Optimierungen erfolgen ausschließlich **offline** auf Basis geloggter Entscheidungen, nicht durch laufendes Anpassen der Regeln.

Diese bewussten Einschränkungen dienen dazu, **Komplexität zu reduzieren** und die **Erklärbarkeit jeder Entscheidung sicherzustellen**.


---

> **Nächster Schritt:** Die Annahmen und Grenzen sind geklärt.
> Im nächsten Kapitel werden das Systemmodell und die Entscheidungslogik beschrieben.
>
> 👉 Weiter zu **[23 - Systemmodell & Entscheidungslogik](../23_system_model_and_decision_logic/README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
