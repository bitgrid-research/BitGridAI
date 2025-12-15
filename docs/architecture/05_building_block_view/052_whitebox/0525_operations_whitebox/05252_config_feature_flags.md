# 05.2.5.2 Configuration & Feature Flags

Der Werkzeugkasten für Verhalten.

Dieses Modul definiert, **wie sich BitGridAI verhält**, ohne Code anzufassen.
Profile, Defaults und Feature Flags werden sauber geladen, geprüft und verteilt –  
Änderungen greifen **ohne Neustart**.

*(Platzhalter für ein Bild: Der Hamster steht vor einem offenen Werkzeugkasten.
YAML-Rollen, Schalter und Etiketten wie „Defaults“, „Flags“, „Reload“ sind sichtbar.)*
![Hamster Configuration](../media/pixel_art_configuration_flags.png)

---

## Verantwortung

- Laden und Validieren von Konfigurationsprofilen
- Verteilen von Feature Flags und Defaults
- Sichere Reloads zur Laufzeit

---

## Struktur

- **Config Loader**  
  Lädt `config/*.yaml`, prüft Schemas und setzt explizite Defaults.

- **Integrity Check**  
  Optionale Signatur- oder Checksum-Prüfung gegen Manipulation.

- **Flag Dispatcher**  
  Verteilt Flags und Profile an Core, Adapter und UI.

- **Reload Hook**  
  Erkennt Änderungen, führt Reloads durch und versioniert den Zustand.

---

## Schnittstellen

**Provided**
- Valide Konfigurationen und Feature Flags
- Reload- und Versions-Events

**Required**
- Konfigurationsdateien (`config/*.yaml`)
- Schema-Definitionen
- Optional: Signaturen/Checksummen

---

## Ablauf (vereinfacht)

1) **Config Loader** liest Dateien und prüft Schema/Integrität  
2) **Flag Dispatcher** verteilt Werte an Abnehmer  
3) **Reload Hook** aktiviert Änderungen und erhöht die Konfigurationsversion  
4) Reload wird geloggt und als Event veröffentlicht

---

## Qualitäts- und Betriebsaspekte

- **Explizit:** keine stillen Defaults, alles ist benannt  
- **Nachvollziehbar:** Versionierung und Logs bei jedem Reload  
- **Robust:** Fallback-Profile für Minimalbetrieb bei Fehlern  

---

> 🔙 Zurück zu **[5.2.5.x Operations (Level 3)](./README.md)**  
> 🔙 Zurück zu **[5.2.5 Whitebox Operations](../0525_operations_whitebox.md)**
