// BitGridAI — Bitcoin-Kurs-Chart als eigenstaendiges Custom-Element, gleiches
// Hausmuster wie www/bitgrid_regelschwellen_chart.js (raw ApexCharts statt
// Inline-SVG, damit derselbe durchgearbeitete Stil strukturell gilt: 17px-
// Achsen in Serienfarbe, Text-Halo, eigene HTML-Legende, gestricheltes
// Gitter, dropShadow, Custom-Tooltip).
//
// Ersetzt views/stats_btc_price.yaml (statisches 90-Tage-EUR-SVG) im Tab
// "BitcoinInfo", Nutzer-Vorgaben 25.09.2026:
//   1. Design an Regelschwellen angleichen (ApexCharts statt Hand-SVG,
//      Legende, beschriftete X-/Y-Achse in gleicher Schriftgroesse).
//   2. Dynamisch bis zum aktuellen Tag statt statischem 90-Tage-Fenster.
//   3. Zeitraum-Buttons 1 Tag/5 Tage/1 Monat/1 Jahr/5 Jahre/Max.
//   4. EUR/USD/Power-Law als drei "Seiten" umschaltbar per Pfeile + Titel in
//      der Mitte (gleiches Muster wie views/historie_zeitraum_cycler.yaml),
//      Legende passt sich der jeweiligen Seite an.
//
// Datenquelle EUR/USD: src/data/btc_price_history.py schreibt die VOLLE
// mempool.space-Rohaufloesung (stuendlich fuer die juengsten ~100 Tage,
// danach taeglich/woechentlich) als www/btc_price_full.json. Die Zeitraum-
// Buttons filtern client-seitig aus dieser einen Reihe — kein zweiter
// Datenabruf pro Zeitraum, kein Live-Netzwerkzugriff vom Wandtablet
// (fetch('/local/...') wie bei allen uebrigen JSON-Artefakten im Projekt).
//
// Datenquelle Power-Law: seit 26.09.2026 dieselbe USD-Reihe aus
// btc_price_full.json, Fit im Browser 1:1 wie src/data/btc_power_law.py
// (s. buildPowerLaw); vorher ein einmaliger Backfill in btc_power_law.json,
// der nie aktualisiert wurde. Aktueller Kurs live aus HA (s. _livePrice).
// Rendering hier bewusst NICHT ueber ApexCharts: der Log-Log-
// Raum mit Regressions-/Support-/Widerstandsgeraden ist bereits als Inline-
// SVG ausgereift (views/ki_powerlaw.yaml, seit 01.09.2026 unveraendert
// korrekt), ein voller Umbau auf ApexCharts haette nur Risiko ohne fachlichen
// Gewinn gebracht. Portiert wird nur die Mathematik, mit angeglichener
// Achsen-/Legendenschrift (Nutzer-Vorgabe 4: gleiche Schriftgroesse ueber
// alle Tabs).
//
// Aktualitaet (26.09.2026 geprueft und behoben): btc_price_full.json wurde
// auf .96 nie erneuert. Dort lief eine alte btc_price_history.py ohne den
// Voll-Export, und der Cron kopierte nur btc_price_eur.json. Seitdem schreibt
// der 30-Minuten-Cron auf .96 beide Dateien und kopiert beide nach HA. Die
// Power-Law ist damit hoechstens 30 Minuten alt, der Kurspunkt live.
//
// Kein Steuerpfad: reiner Marktkontext, beeinflusst keine Mining-Entscheidung
// in core/.

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

// Bitcoin-Rolle (bgai-mining-v3/bg-color-super), literal statt var(): ApexCharts
// loest CSS-Variablen in seinen Optionen nicht auf (gleiche Begruendung wie in
// bitgrid_regelschwellen_chart.js).
const COLOR_PRICE = "#F7931A";
const COLOR_REG = "#4CAF50"; // bg-color-eco
const COLOR_SUP = "#EF5350"; // bg-color-reserve

// 26.09.2026, Nutzer-Wunsch: Kurslinie gruen, wenn der gewaehlte Zeitraum
// im Plus liegt, rot im Minus (dieselben Tokens wie die Delta-Anzeige).
const COLOR_UP = "#4CAF50"; // bg-color-eco
const COLOR_DOWN = "#EF5350"; // bg-color-reserve
// 2-Year-MA-Korridor (Nutzer-Wunsch 26.09.2026, Vorbild "Bitcoin Investor
// Tool", lookintobitcoin.com): untere Linie = 730-Tage-Mittel, obere = das
// Fuenffache. Dort gruen/rot, hier bewusst NICHT, weil die Kurslinie selbst
// jetzt gruen/rot nach Zeitraum-Bilanz ist: Cyan (bg-color-standard) und
// Lila (wie die Power-Law-Widerstandslinie), beide gestrichelt.
const COLOR_MA = "#26C6DA"; // bg-color-standard
const COLOR_MA5 = "#AB7DF0";
const MA_DAYS = 730;
// Korridor nur auf den langen Zeitraeumen, dort mit logarithmischer Y-Achse
// (wie das Vorbild). Auf 1 Tag bis 1 Jahr liegt die x5-Linie beim Fuenffachen
// des Kursniveaus und wuerde den Kurs auf einer linearen Achse zu einem
// flachen Strich stauchen; die aktuellen Werte stehen dort in der Legende.
const CORRIDOR_RANGES = new Set(["5j", "max"]);

const PAGES = [
  { key: "eur", title: "BTC / EUR", icon: "mdi:currency-eur" },
  { key: "usd", title: "BTC / USD", icon: "mdi:currency-usd" },
  { key: "powerlaw", title: "POWER-LAW", icon: "mdi:chart-line-variant" },
];

const RANGES = [
  { key: "1t", label: "1 Tag", secs: 1 * 86400 },
  { key: "5t", label: "5 Tage", secs: 5 * 86400 },
  { key: "1m", label: "1 Monat", secs: 30 * 86400 },
  { key: "1j", label: "1 Jahr", secs: 365 * 86400 },
  { key: "5j", label: "5 Jahre", secs: 5 * 365 * 86400 },
  { key: "max", label: "Max", secs: Infinity },
];

const GENESIS_MS = Date.UTC(2009, 0, 3);

function fmtMoney(v, unit) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const opts = v >= 1000 ? { maximumFractionDigits: 0 } : { maximumFractionDigits: 2 };
  return v.toLocaleString("de-DE", opts) + " " + unit;
}

// Grosse Betraege kompakt, deutsch: 1.480.000.000.000 -> "1,48 Bio. €".
function fmtCompact(v, unit) {
  if (v === null || v === undefined || !Number.isFinite(v)) return "—";
  return new Intl.NumberFormat("de-DE", { notation: "compact", maximumFractionDigits: 2 }).format(v) + " " + unit;
}

function fmtDay(sec) {
  return new Date(sec * 1000).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
}

// Tagesschlusskurse: je UTC-Tag der letzte verfuegbare Wert, Luecken per
// Forward-Fill. Noetig, weil die Rohreihe gemischt aufgeloest ist (stuendlich
// ~100 Tage, dann taeglich, aelter woechentlich): ein Mittel direkt ueber die
// Rohpunkte wuerde den stuendlichen Abschnitt 24-fach gewichten. Mit einem
// Wert pro Tag entspricht das 730-Tage-Mittel dem ueblichen 2-Year-MA auf
// Tagesschlusskursen (bei woechentlicher Altdaten-Aufloesung eine Naeherung).
function dailyCloses(points, idx) {
  const DAY = 86400;
  const valid = points.filter((p) => p[idx] !== null && p[idx] !== undefined);
  if (valid.length < 2) return [];
  const firstDay = Math.floor(valid[0][0] / DAY);
  const lastDay = Math.floor(valid[valid.length - 1][0] / DAY);
  const out = [];
  let j = 0;
  let last = null;
  for (let day = firstDay; day <= lastDay; day++) {
    const dayEnd = (day + 1) * DAY;
    while (j < valid.length && valid[j][0] < dayEnd) {
      last = valid[j][idx];
      j++;
    }
    if (last !== null) out.push([day * DAY, last]);
  }
  return out;
}

// Gleitendes Mittel ueber n Tageswerte, erst ab dem n-ten Tag definiert.
function movingAverage(daily, n) {
  const out = [];
  let sum = 0;
  for (let i = 0; i < daily.length; i++) {
    sum += daily[i][1];
    if (i >= n) sum -= daily[i - n][1];
    if (i >= n - 1) out.push([daily[i][0], sum / n]);
  }
  return out;
}

// Ausgegebene BTC bis einschliesslich Block `height`, deterministisch aus dem
// Halving-Plan (50 BTC, Halbierung alle 210.000 Bloecke). Grundlage der
// Marktkapitalisierung, damit sie lokal aus sensor.bitcoin_block_height
// entsteht statt aus einer externen Marktdaten-API. Genesis-Block (nicht
// ausgebbar) ist wie bei den ueblichen Supply-Angaben enthalten.
function btcSupplyAtHeight(height) {
  let blocks = Math.floor(height) + 1;
  let reward = 50;
  let supply = 0;
  while (blocks > 0 && reward >= 1e-8) {
    const n = Math.min(blocks, 210000);
    supply += n * reward;
    blocks -= n;
    reward /= 2;
  }
  return supply;
}

// ── Power-Law nach bitcoinpower.law (26.09.2026, abends) ─────────────────
// Nutzer-Vorgabe "Power-Law-Chart ist nicht richtig, siehe
// https://bitcoinpower.law/": dessen festes Modell statt eines eigenen Fits.
// Aus dem Seitenquelltext uebernommen (calculatePrice), am 26.09.2026
// gelesen:
//   fairer Preis (USD) = 10^-16.493 * Tage_seit_Genesis^5.688
//   Boden              = 0,40 * fairer Preis ("Power Law Support (-60%)")
// Genesis = 03.01.2009. Einen Deckel/Widerstand zeigt die Referenz nicht
// (ihre "Peak Estimation" ist im Quelltext auskommentiert), deshalb auch hier
// nicht. Vorher: eigener OLS-Fit ueber die USD-Tageswerte mit +/-2 Sigma-Band
// (Steigung 5,49, heute ca. 20 % unter der Referenz). Zwei Modelle nebeneinander
// waeren fuer den Nutzer nicht nachvollziehbar; die Referenz ist verbreitet
// und vergleichbar. Deterministisch, reine Anzeige, kein Einfluss auf core/.
const GENESIS_DAY = Math.floor(GENESIS_MS / 86400000);
const PL_LOG_A = -16.493;
const PL_EXP = 5.688;
const PL_SUPPORT_FACTOR = 0.4;
// Sichtfenster der Power-Law-Seite (s. _renderPowerlaw).
// Zweite Vorgabe am selben Abend: Zeitachse ab 2010 (erster Boersenkurs,
// wie die Referenz), Ende 2040 bleibt.
const PL_VIEW_TO = 2040;

// 15.10.2026, Lab-Replay: solange simulation_mode an ist und das Lab-Profil
// existiert (sensor.lab_sim_profile = Sim-Datum, sensor.lab_sim_clock = HH:MM,
// beides nur im Lab), gilt das Sim-Datum als "heute". In Prod immer null.
function simToday(hass) {
  const st = hass && hass.states;
  if (!st || st["input_boolean.simulation_mode"]?.state !== "on") return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(st["sensor.lab_sim_profile"]?.state || "");
  if (!m) return null;
  const c = /^(\d{2}):(\d{2})$/.exec(st["sensor.lab_sim_clock"]?.state || "");
  return new Date(+m[1], +m[2] - 1, +m[3], c ? +c[1] : 12, c ? +c[2] : 0);
}

// Sekunden-Variante fuer die Zeitachse (Sim-Zeitpunkt), sonst null.
function simNowSec(hass) {
  const d = simToday(hass);
  return d ? Math.floor(d.getTime() / 1000) : null;
}

function buildPowerLaw(points) {
  const byDay = new Map();
  for (const p of points) {
    const v = p[2];
    if (v === null || v === undefined) continue;
    const day = Math.floor(p[0] / 86400) - GENESIS_DAY;
    if (!byDay.has(day)) byDay.set(day, v);
  }
  const prices = [...byDay.entries()].filter(([d, v]) => d > 0 && v > 0).sort((x, y) => x[0] - y[0]);
  if (prices.length < 2) return null;
  // Fuer die Euro-Anzeige (s. _renderPowerlaw): echte Euro-Tageswerte (je
  // UTC-Tag der erste, wie oben) und der juengste USD/EUR-Kurs aus der Reihe
  // als Rueckfall, falls die Live-Sensoren fehlen. Das Modell bleibt USD.
  const eurByDay = new Map();
  let lastRatio = null;
  for (const p of points) {
    if (p[1] === null || p[1] === undefined || p[1] <= 0) continue;
    const day = Math.floor(p[0] / 86400) - GENESIS_DAY;
    if (!eurByDay.has(day)) eurByDay.set(day, p[1]);
    if (p[2] !== null && p[2] !== undefined && p[2] > 0) lastRatio = p[2] / p[1];
  }
  const eurPrices = [...eurByDay.entries()].filter(([d]) => d > 0).sort((x, y) => x[0] - y[0]);
  return { prices, eurPrices, lastRatio };
}

// Y-Achse der Power-Law-Seite: Nutzer-Wunsch 26.09.2026 "10k, 100k, 1 Mio,
// 10 Mio" statt voller Zahlen ("10.000.000" passte nicht in den linken Rand
// und wurde zu "0.000.000" abgeschnitten).
function fmtPlAxis(v) {
  if (v >= 1e6) return (v / 1e6).toLocaleString("de-DE") + " Mio";
  if (v >= 1e3) return (v / 1e3).toLocaleString("de-DE") + "k";
  return v.toLocaleString("de-DE");
}

// Achsenbeschriftung auf der Log-Achse: 2 signifikante Stellen, damit aus
// 10^4.5 = 31.622 ein lesbares "32.000" wird.
function fmtLogTick(p) {
  if (!Number.isFinite(p) || p <= 0) return "";
  if (p < 1) return p.toLocaleString("de-DE", { maximumSignificantDigits: 2 });
  const mag = Math.pow(10, Math.floor(Math.log10(p)) - 1);
  return (Math.round(p / mag) * mag).toLocaleString("de-DE");
}

class BitgridBtcKursChart extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._page = 0;
    this._range = "1m";
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
        :host { display: block; }
        /* Anders als bitgrid_regelschwellen_chart.js sitzt dieses Element
           NICHT in einem gemeinsam umrandeten Stack, sondern direkt als
           eigene Kachel im Grid von bitgrid_dashboard_v3.yaml (vorher
           stats_btc_price.yaml mit denselben vier Werten) — braucht deshalb
           die volle Kartenhuelle selbst. */
        .bgai-card {
          box-sizing: border-box;
          padding: 14px 18px;
          background: var(--ha-card-background);
          border-radius: var(--bgai-card-radius-v3);
          border: var(--bgai-card-border-width-v3) solid var(--bgai-card-border-v3);
          box-shadow: var(--bgai-card-shadow-v3);
          overflow: hidden;
        }

        /* Seiten-Umschalter: Pfeile links/rechts, Titel mittig, exakt das
           Muster aus views/historie_zeitraum_cycler.yaml. */
        .bgai-cycler {
          display: grid;
          grid-template-columns: auto minmax(0, 1fr) auto;
          align-items: center;
          margin-bottom: 6px;
        }
        .bgai-cycler-arrow {
          cursor: pointer;
          color: var(--bgai-section-label-v3);
          filter: var(--bgai-header-icon-halo-v3);
          --mdc-icon-size: 30px;
          width: 30px; height: 30px;
        }
        .bgai-cycler-title {
          text-align: center;
          font-size: var(--bg-fs-group-header);
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.07em;
          color: var(--bgai-section-label-v3);
          text-shadow: var(--bgai-header-halo-v3);
        }

        /* Waagerechte Trenner (27.09.2026, Nutzer-Wunsch): einer zwischen
           Seitentitel und Kurs, einer unter den Zeitraum-Pillen. Gleiches
           Muster wie die Linie ueber der Legende (Gradient, an den Raendern
           auslaufend), damit die Karte nur EINE Art Trennlinie kennt. Gilt
           fuer alle Seiten des Cyclers, also auch BTC/USD. */
        .bgai-sep {
          height: 2px; margin: 0 2px 10px;
          background-image: linear-gradient(to right, transparent, var(--divider-color) 15%, var(--divider-color) 85%, transparent);
        }

        /* Header: aktueller Preis + Veraenderung im gewaehlten Zeitraum.
           26.09.2026, Nutzer-Wunsch: Kurs und Zeitraum-Pillen mittig. */
        .bgai-header { display: flex; align-items: baseline; justify-content: center; flex-wrap: wrap; gap: 10px; margin: 4px 2px 10px; }
        .bgai-price { font-size: var(--bg-fs-title); font-weight: 700; color: var(--primary-text-color); white-space: nowrap; }
        .bgai-delta { font-size: var(--bg-fs-secondary); font-weight: 600; white-space: nowrap; }

        /* Zeitraum-Pillen. */
        .bgai-ranges { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin: 0 2px 10px; }
        .bgai-range-btn {
          cursor: pointer;
          padding: 4px 10px;
          border-radius: 999px;
          font-size: var(--bg-fs-secondary);
          font-weight: 600;
          color: var(--secondary-text-color);
          background: var(--bgai-pill-bg-v3);
          user-select: none;
        }
        .bgai-range-btn.active { color: var(--primary-text-color); background: var(--secondary-background-color); }

        #chart { width: 100%; }
        #powerlaw { width: 100%; }
        .bgai-msg { padding: 30px 0; text-align: center; color: var(--secondary-text-color); font-size: var(--bg-fs-body); }

        /* Legende, Halo — 1:1 aus bitgrid_regelschwellen_chart.js, damit die
           Optik ueber beide Charts identisch ist. */
        .bgai-legend {
          display: flex; flex-wrap: wrap; justify-content: center; align-items: center;
          column-gap: 16px; row-gap: 4px; padding-top: 12px; margin-top: 8px;
          background-image: linear-gradient(to right, transparent, var(--divider-color) 15%, var(--divider-color) 85%, transparent);
          background-repeat: no-repeat; background-size: 100% 2px; background-position: top;
        }
        /* Spalten-Variante der Legende (27.09.2026, Nutzer-Wunsch): drei
           Dreier-Gruppen nebeneinander, jede untereinander gelesen, dazwischen
           senkrechte Trenner. Nur auf den Kurs-Seiten (EUR/USD); die Power-
           Law-Seite befuellt denselben Container weiterhin als eine Reihe. */
        .bgai-legend--cols { align-items: stretch; column-gap: 14px; row-gap: 10px; }
        .bgai-legend-col { display: flex; flex-direction: column; justify-content: center; gap: 4px; }
        .bgai-legend-sep { width: 1px; flex: 0 0 auto; align-self: stretch; background: var(--divider-color); }
        .bgai-legend-item { display: flex; align-items: center; gap: 6px; font-size: 16px; font-family: Roboto, sans-serif; font-weight: 400; text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9); }
        /* 27.09.2026, Nutzer-Wunsch "Schrift kleiner, damit alles in eine
           Reihe passt": Schriftgroesse der Spalten-Legende steuert _fitLegend()
           ueber diese Variable, Icons und Striche skalieren mit. Eine feste
           px-Zahl waere entweder auf dem Desktop unnoetig klein oder auf dem
           Wandtablet immer noch zu breit. */
        .bgai-legend--cols .bgai-legend-item { font-size: var(--bgai-legend-fs, 16px); gap: 5px; white-space: nowrap; }
        .bgai-legend--cols .bgai-legend-dot { --mdc-icon-size: calc(var(--bgai-legend-fs, 16px) * 1.2); width: calc(var(--bgai-legend-fs, 16px) * 1.2); height: calc(var(--bgai-legend-fs, 16px) * 1.2); }
        .bgai-legend--cols .bgai-legend-dash { width: calc(var(--bgai-legend-fs, 16px) * 1.3); }
        .bgai-legend-dot { --mdc-icon-size: 20px; width: 20px; height: 20px; flex: 0 0 auto; filter: drop-shadow(0 0 3px rgba(0,0,0,.9)) drop-shadow(0 0 3px rgba(0,0,0,.9)); }
        .bgai-legend-line { width: 20px; height: 3px; border-radius: 2px; flex: 0 0 auto; box-shadow: 0 0 3px rgba(0,0,0,.9); }
        /* Gestricheltes Legenden-Muster fuer die 2J-MA-Korridorlinien. */
        .bgai-legend-dash { width: 22px; height: 3px; flex: 0 0 auto; }
        .apexcharts-text, .apexcharts-xaxis-annotation-label, .apexcharts-yaxis-annotation-label { text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9) !important; }
      </style>
      <div class="bgai-card">
        <div class="bgai-cycler">
          <ha-icon class="bgai-cycler-arrow" id="prev" icon="mdi:chevron-left"></ha-icon>
          <div class="bgai-cycler-title" id="title"></div>
          <ha-icon class="bgai-cycler-arrow" id="next" icon="mdi:chevron-right"></ha-icon>
        </div>
        <div class="bgai-sep"></div>
        <div id="header" class="bgai-header"></div>
        <div id="ranges" class="bgai-ranges"></div>
        <div id="sepRanges" class="bgai-sep"></div>
        <div id="priceView">
          <div id="chart"></div>
        </div>
        <div id="powerlawView" style="display:none">
          <div id="powerlaw"></div>
        </div>
        <div id="legend" class="bgai-legend"></div>
      </div>
    `;
    this._titleEl = root.getElementById("title");
    this._headerEl = root.getElementById("header");
    this._rangesEl = root.getElementById("ranges");
    this._sepRangesEl = root.getElementById("sepRanges");
    this._priceViewEl = root.getElementById("priceView");
    this._powerlawViewEl = root.getElementById("powerlawView");
    this._chartEl = root.getElementById("chart");
    this._powerlawEl = root.getElementById("powerlaw");
    this._legendEl = root.getElementById("legend");

    root.getElementById("prev").addEventListener("click", () => this._changePage(-1));
    root.getElementById("next").addEventListener("click", () => this._changePage(1));
  }

  _changePage(dir) {
    this._page = (this._page + dir + PAGES.length) % PAGES.length;
    this._render();
  }

  _changeRange(key) {
    this._range = key;
    this._render();
  }

  async _maybeRefresh() {
    if (!this._hass) return;
    const now = Date.now();
    // 5-Minuten-Cache: die Artefakte aktualisieren sich per Cron/manuellem
    // Skript-Lauf, nicht bei jedem hass-Update (gleiches Muster wie die
    // History-Abfrage in bitgrid_regelschwellen_chart.js).
    // 26.09.2026, gleicher Bug wie bitgrid_verlauf_chart.js: disconnectedCallback()
    // zerstoert this._apexChart beim View-Wechsel; _render() baut sie zwar bei
    // Bedarf neu auf, wurde aber innerhalb der Cache-Frist nie erreicht.
    if (this._apexChart && this._lastFetch && now - this._lastFetch < 5 * 60 * 1000) {
      this._applySimCut();
      this._render();
      return;
    }
    this._lastFetch = now;
    await this._fetchData();
    this._render();
  }

  async _fetchData() {
    try {
      this._rawPriceData = await fetch("/local/btc_price_full.json?v=" + Date.now()).then((r) => r.json());
    } catch (e) {
      this._rawPriceData = null;
    }
    this._cutKey = undefined;
    this._applySimCut();
  }

  // 15.10.2026, Lab-Replay: Kurshistorie nur bis vor den Sim-Tag (s. simToday),
  // der Sim-Kurs des Tages kommt als Live-Punkt dazu (s. _livePrice). Sonst
  // haengt der Juli-Kurs an der Oktober-Kurve und sieht wie ein Absturz aus.
  // Ohne Replay: unveraendert die volle Reihe.
  _applySimCut() {
    const sim = simToday(this._hass);
    const cutoff = sim ? new Date(sim.getFullYear(), sim.getMonth(), sim.getDate()).getTime() / 1000 : null;
    // Darstellungs-Versatz des Replays (Datenbasis 11.07., gezeigt als 21.07.,
    // build_sim_day.py "Display date"): die Kursreihe rueckt um dieselben Tage,
    // damit die Achse zum gezeigten Datum passt.
    const offDays = sim ? Number(this._hass.states["sensor.lab_sim_profile"]?.attributes?.display_offset_days) || 0 : 0;
    const key = cutoff === null ? "live" : `${cutoff}|${offDays}`;
    if (key === this._cutKey) return;
    this._cutKey = key;
    const raw = this._rawPriceData;
    if (raw && Array.isArray(raw.points) && cutoff !== null) {
      const shift = offDays * 86400;
      const pts = shift ? raw.points.map((p) => [p[0] + shift, p[1], p[2]]) : raw.points;
      this._priceData = { ...raw, points: pts.filter((p) => p[0] < cutoff) };
    } else {
      this._priceData = raw;
    }
    // Power-Law aus derselben Reihe (s. buildPowerLaw), btc_power_law.json
    // wird von dieser Karte nicht mehr gelesen.
    const pts = this._priceData && Array.isArray(this._priceData.points) ? this._priceData.points : null;
    this._powerlawData = pts ? buildPowerLaw(pts) : null;
    // 2J-MA je Waehrung einmal pro Datenstand berechnen, nicht bei jedem
    // Render (Zeitraum-/Seitenwechsel), s. _movingAverage().
    this._maCache = {};
  }

  // Live-Kurs aus HA (REST-Sensor gegen die self-hosted mempool-Instanz,
  // alle 5 min, packages/pool.yaml). Die Kurshistorie im JSON wird nur
  // periodisch erzeugt; mit dem Live-Wert als letztem Punkt zeigen Header,
  // Legende und Power-Law-Marker immer den heutigen Stand. Kein eigener
  // Netzwerkzugriff des Wandtablets: der Wert kommt aus dem HA-Zustand.
  // USD (sensor.btc_usd_price) steht aus derselben mempool-Antwort bereit;
  // fehlt der Sensor, gilt wie bisher der letzte Wert der Historie.
  _livePrice(currencyKey) {
    const id = currencyKey === "eur" ? "sensor.btc_eur_price" : "sensor.btc_usd_price";
    const st = this._hass && this._hass.states[id];
    const v = parseFloat(st && st.state);
    if (!Number.isFinite(v) || v <= 0) return null;
    const sim = simNowSec(this._hass);
    if (sim !== null) return { price: v, sec: sim };
    const t = Date.parse((st && (st.last_reported || st.last_updated)) || "");
    return { price: v, sec: Number.isFinite(t) ? Math.floor(t / 1000) : Math.floor(Date.now() / 1000) };
  }

  _movingAverage(currencyKey, idx) {
    if (!this._maCache) this._maCache = {};
    if (!this._maCache[currencyKey]) {
      this._maCache[currencyKey] = movingAverage(dailyCloses(this._priceData.points, idx), MA_DAYS);
    }
    return this._maCache[currencyKey];
  }

  _render() {
    if (!this._titleEl) return;
    const page = PAGES[this._page];
    this._titleEl.textContent = page.title;

    const isPowerlaw = page.key === "powerlaw";
    this._rangesEl.style.display = isPowerlaw ? "none" : "flex";
    // Der zweite Trenner gehoert zu den Zeitraum-Pillen: ohne sie staende er
    // direkt unter dem ersten.
    this._sepRangesEl.style.display = isPowerlaw ? "none" : "block";
    this._priceViewEl.style.display = isPowerlaw ? "none" : "block";
    this._powerlawViewEl.style.display = isPowerlaw ? "block" : "none";

    if (isPowerlaw) {
      this._headerEl.innerHTML = "";
      this._renderPowerlaw();
    } else {
      this._renderRangeButtons();
      this._renderPriceChart(page.key);
    }
  }

  _renderRangeButtons() {
    this._rangesEl.innerHTML = "";
    RANGES.forEach((r) => {
      const btn = document.createElement("span");
      btn.className = "bgai-range-btn" + (r.key === this._range ? " active" : "");
      btn.textContent = r.label;
      btn.addEventListener("click", () => this._changeRange(r.key));
      this._rangesEl.appendChild(btn);
    });
  }

  _renderPriceChart(currencyKey) {
    const unit = currencyKey === "eur" ? "€" : "$";
    const idx = currencyKey === "eur" ? 1 : 2;
    const data = this._priceData;

    if (!data || !Array.isArray(data.points) || data.points.length < 2) {
      this._headerEl.innerHTML = "";
      this._legendEl.innerHTML = "";
      this._chartEl.innerHTML = `<div class="bgai-msg">${
        data ? "Zu wenig Kursverlauf geladen." : "Lade Kursverlauf …"
      }</div>`;
      return;
    }

    const points = data.points;
    const nowSec = simNowSec(this._hass) ?? Math.floor(Date.now() / 1000);
    const rangeSecs = RANGES.find((r) => r.key === this._range).secs;
    const cutoff = rangeSecs === Infinity ? -Infinity : nowSec - rangeSecs;
    const series = points
      .filter((p) => p[0] >= cutoff && p[idx] !== null && p[idx] !== undefined)
      .map((p) => [p[0] * 1000, p[idx]]);

    if (series.length < 2) {
      this._headerEl.innerHTML = "";
      this._legendEl.innerHTML = "";
      this._chartEl.innerHTML = `<div class="bgai-msg">Zu wenig Kursverlauf im gewaehlten Zeitraum.</div>`;
      return;
    }

    const range = RANGES.find((r) => r.key === this._range);

    // Live-Kurs als juengsten Punkt anhaengen, wenn er neuer ist als die
    // Historie (s. _livePrice). Header, Zeitraum-Delta, Linienfarbe und
    // Hoch/Tief 24h beziehen sich damit auf heute, nicht auf den letzten
    // Lauf des Historien-Skripts.
    const live = this._livePrice(currencyKey);
    if (live && live.sec * 1000 > series[series.length - 1][0]) {
      series.push([live.sec * 1000, live.price]);
    }

    // ── Header: aktueller Preis + Veraenderung im GEWAEHLTEN Zeitraum ────
    // 26.09.2026, Nutzer-Befund (Bug): der Header zeigte unabhaengig vom
    // Zeitraum-Button immer die 24h-Veraenderung. Jetzt erster gegen letzten
    // Punkt des sichtbaren Zeitraums, beschriftet mit dem Buttonnamen. Die
    // 24h-Spanne steht weiterhin in der Legende (Hoch/Tief 24h).
    const current = series[series.length - 1][1];
    const first = series[0][1];
    const deltaPct = first > 0 ? ((current - first) / first) * 100 : null;
    const lineColor = deltaPct === null || deltaPct >= 0 ? COLOR_UP : COLOR_DOWN;
    const deltaColor = deltaPct === null ? "var(--secondary-text-color)" : lineColor;
    const deltaStr = deltaPct === null
      ? "—"
      : (deltaPct >= 0 ? "+" : "") + deltaPct.toLocaleString("de-DE", { maximumFractionDigits: 1 }) + ` % (${range.label})`;
    this._headerEl.innerHTML = `
      <span class="bgai-price">${fmtMoney(current, unit)}</span>
      <span class="bgai-delta" style="color:${deltaColor}">${deltaStr}</span>
    `;

    // ── 2-Year-MA-Korridor ──────────────────────────────────────────────
    const ma = this._movingAverage(currencyKey, idx);
    const maNow = ma.length ? ma[ma.length - 1][1] : null;
    const showCorridor = CORRIDOR_RANGES.has(this._range) && ma.length > 0;
    const maSeries = showCorridor ? ma.filter(([t]) => t >= cutoff).map(([t, v]) => [t * 1000, v]) : [];
    const ma5Series = maSeries.map(([t, v]) => [t, v * 5]);

    // ── Kennzahlen fuer die Legende, alle lokal berechnet ───────────────
    // Hoch/Tief 24h: aus den stuendlichen Rohpunkten der letzten 24h vor dem
    // juengsten Punkt (nicht vor "jetzt", falls das Artefakt etwas aelter ist).
    const lastSec = series[series.length - 1][0] / 1000;
    const win24 = points.filter((p) => p[0] >= lastSec - 86400 && p[idx] !== null && p[idx] !== undefined).map((p) => p[idx]);
    if (live) win24.push(live.price);
    const hi24 = win24.length ? Math.max(...win24) : null;
    const lo24 = win24.length ? Math.min(...win24) : null;
    // Allzeithoch: hoechster Wert der verfuegbaren Reihe. Die Reihe ist fuer
    // aeltere Zeitraeume nur taeglich/woechentlich aufgeloest, ein kurzes
    // Intraday-Hoch einer Boerse kann also etwas hoeher gelegen haben.
    let ath = null;
    let athSec = null;
    points.forEach((p) => {
      const v = p[idx];
      if (v !== null && v !== undefined && (ath === null || v > ath)) {
        ath = v;
        athSec = p[0];
      }
    });
    if (live && (ath === null || live.price > ath)) {
      ath = live.price;
      athSec = live.sec;
    }
    // Marktkapitalisierung: Kurs x ausgegebene BTC laut Halving-Plan bei der
    // aktuellen Blockhoehe (kein externer Marktdaten-Abruf noetig).
    const height = parseFloat(this._hass?.states["sensor.bitcoin_block_height"]?.state);
    const mcap = Number.isFinite(height) && height > 0 ? current * btcSupplyAtHeight(height) : null;

    // Netzwerk-Kennzahlen aus der self-hosted mempool-Instanz (27.09.2026,
    // Nutzer-Wunsch "Mining-Difficulty und Halving-Datum aus mempool"):
    // beide Sensoren existieren bereits in packages/bitcoin.yaml und ziehen
    // aus derselben LAN-Instanz, kein neuer externer Abruf.
    //   difficulty  = sensor.bitcoin_network_difficulty (/api/v1/mining/hashrate/3d)
    //   Halving     = sensor.bitcoin_next_halving, Attribut next_halving_date
    // Das Halving-Datum ist eine Hochrechnung mit der Ziel-Blockzeit 600 s
    // (s. Kommentar am Sensor), deshalb hier als "ca." beschriftet statt als
    // feststehender Termin.
    const diffT = parseFloat(this._hass?.states["sensor.bitcoin_network_difficulty"]?.state);
    const diffStr = Number.isFinite(diffT)
      ? diffT.toLocaleString("de-DE", { maximumFractionDigits: 2 }) + " T"
      : "—";
    const halvingIso = this._hass?.states["sensor.bitcoin_next_halving"]?.attributes?.next_halving_date;
    const halvingMs = halvingIso ? Date.parse(halvingIso) : NaN;
    const halvingStr = Number.isFinite(halvingMs) ? "ca. " + fmtDay(halvingMs / 1000) : "—";

    // ── Legende ─────────────────────────────────────────────────────────
    // 27.09.2026, Nutzer-Wunsch: drei Dreier-Gruppen nebeneinander statt
    // einer langen Reihe, senkrecht getrennt. Links die 24h-Marktsicht,
    // mittig die im Chart gezeichneten Serien (deshalb dort die Serienfarben),
    // rechts die langfristigen Netzwerk-Eckdaten. Handelsvolumen fehlt
    // weiterhin bewusst: es steht in keiner lokalen Quelle und liesse sich nur
    // ueber eine externe Marktdaten-API holen (CLAUDE.md: keine externen APIs
    // ohne lokale Alternative).
    this._legendEl.innerHTML = "";
    this._legendEl.classList.add("bgai-legend--cols");
    const neutral = "var(--secondary-text-color)";
    const mkItem = (swatch, color, text) => {
      const item = document.createElement("span");
      item.className = "bgai-legend-item";
      let sw;
      if (swatch === "dash") {
        sw = document.createElement("span");
        sw.className = "bgai-legend-dash";
        sw.style.background = `repeating-linear-gradient(to right, ${color} 0 6px, transparent 6px 9px)`;
      } else {
        sw = document.createElement("ha-icon");
        sw.className = "bgai-legend-dot";
        sw.setAttribute("icon", swatch);
        sw.style.color = color;
      }
      const label = document.createElement("span");
      label.style.color = color;
      label.textContent = text;
      item.appendChild(sw);
      item.appendChild(label);
      return item;
    };
    const mkCol = (items) => {
      const col = document.createElement("div");
      col.className = "bgai-legend-col";
      items.filter(Boolean).forEach((i) => col.appendChild(i));
      return col;
    };
    const mkSep = () => {
      const sep = document.createElement("span");
      sep.className = "bgai-legend-sep";
      return sep;
    };

    const colLeft = mkCol([
      mkItem("mdi:arrow-up-bold", neutral, `Hoch 24h: ${fmtMoney(hi24, unit)}`),
      mkItem("mdi:arrow-down-bold", neutral, `Tief 24h: ${fmtMoney(lo24, unit)}`),
      mkItem("mdi:chart-pie", neutral, `Marktkap.: ${fmtCompact(mcap, unit)}`),
    ]);
    const colMid = mkCol([
      mkItem(currencyKey === "eur" ? "mdi:currency-eur" : "mdi:currency-usd", lineColor, `Kurs: ${fmtMoney(current, unit)}`),
      maNow !== null ? mkItem("dash", COLOR_MA, `2J-MA: ${fmtMoney(maNow, unit)}`) : null,
      maNow !== null ? mkItem("dash", COLOR_MA5, `2J-MA ×5: ${fmtMoney(maNow * 5, unit)}`) : null,
    ]);
    const colRight = mkCol([
      mkItem("mdi:trophy-outline", neutral, `Allzeithoch: ${fmtMoney(ath, unit)}${athSec ? ` (${fmtDay(athSec)})` : ""}`),
      mkItem("mdi:speedometer", neutral, `Mining-Difficulty: ${diffStr}`),
      mkItem("mdi:content-cut", neutral, `Halving: ${halvingStr}`),
    ]);
    this._legendEl.append(colLeft, mkSep(), colMid, mkSep(), colRight);
    this._fitLegend();

    this._renderApexChart(series, unit, { lineColor, maSeries, ma5Series, log: showCorridor });
  }

  // Groesste Schriftgroesse waehlen, bei der die drei Legenden-Gruppen noch in
  // EINE Reihe passen (27.09.2026, Nutzer-Wunsch). Bewusst am echten Layout
  // gemessen statt mit geschaetzten Zeichenbreiten gerechnet: umgebrochen ist
  // die Legende genau dann, wenn die Gruppen nicht mehr alle auf derselben
  // Hoehe sitzen. Stufen sind fest und werden in fester Reihenfolge geprueft,
  // das Ergebnis haengt nur von der Kartenbreite ab.
  // Reicht auch die kleinste Stufe nicht, bleibt der bisherige Umbruch:
  // lieber zweizeilig als abgeschnitten (die Karte hat overflow:hidden).
  _fitLegend() {
    const el = this._legendEl;
    if (!el || !el.classList.contains("bgai-legend--cols")) return;
    // Unsichtbare Karte (anderer Tab): alle offsetTop sind 0, die Messung
    // waere wertlos. Der naechste Render bei sichtbarer Karte holt das nach.
    if (!el.clientWidth) return;
    const cols = Array.from(el.children);
    if (cols.length < 2) return;
    for (const size of [16, 15, 14, 13, 12, 11, 10]) {
      el.style.setProperty("--bgai-legend-fs", size + "px");
      const top = cols[0].offsetTop;
      if (cols.every((c) => c.offsetTop === top)) return;
    }
  }

  async _renderApexChart(series, unit, opts = {}) {
    try {
      await loadApexCharts();
    } catch (e) {
      this._chartEl.textContent = "ApexCharts konnte nicht geladen werden.";
      return;
    }

    const { lineColor = COLOR_PRICE, maSeries = [], ma5Series = [], log = false } = opts;

    // Log-Achse fuer den 2J-MA-Korridor (5 Jahre/Max): Werte als log10 auf
    // einer LINEAREN Achse, Beschriftung zurueckgerechnet. Bewusst nicht
    // ApexCharts' yaxis.logarithmic: das rastet Min/Max auf ganze Zehner-
    // potenzen ein (5 Jahre: 10.000 bis 1.000.000), der Kurs saesse wieder
    // gestaucht im unteren Drittel. So sitzen die Grenzen auf Viertel-/
    // halben/ganzen Dekaden knapp um die Daten.
    const tf = log ? (v) => Math.log10(v) : (v) => v;
    const inv = log ? (v) => Math.pow(10, v) : (v) => v;
    const toApex = (arr) => arr.filter(([, v]) => v > 0 || !log).map(([t, v]) => [t, tf(v)]);

    const apexSeries = [{ name: "Kurs", type: "area", data: toApex(series) }];
    const colors = [lineColor];
    const widths = [2];
    const dashes = [0];
    const fillTypes = ["gradient"];
    if (maSeries.length) {
      apexSeries.push({ name: "2J-MA", type: "line", data: toApex(maSeries) });
      apexSeries.push({ name: "2J-MA ×5", type: "line", data: toApex(ma5Series) });
      colors.push(COLOR_MA, COLOR_MA5);
      widths.push(1.5, 1.5);
      dashes.push(6, 6);
      fillTypes.push("solid", "solid");
    }

    let yRange = {};
    if (log) {
      const all = apexSeries.flatMap((s) => s.data.map((p) => p[1])).filter(Number.isFinite);
      const lo = Math.min(...all);
      const hi = Math.max(...all);
      const span = hi - lo;
      const step = span > 3 ? 1 : span > 1.5 ? 0.5 : 0.25;
      const yMin = Math.floor(lo / step) * step;
      const yMax = Math.ceil(hi / step) * step;
      yRange = { min: yMin, max: yMax, tickAmount: Math.max(1, Math.round((yMax - yMin) / step)) };
    }

    // 26.09.2026, Nutzer-Wunsch: Y-Achse (Titel + Werte) in Weiss statt in
    // der Kursfarbe, die Kurslinie selbst traegt jetzt die Gruen/Rot-Bilanz.
    const yTitle = (unit === "€" ? "Preis (€" : "Preis ($") + (log ? ", log)" : ")");
    const options = {
      chart: {
        type: "line",
        height: this._config.height || 260,
        toolbar: { show: false },
        zoom: { enabled: false },
        background: "transparent",
        foreColor: "#FFFFFF",
        dropShadow: { enabled: true, top: 0, left: 0, blur: 3, opacity: 0.5 },
        animations: { enabled: false },
      },
      series: apexSeries,
      colors,
      stroke: { curve: "smooth", width: widths, dashArray: dashes },
      fill: {
        type: fillTypes,
        gradient: { shadeIntensity: 1, opacityFrom: 0.28, opacityTo: 0, stops: [0, 90, 100] },
      },
      markers: { size: 0 },
      xaxis: {
        type: "datetime",
        title: {
          text: "Datum",
          offsetY: -4,
          style: { color: "rgba(255,255,255,0.55)", fontSize: "15px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
        },
        labels: {
          style: { colors: "#FFFFFF", fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
          datetimeUTC: false,
          // 27.09.2026, Nutzer-Wunsch: Monat unter die Tageszahl statt
          // daneben. ApexCharts rendert ein zurueckgegebenes Array als
          // mehrzeiliges Label (ein tspan je Eintrag). Grund: einzeilig
          // klebten benachbarte Beschriftungen aneinander ("28 Aug31 Aug").
          formatter: (value, timestamp) => {
            const ts = Number.isFinite(timestamp) ? timestamp : Number(value);
            if (!Number.isFinite(ts)) return value;
            const d = new Date(ts);
            if (this._range === "1t") {
              return d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
            }
            if (this._range === "5t" || this._range === "1m") {
              return [String(d.getDate()).padStart(2, "0"), d.toLocaleDateString("de-DE", { month: "short" })];
            }
            return [d.toLocaleDateString("de-DE", { month: "short" }), String(d.getFullYear())];
          },
        },
        axisTicks: { show: true },
        tooltip: { enabled: false },
      },
      yaxis: {
        ...yRange,
        title: {
          text: yTitle,
          style: { color: "#FFFFFF", fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
        },
        labels: {
          style: { colors: "#FFFFFF", fontSize: "17px", fontFamily: "Roboto, sans-serif" },
          formatter: (v) => (log ? fmtLogTick(inv(v)) : Math.round(v).toLocaleString("de-DE")),
        },
      },
      grid: {
        borderColor: "rgba(255,255,255,0.07)",
        strokeDashArray: 4,
        padding: { left: 15, right: 15 },
      },
      legend: { show: false },
      // shared:false: Kurs und Korridorlinien haben unterschiedliche
      // Zeitstempel (Rohpunkte vs. Tageswerte), ein geteilter Tooltip wuerde
      // Punkte verschiedener Zeitpunkte nebeneinanderstellen. Angezeigt wird
      // der Punkt der Serie unter dem Zeiger, auf der Log-Achse zurueck-
      // gerechnet auf den echten Betrag.
      tooltip: {
        theme: "dark",
        shared: false,
        intersect: false,
        custom: ({ seriesIndex, dataPointIndex, w }) => {
          const s = w.config.series[seriesIndex];
          const pt = s && s.data[dataPointIndex];
          if (!pt) return "";
          const [x, y] = pt;
          const d = new Date(x);
          const dateStr = d.toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
          const color = w.config.colors[seriesIndex];
          return `
            <div style="background:#1a1a2e;min-width:200px;border-radius:6px;overflow:hidden;">
              <div style="background:#000000;color:#FFFFFF;font-family:Roboto,sans-serif;font-weight:700;font-size:15px;padding:8px 14px;">${dateStr}</div>
              <div style="padding:6px 14px;display:flex;align-items:center;gap:8px;">
                <span style="width:12px;height:12px;border-radius:50%;background:${color};flex:0 0 auto;box-shadow:0 0 4px rgba(0,0,0,.9);"></span>
                <span style="color:#FFFFFF;font-family:Roboto,sans-serif;font-size:14px;">${s.name}:</span>
                <span style="color:#FFFFFF;font-family:Roboto,sans-serif;font-size:14px;font-weight:700;margin-left:auto;">${fmtMoney(inv(y), unit)}</span>
              </div>
            </div>`;
        },
      },
      dataLabels: { enabled: false },
    };

    // updateOptions() MERGT in die bestehende Konfiguration: nach einem
    // Wechsel Log -> linear (5 Jahre -> 1 Monat) blieben yaxis.min/max der
    // Log-Achse stehen und der Kurs laege ausserhalb. Bei geaendertem Modus
    // (Achse oder Serienzahl) darum neu aufbauen, sonst wie bisher updaten.
    const mode = (log ? "log" : "lin") + apexSeries.length;
    await this._drawChart(options, mode);
  }

  // 15.10.2026: Zeichnen serialisiert. _render() laeuft bei JEDEM hass-Update;
  // im Lab-Replay (Dutzende Zustandswechsel je Sekunde) ueberholten sich
  // render()/updateOptions() ("t.put is not a function"), der Chart blieb leer.
  // Jetzt: nur ein Zeichenvorgang zugleich, der juengste Wunsch wird danach
  // nachgeholt, unveraenderte Daten werden uebersprungen, ein Fehler verwirft
  // den Chart (naechster Durchlauf baut neu auf).
  async _drawChart(options, mode) {
    const key = mode + JSON.stringify([options.series, options.xaxis, options.annotations]);
    if (this._chartBusy) {
      this._pending = [options, mode];
      return;
    }
    if (this._apexChart && key === this._drawnKey) return;
    this._chartBusy = true;
    try {
      if (this._apexChart && this._apexMode === mode) {
        await this._apexChart.updateOptions(options, true, true);
      } else {
        if (this._apexChart) this._apexChart.destroy();
        this._apexChart = new window.ApexCharts(this._chartEl, options);
        this._apexMode = mode;
        await this._apexChart.render();
      }
      this._drawnKey = key;
    } catch (e) {
      try {
        if (this._apexChart) this._apexChart.destroy();
      } catch (e2) {
        // halb aufgebauter Chart kann beim Aufraeumen ebenfalls werfen
      }
      this._apexChart = null;
      this._apexMode = null;
      this._drawnKey = null;
    } finally {
      this._chartBusy = false;
    }
    if (this._pending) {
      const [o, m] = this._pending;
      this._pending = null;
      await this._drawChart(o, m);
    }
  }

  // ── Power-Law-Seite: Log-Log-Regression, Mathematik 1:1 aus
  // views/ki_powerlaw.yaml portiert (dort seit 01.09.2026 unveraendert
  // korrekt), Achsen-/Legendenschrift an die uebrige App angeglichen. ──────
  _renderPowerlaw() {
    const data = this._powerlawData;
    this._legendEl.innerHTML = "";
    // Diese Seite befuellt die Legende als eine Reihe, nicht als drei
    // Spalten (s. .bgai-legend--cols).
    this._legendEl.classList.remove("bgai-legend--cols");
    if (!data || !Array.isArray(data.prices) || data.prices.length < 2) {
      this._powerlawEl.innerHTML = `<div class="bgai-msg">${
        data ? "Zu wenig Preishistorie geladen." : "Lade Preishistorie …"
      }</div>`;
      return;
    }

    // Anzeige in Euro (Nutzer-Entscheidung 26.09.2026): das Modell ist in USD
    // definiert und wird zum AKTUELLEN Wechselkurs umgerechnet (konstanter
    // Versatz im Log-Raum, Linien bleiben gerade); die Kurslinie zeigt echte
    // Euro-Werte. "% zum fairen Preis" ist damit identisch zur USD-Aussage
    // der Referenz. Historische Wechselkursschwankungen verschieben die
    // vergangenen Linienlagen leicht, im Footer benannt.
    const liveEur = this._livePrice("eur");
    const liveUsd = this._livePrice("usd");
    const fx = liveEur && liveUsd ? liveUsd.price / liveEur.price : data.lastRatio || 1;
    const lfx = Math.log10(fx);
    const regY = (days) => PL_LOG_A + PL_EXP * Math.log10(days) - lfx;
    const supY = (days) => regY(days) + Math.log10(PL_SUPPORT_FACTOR);

    // Kurslinie: echte Euro-Tageswerte ab Okt. 2013, heute aus dem Live-
    // Sensor (s. _livePrice), sofern neuer als die Historie. Davor gibt es
    // keine Euro-Kurse: 2010 bis 2013 zeigt die USD-Reihe, zum selben
    // aktuellen Wechselkurs umgerechnet wie die Modell-Linien (im Footer
    // benannt).
    const eur = data.eurPrices && data.eurPrices.length >= 2 ? data.eurPrices : [];
    const firstEurDay = eur.length ? eur[0][0] : Infinity;
    const prices = data.prices
      .filter(([days]) => days < firstEurDay)
      .map(([days, usd]) => [days, usd / fx])
      .concat(eur);
    const histLastDays = prices[prices.length - 1][0];
    const live = liveEur;
    const liveDays = live ? Math.floor(live.sec / 86400) - GENESIS_DAY : null;
    if (live && liveDays >= histLastDays) {
      if (liveDays === histLastDays) prices[prices.length - 1] = [liveDays, live.price];
      else prices.push([liveDays, live.price]);
    }

    // Sichtfenster: erster Kurstag (Juli 2010) bis Ende 2040, Zeitachse
    // logarithmisch (Tage seit Genesis) wie bei der Referenz, damit die
    // Modell-Linien Geraden sind. Y ueber ganze Dekaden mit k/Mio-Kurzform.
    const dayOf = (yr) => (Date.UTC(yr, 0, 1) - GENESIS_MS) / 86400000;
    const xMinDays = data.prices[0][0];
    const xMaxDays = dayOf(PL_VIEW_TO + 1);
    const lastPrice = prices[prices.length - 1][1];
    const lastDays = prices[prices.length - 1][0];
    const visible = prices.filter(([days]) => days >= xMinDays && days <= xMaxDays);

    // Y-Bereich: ganze Dekaden um Kurs und Linien im Fenster (Linien sind
    // monoton, die Fensterraender genuegen).
    const logs = visible.map((p) => Math.log10(p[1]));
    const yLo = Math.floor(Math.min(...logs, supY(xMinDays)));
    const yHi = Math.ceil(Math.max(...logs, regY(xMaxDays)));

    const W = 640,
      H = 360,
      cL = 62,
      cR = 618,
      cT = 20,
      cB = 300;
    const xLogMin = Math.log10(xMinDays);
    const xLogMax = Math.log10(xMaxDays);
    const xForDays = (days) => cL + ((Math.log10(days) - xLogMin) / (xLogMax - xLogMin)) * (cR - cL);
    const yForLogPrice = (logP) => cB - ((logP - yLo) / (yHi - yLo)) * (cB - cT);
    const yForPrice = (price) => yForLogPrice(Math.log10(price));

    let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;overflow:hidden">`;
    s += `<defs><clipPath id="plClip"><rect x="${cL}" y="${cT}" width="${cR - cL}" height="${cB - cT}"/></clipPath></defs>`;

    for (let e = yLo; e <= yHi; e++) {
      const y = yForLogPrice(e);
      s += `<line x1="${cL}" y1="${y}" x2="${cR}" y2="${y}" stroke="rgba(255,255,255,0.07)" stroke-dasharray="4" stroke-width="0.8"/>`;
      s += `<text x="${cL - 8}" y="${y + 4}" fill="#FFFFFF" font-size="13" font-family="Roboto,sans-serif" text-anchor="end" style="text-shadow:0 0 4px rgba(0,0,0,.9)">${fmtPlAxis(Math.pow(10, e))}</text>`;
    }
    s += `<text transform="translate(16,${(cT + cB) / 2}) rotate(-90)" fill="rgba(255,255,255,0.55)" font-size="12" font-family="Roboto,sans-serif" text-anchor="middle">Preis (EUR, log)</text>`;

    // X-Achse: Gitter je Jahr. Auf der Log-Zeitachse ruecken spaetere Jahre
    // immer enger zusammen; beschriftet wird deshalb jedes, jedes 2. oder
    // jedes 4. Jahr, sobald ein Jahr schmaler als MIN_GAP ist (ergibt 2011,
    // 12 ... 16, 18 ... 24, 28 ... 40). Erstes Label ausgeschrieben, danach
    // zweistellig ohne Apostroph (Nutzer-Vorgabe "24, 28, 32 ...").
    const MIN_GAP = 22;
    let lastLabelX = -Infinity;
    for (let yr = new Date(GENESIS_MS + xMinDays * 86400000).getUTCFullYear() + 1; yr <= PL_VIEW_TO; yr++) {
      const x = xForDays(dayOf(yr));
      s += `<line x1="${x}" y1="${cT}" x2="${x}" y2="${cB}" stroke="rgba(255,255,255,0.05)" stroke-width="0.8"/>`;
      const pxPerYear = xForDays(dayOf(yr + 1)) - x;
      const step = [1, 2, 4].find((st) => st * pxPerYear >= MIN_GAP) || 4;
      if (yr % step === 0 && x - lastLabelX >= MIN_GAP) {
        const label = lastLabelX === -Infinity ? String(yr) : String(yr % 100).padStart(2, "0");
        s += `<text x="${x}" y="${cB + 17}" fill="#FFFFFF" font-size="13" font-family="Roboto,sans-serif" text-anchor="middle" style="text-shadow:0 0 4px rgba(0,0,0,.9)">${label}</text>`;
        lastLabelX = x;
      }
    }
    s += `<text x="${cL + (cR - cL) / 2}" y="${cB + 32}" fill="rgba(255,255,255,0.55)" font-size="12" font-family="Roboto,sans-serif" text-anchor="middle">Jahr</text>`;

    const curve = (fn, color, dash) => {
      const pts = [];
      for (let i = 0; i <= 96; i++) {
        const days = xMinDays + ((xMaxDays - xMinDays) * i) / 96;
        pts.push(`${xForDays(days).toFixed(1)},${yForLogPrice(fn(days)).toFixed(1)}`);
      }
      return `<polyline points="${pts.join(" ")}" fill="none" style="stroke:${color}" stroke-width="1.8" ${
        dash ? `stroke-dasharray="${dash}"` : ""
      } opacity="0.9" clip-path="url(#plClip)"/>`;
    };
    s += curve(regY, COLOR_REG, "");
    s += curve(supY, COLOR_SUP, "5 3");

    const pts = visible.map(([days, price]) => `${xForDays(days).toFixed(1)},${yForPrice(price).toFixed(1)}`).join(" ");
    s += `<polyline points="${pts}" fill="none" stroke="${COLOR_PRICE}" stroke-width="1.8" stroke-linejoin="round" clip-path="url(#plClip)"/>`;

    const curX = xForDays(lastDays),
      curY = yForPrice(lastPrice);
    s += `<circle cx="${curX}" cy="${curY}" r="4" fill="white" stroke="${COLOR_PRICE}" stroke-width="2"/>`;

    s += `<line x1="${cL}" y1="${cT}" x2="${cL}" y2="${cB}" stroke="rgba(255,255,255,0.25)" stroke-width="1"/>`;
    s += `<line x1="${cL}" y1="${cB}" x2="${cR}" y2="${cB}" stroke="rgba(255,255,255,0.25)" stroke-width="1"/>`;
    s += "</svg>";
    this._powerlawEl.innerHTML = s;

    // Header wie bei den Preisseiten: aktueller Kurs + Einordnung statt Delta.
    const fairValue = Math.pow(10, regY(lastDays));
    const pctDiff = (lastPrice / fairValue - 1) * 100;
    const diffStr = (pctDiff >= 0 ? "+" : "") + pctDiff.toLocaleString("de-DE", { maximumFractionDigits: 0 }) + " % zum fairen Preis";
    // Preis exakt mittig (Nutzer-Vorgabe 26.09.2026), Einordnung darunter
    // statt daneben: nebeneinander stand die Gruppe mittig, der Preis nicht.
    this._headerEl.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;gap:2px;">
        <span class="bgai-price">${fmtMoney(lastPrice, "€")}</span>
        <span class="bgai-delta" style="color:var(--secondary-text-color)">${diffStr}</span>
      </div>
    `;

    // Dynamische Legende: vier Serien dieser Seite statt der einen "Kurs"-
    // Zeile der EUR/USD-Seiten — derselbe .bgai-legend-Container, nur anders
    // befuellt (Nutzer-Vorgabe: "Legende soll sich dynamisch anpassen").
    const legendLine = (color, label) => {
      const item = document.createElement("span");
      item.className = "bgai-legend-item";
      const line = document.createElement("span");
      line.className = "bgai-legend-line";
      line.style.background = color;
      const text = document.createElement("span");
      text.style.color = color;
      text.textContent = label;
      item.appendChild(line);
      item.appendChild(text);
      this._legendEl.appendChild(item);
    };
    legendLine(COLOR_PRICE, `Kurs: ${fmtMoney(lastPrice, "€")}`);
    legendLine(COLOR_REG, `Fairer Preis: ${fmtMoney(fairValue, "€")}`);
    legendLine(COLOR_SUP, `Boden (−60 %): ${fmtMoney(fairValue * PL_SUPPORT_FACTOR, "€")}`);

    // Datenbasis statt "Backfill": wie viele Tageswerte den Fit tragen, bis
    // wann die Historie reicht und ob der Kurs live ist.
    const histLastSec = (histLastDays + GENESIS_DAY) * 86400;
    const liveTxt = live && liveDays >= histLastDays ? " · Kurs live" : "";
    const footer = document.createElement("span");
    footer.className = "bgai-legend-item";
    footer.style.color = "var(--secondary-text-color)";
    footer.style.opacity = "0.7";
    footer.style.fontSize = "13px";
    // Offenlegen, dass das Modell in USD gefittet und nur umgerechnet ist
    // (s. Kommentar am Anfang dieser Methode).
    const fxTxt = fx.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    footer.textContent = `Modell wie bitcoinpower.law: 10^−16,493 · Tage^5,688 (USD), Linien zu 1 € = ${fxTxt} $ umgerechnet (vor Okt. 2013 auch der Kurs) · Kurs bis ${fmtDay(histLastSec)}${liveTxt} · heuristisches Modell, keine Prognose`;
    this._legendEl.appendChild(footer);
  }

  disconnectedCallback() {
    if (this._apexChart) {
      this._apexChart.destroy();
      this._apexChart = null;
    }
  }
}

customElements.define("bitgrid-btc-kurs-chart", BitgridBtcKursChart);
