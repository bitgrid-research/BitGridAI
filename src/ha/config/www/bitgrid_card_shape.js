// BitGridAI — runde Ecken für die Karten ohne sauberes Theme-Radius-Clipping
// (power-flow-card-plus, clock-weather-card, horizon-card), die eingebaute
// weather-forecast-Karte (Stunden-Streifen) und die button-card (Hamster),
// damit alle Karten gleich runden.
//
// Why: card-mod is not installed in this setup and the theme deliberately
// avoids it. The theme token --ha-card-border-radius does not visibly round
// these cards, because they paint their own background (PFCP: the flow graph,
// clock-weather-card: the forecast temperature bars) without clipping it to
// the card radius. Theme variables alone cannot enforce it, so we inject the
// radius directly into each card's shadow root. Read-only on the DOM, no
// effect on any control decision (stays out of the deterministic core).
//
// Loaded via `frontend.extra_module_url` (works regardless of the Lovelace
// resource_mode). One responsibility on purpose: shape only, no width/color
// side effects (an earlier, now-removed wide.js module handled those).

const RADIUS = "20px";
const SHAPED_CARDS = new Set([
  "POWER-FLOW-CARD-PLUS",
  "CLOCK-WEATHER-CARD",
  "HORIZON-CARD",
  // Eingebaute weather-forecast-Karte (Stunden-Streifen, type: weather-
  // forecast). Standard-ha-card erbt den Theme-Radius zwar, aber wir klemmen
  // sie hier mit, damit sie wie die anderen garantiert auf den Radius
  // geclippt wird (overflow:hidden), auch im gestreckten Grid-Cell.
  "HUI-WEATHER-FORECAST-CARD",
  // custom:button-card (Hamster-Karte). Ihr styles.card border-radius greift
  // hier nicht sichtbar (gleiches Theme-Clipping-Problem wie oben), daher hart
  // mitklemmen. Trifft auch die zwei transparenten Titel-Buttons (tl/tr), das
  // ist harmlos (kein Hintergrund, nichts zu clippen).
  "BUTTON-CARD",
]);

// ── power-flow-card-plus: Miner-Bubbles nach Leistung einfärben ──────────
// Read-only auf DOM + hass, kein Einfluss auf eine Steuerentscheidung (bleibt
// aus dem deterministischen Kern raus, wie das Radius-Clipping oben).
//
// Why: PFCP (1.15.7) kann die Knotenfarbe NICHT wertabhängig setzen (color:
// ist statisch, kein Templating). PFCP färbt jeden Individual-Knoten aber über
// die CSS-Variable --individual-<slot>-color (slot = left-top | right-top |
// left-bottom | right-bottom), konsumiert für Ring (border-color) sowie Fluss-
// Linie/-Punkte (stroke/fill). Wir überschreiben genau diese Variable per
// :host-Regel mit !important: schlägt PFCPs inline-Default und überlebt dessen
// Re-Render.
//
// Farbe richtet sich nach der Leistung (W) der jeweiligen Bubble (derselbe
// Shelly-Sensor, der auch in der Bubble angezeigt wird):
//   < 300 W → grau · 300–800 W → grün · 800–1600 W → cyan · > 1600 W → orange.
//
// Bubble→Miner wird über den gerenderten <span class="label"> (= config name)
// bestimmt und die echte Slot-Klasse aus dem DOM gelesen, NICHT über eine
// geratene Reihenfolge. Greift nichts (Karte neu, Miner aus/unter display_zero,
// hass fehlt, Wert unbekannt), bleibt die statische Fallback-Farbe aus der
// Lovelace-Config — nichts bricht.
const MINER_BUBBLES = [
  { label: "Miner 1", power: "sensor.shellyplugsg3_dcb4d9c5567c_leistung" },
  { label: "Miner 2", power: "sensor.shellyplugsg3_d0cf13d86254_leistung" },
];

// Container-Klasse → Slot (= Suffix der CSS-Variable --individual-<slot>-color).
// ACHTUNG, PFCP-Eigenheit (verifiziert am gebündelten 1.x-Source auf dem Umbrel):
// der LINKE Knoten bekommt nur `individual-top` bzw. `individual-bottom` (OHNE
// `left`!), nur die RECHTEN Knoten tragen zusätzlich `individual-right`. Die
// konsumierte Variable heißt aber immer --individual-<left|right>-<top|bottom>-
// color. Früher prüften wir stur auf die Klasse `individual-left-top` usw. und
// verfehlten damit JEDEN linken Knoten (blieb auf Fallback-Grau). Jetzt: Seite
// aus dem Vorhandensein von `individual-right`, vertikale Lage aus
// `individual-top`/`individual-bottom`.
function bubbleSlot(cl) {
  const side = cl.contains("individual-right") ? "right" : "left";
  if (cl.contains("individual-top")) return side + "-top";
  if (cl.contains("individual-bottom")) return side + "-bottom";
  return null;
}

// Leistungs-Banding (W) → Bubble-Farbe. Null = unbekannt → Fallback behalten.
function minerPowerColor(w) {
  if (w === null || Number.isNaN(w)) return null;
  if (w < 300) return "#757575";    // grau (quasi aus / sehr niedrig)
  if (w <= 800) return "#4CAF50";   // grün (300–800)
  if (w <= 1600) return "#26C6DA";  // cyan (800–1600)
  return "#F7931A";                 // orange (> 1600)
}

// Baut die :host-Override-CSS für die Miner-Bubbles einer PFCP-Instanz.
function pfcpMinerCss(node) {
  const root = node.shadowRoot;
  const hass = document.querySelector("home-assistant") &&
    document.querySelector("home-assistant").hass;
  if (!root || !hass) return "";
  const containers = root.querySelectorAll(".circle-container");
  let css = "";
  for (const b of MINER_BUBBLES) {
    const st = hass.states[b.power];
    const color = minerPowerColor(st ? parseFloat(st.state) : null);
    if (!color) continue; // unbekannt → Fallback-Farbe behalten
    let slot = null;
    containers.forEach((c) => {
      if (slot) return;
      const lbl = c.querySelector(".label");
      if (lbl && lbl.textContent.trim() === b.label) {
        slot = bubbleSlot(c.classList);
      }
    });
    if (slot) css += `:host{--individual-${slot}-color:${color}!important;}`;
  }
  return css;
}

// clock-weather-card: zwei Instanzen, getrennt nach Sektion. Welche eine
// Instanz rendert, erkennt styleCard am DOM (today- vs forecast-Element) und
// injiziert nur die passende Regel, damit clk und wek sich nicht stoeren.
//  - clk (nur Heute): das Stock-Layout (Icon links, rechts Lage/Uhr/Datum
//    gestapelt) ist gewollt. Kein Umbau mehr, nur ha-card auf volle Hoehe und
//    den Heute-Block vertikal mittig (der 25%-Slot bietet genug Platz).
//  - wek (nur Vorschau): die 5 Tageszeilen vertikal zentrieren und leicht
//    herunterzoomen, damit sie mit gleichmaessigem Padding in den Slot passen.
const CLOCK_TODAY_CSS = `
  :host{height:100%!important;}
  ha-card{height:100%!important;display:flex!important;flex-direction:column!important;justify-content:center!important;}
`;

// Today-Bereich (clk): rechts neben dem Icon drei gestapelte Zeilen:
//   -top    = Wetterlage + Temperatur ("Teils bewoelkt, 37°C")
//   -center = Uhrzeit ("18:54")
//   -bottom = Datum ("Samstag, 27.06.2026")
// Auf Wunsch alles in Hellgrau (--secondary-text-color), nur die Uhrzeit bleibt
// weiss (--primary-text-color), damit sie der dominante Wert bleibt. Wird in den
// Card-Shadow-Root UND (falls clock-weather-card-today einen eigenen Shadow-Root
// hat) zusaetzlich dort injiziert, damit die Regel die Elemente sicher erreicht.
// WICHTIG: clock-weather-card rendert diese Bereiche als eigene Custom-Element-
// TAGS (<clock-weather-card-today-left>, <...-right-wrap-top> usw.), NICHT als
// Klassen. Daher ohne Punkt selektieren (Tag-Selektor); ein '.'-Praefix matcht
// hier nichts und die Regel waere ein toter No-op.
// Zusaetzlich zwei Layout-Korrekturen fuer den jetzt frei fliessenden clk-Slot
// (kein 100vh-Lock mehr, die Karte bekommt ihre natuerliche Hoehe):
//  - Icon hart deckeln: .grow-img skaliert sonst auf 100% der (variablen) Spalte
//    und wird riesig. Fester Pixel-Deckel haelt es unabhaengig von der Kartenhoehe
//    klein UND drueckt die Kartenhoehe (vertikale Leerflaeche) mit zusammen.
//    (.grow-img IST eine Klasse am <img>, daher MIT Punkt; die today-*-Bereiche
//    sind dagegen Tags, daher ohne Punkt, siehe oben.)
//  - Uhr/Info-Gruppe horizontal mittig setzen: today-right zentriert seinen
//    Inhalt (justify-content:center) in der 65%-Spalte. So bleibt das Icon der
//    linke Anker und die Uhr sitzt rechts-mittig mit symmetrischem Weissraum,
//    statt links zu kleben (flex-start) oder am Rand zu kleben (flex-end). Passt
//    zu den Geschwisterkarten (Stunden/5-Tage/Sonnenstand), die die volle Breite
//    nutzen. Mit dem jetzt kleinen Icon entsteht dabei kein stoerender Spalt mehr.
const CLOCK_TODAY_TEXT_CSS = `
  .grow-img{max-width:104px!important;max-height:104px!important;}
  clock-weather-card-today-right{justify-content:center!important;}
  clock-weather-card-today-right-wrap-top{color:var(--secondary-text-color)!important;}
  clock-weather-card-today-right-wrap-center{color:var(--primary-text-color)!important;}
  clock-weather-card-today-right-wrap-bottom{color:var(--secondary-text-color)!important;}
`;

const CLOCK_FORECAST_CSS = `
  :host{height:100%!important;}
  ha-card{height:100%!important;display:flex!important;flex-direction:column!important;justify-content:center!important;}
  clock-weather-card-forecast{zoom:0.9!important;}
`;

// 5-Tage-Vorschau: Minimal-/Maximaltemperatur in den Zeilen kleiner, nicht fett
// und in der gleichen Farbe wie die Uhrzeiten in der Stunden-Karte (FORECAST_CSS).
const CLOCK_FORECAST_ROW_CSS = `
  .low-temp,.high-temp,.temp-low,.temp-high{font-size:0.85rem!important;font-weight:400!important;color:var(--secondary-text-color)!important;}
`;

// weather-forecast-Karte (Stunden, hrs): jede Spalte stapelt Uhrzeit (oben),
// Icon, Temperatur. Die Temperatur bleibt prominent (1.05rem, fett, weiss). Die
// Uhrzeit darueber kleiner, nicht fett und in Hellgrau (--secondary-text-color),
// damit sie ruhiger als die Temperatur wirkt. Erste Zeile je Spalte
// (.forecast > div > div:first-child) = Uhrzeit, .temp = Temperatur.
const FORECAST_CSS = `
  ha-card{zoom:0.85!important;}
  .forecast > div > div:first-child{font-size:0.85rem!important;font-weight:400!important;color:var(--secondary-text-color)!important;}
  .forecast .temp{font-size:1.05rem!important;font-weight:400!important;}
`;

// horizon-card: .horizon-card ist die Wurzel (header + graph + footer), und der
// uniforme zoom skaliert ALLES mit, auch die Labels (empirisch: 12px wurden bei
// zoom 0.2 zu ~2px). Vorteile des Ganz-Karten-zoom: Bogen bleibt voll breit, die
// Kreise rund und die Labels ueber den Bogen-Punkten ausgerichtet. Preis: die
// Schrift muss vor dem zoom entsprechend groesser gesetzt werden, damit sie nach
// dem zoom lesbar bleibt. Bei zoom 0.5 also Rohwerte ~2x: Name 26px -> ~13px,
// Wert 30px -> ~15px effektiv (= ungefaehr Energyflow-Groesse, PFCP .label 12px).
// ha-card padding = 8px Innenabstand; liegt ausserhalb des zoom, also echte 8px.
const HORIZON_CSS = `
  ha-card{padding:8px!important;}
  .horizon-card{zoom:0.5!important;}
  .horizon-card-graph{margin:0.3em 0.5em!important;}
  .horizon-card-field-name{font-size:26px!important;}
  .horizon-card-field-value{font-size:30px!important;}
`;

// Append/update a <style id> inside an arbitrary shadow root (idempotent).
function injectInto(root, id, css) {
  if (!root) return;
  let st = root.querySelector("#" + id);
  if (!st) {
    st = document.createElement("style");
    st.id = id;
    root.appendChild(st);
  }
  if (st.textContent !== css) st.textContent = css;
}

function styleCard(node) {
  if (!node.shadowRoot) return;
  let s = node.shadowRoot.querySelector("#bitgrid-card-shape");
  if (!s) {
    s = document.createElement("style");
    s.id = "bitgrid-card-shape";
    node.shadowRoot.appendChild(s);
  }
  // :host clips the whole element; ha-card rounds the themed background. Both
  // with !important so a card-internal radius reset cannot win.
  // button-cards inside a horizontal-stack are mode-selector segments — use a
  // smaller radius so they fit flush inside the outer pill container (14px).
  const inHStack = node.tagName === "BUTTON-CARD" &&
    node.getRootNode()?.host?.tagName === "HUI-HORIZONTAL-STACK-CARD";
  const r = inHStack ? "10px" : RADIUS;
  let css = `:host,ha-card{border-radius:${r}!important;overflow:hidden!important;}`;
  // clock-weather-card: zusaetzlich den Heute-Bereich stauchen, damit clk in
  // den flachen Slot passt (nur die clk-Instanz rendert ihn).
  if (node.tagName === "CLOCK-WEATHER-CARD") {
    // Instanz an ihrem gerenderten Bereich erkennen, nur passende Regel setzen.
    const sr = node.shadowRoot;
    const todayEl = sr.querySelector("clock-weather-card-today");
    if (todayEl) {
      // Farbregel in den Card-Root (deckt Light-DOM-Fall ab) und zusaetzlich in
      // den eigenen Shadow-Root des Today-Elements (deckt Shadow-DOM-Fall ab).
      css += CLOCK_TODAY_CSS + CLOCK_TODAY_TEXT_CSS;
      injectInto(todayEl.shadowRoot, "bitgrid-clock-today-text", CLOCK_TODAY_TEXT_CSS);
    }
    if (sr.querySelector("clock-weather-card-forecast")) {
      css += CLOCK_FORECAST_CSS;
      const forecastEl = sr.querySelector("clock-weather-card-forecast");
      const searchRoot = (forecastEl && forecastEl.shadowRoot) || sr;
      searchRoot.querySelectorAll("clock-weather-card-forecast-row").forEach((row) => {
        injectInto(row.shadowRoot, "bitgrid-forecast-row", CLOCK_FORECAST_ROW_CSS);
      });
    }
  }
  if (node.tagName === "HUI-WEATHER-FORECAST-CARD") css += FORECAST_CSS;
  if (node.tagName === "HORIZON-CARD") css += HORIZON_CSS;
  if (s.textContent !== css) s.textContent = css;
  // Miner-Einfärbung in einen EIGENEN <style>, da dynamisch (Modus-abhängig)
  // und unabhängig vom statischen Radius oben aktualisiert.
  if (node.tagName === "POWER-FLOW-CARD-PLUS") {
    injectInto(node.shadowRoot, "bitgrid-pfcp-miner", pfcpMinerCss(node));
  }
}

function walk(node) {
  if (!node) return;
  if (SHAPED_CARDS.has(node.tagName)) {
    styleCard(node);
    return;
  }
  if (node.shadowRoot) node.shadowRoot.querySelectorAll("*").forEach(walk);
}

function apply() {
  walk(document.querySelector("home-assistant"));
}

// Cards render asynchronously after load and on view changes; re-apply a few
// times, then on navigation and tab focus (mirrors the existing JS pattern).
let n = 0;
const t = setInterval(() => {
  apply();
  if (++n >= 20) clearInterval(t);
}, 800);

// Dauerlauf (leicht): die Miner-Bubble-Farbe muss Workmode-Wechsel über den
// ganzen Tag mitbekommen, nicht nur im 16-s-Startfenster. apply() ist idempotent
// (injectInto schreibt nur bei Änderung), die Radius-Injektionen sind dabei
// No-ops; nur die dynamische Miner-CSS aktualisiert. 5 s = flüssig genug für
// Modus-Wechsel, vernachlässigbare Last fürs Wandtablet (Qualitätsziel
// Nachhaltigkeit/Edge-Schonung).
setInterval(apply, 5000);

window.addEventListener("location-changed", () => setTimeout(apply, 500));
document.addEventListener("visibilitychange", () => setTimeout(apply, 500));
