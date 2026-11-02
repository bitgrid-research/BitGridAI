# Design-Tokens — BitGridAI Home-Assistant-Dashboard

Referenz für alle Farb- und Typo-Werte. Einmal hier nachschlagen statt durch
Kommentare in fünf Dateien zu suchen.

**Pfade:** alle Dateinamen sind relativ zu `src/ha/config/` (Ausnahme:
`scripts/deploy_ha.sh`, relativ zum Repo-Root). Der gerenderte Zustand des
Home-Tabs steht daneben in `STYLEGUIDE_HOME_V3.md`.

**Begriffsklärung:** HA-Themes sind reines YAML, geladen beim Config-Reload.
Jeder Schlüssel im Theme wird zu einer CSS-Custom-Property `--schlüssel`, die
per `var(--schlüssel)` in Dashboards, Karten und `card_mod`-CSS referenziert
wird. Farben sind kein Geheimnis (anders als IPs/Tokens) und gehören
versioniert ins Repo.

## 16.09.2026 — Konsolidierung auf ein Design

Bis hierhin trug das Projekt zwei Wertesätze: den dunklen "Glass"-Look von
v1/v2 als Theme-Wurzelwert und den v3-Look in zusätzlichen `-v3`-Tokens, die
jede Karte per zweistufigem `var(--bgai-x-v3, var(--generisch))` einzeln
nachziehen musste. v1/v2 sind seit 12.09.2026 nicht mehr in HA registriert
(`configuration.yaml`), die Doppelung war damit reiner Ballast.

Was sich geändert hat:

1. **Das Theme trägt jetzt die v3-Werte in den Standard-Tokens**
   (`--primary-text-color`, `--ha-card-background`, `--divider-color`, …).
   Kein zweiter Wertesatz mehr.
2. **363 Fallback-Ketten aufgelöst.** Sechs Tokens sind ersatzlos entfallen,
   weil sie nur den v1-Wert überschreiben sollten:
   `bgai-text-primary-v3`, `bgai-text-secondary-v3`, `bgai-divider-v3`,
   `bgai-card-bg-v3`, `bgai-text-*`, `bgai-divider-v3`. Jede Rolle hat genau
   einen Namen. `bgai-card-border-width-v3`, `bgai-card-border-v3` und
   `bgai-card-shadow-v3` sind dagegen zwingend nötig, siehe nächster Abschnitt.
3. **Sieben identische View-`:host`-Blöcke gelöscht** (je ~65 Zeilen im
   Dashboard). Ihre Farb- und Typo-Werte liegen jetzt im Theme.
4. **`--bgai-header-font-size-v3` → `--bg-fs-group-header`**, damit die
   Gruppentitelgröße in derselben Skala liegt wie alles andere.
5. **Pillen-, Zeilen- und Hover-Tokens stehen jetzt an der Wurzel.** Sie
   mussten früher literal im View stehen, weil ein Wurzelwert sonst auch in
   v1 gelandet wäre.

### Warum Karten-Chrome eigene Tokens braucht (live nachgemessen)

**Am 16.09.2026 im Browser per Computed-Style verifiziert**, nachdem eine
frühere Vermutung an dieser Stelle falsch war und beim Umbau die Outline aller
Karten gekostet hat:

HAs Karten-Wrapper `<hui-card>` setzt auf seinem Host
`--ha-card-border-width: 0` und `--ha-card-box-shadow: none`. Gemessene Kette
von oben nach unten:

```
html … hui-panel-view     border-width=1px   box-shadow=0 0 0 1px rgba(…)
hui-card                  border-width=0     box-shadow=none
button-card … ha-card     border-width=0     box-shadow=none
```

Kartenfläche (`--ha-card-background`) und Randfarbe erben normal durch, nur
Breite und Schatten werden neutralisiert. Konsequenzen:

1. Karten-Chrome läuft über `--bgai-card-border-width-v3`,
   `--bgai-card-border-v3` und `--bgai-card-shadow-v3`. Diese Namen kennt HA
   nicht und setzt sie deshalb nicht zurück.
2. `card-mod-card` im Theme stellt die neutralisierten HA-Variablen
   (`border-width`, `border-color`, `box-shadow`, `border-radius`) unterhalb
   von `hui-card` wieder her, damit auch Karten ohne eigene
   Chrome-Deklaration Rand und Schatten bekommen. Der Block setzt sie sowohl
   auf `ha-card` als auch auf `:host`, also das Kartenelement selbst: nur so
   erreicht die Reparatur Karten **ohne** `ha-card`, etwa die eigenen
   Chart-Module `bitgrid-verlauf-chart` und `bitgrid-finanz-chart`, die ihre
   Fläche in einem eigenen `div` zeichnen. Bewusst über Variablen und
   ohne `!important`: absichtlich flache Karten (Gruppentitel, Buttons im
   Stack, Wetter-Merge) deklarieren ihr eigenes `box-shadow: none` und
   behalten es.
3. **Nicht** auf `var(--ha-card-box-shadow)` oder `var(--ha-card-border-width)`
   zurückbauen.

**Offen, nicht verifiziert:** warum die früher view-scoped gesetzte, größere
Typo-Skala nie gerendert hat. Die Theme-Werte erreichen die Karten
nachweislich, die View-Variante tat es nicht. Vor einer Erhöhung der
`bg-fs-*`-Werte kurz live gegenmessen.

## Wie eine Änderung wirkt

1. Wert in `themes/bitgrid.yaml` ändern. Das ist seit der Konsolidierung
   wirklich die einzige Stelle.
2. Deployen: `bash scripts/deploy_ha.sh --restart` (siehe CLAUDE.md,
   "HA Deploy — Pflichtablauf"). Für reine Theme-Änderungen reicht auch ein
   Deploy ohne Restart plus `frontend.reload_themes`, das spart eine
   SMA-WebConnect-Session.
3. **Echten Reload der Seite erzwingen.** Eine offene Kiosk-Tab kann die alte
   Config im Speicher halten.
4. Cache-Bust bei Änderungen an `www/*.js`: `?v=`-Parameter in
   `configuration.yaml` hochzählen. Der greift erst nach einem HA-Neustart,
   weil `frontend.extra_module_url` und `lovelace.resources` nur beim Start
   gelesen werden.
5. **Wer nur eine Datei unter `views/` deployt, sieht nichts.** HA cached den
   Parse des Dashboards und prüft dafür offenbar nur den Zeitstempel der
   Wurzeldatei, nicht den der `!include`-Dateien. Am 16.09.2026 mehrfach
   reproduziert: geänderte View-Datei auf dem Server, HA lieferte per
   `lovelace/config` weiter die alte Struktur, bis `bitgrid_dashboard_v3.yaml`
   selbst angefasst wurde. Beim Deploy einzelner Views also dort eine Zeile
   ändern (oder neu starten).

## Flex-Falle in HA-Stacks

`horizontal-stack` verteilt seinen Platz zu gleichen Teilen (`flex: 1 1 0`).
Ein `card_mod` auf `#root > *` korrigiert das **nicht**: die direkten Kinder
sind `hui-card`-Elemente mit `display: contents`, das echte Flex-Item ist deren
Kind eine Ebene tiefer. Für ungleiche Spalten (Pfeil, Titel, Pfeil) deshalb
gleich `custom:layout-card` mit `grid-template-columns` nehmen, so gelöst in
`views/historie_*_cycler.yaml`.

## Flächen, Rand, Schatten

| Token | Wert | Bedeutung |
|---|---|---|
| `ha-card-background` | `#313a55` | Kartenfläche, deckend (transluzentes Glas war auf der Grastextur nicht lesbar) |
| `card-background-color` | `#313a55` | dasselbe für Komponenten, die diesen Namen lesen |
| `secondary-background-color` | `#446F94` | erhöhte Fläche |
| `ha-card-border-radius` / `-width` / `-color` (HA-eigene Komponenten) | `20px` / `1px` / `rgba(0,0,0,0.55)` | Kartenrahmen |
| `ha-card-box-shadow` | `0 0 0 1px rgba(0,0,0,0.7), 0 4px 16px rgba(0,0,0,0.5)` | 1px-Outline plus weicher Schlagschatten (Nutzer-Wunsch 12.09.2026) |
| `divider-color` | `rgba(255,255,255,0.20)` | Trennlinien |
| `lovelace-background` | `linear-gradient(150deg, #1a2e1a, #3F6B2E, #5F8F4A)` | nur Fallback hinter der Grastextur |

Der sichtbare View-Hintergrund ist nicht dieser Verlauf, sondern die
Pixel-Grastextur, die jeder View als eigene Vollbildkarte setzt
(`bitgrid_dashboard_v3.yaml`, Tag/Nacht über `sun.sun`):

| Zustand | Wert |
|---|---|
| Tag | `url('/local/bg_grass.jpg') repeat 0 0 / 800px 400px` über `linear-gradient(135deg, #5F8F4A, #3F6B2E)` |
| Nacht | `url('/local/bg_grass_night.jpg') repeat 0 0 / 800px 400px` über `linear-gradient(135deg, #16232f, #0d151c)` |

Quellbilder in `docs/media/design/`, als JPEG re-encodiert (127 KB statt
1,3 MB PNG, Qualitätsziel Nachhaltigkeit für das Wandtablet). Beim Austausch
den `?v=`-Parameter hochzählen. Die Kachel ist ein Szenen-Crop, Nahtlosigkeit
ist nicht geprüft.

## Text und Typo

| Token | Wert |
|---|---|
| `primary-text-color` | `#F5F8FC` |
| `secondary-text-color` | `#D3DEEA` |
| `disabled-text-color` | `rgba(245,248,252,0.40)` |
| `state-icon-color` | `#F5F8FC` |
| `bgai-section-label-v3` | `#FFFFFF` (Gruppentitel und Mini-Labels) |

Keine eigene `font-family`: es gilt der HA-Standardstack (Roboto).

| Token | Wert | Rolle |
|---|---|---|
| `bg-fs-hero` | `3.5rem` | aktuell ungenutzt |
| `bg-fs-title` | `1.75rem` | Karten-Headline, große Stat-Werte |
| `bg-fs-group-header` | `1.4875rem` | Gruppentitel (`group_header`-Template) |
| `bg-fs-body` | `1rem` | Fließtext |
| `bg-fs-secondary` | `0.875rem` | Sekundärtext |
| `bg-fs-label` | `0.75rem` | Mini-Labels (UPPERCASE) |

Diese Werte sind seit dem 16.09.2026 die tatsächlich gerenderten. Vorher
standen größere Werte im View, die nie ankamen. Eine Vergrößerung fürs
Wandtablet ist jetzt eine Zeilenänderung hier und wirkt sofort.

## Halo (Text auf der Grastextur)

| Token | Wert |
|---|---|
| `bgai-header-halo-v3` | `0 0 3px rgba(0,0,0,0.7)` |
| `bgai-header-icon-halo-v3` | `drop-shadow(0 0 0 rgba(0,0,0,0))`, bewusst wirkungslos |

Die harte Kontur kommt nicht aus dem Halo, sondern per
`-webkit-text-stroke: 1px #000` (Text) beziehungsweise als echter SVG-Stroke
auf dem Icon-`<path>` (`button_card_templates.yaml`, verschachteltes
`card_mod` über drei Shadow-Root-Ebenen). **Achtung:** `none` als letztes
Glied einer `filter`-Kette ist ungültiges CSS und killt die gesamte Kette,
deshalb der gültige Null-Schatten.

## Semantische Modus- und Statusfarben

| Token | Wert | Bedeutung |
|---|---|---|
| `bg-color-eco` | `#4CAF50` | Eco-Modus / positiv (= `primary-color`) |
| `bg-color-standard` | `#26C6DA` | Standard-Modus |
| `bg-color-super` | `#F7931A` | Super-Modus (Bitcoin-Orange) |
| `bg-color-reserve` | `#EF5350` | Hausreserve / Warnung / negativ |
| `bg-color-heat` | `#FF7043` | Temperatur-Warnstufe (100–109 °C Chip-Temp) |
| `bg-color-pv` | `#EFB73C` | PV/Sonne |
| `bg-color-idle` | `#757575` | aus / inaktiv / unter Schwelle |

## Datenrollen

Jede Farbe bedeutet dashboard-weit genau eine Sache (PFCP-Kreise,
Chart-Linien, Bilanz-Balken). Werte vom 12.09.2026 (Nutzer-Referenzpalette).
Das Suffix `-v3` ist historisch und bleibt nur, um einen Rename über
mehrere hundert Stellen ohne Funktionsgewinn zu vermeiden.

| Token | Wert | Bedeutung |
|---|---|---|
| `bgai-pv-v3` | `#fbb210` | PV-Ertrag |
| `bgai-mining-v3` | `#F7931A` | Mining / Bitcoin |
| `bgai-home-v3` | `#b3d804` | Zuhause / Akku |
| `bgai-grid-v3` | `#1aaccb` | Netz |
| `bgai-geraete-v3` | `#f49891` | Sonstige Geräte |
| `bgai-total-v3` | `#CBF1FD` | Summe / Gesamtprofit |
| `bgai-alarm-v3` | `#C4442C` | Alarm, unverdrahtet |
| `bgai-erklaerung-v3` | `#A2EFED` | Erklärung, unverdrahtet |

Bewusste Abweichungen im laufenden Dashboard: Hausverbrauch und der
PFCP-Haus-Ring teilen sich die Geräte-Rolle `#f49891`, der Heizstab hat mit
`#5C9EE2` eine eigene Farbe (keine Rolle trifft zu), die Miner-Bubbles sind
statisch `#757575`.

`bgai-mining-v3` und `bgai-total-v3` sind aktuell nirgends per `var()`
referenziert: die Charts tragen dieselben Werte literal, weil ApexCharts
`var()` in der `color`-Option nicht auflöst.

## View-`:host`-Overrides funktionieren nicht

Am 16.09.2026 mehrfach live geprüft: ein `card_mod`-`:host`-Block auf einem
View erreicht die Karten darunter nicht, auch nicht für projekteigene Tokens
wie `--bgai-row-bg-v3`. Die früher hier stehende Aussage, diese Namen würden
view-scoped wirken, war falsch.

**Wo ein Override hingehört, wenn er nur für einen Kontext gelten soll:** an
die Karte selbst, also in ihr eigenes `card_mod`-`:host`, in ihre
`styles.card`-Liste oder in ein eigenes button-card-Template. Beispiel unten.

## Zeilen auf einer Karte vs. Zeilen auf dem Hintergrund

`settings_row` füllt transluzent weiß (`--bgai-row-bg-v3`). Das liest sich als
leichte Erhöhung, solange die Zeile **auf** einer Karte sitzt (Tab Steuerung).
Frei auf der Grastextur (Tab Einstellungen) wirkt dieselbe Füllung schlicht
durchsichtig. Deshalb gibt es `settings_row_solid` (button_card_templates.yaml),
das nur den Hintergrund auf die Kartenfläche zieht. Immer NACH `settings_row`
listen, button-card merged Templates in Listenreihenfolge:

```yaml
template: [settings_row, settings_row_icon, settings_row_solid]
```

Dieselbe Ursache, andere Stelle: die Raumkacheln (`views/raumkachel_*.yaml`)
standen auf `rgba(255,255,255,0.045)` und wurden am 16.09.2026 auf
`var(--ha-card-background)` gezogen.

## Pillen und Einstellungszeilen

| Token | Wert |
|---|---|
| `bgai-card-bg-hover-v3` | `#446F94` |
| `bgai-pill-bg-v3` | `rgba(255,255,255,0.12)` |
| `bgai-pill-name-color-v3` | `rgba(255,255,255,0.55)` |
| `bgai-row-bg-v3` | `rgba(255,255,255,0.10)` |
| `bgai-row-name-color-v3` | `rgba(255,255,255,0.85)` |

Diese fünf standen bis zum 16.09.2026 literal in jedem View-`:host` (wo sie
nichts bewirkt haben, siehe oben) und liegen jetzt an der Wurzel. Der Hover-Ton wechselt dadurch vom alten dunklen `#233B3E` auf den
v3-Wert, das war immer die Absicht und wurde bisher vom toten View-Override
verhindert.

## Overlays: Dialoge, Menüs, Tooltips, Eingabefelder

| Token | Wert |
|---|---|
| `mdc-theme-surface`, `ha-dialog-surface-background` | `#313a55` |
| `ha-tooltip-background-color`, `paper-tooltip-background` | `#446F94` |
| Tooltip-Textfarbe | `#F5F8FC` |
| `mdc-text-field-fill-color` / `-ink-color` | `#e9ecf5` / `#1a1a2e` |

**Nicht ohne Rücksprache ändern: die Opazität.** Transluzente Overlays machten
More-Info-Dialoge unlesbar und Tooltips weiß-auf-weiß (Beschluss 10.07.2026).
Die Farbwerte wurden am 16.09.2026 vom alten Marineblau auf die Designfläche
gezogen, damit ein Dialog nicht mehr als v1-Fremdkörper aufgeht. Opak bleibt
opak.

Die hellen Eingabefelder mit dunkler Tinte sind Absicht: ohne explizite
Füllfarbe fällt MWC je nach Kontext auf Weiß oder die dunkle Surface zurück,
beides unlesbar. Falls die MDC-Tokens nicht durchdringen (Stand HA 2026.5.3
bestätigt), greift der `card-mod-root`/`card-mod-more-info`-Block im Theme,
der per `$:` bis ins eigentliche `<input>` durchsticht.

## Energiefluss: Knotenfarben und Icons

Die Icons in den Bubbles tragen seit 16.09.2026 dieselbe Farbe wie ihr Ring.
Zwei Fallen dabei, beide live verifiziert:

1. **PFCP schreibt `--icon-solar-color`, `--icon-grid-color`,
   `--icon-battery-color` und `--icon-home-color` selbst als Inline-Style** auf
   das Kartenelement (`e.style.setProperty(...)` im Bundle). Eine normale
   CSS-Regel auf demselben Element verliert dagegen, deshalb stehen diese vier
   Variablen im `card_mod` mit `!important`.
2. **Die Slots der Individual-Bubbles werden nach sichtbarer Reihenfolge
   vergeben.** Eine feste Zuordnung Slot zu Gerät ist deshalb falsch, sobald
   eine Bubble ausgeblendet ist. `www/bitgrid_card_shape.js`
   (`colorIndividualBubbles`) identifiziert jede Bubble über ihr Label, liest
   ihren tatsächlichen Slot und setzt nur dessen Variablen, inline. Miner
   zeigen dort die Stufenfarbe (Eco, Standard, Super), kein Grau.

Ausnahme Haus: sein Ring ist keine Rollenfarbe, sondern eine Herkunftsanzeige
aus Segmenten (PV-Anteil, Netz, Akku). Das Icon nutzt deshalb den Wert aus der
Haus-Config.

## Stellen, an denen `var()` nicht funktioniert

`apexcharts-card` löst CSS-Variablen in der `color`-Option nicht auf, und in
rohem Inline-SVG (per JS-Template in `custom:button-card`) ist es ebenfalls
unzuverlässig. Dort stehen literale Hex- und `rgba()`-Werte:

- `bitgrid_dashboard_v3.yaml`, Miner-Sparkline (Achsen, Gitter, Text)
- `www/bitgrid_verlauf_chart.js` und `www/bitgrid_finanz_chart.js`
  (Serienfarben, Achsen, Legende, Tooltip)

Bei einem Hell/Dunkel-Wechsel reicht ein Theme-Edit dort **nicht**: in diesen
Dateien zusätzlich nach `rgba(255,255,255,` und `rgba(0,0,0,` suchen.

## Offene Punkte

- Mehrere Home-Karten erzwingen Hintergrund, Rand und Schatten weiterhin per
  eigenem `card_mod`-Block. Seit die Wurzel korrekt ist, ist das Redundanz,
  kein Fix mehr. Entfernen erst nach einem Live-Check, nicht blind.
- Kontrast der sechs Datenrollen auf `#313a55` ist nicht systematisch geprüft.
- `bitgrid_dashboard_v1.yaml` und `bitgrid_dashboard_v2.yaml` liegen noch im
  Repo, sind aber in HA nicht registriert. `views/ki_bitsy.yaml` und
  `views/ki_beratung.yaml` hängen nur noch an v2, sind also aktuell über kein
  laufendes Dashboard erreichbar.
