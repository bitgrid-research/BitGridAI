# COMMANDS.md – ₿itsy-Dev Kommandos

Erkannte Kommandos — im Chat eingeben oder via Trigger-Flag in `HEARTBEAT.md` auslösen.
Wenn du eines empfängst oder siehst, führe das definierte Protokoll sofort aus.

---

## /full-review

**Zweck:** Vollständige Analyse aller `src/` und `docs/` Dateien — Schwachstellen, Inkonsistenzen und Lücken finden.
**Auslöser:**
- Direkte Chat-Eingabe: `/full-review`
- Trigger-Flag in `HEARTBEAT.md`: `FULL_REVIEW_REQUESTED`

### Protokoll

#### Schritt 1 — src/ scannen

- Alle `.py`-Dateien und `README.md` lesen
- **Schichtentrennung prüfen:** Hat `core/` Imports aus `explain/`, `ui/` oder `adapters/`? → Kritischer Befund
- **Vollständigkeit prüfen:** Fehlen `__init__.py`, leere Module, Stubs ohne Implementierung?
- **TODO/FIXME-Marker sammeln:** Datei + Zeile notieren
- **Konsistenz prüfen:** Klassennamen, Feldnamen und Zustände (z. B. `EnergyState`, `DecisionEvent`) konsistent mit Docs?

#### Schritt 2 — docs/architecture/ scannen (arc42 Kapitel 01–12)

- Kapitelstruktur vollständig? Pflichtabschnitte nach arc42 vorhanden?
- Querverweise: Zeigen Links auf existierende Dateien?
- Nummerierungsschema (`01_`, `011_`, `0521_` etc.) korrekt in allen Dateinamen?
- Datenmodell: `EnergyState`, `DecisionEvent`, Regelbezeichnungen (R1–R5) konsistent über alle Kapitel?
- Laufzeitsicht (Kap. 06): Decken die Szenarien alle kritischen Pfade ab? Edge Cases identifizieren.
- Widersprüche zwischen Kapiteln? (z. B. Kap. 04 Strategie vs. Kap. 05 Baustein)

#### Schritt 3 — docs/research/ scannen (Kapitel 20–29)

- Offene TODO-Blöcke inventarisieren (Datei + Abschnitt)
- BP-01–BP-21: Widersprechen Architekturentscheidungen (Kap. 09 ADR) einem der Prinzipien?
- Forschungsfragen (Kap. 20): Sind Working Questions für 2023/2024/2025 durch Inhalte abgedeckt?
- Terminologie: Glossar (Kap. 12) vs. tatsächlicher Sprachgebrauch — Abweichungen notieren

#### Schritt 4 — Befunde dokumentieren

- **Alle Probleme** nach `FINDINGS.md` Format eintragen — nichts weglassen, auch Niedrig-Schwere
- Format einhalten:
  ```
  ### [DATUM] [BEREICH] Kurztitel
  **Datei:** `pfad/zur/datei` (Zeile X)
  **Problem:** Was genau stimmt nicht?
  **Schwere:** Kritisch / Mittel / Niedrig
  **Empfehlung:** Was sollte getan werden?
  **Status:** Offen
  ```
- Neue Befunde **oben** in FINDINGS.md eintragen

#### Schritt 5 — Abschluss

- `FULL_REVIEW_REQUESTED` Flag in `HEARTBEAT.md` entfernen (falls gesetzt)
- Kurze Zusammenfassung ausgeben:
  ```
  /full-review abgeschlossen: X neue Befunde — Y Kritisch, Z Mittel, W Niedrig
  Details: FINDINGS.md
  ```

---

## Weitere Kommandos (noch nicht definiert)

Wenn diese Kommandos gebraucht werden, Protokoll ergänzen und Trigger-Flag in HEARTBEAT.md aufnehmen.

| Kommando | Trigger-Flag | Zweck |
|----------|-------------|-------|
| `/check-todos` | `CHECK_TODOS` | Nur TODO-Marker in src/ und docs/ sammeln, PROJECT_STATE.md aktualisieren |
| `/check-links` | `CHECK_LINKS` | Kaputte Querverweise in arc42-Kapitel prüfen |
| `/sync-state` | `SYNC_STATE` | PROJECT_STATE.md mit aktuellem Repo-Stand abgleichen |

> **Hinweis:** Kein Protokoll = kein aktiver Flag. Erst vollständig definieren, dann in HEARTBEAT.md eintragen.
