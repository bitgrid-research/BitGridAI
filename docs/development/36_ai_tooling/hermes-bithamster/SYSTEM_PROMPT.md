# Hermes BitHamster (DEV) — Einrichtung

Der **DEV-BitHamster** ist ein lokaler Hermes-Agent (`qwen3.5:9b` via Ollama), der zwei
Rollen vereint: er **erklärt** die Energie-Entscheidungen für Laien und **analysiert**
die Haushalts-Datenbank read-only nach Optimierungsmustern. Sein Gedächtnis wächst über
die Zeit aus überprüften Fakten.

## Artefakte (Hermes-Agent → ⋮)

| Hermes-Feld | Datei | Inhalt |
|---|---|---|
| EDIT SOUL.MD | [SOUL.md](SOUL.md) | Persona / System-Prompt (ganze Datei kopieren) |
| EDIT DESCRIPTION | [DESCRIPTION.md](DESCRIPTION.md) | Kurzbeschreibung des Agenten |

Beim Einsetzen in die **Live-SOUL.MD** auf der `.96`-Box den Platzhalter `<HA-IP>` durch
die echte HA-Adresse ersetzen. Im Repo bleibt der Platzhalter (keine echten IPs in Git).

## Abgrenzung (wichtig)

Dieser DEV-Agent ist **nicht** der eingefrorene Studien-BitHamster (Gruppe B). Die Studie
nutzt reproduzierbare, eingefrorene Texte aus `src/sim/study_freeze.py` und die Konstante
`_B_INSTRUCTION` in [`src/explain/explain_agent.py`](../../../../src/explain/explain_agent.py).
Quelle der Wahrheit für die Studien-Stimme bleibt der Code. SOUL.md hier erweitert die
Persona bewusst um den Analyst-Auftrag und gilt nur für den Live-DEV-Agenten.

## Analyse-Ziel (der Nordstern des Agenten)

Der Agent soll aus den Daten den **Sweet Spot** finden: bei welcher Wetterlage und in
welcher Saison sich Solar-Mining am effektivsten betreiben lässt und welche **SoC-Bänder**
dafür optimal sind. Dafür kombiniert er:

- Speicher (SoC, Lade-/Entladeleistung)
- Miner (Leistung, Modus, Chip-Temperatur, Hashrate, Laufzeit)
- Wetter (Außentemperatur, Bewölkung, Niederschlag)
- Sonnenstand (Elevation, Azimut)
- PV-Erzeugung, Hausverbrauch, Netzbezug/-einspeisung

Zielgröße „Effektivität": möglichst viel Mining aus echtem Solarüberschuss (hoher
Eigenverbrauch, wenig Netzbezug) bei sicherem Speicher-Ladezustand. Ergebnis sind
**Hypothesen** über Bänder und Wetter-/Saisonfenster, die der Mensch prüft und gegebenenfalls
in deterministische Regeln (R1–R5) gießt. Nie automatischer Rückfluss in die Steuerung.

## Eiserne Leitplanken

- **Nur lesen.** Niemals in die Live-DB, niemals in `core/` oder die Steuerlogik schreiben,
  keine Geräte schalten. Das ist die operative Form von „read-only auf DecisionEvents".
- **Beratend, nicht steuernd.** Gefundene Muster sind Hypothesen. Ob daraus eine
  deterministische Regel (R1–R5) wird, entscheidet der Mensch. Kein automatischer Rückfluss
  in den Entscheidungskern (sonst Lernen im Steuerpfad, Verstoß gegen das Determinismus-Prinzip).
- **Lokal.** Keine Daten nach außen, keine Cloud, kein externer Chat-Kanal an diesem Agenten.

Die Regeln in SOUL.md sind die weiche Absicherung. Die **harte** Garantie ist das
Tool-Profil unten: ein Prompt allein hält ein Modell nicht zurück, die Tool-Freigabe schon.

## Tool-Profil (Hermes → MANAGE SKILLS & TOOLS)

| Tool | Status | Grund |
|---|---|---|
| Code Execution | **an** | SQL/pandas-Analyse der DB |
| File Operations | **an** (faktisch read) | DB-Snapshot und CSVs lesen |
| Memory | **an** | wachsendes, geerdetes Gedächtnis |
| Cron Jobs | **an** | nächtlicher DB-Scan |
| Web Search (DuckDuckGo) | optional | Methoden nachschlagen |
| Home Assistant (device control) | **aus** | Steuerpfad, rote Linie |
| Computer Use, Vision, Spotify, X, Image/Video | aus | nicht gebraucht |

## Datenzugang (read-only)

Echte Betriebsdaten liegen im **HA-Recorder** (`home-assistant_v2.db`, 1 Jahr Retention)
plus `mining_log.csv` / `stats_monthly.csv`. Wetter und Sonnenstand werden seit dem
Package [`weather_sun_tracking.yaml`](../../../../src/ha/config/packages/weather_sun_tracking.yaml)
mitaufgezeichnet (ab Deploy, vorwärts). Der Agent bekommt einen **nächtlichen Snapshot**,
nie die Live-DB:

```bash
# auf dem HA-Host, in den Agenten-Datenpfad kopieren:
sqlite3 home-assistant_v2.db ".backup /pfad/zum/snapshot/ha_snapshot.db"
```

Öffnen immer read-only: `sqlite3.connect("file:ha_snapshot.db?mode=ro", uri=True)`.

Vor dem ersten echten Nutzen: [`scripts/ha_recorder_audit.py`](../../../../scripts/ha_recorder_audit.py)
laufen lassen (prüft, ob alles sauber aufgezeichnet wird).
