# 5.2 - Level 2: Die Whitebox (Innenleben)

Jetzt geht die Klappe auf.

Auf dieser Ebene öffnen wir die wichtigsten Bausteine aus der System-Whitebox und schauen hinein:  
**Was macht welcher Teil, wofür ist er verantwortlich und über welche Schnittstellen arbeitet er?**

&nbsp;

## Inhalt

- **[5.2.1 - Core-Orchestrierung](../052_whitebox/0521_core_whitebox/README.md)**  
  Regel-Engine, Block-Scheduler und EnergyState als deterministischer Kern.  
  *(Der Taktgeber mit Sicherheitsnetz.)*

- **[5.2.2 - Adapter & Feld-I/O](../052_whitebox/0522_adapters_whitebox/README.md)**  
  Anbindung von PV, Speicher, Smart Meter und Miner über MQTT, REST und Modbus.  
  *(Übersetzer zwischen Strom und Bytes.)*

- **[5.2.3 - UI & Explainability](../052_whitebox/0523_ui_explain_whitebox/README.md)**  
  Web-UI, API-Layer und Explain-Agent für Transparenz, Vorschau und Overrides.  
  *(Das Gesicht und die Stimme des Systems.)*

- **[5.2.4 - Data & Research](../052_whitebox/0524_data_research_whitebox/README.md)**  
  Persistenz, Exporte und Governance für Analyse und Replays.  
  *(Das Gedächtnis mit Notizzettel.)*

- **[5.2.5 - Operations (Security, Config, Observability)](../052_whitebox/0525_operations_whitebox/README.md)**  
  Authentifizierung, Policies, Konfiguration und Monitoring.  
  *(Der Hausmeister im Hintergrund.)*

---

<img src="../../../media/architecture/05_building_block_view/bithamster_052.png" alt="Hamster whitebox" width="1000" />

---
> **Nächster Schritt:** Jetzt sehen wir, *was* es gibt.  
> Im nächsten Kapitel betrachten wir, *wie* diese Bausteine im Betrieb zusammenspielen.
>
> 👉 Weiter zu **[06 - Laufzeitsicht](../../06_runtime_view/README.md)**
> 
> 🔙 Zurück zu **[5.1 - Level 1: Die Blackbox (Gesamtsicht)](../051_blackbox/README.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](../README.md)**
