# TOOLS.md – ₿itsy-Study

## API-Endpunkte (read-only)

| Endpunkt | Beschreibung | Voraussetzung |
|----------|-------------|---------------|
| `GET http://bitgrid-core/state` | Aktueller EnergyState | — |
| `GET http://bitgrid-core/timeline` | Entscheidungshistorie | — |
| `GET http://bitgrid-core/preview` | Prognose nächster Block | — |
| `GET http://bitgrid-core/research/export` | Signiertes Export-Bundle | Opt-in aktiv |

## Modell

| Eigenschaft | Wert |
|------------|------|
| Modell | `qwen3:14b` |
| Betrieb | lokal auf Umbrel oder Research-Node |
| Telemetrie | keine |

## Infrastruktur

| Service | Adresse |
|---------|---------|
| OpenClaw | `umbrel.local:18789` oder Research-Node |
| BitGridAI API | `bitgrid-core:8080` (intern im Docker-Netz) |

## Export-Format

Signierte Export-Bundles enthalten:
- `decisions.parquet` — DecisionEvents im Zeitraum
- `states.parquet` — EnergyState-Snapshots
- `kpis.json` — aggregierte Kennzahlen
- `manifest.json` — Zeitraum, Hash, Opt-in-Zeitstempel
