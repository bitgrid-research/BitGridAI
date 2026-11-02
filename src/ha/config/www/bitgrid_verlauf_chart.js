// BitGridAI — eigenstaendige Verlaufs-Karte (rohes ApexCharts.js statt
// custom:apexcharts-card), einziger Zweck: echte 3h-Schritte auf der
// Stunden-X-Achse (00,03,06,09,12,15,18,21,24).
//
// Historie (12.09.2026): erster Anlauf mit dieser Karte wurde auf
// Nutzer-Wunsch zurueckgebaut ("Verlauf wieder zuruecksetzen"), danach zwei
// weitere Anlaeufe direkt in apexcharts-card selbst versucht:
// - xaxis.labels.formatter auf der datetime-Achse: bestaetigter Upstream-Bug
//   (github.com/apexcharts/apexcharts.js/issues/164), nur der erste Tick
//   rendert korrekt.
// - Danach ein DOM-Post-Processing-Ansatz (bitgrid_card_shape.js), der
//   ApexCharts' EIGENE, native Ticks nachtraeglich ausblendet: funktional
//   begrenzt, weil die native datetime-Achse fuer einen 24h-Span selbst nur
//   ein 2h-Raster erzeugt (00,02,04,...) — von diesem Raster sind nur
//   0/6/12/18 auch Vielfache von 3, die "krummen" 3h-Werte (03,09,15,21)
//   kommen im nativen Tick-Raster gar nicht vor und lassen sich nicht durch
//   Ausblenden herbeizaubern. Bestenfalls 6h-Schritte, kein echtes 3h.
// Einzige verbleibende Loesung fuer ECHTE 0/3/6/9/12/15/18/21/24-Schritte:
// eine category-Achse mit 24 Stunden-Kategorien + einem 25. synthetischen
// "24:00"-Randpunkt (nur fuer den letzten Tick, keine Daten). category
// wertet labels.formatter zuverlaessig aus (der #164-Bug betrifft
// ausschliesslich datetime) — apexcharts-card selbst liefert aber laut
// eigener Doku (data_generator-Abschnitt) JEDE Serie zwingend als
// [timestamp, value]-Paare, es gibt dort keinen dokumentierten Weg auf
// echte Kategorie-Labels umzustellen. Daher zwangslaeufig dieses eigene
// Custom-Element mit rohem ApexCharts.js.
//
// Optik 1:1 aus der bisherigen views/energieverlauf_tag.yaml uebernommen
// (Farben, Dash-Muster, Legenden-Divider-Fade, Text-Halo). Kartenhoehe fix
// per chart.height (Nutzer-Feingefuehl, s. Kommentar dort) — ein Versuch am
// 12.09.2026, sie per Flexbox-Kette dynamisch an Energiefluss anzugleichen,
// ist live gescheitert und wurde zurueckgebaut. Datenaufloesung:
// stuendliche Mittelwerte, identisch zu apexcharts-cards group_by: {func:
// avg, duration: 1h} + extend_to: now.
//
// Bekannter, akzeptierter Unterschied zur bisherigen datetime-Achse: die
// "jetzt"-Linie kann nur noch auf die volle aktuelle Stunde einrasten (nicht
// mehr minutengenau), weil eine category-Achse keine gebrochenen
// Zwischenpositionen kennt.
//
// Read-only auf hass.callApi (History), kein Einfluss auf eine
// Steuerentscheidung — bleibt aus dem deterministischen Kern raus, wie jedes
// andere reine Anzeige-Modul in www/.

const APEXCHARTS_CDN = "https://cdn.jsdelivr.net/npm/apexcharts@3.45.1/dist/apexcharts.min.js";
let apexChartsLoadPromise = null;

function loadApexCharts() {
  if (window.ApexCharts) return Promise.resolve();
  if (apexChartsLoadPromise) return apexChartsLoadPromise;
  apexChartsLoadPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = APEXCHARTS_CDN;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("ApexCharts konnte nicht geladen werden"));
    document.head.appendChild(script);
  });
  return apexChartsLoadPromise;
}

// 13.09.2026, Nutzer-Wunsch: feste PV-Leistungs-Skala statt ApexCharts'
// Auto-Min/Max (0-10 kW in 2er-Schritten, s. yaxis-Aufbau unten).
const POWER_YAXIS_MAX = 10;
const POWER_YAXIS_STEP = 2;

// Eine Serien-Definition pro Datenrolle, 1:1 aus views/energieverlauf_tag.yaml
// (Farben, Opazitaet, Dash-Muster, Transform auf kW). yaxis: "power" (links,
// kW) oder "soc" (rechts, %).
const SERIES_DEFS = [
  {
    entity: "sensor.pv_power_w",
    name: "PV-Leistung",
    icon: "mdi:white-balance-sunny",
    // 16.09.2026, Nutzer-Vorgabe: die Serie nutzt jetzt dieselbe PV-Rollenfarbe
    // wie die Bubble im Energiefluss (bgai-pv-v3). Damit endet die bewusste
    // Sonderlocke vom 12.09.2026 (gedecktes Mustard #C99A3C statt Signalgelb),
    // die es gab, solange die Rollenfarbe ein helles Gelb war. Betrifft Linie,
    // Legenden-Punkt UND die linke Y-Achse: alle leiten sich von diesem einen
    // Wert ab (primaryPowerColor). Literal statt var(), ApexCharts loest CSS-
    // Variablen in der color-Option nicht auf (s. DESIGN.md).
    color: "#fbb210",
    yaxis: "power",
    opacity: 0.35,
    dash: 6,
    unit: "kW",
    transform: (v) => v / 1000,
  },
  {
    entity: "sensor.grid_import_w",
    name: "Netzbezug",
    icon: "mdi:transmission-tower",
    // 16.09.2026: Netz-Rolle auf #1aaccb (Nutzer-Vorgabe).
    color: "#1aaccb",
    yaxis: "power",
    opacity: 0.25,
    dash: 4,
    unit: "kW",
    transform: (v) => v / 1000,
  },
  {
    // 13.09.2026, Nutzer-Wunsch: Legenden-Reihenfolge PV-Leistung/Netzbezug/
    // Batteriestand (vorher Batteriestand an erster Stelle) — reine
    // Array-Reihenfolge, betrifft weder yaxis-Zuordnung (yaxis: "soc" bleibt
    // eindeutig ueber den yaxis-Key) noch primaryPowerSeries (erste
    // yaxis:"power"-Serie ist weiterhin PV-Leistung).
    entity: "sensor.battery_soc_pct",
    name: "Batteriestand",
    icon: "mdi:battery",
    // 16.09.2026: Akku-Rolle auf #b3d804 (Nutzer-Vorgabe).
    color: "#b3d804",
    yaxis: "soc",
    opacity: 0.14,
    dash: 0,
    unit: "%",
    transform: (v) => v,
  },
  {
    entity: "sensor.house_load_w",
    name: "Hausverbrauch",
    icon: "mdi:home",
    // 12.09.2026, Bug gefunden: #C9814A war die gedriftete themes/bitgrid.
    // yaml-Farbe (s. dortiger Kommentar), nicht die dokumentierte Geraete/
    // Rosa-Rolle (bgai-geraete-v3, DESIGN.md im Repo-Root), die Hausverbrauch laut Kommentar in
    // bitgrid_dashboard_v3.yaml (PFCP-Home-Ring) absichtlich teilen soll.
    // 16.09.2026: Rolle auf #f49891 umgestellt, zieht mit der Geraete-Rolle mit.
    color: "#f49891",
    yaxis: "power",
    opacity: 0.25,
    dash: 2,
    unit: "kW",
    transform: (v) => v / 1000,
  },
  {
    entity: "sensor.miner_total_power_w",
    name: "Miner-Verbrauch",
    icon: "mdi:pickaxe",
    color: "#F7931A",
    yaxis: "power",
    opacity: 0.25,
    dash: 8,
    unit: "kW",
    transform: (v) => v / 1000,
  },
];

// 24 Stunden-Mittelwerte (Index 0..23) fuer den laufenden Tag, Stunden NACH
// der aktuellen bleiben null (kein Daten-Fake wie eine flache Fortschreibung
// — identisch zum Zweck von extend_to: now). Index 24 ist ein rein
// synthetischer Randpunkt (immer null), existiert nur damit die 25.
// Kategorie "24:00" als Tick-Label ueberhaupt platziert werden kann.
function hourlyAverages(history, now) {
  const startOfDay = new Date(now);
  startOfDay.setHours(0, 0, 0, 0);
  const currentHour = now.getHours();
  const sums = new Array(24).fill(0);
  const counts = new Array(24).fill(0);
  for (const point of history) {
    const v = parseFloat(point.state);
    if (Number.isNaN(v)) continue;
    const t = new Date(point.last_changed);
    const bucket = Math.floor((t - startOfDay) / 3600000);
    if (bucket < 0 || bucket > 23) continue;
    sums[bucket] += v;
    counts[bucket] += 1;
  }
  const out = [];
  for (let h = 0; h < 24; h++) {
    if (h > currentHour) {
      out.push(null);
      continue;
    }
    out.push(counts[h] > 0 ? sums[h] / counts[h] : null);
  }
  out.push(null); // Randpunkt "24:00"
  return out;
}

// 13.10.2026, Lab-Tagesreplay (src/ha/lab_only/lab_sim_day.yaml): Solange
// simulation_mode an ist UND sensor.lab_sim_profile das Tagesprofil liefert
// (existiert nur im Lab), zeigt der Chart den SIMULIERTEN Tag bis zur Sim-Uhr
// statt der Recorder-Historie. Die Historie enthaelt im Lab den im Zeitraffer
// endlos wiederholten Tag (ein Sim-Tag alle 24 min Echtzeit), stundenweise
// gemittelt ergab das ein flaches Wellenmuster statt eines Tagesverlaufs. In
// Prod fehlt das Profil, dort bleibt alles beim Recorder.
// Profilzeile (build_sim_day.py): [0] PV, [1] Haus, [2] Netzbezug, [4] SoC,
// [12]/[13] Stufe Miner 1/2 (0 Standby .. 3 Super). Miner-Leistung wie im
// Energiefluss aus der Stufe (Avalon-Q-Werte je Miner, demo_flow.yaml).
const SIM_MINER_W = [0, 800, 1300, 1674];
const SIM_VALUE = {
  "sensor.pv_power_w": (r) => r[0],
  "sensor.house_load_w": (r) => r[1],
  "sensor.grid_import_w": (r) => r[2],
  "sensor.battery_soc_pct": (r) => r[4],
  "sensor.miner_total_power_w": (r) => (SIM_MINER_W[r[12]] || 0) + (SIM_MINER_W[r[13]] || 0),
};

function simProfile(hass) {
  if (hass?.states?.["input_boolean.simulation_mode"]?.state !== "on") return null;
  const steps = hass.states["sensor.lab_sim_profile"]?.attributes?.steps;
  if (!Array.isArray(steps) || !steps.length) return null;
  const raw = parseInt(hass.states["input_number.sim_step"]?.state, 10);
  const step = Math.min(Number.isNaN(raw) ? 0 : raw, steps.length - 1);
  return { steps, step };
}

// Stuendliche Mittel aus den 10-Minuten-Bloecken (6 je Stunde) bis zur Sim-Uhr,
// gleiche Form wie hourlyAverages(): 24 Stunden + Randpunkt "24:00".
function simHourlyAverages(sim, entity) {
  const value = SIM_VALUE[entity];
  const currentHour = Math.floor(sim.step / 6);
  const out = [];
  for (let h = 0; h < 24; h++) {
    if (!value || h > currentHour) {
      out.push(null);
      continue;
    }
    const last = Math.min(h * 6 + 5, sim.step);
    let sum = 0;
    let n = 0;
    for (let i = h * 6; i <= last; i++) {
      const v = value(sim.steps[i]);
      if (typeof v === "number" && !Number.isNaN(v)) {
        sum += v;
        n += 1;
      }
    }
    out.push(n ? sum / n : null);
  }
  out.push(null); // Randpunkt "24:00"
  return out;
}

function hourLabel(h) {
  return `${String(h).padStart(2, "0")}:00`;
}

// Aktueller Stand fuer die Legende (12.09.2026, Nutzer-Wunsch "Stand mit
// anzeigen"): bewusst der LIVE-Zustand aus hass.states, nicht der letzte
// Stunden-Mittelwert aus der Chart-Serie — die Legende steht unter dem Chart
// als "jetzt"-Angabe, kein Hover-Datenpunkt. Dezimalstellen/Einheit exakt
// wie im Tooltip-Formatter unten (soc: 0 Nachkommastellen + "%", Leistung:
// 1 Nachkommastelle + "kW").
// 17.10.2026, Nutzer-Wunsch: das Batteriestand-Icon der Legende folgt dem
// Ladestand genau wie die Batterie im Energiefluss (power-flow-card-plus,
// Schwellen dort im Bundle nachgelesen: > 72 % high, > 44 % medium,
// > 16 % low, sonst outline, ohne Wert mdi:battery).
function batteryIconForSoc(state) {
  const soc = state ? parseFloat(state.state) : NaN;
  if (Number.isNaN(soc)) return "mdi:battery";
  if (soc > 72) return "mdi:battery-high";
  if (soc > 44) return "mdi:battery-medium";
  if (soc > 16) return "mdi:battery-low";
  return "mdi:battery-outline";
}

function legendValueText(def, state) {
  if (!state || state.state === "unavailable" || state.state === "unknown") return "–";
  const raw = parseFloat(state.state);
  if (Number.isNaN(raw)) return "–";
  const value = def.transform(raw);
  const decimals = def.yaxis === "soc" ? 0 : 1;
  return `${value.toLocaleString("de-DE", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })} ${def.unit}`;
}

class BitgridVerlaufChart extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    if (!this.shadowRoot) this._buildDom();
  }

  set hass(hass) {
    this._hass = hass;
    this._maybeRefresh();
  }

  getCardSize() {
    return 6;
  }

  _buildDom() {
    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        /* 12.09.2026: Versuch, die Kartenhoehe per Flexbox-Kette (:host/
           #root ueber mehrere Shadow-DOM-Grenzen) automatisch an
           Energiefluss anzugleichen, live gescheitert (Karte wurde hoeher
           statt gleich hoch) — zurueckgebaut auf schlichtes display:block,
           feste Chart-Hoehe unten (Nutzer-Anweisung "einfach Verlauf 15px
           groesser" statt weiterer Automatik). */
        :host { display: block; }
        /* 12.09.2026: bewusst KEIN <ha-card>-Element mehr (Root Cause fuer
           "runde Ecken fehlen" trotz !important): ha-card bringt sein
           EIGENES internes :host{border-radius:...}-Regelwerk mit, und ein
           :host-Selektor hat HOEHERE Spezifitaet (0,1,0) als ein einfacher
           Typselektor wie "ha-card{...}" von aussen (0,0,1) — !important auf
           beiden Seiten aendert daran nichts, :host gewinnt den Gleichstand.
           card_mod umgeht das, weil es sein <style> DIREKT in ha-cards
           eigenes Shadow-Root injiziert (dort gilt :host vs :host, gleiche
           Spezifitaet). Fuer ein eigenes Custom-Element ist ein normaler,
           selbst kontrollierter <div> die zuverlaessigere Wahl: keine
           konkurrierende interne Stylesheet-Ebene, kein Spezifitaets-Wettlauf. */
        .bgai-card {
          box-sizing: border-box;
          /* Bezug fuer die cqw-Einheiten der Legende (17.10.2026). */
          container-type: inline-size;
          padding: 12px;
          background: var(--ha-card-background);
          /* 12.09.2026, dritter Anlauf: var(--bgai-card-radius-v3)
             blieb trotz Fallback sichtbar eckig (zwei Deploys, Cache-Bust
             jeweils hochgezaehlt, Root Cause nicht gefunden) — hart auf den
             Theme-Literalwert (themes/bitgrid.yaml: ha-card-border-radius:
             "20px") umgestellt statt weiter auf die Variable zu vertrauen.
             Nachteil: folgt einer kuenftigen Theme-Aenderung des Radius
             nicht automatisch mehr, wird dann hier manuell nachgezogen. */
          border-radius: 20px !important;
          border: var(--bgai-card-border-width-v3) solid var(--bgai-card-border-v3);
          box-shadow: var(--bgai-card-shadow-v3);
          overflow: hidden !important;
        }
        #chart { width: 100%; }
        /* 12.09.2026, Root Cause gefunden (apexcharts.min.js @3.45.1 direkt
           inspiziert, appendToForeignObject()/elLegendForeign): ApexCharts
           rendert seine eingebaute Legende NICHT als normales HTML im
           Shadow-DOM, sondern in einem SVG <foreignObject>. Prozentuale
           Breiten/Flex-Layout darin sind in mehreren Browsern nachweislich
           unzuverlaessig (Chromium-Bugs zu foreignObject-Sizing) — deshalb
           griff selbst display:flex/flex-wrap mit !important nicht (die
           Legende blieb einspaltig gestapelt, unabhaengig von position/
           horizontalAlign in der Config). Fix: eingebaute Legende komplett
           deaktiviert (legend.show:false unten), eigene Legende als
           GEWOEHNLICHES <div> ausserhalb jeder SVG/foreignObject-Ebene —
           damit greift normales CSS-Flexbox garantiert.
           Reihenfolge/Umbruch (Nutzer-Vorgabe): Zeile 1 Batteriestand/PV-
           Leistung/Netzbezug, Zeile 2 Hausverbrauch/Miner-Verbrauch — ergibt
           sich hier automatisch aus SERIES_DEFS-Reihenfolge + Umbruchbreite,
           kein manuelles Zeilen-Array noetig. */
        .bgai-legend {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          align-items: center;
          /* 27.09.2026, Nutzer-Wunsch "etwas Space fuer bessere Lesbarkeit":
             column-gap 16px -> 28px (Abstand zwischen den Eintraegen einer
             Zeile), row-gap 4px -> 10px (Abstand der beiden Legendenzeilen).
             Der erzwungene Umbruch nach dem 3. Eintrag (s. _fetchAndRender)
             bleibt damit stabil: Zeile 1 misst rund 550px, die Karte hat auch
             auf einem 1280px-Tablet (halbe Viewportbreite, View-Zoom 0.8)
             noch rund 775px CSS-Breite — 2x28px Zusatzabstand passen. */
          /* 17.10.2026, Nutzer-Wunsch "weniger Abstand zwischen den zwei
             Zeilen", damit Energiefluss und Verlauf (heute) gleich hoch sind.
             Der fruehere Umbruch-Span bildete eine eigene leere Flex-Zeile, der
             row-gap von 10px wirkte dadurch doppelt (20px). Jetzt zwei echte
             Zeilen (.bgai-legend-row) untereinander mit genau einem Abstand
             von 8px. Gemessen vorher: Verlauf 333 px, Energiefluss 323 px
             hoch (View-Zoom 0.87). */
          flex-direction: column;
          row-gap: 8px;
          padding-top: 12px;
          margin-top: 8px;
          background-image: linear-gradient(to right, transparent, var(--divider-color) 15%, var(--divider-color) 85%, transparent);
          background-repeat: no-repeat;
          background-size: 100% 2px;
          background-position: top;
        }
        /* 17.10.2026, Nutzer-Befund am Tablet "Legende 3-zeilig statt 2": Zeile 1
           braucht 561 px und brach unter ~1060 px Fensterbreite um (gemessen
           1024 px: Karte 549 px, Batteriestand in eigener Zeile). Jetzt kein
           Umbruch mehr; Abstand und Schrift schrumpfen mit der Kartenbreite
           (cqw = 1 % der Innenbreite der .bgai-card, container-type unten). Bei
           673 px Innenbreite (1280er Fenster) ergeben 4.2cqw/2.4cqw die bisherigen
           28/16 px (per clamp gedeckelt). */
        .bgai-legend-row {
          display: flex;
          flex-wrap: nowrap;
          justify-content: center;
          align-items: center;
          column-gap: clamp(10px, 4.2cqw, 28px);
          row-gap: 8px;
        }
        .bgai-legend-item {
          display: flex;
          align-items: center;
          /* 27.09.2026: 6px -> 8px. Der gap wirkt jetzt zweimal pro Eintrag
             (Icon | Bezeichner | Wert, s. u. bgai-legend-value), nicht mehr
             nur einmal — der Wert steht seit dieser Aenderung in einem
             eigenen <span> statt im selben Textknoten wie der Bezeichner. */
          gap: 8px;
          font-size: clamp(13px, 2.4cqw, 16px);
          white-space: nowrap;
          font-family: Roboto, sans-serif;
          font-weight: 400;
          /* 12.09.2026, Nutzer-Wunsch "mehr Schatten", analog zur
             Achsenbeschriftung (s. .apexcharts-text oben): Blur 2px -> 4px,
             Deckkraft .85 -> .9. */
          text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9);
        }
        /* 27.09.2026, Nutzer-Vorgabe: nur der Bezeichner traegt noch die
           Serienfarbe, der Zahlenwert ist weiss. Zweck ist Lesbarkeit — die
           Farbe ordnet den Eintrag der Kurve zu, dafuer reicht Icon +
           Bezeichner; der Messwert selbst gewinnt auf dunklem Grund durch
           maximalen Kontrast. Literal #FFFFFF statt var(--primary-text-color):
           das Theme setzt dort #F5F8FC (leicht blaustichig), der Nutzer hat
           ausdruecklich Weiss verlangt. */
        .bgai-legend-value {
          color: #FFFFFF;
        }
        .bgai-legend-dot {
          --mdc-icon-size: 20px;
          width: 20px;
          height: 20px;
          flex: 0 0 auto;
          /* Halo wie beim Text daneben. Jetzt drop-shadow statt box-shadow:
             ein Icon braucht die Silhouetten-Verfolgung, ein box-shadow wuerde
             ein Rechteck hinter das Symbol legen. */
          filter: drop-shadow(0 0 3px rgba(0,0,0,.9)) drop-shadow(0 0 3px rgba(0,0,0,.9));
        }
        .apexcharts-text, .apexcharts-xaxis-annotation-label {
          /* 12.09.2026, Nutzer-Wunsch "mehr Schatten": Blur 2px -> 4px,
             Deckkraft .85 -> .9, staerkerer Halo fuer bessere Lesbarkeit
             der jetzt groesseren (17px) Achsenbeschriftungen. */
          text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9) !important;
        }
      </style>
      <div class="bgai-card">
        <div id="chart"></div>
        <div id="legend" class="bgai-legend"></div>
      </div>
    `;
    this._chartEl = root.getElementById("chart");
    this._legendEl = root.getElementById("legend");
  }

  async _maybeRefresh() {
    if (!this._hass) return;
    // 13.10.2026, Lab-Replay (s. simProfile): die Sim-Uhr springt alle 10 s
    // um 10 Minuten, also bei jedem neuen Schritt neu zeichnen. Keine
    // History-Abfrage, daher billig. _lastFetch zuruecksetzen, damit nach
    // dem Demo-Ende sofort wieder die echte Historie geladen wird.
    const sim = simProfile(this._hass);
    if (sim) {
      if (this._apexChart && sim.step === this._lastSimStep) return;
      this._lastSimStep = sim.step;
      this._lastFetch = 0;
      await this._fetchAndRender();
      return;
    }
    this._lastSimStep = undefined;
    const now = Date.now();
    // 5 Minuten Cache (identisch zu update_interval: 5min der bisherigen
    // apexcharts-card-Config) — History-Abfragen sind teurer als ein simples
    // State-Update, taeglicher Verlauf muss nicht sekundengenau sein.
    // 26.09.2026, Bug gefunden (Nutzer-Meldung "Graph laedt oft nicht nach
    // View-Wechsel"): disconnectedCallback() zerstoert this._apexChart beim
    // Verlassen der View, aber ein Reconnect INNERHALB der 5-Minuten-Frist
    // sprang bisher direkt in den fruehen return, ohne das je zu bemerken —
    // der Container blieb leer, bis der Cache von selbst ablief. Deshalb
    // zusaetzlich pruefen, ob ueberhaupt noch eine Chart-Instanz existiert.
    if (this._apexChart && this._lastFetch && now - this._lastFetch < 5 * 60 * 1000) return;
    this._lastFetch = now;
    await this._fetchAndRender();
  }

  async _fetchAndRender() {
    try {
      await loadApexCharts();
    } catch (e) {
      this._chartEl.textContent = "ApexCharts konnte nicht geladen werden.";
      return;
    }
    const hass = this._hass;
    const now = new Date();
    const startOfDay = new Date(now);
    startOfDay.setHours(0, 0, 0, 0);
    // Lab-Replay: Sim-Stunde statt Uhrzeit, keine Recorder-Abfrage (s. simProfile).
    const sim = simProfile(hass);
    const currentHour = sim ? Math.floor(sim.step / 6) : now.getHours();
    const entityIds = SERIES_DEFS.map((s) => s.entity);
    let historyByEntity = {};
    if (!sim) {
      try {
        const raw = await hass.callApi(
          "GET",
          `history/period/${startOfDay.toISOString()}?filter_entity_id=${entityIds.join(",")}&end_time=${now.toISOString()}&minimal_response&significant_changes_only=0`
        );
        raw.forEach((entityHistory) => {
          if (entityHistory.length) {
            historyByEntity[entityHistory[0].entity_id] = entityHistory;
          }
        });
      } catch (e) {
        this._chartEl.textContent = "Historie konnte nicht geladen werden.";
        return;
      }
    }

    // Immer alle 24 Stunden + 1 Randpunkt ("24:00") als Kategorien, unabhaengig
    // davon wie weit der Tag schon fortgeschritten ist — damit die Achse wie
    // bisher den GESAMTEN Tag 00:00-24:00 abbildet (kuenftige Stunden bleiben
    // als Luecke sichtbar, keine Kuerzung der Achse auf "bis jetzt").
    const categories = [];
    for (let h = 0; h < 24; h++) categories.push(hourLabel(h));
    categories.push("24:00");

    const series = SERIES_DEFS.map((def) => {
      const hist = historyByEntity[def.entity] || [];
      const avgs = sim ? simHourlyAverages(sim, def.entity) : hourlyAverages(hist, now);
      return {
        name: def.name,
        data: avgs.map((v) => (v === null ? null : def.transform(v))),
        __def: def,
      };
    });

    const colors = series.map((s) => s.__def.color);
    const dashArray = series.map((s) => s.__def.dash);
    const opacities = series.map((s) => s.__def.opacity);

    // Eigene Legende (s. Kommentar bei .bgai-legend): normales <div>, kein
    // SVG-foreignObject-Layout-Bug moeglich. Reihenfolge = SERIES_DEFS.
    this._legendEl.innerHTML = "";
    // Zeile 1 Batteriestand/PV-Leistung/Netzbezug, Zeile 2 Hausverbrauch/
    // Miner-Verbrauch (Nutzer-Vorgabe 12.09.2026), je Zeile zentriert.
    const legendRows = [document.createElement("div"), document.createElement("div")];
    legendRows.forEach((r) => {
      r.className = "bgai-legend-row";
      this._legendEl.appendChild(r);
    });
    series.forEach((s, i) => {
      const item = document.createElement("span");
      item.className = "bgai-legend-item";
      // 16.09.2026, Nutzer-Wunsch: statt eines Farbpunkts das Icon des
      // jeweiligen Knotens aus dem Energiefluss, in der Serienfarbe. ha-icon
      // ist global registriert und funktioniert auch in diesem Shadow-Root.
      const dot = document.createElement("ha-icon");
      dot.className = "bgai-legend-dot";
      dot.setAttribute("icon", s.__def.entity === "sensor.battery_soc_pct"
        ? batteryIconForSoc(hass.states[s.__def.entity])
        : s.__def.icon);
      dot.style.color = s.__def.color;
      // 27.09.2026, Nutzer-Vorgabe: Bezeichner und Zahlenwert in getrennten
      // <span>s statt in einem Textknoten — nur so kann der Wert eine eigene
      // Farbe (weiss, s. .bgai-legend-value) tragen. Der Doppelpunkt bleibt
      // beim Bezeichner, damit er dessen Farbe erbt.
      const label = document.createElement("span");
      label.className = "bgai-legend-label";
      label.style.color = s.__def.color;
      label.textContent = `${s.name}:`;
      const value = document.createElement("span");
      value.className = "bgai-legend-value";
      const stateObj = hass.states[s.__def.entity];
      value.textContent = legendValueText(s.__def, stateObj);
      item.appendChild(dot);
      item.appendChild(label);
      item.appendChild(value);
      legendRows[i < 3 ? 0 : 1].appendChild(item);
    });

    // "jetzt": die letzte Kategorie mit echten Daten ist die aktuelle Stunde
    // (nicht die letzte Kategorie ueberhaupt — die Achse reicht jetzt bis
    // 24:00, auch wenn der Tag erst zur Haelfte um ist).
    const nowLabel = hourLabel(currentHour);

    // yaxis MUSS positionsgleich zu series sein (ApexCharts bindet yaxis[i]
    // an series[i], seriesName als ARRAY wird NICHT unterstuetzt — genau das
    // hatte den ersten Deploy kaputt gemacht: mit nur 2 yaxis-Eintraegen fuer
    // 5 Serien landete Batteriestand auf yaxis[0] ("Leistung (kW)", 0-100
    // autoskaliert auf den %-Wertebereich) und alle vier Leistungs-Serien
    // wurden auf yaxis[1] (min:0/max:100 fuer SoC) zusammengequetscht.
    // Fix: EIN yaxis-Eintrag pro Serie (5 Eintraege), alle Leistungs-Serien
    // bekommen denselben seriesName (der Name der ersten Leistungs-Serie) —
    // das ist der offizielle ApexCharts-Mechanismus, mehrere Serien eine
    // gemeinsame, gemeinsam skalierte Achse teilen zu lassen (nur der
    // "primaere" Eintrag zeigt Titel/Beschriftung, die uebrigen show:false).
    const primaryPowerSeries = series.find((s) => s.__def.yaxis === "power");
    const primaryPowerName = primaryPowerSeries.name;
    // 12.09.2026, Nutzer-Wunsch: Y-Achse "Leistung (kW)" in PV-Leistung-Farbe
    // statt Weiss — primaryPowerSeries ist ohnehin schon PV-Leistung (erste
    // "power"-Serie in SERIES_DEFS-Reihenfolge), daher einfach deren Farbe
    // statt eines hart codierten Hex-Werts uebernehmen.
    const primaryPowerColor = primaryPowerSeries.__def.color;
    const yaxis = series.map((s) => {
      if (s.__def.yaxis === "soc") {
        // 12.09.2026, Nutzer-Wunsch: Achse in Batteriestand-Gruen statt
        // Weiss, analog zur PV-Leistung-Faerbung der linken Achse.
        return {
          seriesName: s.name,
          opposite: true,
          min: 0,
          max: 100,
          title: { text: "Batteriestand (%)", offsetX: 25, style: { color: s.__def.color, fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 } },
          labels: { style: { colors: s.__def.color, fontSize: "17px", fontFamily: "Roboto, sans-serif" } },
          decimalsInFloat: 0,
        };
      }
      if (s.name === primaryPowerName) {
        // 12.09.2026, Nutzer-Wunsch: Achsentitel wie in der Legende
        // "PV-Leistung" nennen (statt generisch "Leistung"), Werte ohne
        // Nachkommastelle (decimalsInFloat: 0 statt 1) — betrifft nur die
        // Achsenbeschriftung, Legende/Tooltip runden weiterhin auf 1
        // Nachkommastelle (eigener Formatter, s. legendValueText/tooltip.y).
        // 13.09.2026, Nutzer-Wunsch "keine dynamischen Werte": feste Skala
        // 0-10 kW in 2er-Schritten statt ApexCharts' Auto-Min/Max, das bei
        // wechselnder PV-Leistung staendig die Tick-Werte verschob.
        return {
          seriesName: primaryPowerName,
          min: 0,
          max: POWER_YAXIS_MAX,
          tickAmount: POWER_YAXIS_MAX / POWER_YAXIS_STEP,
          title: { text: "PV-Leistung (kW)", style: { color: primaryPowerColor, fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 } },
          labels: { style: { colors: primaryPowerColor, fontSize: "17px", fontFamily: "Roboto, sans-serif" } },
          decimalsInFloat: 0,
        };
      }
      // Restliche Leistungs-Serien: teilen sich die Achse des primaeren
      // Eintrags (gleicher seriesName), rendern aber keine eigene, doppelte
      // Achsenlinie/-beschriftung. min/max hier identisch mitgeben, sonst
      // rechnet ApexCharts beim Zusammenfuehren mehrerer yaxis-Eintraege mit
      // gleichem seriesName aus DEREN Auto-Range und die feste Skala oben
      // wird wieder ueberschrieben.
      return { seriesName: primaryPowerName, show: false, min: 0, max: POWER_YAXIS_MAX, decimalsInFloat: 1 };
    });

    const options = {
      chart: {
        type: "area",
        // 255px (12.09.2026): kein fester Bezug mehr zu Energiefluss'
        // Hoehe (Automatik per Flexbox-Kette live gescheitert, s. Git-
        // Historie dieser Zeile), reiner Wert nach Nutzer-Feingefuehl.
        height: 250,
        toolbar: { show: false },
        zoom: { enabled: false },
        background: "transparent",
        foreColor: "#FFFFFF",
        // 12.09.2026, Nutzer-Wunsch "mit Schatten" (zu den dickeren
        // Linien): dropShadow ist ein Chart-weiter ApexCharts-Effekt, gilt
        // damit fuer alle Serien-Linien gleichermassen, kein Bauplan pro
        // Serie noetig.
        dropShadow: {
          enabled: true,
          top: 0,
          left: 0,
          blur: 3,
          opacity: 0.5,
        },
      },
      series: series.map((s) => ({ name: s.name, data: s.data })),
      colors,
      stroke: {
        curve: "smooth",
        // 12.09.2026, Nutzer-Wunsch: 1px dicker (1.5 -> 2.5).
        width: 2.5,
        dashArray,
      },
      fill: {
        type: "solid",
        opacity: opacities,
      },
      xaxis: {
        type: "category",
        categories,
        tickPlacement: "on",
        // 3h-Schritte (der eigentliche Zweck dieser Karte): category-Achsen
        // werten labels.formatter zuverlaessig aus, anders als datetime
        // (github.com/apexcharts/apexcharts.js/issues/164). h ist hier immer
        // ein "echter" Stundenwert 0..24, daher trifft %3===0 exakt
        // 0/3/6/9/12/15/18/21/24.
        // 25.09.2026, Nutzer-Vorgabe "wie bei Regelschwellen (Tab Steuerung)":
        // Achsentitel "Uhrzeit" wie dort, Stil 1:1 aus
        // www/bitgrid_regelschwellen_chart.js uebernommen.
        title: {
          text: "Uhrzeit",
          offsetY: -4,
          style: { color: "rgba(255,255,255,0.55)", fontSize: "15px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
        },
        labels: {
          style: { colors: "#FFFFFF", fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
          // rotate: 0 (12.09.2026, Nutzer-Wunsch "Rest soll aussehen wie
          // vorher"): ApexCharts rotiert category-Labels automatisch
          // schraeg, sobald es meint sie koennten sich sonst ueberlappen —
          // die alte datetime-Achse zeigte die Uhrzeiten immer horizontal.
          rotate: 0,
          // offsetY: 12.09.2026, Nutzer-Wunsch: etwas Abstand zwischen
          // Achsenlinie/Ticks und den Uhrzeit-Labels, die sassen vorher fast
          // direkt an den Tick-Strichen.
          offsetY: 4,
          // h < 24: Kategorie "24:00" bleibt ein reiner Rand-Ankerpunkt
          // (ohne sie waere 21:00 der letzte 3h-Tick, die Flaeche wuerde
          // rechts nicht bis zum Kartenrand reichen), ihr Tick-LABEL aber
          // ausgeblendet — am 12.09.2026 erst entfernt, dann als "00:00"
          // wieder eingefuehrt, dann noch am selben Tag erneut entfernt
          // (Nutzer-Entscheidung). Die "0" am linken Rand (Stunde 0) ist
          // davon unberuehrt, die bleibt immer sichtbar.
          //
          // 25.09.2026, Nutzer-Vorgabe: Beschriftung ohne Minuten, angeglichen
          // an www/bitgrid_regelschwellen_chart.js (dort String(h % 24) ohne
          // fuehrende Null und ohne ":00"). value ist weiterhin die volle
          // Kategorie "HH:00" (categories/hourLabel bleiben unveraendert,
          // sonst bricht die interne "jetzt"-Positionssuche ueber
          // categories.indexOf(nowLabel)), nur die ANZEIGE wird hier auf die
          // reine Stunde gekuerzt.
          formatter: (value) => {
            const h = parseInt(value, 10);
            return h % 3 === 0 && h < 24 ? String(h) : "";
          },
        },
        axisTicks: { show: true },
        // 12.09.2026, Nutzer-Befund "Uhrzeit-Bug von der Skala": ApexCharts'
        // eigenes Achsen-Tooltip-Label (die kleine Box direkt auf der
        // x-Achse unterm Fadenkreuz, .apexcharts-xaxistooltip) ist ein
        // GESONDERTES Element, unabhaengig vom grossen tooltip.x oben —
        // sass an der 21:00/23:00-Grenze ueberlappend auf der echten
        // Tick-Beschriftung. Redundant seit der grosse Tooltip die Uhrzeit
        // zuverlaessig zeigt, deshalb komplett aus statt separat fixen.
        tooltip: { enabled: false },
      },
      yaxis,
      grid: {
        borderColor: "rgba(255,255,255,0.07)",
        strokeDashArray: 4,
        padding: { left: 15, right: 15 },
      },
      // Eingebaute Legende AUS (12.09.2026): rendert nachweislich in einem
      // SVG-foreignObject und lief dort selbst mit !important-CSS immer
      // einspaltig (s. Kommentar bei .bgai-legend) — eigene HTML-Legende
      // uebernimmt das jetzt komplett.
      legend: { show: false },
      annotations: {
        xaxis: [
          {
            x: nowLabel,
            borderColor: "rgba(255,255,255,0.5)",
            strokeDashArray: 4,
            label: {
              text: "jetzt",
              orientation: "vertical",
              offsetY: 7,
              borderColor: "rgba(255,255,255,0)",
              style: {
                color: "rgba(255,255,255,0.8)",
                background: "rgba(255,255,255,0)",
                fontSize: "10px",
                fontFamily: "Roboto, sans-serif",
              },
            },
          },
        ],
      },
      // Tooltip komplett selbst gebaut (12.09.2026, dritter Anlauf beim
      // "Uhrzeitbug"): tooltip.x.formatter verliess sich auf ApexCharts'
      // "value"-Argument, dessen Bedeutung bei einer category-Achse sich
      // als nicht konsistent herausstellte (13:00/23:00 stimmten, ganz
      // links bei Stunde 0 zeigte es faelschlich "01:00" statt "00:00").
      // tooltip.custom bekommt stattdessen den offiziell dokumentierten,
      // eindeutigen dataPointIndex direkt vom Callback — kein Raten mehr
      // ueber ApexCharts' interne Indexierung. series (aeusseres Array mit
      // __def) und categories sind hier per Closure erreichbar, die
      // Reihenfolge von w-uebergebenem seriesValues entspricht 1:1 dem
      // aeusseren series-Array (options.series wurde direkt daraus gebaut).
      tooltip: {
        theme: "dark",
        custom: ({ series: seriesValues, dataPointIndex }) => {
          const label = categories[dataPointIndex] ?? "";
          const rows = series
            .map((s) => {
              const idx = series.indexOf(s);
              const val = seriesValues[idx][dataPointIndex];
              const decimals = s.__def.yaxis === "soc" ? 0 : 1;
              const valueText = val === null || val === undefined ? "–" : `${val.toLocaleString("de-DE", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })} ${s.__def.unit}`;
              return `
                <div style="display:flex;align-items:center;gap:8px;padding:4px 0;">
                  <span style="width:12px;height:12px;border-radius:50%;background:${s.__def.color};flex:0 0 auto;box-shadow:0 0 4px rgba(0,0,0,.9);"></span>
                  <span style="color:#FFFFFF;font-family:Roboto,sans-serif;font-size:14px;">${s.name}:</span>
                  <span style="color:#FFFFFF;font-family:Roboto,sans-serif;font-size:14px;font-weight:700;margin-left:auto;">${valueText}</span>
                </div>`;
            })
            .join("");
          return `
            <div style="background:#1a1a2e;min-width:220px;border-radius:6px;overflow:hidden;">
              <div style="background:#000000;color:#FFFFFF;font-family:Roboto,sans-serif;font-weight:700;font-size:15px;padding:8px 14px;">${label}</div>
              <div style="padding:6px 14px;">${rows}</div>
            </div>`;
        },
      },
      dataLabels: { enabled: false },
    };

    await this._drawChart(options, sim);
  }

  // 17.10.2026: Zeichnen serialisiert (gleiches Muster wie _drawChart in
  // bitgrid_bar_trend_chart.js). Vorher konnten sich mehrere updateOptions()
  // ueberholen ("t.put is not a function"); der verworfene Chart wurde erst
  // beim naechsten Sim-Schritt neu gebaut, im ANGEHALTENEN Replay also nie:
  // die Karte blieb leer (Lab-Befund 12:30). Jetzt: nur ein Zeichenvorgang
  // zugleich, der juengste Wunsch wird danach nachgeholt, nach einem Fehler
  // wird einmal kurz darauf neu aufgebaut.
  async _drawChart(options, sim) {
    if (this._chartBusy) {
      this._pendingDraw = [options, sim];
      return;
    }
    this._chartBusy = true;
    let failed = false;
    try {
      if (this._apexChart) {
        // Im Lab-Replay (Update je Sim-Schritt) ohne Neuaufbau und ohne
        // Animation, sonst wuerde der Chart wie zuvor die Finanzen springen.
        await this._apexChart.updateOptions(options, !sim, !sim);
      } else {
        this._apexChart = new window.ApexCharts(this._chartEl, options);
        await this._apexChart.render();
      }
      this._lengthenMajorTicks();
    } catch (e) {
      failed = true;
      try {
        if (this._apexChart) this._apexChart.destroy();
      } catch (e2) {
        // ein halb aufgebauter Chart kann auch beim Aufraeumen werfen
      }
      this._apexChart = null;
    } finally {
      this._chartBusy = false;
    }
    if (this._pendingDraw) {
      const [nextOptions, nextSim] = this._pendingDraw;
      this._pendingDraw = null;
      await this._drawChart(nextOptions, nextSim);
    } else if (failed && !this._retryTimer && this.isConnected) {
      this._retryTimer = setTimeout(() => {
        this._retryTimer = null;
        if (!this._apexChart && this.isConnected) this._drawChart(options, sim);
      }, 500);
    }
  }

  // 12.09.2026, Nutzer-Wunsch "3h-Striche etwas laenger": ApexCharts kennt
  // fuer category-Achsen kein eingebautes Konzept von "Haupt-"/"Neben"-
  // Ticks (axisTicks.height gilt einheitlich fuer alle 25 Stunden-Ticks),
  // daher direkter DOM-Eingriff nach dem Rendern statt Config-Option: die
  // Tick-Linien liegen in derselben Reihenfolge wie categories (Index 0-24
  // = Stunde 0-24), jede 3. (vom Start aus, h%3===0, inkl. Index 24) wird
  // um EXTRA_TICK_LENGTH_PX verlaengert. Muss nach JEDEM render/
  // updateOptions erneut laufen, weil ApexCharts die Tick-Linien dabei
  // (zumindest teilweise) komplett neu zeichnet.
  // 26.09.2026, Bug gefunden (Nutzer-Meldung "Striche werden immer
  // groesser"): die Funktion las bisher die AKTUELLE y2 (moeglicherweise
  // schon von einem frueheren Aufruf verlaengert) und addierte erneut
  // EXTRA_TICK_LENGTH_PX drauf. _maybeRefresh() ruft _fetchAndRender() alle
  // 5 Minuten erneut auf; sobald ApexCharts ein konkretes <line>-Element
  // zwischen zwei updateOptions()-Aufrufen NICHT neu erzeugt (z.B. weil sich
  // an dessen Achsenposition nichts geaendert hat), kumulierte sich das den
  // ganzen Tag ueber: 5px, 10px, 15px, ... Fix: die urspruengliche Laenge
  // einmalig pro DOM-Element in einem data-Attribut sichern und IMMER von
  // dieser Basis aus rechnen, nie von der zuletzt gesetzten. Wird das
  // Element von ApexCharts doch neu erzeugt, fehlt das Attribut und die
  // neue Basis wird einfach neu gesichert, ganz ohne Kumulierung.
  _lengthenMajorTicks() {
    if (!this._chartEl) return;
    const EXTRA_TICK_LENGTH_PX = 5;
    const ticks = this._chartEl.querySelectorAll(".apexcharts-xaxis-tick");
    ticks.forEach((tick, i) => {
      if (i % 3 !== 0) return;
      const y1 = parseFloat(tick.getAttribute("y1"));
      if (tick.dataset.bgaiBaseY2 === undefined) {
        tick.dataset.bgaiBaseY2 = tick.getAttribute("y2");
      }
      const y2 = parseFloat(tick.dataset.bgaiBaseY2);
      if (Number.isNaN(y1) || Number.isNaN(y2)) return;
      const direction = Math.sign(y2 - y1) || 1;
      tick.setAttribute("y2", y2 + direction * EXTRA_TICK_LENGTH_PX);
    });
  }

  disconnectedCallback() {
    if (this._retryTimer) {
      clearTimeout(this._retryTimer);
      this._retryTimer = null;
    }
    if (this._apexChart) {
      this._apexChart.destroy();
      this._apexChart = null;
    }
  }
}

customElements.define("bitgrid-verlauf-chart", BitgridVerlaufChart);
