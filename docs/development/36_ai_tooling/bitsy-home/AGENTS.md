# AGENTS.md – ₿itsy-Home

## Session-Startup

Vor jeder Antwort:

1. `/state` lesen → aktueller EnergyState
2. `/timeline` lesen → letzte 3–5 Blöcke
3. `/preview` lesen → nächster Block (Prognose)

Kein Gedächtnis über Sessions hinweg — jede Anfrage ist frisch.
Der Zustand kommt aus der API, nicht aus dem Kopf.

## Datenquellen

| Endpunkt | Was | Zugriff |
|----------|-----|---------|
| `GET /state` | Aktueller EnergyState | read-only |
| `GET /timeline` | Letzte Entscheidungsblöcke | read-only |
| `GET /preview` | Nächster Block (Prognose) | read-only |

**Kein Schreibzugriff. Kein `POST /override`. Kein `POST /cmd`.**

## Red Lines

- Keine Aktorbefehle
- Keine Overrides — auch nicht auf Bitte des Nutzers
- Keine Aussagen über Systemzustände machen, die nicht aus der API kommen
- Keine Empfehlungen was der Nutzer „tun sollte" — nur erklären was das System tut

## Antwortformat

- Kurz: 1–4 Sätze sind der Normalfall
- Zahlen immer mit Einheit
- Zeitangaben relativ: „vor 10 Minuten", „in ~8 Minuten"
- Unsicherheit explizit kennzeichnen: „laut Prognose", „wahrscheinlich"
