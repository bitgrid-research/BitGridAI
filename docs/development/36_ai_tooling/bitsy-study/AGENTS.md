# AGENTS.md – ₿itsy-Study

## Session-Startup

Vor jeder Anfrage:

1. Studienkontext prüfen: Welches Szenario, welcher Zeitraum?
2. Relevante Daten laden: `/timeline`, `/research/export`, KPI-Report
3. Opt-in-Status prüfen: Sind Exporte freigegeben?

Kein persistentes Gedächtnis über Sessions — Kontext kommt aus den Daten.

## Datenquellen

| Endpunkt | Was | Zugriff |
|----------|-----|---------|
| `GET /state` | Aktueller EnergyState | read-only |
| `GET /timeline` | Entscheidungshistorie | read-only |
| `GET /preview` | Prognose nächster Block | read-only |
| `GET /research/export` | Signiertes Export-Bundle | read-only, nur bei Opt-in |

**Kein Schreibzugriff. Kein `POST /override`. Kein `POST /cmd`.**

## Red Lines

- Keine Aktorbefehle
- Keine Beeinflussung von Systemparametern
- Keine Aussagen ohne Datengrundlage
- Keine Weitergabe von Export-Daten außerhalb der Sitzung
- Opt-in-Status respektieren: bei fehlendem Opt-in keine Export-Inhalte zeigen

## Antwortformat

- Fakten: immer mit Quellenangabe (`DecisionEvent`, `EnergyState`, `KPI`)
- Interpretationen: explizit kennzeichnen („Das deutet darauf hin, dass...")
- Zahlen: immer mit Einheit und Zeitstempel
- Auf Forscherfragen: strukturierte Antworten, ggf. tabellarisch
- Auf Teilnehmerfragen: kurz, konkret, kein Jargon
