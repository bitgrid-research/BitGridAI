// BitGridAI — geteiltes Balken-Trend-Custom-Element fuer die beiden
// Statistik-Karten im Tab "BitcoinInfo": Effizienz (Energy-to-Sats,
// views/energy_to_sats_chart.yaml) und Langzeitbilanz (Sats/Monat,
// views/pool_monthly_chart.yaml). Ersetzt die bisherigen Hand-SVG-Templates
// in stats_energy_to_sats.yaml/stats_pool_monthly.yaml.
//
// Nutzer-Vorgabe 25.09.2026:
//   1. Stil wie die uebrigen Custom-Charts (bitgrid_verlauf_chart.js/
//      bitgrid_btc_kurs_chart.js): ApexCharts statt Inline-SVG, beschriftete
//      X-/Y-Achse in gleicher Schriftgroesse, Legende UNTER dem Chart statt
//      als kleine SVG-Zeile oben.
//   2. Zeitraum-Navigation per Pfeile + Titel mittig, gleiches Muster wie
//      views/historie_zeitraum_cycler.yaml.
//   3. Legendenfarben aus den bereits etablierten Rollen (DESIGN.md): Sats/
//      Mining-Werte in der Bitcoin-Rolle (#F7931A), Vergleichs-/Ø-Linien in
//      der Standard-Rolle (#26C6DA), Ziel-/Positiv-Linien in der Eco-Rolle
//      (#4CAF50) — dieselben drei Farben, die schon in mining_log.yaml
//      (Sats-Spalte) und bitgrid_regelschwellen_chart.js verwendet werden.
//
// EIN Custom-Element statt zwei separaten Dateien: beide Karten sind
// strukturell identisch (Balken + Ø-Linie + optionale Ziel-Linie, mit
// Zeitraum-Paging) — anders als z.B. Verlauf/Regelschwellen/Finanz, die
// fachlich verschiedene Dinge zeigen, ist hier eine Abstraktion die
// wartbarere Wahl als zweimal ~250 Zeilen fast identischer Code.
//
// Datenquelle Effizienz: www/energy_to_sats.json (src/data/
// energy_to_sats_export.py, seit 25.09.2026 mit einem deutlich weiteren
// --days-Fenster als bisher, damit Woche/Monat-Paging ueberhaupt Daten zum
// Blaettern hat). Datenquelle Langzeitbilanz: hass.states direkt
// (sensor.pool_monthly_history/sensor.pool_balance_btc), 1:1 dieselbe Logik
// wie zuvor in stats_pool_monthly.yaml, nur ins Custom-Element verschoben —
// kein neuer Datenpfad.
//
// Kein Steuerpfad: reine Anzeige, beeinflusst keine Mining-Entscheidung in
// core/.
//
// Nutzer-Vorgabe 26.09.2026 (nur Langzeitbilanz):
//   1. Y-Achse (Titel + Sats-Werte) weiss wie die X-Achse statt in der
//      Bitcoin-Rolle. Parameter yWhite statt globaler Aenderung; seit
//      26.09.2026 (zweite Nutzer-Vorgabe) nutzt ihn auch Effizienz, dort
//      zusaetzlich weisse Balken (COLOR_WHITE). Langzeitbilanz behaelt die
//      orangen Balken (Sats = Bitcoin-Rolle).
//   2. Laufender Monat als zweizeiliges Label ["Sep '26", "(laufend)"]:
//      ApexCharts rendert einen Array-x-Wert mehrzeilig. Einzeilig lief das
//      Label in den Nachbarmonat, weil unter 11 Kategorien bewusst nicht
//      rotiert wird.
//   3. Pfeile blaettern zyklisch durch Seiten (Umlauf wie in
//      bitgrid_btc_kurs_chart.js): Monatsansicht (12-Monats-Fenster wie
//      bisher, aeltere Fenster als weitere Seiten) und Jahresansicht (ein
//      Balken pro Kalenderjahr). Ein Jahr erscheint NUR, wenn es
//      abgeschlossen UND von Januar bis Dezember lueckenlos erfasst ist (s.
//      buildMonthlyData). Ein Teiljahr wie 2026 (Start 23.03.) neben vollen
//      Jahren wuerde einen Rueckgang vortaeuschen, den es nie gab.
//
// Effizienz, Nutzer-Vorgabe 26.09.2026 ("Vorschlaege umsetzen"): nicht
// abgerechnete Tage als "ausstehend" statt als 0-Balken (die 0 zog den Ø von
// 112,6 auf 90,1), Y-Achse reicht immer bis ueber das Ziel (niceScale),
// Legende mit Abstand zum Ziel und Zielquote "erreicht an x von n Tagen".
// Die Quelle der 0 ist in src/data/pool_settlement_sync.py behoben.
//
// Quellen-Vorrang seit 26.09.2026: F2Pools payout_history (taegliche
// Gutschriften, vom Pool selbst gefuehrt) gewinnt fuer jeden Monat, den sie
// vollstaendig abdeckt; pool_monthly.csv fuellt nur Monate davor. Vorher galt
// CSV zuerst. Umgedreht, weil der CSV-Pfad live nichts liefert (am 26.09.
// geprueft: Datei fehlt auf dem Host, obwohl der Monatsreset am 01.09. lief,
// und der MTD-Akkumulator steht auf 0). Eine spaeter doch geschriebene
// 0-Zeile haette sonst den echten Monatswert aus den Gutschriften
// ueberschrieben und den Monat aus dem Chart geloescht.

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

// Literal statt var(): ApexCharts loest CSS-Variablen in seinen Optionen
// nicht auf (gleiche Begruendung wie in den uebrigen bitgrid_*_chart.js).
const COLOR_MINING = "#F7931A"; // bg-color-super / bgai-mining-v3
const COLOR_STD = "#26C6DA"; // bg-color-standard — Trend/Vergleichswert
const COLOR_ECO = "#4CAF50"; // bg-color-eco — Ziel/positiv
const COLOR_WHITE = "#FFFFFF"; // Effizienz-Balken (Nutzer-Vorgabe 26.09.2026)

const MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];
const MONTH_WINDOW = 12;
const X_TITLE_STYLE = { color: "rgba(255,255,255,0.55)", fontSize: "15px", fontFamily: "Roboto, sans-serif", fontWeight: 400 };

// Obergrenze + Tick-Anzahl fuer eine Y-Achse ab 0, die `top` sicher
// einschliesst (Schrittweite 1/2/2,5/5 x 10^n). targetTicks steuert, wie
// dicht die Achse beschriftet wird: 6 fuer die Effizienz (hohe Karte),
// weniger fuer die flachere Langzeitbilanz (27.09.2026, Nutzer-Wunsch
// "weniger Werte auf der Achse damit es uebersichtlich bleibt").
function niceScale(top, targetTicks = 6) {
  const raw = (Math.max(top, 1) * 1.08) / targetTicks;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].find((f) => f * mag >= raw) * mag;
  const max = Math.ceil((Math.max(top, 1) * 1.08) / step) * step;
  return { max, ticks: Math.round(max / step) };
}

const monthKey = (y, m) => `${y}-${String(m).padStart(2, "0")}`;

// Monats-/Jahresbilanz aus beiden Quellen zusammenfuehren. Pure Funktion
// (kein DOM, kein hass), damit sie isoliert pruefbar bleibt.
//   rawRows:    sensor.pool_monthly_history.rows ("YYYY,MM,btc|...")
//   payoutHist: sensor.pool_balance_btc.payout_history ([[ts, desc, btc], ...])
//   now:        Date, bestimmt den laufenden Monat und das laufende Jahr
// Liefert:
//   months:        [{ y, m, btc, live }] chronologisch, nur Monate mit Ertrag
//                  oder der laufende Monat (wie bisher)
//   years:         [{ y, btc }] nur abgeschlossene, lueckenlos erfasste Jahre
function buildMonthlyData(rawRows, payoutHist, now) {
  const csvMap = {};
  if (rawRows && rawRows !== "unknown" && rawRows !== "unavailable") {
    rawRows
      .split("|")
      .filter((e) => e.includes(","))
      .forEach((e) => {
        const [y, m, btc] = e.split(",");
        csvMap[monthKey(parseInt(y), parseInt(m))] = parseFloat(btc) || 0;
      });
  }

  const payoutMap = {};
  let firstTs = null;
  (payoutHist || []).forEach((e) => {
    const ts = e[0],
      desc = e[1],
      btc = e[2];
    if (!ts || typeof btc !== "number" || btc <= 0) return;
    if (typeof desc === "string" && !desc.includes("user_payout")) return;
    const k = ts.slice(0, 7);
    payoutMap[k] = (payoutMap[k] || 0) + btc;
    if (firstTs === null || ts < firstTs) firstTs = ts;
  });

  // Erster Monat, den die Gutschriften vollstaendig abdecken. Der Monat der
  // ersten Gutschrift zaehlt nur, wenn sie am 1. liegt, sonst ist er
  // angebrochen (Mining-Start oder von F2Pool abgeschnittene Historie).
  let fullFrom = null;
  if (firstTs !== null) {
    const y = parseInt(firstTs.slice(0, 4));
    const m = parseInt(firstTs.slice(5, 7));
    const d = parseInt(firstTs.slice(8, 10));
    fullFrom = d === 1 ? monthKey(y, m) : m === 12 ? monthKey(y + 1, 1) : monthKey(y, m + 1);
  }
  // Innerhalb der Abdeckung ist ein Monat ohne Gutschrift ein echter
  // Nullmonat (z. B. Miner im Winter aus), kein Datenloch: payout_history ist
  // F2Pools Buchungsjournal, nicht eine Stichprobe.
  const covered = (k) => fullFrom !== null && k >= fullFrom;
  const known = (k) => covered(k) || csvMap[k] !== undefined;
  const valueOf = (k) => (covered(k) ? payoutMap[k] || 0 : csvMap[k] !== undefined ? csvMap[k] : payoutMap[k] || 0);

  const curKey = monthKey(now.getFullYear(), now.getMonth() + 1);
  const months = [...new Set([...Object.keys(csvMap), ...Object.keys(payoutMap)])]
    .sort()
    .map((k) => {
      const [y, m] = k.split("-").map(Number);
      return { y, m, btc: valueOf(k), live: k === curKey };
    })
    .filter((mo) => mo.btc > 0 || mo.live);

  const years = [];
  if (months.length > 0) {
    for (let y = months[0].y; y < now.getFullYear(); y++) {
      let complete = true;
      let btc = 0;
      for (let m = 1; m <= 12 && complete; m++) {
        const k = monthKey(y, m);
        if (known(k)) btc += valueOf(k);
        else complete = false;
      }
      if (complete) years.push({ y, btc });
    }
  }

  return { months, years };
}

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

function isoDay(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const SHARED_STYLE = `
  :host { display: block; }
  /* height 100% (17.10.2026, "Karten nebeneinander buendig"): fuellt den Host,
     wenn www/bitgrid_wide.js die Spalte streckt (Host = wachsendes Flex-Element);
     sonst ist die Host-Hoehe auto und die Regel wirkungslos. */
  .bgai-card {
    height: 100%;
    box-sizing: border-box;
    padding: 14px 18px;
    background: var(--ha-card-background);
    border-radius: var(--bgai-card-radius-v3);
    border: var(--bgai-card-border-width-v3) solid var(--bgai-card-border-v3);
    box-shadow: var(--bgai-card-shadow-v3);
    overflow: hidden;
  }
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
    --mdc-icon-size: 28px;
    width: 28px; height: 28px;
  }
  .bgai-cycler-arrow.disabled { opacity: 0.25; cursor: default; pointer-events: none; }
  .bgai-cycler-title {
    text-align: center;
    font-size: var(--bg-fs-body);
    font-weight: 700;
    color: var(--primary-text-color);
  }
  .bgai-toggle { display: flex; gap: 4px; margin-bottom: 8px; }
  .bgai-toggle-btn {
    cursor: pointer;
    padding: 6px;
    flex: 1 1 0;
    text-align: center;
    border-radius: 8px;
    font-size: var(--bg-fs-secondary);
    font-weight: 700;
    color: var(--secondary-text-color);
  }
  .bgai-toggle-btn.active { color: var(--primary-text-color); background: var(--secondary-background-color); }
  #chart { width: 100%; }
  .bgai-msg { padding: 30px 0; text-align: center; color: var(--secondary-text-color); font-size: var(--bg-fs-body); }
  .bgai-legend {
    display: flex; flex-wrap: wrap; justify-content: center; align-items: center;
    column-gap: 16px; row-gap: 4px; padding-top: 12px; margin-top: 8px;
    background-image: linear-gradient(to right, transparent, var(--divider-color) 15%, var(--divider-color) 85%, transparent);
    background-repeat: no-repeat; background-size: 100% 2px; background-position: top;
  }
  .bgai-legend-item { display: flex; align-items: center; gap: 6px; font-size: 16px; font-family: Roboto, sans-serif; font-weight: 400; text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9); }
  .bgai-legend-dot { --mdc-icon-size: 20px; width: 20px; height: 20px; flex: 0 0 auto; filter: drop-shadow(0 0 3px rgba(0,0,0,.9)) drop-shadow(0 0 3px rgba(0,0,0,.9)); }
  .apexcharts-text, .apexcharts-xaxis-annotation-label, .apexcharts-yaxis-annotation-label { text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9) !important; }
`;

class BitgridBarTrendChart extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._mode = this._config.mode === "monthly" ? "monthly" : "efficiency";
    this._period = "woche"; // nur Effizienz-Modus
    this._offset = 0; // nur Effizienz-Modus
    this._mPage = "m0"; // nur Langzeitbilanz: "y" = Jahre, "m<n>" = n-tes Monatsfenster zurueck
    if (!this.shadowRoot) this._buildDom();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._mode === "monthly") {
      this._render();
    } else {
      this._maybeFetchEfficiency();
    }
  }

  getCardSize() {
    return 6;
  }

  _buildDom() {
    const root = this.attachShadow({ mode: "open" });
    const toggleHtml =
      this._mode === "efficiency"
        ? `<div class="bgai-toggle" id="toggle">
             <div class="bgai-toggle-btn" data-period="woche">Woche</div>
             <div class="bgai-toggle-btn" data-period="monat">Monat</div>
           </div>`
        : "";
    root.innerHTML = `
      <style>${SHARED_STYLE}</style>
      <div class="bgai-card">
        ${toggleHtml}
        <div class="bgai-cycler">
          <ha-icon class="bgai-cycler-arrow" id="prev" icon="mdi:chevron-left"></ha-icon>
          <div class="bgai-cycler-title" id="title"></div>
          <ha-icon class="bgai-cycler-arrow" id="next" icon="mdi:chevron-right"></ha-icon>
        </div>
        <div id="chart"></div>
        <div id="legend" class="bgai-legend"></div>
      </div>
    `;
    this._titleEl = root.getElementById("title");
    this._chartEl = root.getElementById("chart");
    this._legendEl = root.getElementById("legend");
    this._prevEl = root.getElementById("prev");
    this._nextEl = root.getElementById("next");
    this._prevEl.addEventListener("click", () => (this._mode === "monthly" ? this._cycleMonthly(-1) : this._page(1)));
    this._nextEl.addEventListener("click", () => (this._mode === "monthly" ? this._cycleMonthly(1) : this._page(-1)));

    const toggleEl = root.getElementById("toggle");
    if (toggleEl) {
      toggleEl.querySelectorAll(".bgai-toggle-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          this._period = btn.dataset.period;
          this._offset = 0;
          this._render();
        });
      });
    }
  }

  // dir: +1 = weiter zurueck in die Vergangenheit, -1 = Richtung Gegenwart.
  _page(dir) {
    this._offset = Math.max(0, this._offset + dir);
    this._render();
  }

  async _maybeFetchEfficiency() {
    if (!this._hass) return;
    const now = Date.now();
    // 26.09.2026, gleicher Bug wie bitgrid_verlauf_chart.js: disconnectedCallback()
    // zerstoert this._apexChart beim View-Wechsel; _render() baut sie zwar bei
    // Bedarf neu auf, wurde aber innerhalb der Cache-Frist nie erreicht.
    if (this._apexChart && this._lastFetch && now - this._lastFetch < 5 * 60 * 1000) {
      this._render();
      return;
    }
    this._lastFetch = now;
    try {
      this._efficiencyData = await fetch("/local/energy_to_sats.json?v=" + Date.now()).then((r) => r.json());
    } catch (e) {
      this._efficiencyData = null;
    }
    this._render();
  }

  _render() {
    if (!this._titleEl) return;
    if (this._mode === "monthly") this._renderMonthly();
    else this._renderEfficiency();
  }

  // ── Effizienz (Energy-to-Sats), Woche/Monat-Paging ──────────────────────
  _renderEfficiency() {
    const root = this.shadowRoot;
    root.querySelectorAll(".bgai-toggle-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.period === this._period);
    });

    const data = this._efficiencyData;
    if (!data || !Array.isArray(data.days)) {
      this._titleEl.textContent = "";
      this._legendEl.innerHTML = "";
      this._showMessage(data ? "Keine Daten geladen." : "Lade Effizienz-Historie …");
      return;
    }

    const today = simToday(this._hass) || new Date();
    let rangeStart, rangeEnd, label;
    if (this._period === "monat") {
      const base = new Date(today.getFullYear(), today.getMonth() - this._offset, 1);
      rangeStart = new Date(base.getFullYear(), base.getMonth(), 1);
      rangeEnd = new Date(base.getFullYear(), base.getMonth() + 1, 0);
      label = base.toLocaleDateString("de-DE", { month: "long", year: "numeric" });
    } else {
      const dow = (today.getDay() + 6) % 7;
      rangeStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - dow - this._offset * 7);
      rangeEnd = new Date(rangeStart.getFullYear(), rangeStart.getMonth(), rangeStart.getDate() + 6);
      const fmt = (d) => d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
      label = `${fmt(rangeStart)} – ${fmt(rangeEnd)} ${rangeEnd.getFullYear()}`;
    }
    this._titleEl.textContent = label + (this._offset === 0 ? " (aktuell)" : "");
    this._nextEl.classList.toggle("disabled", this._offset === 0);

    const rangeStartIso = isoDay(rangeStart);
    const rangeEndIso = isoDay(rangeEnd);
    // Nicht abgerechnete Tage (26.09.2026): F2Pool rechnet einen Tag erst am
    // Folgetag ab, der Export laeuft davor. Gestern fehlt deshalb meist und
    // wird als "ausstehend" gezeigt statt stillschweigend zu fehlen; ein
    // Wert <= 0 ist keine Messung (Altlast aus dem Fallback-Log, s.
    // pool_settlement_sync.py) und zaehlt nie in Ø oder Zielquote.
    const byDay = new Map(data.days.filter((d) => d.day >= rangeStartIso && d.day <= rangeEndIso).map((d) => [d.day, d.energy_to_sats]));

    // Lueckenlose Tagesachse (27.09.2026, Nutzer-Befund "die Bezeichner
    // passen nicht richtig zu den Balken"): bisher standen NUR Tage mit
    // Abrechnung als Kategorie, die Achse sprang also ueber Luecken und
    // passte nicht mehr zum Zeitraum im Titel. Jetzt jeder Tag von
    // Zeitraumbeginn bis heute, fehlende Tage bleiben als Leerstelle sichtbar.
    const lastDay = rangeEnd > today ? today : rangeEnd;
    const days = [];
    for (let d = new Date(rangeStart.getFullYear(), rangeStart.getMonth(), rangeStart.getDate()); d <= lastDay; d.setDate(d.getDate() + 1)) {
      days.push(isoDay(d));
    }

    if (days.length === 0) {
      this._legendEl.innerHTML = "";
      this._showMessage("Keine F2Pool-Abrechnung in diesem Zeitraum.");
      return;
    }

    const target = data.target_sats_per_kwh ?? 45;
    const isSettled = (v) => typeof v === "number" && v > 0;
    const valueOf = (iso) => (byDay.has(iso) ? byDay.get(iso) : null);
    const settledVals = days.map(valueOf).filter(isSettled);
    const n = settledVals.length;
    const avgVal = n > 0 ? settledVals.reduce((a, b) => a + b, 0) / n : null;
    const hits = settledVals.filter((v) => v >= target).length;
    const fmt1 = (v) => v.toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

    // Einzeilige, kurze Kategorien statt der frueheren zweizeiligen Labels
    // ["08.09", "keine Daten"]: gedreht liefen die in den Nachbartag hinein
    // ("Keine Dat08.09"). Im Monat reicht die Tageszahl, der Monat steht im
    // Titel — damit passen auch 31 Labels waagerecht nebeneinander. Was mit
    // einem leeren Tag ist, sagen Tooltip und Legende.
    const dayLabel = (iso) => (this._period === "monat" ? iso.slice(8, 10) : iso.slice(8, 10) + "." + iso.slice(5, 7));
    const categories = days.map(dayLabel);
    // Balken am oder ueber Ziel in der Eco-Rolle, darunter weiss: dieselbe
    // Farbe wie die Ziellinie steht damit fuer dieselbe Aussage ("Ziel
    // erreicht") statt fuer zwei verschiedene Dinge (27.09.2026, Nutzer-
    // Befund "die Farben sind auch 2x Gruen").
    const series = [
      {
        name: "Tageswert",
        data: days.map((iso) => {
          const v = valueOf(iso);
          const ok = isSettled(v);
          return { x: dayLabel(iso), y: ok ? v : null, fillColor: ok && v >= target ? COLOR_ECO : COLOR_WHITE };
        }),
      },
    ];

    // Legende: drei Zeilen, jede Farbe genau einmal und mit klarer Zustaendig-
    // keit — weiss = Balken/Datenlage, cyan = Ø-Linie, gruen = Ziel. Vorher
    // trugen zwei gruene Zeilen zwei verschiedene Aussagen, und der Ø stand
    // in Weiss, obwohl seine Linie im Chart cyan ist.
    const openDays = days.length - n;
    this._legendEl.innerHTML = "";
    this._legendItem(
      "mdi:chart-bar",
      COLOR_WHITE,
      "Tageswerte:",
      `${n} von ${days.length} abgerechnet${openDays > 0 ? `, ${openDays} offen` : ""}`
    );
    if (n > 0) {
      const diff = avgVal - target;
      const pct = Math.round((diff / target) * 100);
      this._legendItem("mdi:chart-line", COLOR_STD, "Tagesdurchschnitt:", `${fmt1(avgVal)} sats/kWh`);
      this._legendItem(
        "mdi:flag-checkered",
        COLOR_ECO,
        `Ziel ${target}:`,
        `${hits} von ${n} ${n === 1 ? "Tag" : "Tagen"} erreicht · Ø ${fmt1(Math.abs(diff))} ${diff >= 0 ? "darüber" : "darunter"} (${pct >= 0 ? "+" : "−"}${Math.abs(pct)} %)`
      );
    } else {
      this._legendItem("mdi:flag-checkered", COLOR_ECO, "Ziel:", `${target} sats/kWh`);
    }

    const yLines = [{ y: target, color: COLOR_ECO, dash: 0, label: `Ziel ${target}` }];
    if (n > 0) yLines.push({ y: avgVal, color: COLOR_STD, dash: 4, label: `Ø ${fmt1(avgVal)}` });

    this._renderApexBars({
      series,
      categories,
      colors: [COLOR_WHITE],
      yTitle: "sats/kWh",
      xTitle: "Tag",
      yLines,
      unit: " sats/kWh",
      yWhite: true,
      // Kurze Labels brauchen keine Drehung mehr, auch nicht bei 31 Tagen.
      rotateLabels: 0,
      // Achse reicht immer bis ueber das Ziel: ApexCharts erweitert die
      // Skala nicht fuer Annotationen, bei Ziel 130 und Achse bis 120 war die
      // Ziellinie bisher schlicht abgeschnitten.
      yScale: niceScale(Math.max(target, ...settledVals)),
    });
  }

  // ── Langzeitbilanz: Seiten per Pfeil ────────────────────────────────────
  // Seitenfolge [Jahre, aeltestes Monatsfenster, ..., aktuelles Monats-
  // fenster] mit Umlauf: links = weiter zurueck bzw. verdichtet, rechts =
  // Richtung Gegenwart. Startseite ist das aktuelle Monatsfenster. Mit den
  // heutigen Daten (< 12 Monate) sind das genau zwei Seiten.
  _monthlyPages() {
    const hass = this._hass;
    const data = buildMonthlyData(
      hass.states["sensor.pool_monthly_history"]?.attributes?.rows ?? "",
      hass.states["sensor.pool_balance_btc"]?.attributes?.payout_history ?? [],
      simToday(hass) || new Date()
    );
    const pages = ["y"];
    for (let i = Math.ceil(data.months.length / MONTH_WINDOW) - 1; i >= 0; i--) pages.push("m" + i);
    return { data, pages };
  }

  _cycleMonthly(dir) {
    if (!this._hass) return;
    const { pages } = this._monthlyPages();
    const idx = Math.max(0, pages.indexOf(this._mPage));
    this._mPage = pages[(idx + dir + pages.length) % pages.length];
    this._render();
  }

  _renderMonthly() {
    if (!this._hass) return;
    const { data, pages } = this._monthlyPages();

    if (data.months.length === 0) {
      this._titleEl.textContent = "";
      this._legendEl.innerHTML = "";
      this._prevEl.classList.add("disabled");
      this._nextEl.classList.add("disabled");
      this._showMessage("Noch keine Monatsdaten.");
      return;
    }

    if (!pages.includes(this._mPage)) this._mPage = pages[pages.length - 1];
    this._prevEl.classList.remove("disabled");
    this._nextEl.classList.remove("disabled");

    if (this._mPage === "y") this._renderYears(data);
    else this._renderMonthWindow(data.months, parseInt(this._mPage.slice(1)));
  }

  _renderMonthWindow(allMonths, offset) {
    const endIdx = allMonths.length - offset * MONTH_WINDOW;
    const months = allMonths.slice(Math.max(0, endIdx - MONTH_WINDOW), endIdx);

    const fmtLabel = (mo) => MONATE[mo.m - 1] + " '" + String(mo.y).slice(2);
    // 27.09.2026, Nutzer-Wunsch: zwischen den Pfeilen nur das Jahr statt
    // "Monate · Mär '26 – Sep '26". Die Monatsnamen stehen ohnehin an der
    // X-Achse. Ein 12-Monats-Fenster kann zwei Jahre ueberspannen, dann
    // beide.
    const yearsInWindow = [...new Set(months.map((m) => m.y))];
    this._titleEl.textContent =
      yearsInWindow.length === 1 ? String(yearsInWindow[0]) : `${yearsInWindow[0]} – ${yearsInWindow[yearsInWindow.length - 1]}`;

    const fmtSats = (btc) => Math.round(btc * 1e8);
    const completedSats = months.filter((m) => !m.live).map((m) => fmtSats(m.btc));
    const avgSats = completedSats.length > 0 ? completedSats.reduce((a, b) => a + b, 0) / completedSats.length : 0;
    const sumSats = months.reduce((a, m) => a + fmtSats(m.btc), 0);

    // Array-Label = zweizeilig (s. Kopf, Punkt 2).
    const labelOf = (m) => (m.live ? [fmtLabel(m), "(laufend)"] : fmtLabel(m));
    const categories = months.map(labelOf);
    const series = [
      {
        name: "Monatsertrag",
        data: months.map((m) => ({ x: labelOf(m), y: fmtSats(m.btc), fillColor: m.live ? "rgba(247,147,26,0.4)" : COLOR_MINING })),
      },
    ];

    // 27.09.2026, Nutzer-Wunsch: "Monatsertrag" traegt jetzt die Summe des
    // sichtbaren Fensters, "Ø Fenster" heisst "Monatsdurchschnitt" (das alte
    // Wort beschrieb die Rechengrundlage, nicht die Aussage). Der Ø zaehlt
    // weiterhin nur abgeschlossene Monate, der laufende wuerde ihn nach unten
    // ziehen; die Summe schliesst ihn ein, sie ist eine Summe und keine
    // Hochrechnung.
    const n = months.length;
    this._legendEl.innerHTML = "";
    this._legendItem("mdi:chart-bar", COLOR_MINING, "Monatsertrag:", `${sumSats.toLocaleString("de-DE")} Sats (${n} ${n === 1 ? "Monat" : "Monate"})`);
    if (avgSats > 0) this._legendItem("mdi:chart-line", COLOR_STD, "Monatsdurchschnitt:", `${Math.round(avgSats).toLocaleString("de-DE")} Sats`);

    this._renderApexBars({
      series,
      categories,
      colors: [COLOR_MINING],
      yTitle: "Sats",
      xTitle: "Monat",
      yLines: avgSats > 0 ? [{ y: avgSats, color: COLOR_STD, dash: 4, label: `Ø ${Math.round(avgSats).toLocaleString("de-DE")}` }] : [],
      unit: " Sats",
      yWhite: true,
      // Flachere Karte (s. pool_monthly_chart.yaml): weniger Y-Beschriftungen,
      // sonst stehen sie bei ~210px Hoehe zu dicht.
      yScale: niceScale(Math.max(...months.map((m) => fmtSats(m.btc)), avgSats, 1), 4),
    });
  }

  // Jahr des naechsten Halvings aus sensor.bitcoin_next_halving (Attribut
  // next_halving_date, packages/bitcoin.yaml: Hochrechnung aus der mempool-
  // Blockhoehe mit der Ziel-Blockzeit). Dient nur als Horizont der leeren
  // Folgejahre, nicht als Messwert. Ohne den Sensor gibt es keinen belegten
  // Horizont, dann endet der Chart beim laufenden Jahr.
  _halvingYear() {
    const iso = this._hass?.states["sensor.bitcoin_next_halving"]?.attributes?.next_halving_date;
    const ms = iso ? Date.parse(iso) : NaN;
    return Number.isFinite(ms) ? new Date(ms).getFullYear() : null;
  }

  _renderYears(data) {
    const curYear = (simToday(this._hass) || new Date()).getFullYear();
    // 27.09.2026, Nutzer-Wunsch: die Jahresansicht beginnt beim laufenden
    // Jahr (Balken halbtransparent und "(laufend)" beschriftet, genau wie der
    // laufende Monat) und reicht bis zum Halving-Jahr, die Jahre dazwischen
    // als leere Balken.
    // Bewusste Abgrenzung: leere Folgejahre sind PLATZHALTER, kein Messwert 0.
    // Sie fliessen darum weder in den Ø noch in die Summe ein, und der Ø
    // zaehlt weiterhin nur abgeschlossene, lueckenlos erfasste Jahre (s.
    // buildMonthlyData) — ein Teiljahr neben vollen Jahren wuerde einen
    // Rueckgang vortaeuschen, den es nie gab.
    const closed = data.years;
    const liveBtc = data.months.filter((m) => m.y === curYear).reduce((a, m) => a + m.btc, 0);
    const halvingYear = this._halvingYear();

    const toSats = (btc) => Math.round(btc * 1e8);
    const rows = [
      ...closed.map((yr) => ({ y: yr.y, sats: toSats(yr.btc), kind: "closed" })),
      { y: curYear, sats: toSats(liveBtc), kind: "live" },
    ];
    for (let y = curYear + 1; halvingYear !== null && y <= halvingYear; y++) rows.push({ y, sats: 0, kind: "future" });

    const first = rows[0].y;
    const last = rows[rows.length - 1].y;
    this._titleEl.textContent = first === last ? `Jahre · ${first}` : `Jahre · ${first} – ${last}`;

    // Ø erst ab zwei abgeschlossenen Jahren: bei einem waere die Linie nur
    // der Balken selbst.
    const closedSats = closed.map((yr) => toSats(yr.btc));
    const avgSats = closedSats.length >= 2 ? closedSats.reduce((a, b) => a + b, 0) / closedSats.length : 0;
    const sumSats = rows.filter((r) => r.kind !== "future").reduce((a, r) => a + r.sats, 0);
    const nData = rows.filter((r) => r.kind !== "future").length;

    // Array-Label = zweizeilig, gleiches Muster wie der laufende Monat.
    const labelOf = (r) => (r.kind === "live" ? [String(r.y), "(laufend)"] : String(r.y));
    const fillOf = (r) =>
      r.kind === "live" ? "rgba(247,147,26,0.4)" : r.kind === "future" ? "rgba(247,147,26,0.15)" : COLOR_MINING;

    this._legendEl.innerHTML = "";
    this._legendItem("mdi:chart-bar", COLOR_MINING, "Jahresertrag:", `${sumSats.toLocaleString("de-DE")} Sats (${nData} ${nData === 1 ? "Jahr" : "Jahre"})`);
    if (avgSats > 0) {
      this._legendItem("mdi:chart-line", COLOR_STD, "Jahresdurchschnitt:", `${Math.round(avgSats).toLocaleString("de-DE")} Sats`);
    } else {
      // Erklaert die fehlende Ø-Linie, statt sie kommentarlos wegzulassen.
      this._legendItem("mdi:chart-line", COLOR_STD, "Ø ab zwei abgeschlossenen Jahren", null);
    }
    if (halvingYear !== null && halvingYear > curYear) {
      this._legendItem("mdi:content-cut", "var(--secondary-text-color)", "Leere Balken bis Halving:", `ca. ${halvingYear}`);
    }

    this._renderApexBars({
      series: [{ name: "Jahresertrag", data: rows.map((r) => ({ x: labelOf(r), y: r.sats, fillColor: fillOf(r) })) }],
      categories: rows.map(labelOf),
      colors: [COLOR_MINING],
      yTitle: "Sats",
      xTitle: "Jahr",
      yLines: avgSats > 0 ? [{ y: avgSats, color: COLOR_STD, dash: 4, label: `Ø ${Math.round(avgSats).toLocaleString("de-DE")}` }] : [],
      unit: " Sats",
      yWhite: true,
      yScale: niceScale(Math.max(...rows.map((r) => r.sats), avgSats, 1), 4),
    });
  }

  // Meldung statt Chart. Zerstoert eine vorhandene ApexCharts-Instanz:
  // sonst ruft der naechste Render updateOptions() auf einem Chart auf,
  // dessen DOM hier gerade ersetzt wurde, und die Karte bleibt leer (tritt
  // mit dem Seitenwechsel Jahre -> Monate bei jedem Blaettern auf).
  // min-height haelt die Kartenhoehe beim Blaettern stabil.
  _showMessage(text) {
    this._renderSeq = (this._renderSeq || 0) + 1;
    if (this._apexChart) {
      this._apexChart.destroy();
      this._apexChart = null;
    }
    const msg = document.createElement("div");
    msg.className = "bgai-msg";
    msg.style.minHeight = `${this._config.height || 260}px`;
    msg.style.boxSizing = "border-box";
    msg.textContent = text;
    this._chartEl.replaceChildren(msg);
  }

  // 27.09.2026, Nutzer-Wunsch: Messwerte in der Legende weiss, damit sie sich
  // vom Farbcode der Serie abheben. Icon und Beschriftung tragen weiter die
  // Serienfarbe (die Zuordnung Legende -> Balken/Linie haengt daran), der
  // Wert dahinter steht in Weiss und etwas fetter.
  _legendItem(icon, color, text, value = null) {
    const item = document.createElement("span");
    item.className = "bgai-legend-item";
    const dot = document.createElement("ha-icon");
    dot.className = "bgai-legend-dot";
    dot.setAttribute("icon", icon);
    dot.style.color = color;
    const label = document.createElement("span");
    label.style.color = color;
    label.textContent = text;
    item.appendChild(dot);
    item.appendChild(label);
    if (value !== null) {
      const val = document.createElement("span");
      val.style.color = COLOR_WHITE;
      val.style.fontWeight = "600";
      val.textContent = value;
      item.appendChild(val);
    }
    this._legendEl.appendChild(item);
  }

  async _renderApexBars({ series, categories, colors, yTitle, xTitle, yLines, unit, yWhite = false, yScale = null, rotateLabels = null }) {
    // Nur der juengste Render-Auftrag darf zeichnen: waehrend ApexCharts beim
    // ersten Aufruf noch laedt, koennen Seitenwechsel/hass-Updates dazwischen
    // kommen (sonst landet ein Chart unter einer Meldung).
    const seq = (this._renderSeq = (this._renderSeq || 0) + 1);
    try {
      await loadApexCharts();
    } catch (e) {
      this._showMessage("ApexCharts konnte nicht geladen werden.");
      return;
    }
    if (seq !== this._renderSeq) return;
    // Eine Meldung (s. _showMessage) steht noch im Container: vor dem ersten
    // Zeichnen leeren, sonst rendert ApexCharts darunter.
    if (!this._apexChart) this._chartEl.replaceChildren();

    const yColor = yWhite ? "#FFFFFF" : COLOR_MINING;
    const yTitleStyle = yWhite ? X_TITLE_STYLE : { color: COLOR_MINING, fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 };

    const options = {
      chart: {
        type: "bar",
        height: this._config.height || 260,
        toolbar: { show: false },
        zoom: { enabled: false },
        background: "transparent",
        foreColor: "#FFFFFF",
        dropShadow: { enabled: true, top: 0, left: 0, blur: 3, opacity: 0.4 },
        animations: { enabled: false },
      },
      series,
      colors,
      plotOptions: { bar: { columnWidth: "55%", borderRadius: 3 } },
      dataLabels: { enabled: false },
      xaxis: {
        categories,
        title: {
          text: xTitle,
          offsetY: -4,
          style: X_TITLE_STYLE,
        },
        labels: {
          style: { colors: "#FFFFFF", fontSize: "13px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
          rotate: rotateLabels !== null ? rotateLabels : categories.length > 10 ? -45 : 0,
          // Falls es doch zu eng wird (schmales Tablet, 31 Tage): ApexCharts
          // laesst einzelne Beschriftungen weg, statt sie uebereinander zu
          // stapeln.
          hideOverlappingLabels: true,
        },
        axisTicks: { show: true },
      },
      yaxis: {
        ...(yScale ? { min: 0, max: yScale.max, tickAmount: yScale.ticks } : {}),
        title: {
          text: yTitle,
          style: yTitleStyle,
        },
        labels: {
          style: { colors: yColor, fontSize: "17px", fontFamily: "Roboto, sans-serif" },
          formatter: (v) => Math.round(v).toLocaleString("de-DE"),
        },
      },
      grid: {
        borderColor: "rgba(255,255,255,0.07)",
        strokeDashArray: 4,
        padding: { left: 15, right: 15 },
      },
      legend: { show: false },
      annotations: {
        yaxis: (yLines || []).map((l) => ({
          y: l.y,
          borderColor: l.color,
          strokeDashArray: l.dash,
          label: {
            text: l.label,
            position: "right",
            offsetX: -4,
            borderColor: "transparent",
            style: { color: l.color, background: "transparent", fontSize: "13px", fontWeight: 600, fontFamily: "Roboto, sans-serif" },
          },
        })),
      },
      tooltip: {
        theme: "dark",
        custom: ({ series: s, seriesIndex, dataPointIndex, w }) => {
          const rawCat = w.globals.labels[dataPointIndex] ?? categories[dataPointIndex];
          const cat = Array.isArray(rawCat) ? rawCat.join(" ") : rawCat;
          const val = s[seriesIndex][dataPointIndex];
          const valText = val === null || val === undefined ? "noch nicht abgerechnet" : `${Math.round(val).toLocaleString("de-DE")}${unit}`;
          return `
            <div style="background:#1a1a2e;min-width:160px;border-radius:6px;overflow:hidden;">
              <div style="background:#000000;color:#FFFFFF;font-family:Roboto,sans-serif;font-weight:700;font-size:14px;padding:6px 12px;">${cat}</div>
              <div style="padding:6px 12px;display:flex;align-items:center;gap:8px;">
                <span style="width:10px;height:10px;border-radius:50%;background:${colors[0]};flex:0 0 auto;"></span>
                <span style="color:#FFFFFF;font-family:Roboto,sans-serif;font-size:13px;font-weight:700;">${valText}</span>
              </div>
            </div>`;
        },
      },
    };

    await this._drawChart(options);
  }

  // 15.10.2026: Zeichnen serialisiert. _render() laeuft bei JEDEM hass-Update;
  // im Lab-Replay (Dutzende Zustandswechsel je Sekunde) ueberholten sich
  // render()/updateOptions() ("t.put is not a function"), der Chart blieb leer.
  // Jetzt: nur ein Zeichenvorgang zugleich, der juengste Wunsch wird danach
  // nachgeholt, unveraenderte Daten werden uebersprungen, ein Fehler verwirft
  // den Chart (naechster Durchlauf baut neu auf).
  async _drawChart(options) {
    const key = JSON.stringify([options.series, options.xaxis, options.yaxis, options.annotations]);
    if (this._chartBusy) {
      this._pendingOptions = options;
      return;
    }
    if (this._apexChart && key === this._drawnKey) return;
    this._chartBusy = true;
    try {
      if (this._apexChart) {
        await this._apexChart.updateOptions(options, true, true);
      } else {
        this._apexChart = new window.ApexCharts(this._chartEl, options);
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
      this._drawnKey = null;
    } finally {
      this._chartBusy = false;
    }
    if (this._pendingOptions) {
      const next = this._pendingOptions;
      this._pendingOptions = null;
      await this._drawChart(next);
    }
  }

  disconnectedCallback() {
    if (this._apexChart) {
      this._apexChart.destroy();
      this._apexChart = null;
    }
  }
}

customElements.define("bitgrid-bar-trend-chart", BitgridBarTrendChart);
