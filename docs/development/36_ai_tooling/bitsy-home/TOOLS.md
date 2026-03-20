# TOOLS.md – ₿itsy-Home

## API-Endpunkte (read-only)

| Endpunkt | Beschreibung |
|----------|-------------|
| `GET http://bitgrid-core/state` | Aktueller EnergyState |
| `GET http://bitgrid-core/timeline` | Letzte Entscheidungsblöcke |
| `GET http://bitgrid-core/preview` | Prognose nächster Block |

## Modell

| Eigenschaft | Wert |
|------------|------|
| Modell | `qwen3:4b` |
| Betrieb | lokal auf Umbrel |
| Telemetrie | keine |

## Infrastruktur

| Service | Adresse |
|---------|---------|
| OpenClaw | `umbrel.local:18789` |
| BitGridAI API | `bitgrid-core:8080` (intern im Docker-Netz) |
