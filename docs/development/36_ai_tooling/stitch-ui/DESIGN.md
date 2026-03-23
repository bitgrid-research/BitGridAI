# BitGridAI – Stitch Design Prompt

> **Hinweis:** Diese Datei enthält einen englischen Designprompt für [Google Stitch](https://stitch.withgoogle.com),
> ein KI-gestütztes UI-Generierungstool von Google. Der Prompt ist bewusst auf Englisch verfasst,
> da Stitch englische Eingaben deutlich zuverlässiger verarbeitet und bessere Ergebnisse liefert.
> Der Prompt selbst wird **nicht verändert** — nur das generierte Design-System (`src/ui/design.md`) wird ins Projekt übernommen.

Dieser Prompt wird in [Google Stitch](https://stitch.withgoogle.com) eingegeben,
um das Design-System für das BitGridAI Web-UI zu generieren.

Nach der Generierung: Design System → `design.md` exportieren → in `src/ui/design.md` ablegen.

---

## Stitch-Prompt

```
Design a local-first energy management dashboard for a home prosumer system
called "BitGridAI". The user has solar panels, a home battery, and a Bitcoin
miner as a flexible load.

--- PRODUCT CONTEXT ---
The system makes rule-based decisions every 10 minutes to start/stop the miner
based on PV surplus, battery state of charge, temperature, grid price, and
forecasts. Every decision has a full explanation. No cloud. No machine learning.
100% local control.

--- DESIGN LANGUAGE ---
- Dark theme, energy-tech aesthetic (like a professional inverter dashboard)
- Accent colors: solar yellow (#F5A623), grid blue (#4A9EFF), battery green (#34C759)
- Safety/stop: red (#FF3B30), neutral/noop: gray
- Dense but readable — expert user, not a consumer app
- Typography: monospace for sensor values, sans-serif for labels
- Card-based layout with clear hierarchy

--- MAIN DASHBOARD (primary view) ---

TOP ROW: System Status Bar
- "BitGridAI" logo/wordmark (left)
- Block countdown: "Next block in 7:42" (center)
- System health dot: green/yellow/red + "Core OK | MQTT OK | DB OK"
- Date/time (right)

SECTION 1: Energy Flow (hero section)
A horizontal energy flow diagram showing:
  [SUN icon] 3.2 kW → [HOUSE 0.8 kW] → [BATTERY 80%] → [GRID ±0W]
                                              ↓
                                         [MINER: RUNNING]

SECTION 2: Four metric cards in a row
- "PV Leistung" — 3.200 W (yellow, sun icon)
- "Hausverbrauch" — 800 W (blue, house icon)
- "Batterie SoC" — 80% with circular progress gauge (green)
- "Miner Temp" — 42°C with a thermal bar (green/yellow/red zones at 75°C/85°C)

SECTION 3: Current Decision (most prominent card)
- Large action badge: "LÄUFT" (green, pulsing indicator)
- Decision code: "START_R1_SURPLUS_OK" in monospace
- Short explanation: "Überschuss verfügbar — PV übersteigt Hauslast um 2.4 kW"
- Rule votes: 5 pills labeled R1 R2 R3 R4 R5 — each green (ok) or red (blocking)
- "Gültig bis 10:20 Uhr" with countdown bar

SECTION 4: Two-column row
LEFT — 24h Timeline Chart:
  Line chart showing: PV (yellow), House Load (blue), Battery SoC (green dashed)
  Below chart: decision event bar — colored segments by action
  (green=START, red=STOP, gray=NOOP, orange=THROTTLE)

RIGHT — Override Panel:
  Title: "Manuelle Steuerung"
  Buttons: [STARTEN] [STOPPEN] [DROSSELN] [ABBRECHEN]
  Duration: "30 Minuten" stepper/slider
  Warning banner when R3 is active:
  "⚠ Sicherheitsstopp aktiv — Override nicht möglich"
  Recent overrides log: 3 entries with timestamp + icon

--- SECONDARY SCREENS (show as collapsed sections or tabs) ---

KPI VIEW:
- "Grid-Reduktion letzte 30 Tage: -31%" with trend sparkline
- "Flapping Rate: 0.8 starts/day"
- "Erklärungsabdeckung: 99.2%"
- "Thermische Vorfälle: 0"
- Decision latency: avg 340ms sparkline

RULE DETAIL VIEW (expandable panel):
Table with 5 rows (R1-R5):
- R1 Profitabilität | VOTE: START | Confidence 0.85 | "Surplus 2.4kW > Schwelle 1.5kW"
- R2 Autarkie      | VOTE: OK    | 0.95 | "SoC 80% über Minimum 20%"
- R3 Sicherheit    | VOTE: OK    | 1.00 | "Temp 42°C unter Limit 85°C"
- R4 Prognose      | VOTE: START | 0.70 | "Nächste Stunde: +3.1kW erwartet"
- R5 Stabilität    | VOTE: NOOP  | 0.60 | "Mindestlaufzeit erfüllt"

WHAT-IF PANEL (collapsible):
Sliders for: PV Power, House Load, Battery SoC, Miner Temp, Grid Price
Shows: "Wenn diese Werte gelten würden → Entscheidung: STOP (R2 blockiert)"

--- VISUAL NOTES ---
- Mobile: stack all cards vertically, energy flow becomes top-to-bottom
- The energy flow diagram should animate (power flow arrows/particles)
- Decision action badge should pulse when RUNNING
- Miner temperature gauge: green zone 0-75°C, yellow 75-85°C, red >85°C
- Battery SoC gauge: red zone <20% (R2 soft), dark red <10% (R2 hard stop)
- All values update every 10 seconds (polling interval)
- German language throughout UI labels

--- TECH STACK HINT ---
This will be built with FastAPI backend (REST) + lightweight JS frontend.
Keep the design implementable without heavy frameworks.

Generate 3 design variants: compact, spacious, and mobile-first.
```

---

## Nach der Generierung: Was zu prüfen ist

- [ ] Farben korrekt? Solar-Gelb, Grid-Blau, Battery-Grün, Safety-Rot
- [ ] Fonts: Monospace für Sensorwerte, Sans-serif für Labels
- [ ] R3-Sicherheitsregel visuell klar hervorgehoben?
- [ ] Keine Features entworfen, die im Backend noch nicht existieren
- [ ] design.md in Stitch vollständig (Farben, Fonts, Abstände, Komponenten)?

## Nach dem Export

1. `design.md` aus Stitch kopieren
2. Ablegen als `src/ui/design.md`
3. Claude Code Prompt:
   ```
   Implementiere src/ui/ anhand der Designvorgaben in src/ui/design.md.
   Nutze FastAPI für das Backend (src/ui/api.py existiert bereits).
   Frontend: statisches HTML/CSS/JS, keine externen Frameworks außer
   einem leichtgewichtigen Chart-Tool (z.B. Chart.js via CDN).
   ```
