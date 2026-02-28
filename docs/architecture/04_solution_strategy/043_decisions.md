# 04.3 - Zentrale Architekturentscheidungen (Weichenstellungen)

Bewusste Weichenstellungen. Architektur entsteht nicht zufällig. 

Sie ist das Ergebnis von Entscheidungen – und von dem Mut, **eine Richtung einzuschlagen und andere bewusst nicht**.

In diesem Kapitel halten wir die **zentralen Architekturentscheidungen** von **BitGridAI** fest. Nicht im Sinne eines vollständigen Entscheidungsarchivs, sondern als nachvollziehbare Sammlung derjenigen Weichenstellungen, die den Charakter des Systems maßgeblich prägen.

<img src="../../media/architecture/04_soultion_strategy/bithamster_043.png" alt="Hamster tech" width="1000" />


&nbsp;

## Zentrale Architekturentscheidungen

| Entscheidung | Festlegung | Begründung | Konsequenzen |
| :--- | :--- | :--- | :--- |
| **Local First statt Cloud** 🏠| Betrieb vollständig lokal, ohne verpflichtende Cloud-Anbindung | • Energiedaten sind sensibel<br>• Offline-Betrieb muss möglich sein<br>• Forschung verlangt Datenhoheit | • Höhere Anforderungen an lokale Hardware<br>• Maximale Autonomie statt Cloud-Komfort |
| **Deterministische Regeln statt Black-Box-KI** ⚙️| Zentrale Entscheidungen über explizite Regeln (R1–R5) | • Entscheidungen müssen erklärbar sein<br>• Verhalten muss testbar bleiben<br>• Reproduzierbarkeit für Forschung | • Höherer Modellierungsaufwand<br>• Dafür transparente und stabile Entscheidungen |
| **Ereignisgetriebener Betrieb mit Block-Takt** ⏱️| Entscheidungen erfolgen ereignisgetrieben im festen 10-Minuten-Takt | • Vermeidung von Flapping<br>• Vorhersagbares Systemverhalten<br>• Klare Replays und Simulationen | • Keine Sofortreaktionen<br>• Ruhiger Betrieb für Hardware und Nutzer |
| **Strikte Trennung von Core und Adaptern** 🔌| Fachlogik und Geräteanbindung sind strikt entkoppelt | • Hardware ändert sich schneller als Logik<br>• Core muss isoliert testbar sein | • Mehr Schnittstellen<br>• Geringere Kopplung und bessere Wartbarkeit |
| **Explainability als Pflicht** 💬| Jede Entscheidung ist erklärbar und nachvollziehbar | • Vertrauen entsteht durch Verständnis<br>• Forschung benötigt semantische Einordnung | • Zusätzliche Komponenten (Explain-Agent)<br>• Klare Decision-Events mit Metadaten |
| **Append-only Logging & Replay-Fähigkeit** 💾| Logs werden unveränderlich gespeichert und sind replay-fähig | • Manipulationssicherheit<br>• Wissenschaftliche Nachvollziehbarkeit | • Höherer Speicherbedarf<br>• Dafür maximale Analysefähigkeit |



---

> **Nächster Schritt:** Nicht alles, was denkbar ist, gehört ins System. Im nächsten Kapitel halten wir fest, **was BitGridAI bewusst nicht sein will**.
>
> 👉 Weiter zu **[4.4 - Abgrenzungen & bewusste Nicht-Ziele (Fokus)](./044_non_goals.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
