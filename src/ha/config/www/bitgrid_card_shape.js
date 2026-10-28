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
  // apexcharts-card (Wochen-Verlauf, Demo-Home-Tab): malt seinen Hintergrund
  // ebenfalls ungeclippt, gleiches Muster wie PFCP/clock-weather-card oben.
  "APEXCHARTS-CARD",
]);

// 12.09.2026, Nutzer-Wunsch "raus mit dem Skript! nichts einfaerben, auch
// nicht die Miner": die bisherige leistungsabhaengige Miner-Bubble-Faerbung
// (Idle-Grau/Eco-Gruen/Standard-Cyan/Super-Orange ueber --individual-<slot>-
// color) ist komplett entfernt — trotz zweier Fix-Versuche (Variable aufs
// Element statt :host, dann Idle-Stufe ganz weggelassen) blieb die Geraete-
// Bubble grau ueberlagert, Root Cause nie gefunden. Alle Individual-Bubbles
// (Miner #1/#2, Heizstab, Geraete) zeigen jetzt nur noch ihre statische
// Farbe aus der Lovelace-Config (bitgrid_dashboard_v3.yaml, individual.
// color), keine dynamische Einfaerbung mehr.

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
// 12.09.2026, Nutzer-Wunsch "obere Karte (Heute-Icon) auch mit den Pixel-Art-
// PNGs": .grow-img ist bereits ein echtes <img>-Tag (clock-weather-card
// rendert <clock-weather-card-today-left><img class="grow-img" src=...></...>,
// s. github.com/pkissling/clock-weather-card, renderToday()/toIcon()) — daher
// hier nur src austauschen (setTodayIcon() unten), keine Container-Ersetzung
// wie bei der eingebauten weather-forecast-Karte noetig. object-fit/pixelated
// gilt einheitlich fuer jedes Icon, das wir per PNG ersetzen (Nutzer-Vorgabe).
const CLOCK_TODAY_TEXT_CSS = `
  .grow-img{max-width:114px!important;max-height:114px!important;object-fit:contain!important;image-rendering:pixelated!important;image-rendering:crisp-edges!important;filter:drop-shadow(0 0 1px rgba(0,0,0,.6))!important;}
  clock-weather-card-today-right{justify-content:center!important;}
  clock-weather-card-today-right-wrap-top{color:var(--secondary-text-color)!important;}
  clock-weather-card-today-right-wrap-center{color:var(--primary-text-color)!important;}
  clock-weather-card-today-right-wrap-bottom{color:var(--secondary-text-color)!important;}
`;

// 5-Tage-Vorschau: Zeilen bestehen aus <forecast-text>-Tags (Tag, Min-Temp,
// Max-Temp) direkt im Haupt-Shadow-Root der Karte — die Rows haben KEINEN
// eigenen Shadow-Root, daher muss die Farbregel hier hinein. Erste
// forecast-text je Zeile = Wochentag (bleibt), die uebrigen = Min/Max-
// Temperatur, in Hellgrau wie die Uhrzeiten der Stunden-Karte (FORECAST_CSS).
const CLOCK_FORECAST_CSS = `
  :host{height:100%!important;}
  ha-card{height:100%!important;display:flex!important;flex-direction:column!important;justify-content:center!important;}
  clock-weather-card-forecast{zoom:0.81!important;}
  clock-weather-card-forecast-row forecast-text:not(:first-of-type){color:var(--secondary-text-color)!important;}
`;

// weather-forecast-Karte (Stunden, hrs): jede Spalte stapelt bisher Uhrzeit
// (oben), Icon, Temperatur senkrecht gestapelt. Erste Zeile je Spalte
// (.forecast > div > div:first-child) = Uhrzeit, .temp = Temperatur — DAS SIND
// DIE EINZIGEN ECHTEN SELEKTOREN: die eingebaute Karte vergibt fuer die
// Uhrzeit KEINE Klasse (nur Positions-Selektor moeglich), nur .temp und
// .forecast-image-icon existieren als echte Klassen. Ein card_mod-Versuch mit
// erfundenem .forecast-item-label/.forecast-item-Wrapper (bitgrid_dashboard_
// v3.yaml, seit entfernt) traf deshalb nie ein echtes Element — dieselbe
// Erkenntnis wie bei clock-weather-card-today-right-wrap-top/-bottom oben
// (Farbe wirkte nur ueber den --secondary-text-color-Umweg, nie direkt).
//
// 12.09.2026, Nutzer-Wunsch "Uhrzeit nach unten in die gleiche Reihe wie
// Temperatur ziehen, mit Trenner dazwischen": von reinem Flex-Stapel auf ein
// 2x2-Grid pro Spalte umgebaut (Icon oben ueber volle Breite, Uhrzeit+Temperatur
// nebeneinander in der unteren Zeile) — dieselbe display:contents/Grid-Technik
// wie beim Today-Bereich der Uhr-Karte (styles.ts kennt kein natives Reordering,
// s. bitgrid_dashboard_v3.yaml). Groesse/Farbe jetzt ueber dieselben Tokens wie
// die uebrige v3-Typo-Skala (--bg-fs-body/--secondary-/--primary-text-color)
// statt freihaendiger rem-Werte — Custom Properties durchqueren den Shadow-Root
// problemlos, sind View-weit gesetzt (bitgrid_dashboard_v3.yaml) und muessen
// hier nur referenziert werden. Temperatur zunaechst auf --bg-fs-title (wie der
// grosse Stat-Wert der Hamster-Karte) versucht, Nutzer-Feedback direkt danach:
// zu gross im Verhaeltnis zur Uhrzeit — beide jetzt einheitlich --bg-fs-body,
// Trenner-Abstand nach dem Punkt (margin-right) auf 0 (Nutzer-Wunsch).
// 26.09.2026, Nutzer-Wunsch "Uhrzeit/Temperatur im Grauton der Hamster-
// Erklaerung": Label, Temperatur und Trenner jetzt alle auf
// --secondary-text-color, exakt dasselbe Token wie der Erklaertext unter der
// Hamster-Ueberschrift (bitgrid_dashboard_v3.yaml, BitGridAI-Karte, "sub").
// Ein Zwischenschritt mit --disabled-text-color (40 % Deckkraft) war live zu
// dunkel. Greift nur, weil der fruehere lokale Override
// --secondary-text-color:#F5F8FC am :host der weather-forecast-Karte
// (bitgrid_dashboard_v3.yaml) entfernt wurde, sonst loeste das Token dort
// weiter auf Weiss auf.
const FORECAST_CSS = `
  .forecast > div{display:grid!important;height:100%!important;grid-template-columns:auto auto;grid-template-rows:auto auto;grid-template-areas:"icon icon" "label temp";justify-items:center!important;align-items:center!important;justify-content:center!important;align-content:center!important;column-gap:6px!important;}
  .forecast > div > div:first-child{grid-area:label;font-size:var(--bg-fs-body)!important;font-weight:normal!important;color:var(--secondary-text-color)!important;text-shadow:var(--bgai-header-halo-v3)!important;}
  .forecast-image-icon{grid-area:icon;--bgai-forecast-icon-size-v3:44px;}
  .forecast-image-icon > img.bgai-weather-png{width:var(--bgai-forecast-icon-size-v3);height:var(--bgai-forecast-icon-size-v3);object-fit:contain;image-rendering:pixelated;image-rendering:crisp-edges;display:block;filter:drop-shadow(0 0 1px rgba(0,0,0,.6));}
  .forecast .temp{grid-area:temp;font-size:var(--bg-fs-body)!important;font-weight:normal!important;color:var(--secondary-text-color)!important;text-shadow:var(--bgai-header-halo-v3)!important;}
  .forecast .temp::before{content:"/";margin-right:0;font-weight:700;color:var(--secondary-text-color);}
`;

// 12.09.2026, Nutzer-Wunsch "eigene Pixel-Art-PNGs statt der eingebauten
// Wetter-Icons": .forecast-image-icon ist der einzige echte Icon-Container
// (s. Kommentar oben) — sein bisheriges Kind (von getWeatherStateIcon()
// gerendert, Form je nach HA-Version SVG oder Custom-Element) wird durch ein
// <img> ersetzt. Groesse ueber die neue, selbst definierte Variable
// --bgai-forecast-icon-size-v3 (s. FORECAST_CSS oben) statt ueber die
// eingebaute --forecast-icon-size: die aktuell installierte HA-Version
// rendert die aeltere .forecast > div-Struktur (kein .forecast-item), ob die
// neuere --forecast-icon-size-Variable dort ueberhaupt existiert ist deshalb
// nicht sicher — mit einer eigenen, selbst gesetzten Variable ist die Groesse
// unabhaengig davon garantiert und bleibt trotzdem die vom Nutzer gewuenschte
// zentrale Stellschraube (40px = angenaeherte bisherige Icongroesse).
//
// PNG-Dateien liegen unter /config/www/weather-icons/ (deploybar ueber
// www/, s. CLAUDE.md „HA Deploy"), erreichbar unter /local/weather-icons/.
// Explizite Zuordnungstabelle statt Text-Heuristik ("rain"/"snow" erraten),
// deckt alle 15 offiziellen HA-Wetter-Conditions ab (home-assistant/core,
// weather/const.py ATTR_CONDITION_*, verifiziert 12.09.2026).
const WEATHER_ICON_BASE = "/local/weather-icons/";
const WEATHER_ICON_MAP = {
  "sunny": "sunny.png",
  "clear-night": "clear-night.png",
  "cloudy": "cloudy.png",
  "fog": "fog.png",
  "hail": "hail.png",
  "lightning": "lightning.png",
  "lightning-rainy": "lightning-rainy.png",
  "partlycloudy": "partlycloudy.png",
  "pouring": "pouring.png",
  "rainy": "rainy.png",
  "snowy": "snowy.png",
  "snowy-rainy": "snowy-rainy.png",
  "windy": "windy.png",
  "windy-variant": "windy-variant.png",
  "exceptional": "exceptional.png",
};
const WEATHER_ICON_FALLBACK = "exceptional.png";
// Entity, die alle drei weather-forecast-Karten im Repo tatsaechlich zeigen
// (bitgrid_dashboard_v2/v3.yaml, views/miner_stats.yaml — geprueft 12.09.2026,
// alle drei: entity weather.forecast_home, forecast_type hourly).
const WEATHER_ENTITY = "weather.forecast_home";
// /local/ liefert Cache-Control: public, max-age=2678400 (31 Tage, verifiziert
// 12.09.2026) — auch fuer einen 404 (der allererste Deploy-Versuch traf die
// PNGs noch nicht, s. bekannter Bug: inkrementelles Deploy uebernimmt neue
// UNTRACKED VERZEICHNISSE nicht, nur einzelne Dateien). Ohne Cache-Bust haengt
// ein Tablet, das die Karte in genau diesem Fenster geladen hat, an einem
// gecachten 404 fest. Versionsstring in der URL erzwingt eine neue Cache-
// Identitaet; bei kuenftigem Icon-Tausch (gleicher Dateiname, neuer Inhalt)
// hier hochzaehlen.
const WEATHER_ICON_VERSION = "5";

function weatherIconUrl(condition) {
  const file = WEATHER_ICON_MAP[condition] || WEATHER_ICON_FALLBACK;
  return WEATHER_ICON_BASE + file + "?v=" + WEATHER_ICON_VERSION;
}

// clock-weather-card, Today-Icon: braucht keinen Forecast-Call, die "echte
// Condition" ist hier einfach der aktuelle Zustand der Wetter-Entity selbst
// (hass.states[...].state) — dieselbe Quelle, die die Karte intern fuer ihr
// eigenes toIcon(weatherState, ...) liest. .grow-img existiert bereits als
// <img>, daher genuegt ein src-Tausch (kein Container-Rebuild wie bei der
// eingebauten weather-forecast-Karte). Sucht defensiv in BEIDEN moeglichen
// Shadow-Root-Ebenen (dasselbe Unsicherheits-Muster wie injectInto fuer
// CLOCK_TODAY_TEXT_CSS oben: -left koennte Light-DOM-Kind des Haupt-Shadow-
// Roots oder ein eigener Shadow-Root sein).
function applyTodayIcon(node, todayEl, hass) {
  if (!hass) return;
  // 13.10.2026: Bedingung aus der Entity, die die Karte TATSAECHLICH zeigt
  // (clock-weather-card haelt ihre Konfiguration in .config). Vorher fest
  // WEATHER_ENTITY: zeigte die Karte eine andere Entity (Lab-Demo:
  // weather.bitgrid_demo_weather = "sunny"), stand ein Regen-Icon unter
  // "Sonnig, 26 °C". Fallback bleibt WEATHER_ENTITY.
  const cfg = node.config || node._config || {};
  const st = hass.states[cfg.entity || WEATHER_ENTITY];
  const condition = st && st.state;
  const sel = "clock-weather-card-today-left img.grow-img";
  const img =
    (todayEl.shadowRoot && todayEl.shadowRoot.querySelector(sel)) ||
    node.shadowRoot.querySelector(sel);
  if (!img) return;
  if (img.dataset.condition !== String(condition)) {
    img.dataset.condition = String(condition);
    img.src = weatherIconUrl(condition);
  }
}

// Der Replay-Neustart per Tipp aufs Heute-Wetter-Icon (15.10.2026) ist am
// 17.10.2026 entfernt (Nutzer: "brauch man nicht", die Sim-Steuerung kann das):
// er galt auch auf dem Probanden-Tablet, ein Tipp setzte den Reiz zurueck.

// 15.10.2026, Lab-Replay: Uhrzeit und Datum der clock-weather-card folgen der
// Sim-Uhr, solange simulation_mode an ist UND das Lab-Profil existiert
// (sensor.lab_sim_profile = Sim-Datum, sensor.lab_sim_clock = HH:MM; beide nur
// im Lab, in Prod greift der Patch also nie). Die Karte haelt die Zeit in der
// Lit-Eigenschaft currentDate (Luxon-DateTime, setzt sie jede Sekunde neu und
// formatiert selbst ueber time_pattern/date_pattern). Statt Text im DOM zu
// ueberschreiben (wuerde jede Sekunde zurueckspringen) liefert ein eigener
// Getter auf der Instanz im Sim eine auf Sim-Datum/-Uhrzeit gesetzte Kopie;
// der Setter bleibt der originale (Lit-Rendering unveraendert).
// Zuletzt gesehener Sim-Block und wann er im Browser ankam (s. simNowParts).
let simBlockSeen = { step: null, at: 0 };
// Zuletzt gesehener Wechsel "angehalten -> laeuft" (Play) im Browser und die
// angehaltene Minute, ab der weitergezaehlt wird. running=null: Zustand beim
// Laden der Seite unbekannt, dann gibt es keinen Play-Anker.
let simRunSeen = { running: null, at: 0, minute: null };

function simNowParts(hass) {
  if (!hass || hass.states?.["input_boolean.simulation_mode"]?.state !== "on") return null;
  const st = hass.states;
  const day = st["sensor.lab_sim_profile"]?.state || "";
  const clk = st["sensor.lab_sim_clock"]?.state || "";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !/^\d{2}:\d{2}$/.test(clk)) return null;
  // Block-Uhr (10-min-Raster), gilt bei angehaltenem Replay.
  let minute = +clk.slice(0, 2) * 60 + +clk.slice(3, 5);
  // 15.10.2026, Nutzer-Wunsch "Minute fuer Minute statt 10-min-Spruengen":
  // laeuft das Replay, zaehlt die Uhr ab dem Moment, in dem der aktuelle
  // 10-min-Block im Browser ankommt (10 Sim-Minuten je lab_demo_block_s
  // Sekunden). Bewusst NICHT gegen die HA-Startzeit gerechnet: schon wenige
  // Sekunden Versatz zwischen Browser- und HA-Uhr (plus Schaltverzoegerung)
  // liessen die Uhr live gemessen 3-4 Sim-Minuten vorlaufen. Begrenzt auf den
  // Block; im Startblock ab der Startminute (05:21).
  const step = parseInt(st["input_number.sim_step"]?.state, 10);
  if (step !== simBlockSeen.step) simBlockSeen = { step, at: Date.now() };
  const running = st["input_boolean.lab_demo_running"]?.state === "on";
  if (running !== simRunSeen.running) {
    const resumed = running && simRunSeen.running === false;
    simRunSeen = {
      running, at: Date.now(),
      minute: resumed ? parseInt(st["input_number.lab_sim_minute"]?.state, 10) : null,
    };
  }
  if (running) {
    const bs = parseFloat(st["input_number.lab_demo_block_s"]?.state);
    const m0 = parseInt(st["input_number.lab_demo_start_minute"]?.state, 10);
    const first = !Number.isNaN(m0) && Math.floor(m0 / 10) * 10 === minute ? m0 - minute : 0;
    if (bs > 0) {
      let live = minute + first + Math.floor(((Date.now() - simBlockSeen.at) / 1000 / bs) * 10);
      // 17.10.2026, Play nach Pause/Reset: der aktuelle Block kam lange vor dem
      // Play an, also ab der angehaltenen Minute und dem Play-Zeitpunkt zaehlen
      // (sonst sprang die Uhr sofort ans Blockende). Der naechste Block loest
      // wieder den Block-Anker aus.
      const pm = simRunSeen.minute;
      if (pm !== null && !Number.isNaN(pm) && simRunSeen.at > simBlockSeen.at && pm >= minute && pm <= minute + 9) {
        live = pm + Math.floor(((Date.now() - simRunSeen.at) / 1000 / bs) * 10);
      }
      minute = Math.min(live, minute + 9);
    }
  } else {
    // Angehalten / Laufende: die exakte Minute (Start 05:21, Ende 23:21), sofern
    // sie im angezeigten Block liegt, sonst die Blockzeit.
    const frozen = parseInt(st["input_number.lab_sim_minute"]?.state, 10);
    if (frozen >= minute && frozen <= minute + 9) minute = frozen;
  }
  return {
    year: +day.slice(0, 4), month: +day.slice(5, 7), day: +day.slice(8, 10),
    hour: Math.floor(minute / 60) % 24, minute: minute % 60, second: 0, millisecond: 0,
  };
}

// 17.10.2026, Lab-Replay: Tagesreihen fuer die apexcharts-card-Verlaeufe
// ("Verlauf (heute)" im Tab Heizung u. a.). deploy_ha_lab.py setzt im Lab einen
// data_generator ein, der diese Funktionen ruft; in Prod nutzt sie niemand und
// ohne Replay liefern sie null bzw. die echte Historie.
// bgaiSimSeries: [[Zeitstempel, Wert], ...] bis zum aktuellen Sim-Block, auf dem
// HEUTIGEN Datum (die Kartenachse zeigt den echten Tag 00-24 Uhr). Quelle:
// Attribut day_values der Lab-Ersatzentitaet, sensor.heizstab_power_w aus
// Profil-Spalte 24, Shelly-Leistungen aus sensor.lab_sim_devices (dev_w).
window.bgaiSimSeries = function (hass, entityId, start) {
  const st = (hass && hass.states) || {};
  if (st["input_boolean.simulation_mode"]?.state !== "on") return null;
  const steps = st["sensor.lab_sim_profile"]?.attributes?.steps;
  const i = parseInt(st["input_number.sim_step"]?.state, 10);
  if (!Array.isArray(steps) || Number.isNaN(i)) return null;
  let vals = null;
  const dayValues = st[entityId]?.attributes?.day_values;
  const roomW = st["sensor.lab_sim_devices"]?.attributes?.room_w;
  const objId = (entityId || "").replace(/^sensor\./, "");
  if (Array.isArray(dayValues)) vals = dayValues;
  else if (roomW && Array.isArray(roomW[objId])) vals = roomW[objId];
  else if (entityId === "sensor.heizstab_power_w") vals = steps.map((r) => r[24]);
  else {
    const m = /^sensor\.(.+)_leistung$/.exec(entityId || "");
    const devW = st["sensor.lab_sim_devices"]?.attributes?.dev_w;
    if (m && devW && Array.isArray(devW[m[1]])) vals = devW[m[1]];
  }
  if (!vals) return null;
  const d0 = new Date(start);
  d0.setHours(0, 0, 0, 0);
  const out = [];
  for (let k = 0; k <= i && k < vals.length; k++) {
    const minute = steps[k] ? steps[k][9] : k * 10;
    out.push([d0.getTime() + minute * 60000, Number(vals[k])]);
  }
  return out;
};
// Tageswerte des abgespielten Tages fuer Karten mit "heute"-Kennzahlen
// (views/heizung_oel.yaml, views/heizstab.yaml): aktuelle Profilzeile,
// kumulierte Geraete-kWh seit 00:00 (sensor.lab_sim_devices) und Anteil der
// bisherigen 10-min-Bloecke ueber einer Schwelle. null ohne Replay (Prod).
window.bgaiSimToday = function (hass) {
  const st = (hass && hass.states) || {};
  if (st["input_boolean.simulation_mode"]?.state !== "on") return null;
  const steps = st["sensor.lab_sim_profile"]?.attributes?.steps;
  const step = parseInt(st["input_number.sim_step"]?.state, 10);
  if (!Array.isArray(steps) || Number.isNaN(step) || !steps[step]) return null;
  const dev = st["sensor.lab_sim_devices"]?.attributes || {};
  return {
    row: steps[step],
    step,
    steps,
    devW: (id) => (dev.dev_w && Array.isArray(dev.dev_w[id]) ? dev.dev_w[id] : []),
    kwh: (id) => (dev.dev_kwh && Array.isArray(dev.dev_kwh[id]) ? Number(dev.dev_kwh[id][step]) : null),
    duty: (vals, threshold) => {
      let on = 0;
      for (let k = 0; k <= step && k < vals.length; k++) if (Number(vals[k]) > threshold) on++;
      return (on / (step + 1)) * 100;
    },
  };
};
// Sim-"jetzt" als Zeitstempel auf dem heutigen Datum, null ohne Replay.
window.bgaiSimNowTs = function (hass, start) {
  const p = simNowParts(hass);
  if (!p) return null;
  const d0 = start ? new Date(start) : new Date();
  d0.setHours(p.hour, p.minute, 0, 0);
  return d0.getTime();
};
// Echte Historie wie ohne data_generator (Fallback ausserhalb des Replays).
window.bgaiHistory = async function (hass, entityId, start, end, map) {
  const url = `history/period/${new Date(start).toISOString()}?filter_entity_id=${entityId}`
    + `&end_time=${new Date(end).toISOString()}&minimal_response&no_attributes`;
  const res = await hass.callApi("GET", url);
  return ((res && res[0]) || [])
    .map((s) => [new Date(s.last_changed || s.lu * 1000).getTime(), parseFloat(s.state ?? s.s)])
    .filter((p) => !Number.isNaN(p[1]))
    .map((p) => [p[0], map ? map(p[1]) : p[1]]);
};

// Die Karte rendert von sich aus nur jede Sekunde neu (eigener 1-s-Takt), eine
// Sim-Minute dauert aber nur ~0,67 s: im laufenden Replay deshalb alle 250 ms
// ein requestUpdate() auf die gepatchten Uhren, sonst wuerden Minuten
// uebersprungen. Ausserhalb des Replays passiert hier nichts.
const patchedClocks = new Set();
// Sim-Stunde, fuer die die Prognose-Icons zuletzt geholt wurden: die Prognose
// rueckt im Replay alle ~40 s eine Stunde weiter, der 5-s-Takt von apply()
// liesse die Icons bis zu ~9 s auf der alten Stunde stehen.
let lastSimHour = null;
setInterval(() => {
  if (!patchedClocks.size) return;
  const ha = document.querySelector("home-assistant");
  const hass = ha && ha.hass;
  if (!hass || hass.states["input_boolean.lab_demo_running"]?.state !== "on" || !simNowParts(hass)) return;
  for (const node of patchedClocks) {
    if (!node.isConnected) {
      patchedClocks.delete(node);
      continue;
    }
    if (typeof node.requestUpdate === "function") node.requestUpdate();
  }
  const hour = (hass.states["sensor.lab_sim_clock"]?.state || "").slice(0, 2);
  if (hour && hour !== lastSimHour) {
    lastSimHour = hour;
    forecastCacheAt = Date.now();
    refreshForecastCache(hass).then(apply);
  }
}, 250);

// 17.10.2026, Nutzer-Befund "Uhrzeit/Datum laden falsch": der Instanz-Patch
// unten greift erst beim ersten apply()-Durchlauf (bis zu 0,8 s nach dem
// Rendern), die Karte zeigte so beim Laden zuerst kurz die echte Uhrzeit und
// das echte Datum (gemessen: 04:51 statt Sim-Zeit). Deshalb wird zusaetzlich
// die Klasse gepatcht, sobald sie definiert ist; schon das erste Rendern nutzt
// dann Sim-Zeit/-Datum. Ohne Replay (Prod) liefert simNowParts null, dann
// bleibt alles echt.
let clockProtoPatched = false;
customElements.whenDefined("clock-weather-card").then(() => {
  const Ctor = customElements.get("clock-weather-card");
  let proto = Ctor && Ctor.prototype;
  let owner = null;
  let desc = null;
  while (proto && !desc) {
    const d = Object.getOwnPropertyDescriptor(proto, "currentDate");
    if (d && d.get && d.set) {
      desc = d;
      owner = proto;
    }
    proto = Object.getPrototypeOf(proto);
  }
  if (!desc) return; // andere Kartenversion: Instanz-Patch bleibt der Weg
  Object.defineProperty(owner, "currentDate", {
    configurable: true,
    get() {
      const real = desc.get.call(this);
      const ha = document.querySelector("home-assistant");
      const p = simNowParts(ha && ha.hass);
      if (p && !patchedClocks.has(this)) patchedClocks.add(this);
      return p && real && typeof real.set === "function" ? real.set(p) : real;
    },
    set(v) {
      desc.set.call(this, v);
    },
  });
  clockProtoPatched = true;
});

function patchClock(node) {
  if (node.__bgaiClockPatched) return;
  if (clockProtoPatched) {
    node.__bgaiClockPatched = true;
    patchedClocks.add(node);
    return;
  }
  let proto = Object.getPrototypeOf(node);
  let desc = null;
  while (proto && !desc) {
    const d = Object.getOwnPropertyDescriptor(proto, "currentDate");
    if (d && d.get && d.set) desc = d;
    proto = Object.getPrototypeOf(proto);
  }
  if (!desc) return; // andere Kartenversion: nichts anfassen
  Object.defineProperty(node, "currentDate", {
    configurable: true,
    get() {
      const real = desc.get.call(this);
      const ha = document.querySelector("home-assistant");
      const p = simNowParts(ha && ha.hass);
      return p && real && typeof real.set === "function" ? real.set(p) : real;
    },
    set(v) {
      desc.set.call(this, v);
    },
  });
  node.__bgaiClockPatched = true;
  patchedClocks.add(node);
}

// Echte Condition pro Forecast-Spalte: NICHT aus dem gerenderten Icon
// zurueckgeraten (SVG-Form/Text waere Rateweg, ausdruecklich unerwuenscht),
// sondern ueber die offizielle WS-Service-Aktion weather.get_forecasts
// geholt — dieselbe Aktion, die auch die eingebaute Karte fuer Temp/Uhrzeit
// nutzt (home-assistant/core, weather/websocket_api.py + __init__.py,
// verifiziert per Live-REST-Call gegen die echte Instanz 12.09.2026: Reihen-
// folge und Werte der Antwort stimmen 1:1 mit den bereits gerenderten Spalten
// ueberein, also einfache Index-Zuordnung ohne weitere Filterung noetig).
// Gecacht (5 min TTL, Forecast aendert sich nicht minuetlich) statt bei jedem
// apply()-Tick (alle 5s/800ms) neu abzufragen.
let forecastCache = null; // Array<condition-string>, in Render-Reihenfolge
let forecastCacheAt = 0;
let forecastEntity = WEATHER_ENTITY; // Entity der gerenderten Prognose-Karte
const FORECAST_CACHE_TTL_MS = 5 * 60 * 1000;

async function refreshForecastCache(hass) {
  try {
    const result = await hass.callWS({
      type: "call_service",
      domain: "weather",
      service: "get_forecasts",
      service_data: { entity_id: forecastEntity, type: "hourly" },
      return_response: true,
    });
    const entries = result && result.response &&
      result.response[forecastEntity] && result.response[forecastEntity].forecast;
    if (Array.isArray(entries)) {
      forecastCache = entries.map((e) => e.condition);
    }
  } catch (e) {
    // API/Netzwerk-Hickser: alten Cache behalten, naechster TTL-Ablauf
    // versucht es erneut. Nichts bricht, Icons bleiben auf dem letzten
    // bekannten Stand bzw. der urspruengliche HA-Icon-Renderer bleibt sichtbar.
  }
}

// Ersetzt je Spalte den Icon-Inhalt durch ein <img>, eine Spalte = ein Index
// im gecachten Forecast-Array (verifizierte 1:1-Reihenfolge, s. o.).
// Idempotent (wie injectInto): nur bei tatsaechlicher Aenderung anfassen,
// erneut aufgerufen bei jedem apply()-Tick, falls ein Karten-Re-Render
// (z. B. beim naechsten stuendlichen Forecast-Update) das <img> wieder
// entfernt haben sollte.
function applyForecastIcons(node) {
  if (!forecastCache) return;
  const cols = node.shadowRoot.querySelectorAll(".forecast-image-icon");
  cols.forEach((col, i) => {
    const condition = forecastCache[i];
    let img = col.querySelector("img.bgai-weather-png");
    if (!img) {
      col.innerHTML = "";
      img = document.createElement("img");
      img.className = "bgai-weather-png";
      col.appendChild(img);
    }
    if (img.dataset.condition !== String(condition)) {
      img.dataset.condition = String(condition);
      img.src = weatherIconUrl(condition);
      img.alt = condition || "";
    }
  });
}

// 12.09.2026, Nutzer-Wunsch "auch beim Wetter Divider-Striche": das reine
// CSS-Pendant (.forecast > div:not(:last-child){border-right:...} in
// FORECAST_CSS) zeigte trotz korrekt deployter Datei (per curl gegen die
// live Instanz verifiziert) keine sichtbare Wirkung — dasselbe Muster wie
// zuvor bei der Wetter-Karten-Rundung (CSS-Selektor auf dieser Fremd-Karte
// unzuverlässig). Direkter Inline-Style-Zugriff auf die tatsaechlichen
// Spalten-Elemente stattdessen, garantiert per !important, unabhaengig von
// jeder Cascade-/Selektor-Unsicherheit.
function applyForecastDividers(node) {
  const cols = node.shadowRoot.querySelectorAll(".forecast > div");
  cols.forEach((col, i) => {
    if (i < cols.length - 1) {
      // 12.09.2026, Nutzer-Wunsch "alle Divider in diesem Tab ausgefadet":
      // border-right kann keinen Verlauf haben, daher 2px breiter Gradient-
      // Hintergrund rechts statt echtem Rahmen (gleiches Muster wie die
      // uebrigen Divider in diesem Tab).
      col.style.setProperty(
        "background-image",
        "linear-gradient(to bottom, transparent, var(--divider-color) 15%, var(--divider-color) 85%, transparent)",
        "important"
      );
      col.style.setProperty("background-repeat", "no-repeat", "important");
      // 13.09.2026, Nutzer-Wunsch "senkrecht mittiger ausrichten": 100% Hoehe
      // liess den Strich ueber die volle (padding-behaftete) Spaltenhoehe
      // laufen statt zentriert auf Hoehe der Wetter-Icons zu sitzen. Kuerzer
      // (70%) plus "right center" nutzt den uebrigen Platz fuer automatische
      // vertikale Zentrierung statt Kante-zu-Kante.
      col.style.setProperty("background-size", "2px 70%", "important");
      col.style.setProperty("background-position", "right center", "important");
      col.style.setProperty("padding-right", "16px", "important");
    }
    if (i > 0) {
      col.style.setProperty("padding-left", "16px", "important");
    }
  });
}

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
  // ha-card rounds AND clips the themed background/content — overflow:hidden
  // stays here, that's what makes the internal rendering (PFCP flow graph,
  // apexcharts background, ...) respect the radius.
  // :host gets ONLY the radius, no overflow:hidden (12.09.2026, Nutzer-Befund
  // "keine Outline/kein Schatten bei den Karten" — der view-scoped --ha-
  // card-box-shadow-Override, den ha-card selbst per var() liest, wurde
  // komplett unsichtbar geclippt: ha-card sitzt INNERHALB von :host, ein
  // Box-Shadow ist fuer :host aus dessen eigener Sicht "ueberlaufender
  // Kindinhalt" und wurde von :hosts eigenem overflow:hidden abgeschnitten,
  // bevor er je sichtbar wurde — ein bekanntes CSS-Verhalten, Eltern-
  // overflow:hidden clippt den Schatten von Kindern. box-shadow auf ha-card
  // selbst wird dagegen NICHT durch ha-cards eigenes overflow:hidden
  // beschnitten (das clippt nur eigenen Inhalt, nicht die eigene Box-Deko) —
  // beide !important, damit ein karten-internes Radius-Reset nicht gewinnt.
  // button-cards inside a horizontal-stack are mode-selector segments — use a
  // smaller radius so they fit flush inside the outer pill container (14px).
  const inHStack = node.tagName === "BUTTON-CARD" &&
    node.getRootNode()?.host?.tagName === "HUI-HORIZONTAL-STACK-CARD";
  // 12.09.2026, Nutzer-Wunsch "Divider zwischen Power/Auto/Reboot und unter
  // dem Miner-Header, gerade statt gerundet": diese sitzen (wie Eco/Standard/
  // Super) ebenfalls in einem horizontal-stack und teilten sich bisher
  // denselben 10px-inHStack-Radius — reicht aber, um border-left/-bottom an
  // den Enden sichtbar zu runden (dieselbe Ursache wie beim Hamster-Icon-
  // Ring frueher diese Session). styles.card.border-radius:0 an der Instanz
  // (steuerung_quick.yaml) verliert dagegen IMMER gegen shape.js' spaeter
  // injiziertes !important — daher hier direkt am gerenderten .name-Text
  // erkannt (stabiler als eine geratene DOM-Tiefe) und auf 0 gesetzt, statt
  // eine weitere Sonderfall-Bedingung an anderer Stelle zu jagen.
  const nameText = node.shadowRoot.querySelector(".name")?.textContent?.trim();
  // 13.09.2026: Namen von "Power"/"Auto"/"Reboot" auf "Betrieb"/"Automatik"/
  // "Neustart" geaendert (views/miner_controls.yaml, views/steuerung_quick.
  // yaml) — Liste hier mitgezogen, sonst verlieren die Buttons stillschweigend
  // ihre eckige Form (Fallback waere der 10px-inHStack-Radius).
  const isSquareMinerBtn = ["Betrieb", "Automatik", "Neustart", "Miner #1", "Miner #2"].includes(nameText);
  const r = isSquareMinerBtn ? "0px" : (inHStack ? "10px" : RADIUS);
  let css = `:host{border-radius:${r}!important;}ha-card{border-radius:${r}!important;overflow:hidden!important;}`;
  // clock-weather-card: zusaetzlich den Heute-Bereich stauchen, damit clk in
  // den flachen Slot passt (nur die clk-Instanz rendert ihn).
  if (node.tagName === "CLOCK-WEATHER-CARD") {
    patchClock(node);
    // Instanz an ihrem gerenderten Bereich erkennen, nur passende Regel setzen.
    const sr = node.shadowRoot;
    const todayEl = sr.querySelector("clock-weather-card-today");
    if (todayEl) {
      // Farbregel in den Card-Root (deckt Light-DOM-Fall ab) und zusaetzlich in
      // den eigenen Shadow-Root des Today-Elements (deckt Shadow-DOM-Fall ab).
      css += CLOCK_TODAY_CSS + CLOCK_TODAY_TEXT_CSS;
      injectInto(todayEl.shadowRoot, "bitgrid-clock-today-text", CLOCK_TODAY_TEXT_CSS);
      const haEl = document.querySelector("home-assistant");
      applyTodayIcon(node, todayEl, haEl && haEl.hass);
    }
    if (sr.querySelector("clock-weather-card-forecast")) {
      css += CLOCK_FORECAST_CSS;
    }
  }
  if (node.tagName === "HUI-WEATHER-FORECAST-CARD") {
    // Icons fuer die Entity, die diese Karte TATSAECHLICH zeigt (Lab: das
    // Replay-Wetter weather.lab_sim_weather), nicht pauschal WEATHER_ENTITY.
    const ent = (node._config && node._config.entity) || WEATHER_ENTITY;
    if (ent !== forecastEntity) {
      forecastEntity = ent;
      forecastCacheAt = 0;
    }
    css += FORECAST_CSS;
    applyForecastIcons(node);
    applyForecastDividers(node);
  }
  if (node.tagName === "HORIZON-CARD") css += HORIZON_CSS;
  if (s.textContent !== css) s.textContent = css;
}

// 12.09.2026, Nutzer-Wunsch "die 2 Wetterkarten in eine Karte mit Strich
// dazwischen": card_mod auf dem umschliessenden vertical-stack (dashboard_v3.
// yaml) sollte #root/​:host runden+clippen — Nutzer-Befund nach mehreren
// Anlaeufen (Variable, direkter #root-Override, ".": |-Punktform, alles laut
// card-mod-Doku): "immer noch eckig". Statt weiter an einem ungewissen CSS-
// Selektor zu raten, hier stattdessen per JS direkt auf das TATSAECHLICHE
// erste Kind-Element im Shadow-Root zugreifen (voellig unabhaengig davon, ob
// es "#root" heisst oder anders) und Radius/Clipping als Inline-Style mit
// !important erzwingen — das schlaegt jede externe Stylesheet-Regel
// garantiert, unabhaengig von Injection-Reihenfolge/Spezifitaet.
// Erkennung ohne SHAPED_CARDS (das wuerde walk() vorzeitig abbrechen lassen
// und den Rekursions-Abstieg zu clock-weather-card/weather-forecast
// verhindern, s. deren eigene FORECAST_CSS/Icon-Logik unten): einfach jeden
// vertical-stack pruefen, der (als Lichte-DOM-Nachfahre, Shadow-Root-
// Grenzen von Zwischen-hui-card-Wrappern werden dabei nicht durchquert, nur
// deren eigene Licht-DOM-Kinder) eine clock-weather-card enthaelt — genau
// die eine Wetter-Merge-Huelle, sonst keine andere Karte im Dashboard.
function styleWeatherMergeStack(node) {
  if (!node.shadowRoot) return;
  const clock = node.shadowRoot.querySelector("clock-weather-card");
  if (!clock) return;
  // 12.09.2026, Nutzer-Befund "runde Ecken aussen immer noch nicht": der
  // erste Versuch (firstElementChild) blieb wirkungslos, obwohl dieselbe
  // Inline-Style-Technik bei den inneren Karten (unten) nachweislich griff —
  // ha-card{background/border/box-shadow} per card_mod-CSS auf "#root" zeigte
  // dagegen sichtbar Wirkung (Rand+Schatten um beide Karten zusammen kommen
  // von genau dieser Regel). Wahrscheinlichste Erklaerung: #root ist NICHT
  // das erste Kind-Element im Shadow-Root (z. B. ein vorangestelltes <style>-
  // Tag zaehlt fuer firstElementChild mit) — deshalb jetzt zuerst gezielt
  // nach "#root" suchen (dasselbe Ziel wie die bereits wirksame CSS-Regel),
  // mit einer Schleife ueber alle echten Kind-Elemente als Fallback, falls
  // #root in dieser HA-Version doch anders/gar nicht existiert.
  let roots = [];
  const byId = node.shadowRoot.querySelector("#root");
  if (byId) {
    roots = [byId];
  } else {
    const skip = new Set(["STYLE", "LINK", "SCRIPT", "TEMPLATE"]);
    roots = Array.from(node.shadowRoot.children).filter((el) => !skip.has(el.tagName));
  }
  roots.forEach((root) => {
    root.style.setProperty("border-radius", RADIUS, "important");
    root.style.setProperty("overflow", "hidden", "important");
  });
  // 12.09.2026, Nutzer-Wunsch "innere Karten nicht rund, nur aussen": beide
  // Kind-Karten quadratisch (radius:0), nur die Huelle oben rundet. Behebt
  // nebenbei den Bogen-Artefakt an der Naht von vorhin (radius-Mismatch
  // zwischen shape.js' hartem 20px auf ha-card und der Huelle) endgueltig,
  // da hier gar kein Radius mehr uebrig ist, der mismatchen koennte.
  // ha-card{border:none} auch hier per Inline-Style statt card_mod: dieselbe
  // Unsicherheit wie beim #root-Versuch (mehrere Anlaeufe blieben wirkungslos,
  // s. Kopfkommentar bei styleWeatherMergeStack), hier aber schon vorher von
  // shape.js selbst kontrolliert (ha-card bekommt seinen 20px-Radius genau
  // hier injiziert, s. styleCard()) — der zuverlaessigere Ort fuer den
  // Override, garantiert per Inline-Style + !important, unabhaengig von
  // Injection-Reihenfolge.
  const forecast = node.shadowRoot.querySelector("hui-weather-forecast-card");
  const clockHa = clock.shadowRoot && clock.shadowRoot.querySelector("ha-card");
  if (clockHa) {
    clockHa.style.setProperty("border-radius", "0", "important");
    clockHa.style.setProperty("border", "none", "important");
  }
  const forecastHa = forecast && forecast.shadowRoot && forecast.shadowRoot.querySelector("ha-card");
  if (forecastHa) {
    forecastHa.style.setProperty("border-radius", "0", "important");
    forecastHa.style.setProperty("border", "none", "important");
  }
  // 12.09.2026, Nutzer-Wunsch "Trennlinie wie bei BitGridAI/Hamster, mit
  // Platz an den Seiten statt randlos durchgezogen": ein border-top DIREKT
  // auf ha-card sitzt am aeusseren Rand der Box (Border wird immer an der
  // Border-Box-Kante gezeichnet, UNABHAENGIG von ha-cards eigenem Padding —
  // deshalb ging der Strich zuvor randlos von Seite zu Seite). Die Hamster-
  // Karte bekommt ihren eingerueckten Strich, weil ihr border-top auf einem
  // Element INNERHALB des gepolsterten Innenbereichs sitzt (padding-top:8px;
  // border-top:...), nicht auf der Karte selbst. Gleiches Muster hier: Strich
  // auf .forecast (liegt bereits innerhalb von ha-cards 12px-Padding) statt
  // auf ha-card selbst.
  const forecastDiv = forecast && forecast.shadowRoot && forecast.shadowRoot.querySelector(".forecast");
  if (forecastDiv) {
    // 12.09.2026, Nutzer-Wunsch "alle Divider in diesem Tab ausgefadet, wie
    // beim Wetter-Uhr-Divider": border-top kann keinen Verlauf haben, daher
    // ein 2px hoher Gradient-Hintergrund oben statt eines echten Rahmens
    // (identisches Muster wie der Hamster-horizontal-Divider).
    forecastDiv.style.setProperty(
      "background-image",
      "linear-gradient(to right, transparent, var(--divider-color) 15%, var(--divider-color) 85%, transparent)",
      "important"
    );
    forecastDiv.style.setProperty("background-repeat", "no-repeat", "important");
    forecastDiv.style.setProperty("background-size", "100% 2px", "important");
    forecastDiv.style.setProperty("background-position", "top", "important");
    forecastDiv.style.setProperty("padding-top", "8px", "important");
  }
}


// ── Individual-Bubbles einfaerben, ueber das LABEL statt ueber den Slot ──────
// 16.09.2026. Vorgeschichte: eine frueherere Fassung (zuletzt in
// www/bitgrid_wide.js) schrieb die Farbe fest auf --individual-left-top-color.
// PFCP vergibt die Slots aber nach SICHTBARER Reihenfolge, und die Miner sind
// bei Standby ausgeblendet (display_zero) — dadurch landete die Miner-Farbe,
// bei Miner aus ein Grau, regelmaessig auf der Geraete-Bubble.
//
// Deshalb hier umgekehrt: jede gerenderte Bubble wird ueber ihr <span.label>
// identifiziert, ihr TATSAECHLICHER Slot aus den Klassen gelesen und nur
// dessen Variable gesetzt. PFCP-Eigenheit (im Bundle verifiziert): der linke
// Knoten traegt nur "individual-top"/"individual-bottom" OHNE "left", nur die
// rechten tragen zusaetzlich "individual-right".
//
// Miner-Bubbles zeigen die Stufenfarbe (Eco/Standard/Super), kein Grau mehr.
const BUBBLE_STATIC = { "Heizstab": "#5C9EE2", "Geräte": "#f49891" };
const MINER_MODE_COLOR = {
  Eco: "var(--bg-color-eco, #4CAF50)",
  Standard: "var(--bg-color-standard, #26C6DA)",
  Super: "var(--bg-color-super, #F7931A)",
};
// Faellt der Workmode auf Standby/unknown, bleibt es bei der Mining-Rolle
// statt Grau (Nutzer-Vorgabe 16.09.2026). Im Normalfall ist die Bubble dann
// ohnehin ausgeblendet (display_zero).
const MINER_FALLBACK = "var(--bgai-mining-v3, #F7931A)";

function bubbleColor(label, hass) {
  if (BUBBLE_STATIC[label]) return BUBBLE_STATIC[label];
  const m = /^Miner #(\d)$/.exec(label);
  if (!m) return null;
  const mode = hass?.states?.[`sensor.miner${m[1]}_workmode_status`]?.state;
  return MINER_MODE_COLOR[mode] || MINER_FALLBACK;
}

// 25.09.2026, Nutzer-Befund "Miner-Bubble-Farbe wird nicht richtig angezeigt"
// (live verifiziert: beide Miner blieben dauerhaft #F7931A, egal welcher
// Modus lief). Ursache: node.style.setProperty() schreibt in DENSELBEN
// Inline-Style-Slot des Karten-Elements, in den PFCP bei jedem eigenen
// Re-Render (ausgeloest durch die Leistungssensoren, die sich alle paar
// Sekunden aendern, also weit oefter als unser 5s-Tick) die STATISCHE
// Config-Farbe (entities.individual[].color, hier #F7931A) zurueckschreibt —
// letzter Schreibzugriff gewinnt, und das ist fast immer PFCP. Exakt dieselbe
// Bugklasse wie bei --icon-solar-/-grid-/-battery-color weiter oben, dort per
// echter Stylesheet-Regel mit !important gefixt (schlaegt normalen Inline-
// Write dauerhaft, unabhaengig von der Schreibreihenfolge). Hier dasselbe
// Muster: statt node.style.setProperty ein <style>-Tag im PFCP-eigenen
// Shadow-Root (:host{...!important}), ueber injectInto() wie schon bei
// styleCard()'s Radius-Injektion.
function colorIndividualBubbles(node) {
  const sr = node.shadowRoot;
  if (!sr) return;
  const ha = document.querySelector("home-assistant");
  const hass = ha && (ha.hass || ha.__hass);
  const rules = [];
  sr.querySelectorAll(".circle-container").forEach((c) => {
    const cl = c.classList;
    if (!cl.contains("individual-top") && !cl.contains("individual-bottom")) return;
    const side = cl.contains("individual-right") ? "right" : "left";
    const pos = cl.contains("individual-top") ? "top" : "bottom";
    const label = c.querySelector("span.label")?.textContent?.trim();
    if (!label) return;
    const color = bubbleColor(label, hass);
    if (!color) return;
    rules.push(`--individual-${side}-${pos}-color:${color}!important;`);
    rules.push(`--icon-individual-${side}-${pos}-color:${color}!important;`);
    // Linke Knoten tragen im Bundle zusaetzlich die generischen Namen ohne
    // Seite (--individual-top-color / --icon-individual-top-color), siehe die
    // Klassen-Eigenheit oben. Beide setzen, damit Ring UND Icon sicher treffen.
    if (side === "left") {
      rules.push(`--individual-${pos}-color:${color}!important;`);
      rules.push(`--icon-individual-${pos}-color:${color}!important;`);
    }
  });
  injectInto(sr, "bitgrid-miner-mode-color", rules.length ? `:host{${rules.join("")}}` : "");
}

// 17.10.2026, Befund Lab (Galaxy Tab, live nachgestellt): rendert die
// clock-weather-card genau waehrend eines HA-Neustarts, meldet sie "Weather
// entity ... could not be found" und bleibt in diesem Fehlerzustand, auch wenn
// die Entitaet wieder da ist. Uhr und Wetter fehlen dann bis zum Neuladen der
// Seite (gemessen: nach 150 s noch leer). Ob es passiert, ist ein Wettlauf mit
// dem Neustart. Selbstheilung: sobald die Entitaet wieder existiert, Fehler
// zuruecksetzen und die Karte einmal aus- und einhaengen, damit sie ihr
// Prognose-Abo neu aufbaut (nur das Einhaengen allein liess den Fehler stehen).
// Hoechstens alle 10 s je Karte.
function healClockWeather(node) {
  if (!node.error) return;
  const ha = document.querySelector("home-assistant");
  const hass = ha && ha.hass;
  const ent = (node.config && node.config.entity) || (node.__config && node.__config.entity);
  if (!ent || !hass || !hass.states[ent]) return;
  if (Date.now() - (node.__bgaiHealedAt || 0) < 10000) return;
  node.__bgaiHealedAt = Date.now();
  node.error = undefined;
  const parent = node.parentNode;
  const next = node.nextSibling;
  if (parent) {
    parent.removeChild(node);
    parent.insertBefore(node, next);
  }
  if (node.requestUpdate) node.requestUpdate();
}

function walk(node) {
  if (!node) return;
  if (SHAPED_CARDS.has(node.tagName)) {
    styleCard(node);
    if (node.tagName === "POWER-FLOW-CARD-PLUS") colorIndividualBubbles(node);
    if (node.tagName === "CLOCK-WEATHER-CARD") healClockWeather(node);
    return;
  }
  if (node.tagName === "HUI-VERTICAL-STACK-CARD") styleWeatherMergeStack(node);
  if (node.shadowRoot) node.shadowRoot.querySelectorAll("*").forEach(walk);
}

function apply() {
  const ha = document.querySelector("home-assistant");
  walk(ha);
  const hass = ha && ha.hass;
  // Im Lab-Replay wechselt die Sim-Stunde alle ~40 s, der 5-min-Cache waere zu
  // traege; dort genuegt der 5-s-Takt von apply().
  const ttl = simNowParts(hass) ? 4000 : FORECAST_CACHE_TTL_MS;
  if (hass && Date.now() - forecastCacheAt > ttl) {
    forecastCacheAt = Date.now(); // vor dem await setzen, keine ueberlappenden Calls
    refreshForecastCache(hass);
  }
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

// 17.10.2026, Lab-Befund "Hintergrund laedt verzoegert": die Tag/Nacht-Bilder
// werden sonst erst beim ersten Wechsel geladen, die Grundrisse sind je 1,2 bis
// 1,6 MB PNG (auf dem Wandtablet ueber WLAN sichtbar). Einmal nach dem
// Seitenaufbau in den Browser-Cache vorladen. Die URLs muessen exakt denen in
// views/floorplan.yaml, views/garage_floorplan.yaml und bitgrid_dashboard_v3.yaml
// entsprechen (inkl. ?version/?v), sonst greift der Cache nicht; nach einem
// Bildwechsel dort auch hier anpassen.
const PRELOAD_IMAGES = [
  "/local/floorplan/base.png?version=2350CF723E1CB2BDD4076DF6AC25C59A",
  "/local/floorplan/base_night.png?version=63BD476D3D52319852B4400403D2014C",
  "/local/garage_floorplan/base.png?version=AE860AAC9603D3C1A58425DF8407C622",
  "/local/garage_floorplan/base_night.png?version=668308AB46BB030E90EA5DAEDF717654",
  "/local/bg_grass.jpg?v=20260926",
  "/local/bg_grass_night.jpg?v=20260926",
];
setTimeout(() => {
  PRELOAD_IMAGES.forEach((src) => {
    const img = new Image();
    img.decoding = "async";
    img.src = src;
  });
}, 4000);

window.addEventListener("location-changed", () => setTimeout(apply, 500));
document.addEventListener("visibilitychange", () => setTimeout(apply, 500));

// 17.10.2026, Lab-Studie: das Probanden-Tablet meldet, was es zeigt, damit die
// Versuchsleitung in der Sim-Steuerung sieht, dass der geplante Reiz wirklich
// angezeigt wird (Gruppe, Hamster-Zustand), und das Protokoll eine
// Expositionsspur hat. Nur auf /bitgridai-home/ und nur, wenn die Lab-Entitaeten
// existieren (lab_only/lab_studie.yaml); in Prod gibt es beide nicht, hier
// passiert dort also nichts. Puls alle 10 s (sein last_changed zeigt "Tablet
// verbunden"), die Anzeige nur bei Aenderung (ihr Verlauf = Expositionsspur).
const STUDY_PULSE = "input_text.lab_studie_tablet_puls";
const STUDY_SHOWN = "input_text.lab_studie_tablet_anzeige";
let studyShownLast = null;

function findHamsterCard(node) {
  if (!node) return null;
  if (node.tagName === "BUTTON-CARD" && node.shadowRoot) {
    const img = node.shadowRoot.querySelector('img[src*="/local/bithamster_"]');
    if (img) return img;
  }
  const kids = node.shadowRoot ? [...node.shadowRoot.children, ...node.children] : [...node.children];
  for (const c of kids) {
    const hit = findHamsterCard(c);
    if (hit) return hit;
  }
  return null;
}

function reportStudyTablet() {
  const ha = document.querySelector("home-assistant");
  const hass = ha && ha.hass;
  if (!hass || !hass.states[STUDY_PULSE] || !hass.states[STUDY_SHOWN]) return;
  if (!location.pathname.startsWith("/bitgridai-home/") || document.hidden) return;
  // Hamster-Karte: Bild und Ueberschrift so, wie sie gerade im DOM stehen
  // (bitgrid_dashboard_v3.yaml: Bild-Spalte, Trennstrich, Text-Spalte).
  const img = findHamsterCard(ha);
  const row = img && img.parentElement && img.parentElement.parentElement;
  const head = row && row.children[2] && row.children[2].children[0];
  const shown = JSON.stringify({
    u: (hass.user && hass.user.name) || "",
    a: hass.user && hass.user.is_admin ? 1 : 0,
    p: location.pathname,
    v: hass.states["input_select.lab_studie_gruppe"]?.state || "",
    k: head ? head.textContent.trim().slice(0, 90) : "",
    i: img ? (img.getAttribute("src") || "").replace(/^\/local\//, "").replace(/\?.*$/, "") : "",
  });
  const call = (entity, value) =>
    hass.callService("input_text", "set_value", { entity_id: entity, value }).catch(() => {});
  if (shown !== studyShownLast && shown.length <= 255) {
    studyShownLast = shown;
    call(STUDY_SHOWN, shown);
  }
  call(STUDY_PULSE, String(Math.floor(Date.now() / 1000)));
}
setInterval(reportStudyTablet, 10000);
window.addEventListener("location-changed", () => setTimeout(reportStudyTablet, 1500));

// Tablet-Schutz entfernt am 18.10.2026 (Nutzer: der Tester soll in seiner Simulation wieder
// alle Funktionen nutzen koennen). Vorher verschluckte er Schalt-Taps und more-info-Dialoge
// auf /bitgridai-home/ fuer Nicht-Admins ausser Eco-Start und Investierte Hardware. Die
// Eingaben der beiden Aufgaben protokolliert weiter lab_only/lab_studie.yaml.
