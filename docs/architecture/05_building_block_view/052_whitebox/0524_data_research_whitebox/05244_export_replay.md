# 05.2.4.4 Export/Replay Service

Verantwortung: baut signierte Export-Bundles fuer Forschung/Replays (Opt-in), stellt Manifest und Hash bereit, und stellt Replay-Funktionen lokal zur Verfuegung.

## Struktur

- **Request Handler:** nimmt Export-Auftraege (Scope, Zeitfenster) entgegen; prueft Opt-in.
- **Bundle Builder:** sammelt Logs/KPIs/Explain-Sessions, baut ZIP/Parquet-Bundle, erstellt Manifest + Hash.
- **Signer/Hasher:** signiert oder erzeugt Checksums fuer Integritaet.
- **Replay Runner:** erlaubt lokales Replay gegen Core/Preview (read-only).

## Schnittstellen

- **Provided:** Export-Bundles (Datei/Download), Manifest + Hash, optional Replay-Ergebnisse.
- **Required:** Event/Log Store, KPI-Daten, Explain-Sessions, Opt-in-Status, Speicherpfade.

## Ablauf (vereinfacht)

1) Request Handler prueft Opt-in und Parameter.  
2) Bundle Builder sammelt Daten, erstellt Bundle + Manifest.  
3) Signer/Hasher erzeugt Hash/Signatur; Rueckgabe an UI/API.  
4) Replay Runner nutzt Bundle fuer lokale Replays (keine Aktor-Kommandos).

## Qualitaet und Betrieb

- Opt-in-Pflicht; keine Exporte ohne ausdrueckliche Zustimmung.  
- Integritaet: Hash/Signatur, Manifest mit Quellen/Versionen.  
- Ressourcenlimits: groessen- und zeitliche Limits pro Export; Backpressure/Queueing.

---
> Zurueck zu **[5.2.4.x Data und Research (Level 3)](./README.md)**  
> Zurueck zu **[5.2.4 Whitebox Data und Research](../0524_data_research_whitebox.md)**
