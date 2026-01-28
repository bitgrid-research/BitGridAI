# 26.2 – Szenarien im Automotive-Kontext

Dieses Unterkapitel beschreibt **typische Nutzungssituationen im Automotive-Kontext**, in denen Lade- oder Energieentscheidungen durch ein In-Car-Interface nachvollziehbar kommuniziert werden müssen.
Im Gegensatz zum Smart-Home-Kontext ist die verfügbare Aufmerksamkeit stark begrenzt, weshalb **Klarheit, Kürze und Vorhersehbarkeit** im Vordergrund stehen.

Die Szenarien konzentrieren sich auf **Ladebeginn, Verzögerung und manuelle Overrides**, nicht auf detaillierte Energieoptimierung.

&nbsp;

## Szenario AU-1 – Verzögerter Ladebeginn (Preis- / PV-Optimierung)

**Beschreibung**
Ein Elektrofahrzeug ist angeschlossen, der Ladevorgang startet jedoch nicht sofort, da günstigere Bedingungen erwartet werden (z. B. PV-Verfügbarkeit oder niedrigerer Preis).

**Rahmenbedingungen**

* Fahrzeug angeschlossen
* Ladezustand ausreichend für nächste Fahrt
* Günstigere Bedingungen in absehbarer Zeit

**Erwartetes Systemverhalten**

* Kein sofortiger Ladebeginn
* Anzeige eines klaren Zustands (z. B. „Laden geplant“)
* Kurze Begründung für die Verzögerung

**Relevante Aspekte für Evaluation**

* Verständlichkeit der Verzögerung
* Akzeptanz von geplantem statt sofortigem Laden
* Keine Aufforderung zur Interaktion während der Fahrt

&nbsp;

## Szenario AU-2 – Sofortladen als manueller Override

**Beschreibung**
Nutzer:innen entscheiden sich bewusst für einen sofortigen Ladebeginn, unabhängig von Systemempfehlungen.

**Rahmenbedingungen**

* Automatikbetrieb aktiv
* Manueller Eingriff über das In-Car-Interface

**Erwartetes Systemverhalten**

* Sofortiger Ladebeginn
* Klare Kennzeichnung des Override-Zustands
* Transparente Information über Abweichung von der Automatik

**Relevante Aspekte für Evaluation**

* Verständlichkeit der Override-Wirkung
* Wahrnehmung von Kontrolle ohne Kontrollillusion
* Saubere Rückkehr in den Automatikbetrieb

&nbsp;

## Szenario AU-3 – Kurzfristige Abfahrtszeit

**Beschreibung**
Eine ungeplante, kurzfristige Abfahrt macht eine schnelle Ladeentscheidung erforderlich.

**Rahmenbedingungen**

* Abfahrtszeit liegt deutlich vor ursprünglich geplanter Ladephase
* Mindestladeziel muss erreicht werden

**Erwartetes Systemverhalten**

* Priorisierung der Mobilitätsanforderung
* Anpassung oder Aufhebung bestehender Ladepläne
* Klare, kurze Erklärung der Entscheidung

**Relevante Aspekte für Evaluation**

* Vertrauen in sicherheitsrelevante Priorisierung
* Verständlichkeit unter Zeitdruck
* Vermeidung komplexer Detailanzeigen

&nbsp;

## Zusammenfassung

Die Automotive-Szenarien zeigen, wie dieselbe Entscheidungslogik wie im Smart-Home-Kontext unter **radikal anderen Aufmerksamkeitsbedingungen** vermittelt werden muss.

Im Fokus stehen:

* minimale kognitive Belastung,
* klare Zustandskommunikation,
* und konsistente, kurze Erklärungen.

Diese Szenarien bilden die Grundlage für **Use Cases**, die im nächsten Unterkapitel formalisiert werden.


---

> **Nächster Schritt:** Im nächsten Unterkapitel folgen die Use Cases.
>
> 👉 Weiter zu **[26.3 - Use Cases für Tests & Evaluation](../263_evaluation_use_cases/README.md)**
>
> 🔙 Zurück zu **[26 - Szenarien & Use Cases](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
