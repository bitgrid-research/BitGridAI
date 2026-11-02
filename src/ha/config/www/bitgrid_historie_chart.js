// BitGridAI — eigenstaendiges Custom-Element fuer den Raum-/Gesamtenergie-
// Verlauf im Abschnitt "Historie" (Tab "EnergieInfo"). Ersetzt dort
// custom:apexcharts-card (bisher in historie_untergeschoss.yaml und den
// uebrigen historie_*.yaml).
//
// 25.09.2026, Nutzer-Vorgabe: "baue den Graph von Historie genauso wie in
// Tab Home von der Achsenbeschriftung und Stil" — Uebernahme des Stils, der
// sich seit 12.09.2026 durch www/bitgrid_verlauf_chart.js,
// bitgrid_regelschwellen_chart.js, bitgrid_btc_kurs_chart.js und
// bitgrid_bar_trend_chart.js zieht: beschriftete, farbige 17px-Achsen,
// dickere Linien mit chart-weitem dropShadow, eigene HTML-Legende (Icon +
// Live-Wert) statt ApexCharts' foreignObject-Legende, gestricheltes Gitter,
// eigener dunkler Tooltip.
//
// Warum ein NEUES Element statt Wiederverwendung von bitgrid-verlauf-chart
// oder bitgrid-regelschwellen-chart: beide sind hart auf "heute, 00-24 Uhr"
// zugeschnitten (SERIES_DEFS/X_START_HOUR fest codiert). Die Historie-Karte
// braucht dagegen vier ROLLIERENDE Fenster (letzte 24h/7d/30d/12 Monate, ab
// jetzt zurueckgerechnet, nicht Kalendertag-ausgerichtet) mit wechselnder
// Bucket-Aufloesung — eine andere Datenform, die eine eigene Achsen-
// Beschriftungslogik braucht (s. bucketLabel/tickVisible unten). Naeher am
// Vorbild bitgrid-bar-trend-chart (ein Element, per config.mode/-span fuer
// mehrere Einsatzorte parametrisiert) als an den beiden Einzelzweck-Karten.
//
// Ein Element pro (Raum, Zeitraum)-Kombination: die aufrufenden historie_*.
// yaml-Dateien behalten ihre bestehende Struktur (4 bedingte Karten je
// input_select.historie_zeitraum-Wert, s. dortiger Kopfkommentar) —
// geaendert wird nur der Karten-TYP innerhalb jeder Bedingung, nicht die
// Raum-/Zeitraum-Auswahl selbst (die laeuft weiter ueber input_select +
// type: conditional, HAs conditional-Karte mountet/unmountet ihr Kind
// tatsaechlich bei jedem Wechsel neu — dieses Element muss config-Aenderungen
// zur Laufzeit deshalb nicht selbst behandeln).
//
// Datenquelle: recorder/statistics_during_period (type: mean), derselbe
// WS-Befehl, den apexcharts-card intern schon fuer genau diese Karte nutzte
// (Performance-Begruendung: historie_untergeschoss.yaml, 25.08.2026 —
// statistics statt roher History, sonst zehntausende Rohdatenpunkte bei
// 30 Tage/12 Monate). start/end kommen laut HA-Standard als ms-Epoch;
// toDate() haelt zur Sicherheit eine Sekunden-Fallback-Heuristik vor, falls
// ein HA-Release das je anders liefert — auf dem Wandtablet nicht gegen die
// echte API getestet, dieses Sicherheitsnetz ist unverifiziert, aber billig.
//
// Read-only, keine Steuerentscheidung — reines Anzeige-Modul in www/.

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

const COLOR_DEFAULT = "#4FC3F7"; // bisherige Serienfarbe aus apexcharts-card
// 26.09.2026, Nutzer-Wunsch: Y-Achse (Titel + Werte) in der Netzbezug-Farbe des
// Home-Charts (bitgrid_verlauf_chart.js, Serie Netzbezug #1aaccb) statt in der
// Serienfarbe. Per Karten-Config `axis_color` ueberschreibbar.
const COLOR_YAXIS = "#1aaccb";
const COLOR_AVG = "#26C6DA"; // Standard-Rolle, hier fuer die Ø-Linie (gleiche Rollenbedeutung wie in bitgrid_bar_trend_chart.js)

const SPAN_HOURS = { "24h": 24, "7d": 24 * 7, "30d": 24 * 30, "365d": 24 * 365 };
const WOCHENTAGE_KURZ = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
const MONATE_KURZ = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];

function pad2(n) {
  return String(n).padStart(2, "0");
}

// ms-Epoch -> Date, mit Sekunden-Fallback (s. Kopfkommentar).
function toDate(raw) {
  let ms = typeof raw === "number" ? raw : Date.parse(raw);
  if (ms < 946684800000) ms *= 1000; // < Jahr 2000 in ms => vermutlich Sekunden
  return new Date(ms);
}

// Anzeigetext eines sichtbaren Ticks, abhaengig vom Zeitraum-Modus.
function bucketLabel(span, d) {
  if (span === "24h") {
    return d.getHours() === 0 ? `${d.getDate()}. ${MONATE_KURZ[d.getMonth()]}` : String(d.getHours());
  }
  if (span === "7d") {
    return `${WOCHENTAGE_KURZ[d.getDay()]} ${pad2(d.getDate())}.${pad2(d.getMonth() + 1)}`;
  }
  if (span === "30d") {
    return `${pad2(d.getDate())}.${pad2(d.getMonth() + 1)}`;
  }
  return MONATE_KURZ[d.getMonth()]; // 365d
}

// Ob ein Bucket ueberhaupt ein Tick-LABEL bekommt (der Tick-Strich selbst
// bleibt fuer jeden Bucket stehen) — sonst waeren bei 168 Stunden-Buckets
// (7 Tage) oder 52 Wochen-Buckets (12 Monate) alle Beschriftungen
// uebereinander. Grenzen bewusst an echten Kalendereinheiten (Tageswechsel/
// Montag/Monatserste-Woche), nicht an einem festen Bucket-Index-Modulo,
// damit die Beschriftung bei Fenstern, die nicht auf 0 Uhr ausgerichtet
// sind (rollierend, nicht Kalendertag), trotzdem an sinnvollen Stellen
// sitzt.
function tickVisible(span, d) {
  if (span === "24h") return d.getHours() % 3 === 0;
  if (span === "7d") return d.getHours() === 0;
  if (span === "30d") return d.getDay() === 1; // jeder Montag
  return d.getDate() <= 7; // 365d: einmal pro Monat
}

function xAxisTitle(span) {
  if (span === "24h") return "Uhrzeit";
  if (span === "365d") return "Monat";
  return "Datum";
}

const SHARED_STYLE = `
  :host { display: block; }
  .bgai-card {
    box-sizing: border-box;
    /* 26.09.2026: unten 14px statt 2px, Luft zwischen Legende und dem
       Zeitraum-Umschalter darunter (Nutzer-Wunsch Lesbarkeit). */
    padding: 6px 6px 14px 6px;
    background: transparent;
  }
  .bgai-card.standalone {
    padding: 12px;
    background: var(--ha-card-background);
    border-radius: var(--bgai-card-radius-v3);
    border: var(--bgai-card-border-width-v3) solid var(--bgai-card-border-v3);
    box-shadow: var(--bgai-card-shadow-v3);
    overflow: hidden;
  }
  #chart { width: 100%; }
  .bgai-msg { padding: 40px 0; text-align: center; color: var(--secondary-text-color); font-size: var(--bg-fs-body); }
  .bgai-legend {
    display: flex; flex-wrap: wrap; justify-content: center; align-items: center;
    column-gap: 16px; row-gap: 4px; padding-top: 12px; margin-top: 4px;
    background-image: linear-gradient(to right, transparent, var(--divider-color) 15%, var(--divider-color) 85%, transparent);
    background-repeat: no-repeat; background-size: 100% 2px; background-position: top;
  }
  .bgai-legend-item { display: flex; align-items: center; gap: 6px; font-size: 16px; font-family: Roboto, sans-serif; font-weight: 400; text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9); }
  .bgai-legend-dot { --mdc-icon-size: 20px; width: 20px; height: 20px; flex: 0 0 auto; filter: drop-shadow(0 0 3px rgba(0,0,0,.9)) drop-shadow(0 0 3px rgba(0,0,0,.9)); }
  .apexcharts-text, .apexcharts-xaxis-annotation-label, .apexcharts-yaxis-annotation-label { text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9) !important; }
`;

class BitgridHistorieChart extends HTMLElement {
  setConfig(config) {
    if (!config || !config.entity) throw new Error("bitgrid-historie-chart: 'entity' fehlt in der Config");
    this._config = config;
    this._span = SPAN_HOURS[config.span] ? config.span : "24h";
    if (!this.shadowRoot) this._buildDom();
  }

  set hass(hass) {
    this._hass = hass;
    this._maybeRefresh();
  }

  getCardSize() {
    return 5;
  }

  _buildDom() {
    const root = this.attachShadow({ mode: "open" });
    const standalone = this._config.standalone === true;
    root.innerHTML = `
      <style>${SHARED_STYLE}</style>
      <div class="bgai-card${standalone ? " standalone" : ""}">
        <div id="chart"></div>
        <div id="legend" class="bgai-legend"></div>
      </div>
    `;
    this._chartEl = root.getElementById("chart");
    this._legendEl = root.getElementById("legend");
  }

  async _maybeRefresh() {
    if (!this._hass) return;
    // 17.10.2026, Lab-Replay: je Sim-Block neu zeichnen (Daten aus dem Profil,
    // window.bgaiSimToday/bgaiSimSeries in www/bitgrid_card_shape.js; Prod: null).
    const simT = window.bgaiSimToday && window.bgaiSimToday(this._hass);
    if (simT) {
      const key = String(simT.step);
      if (this._apexChart && key === this._lastSimKey) {
        this._updateLegendLiveValue();
        return;
      }
      this._lastSimKey = key;
      await this._fetchAndRender();
      return;
    }
    if (this._lastSimKey) {
      this._lastSimKey = null;
      this._lastFetch = 0;
    }
    const now = Date.now();
    // 26.09.2026, gleicher Bug wie bitgrid_verlauf_chart.js: disconnectedCallback()
    // zerstoert this._apexChart beim View-Wechsel, _updateLegendLiveValue()
    // allein baut die Chart nicht wieder auf. Deshalb zusaetzlich pruefen,
    // ob ueberhaupt noch eine Chart-Instanz existiert, bevor auf den Cache
    // vertraut wird.
    // 5-Minuten-Cache, identisch zum bisherigen update_interval: 5min der
    // abgeloesten apexcharts-card-Config — ein Statistics-Abruf ist teurer
    // als ein simples State-Update.
    if (this._apexChart && this._lastFetch && now - this._lastFetch < 5 * 60 * 1000) {
      this._updateLegendLiveValue();
      return;
    }
    this._lastFetch = now;
    await this._fetchAndRender();
  }

  // Der Live-Wert in der Legende soll nicht auf den 5-Minuten-Cache warten
  // (dieselbe Erwartung wie bei bitgrid_verlauf_chart.js: die Legende zeigt
  // "jetzt", der Graph selbst darf traeger sein).
  _updateLegendLiveValue() {
    if (!this._legendLiveEl || !this._hass) return;
    const state = this._hass.states[this._config.entity];
    this._legendLiveEl.textContent = this._liveValueText(state);
  }

  _liveValueText(state) {
    if (!state || state.state === "unavailable" || state.state === "unknown") return "–";
    const raw = parseFloat(state.state);
    if (Number.isNaN(raw)) return "–";
    // 27.09.2026: folgt der Einheit, die _fetchAndRender fuer diesen Zeitraum
    // gewaehlt hat (this._unitW), sonst staende in der Legende kW und auf der
    // Achse W.
    if (this._unitW) return `${Math.round(raw).toLocaleString("de-DE")} W`;
    const d = raw < 10000 ? 2 : 1;
    return `${(raw / 1000).toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d })} kW`;
  }

  async _fetchAndRender() {
    try {
      await loadApexCharts();
    } catch (e) {
      this._chartEl.textContent = "ApexCharts konnte nicht geladen werden.";
      return;
    }
    const hass = this._hass;
    const config = this._config;
    const span = this._span;
    const hours = SPAN_HOURS[span];
    const period = config.period || (span === "30d" ? "day" : span === "365d" ? "week" : "hour");

    const end = new Date();
    const start = new Date(end.getTime() - hours * 3600000);

    let buckets = [];
    // Lab-Replay: es gibt nur den abgespielten Tag (Raumsumme je 10-min-Block
    // aus dem Profil), als Stundenmittel bis zum aktuellen Sim-Block.
    const simSeries = window.bgaiSimToday && window.bgaiSimToday(hass) && window.bgaiSimSeries
      ? window.bgaiSimSeries(hass, config.entity, new Date())
      : null;
    if (simSeries && period !== "hour") {
      this._legendEl.innerHTML = "";
      // Ohne "Replay" im Text (17.10.2026): die Meldung erscheint auf dem
      // Probanden-Tablet, sobald jemand den Zeitraum weiterblaettert.
      this._chartEl.innerHTML = `<div class="bgai-msg">Für diesen Zeitraum liegen keine Werte vor, bitte „Letzte 24 Stunden“ wählen.</div>`;
      if (this._apexChart) {
        this._apexChart.destroy();
        this._apexChart = null;
      }
      return;
    }
    if (simSeries) {
      const byHour = new Map();
      for (const [ts, v] of simSeries) {
        const d = new Date(ts);
        d.setMinutes(0, 0, 0);
        const list = byHour.get(d.getTime()) || [];
        list.push(v);
        byHour.set(d.getTime(), list);
      }
      buckets = [...byHour.entries()]
        .sort((a, b) => a[0] - b[0])
        .map(([k, vs]) => ({ date: new Date(k), value: vs.reduce((a, v) => a + v, 0) / vs.length }));
    } else try {
      const wsFn = hass && hass.callWS ? hass.callWS.bind(hass) : null;
      const result = wsFn
        ? await wsFn({
            type: "recorder/statistics_during_period",
            start_time: start.toISOString(),
            end_time: end.toISOString(),
            statistic_ids: [config.entity],
            period,
            types: ["mean"],
          })
        : null;
      const rows = result ? result[config.entity] || [] : [];
      buckets = rows
        .filter((r) => typeof r.mean === "number")
        .map((r) => ({ date: toDate(r.start), value: r.mean }));
    } catch (e) {
      this._chartEl.innerHTML = `<div class="bgai-msg">Historie konnte nicht geladen werden.</div>`;
      return;
    }

    if (buckets.length < 2) {
      this._legendEl.innerHTML = "";
      this._chartEl.innerHTML = `<div class="bgai-msg">Noch keine Daten fuer diesen Zeitraum.</div>`;
      return;
    }

    const color = config.color || COLOR_DEFAULT;
    const axisColor = config.axis_color || COLOR_YAXIS;
    const categories = buckets.map((b) => b.date.toISOString());
    // 27.09.2026, Nutzer-Befund am Kuechen-Verlauf ("fehlt hier was?"): die
    // Achse stand fest auf kW mit einer Nachkommastelle. Ein Raum mit ~0,05 kW
    // bekam dadurch nur die Beschriftungen 0.0 und 0.1, alle uebrigen
    // Gitterlinien rundeten auf denselben Wert und blieben unbeschriftet — der
    // Graph wirkte leer, obwohl die Daten stimmten. Die Einheit richtet sich
    // jetzt nach dem groessten Wert im Zeitraum: unter 1000 W wird in W
    // gezeichnet (ganzzahlige Ticks), darueber wie bisher in kW. Betrifft
    // Achsentitel, Ticks, Ø-Linie, Tooltip und den Live-Wert in der Legende
    // gemeinsam, damit nirgends zwei Einheiten nebeneinander stehen.
    const maxW = buckets.reduce((m, b) => Math.max(m, b.value || 0), 0);
    const useW = maxW < 1000;
    this._unitW = useW;
    const unitText = useW ? "W" : "kW";
    const values = buckets.map((b) => (useW ? b.value : b.value / 1000));
    const fmtVal = (v) => (useW ? Math.round(v).toLocaleString("de-DE") : v.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    const avgKw = values.reduce((a, v) => a + v, 0) / values.length;

    // ── Legende: Icon + Name + Live-Wert (primaer), Ø fuer den Zeitraum
    // (sekundaer) — gleiches Zwei-Zeilen-Muster wie bitgrid_bar_trend_chart.js
    // ("Tageswert"/"Ziel") und bitgrid_verlauf_chart.js ("jetzt"-Legende).
    this._legendEl.innerHTML = "";
    const primary = document.createElement("span");
    primary.className = "bgai-legend-item";
    const primaryDot = document.createElement("ha-icon");
    primaryDot.className = "bgai-legend-dot";
    primaryDot.setAttribute("icon", config.icon || "mdi:flash");
    primaryDot.style.color = color;
    const primaryLabel = document.createElement("span");
    primaryLabel.style.color = color;
    const nameText = config.name || config.entity;
    const liveSpan = document.createElement("span");
    liveSpan.textContent = this._liveValueText(hass.states[config.entity]);
    primaryLabel.textContent = `${nameText}: `;
    primaryLabel.appendChild(liveSpan);
    this._legendLiveEl = liveSpan;
    primary.appendChild(primaryDot);
    primary.appendChild(primaryLabel);
    this._legendEl.appendChild(primary);

    const avgItem = document.createElement("span");
    avgItem.className = "bgai-legend-item";
    const avgDot = document.createElement("ha-icon");
    avgDot.className = "bgai-legend-dot";
    avgDot.setAttribute("icon", "mdi:chart-line");
    avgDot.style.color = COLOR_AVG;
    const avgLabel = document.createElement("span");
    avgLabel.style.color = COLOR_AVG;
    avgLabel.textContent = `Ø Zeitraum: ${fmtVal(avgKw)} ${unitText}`;
    avgItem.appendChild(avgDot);
    avgItem.appendChild(avgLabel);
    this._legendEl.appendChild(avgItem);

    const options = {
      chart: {
        type: "area",
        height: config.height || 220,
        toolbar: { show: false },
        zoom: { enabled: false },
        background: "transparent",
        foreColor: "#FFFFFF",
        dropShadow: { enabled: true, top: 0, left: 0, blur: 3, opacity: 0.5 },
        animations: { enabled: false },
      },
      series: [{ name: nameText, data: values }],
      colors: [color],
      stroke: { curve: "smooth", width: 2.5, dashArray: 0 },
      fill: { type: "solid", opacity: [0.35] },
      markers: { size: 0 },
      xaxis: {
        type: "category",
        categories,
        tickPlacement: "on",
        title: {
          text: xAxisTitle(span),
          offsetY: -4,
          style: { color: "rgba(255,255,255,0.55)", fontSize: "15px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
        },
        labels: {
          style: { colors: "#FFFFFF", fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
          rotate: 0,
          offsetY: 4,
          formatter: (value) => {
            const d = new Date(value);
            if (Number.isNaN(d.getTime())) return "";
            // Replay (17.10.2026): die Reihe liegt auf dem echten Datum (s.
            // bgaiSimSeries), die Mitternachts-Marke zeigte "17. Okt" neben dem
            // dargestellten 21.07. Im Replay daher nur Stunden.
            if (!tickVisible(span, d)) return "";
            return simSeries && d.getHours() === 0 ? "0" : bucketLabel(span, d);
          },
        },
        axisTicks: { show: true },
        tooltip: { enabled: false },
      },
      yaxis: {
        title: {
          text: `Leistung (${unitText})`,
          style: { color: axisColor, fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
        },
        labels: {
          style: { colors: axisColor, fontSize: "17px", fontFamily: "Roboto, sans-serif" },
          formatter: (v) => (useW ? Math.round(v).toLocaleString("de-DE") : v.toLocaleString("de-DE", { maximumFractionDigits: v < 10 ? 1 : 0 })),
        },
        min: 0,
      },
      grid: {
        borderColor: "rgba(255,255,255,0.07)",
        strokeDashArray: 4,
        padding: { left: 15, right: 15 },
      },
      legend: { show: false },
      annotations: {
        yaxis: [
          {
            y: avgKw,
            borderColor: COLOR_AVG,
            strokeDashArray: 4,
            label: {
              text: `Ø ${fmtVal(avgKw)} ${unitText}`,
              position: "right",
              offsetX: -4,
              borderColor: "transparent",
              style: { color: COLOR_AVG, background: "transparent", fontSize: "13px", fontWeight: 600, fontFamily: "Roboto, sans-serif" },
            },
          },
        ],
      },
      tooltip: {
        theme: "dark",
        custom: ({ dataPointIndex }) => {
          const b = buckets[dataPointIndex];
          if (!b) return "";
          const label =
            span === "24h"
              ? `${pad2(b.date.getHours())}:${pad2(b.date.getMinutes())} Uhr`
              : `${pad2(b.date.getDate())}.${pad2(b.date.getMonth() + 1)}.${b.date.getFullYear()}`;
          const valueText = `${fmtVal(useW ? b.value : b.value / 1000)} ${unitText}`;
          return `
            <div style="background:#1a1a2e;min-width:180px;border-radius:6px;overflow:hidden;">
              <div style="background:#000000;color:#FFFFFF;font-family:Roboto,sans-serif;font-weight:700;font-size:14px;padding:6px 12px;">${label}</div>
              <div style="padding:6px 12px;display:flex;align-items:center;gap:8px;">
                <span style="width:10px;height:10px;border-radius:50%;background:${color};flex:0 0 auto;box-shadow:0 0 4px rgba(0,0,0,.9);"></span>
                <span style="color:#FFFFFF;font-family:Roboto,sans-serif;font-size:13px;font-weight:700;">${valueText}</span>
              </div>
            </div>`;
        },
      },
      dataLabels: { enabled: false },
    };

    // 17.10.2026: die Historie steht viermal im Tab (24 h / 7 / 30 Tage /
    // 12 Monate, je eine conditional-Karte), nur eine ist eingehaengt. Die
    // anderen bekamen trotzdem hass und zeichneten ins Leere: ApexCharts warf
    // "Element not found" (Lab-Befund). Gezeichnet wird nur eingehaengt,
    // connectedCallback holt das beim Einblenden nach. Zeichnen serialisiert
    // wie in bitgrid_bar_trend_chart.js, ein Fehler verwirft den Chart.
    if (!this.isConnected) return;
    if (this._chartBusy) return;
    this._chartBusy = true;
    try {
      if (this._apexChart) {
        await this._apexChart.updateOptions(options, true, true);
      } else {
        this._apexChart = new window.ApexCharts(this._chartEl, options);
        await this._apexChart.render();
      }
    } catch (e) {
      try {
        if (this._apexChart) this._apexChart.destroy();
      } catch (e2) {
        // ein halb aufgebauter Chart kann auch beim Aufraeumen werfen
      }
      this._apexChart = null;
      this._lastFetch = 0;
      this._lastSimKey = null;
    } finally {
      this._chartBusy = false;
    }
  }

  connectedCallback() {
    if (!this._hass) return;
    this._lastFetch = 0;
    this._lastSimKey = null;
    this._maybeRefresh();
  }

  disconnectedCallback() {
    if (this._apexChart) {
      this._apexChart.destroy();
      this._apexChart = null;
    }
  }
}

customElements.define("bitgrid-historie-chart", BitgridHistorieChart);
