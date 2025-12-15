# 05.2.4.4 Export / Replay Service

Vom System zur Wissenschaft.

Der Export- und Replay-Service ist die **kontrollierte Schnittstelle nach außen**.
Er macht Entscheidungen, Zustände und Erklärungen **transportabel** –  
ohne die Kontrolle über Daten oder Betrieb zu verlieren.

Nichts verlässt das System zufällig.  
Alles ist **bewusst gewählt**, **signiert** und **reproduzierbar**.

*(Platzhalter für ein Bild: Der Hamster packt sorgfältig Ordner und Diagramme
in eine beschriftete Box „Export“. Daneben ein Siegel und ein Pfeil zu „Replay“.)*
![Hamster erstellt Export-Bundle](../media/pixel_art_export_replay.png)

&nbsp;

## Verantwortung

- Aufbau signierter Export-Bundles für Forschung und Analyse
- Durchsetzung von Opt-in und klaren Export-Scope-Regeln
- Bereitstellung von Manifest und Hash zur Verifikation
- Lokale Replay-Funktionen zur reproduzierbaren Analyse

&nbsp;

## Struktur

- **Request Handler**  
  Nimmt Export-Aufträge entgegen (Zeitfenster, Scope),
  prüft Opt-in und Berechtigungen.

- **Bundle Builder**  
  Sammelt Logs, KPIs und Explain-Sessions,
  baut ein strukturiertes ZIP-/Parquet-Bundle
  inkl. Manifest (Inhalt, Versionen, Zeitbasis).

- **Signer / Hasher**  
  Erzeugt Hashes oder Signaturen zur Integritätsprüfung
  und legt sie dem Bundle bei.

- **Replay Runner**  
  Ermöglicht lokale Replays gegen Core- oder Preview-Pfade
  (strict read-only, keine Aktorik).

&nbsp;

## Schnittstellen

**Provided**
- Export-Bundles (Datei / Download)
- Manifest und Hash / Signatur
- Optionale Replay-Ergebnisse (lokal)

**Required**
- Event- und Log Store
- KPI- und Explain-Daten
- Opt-in-Status
- Lokale Speicherpfade

&nbsp;

## Ablauf (vereinfacht)

1) Nutzer oder Tool stellt Export-Anfrage mit Scope und Zeitraum.  
2) Request Handler prüft Opt-in und Parameter.  
3) Bundle Builder sammelt relevante Daten und erstellt Bundle + Manifest.  
4) Signer / Hasher erzeugt Hash oder Signatur.  
5) UI/API erhält Bundle-Referenz, Hash und Metadaten.  
6) Optional: Replay Runner nutzt das Bundle für lokale Replays.

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Opt-in Pflicht**  
  Kein Export ohne explizite Zustimmung des Nutzers.

- **Integrität**  
  Jedes Bundle ist prüfbar über Hash / Signatur und Manifest.

- **Ressourcenschutz**  
  Größen- und Zeitlimits pro Export,
  Queueing und Backpressure bei hoher Last.

- **Sicher**  
  Replays sind strikt read-only:
  keine Geräte, keine Aktoren, kein Seiteneffekt.

---
> **Kapitel abgeschlossen:**  
> Daten können nun gespeichert, erklärt, ausgewertet
> und kontrolliert weitergegeben werden.
>
> 👉 Weiter zu **[5.2.5 Operations (Security, Config & Observability)](../0525_operations_whitebox/README.md)**
>
> 🔙 Zurück zu **[5.2.4 Data und Research](./README.md)**
>
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](../README.md)**
