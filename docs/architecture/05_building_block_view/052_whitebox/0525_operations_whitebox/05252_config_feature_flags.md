# 05.2.5.2 - Baustein: Configuration & Feature Flags

Der Werkzeugkasten für Verhalten.

Dieses Modul legt fest, **wie sich BitGridAI verhält**, ohne dass Code geändert werden muss.
Profile, Defaults und Feature Flags werden konsistent geladen, geprüft und verteilt –  
Änderungen greifen **zur Laufzeit**, ohne Neustart.

Konfiguration ist hier kein Nebenschauplatz,  
sondern ein **kontrollierter Teil der Architektur**.

*(Platzhalter für ein Bild: Der Hamster steht vor einem offenen Werkzeugkasten.
YAML-Rollen, Schalter und Etiketten wie „Defaults“, „Flags“, „Reload“ sind sichtbar.)*
![Hamster Configuration](../media/pixel_art_configuration_flags.png)

&nbsp;

## Verantwortung

- Laden und Validieren von Konfigurationsprofilen
- Zentrale Verwaltung von Feature Flags und Defaults
- Sichere Reloads während des laufenden Betriebs

&nbsp;

## Struktur

- **Config Loader**  
  Lädt `config/*.yaml`, prüft Schemas und setzt explizite Defaults.

- **Integrity Check**  
  Optionale Signatur- oder Checksum-Prüfung zum Schutz vor Manipulation.

- **Flag Dispatcher**  
  Verteilt Flags, Profile und Defaults an Core, Adapter und UI.

- **Reload Hook**  
  Erkennt Änderungen, führt Reloads durch und versioniert den Konfigurationszustand.

&nbsp;

## Schnittstellen

**Provided**
- Valide Konfigurationen und Feature Flags
- Reload- und Versions-Events

**Required**
- Konfigurationsdateien (`config/*.yaml`)
- Schema-Definitionen
- Optional: Signaturen oder Checksummen

&nbsp;

## Ablauf (vereinfacht)

1) **Config Loader** liest Dateien und prüft Schema und Integrität  
2) **Flag Dispatcher** verteilt Konfigurationen an alle Abnehmer  
3) **Reload Hook** aktiviert Änderungen und erhöht die Versionsnummer  
4) Reload wird geloggt und als Event veröffentlicht

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Explizit**  
  Keine stillen Defaults – jede Konfiguration ist benannt und dokumentiert.

- **Nachvollziehbar**  
  Jede Änderung ist versioniert und im Log sichtbar.

- **Robust**  
  Fallback-Profile ermöglichen Minimalbetrieb bei fehlerhaften Konfigurationen.

---
> **Nächster Schritt:**  
> Sicherheit und Konfiguration stehen.  
> Jetzt machen wir den Systemzustand sichtbar.
>
> 👉 Weiter zu **[5.2.5.3 Observability & Monitoring](./05253_observability.md)**
>
> 🔙 Zurück zu **[5.2.5 Operations (Security, Config & Observability)](./README.md)**
>
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](../README.md)**
