# 07 Verteilungssicht

Genug der Theorie, jetzt wird’s handfest.

Wo „wohnt“ **BitGridAI** eigentlich?

In der Verteilungssicht bringen wir die Software-Bausteine aus Kapitel 5 in die reale Welt.  
Wir beschreiben die technische Infrastruktur, auf der das System betrieben wird: Hardware, Netzwerke und Laufzeitumgebungen – alles, was man anfassen (oder zumindest pingen) kann.

Hier klären wir, **welche Komponente auf welchem Knoten läuft** und wie diese Knoten miteinander verbunden sind.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster als Systemadministrator, umgeben von Server-Racks und Netzwerk-Switches.)*  
![Hamster als Sysadmin im Serverraum](link_zum_deployment_bild.png)

&nbsp;

## Inhalt dieses Kapitels

Dieses Kapitel beschreibt das konkrete Deployment von BitGridAI im lokalen Netzwerk – vom Basis-Setup bis zu möglichen Betriebsvarianten:

* **[7.1 Deployment (Docker-first, Umbrel-ready)](./071_deployment.md)**  
  *Hauptkapitel.*  
  Basis-Deployment als Docker-Compose-Stack im LAN; optionales Packaging als Umbrel-App.  
  Home Assistant greift sekundär über MQTT/REST zu. Keine Cloud, nur LAN.

* **[7.2 Infrastruktur & Umgebungen](./072_infrastructure_variants.md)**  
  *Erweiterte Sicht.*  
  Hardware-Profile, Netzwerk-Topologien und Betriebsvarianten (Standalone, Distributed, Hybrid).

---

> **Nächster Schritt:** Die Hardware steht, die Container laufen.  
> Aber was hält das System im Innersten zusammen?  
> Im nächsten Kapitel widmen wir uns den Themen, die **alle Bausteine betreffen**: Sicherheit, Logging, Datenmodelle und Explainability.
>
> 👉 Weiter zu **[08 Querschnittliche Konzepte](../08_concepts/README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
