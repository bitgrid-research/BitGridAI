# 082 – Persistenz / Persistency

> **Kurzüberblick:**  
> **Append-only** Speicherung (SQLite/Parquet/JSON), versionierte YAML-Configs, lokale Replays; kein Cloud-Backend.

> **TL;DR (EN):**  
> Append-only SQLite/Parquet/JSON, versioned configs, local replays; no cloud backend.

---

## Speicherstrategie

- **SQLite**: Laufzeit-DB für State/Timeline/KPIs.  
- **Parquet/JSON**: Langzeit-Logs & Replay-Bundles (`data/parquet/*.parq`).  
- **Config (YAML)**: Versioniert mit Checksums; Änderungen per ADR dokumentiert.  
- **ExplainSessions**: versionierte Prompt-/Result-Texte (DE/EN) lokal.

## Prinzipien

- **Append-only** → Auditierbarkeit & Reproduzierbarkeit.  
- **Offline-fähig**: alle Daten bleiben on-prem.  
- **Retention/Rotation**: Archivierung + Low-Disk-Alerts (aus Risikokapitel).  
- **Checksums/Hashes** für Export-Bundles (Research-Toggle = Opt-in).

> Storage contracts enable deterministic replays and research without external services.
