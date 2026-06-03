# FINDINGS.md – Schwachstellen & Analysebefunde

> Autonome Hintergrundanalyse von ₿itsy-Dev.
> Neue Befunde oben eintragen — älteste unten.

---

## Format

```
### [DATUM] [BEREICH] Kurztitel
**Datei:** `pfad/zur/datei.md` (Zeile X)
**Problem:** Was genau stimmt nicht?
**Schwere:** Kritisch / Mittel / Niedrig
**Empfehlung:** Was sollte getan werden?
**Status:** Offen / In Bearbeitung / Erledigt
```

---

<!-- Befunde hier eintragen -->

### [2026-06-03] [SECURITY] Reale lokale IP / Geräte-Identifier in Git
**Datei:** mehrere (siehe unten)
**Problem:** Der Heizstab-Entity-Name (AC ELWA 2) enthielt die lokale Geräte-IP
und war in mehreren Dateien eingecheckt. Verstößt gegen die Projektregel
„echte IPs/Netzwerktopologie nie in Git". Zusätzlich in `2023b_sim.md`:
SMA-Seriennummern und Shelly-Geräte-IDs (MAC-artig). Ebenso die SMA-Seriennummern
in den Kern-Entity-IDs (`sensor.sn_<serial>_*`) quer durch die HA-Config.
**Schwere:** Mittel
**Empfehlung:**
- Python-Tooling: erledigt — Entity über `BITGRID_HEIZSTAB_ENTITY` (.env) konfigurierbar.
- `2023b_sim.md`: IP, SMA-Seriennummern und Shelly-Geräte-IDs maskiert.
- HA-Config: IP-Präfix aus der Heizstab-Entity entfernt (→ `ac_elwa_2_*`) in
  `configuration.yaml` + `bitgrid-dashboard.yaml`.
- HA-Config: SMA-Serial-Präfixe umbenannt (`sn_<serial>_*` → `sma_tripower_*` /
  `sma_storage_*`) in `configuration.yaml`, `bitcoin.yaml`, `sma_watchdog.yaml`.
**Live-Migration ausgeführt:** 13 HA-Entities via `scripts/ha_rename_entities.py`
umbenannt (6 referenzierte + 7 Heizstab), Config deployt + grazil neugestartet,
verifiziert (`sensor.pv_power_w` liest `sma_tripower_pv_power`). ~137 weitere
SMA-Telemetrie-Sensoren bewusst belassen (nicht in Git, nicht referenziert; Rename
würde Energy-Dashboard/Statistik riskieren). Details: `docs/development/30_setup/ha_entity_rename.md`.
**Status:** Erledigt — IP/Serials aus allen Git-Dateien entfernt; referenzierte Live-Entities umbenannt + deployt + verifiziert (Claude Code, 2026-06-03)

### [2026-06-03] [CORE] THROTTLE: Divergenz zwischen Kern und HA-Template
**Datei:** `src/ha/config/configuration.yaml` (Z. 552, 554) vs. `src/core/rules/*` + `src/core/rule_engine.py`
**Problem:** Der deterministische Kern erzeugt **nie** `THROTTLE` — keine Regel R1–R5
gibt es zurück, `actuation_writer.py` behandelt es wie `NOOP`. Das HA-Template
**erzeugt** `THROTTLE` jedoch (bei laufendem Miner unter Soft-Min bzw. verletzter
Profitabilität). Wo der Kern `NOOP`/`NOOP_R1_INSUFFICIENT_SURPLUS` liefert, drosselt
HA aktiv. Damit weicht das real ausgespielte Verhalten vom replaybaren Kern ab —
ein Determinismus-/Reproduzierbarkeitsproblem (betrifft auch die Studie, die laut
2024a den Kern repliziert).
**Schwere:** Mittel
**Empfehlung:** Kern und HA angleichen — entweder `THROTTLE` als echte Regel-Aktion
im Kern implementieren **oder** aus dem HA-Template entfernen. Bis dahin ist kein
THROTTLE-Studienszenario zulässig.
**Status:** Offen
