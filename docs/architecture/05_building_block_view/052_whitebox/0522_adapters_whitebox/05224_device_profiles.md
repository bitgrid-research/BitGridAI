# 05.2.2.4 Device Profiles

Die Steckbriefe der Geräte.

Device Profiles kapseln alles, was **geräte- und herstellerspezifisch** ist:  
Skalierungen, Limits, unterstützte Features und Endpoints.  
So bleibt die Adapter-Logik sauber – und neue Hardware austauschbar.

*(Platzhalter für ein Bild: Der Hamster steht vor einer Wand mit Steckbriefen.
Auf jedem Blatt ein anderes Gerät mit Symbolen für Leistung, Temperatur und Limits.)*
![Hamster verwaltet Geräteprofile](../media/pixel_art_device_profiles.png)

---

## Verantwortung

- Kapselung von Hersteller- und Modellspezifika
- Zentrale Definition von Skalierungen, Limits und Features
- Bereitstellung konsistenter Capabilities für alle Adapter
- Änderbarkeit ohne Code-Anpassung

---

## Struktur

- **Profile Store**  
  Versionierte Dateien (z.B. `config/device_<vendor>_<model>.yaml`).

- **Schema Validator**  
  Prüft Profile gegen festes Schema (Einheiten, Pflichtfelder).

- **Capability Mapper**  
  Übersetzt Profile in lauffähige Capabilities  
  (z.B. `supports_set_power`, `max_kw`, `temp_limit_c`).

- **Reload Hook**  
  Ermöglicht Live-Reload der Profile ohne Dienstneustart.

---

## Schnittstellen

**Provided**
- Capabilities und Limits für Telemetry Ingest und Actuation Writer
- Skalierungsfaktoren und Feature-Flags

**Required**
- Profile-Dateien
- Schema-Definition
- Optional: Signatur oder Checksum zur Integritätsprüfung

---

## Ablauf (vereinfacht)

1. Profile werden geladen und gegen Schema validiert; Fehler blockieren nur betroffene Geräte.  
2. Capability Mapper stellt Capabilities für Ingest und Writer bereit.  
3. Bei Reload werden Änderungen aktiv, Version wird erhöht; Health meldet das Ereignis.

---

## Qualität und Betrieb

- **Strikte Schemas**  
  Keine stillen Defaults, alle Einheiten explizit.

- **Integrität**  
  Optionale Signatur oder Checksum verhindert Manipulation.

- **Fallbacks**  
  Rückfallprofile pro Gerätekategorie ermöglichen Minimalbetrieb.
  
---
> **Nächster Schritt:** Jetzt kommt der Mensch ins Spiel.  
> Anzeige, Erklärungen und bewusste Eingriffe.
>
> 👉 Weiter zu **[5.2.3 Whitebox UI und Explainability](../0523_ui_explain_whitebox.md)**
>
> 🔙 Zurück zu **[5.2.2 Adapter & Feld-I/O](../0522_adapters_whitebox.md)**
> 
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](./README.md)**
