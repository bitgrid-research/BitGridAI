# 05 Bausteinsicht

Willkommen im Maschinenraum von **BitGridAI**!

Nachdem wir Strategie und Kontext geklärt haben, wird es jetzt konkret. Die Bausteinsicht ist das Herzstück der technischen Dokumentation. Sie zeigt die statische Zerlegung des Systems in seine Bestandteile.

Wir nutzen das Prinzip der verschiedenen Abstraktionsebenen: Wir fangen ganz oben an (Level 1) und zoomen dann bei Bedarf tiefer in die einzelnen Container oder Komponenten hinein.

![Cyborg Hamster zeigt einen Baustein](link_zu_image_7.png)

## Inhalt dieses Kapitels

Wir haben die Struktur in zwei Hauptbereiche unterteilt, die du in den entsprechenden Unterordnern findest:

* **[Level 1: Die Blackbox (Gesamtsicht)](./051_blackbox/)**
    * *Kurzbeschreibung:* Der höchste Fluglevel. Hier betrachten wir das gesamte BitGridAI-System als einen einzigen "schwarzen Kasten" in seiner Umgebung. Diese Sicht ist perfekt, um den groben Scope zu verstehen, bevor man sich in Details verliert.

* **[Level 2: Die Whitebox (Innenleben)](./052_whitebox/)**
    * *Kurzbeschreibung:* Jetzt öffnen wir den Deckel der Blackbox. Wir zerlegen das System in seine Hauptkomponenten (z.B. Frontend, API-Gateway, Core-Services, Datenbanken) und erklären deren Aufgaben und Schnittstellen untereinander.
