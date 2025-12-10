# 06 Laufzeitsicht

Hier kommt Leben in die Bude! 

Wir haben die Bausteine definiert – jetzt schauen wir ihnen bei der Arbeit zu.

Die Laufzeitsicht ergänzt die statische Bausteinsicht um die dynamische Perspektive. Sie zeigt, wie die Komponenten von **BitGridAI** in konkreten Szenarien interagieren. Wir beschreiben wichtige Abläufe, Protokolle und Zustandsübergänge, die für das Verständnis des Systems essenziell sind.

Das ist der Ort für Sequenz-, Aktivitäts- oder Zustandsdiagramme, die erklären, *wann* *wer* *was* tut.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster in Aktion, der z.B. an einem Schaltpult steht, während im Hintergrund Energieflüsse oder Datenpakete dynamisch visualisiert werden. Er drückt einen großen "START"-Knopf.)*
![Hamster dirigiert den Ablauf](link_zum_action_bild.png)

## Inhalt dieses Kapitels

Wir haben exemplarisch einige der wichtigsten Laufzeitszenarien für BitGridAI dokumentiert. Diese Liste ist nicht abschließend, deckt aber die kritischen Pfade ab:

* **[6.1 Normaler Startvorgang](./061_normal_start.md)**
    * *Kurzbeschreibung:* Wie fährt das System hoch? Welche Initialisierungsschritte werden durchlaufen, bis BitGridAI betriebsbereit ist und den Regelbetrieb aufnimmt?

* **[6.2 Sicherheitsstopp (Safety Stop)](./062_safety_stop.md)**
    * *Kurzbeschreibung:* Ein kritischer Ablauf. Was passiert, wenn ein Notfall eintritt (z.B. Hardwareausfall, Grenzwertüberschreitung)? Wie wird das System sicher in einen definierten Ruhezustand gebracht?

* **[6.3 Totband-Halten (Deadband Hold)](./063_deadband_hold.md)**
    * *Kurzbeschreibung:* Ein spezifisches Regelungsszenario. Wie verhält sich das System, wenn sich eine Messgröße innerhalb eines definierten Toleranzbereichs (Totband) bewegt, um unnötige Schaltvorgänge zu vermeiden?

* **[6.4 Manuelles Überschreiben](./064_manuell_override.md)**
    * *Kurzbeschreibung:* Der Eingriff durch den Nutzer. Was passiert im System, wenn ein Operator die Automatik übersteuert und manuell eingreift? Welche Komponenten sind beteiligt und wie wird der Normalbetrieb wiederaufgenommen?
