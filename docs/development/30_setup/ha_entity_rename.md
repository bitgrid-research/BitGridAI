# HA-Entity-Umbenennung (Privacy-Migration)

Die HA-Config referenzierte Entity-IDs, die **reale Geräte-Identifier** enthielten
(SMA-Seriennummern, lokale Geräte-IP des Heizstabs). Diese wurden im Repository
durch serien-/IP-freie Namen ersetzt und die zugehörigen **HA-Entities live
umbenannt** (via `scripts/ha_rename_entities.py`), anschließend deployt.

## Status (erledigt)

- **13 Entities umbenannt** über die WS-API: 6 von der Config referenzierte SMA-/
  Heizstab-Sensoren + 7 weitere Heizstab-Sensoren. Config deployt (`--restart`),
  verifiziert: `sensor.pv_power_w` liest live `sensor.sma_tripower_pv_power`.
- **Bewusst NICHT umbenannt:** ~137 weitere SMA-Telemetrie-Sensoren (`sensor.sn_<serial>_*`)
  und 1 `number.hot_water_assurance_<ip>`. Begründung: nicht in Git, nicht von der
  Config referenziert → kein Privacy-Gewinn, aber Risiko für HA-Energy-Dashboard,
  Langzeit-Statistiken und externe Automationen. Siehe [[FINDINGS]].

## Tool

```bash
python scripts/ha_rename_entities.py          # Dry-Run (zeigt regelbasiert alle Treffer)
python scripts/ha_rename_entities.py --apply   # live ausführen
```

Substitutionsregeln in `SUBSTITUTIONS`: `sn_3012953672→sma_tripower`,
`sn_3015995559→sma_storage`, `_192_168_178_58→` (entfernt). Renames sind live
wirksam (kein Restart nötig); Config-Änderungen brauchen anschließend `deploy_ha.sh`.

> Falls später doch alle Telemetrie-Sensoren bereinigt werden sollen: vorher
> HA-Energy-Dashboard-Einbindung und Statistik-Auswirkungen prüfen.

## Ziel-Entity-IDs (neue, serienfreie Namen)

Die **aktuellen** (alten) IDs enthalten noch Serial/IP — sie sind in HA sichtbar
bzw. lokal in `INFRASTRUCTURE.md` (gitignored) dokumentiert. Jede Entity auf die
Ziel-ID unten umbenennen:

| Gerät | Messgröße | Ziel-`entity_id` |
|---|---|---|
| SMA Sunny Tripower (PV) | PV-Leistung | `sensor.sma_tripower_pv_power` |
| SMA Sunny Boy Storage | Batterie-SoC | `sensor.sma_storage_battery_soc_total` |
| SMA Sunny Boy Storage | Akku laden | `sensor.sma_storage_battery_power_charge_total` |
| SMA Sunny Boy Storage | Akku entladen | `sensor.sma_storage_battery_power_discharge_total` |
| SMA Sunny Boy Storage | Netzbezug | `sensor.sma_storage_metering_power_absorbed` |
| SMA Sunny Boy Storage | Netzeinspeisung | `sensor.sma_storage_metering_power_supplied` |
| AC ELWA 2 Heizstab | Solar-Leistung | `sensor.ac_elwa_2_power1_solar` |
| AC ELWA 2 Heizstab | Betriebsmodus | `sensor.ac_elwa_2_screen_mode` |
| AC ELWA 2 Heizstab | Wassertemperatur 1 | `sensor.ac_elwa_2_temperatur_1` |

## Schritte

1. **HA → Einstellungen → Geräte & Dienste → Entitäten.**
2. Pro Zeile die aktuelle Entity (ID enthält noch Serial/IP) suchen →
   **Einstellungen (Zahnrad) → Entitäts-ID** → auf die Ziel-ID ändern.
3. `.env` setzen: `BITGRID_HEIZSTAB_ENTITY=sensor.ac_elwa_2_power1_solar`
4. Neu deployen: `bash scripts/deploy_ha.sh --restart`
5. Prüfen, dass PV/SoC/Netz-Sensoren **nicht** `unavailable` sind.

## Hinweise

- **SMA WebConnect / pysmaplus** kann Entities beim Reload neu anlegen — nach der
  Umbenennung kurz prüfen, ob die IDs stabil bleiben.
- Die **Miner-Configs** (`avalonq_miner1.yaml`, `avalonq_miner2.yaml`) sind bereits
  gitignored — deren IPs liegen nie im Repository, hier ist nichts zu tun.
- Vollständiges Geräte-↔-IP-Mapping: `INFRASTRUCTURE.md` (nur lokal, gitignored).
