# Google Stitch + Claude Code – Workflow

Dieses Verzeichnis dokumentiert den Workflow zur UI-Gestaltung von BitGridAI
mit **Google Stitch** und der Umsetzung durch **Claude Code**.

---

## Das Paradigma: design.md

Google Stitch generiert automatisch eine `design.md` — ein Markdown-Dokument,
das das komplette Design-System beschreibt:
Farben, Typografie, Abstände, Komponenten, Dos & Don'ts.

Diese Datei ist die Brücke zwischen Design und Code.
Claude Code liest sie und implementiert das UI konsistent — ohne manuelle Übergabe.

```
Stitch (Prompt)
  → Designs auf Canvas
  → Design System (automatisch generiert)
  → design.md (Markdown-Export)
      → Option A: Copy/Paste in src/ui/design.md
      → Option B: Stitch MCP → Claude Code liest direkt aus Stitch
```

---

## Workflow Schritt für Schritt

### 1. Design in Stitch erstellen

- Auf [stitch.withgoogle.com](https://stitch.withgoogle.com) einloggen
- Prompt eingeben (siehe [DESIGN.md](./DESIGN.md))
- Optional: Screenshots des bestehenden UI mitgeben
- Stitch generiert Screens + Design System automatisch

### 2. Design System anpassen

- In Stitch: rechts → **Design Systems** → eigenes System öffnen
- Farben, Fonts, Komponenten nach Bedarf anpassen
- Stitch updated die `design.md` automatisch bei jeder Änderung

### 3. design.md exportieren

**Option A — Manuell (einfach, kein API-Key nötig):**
```
Stitch → Design Systems → design.md → Kopieren
→ Einfügen als: src/ui/design.md
```

**Option B — Stitch MCP (direkter Zugriff für Claude Code):**
```bash
# API-Key in Stitch: Settings → API → Key erstellen
# MCP in Claude Code einrichten:
claude mcp add stitch --api-key DEIN_API_KEY
```
→ Neue Claude Code Session starten
→ Claude Code sieht Stitch-Verbindung und kann Frames direkt lesen

### 4. UI mit Claude Code implementieren

**Mit design.md (Option A):**
```
Erstelle das Web-UI für src/ui/ anhand der Designvorgaben in src/ui/design.md.
Halte dich exakt an Farben, Typografie und Komponentenstile aus der Datei.
```

**Mit Stitch MCP (Option B):**
```
Aktualisiere das Dashboard-Screen so, dass es dem
"BitGridAI Dashboard Desktop"-Frame in Google Stitch entspricht.
Nutze dazu das Stitch MCP.
```

---

## Wichtige Hinweise aus der Praxis

- **Fonts:** Stitch wählt Fonts, die nicht immer korrekt geladen werden.
  Explizit prüfen ob CDN-Link in HTML vorhanden ist.

- **Feature-Drift:** Stitch erfindet manchmal Features, die im Code nicht existieren
  (z.B. "Recent Drafts"-Sektion). Vor der Implementierung abgleichen.

- **MCP vs. Copy/Paste:** MCP liefert HTML/CSS direkt aus Stitch-Frames —
  das ist präziser als nur die design.md. Für Layout-Details MCP bevorzugen.

- **design.md iterieren:** Claude Code kann die design.md erweitern,
  wenn neue Komponenten gebaut werden:
  ```
  Ergänze src/ui/design.md um die neuen Komponenten,
  die du gerade implementiert hast.
  ```

---

## Dateien in diesem Verzeichnis

| Datei | Inhalt |
|-------|--------|
| `README.md` | Dieser Workflow-Guide |
| `DESIGN.md` | Stitch-Prompt für BitGridAI + Designvorgaben |

Die generierte `design.md` aus Stitch kommt nach: `src/ui/design.md`

---

> Mehr zum KI-Tooling-Setup: [COLLABORATION.md](../COLLABORATION.md)
