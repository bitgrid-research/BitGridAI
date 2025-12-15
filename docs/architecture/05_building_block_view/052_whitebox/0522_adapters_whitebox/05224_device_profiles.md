# 05.2.2.4 Device Profiles

Verantwortung: kapselt hersteller- und geraetespezifische Parameter (Skalierung, Limits, Features, Endpoints) und stellt sie allen Adapter-Komponenten bereit.

## Struktur

- **Profile Store:** versionierte Dateien (z.B. `config/device_<vendor>_<model>.yaml`).
- **Schema Validator:** prueft Profile gegen Schema (Einheiten, Pflichtfelder).
- **Capability Mapper:** ueberfuehrt Profile in lauffaehige Capabilities (z.B. supports_set_power, max_kw, temp_limit_c).
- **Reload Hook:** erlaubt Live-Reload der Profile ohne Dienstneustart.

## Schnittstellen

- **Provided:** Capabilities/Limits fuer Telemetry Ingest und Actuation Writer; skalierte Faktorwerte; Feature-Flags.
- **Required:** Profile-Dateien, Schema-Definition, optional Signatur/Checksum fuer Integritaet.

## Ablauf (vereinfacht)

1) Profile werden geladen und validiert; Fehler blockieren nur betroffene Geraete.  
2) Capability Mapper exportiert Capabilities an Ingest/Writer (z.B. Skalierung, Limits).  
3) Bei Reload werden Aenderungen angewendet und Version erhoeht; Health meldet Reload.

## Qualitaet und Betrieb

- Strikte Schemas und Einheiten; keine stillen Defaults.  
- Integritaetssicherung: optional Signatur/Checksum.  
- Rueckfallprofil pro Geraeteklasse fuer Minimalbetrieb.

---
> Zurueck zu **[5.2.2.x Adapter und Feld-I/O (Level 3)](./README.md)**  
> Zurueck zu **[5.2.2 Whitebox Adapter und Feld-I/O](../0522_adapters_whitebox.md)**
