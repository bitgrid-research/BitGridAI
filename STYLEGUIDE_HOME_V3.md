# Styleguide: Home-Tab (Dashboard v3)

Abgeleitet aus dem Live-Zustand des Home-Tabs (`/bitgridai-v3/home`), Stand
16.09.2026. Beschreibt die **effektiv gerenderten** Werte, nicht die
deklarierten: wo beides auseinanderfällt, steht die Ursache dabei.

Quelldateien, alle unter `src/ha/config/`: `bitgrid_dashboard_v3.yaml`
(View `home`, Zeilen 100 bis 1450), `themes/bitgrid.yaml`,
`button_card_templates.yaml` (`group_header`), `views/steuerung_quick.yaml`,
`views/energieverlauf_tag.yaml`, `views/finanz_bilanz.yaml`,
`www/bitgrid_card_shape.js`, `www/bitgrid_verlauf_chart.js`,
`www/bitgrid_finanz_chart.js`.

Token-Herkunft und Entscheidungshistorie: siehe `DESIGN.md` (diese Datei
wiederholt sie nicht, sie ergänzt die Ebene "was kommt tatsächlich an").

## 0. Woher die Werte kommen

Seit der Konsolidierung am 16.09.2026 stehen alle Designwerte an der Wurzel in
`themes/bitgrid.yaml`, es gibt keinen zweiten Wertesatz und keine View-scoped
Umleitung mehr. Das Theme ist global ausgewählt (`BitGrid v3`, mit dem alten
Namen als Alias).

**Eine Ausnahme, die man kennen muss:** Rand und Schatten der Karten laufen
nicht über `--ha-card-border-width`/`--ha-card-box-shadow`, sondern über
`--bgai-card-border-width-v3`, `--bgai-card-border-v3` und
`--bgai-card-shadow-v3`. Grund: HAs Wrapper `<hui-card>` setzt die beiden
Standardnamen für jede Karte auf `0` beziehungsweise `none` (am Live-DOM
gemessen). Wer sie auf die Standardnamen zurückbaut, verliert die Outline auf
allen Karten. Details in `DESIGN.md`.

## 1. Schriftart

| Ebene | Wert |
|---|---|
| Dashboard-weit | HA-Standardstack (`Roboto`, dann `Noto`/`sans-serif`). Das Theme setzt **keine** `font-family`, es gibt keinen `@font-face` und keine Webfont-Einbindung. |
| Charts (Verlauf, Finanzen) | explizit `Roboto, sans-serif` in jedem Style-Objekt (ApexCharts erbt sonst nicht sauber) |
| Inline-SVG (Miner-Sparkline, Tab Steuerung) | explizit `Roboto,sans-serif` als `font-family`-Attribut |

Es gibt also genau eine Schriftfamilie im gesamten Home-Tab. Gewichte im
Einsatz: 400 (normal), 600 (nur Delta-Chips), 700 (bold).

## 2. Typo-Skala, effektiv (1 rem = 16 px)

| Rolle | Deklaration | Effektiv | Gewicht | Farbe |
|---|---|---|---|---|
| Gruppentitel (`BITGRIDAI`, `WETTER`, `ENERGIEFLUSS`, `VERLAUF (HEUTE)`, `MINER`, `FINANZEN (HEUTE)`) | `--bg-fs-group-header` | **1,4875 rem = 23,8 px** | 700 | `#FFFFFF` |
| Karten-Headline (`Akku lädt zuerst`) | `--bg-fs-title`, karten-lokal auf `1.5rem` | **1,5 rem = 24 px** | 700 | `#F5F8FC` |
| Stat-Wert (Blockzeit, Balance, Kurs) | dito | **24 px** | 700 | `#F5F8FC` |
| Erklärtext / Fließtext | `--bg-fs-body` | **1 rem = 16 px** | 400 | `#D3DEEA` |
| Stat-Label (`BLOCKZEIT`, `BALANCE`, `KURS`) | `--bg-fs-label` | **0,75 rem = 12 px** | 400, uppercase, `letter-spacing: .06em` | `#FFFFFF` |
| Stat-Unterzeile (`≈ 222,68 €`) | `--bg-fs-secondary` | **0,875 rem = 14 px** | 400, `opacity: .7` | `#D3DEEA` |
| Einheit-Suffix (`€`, `SATs`) | `0.6em` der Wertzeile | **14,4 px** | 400, `opacity: .7` | `#D3DEEA` |
| Delta-Chip auf der Wertzeile (`(+1.682)`) | `0.5em` | **12 px** | 600 | grün `#4CAF50` / rot `#EF5350` |
| Delta-Chip auf der Unterzeile (`(+1,11 €)`) | `0.72em` | **10,1 px** | 600 | dito |
| Uhr (`13:10`) | fest | **4,25 rem = 68 px** | 400 (explizit entfettet) | `#F5F8FC` |
| Wetterlage + Datum | `--bg-fs-body` | **16 px** | 700 | `#F5F8FC` |
| Stundenstreifen: Uhrzeit | `--bg-fs-body` | **16 px** | 400 | `#F5F8FC` (karten-lokal gesetzt) |
| Stundenstreifen: Temperatur | `--bg-fs-body` | **16 px** | 400 | `--primary-text-color` = `#f3f5fb` |
| Energiefluss: Knotennamen (`PV`, `Netz`, `Haus`) | fest | **14 px** | 400 | `#F5F8FC` |
| Energiefluss: Werte (`4,2 kW`, `43 %`) | fest | **14 px** | 700 | `#F5F8FC` |
| Chart: Achsentitel + Achsenbeschriftung | fest | **17 px** | 400 | achsenweise eingefärbt, siehe 6. |
| Chart: eigene HTML-Legende | fest | **16 px** | 400 | `#FFFFFF`, Farbpunkt 12 px |
| Chart: Annotation `jetzt` | fest | **10 px** | 400 | `rgba(255,255,255,.8)` |
| Chart-Tooltip: Kopf / Zeilen | fest | **15 px / 14 px** | 700 / 400 und 700 | `#FFFFFF` |
| Finanz-Chart: Balkenwert | fest | **16 px** | 700 | Balkenfarbe |
| Finanz-Chart: Kategorie / Y-Achse | fest | **14 px / 15 px** | 400 | Balkenfarbe / `#FFFFFF` |
| Miner-Kartentitel (`Miner #1`) | card_mod `!important` | **1,75 rem = 28 px** | 700 | `#F5F8FC` |
| Miner-Buttonname (`Eco`, `Standard`, `Super`, `Betrieb`) | fest | **1,125 rem = 18 px** | 700 aktiv / 400 inaktiv | primär aktiv / sekundär inaktiv |
| Miner-Buttonstatus (Zweitzeile) | card_mod `!important` | **1 rem = 16 px** | 400 | `#D3DEEA` |

Nicht im Home-Tab verwendet: `--bg-fs-hero` (3,5 rem). Die große Uhr nutzt
bewusst einen eigenen Festwert statt dieses Tokens.

## 3. Farben

### Flächen
| Element | Wert |
|---|---|
| Karte | `#313a55` (Token `--ha-card-background`) |
| View-Hintergrund, Tag | `url('/local/bg_grass.jpg') repeat 0 0 / 800px 400px`, darunter `linear-gradient(135deg, #5F8F4A, #3F6B2E)` |
| View-Hintergrund, Nacht | `url('/local/bg_grass_night.jpg') repeat 0 0 / 800px 400px`, darunter `linear-gradient(135deg, #16232f, #0d151c)` |
| Umschaltung Tag/Nacht | Jinja auf `sun.sun` in einer unsichtbaren `position:fixed`-Karte mit `z-index:-1` (reaktiv, kein Reload) |

### Text
| Rolle | Wert |
|---|---|
| Text primär | `#F5F8FC` |
| Text sekundär | `#D3DEEA` |
| Sektionslabel (Gruppentitel, Mini-Labels) | `#FFFFFF` |

### Datenrollen (eine Farbe = eine Bedeutung)
| Rolle | Token | Wert |
|---|---|---|
| PV-Ertrag | `--bgai-pv-v3` | `#fbb210` |
| Mining / Bitcoin | `--bgai-mining-v3` | `#F7931A` |
| Zuhause / Akku | `--bgai-home-v3` | `#b3d804` |
| Netz | `--bgai-grid-v3` | `#1aaccb` |
| Sonstige Geräte | `--bgai-geraete-v3` | `#f49891` |
| Summe / Gesamtprofit | `--bgai-total-v3` | `#CBF1FD` |
| Alarm | `--bgai-alarm-v3` | `#C4442C`, unverdrahtet |
| Erklärung | `--bgai-erklaerung-v3` | `#A2EFED`, unverdrahtet |

**Bekannte Abweichungen von der Rollenlogik im Home-Tab** (bewusst, nicht als
Fehler behandeln, aber auch nicht unbemerkt weiterkopieren):
- Hausverbrauch und PFCP-Haus-Ring nutzen die Geräte-Rolle `#f49891`.
- Heizstab `#5C9EE2` (keine der sechs Rollen trifft zu).
- Miner-Bubbles statisch `#757575`. Die frühere leistungsabhängige Färbung
  wurde aus `bitgrid_card_shape.js` entfernt; der gegenteilige Kommentar im
  Dashboard-YAML ist veraltet.
- Statusfarben in Chips und Buttons kommen weiter aus der globalen Skala
  `--bg-color-eco/-standard/-super/-reserve/-heat/-pv/-idle`.

## 4. Kartenanatomie

| Eigenschaft | Wert |
|---|---|
| Radius | `20px`, zusätzlich hart erzwungen von `bitgrid_card_shape.js` (Custom-Cards clippen sonst nicht). Innerhalb eines `horizontal-stack`: `10px`. Miner-Buttons: `0`. |
| Rand | `1px solid rgba(0,0,0,0.55)` (`--ha-card-border-color`) |
| Schatten / Outline | `0 0 0 1px rgba(0,0,0,0.7), 0 4px 16px rgba(0,0,0,0.5)` (`--ha-card-box-shadow`) |
| Divider | `2px`, Verlauf `transparent → rgba(255,255,255,0.20) @15% … @85% → transparent`, senkrecht wie waagerecht dasselbe Muster |
| Padding BitGridAI-Karte | `12px` |
| Padding Energiefluss | `12px` (überschreibt HA-Default 16px) |
| Padding Wetter (Uhr) | `4px 12px 12px 12px` (oben bewusst knapp) |
| Padding Stundenstreifen | `12px` |
| Padding Verlauf / Finanzen | `12px` |
| Padding Miner-Quick | `8px 14px 14px 14px` |
| Feste Höhen | BitGridAI-Karte `238px`, Miner-Header `68px`, Miner-Modusbutton `80px`, Miner-Funktionsbutton `122px`, Verlauf-Chart `250px`, Finanz-Chart `281px` |

Wichtig: Hintergrund, Rand und Schatten stehen bei jeder Home-Karte
**explizit im eigenen `card_mod`-Block**. Eine neue Karte ohne diesen Block
fällt auf das dunkle v1-Glas zurück und steht als dunkler Fleck im Layout.

## 5. Layout

- 2 Spalten `minmax(0, 1fr) minmax(0, 1fr)`, 3 Zeilen `auto`,
  `grid-gap: 14px`, `padding: 14px`, `align-items: stretch`.
- Paarbildung je Zeile: BitGridAI und Wetter, Energiefluss und Verlauf,
  Miner und Finanzen. Jedes Paar teilt sich eine Grid-Zeile und damit die Höhe.
- Kein `zoom` mehr im Home-Tab (bewusst entfernt). Die Seite scrollt, statt
  sich auf Viewporthöhe zu klemmen.
- Gruppentitel sind eigene Karten **innerhalb** des jeweiligen
  `vertical-stack`, direkt über der Karte, die sie beschriften.

## 6. Wiederkehrende Bausteine

### Gruppentitel (`template: group_header`)
Icon links (24 px) plus Text, Grid `min-content 1fr`, `padding: 4px 4px 0`,
Text mit `padding-left: 10px`, `letter-spacing: 0.07em`, uppercase.
Lesbarkeit gegen die Grastextur über zwei Mechanismen:
- Text: `text-shadow: 0 0 3px rgba(0,0,0,0.7)` plus
  `-webkit-text-stroke: 1px #000000` mit `paint-order: stroke fill`.
- Icon: echter SVG-Stroke `1.5px #000000` per verschachteltem card-mod
  (drei Shadow-Root-Ebenen tief). Der weiche Icon-Halo ist absichtlich auf
  einen wirkungslosen `drop-shadow(0 0 0 …)` gesetzt, **nicht** auf `none`:
  `none` als letztes Glied einer `filter`-Kette ist ungültig und hätte die
  gesamte Kette gekillt.

### Halo-Regel (im Home-Tab durchgängig)
| Kontext | Wert |
|---|---|
| Standardtext auf Karte | `--bgai-header-halo-v3` = `0 0 3px rgba(0,0,0,0.7)` |
| Energiefluss, lokal abgeschwächt | `0 0 2px rgba(0,0,0,.85)` zweilagig |
| Chart-Text und Legende | `0 0 4px rgba(0,0,0,.9)` zweilagig |
| Legendenpunkte | gleiche Werte als `box-shadow` statt `filter` |

Nicht auf den vollen Hamster-Halo hochsetzen, ohne dass der Nutzer es
ausdrücklich verlangt (zweimal abgelehnt).

### Statuskarte BitGridAI
Avatar links (`max-width: 121px`, rund, `drop-shadow(0 0 1px rgba(0,0,0,.6))`),
senkrechter Divider, Text rechts (`flex: 2`). Fußleiste mit drei Spalten
(Blockzeit, Balance, Kurs), getrennt durch denselben Divider, oben abgesetzt
durch einen waagerechten Gradient-Strich. Jede Spalte rendert **immer drei
Zeilen** (Label, Wert, Unterzeile, leer als `&nbsp;`), damit alle Wertzeilen
auf gleicher Höhe sitzen.
Block-Tick: bei neuem Block 60 s Animation in `--bg-color-super` mit
negativem `animation-delay` in Höhe des Blockalters, damit Re-Renders die
Animation fortsetzen statt neu zu starten.

### Energiefluss (power-flow-card-plus)
Ringe `border-width: 3px` (Ausnahme: Haus bleibt beim Default, sonst bricht
das Segment-Overlay), Flusslinien `stroke-width: 1.5`,
Linien-`drop-shadow(0 0 0.75px rgba(0,0,0,.75))`.

### Verlauf (heute)
`area`, `curve: smooth`, `stroke.width: 2.5`, chartweiter
`dropShadow(blur 3, opacity .5)`, feste Y-Skala 0 bis 10 kW in 2er-Schritten,
X-Achse als `category` mit 3-Stunden-Schritten (`datetime` scheidet wegen
ApexCharts-Issue 164 aus).

| Serie | Farbe | Flächen-Opazität | Dash |
|---|---|---|---|
| PV-Leistung | `#fbb210` | 0,35 | 6 |
| Netzbezug | `#1aaccb` | 0,25 | 4 |
| Batteriestand (rechte Achse) | `#b3d804` | 0,14 | 0 |
| Hausverbrauch | `#f49891` | 0,25 | 2 |
| Miner-Verbrauch | `#F7931A` | 0,25 | 8 |

Linke Achse trägt die PV-Farbe, rechte die Batteriestand-Farbe, X-Achse weiß.
Legende ist bewusst selbst gebaut (HTML-Div), weil ApexCharts seine eigene in
ein `foreignObject` rendert und dort kein zuverlässiges Flex-Layout hat.

### Finanzen (heute)
Vier Balken: Ersparnis `#b3d804`, Mining-Ertrag `#F7931A`, Netzbezugskosten
`#1aaccb` (negativ), Gesamtprofit `#CBF1FD`.

## 7. Regeln für neue Karten im Home-Tab

1. Farben über die Standardnamen beziehen (`var(--primary-text-color)`,
   `var(--ha-card-background)`, …). Projekt-eigene Tokens nur dort, wo HA
   keinen Standardnamen hat: Datenrollen, Halo, Pillen, Typo-Skala.
2. Hintergrund, Rand, Schatten und Radius explizit im eigenen `card_mod`
   setzen, nicht auf Vererbung hoffen.
3. Schriftgrößen aus der Skala in Abschnitt 2 nehmen. Ein neuer Festwert
   braucht eine Begründung im Kommentar.
4. Neue Karte mit Text auf Kartenfläche bekommt den Standard-Halo.
5. `var()` funktioniert nicht in ApexCharts-`color`-Optionen und nicht in
   rohem SVG. Dort literale Hex-Werte setzen und die Stelle hier vermerken.
6. Nach Änderungen an `www/*.js` den `?v=`-Parameter in `configuration.yaml`
   hochzählen, sonst zeigt das Wandtablet die gecachte Version.

## 8. Offene Punkte

- Mehrere Karten erzwingen Hintergrund, Rand und Schatten weiterhin per
  eigenem `card_mod`-Block. Seit die Theme-Wurzel korrekt ist, ist das
  Redundanz, kein Fix mehr. Entfernen erst nach einem Live-Check.
- Kontrast der sechs Datenrollen auf `#313a55` ist nicht systematisch geprüft.
- Der Hover-Ton der Pillen wechselt mit der Konsolidierung vom alten dunklen
  `#233B3E` auf `#446F94`. Das war die ursprüngliche v3-Absicht, ist aber die
  einzige unbeabsichtigte Optikänderung des Umbaus und live noch ungesehen.
