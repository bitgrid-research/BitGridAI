# 07 - Verteilungssicht

Genug der Theorie, jetzt wird's handfest. 

Wo "wohnt" **BitGridAI** eigentlich?

In der Verteilungssicht bringen wir die Software-Bausteine aus Kapitel 5 auf die Straße – oder besser gesagt: auf die Server. Wir beschreiben die technische Infrastruktur, auf der das System läuft. Das umfasst Hardware, Netzwerke und alles, was man anfassen (oder zumindest pingen) kann.

Hier klären wir, welche Komponente auf welchem Server läuft und wie die Maschinen miteinander vernetzt sind.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster als Systemadministrator, umgeben von blinkenden Server-Racks, Netzwerk-Switches.)*
![Hamster als Sysadmin im Serverraum](link_zum_deployment_bild.png)

## Inhalt dieses Kapitels

Hier findest du den Bauplan unserer Infrastruktur:

* **[7.01 - Deployment (Docker-first, Umbrel-ready)](../0701_deployment_view.md)**
    * Hauptkapitel. Basis-Deployment als Docker-Compose im LAN; optionales Packaging als Umbrel App.
* **[7.02 - Infrastruktur & Umgebungen](./0702_deployment_view.md)**
    * Detailblick auf Pipeline, Hardware und Betriebsvarianten (Standalone, Distributed, Hybrid).

---
> **Nächster Schritt:** Die Hardware steht, die Container laufen. Aber was hält alles im Innersten zusammen? Im nächsten Kapitel widmen wir uns den Themen, die *alle* Bausteine betreffen: Sicherheit, Logging und Datenmodelle.
>
> 👉 Weiter zu **[08 - Querschnittliche Konzepte](../08_concepts)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
