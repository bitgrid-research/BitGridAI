# 08 Querschnittskonzepte

Willkommen in der "Abteilung für allgemeine Angelegenheiten".

Wir haben die Bausteine definiert, wir wissen, wo sie laufen. Aber wie stellen wir sicher, dass sie alle dieselbe "Sprache" sprechen, wenn es um grundlegende technische Fragen geht?

In diesem Kapitel beschreiben wir die übergreifenden Prinzipien und Muster, die in **BitGridAI** angewendet werden. Das sind die technischen Leitplanken, die dafür sorgen, dass das System "aus einem Guss" ist und nicht wie ein zusammengeklebter Flickenteppich wirkt. Es geht um Themen, die *jeden* Entwickler betreffen, egal an welchem Baustein er gerade arbeitet.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster, der wie ein Dirigent vor verschiedenen technischen Symbolen steht (Datenbank-Tonne, Log-Datei, UI-Fenster, Warnschild) und sie koordiniert, oder einen großen, dicken Ordner mit der Aufschrift "REGELN" hält.)*
![Hamster mit dem Regelwerk](link_zum_konzepte_bild.png)

## Inhalt dieses Kapitels

Wir haben eine ganze Reihe von wichtigen Themen identifiziert, die zentral geregelt werden müssen. Hier ist die Übersicht unserer technischen Standards:

* **[8.1 Fachliche Modelle (Domain Models)](./081_domain_models.md)**
    * *Kurzbeschreibung:* Unsere gemeinsame Sprache. Wie definieren wir zentrale Begriffe wie "Nutzer", "Energiequelle" oder "Messwert" im Code, damit alle dasselbe darunter verstehen?

* **[8.2 Persistenz (Datenhaltung)](./082_persistency.md)**
    * *Kurzbeschreibung:* Wo und wie speichern wir Daten dauerhaft? Welche Datenbanktechnologien nutzen wir für welche Art von Daten?

* **[8.3 Benutzeroberfläche (UI)](./083_user_interface.md)**
    * *Kurzbeschreibung:* Wie sieht BitGridAI für den Menschen aus? Übergreifende Prinzipien für Design, Usability und Frontend-Technologie.

* **[8.4 Plausibilitäts- & Validitätsprüfungen](./084_plausibility_and_validity_checks.md)**
    * *Kurzbeschreibung:* Vertrauen ist gut, Kontrolle ist besser. Wie stellen wir an zentraler Stelle sicher, dass keine unsinnigen Daten ins System gelangen?

* **[8.5 Fehler- & Ausnahmebehandlung](./085_error_and_exception_handling.md)**
    * *Kurzbeschreibung:* Wenn es knallt: Wie fangen wir Fehler einheitlich ab, ohne dass das System abstürzt, und wie informieren wir den Nutzer (oder das Log)?

* **[8.6 Logging & Tracing](./086_logging_and_tracing.md)**
    * *Kurzbeschreibung:* Die Blackbox des Systems. Was schreiben wir wo mit, um im Nachhinein verstehen zu können, was passiert ist (insbesondere bei verteilten Abläufen)?

* **[8.7 Testbarkeit & Simulation](./087_testability_and_simulation.md)**
    * *Kurzbeschreibung:* Wie machen wir es uns leicht, das System zu testen – auch wenn die echte Hardware gerade nicht verfügbar ist? (Stichwort: Mocking, Simulatoren).

* **[8.8 Build- & Release-Management](./088_build_managment.md)**
    * *Kurzbeschreibung:* Von der Codezeile zum laufenden System. Wie sieht unsere CI/CD-Pipeline aus und wie automatisieren wir den Weg in die Produktion?
