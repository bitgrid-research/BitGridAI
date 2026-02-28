# 08 - Querschnittskonzepte

Die Verfassung des Systems.

Wir haben die Bausteine definiert (Kap. 05), ihr Zusammenspiel beschrieben (Kap. 06) und gezeigt, wo BitGridAI betrieben wird (Kap. 07).  
Was noch fehlt, sind die **gemeinsamen Regeln**, nach denen *alle* diese Teile arbeiten.

Dieses Kapitel beschreibt die **übergreifenden Konzepte und Leitplanken**, die in **BitGridAI** systemweit gelten.  
Sie sorgen dafür, dass das System konsistent, verständlich und kontrollierbar bleibt – unabhängig davon, welcher Baustein gerade aktiv ist oder auf welchem Host er läuft.

Es geht hier nicht um konkrete Abläufe oder Implementierungen, sondern um die **Grundsätze**, die jede technische Entscheidung prägen.

&nbsp;

## Inhalt dieses Kapitels

Die folgenden Themen sind **querschnittlich**:  
Sie betreffen mehrere Bausteine gleichzeitig und bilden die technische „Sprache“, die BitGridAI zusammenhält.

* **[8.1 - Fachliche Modelle (Domain Models)](./081_domain_models.md)**  
  *Unsere gemeinsame Sprache.*  
  Wie definieren wir zentrale Begriffe wie „Nutzer“, „Energiequelle“, „Messwert“ oder „Zustand“, sodass alle Komponenten dasselbe darunter verstehen?

* **[8.2 - Sicherheits- & Vertrauenskonzept](./082_security_and_trust.md)**  
  *Sicherheit ist keine Option, sondern Voraussetzung.*  
  Wie definieren wir Vertrauensgrenzen, Authentifizierung, Autorisierung und das Prinzip, dass Safety (R3) niemals übersteuert werden kann?

* **[8.3 - Datenhaltung & Datenlebenszyklus](./083_data_persistence.md)**  
  *Was wird wo und wie lange gespeichert?*  
  Regeln für Persistenz, Hot- vs. Cold-Daten, Append-only-Logs, Exporte und Replays.

* **[8.4 - Explainability & Transparenz](./084_explainability.md)**  
  *Entscheidungen müssen nachvollziehbar sein.*  
  Wie stellt BitGridAI sicher, dass jede relevante Aktion erklärbar ist – für Nutzer, Logs und Research?

* **[8.5 - Autonomie, HCI & menschliche Kontrolle](./085_autonomy_and_hci.md)**  
  *Wer entscheidet was – und wann?*  
  Übergreifende Leitlinien zu Autonomie-Stufen, manuellen Overrides und der bewussten Balance zwischen Komfort und Selbstbestimmung.

* **[8.6 - Fehler-, Degradations- & Fail-safe-Prinzipien](./086_fail_safe_and_degradation.md)**  
  *Kein undefinierter Zustand.*  
  Wie geht das System mit Fehlern, Ausfällen und fehlenden Daten um – deterministisch, sichtbar und sicher?

* **[8.7 - Logging, Events & Monitoring](./087_logging_and_monitoring.md)**  
  *Was ist passiert – und warum?*  
  Einheitliche Regeln für Logs, Events, Health-Signale und Audit-Trails über alle Komponenten hinweg.

* **[8.8 - Testbarkeit, Simulation & Replays](./088_testability_and_simulation.md)**  
  *Verstehen vor Vertrauen.*  
  Wie ermöglichen Mocks, Simulatoren und Replays eine überprüfbare und reproduzierbare Systemlogik – auch ohne reale Hardware?

* **[8.9 - Build-, Update- & Release-Prinzipien](./089_build_and_release.md)**  
  *Vom Code zum stabilen Betrieb.*  
  Leitlinien für Updates, Rollbacks und Releases – mit Fokus auf Determinismus, Nachvollziehbarkeit und Sicherheit, nicht auf Tooling.
  
---

<img src="../../media/architecture/08_concepts/bithamster_08.png" alt="Hamster tech" width="1000" />

---
> **Nächster Schritt:**  
> Entscheidungen sind nun reproduzierbar getestet und überprüfbar.  
> Im nächsten Abschnitt betrachten wir, **wie BitGridAI gebaut, aktualisiert und sicher ausgerollt wird**.
>
> 👉 Weiter zu **[09 - Architektur- & Designentscheidungen](../09_design_decisions/README.md)**
>
> 🔙 Zurück zur **[Hauptübersicht](../../README.md)**

