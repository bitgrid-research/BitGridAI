# 05.2.2.3 Health Monitor

Verantwortung: ueberwacht Verfuegbarkeit von Geraeten/Protokollen, sendet Heartbeats und Fehlermeldungen an Core/UI.

## Struktur

- **Heartbeat Sender:** publiziert periodische Statusmeldungen pro Adapter/Geraet.
- **Watchdog:** erkennt ausbleibende Telemetrie oder fehlgeschlagene Kommandos.
- **Degradation Classifier:** stuft Health (ok/warn/error) ein und dokumentiert Ursache.
- **Notifier:** sendet Health-Events auf `health/#` und an Logging.

## Schnittstellen

- **Provided:** Health-Events (`health/#`), Warnungen bei Telemetrie- oder Aktor-Ausfaellen.
- **Required:** Signal ueber eingehende Telemetrie/Quittungen, Konfiguration fuer Heartbeat-Intervalle und Schwellen.

## Ablauf (vereinfacht)

1) Heartbeat Sender publiziert regelmaessig Status.  
2) Watchdog verfolgt Telemetrie- und Quittungseingaenge; bei Zeitueberschreitung -> Warnung/Error.  
3) Degradation Classifier bewertet Zustand; Notifier sendet Event.  
4) Core/UI zeigen Status, Data persistiert Health-Log.

## Qualitaet und Betrieb

- Klare Schwellen pro Geraet/Protokoll; keine globalen One-size-Werte.  
- Health bleibt entkoppelt: Ausfall eines Adapters blockiert Core nicht.  
- Optionale Selbstheilung: automatischer Reconnect/Restart nach Backoff.

---
> Zurueck zu **[5.2.2.x Adapter und Feld-I/O (Level 3)](./README.md)**  
> Zurueck zu **[5.2.2 Whitebox Adapter und Feld-I/O](../0522_adapters_whitebox.md)**
