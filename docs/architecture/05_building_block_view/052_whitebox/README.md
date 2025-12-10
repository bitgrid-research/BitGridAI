# 05.2 Level 2: Die Whitebox (Innenleben)

Jetzt wird es spannend: Wir werfen einen Blick unter die Motorhaube von **BitGridAI**.

In der Whitebox-Sicht (Level 2) öffnen wir die "Blackbox", die wir in Level 1 definiert haben. Wir zeigen, aus welchen großen funktionalen Blöcken das System besteht (z.B. "Core Services", "Data Ingestion", "API Gateway") und über welche internen Schnittstellen sie miteinander kommunizieren.

Ziel ist es, die grobe interne Struktur zu verstehen, ohne sich sofort in Implementierungsdetails zu verlieren.

![Cyborg Hamster zeigt interne Bausteine](link_zu_image_9.png)

## Inhalt dieses Kapitels

Hier liegt der zentrale Plan des Innenlebens. Diese Sicht ist der Ausgangspunkt für jede tiefere Einarbeitung in den Code.

* **[5.2.1 Die System-Whitebox](./052_whitebox.md)**
    * *Kurzbeschreibung:* Das Hauptdiagramm und die Beschreibung der Top-Level-Architektur. Hier siehst du, welche Module es gibt, wofür sie zuständig sind und mit wem sie Daten austauschen.

*(Hinweis: Sollten einzelne dieser Bausteine selbst sehr komplex sein, können sie in weiteren Unterordnern (Level 3, Level 4...) noch detaillierter als eigene Whiteboxen beschrieben werden.)*
