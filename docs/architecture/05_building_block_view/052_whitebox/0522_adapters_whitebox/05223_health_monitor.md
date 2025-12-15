# 05.2.2.3 Health Monitor

Der Pulsmesser des Systems.

Der Health Monitor überwacht kontinuierlich, **ob Geräte und Protokolle noch leben**.  
Er erkennt Ausfälle früh, stuft sie ein und macht den Zustand für Core, UI und Logs sichtbar.

*(Platzhalter für ein Bild: Der Hamster trägt ein Stethoskop und prüft mehrere Geräte.
Über jedem Gerät leuchtet eine Ampel: grün, gelb oder rot.)*
![Hamster überwacht Systemgesundheit](../media/pixel_art_health_monitor.png)

---

## Verantwortung

- Überwachung der Verfügbarkeit von Geräten und Protokollen
- Versand periodischer Heartbeats
- Erkennung von Ausfällen und Degradierungen
- Transparente Weitergabe von Health-Status an Core, UI und Logging

---

## Struktur

- **Heartbeat Sender**  
  Publiziert periodische Statusmeldungen pro Adapter und Gerät.

- **Watchdog**  
  Erkennt ausbleibende Telemetrie oder fehlgeschlagene Kommandos.

- **Degradation Classifier**  
  Stuften den Zustand in `ok`, `warn` oder `error` ein und dokumentiert die Ursache.

- **Notifier**  
  Sendet Health-Events auf `health/#` und an das Logging.

---

## Schnittstellen

**Provided**
- Health-Events (`health/#`)
- Warnungen bei Telemetrie- oder Aktor-Ausfällen

**Required**
- Signale über eingehende Telemetrie und Quittungen
- Konfiguration für Heartbeat-Intervalle und Schwellenwerte

---

## Ablauf (vereinfacht)

1. Heartbeat Sender publiziert regelmäßig Statusmeldungen.  
2. Watchdog verfolgt Telemetrie- und Quittungseingänge; bei Timeout → Warnung oder Error.  
3. Degradation Classifier bewertet den Zustand und bestimmt die Schwere.  
4. Notifier sendet Events an Core und UI; Data persistiert den Health-Log.

---

## Qualität und Betrieb

- **Feingranulare Schwellen**  
  Pro Gerät und Protokoll konfigurierbar, keine globalen One-size-Fits-all-Werte.

- **Entkopplung**  
  Ein Adapter-Ausfall blockiert den Core nicht.

- **Resilienz**  
  Optionale Selbstheilung: automatischer Reconnect oder Restart mit Backoff.

---
> **Nächster Schritt:** Geräte unterscheiden sich.  
> Jetzt kapseln wir Herstellerlogik, Limits und Fähigkeiten sauber.
>
> 👉 Weiter zu **[5.2.2.4 Device Profiles](./05224_device_profiles.md)**
>
> 🔙 Zurück zu **[5.2.2 Adapter & Feld-I/O](../0522_adapters_whitebox.md)**
> 
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](./README.md)**
