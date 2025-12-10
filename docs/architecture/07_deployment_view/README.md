# 07 Verteilungssicht

Genug der Theorie, jetzt wird's handfest. 

Wo "wohnt" **BitGridAI** eigentlich?

In der Verteilungssicht bringen wir die Software-Bausteine aus Kapitel 5 auf die Straße – oder besser gesagt: auf die Server. Wir beschreiben die technische Infrastruktur, auf der das System läuft. Das umfasst Hardware, Netzwerke und alles, was man anfassen (oder zumindest pingen) kann.

Hier klären wir, welche Komponente auf welchem Server läuft und wie die Maschinen miteinander vernetzt sind.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster als Systemadministrator, umgeben von blinkenden Server-Racks, Netzwerk-Switches.)*
![Hamster als Sysadmin im Serverraum](link_zum_deployment_bild.png)

## Inhalt dieses Kapitels

Hier findest du den Bauplan unserer Infrastruktur:

* **[7.1 Die Infrastruktur & Umgebungen](./07_deployment_view.md)**
    * *Kurzbeschreibung:* Das zentrale Dokument für das Deployment. Es zeigt die Verteilung der Software-Artefakte auf Knoten (Server, Container, etc.). Wir definieren hier auch verschiedene Umgebungen wie Entwicklung (Dev), Test (Staging) und Produktion (Prod) und deren Unterschiede.

---
> **Nächster Schritt:** Die Hardware steht, die Container laufen. Aber was hält alles im Innersten zusammen? Im nächsten Kapitel widmen wir uns den Themen, die *alle* Bausteine betreffen: Sicherheit, Logging und Datenmodelle.
>
> 👉 Weiter zu **[08 Querschnittliche Konzepte](../08_concepts)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
