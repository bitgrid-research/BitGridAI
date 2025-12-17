# 06 - Laufzeitsicht

Hier kommt Leben in die Bude!

Wir haben die Bausteine definiert – jetzt schauen wir ihnen bei der Arbeit zu.

Die Laufzeitsicht ergänzt die statische Bausteinsicht um die dynamische Perspektive. Sie zeigt, wie die Komponenten von **BitGridAI** in konkreten Szenarien interagieren. Wir beschreiben wichtige Abläufe, Protokolle und Zustandsübergänge, die für das Verständnis des Systems essenziell sind.

Das ist der Ort für Sequenz-, Aktivitäts- oder Zustandsdiagramme, die erklären, *wann* *wer* *was* tut.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster in Aktion, der z.B. an einem Schaltpult steht, während im Hintergrund Energieflüsse oder Datenpakete dynamisch visualisiert werden. Er drückt einen großen "START"-Knopf.)*
![Hamster dirigiert den Ablauf](link_zum_action_bild.png)

&nbsp;

## Inhalt dieses Kapitels

Wir haben die wichtigsten Laufzeitszenarien anhand unseres Regelwerks (R1–R5) dokumentiert. Diese Szenarien decken die kritischen Pfade ab:

* **[6.01 - Normaler Start (R1)](./0601_normal_start.md)**
    * Der "Happy Path". Wie fährt das System hoch und entscheidet aufgrund von PV-Überschuss und Strompreis, das Mining zu starten?

* **[6.02 - Autarkie-Schutz (R2)](./0602_autarky_protection.md)**
    * Der Haus-Beschützer. Wie verhindert das System, dass die Hausbatterie leergesaugt wird oder teurer Netzstrom bezogen wird?

* **[6.03 - Sicherheitsstopp (R3)](./0603_safety_stop.md)**
    * Die Notbremse. Was passiert bei Überhitzung oder Verbindungsabbruch? Wie wird der sofortige "Safety Stop" ausgelöst (Interrupt)?

* **[6.04 - Prognose-Optimierung (R4)](./0604_forecast_control.md)**
    * Der Blick in die Zukunft. Wie verhindern Wetter- und Preisprognosen einen Start, der sich in 15 Minuten nicht mehr lohnen würde?

* **[6.05 - Stabilität & Totband (R5)](./0605_deadband_stability.md)**
    * Die Ruhe im System. Wie verhindern wir "Flapping" (schnelles An/Aus) durch Wolkenzug mithilfe von Totbändern?

* **[6.06 - Manuelles Überschreiben](./0606_manual_override.md)**
    * Der Eingriff durch den Nutzer. Was passiert, wenn ein Operator die Automatik übersteuert ("Boost")?

* **[6.07 - Autonomie-Stufen & Kontrollmodi](./0607_autonomy_levels.md)**  
    * Die Kontrolllogik. Wie wird die Entscheidungshoheit zwischen Nutzer und System abhängig vom Autonomie-Level verteilt?

* **[6.08 - Boot & Recovery](./0608_boot_recovery.md)**  
    * Der Systemstart. Wie initialisiert sich BitGridAI sauber – und wie verhält es sich bei Ausfällen von Broker oder Datenbank?

* **[6.09 - Adapter- & Sensor-Ausfall](./0609_adapter_sensor_failure.md)**  
    * Der Blindflug-Schutz. Wie reagiert das System auf fehlende oder degradierte Telemetrie aus Adaptern und Sensoren?

* **[6.10 - Config- & Feature-Flag-Reload](./0610_config_feature_reload.md)**  
    * Umbauen im Betrieb. Wie werden Konfigurationsänderungen sicher zur Laufzeit übernommen – oder verworfen?

* **[6.11 - Export & Replay](./0611_export_replay.md)**  
    * Wissen mitnehmen. Wie werden Logs, KPIs und Explain-Daten kontrolliert exportiert und lokal reproduzierbar gemacht?

* **[6.12 - Authentifizierung & Rate-Limit (Fehlpfade)](./0612_auth_rate_limit_failures.md)**  
    * Kein Zugriff, keine Wirkung. Wie schützt sich BitGridAI vor unautorisierten oder übermäßigen schreibenden Requests?

* **[6.13 - Forecast-Update-Zyklus](./0613_forecast_update_cycle.md)**  
    * Vorausschau ohne Hektik. Wie werden neue Prognosen verarbeitet, ohne den gesamten Entscheidungsblock neu auszuführen?


---
> **Nächster Schritt:** Wir wissen jetzt, wie die Software arbeitet. Aber auf welcher Hardware landet sie eigentlich und wie kommt sie dorthin? Im nächsten Kapitel schauen wir uns die Infrastruktur an.
>
> 👉 Weiter zu **[07 - Verteilungssicht](../07_deployment_view/README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
