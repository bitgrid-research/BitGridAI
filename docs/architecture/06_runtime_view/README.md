# 06 Laufzeitsicht

Hier kommt Leben in die Bude!

Wir haben die Bausteine definiert – jetzt schauen wir ihnen bei der Arbeit zu.

Die Laufzeitsicht ergänzt die statische Bausteinsicht um die dynamische Perspektive. Sie zeigt, wie die Komponenten von **BitGridAI** in konkreten Szenarien interagieren. Wir beschreiben wichtige Abläufe, Protokolle und Zustandsübergänge, die für das Verständnis des Systems essenziell sind.

Das ist der Ort für Sequenz-, Aktivitäts- oder Zustandsdiagramme, die erklären, *wann* *wer* *was* tut.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster in Aktion, der z.B. an einem Schaltpult steht, während im Hintergrund Energieflüsse oder Datenpakete dynamisch visualisiert werden. Er drückt einen großen "START"-Knopf.)*
![Hamster dirigiert den Ablauf](link_zum_action_bild.png)

## Inhalt dieses Kapitels

Wir haben die wichtigsten Laufzeitszenarien anhand unseres Regelwerks (R1–R5) dokumentiert. Diese Szenarien decken die kritischen Pfade ab:

* **[6.1 Normaler Start (R1)](./061_normal_start.md)**
    * Der "Happy Path". Wie fährt das System hoch und entscheidet aufgrund von PV-Überschuss und Strompreis, das Mining zu starten?

* **[6.2 Autarkie-Schutz (R2)](./062_autarky_protection.md)**
    * Der Haus-Beschützer. Wie verhindert das System, dass die Hausbatterie leergesaugt wird oder teurer Netzstrom bezogen wird?

* **[6.3 Sicherheitsstopp (R3)](./063_safety_stop.md)**
    * Die Notbremse. Was passiert bei Überhitzung oder Verbindungsabbruch? Wie wird der sofortige "Safety Stop" ausgelöst (Interrupt)?

* **[6.4 Prognose-Optimierung (R4)](./064_forecast_control.md)**
    * Der Blick in die Zukunft. Wie verhindern Wetter- und Preisprognosen einen Start, der sich in 15 Minuten nicht mehr lohnen würde?

* **[6.5 Stabilität & Totband (R5)](./065_deadband_stability.md)**
    * Die Ruhe im System. Wie verhindern wir "Flapping" (schnelles An/Aus) durch Wolkenzug mithilfe von Totbändern?

* **[6.6 Manuelles Überschreiben](./066_manual_override.md)**
    * Der Eingriff durch den Nutzer. Was passiert, wenn ein Operator die Automatik übersteuert ("Boost")?

* **[6.7 Autonomie-Stufen & Kontrollmodi](./067_autonomy_levels.md)**  
  *Wer entscheidet wann? Wie verteilt BitGridAI Verantwortung zwischen Nutzer und System – von manuell bis vollautomatisch?*

---
> **Nächster Schritt:** Wir wissen jetzt, wie die Software arbeitet. Aber auf welcher Hardware landet sie eigentlich und wie kommt sie dorthin? Im nächsten Kapitel schauen wir uns die Infrastruktur an.
>
> 👉 Weiter zu **[07 Verteilungssicht](../07_deployment_view/README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
