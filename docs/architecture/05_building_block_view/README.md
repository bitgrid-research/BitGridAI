# 05 Bausteinsicht

Jetzt gehen wir ins Innere.

Nachdem Kontext und Lösungsstrategie geklärt sind, zerlegen wir **BitGridAI** in seine konkreten Bausteine.  
Dieses Kapitel zeigt die **statische Struktur** des Systems: Welche Teile es gibt, wofür sie zuständig sind und wie sie zueinander stehen.

Wir bleiben sachlich und übersichtlich.  
Keine Abläufe, keine Timings – nur Struktur.

Wir arbeiten mit **Abstraktionsebenen**:  
von außen nach innen, von grob nach detailliert.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster im Maschinenraum. Vor ihm liegen einzelne Bauklötze mit Labels wie „Core“, „Adapter“, „UI“, „Data“. Er hält einen Schraubenschlüssel und sortiert die Teile.)*  
![Cyborg-Hamster zerlegt das System](link_zum_baustein_bild.png)

&nbsp;

## Inhalt dieses Kapitels

Die Bausteinsicht ist in zwei Ebenen gegliedert:

- **[5.1 Level 1 – Die Blackbox (Gesamtsicht)](./051_blackbox/README.md)**  
  * BitGridAI als ein einzelner Baustein. (*Fokus auf Systemgrenzen, externe Schnittstellen und Verantwortung nach außen*).

- **[5.2 Level 2 – Die Whitebox (Innenleben)](./052_whitebox/README.md)**  
  Aufteilung des Systems in seine Hauptbestandteile.  
  Core, Adapter, Explain/UI sowie Data & Research – mit klaren Zuständigkeiten.

---
> **Nächster Schritt:** Die Struktur ist sichtbar.  
> Jetzt betrachten wir, **wie diese Bausteine im Betrieb zusammenspielen**.
>
> 👉 Weiter zu **[06 Laufzeitsicht](../06_runtime_view/README.md)**
> 
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
