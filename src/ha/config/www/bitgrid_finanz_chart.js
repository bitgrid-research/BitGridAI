// BitGridAI — Finanz-Bilanz als ApexCharts-Balkendiagramm, ersetzt das
// bisherige rohe SVG in custom:button-card (views/finanz_bilanz.yaml).
//
// Grund (12.09.2026, Nutzer-Wunsch "lass uns daraus einfach ein Apexchart
// bauen"): die SVG-Variante skalierte ihre Hoehe ausschliesslich ueber das
// viewBox-Seitenverhaeltnis (kein fester Pixel-Wert), dadurch scheiterten an
// diesem Tag mehrere Versuche, die Kartenhoehe per CSS-Grid-Stretch an Miner
// anzugleichen — button-cards eingebautes #container{display:grid;height:
// 100%;align-items:center} (Quellcode-verifiziert) hebelte jeden Stretch-
// Versuch aus, der Chart landete "oben links" statt zentriert (mehrfach
// dokumentiert und zurueckgebaut, s. Git-Historie von views/
// finanz_bilanz.yaml). ApexCharts hat wie beim Verlauf-Chart (bitgrid_
// verlauf_chart.js) einen echten chart.height in Pixeln, unabhaengig von
// der Kartenbreite — dasselbe, bereits bewaehrte Muster statt eines neuen
// Loesungsversuchs.
//
// Werte sind reine Tages-Livewerte (keine Zeitreihe), deshalb kein
// hass.callApi(History) wie beim Verlauf-Chart noetig, nur direktes Lesen
// aus hass.states bei jedem hass-Update.
//
// Read-only Darstellung von HA-Sensoren (packages/economics.yaml), kein
// Einfluss auf eine Steuerentscheidung — bleibt aus dem deterministischen
// Kern raus, wie jedes andere reine Anzeige-Modul in www/.

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

// Datenrollen-Farben 1:1 aus der bisherigen SVG-Variante (Fallback-Hexwerte
// von themes/bitgrid.yaml: --bgai-home-v3/-mining-v3/-grid-v3/-total-v3),
// hier als Literalwerte statt var(): ApexCharts schreibt Farben intern
// selbst auf die SVG-Elemente, CSS-Custom-Properties loesen dort anders als
// in einem selbst geschriebenen <style>-Block nicht zuverlaessig auf.
// sign: Vorzeichen der Rohdaten fuers Balkendiagramm (Netzbezugskosten
// kommen als positiver Kosten-Betrag aus dem Sensor, muessen fuer die
// "unter der Nulllinie"-Darstellung negiert werden).
const BAR_DEFS = [
  { entity: "sensor.pv_self_use_savings_eur", label: ["Ersparnis", "(PV-Eigenverbrauch)"], color: "#b3d804", sign: 1 },
  { entity: "sensor.mining_revenue_today_eur", label: ["Mining-Ertrag"], color: "#F7931A", sign: 1 },
  { entity: "sensor.grid_import_cost_eur", label: ["Netzbezugskosten"], color: "#1aaccb", sign: -1 },
  { entity: "sensor.total_profit_today_eur", label: ["Gesamtprofit", "heute"], color: "#CBF1FD", sign: 1 },
];

// 2 Nachkommastellen (uebernommen aus der bisherigen SVG-Variante,
// 24.08.2026-Begruendung dort: Cent-Betraege runden bei 1 Nachkommastelle
// unsauber auf "0,0").
function eurFmt(v) {
  return v.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

class BitgridFinanzChart extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    if (!this.shadowRoot) this._buildDom();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  _buildDom() {
    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        /* 12.09.2026, Nutzer-Wunsch "Abbildung mittig in die Karte": height:
           100% + flex/justify-content:center zentriert #chart vertikal,
           FALLS die Karte (z.B. durch align-items:stretch im Home-Tab-Grid,
           gepaart mit der Miner-Box) mehr Hoehe bekommt als der Chart
           selbst braucht — bislang stand alles oben ohne Ausgleich nach
           unten. */
        :host { display: block; height: 100%; }
        .bgai-card {
          box-sizing: border-box;
          padding: 12px;
          height: 100%;
          display: flex;
          flex-direction: column;
          justify-content: center;
          background: var(--ha-card-background);
          /* 12.09.2026: direkt der Literalwert statt var(--ha-card-border-
             radius), gleicher Fix wie bei bitgrid_verlauf_chart.js — dort
             blieb die Variable trotz Fallback ueber drei Deploys eckig,
             Root Cause nie gefunden, harter Wert (Theme-Literal 20px)
             loeste es zuverlaessig. */
          border-radius: 20px !important;
          border: var(--bgai-card-border-width-v3) solid var(--bgai-card-border-v3);
          box-shadow: var(--bgai-card-shadow-v3);
          overflow: hidden !important;
        }
        #chart { width: 100%; }
        .apexcharts-text, .apexcharts-datalabel, .apexcharts-datalabel-label, .apexcharts-datalabel-value {
          text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9) !important;
        }
      </style>
      <div class="bgai-card">
        <div id="chart"></div>
      </div>
    `;
    this._chartEl = root.getElementById("chart");
    // 13.09.2026, Nutzer-Befund "Chart nicht mittig, Y-Achse wirkt
    // abgeschnitten" — erster Fix (leeres updateOptions() im Resize-
    // Callback) hat NICHT gereicht: ApexCharts cached seine Breite intern
    // (w.globals.svgWidth) und ein aufrufloser updateOptions()-Call
    // rechnet diesen Cache nachweislich nicht neu, auch wenn sich der
    // Container laengst geaendert hat. Jetzt hart: die tatsaechliche
    // contentRect-Breite des ResizeObservers wird direkt als NUMERISCHER
    // chart.width-Pixelwert an updateOptions uebergeben (statt uns auf
    // Apex' eigene "100%"-Erkennung zu verlassen) — sowohl beim ersten
    // Aufbau (this._chartWidth wird VOR dem ersten ApexCharts(...)-Aufruf
    // in _render() gebraucht) als auch bei jeder spaeteren echten
    // Breitenaenderung (CSS-Grid-Stretch nach dem ersten Render).
    this._chartWidth = null;
    const resizeObserver = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect?.width;
      if (!width) return;
      this._chartWidth = width;
      this._apexChart?.updateOptions({ chart: { width } }, false, false);
    });
    resizeObserver.observe(root.querySelector(".bgai-card"));
  }

  // Keine History-Abfrage noetig (reine Livewerte), daher kein 5-Minuten-
  // Cache wie beim Verlauf-Chart. Neu gezeichnet wird aber nur bei einer
  // sichtbaren Wertaenderung und ohne Animation (s. _lastKey, 13.10.2026).
  async _render() {
    if (!this._hass) return;
    try {
      await loadApexCharts();
    } catch (e) {
      this._chartEl.textContent = "ApexCharts konnte nicht geladen werden.";
      return;
    }
    const hass = this._hass;
    const num = (id) => {
      const v = parseFloat(hass.states[id]?.state);
      return Number.isNaN(v) ? 0 : v;
    };
    const values = BAR_DEFS.map((b) => num(b.entity) * b.sign);
    // 13.10.2026, Nutzer-Befund "Finanzen springt/laedt staendig neu": set
    // hass feuert bei JEDER Zustandsaenderung in ganz HA (im Lab-Replay ein
    // Dutzend Werte alle 10 s), und der alte Update-Pfad updateOptions(...,
    // true, true) zeichnete die Balken jedes Mal neu UND animierte sie von
    // null hoch. Jetzt: nur bei einer auf Cent sichtbaren Wertaenderung neu
    // zeichnen, und dann ohne Animation (s. updateSeries unten). Die
    // Breitenanpassung erledigt weiterhin der ResizeObserver.
    const key = values.map((v) => v.toFixed(2)).join("|");
    if (this._apexChart && key === this._lastKey) return;
    this._lastKey = key;
    const colors = BAR_DEFS.map((b) => b.color);
    const categories = BAR_DEFS.map((b) => b.label);

    const options = {
      chart: {
        type: "bar",
        // 281px (12.09.2026, +1px Nutzer-Wunsch nach viermal +5px):
        // urspruenglich 260px, gleiche Zeichenflaechen-Hoehe wie zuletzt
        // beim SVG (H=260), jetzt aber ein ECHTER Pixel-Wert unabhaengig
        // von der Kartenbreite statt viewBox-Skalierung (s. Kopfkommentar).
        height: 281,
        // 13.09.2026: expliziter Pixelwert aus dem ResizeObserver statt
        // Apex' eigener "100%"-Berechnung (s. Kommentar bei _buildDom) —
        // Fallback "100%" nur fuer den sehr ersten Tick, bevor der
        // ResizeObserver ueberhaupt einmal gefeuert hat.
        width: this._chartWidth || "100%",
        toolbar: { show: false },
        background: "transparent",
        foreColor: "#FFFFFF",
        dropShadow: { enabled: true, top: 0, left: 0, blur: 3, opacity: 0.5 },
        // 13.09.2026, Nutzer-Wunsch "Inhalt der Karte mittig zentrieren":
        // der Flex-Wrapper (.bgai-card, s. _buildDom) zentriert den Chart
        // bereits korrekt, aber ApexCharts reserviert per Default 15px
        // eigenen Leerraum oben (parentHeightOffset) unabhaengig davon -
        // bei den kleinen, hier ueblichen Balkenhoehen faellt das als
        // sichtbar mehr Luft oben als unten auf. Bekannte ApexCharts-
        // Eigenheit, auf 0 gesetzt.
        parentHeightOffset: 0,
      },
      series: [{ name: "Profit", data: values }],
      colors,
      plotOptions: {
        bar: {
          // distributed: jeder Balken bekommt seine eigene Farbe aus dem
          // colors-Array statt einer einzigen Serienfarbe — noetig, weil
          // alle 4 Werte technisch EINE Serie sind (kein Mehrfach-Serien-
          // Balkendiagramm wie beim Verlauf-Chart).
          distributed: true,
          columnWidth: "50%",
          borderRadius: 4,
          dataLabels: { position: "top" },
        },
      },
      legend: { show: false },
      dataLabels: {
        enabled: true,
        formatter: (val) => `${eurFmt(val)} €`,
        style: { fontSize: "16px", fontFamily: "Roboto, sans-serif", fontWeight: 700, colors },
        offsetY: -4,
      },
      xaxis: {
        categories,
        labels: {
          // 13.09.2026, Nutzer-Wunsch: Bezeichner in der Balkenfarbe statt
          // einheitlich Weiss — ApexCharts nimmt bei labels.style.colors ein
          // ARRAY entgegen (ein Hex-Wert pro Kategorie, gleiche Reihenfolge
          // wie categories/colors oben), kein einzelner String mehr.
          style: { colors, fontSize: "14px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
        },
        axisTicks: { show: true },
      },
      yaxis: {
        title: {
          text: "Profit in €",
          style: { color: "#FFFFFF", fontSize: "15px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
        },
        labels: {
          style: { colors: "#FFFFFF", fontSize: "15px", fontFamily: "Roboto, sans-serif" },
          // 12.09.2026, Nutzer-Wunsch: Achsen-Gridlines ohne Nachkommastellen
          // (Balken-Werte/Tooltip behalten weiterhin 2 Nachkommastellen ueber
          // eurFmt, das sind echte Euro-Betraege, hier nur die grobe Skala).
          formatter: (val) => Math.round(val).toLocaleString("de-DE"),
        },
      },
      grid: {
        borderColor: "rgba(255,255,255,0.07)",
        strokeDashArray: 4,
      },
      // 26.09.2026, Nutzer-Wunsch "Grenze zwischen Gewinn und Verlust
      // sichtbarer machen": eine durchgezogene Linie bei y=0, deutlich
      // kraeftiger als die gestrichelten 0.07-Gridlines darueber/darunter,
      // sonst geht die Nulllinie in den Nachbarlinien unter. Farbwert 1:1
      // --divider-color (themes/bitgrid.yaml) als Literal, keine neue
      // Farbe: ApexCharts loest CSS-Custom-Properties in seinen eigenen
      // Options nicht zuverlaessig auf (s. Kommentar bei BAR_DEFS oben),
      // daher derselbe Farbton hartkodiert statt var().
      annotations: {
        yaxis: [
          {
            y: 0,
            borderColor: "rgba(255,255,255,0.20)",
            borderWidth: 1,
            strokeDashArray: 0,
          },
        ],
      },
      tooltip: {
        theme: "dark",
        y: { formatter: (val) => `${eurFmt(val)} €` },
      },
    };

    if (this._apexChart) {
      // 15.10.2026: erst das noch laufende erste render() abwarten. Ein
      // updateSeries() auf den halb aufgebauten Chart ("t.put is not a
      // function", im Lab-Replay mit Werten im 6,7-s-Takt reproduziert) liess
      // ihn bis zum Neuladen leer.
      const chart = this._apexChart;
      try {
        await this._renderPromise;
        // Nur die Werte tauschen, ohne Animation: kein Neuaufbau von null.
        await chart.updateSeries([{ name: "Profit", data: values }], false);
      } catch (e) {
        this._resetChart(chart);
      }
    } else {
      // Synchron zuweisen, damit parallel laufende _render()-Aufrufe (await
      // oben) den Chart schon sehen und keinen zweiten anlegen.
      const chart = new window.ApexCharts(this._chartEl, options);
      this._apexChart = chart;
      this._renderPromise = chart.render().catch(() => this._resetChart(chart));
    }
  }

  // Fehlgeschlagenen Chart verwerfen; der naechste Wertewechsel baut neu auf.
  _resetChart(chart) {
    if (this._apexChart !== chart) return;
    try {
      chart.destroy();
    } catch (e) {
      // ein halb aufgebauter Chart kann auch beim Aufraeumen werfen
    }
    this._apexChart = null;
    this._renderPromise = null;
    this._lastKey = null;
  }

  disconnectedCallback() {
    if (this._apexChart) {
      this._apexChart.destroy();
      this._apexChart = null;
    }
  }
}

customElements.define("bitgrid-finanz-chart", BitgridFinanzChart);
