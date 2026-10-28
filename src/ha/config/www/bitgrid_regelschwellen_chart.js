// BitGridAI — Regelschwellen-Chart als eigenstaendiges Custom-Element mit
// rohem ApexCharts.js. Loest das handgeschriebene Inline-SVG ab, das bisher
// als custom_fields.chart-Template einer custom:button-card direkt in
// bitgrid_dashboard_v3.yaml lag (~180 Zeilen JS in einem YAML-Block).
//
// Zwei Gruende, 25.09.2026, Nutzer-Vorgabe:
//   1. "Regelschwellen soll aussehen wie beim Verlauf vom Stil her" — der
//      Verlauf-Chart (www/bitgrid_verlauf_chart.js) hat seit 12.-16.09.2026
//      einen durchgearbeiteten Stil (17px-Achsen in Serienfarbe, Text-Halo,
//      eigene HTML-Legende mit ha-icon + Live-Wert, gestricheltes Gitter,
//      chart-weiter dropShadow, Custom-Tooltip). Dieselbe Optik im SVG
//      nachzubauen hiesse, jeden dieser Werte ein zweites Mal von Hand zu
//      pflegen; mit derselben Bibliothek und denselben Options-Bloecken ist
//      die Stilgleichheit dagegen strukturell da.
//   2. "regelschwellen soll eigenes custom element sein" — raus aus dem
//      YAML-Block. Gleiches Hausmuster wie schon zweimal gegangen:
//      views/finanz_bilanz.yaml (rohes SVG in button-card -> www/
//      bitgrid_finanz_chart.js) und views/energieverlauf_tag.yaml.
//
// Der inhaltliche Aufbau ist 1:1 uebernommen und bleibt fachlich identisch:
// schematischer Batterie-Tagesgang (flach 20% bis Sonnenaufgang, Aufladung
// bis Mittag, Plateau, Entladung bis Sonnenuntergang), reale Sonnenkurve aus
// sun.sun, horizontale Schwellenlinien, Marker fuer Hoch-/Runterschalt-
// Punkte AUF der Kurve, echter SoC-Verlauf des Tages, "jetzt"-Linie + Live-
// Punkt.
//
// Unterschied zum SVG-Stand, der aus dem Bibliothekswechsel folgt:
//   - Die Bezier-Kurven rechnen jetzt in DATENKOORDINATEN (Dezimalstunde /
//     SoC-Prozent) statt in SVG-Pixeln und werden fein abgetastet an
//     ApexCharts uebergeben. Dadurch entfaellt die frueher noetige
//     Rueckrechnung Pixel->Kurvenparameter; die Marker-Mathematik
//     (Binaersuche ueber den Bezier-Parameter t) bleibt dieselbe, nur in
//     sauberen Einheiten.
//   - Die duenne Verbindungslinie zwischen Marker-Label und Marker-Punkt
//     entfaellt: ApexCharts' pointAnnotation kennt keinen Connector. Das
//     Label sitzt stattdessen ueber (Hochschalten) bzw. unter (Runter-
//     schalten) dem Punkt, s. mark().
//   - Die X-Achse zeigt wie beim Verlauf 3h-Schritte statt jeder Stunde mit
//     heller/dunkler Abstufung — das ist genau der Verlauf-Stil, der hier
//     gewuenscht war. Sie umspannt seit 25.09.2026 volle 24 Stunden von
//     0 bis 0 Uhr (Nutzer-Vorgabe: nachts die Batteriekurve im Blick
//     behalten, Sonnenhoechststand ungefaehr mittig), s. Block bei
//     X_START_HOUR.
//   - Der frueher fest eingeblendete Debug-Text oben rechts ("fetching/1pts")
//     ist jetzt optional (config.debug: true), weil der Verlauf-Chart so
//     etwas nicht kennt. Bewusst entfernt, nicht vergessen.
//
// Read-only auf hass.states und hass.callApi (History). Keine Zeile hiervon
// beeinflusst eine Steuerentscheidung — reines Anzeige-Modul in www/, der
// deterministische Kern in src/core/ bleibt unberuehrt.

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

// Modus-/Schwellenfarben als LITERALE, nicht als var(--bg-color-*): ApexCharts
// schreibt Farben intern in Attribute und loest CSS-Variablen dabei nicht auf
// (gleiche Begruendung wie in bitgrid_verlauf_chart.js und _finanz_chart.js).
// Werte gespiegelt aus themes/bitgrid.yaml, Zeilen 45-48 — bei einer
// Theme-Aenderung hier manuell nachziehen.
const COLOR_ECO = "#4CAF50"; // bg-color-eco
const COLOR_STD = "#26C6DA"; // bg-color-standard
const COLOR_SUPER = "#F7931A"; // bg-color-super
const COLOR_RESERVE = "#EF5350"; // bg-color-reserve

// 25.09.2026, Nutzer-Vorgabe "einheitliches Farbdesign": drei Farben hier
// NICHT aus dem Regelschwellen-eigenen Theme-Block genommen, sondern 1:1 aus
// bitgrid_verlauf_chart.js gespiegelt (SERIES_DEFS), weil dieselben
// Entitaeten/Rollen gemeint sind:
//   - Schematik ist der Fahrplan fuer die Miner-Umschaltung -> Icon der
//     Miner-Rolle (dort SERIES_DEFS "Miner-Verbrauch", mdi:pickaxe). Die
//     Farbe ist seit 26.09.2026 ein neutrales Grau, s. COLOR_SCHEMATIC.
//   - Verlauf heute UND die zugehoerige Achse zeigen sensor.battery_soc_pct
//     -> dieselbe Farbe wie die dortige "Batteriestand"-Serie/Achse, nicht
//     mehr Weiss (fruehere COLOR_TRACE) und nicht das allgemeine Eco-Gruen.
//     Nutzer-Korrektur 25.09.2026: die Linie sollte NICHT nur die Achse,
//     sondern auch sich selbst in diesem Gruenton zeigen.
//   - Sonnenstand-Achse zieht die PV-Rollenfarbe, weil beide Karten densel-
//     ben "was macht die Sonne gerade"-Bezug haben.
// Literal statt var(--bg-color-*): ApexCharts loest CSS-Variablen in seinen
// Optionen nicht auf (s. Kommentar oben bei COLOR_ECO).
// 26.09.2026, Nutzer-Befund "Gelb und Orange lassen sich schwer
// differenzieren": die Schematik lief bisher in der Miner-Rollenfarbe
// (#F7931A) direkt neben der gelb-orangen Sonne (COLOR_PV). Jetzt ein
// unauffaelliges Grau, damit sie als Referenzlinie in den Hintergrund tritt:
// bgai-pill-name-color-v3 (themes/bitgrid.yaml, rgba(255,255,255,0.55), das
// Styleguide-Token fuer gedaempfte Beschriftung), hier als deckender Hex-Wert
// auf der Kartenflaeche #313a55 wie alle anderen Serienfarben als Literal.
// Hell genug, dass die Legende "Schematik: .. %" in derselben Farbe lesbar
// bleibt.
const COLOR_SCHEMATIC = "#A2A6B3";
const COLOR_SOC = "#b3d804"; // Batteriestand-Farbe, bitgrid_verlauf_chart.js

// Batterie-Icon nach Ladestand, 1:1 aus bitgrid_verlauf_chart.js (dort
// batteryIconForSoc, Schwellen wie power-flow-card-plus: > 72 % high, > 44 %
// medium, > 16 % low, sonst outline, ohne Wert mdi:battery). Kopie statt
// Import: die Karten sind eigenstaendige Module ohne gemeinsames Bundle.
function batteryIconForSoc(state) {
  const soc = state ? parseFloat(state.state) : NaN;
  if (Number.isNaN(soc)) return "mdi:battery";
  if (soc > 72) return "mdi:battery-high";
  if (soc > 44) return "mdi:battery-medium";
  if (soc > 16) return "mdi:battery-low";
  return "mdi:battery-outline";
}
const COLOR_PV = "#fbb210"; // PV-Leistung-Farbe, bitgrid_verlauf_chart.js

// Entities, alle identisch zum bisherigen SVG-Stand.
const ENTITY_SOC = "sensor.battery_soc_pct";
const ENTITY_SUN = "sun.sun";
const ENTITY_SEASON = "sensor.mvp_saison_status";
const ENTITY_ECO = "input_number.mvp_soc_eco_start_pct";
const ENTITY_STD = "input_number.mvp_soc_std_pct";
const ENTITY_SUPER = "input_number.mvp_soc_super_pct";
const ENTITY_STOP = "input_number.mvp_soc_stop_pct";
const ENTITY_SUPER_OFF = "input_number.mvp_soc_super_off_pct";
const ENTITY_STD_OFF = "input_number.mvp_soc_std_off_pct";
// Lüftung-Nachlauf fürs Legenden-Item, s. Kommentar bei der Legenden-Reihe
// unten. Status-Sensor statt eigener Berechnung: rechnet in mvp_auto.yaml
// bereits exakt dasselbe (Aktiv/M:SS-Cooldown/Aus), keine Zweitlogik hier.
const ENTITY_LUEFTUNG_STATUS = "sensor.lueftung_status_display";

// Sichtbarer Ausschnitt: volle 24 Stunden ab Mitternacht, 0 Uhr bis 0 Uhr.
//
// Entwicklung der Vorgabe am 25.09.2026: erst 6..22 Uhr (schnitt die
// naechtliche Entladung ab, die den Ausgangspunkt des naechsten Ladetags
// bestimmt), dann 3..27 Uhr, jetzt 0..24. Ausschlaggebend fuer den letzten
// Schritt war die Symmetrie: der Sonnenhoechststand liegt in unseren Breiten
// gegen 13 Uhr, in einem Fenster ab 3 Uhr saesse er deutlich links der Mitte,
// ab Mitternacht bleibt er ungefaehr mittig. Die Nachtstunden sind weiterhin
// vollstaendig sichtbar, nur auf beide Raender verteilt statt am Stueck.
//
// X_START_HOUR bleibt als Parameter erhalten, statt die Umrechnung fuer den
// Sonderfall 0 wieder auszubauen: die Achse rechnet generisch in
// FENSTERSTUNDEN (X_START_HOUR .. X_START_HOUR+24). Bei einem Start ungleich
// Mitternacht waere Stunde 25 der Folgetag, eine echte Uhrzeit wuerde dort
// auf 0 zurueckspringen und Messpunkte an den linken Rand werfen. Bei
// X_START_HOUR = 0 sind Fensterstunde und Uhrzeit identisch, die Umrechnung
// ist dann wirkungslos und kostet nichts. Der Formatter rechnet ohnehin per
// Modulo zurueck; den rechten Rand laesst er seit 26.09.2026 unbeschriftet
// (s. xaxis.labels.formatter).
//
// tickAmount 24 ueber die Spanne 24 ergibt exakt 1.0 pro Schritt, damit
// liegen alle Ticks auf vollen Stunden und der Formatter blendet daraus die
// 3h-Schritte ein (0/3/6/9/12/15/18/21).
const X_START_HOUR = 0;
const X_MIN = X_START_HOUR;
const X_MAX = X_START_HOUR + 24;
const X_TICK_AMOUNT = 24;

// Beginn des aktuellen Fensters als echter Zeitpunkt. Bei X_START_HOUR = 0
// schlicht Mitternacht; der Rueckgriff auf den Vortag greift nur, wenn der
// Fensterstart spaeter am Tag liegt und die aktuelle Uhrzeit noch davor.
// Bezugspunkt fuer die History-Abfrage UND fuer die Umrechnung von
// Zeitstempeln auf Fensterstunden.
function windowStartFor(now) {
  const start = new Date(now);
  start.setHours(X_START_HOUR, 0, 0, 0);
  if (now.getHours() < X_START_HOUR) start.setDate(start.getDate() - 1);
  return start;
}

// Uhrzeit (0..24) -> Fensterstunde. Alles vor dem Fensterstart gehoert an das
// ENDE des Fensters, nicht an seinen Anfang. Bei X_START_HOUR = 0 unveraendert.
function axisPos(hour) {
  return hour >= X_START_HOUR ? hour : hour + 24;
}

// Schematischer Nacht-/Reserve-Sockel und Vollstand, in Prozent.
const BATTERY_FLOOR = 20;
const BATTERY_FULL = 100;
// Breite des Mittags-Plateaus in Stunden, bevor die schematische Entladung
// einsetzt (Wert aus dem SVG-Stand uebernommen).
const PLATEAU_HOURS = 1.5;

// Abtastdichte der schematischen Kurven. 120 Punkte pro Kurve sind fein genug,
// dass die Linie mit stroke.curve "straight" glatt wirkt — bewusst kein
// "smooth" fuer diese beiden Serien: ApexCharts' Spline wuerde an den
// Knickstellen (Plateau-Ein-/Ausstieg) ueber 100% hinausschwingen und damit
// einen Ladezustand zeichnen, den es nicht gibt.
const CURVE_SAMPLES = 120;

// Fallback-Sonnenzeiten, falls sun.sun (noch) keine Attribute liefert —
// identisch zu den Werten im bisherigen SVG.
const FALLBACK_RISE_H = 5.47;
const FALLBACK_NOON_H = 13.58;
const FALLBACK_SET_H = 21.68;

function num(hass, entityId, fallback) {
  const raw = parseFloat(hass.states[entityId]?.state);
  return Number.isNaN(raw) ? fallback : raw;
}

// Hex -> rgba, um die Deckkraft-Abstufungen des SVG-Stands ("opacity 0.35" auf
// den Schwellenlinien) auch dort nachzubilden, wo ApexCharts nur EINEN
// Farbwert entgegennimmt (Annotation-Border kennt keine eigene Opacity).
function withAlpha(hex, alpha) {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// Runterschalt-Punkte dunkler als die Hochschalt-Punkte derselben Farbe, damit
// "hoch"/"runter" auch ohne Pfeil-Text auf einen Blick erkennbar bleibt (Regel
// aus dem SVG-Stand). Dort per CSS color-mix() geloest, was hier ausfaellt:
// ApexCharts braucht einen fertigen Farbwert, keine CSS-Funktion — deshalb die
// Mischung von Hand.
function darken(hex, factor = 0.55) {
  const h = hex.replace("#", "");
  const mix = (c) => Math.round(parseInt(c, 16) * factor);
  return `rgb(${mix(h.slice(0, 2))},${mix(h.slice(2, 4))},${mix(h.slice(4, 6))})`;
}

// ── Bezier-Helfer (Datenkoordinaten: x = Dezimalstunde, y = SoC-%) ─────────

function cubicAt(p0, p1, p2, p3, t) {
  const u = 1 - t;
  return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3;
}

function sampleCubic(seg, samples = CURVE_SAMPLES) {
  const out = [];
  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    out.push([cubicAt(seg.x0, seg.x1, seg.x2, seg.x3, t), cubicAt(seg.y0, seg.y1, seg.y2, seg.y3, t)]);
  }
  return out;
}

// Kurvenparameter t zu einem gesuchten SoC-Wert, per Binaersuche — dieselbe
// 60-Schritt-Suche wie im SVG (tForY), nur direkt auf dem Prozentwert statt
// auf einer Pixel-Y-Koordinate. "ascending" sagt, ob y mit t steigt (Ladeast)
// oder faellt (Entladeast); danach richtet sich die Richtung der Suche.
function tForSoc(seg, soc, ascending) {
  let lo = 0;
  let hi = 1;
  for (let i = 0; i < 60; i++) {
    const m = (lo + hi) / 2;
    const y = cubicAt(seg.y0, seg.y1, seg.y2, seg.y3, m);
    if (ascending ? y < soc : y > soc) lo = m;
    else hi = m;
  }
  return (lo + hi) / 2;
}

// Punkt (Stunde, SoC) auf einem Ast fuer eine gegebene Schwelle.
function pointForSoc(seg, soc, ascending) {
  const t = tForSoc(seg, soc, ascending);
  return { x: cubicAt(seg.x0, seg.x1, seg.x2, seg.x3, t), y: cubicAt(seg.y0, seg.y1, seg.y2, seg.y3, t) };
}

// Linear interpolierter y-Wert einer [x,y]-Punktreihe an einer gesuchten
// Stunde, fuer den "jetzt"-Wert von Schematik und Sonne in der Legende
// (25.09.2026, Nutzer-Vorgabe: beide sollen wie "Batteriestand" einen
// Live-Stand zeigen). Ausserhalb der Reihe wird auf den jeweiligen Randwert
// geklemmt statt zu extrapolieren.
function valueAtHour(points, hour) {
  if (!points.length) return null;
  if (hour <= points[0][0]) return points[0][1];
  const last = points[points.length - 1];
  if (hour >= last[0]) return last[1];
  for (let i = 0; i < points.length - 1; i++) {
    const [x0, y0] = points[i];
    const [x1, y1] = points[i + 1];
    if (hour >= x0 && hour <= x1) {
      const t = x1 === x0 ? 0 : (hour - x0) / (x1 - x0);
      return y0 + (y1 - y0) * t;
    }
  }
  return last[1];
}

// Schematischer Batterie-Tagesgang, zerlegt in Lade- und Entladeast.
// Kontrollpunkt-Verhaeltnisse (0.35/0.70 morgens, 0.30/0.68 nachmittags) sind
// unveraendert aus dem SVG-Stand uebernommen.
function buildSchematic(riseH, noonH, setH) {
  const morningWidth = noonH - riseH;
  const ascend = {
    x0: riseH,
    x1: riseH + morningWidth * 0.35,
    x2: riseH + morningWidth * 0.7,
    x3: noonH,
    y0: BATTERY_FLOOR,
    y1: BATTERY_FLOOR,
    y2: BATTERY_FULL,
    y3: BATTERY_FULL,
  };
  const plateauEnd = noonH + PLATEAU_HOURS;
  const afternoonWidth = setH - plateauEnd;
  const descend = {
    x0: plateauEnd,
    x1: plateauEnd + afternoonWidth * 0.3,
    x2: plateauEnd + afternoonWidth * 0.68,
    x3: setH,
    y0: BATTERY_FULL,
    y1: BATTERY_FULL,
    y2: BATTERY_FLOOR,
    y3: BATTERY_FLOOR,
  };
  const points = [
    [X_MIN, BATTERY_FLOOR],
    [riseH, BATTERY_FLOOR],
    ...sampleCubic(ascend),
    [plateauEnd, BATTERY_FULL],
    ...sampleCubic(descend),
    [X_MAX, BATTERY_FLOOR],
  ];
  return { points, ascend, descend };
}

// Sonnenkurve aus den echten Zeiten von sun.sun, asymmetrisch: die beiden
// Haelften vor/nach dem Sonnenhoechststand sind unterschiedlich breit. Der
// zweite Ast ist die Spiegelung des ersten am Scheitel (im SVG das "S"-
// Kommando des Pfads, hier ausgeschrieben).
function buildSunCurve(riseH, noonH, setH) {
  const half1 = noonH - riseH;
  const half2 = setH - noonH;
  const up = {
    x0: riseH,
    x1: riseH + half1 * 0.55,
    x2: noonH - half1 * 0.35,
    x3: noonH,
    y0: 0,
    y1: 0,
    y2: 100,
    y3: 100,
  };
  const down = {
    x0: noonH,
    x1: noonH + half1 * 0.35,
    x2: noonH + half2 * 0.55,
    x3: setH,
    y0: 100,
    y1: 100,
    y2: 0,
    y3: 0,
  };
  return [...sampleCubic(up), ...sampleCubic(down)];
}

// Realer SoC-Verlauf des laufenden Tages, auf 10-Minuten-Raster gemittelt
// (identische Aufloesung wie der bisherige WebSocket-Pfad im SVG, der die
// Zeitstempel mit Math.round(h*6)/6 einrastete). Die Quelle ist jetzt
// hass.callApi("history/period/...") wie beim Verlauf-Chart, statt eines
// eigenen history/history_during_period-WebSocket-Calls mit
// input_text-Fallback: ein Datenweg weniger, gleiches Ergebnis.
function socTrace(history, windowStart) {
  const buckets = new Map();
  for (const point of history) {
    const v = parseFloat(point.state);
    if (Number.isNaN(v)) continue;
    const t = new Date(point.last_changed);
    // Fensterstunde aus dem ABSTAND zum Fensterbeginn, nicht aus der Uhrzeit
    // des Zeitstempels: nur so landen Messpunkte nach Mitternacht auf 24..27
    // statt zurueck am linken Rand.
    const h = X_START_HOUR + (t - windowStart) / 3600000;
    if (h < X_MIN || h > X_MAX) continue;
    const bucket = Math.round(h * 6) / 6;
    buckets.set(bucket, v);
  }
  return [...buckets.entries()].sort((a, b) => a[0] - b[0]).map(([h, v]) => [h, v]);
}

// 17.10.2026, Lab-Replay: Profil des abgespielten Tages (sensor.lab_sim_profile
// gibt es nur im Lab; eine Zeile je 10-min-Block, Spalte 4 SoC, 9 Minute des
// Tages, 22 Sonnenhoehe, s. scripts/build_sim_day.py). null = kein Replay, dann
// gilt alles wie bisher (echte Sonne, History, Uhrzeit).
function simProfile(hass) {
  if (hass?.states?.["input_boolean.simulation_mode"]?.state !== "on") return null;
  const steps = hass.states["sensor.lab_sim_profile"]?.attributes?.steps;
  const step = parseInt(hass.states["input_number.sim_step"]?.state, 10);
  if (!Array.isArray(steps) || !steps.length || Number.isNaN(step)) return null;
  const running = hass.states["input_boolean.lab_demo_running"]?.state === "on";
  const frozen = parseInt(hass.states["input_number.lab_sim_minute"]?.state, 10);
  const minute = !running && frozen >= step * 10 && frozen <= step * 10 + 9 ? frozen : step * 10;
  return { steps, step, minute };
}

// Sonnenzeiten des abgespielten Tages aus der aufgezeichneten Sonnenhoehe:
// Auf-/Untergang = Nulldurchgang (linear zwischen zwei Bloecken), Mittag =
// hoechster Stand. Fehlt ein Wert, greifen die Fallback-Zeiten.
function simSunTimes(steps) {
  let rise = null;
  let set = null;
  let noon = null;
  let maxEl = -Infinity;
  for (let k = 0; k < steps.length; k++) {
    const r = steps[k];
    const h = r[9] / 60;
    if (r[22] > maxEl) {
      maxEl = r[22];
      noon = h;
    }
    if (k === 0) continue;
    const a = steps[k - 1][22];
    const b2 = r[22];
    const h0 = steps[k - 1][9] / 60;
    if (rise === null && a <= 0 && b2 > 0) rise = h0 + ((h - h0) * -a) / (b2 - a);
    if (a > 0 && b2 <= 0) set = h0 + ((h - h0) * a) / (a - b2);
  }
  return { rise, noon, set };
}

class BitgridRegelschwellenChart extends HTMLElement {
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
    // standalone: false (Default) laesst Rahmen, Hintergrund und Radius weg.
    // Grund: diese Karte sitzt in bitgrid_dashboard_v3.yaml als erste Karte in
    // einem vertical-stack, der per card_mod bereits EINEN gemeinsamen Rahmen
    // um Chart + alle Detailgruppen zieht (Nutzer-Vorgabe 31.08.2026: "soll
    // auch alles in einer Karte stecken"). Ein eigener Rahmen ergaebe dort
    // sichtbar Rahmen-im-Rahmen. Wer die Karte einzeln einsetzt, setzt
    // standalone: true und bekommt die Kartenhuelle des Verlauf-Charts.
    const standalone = this._config.standalone === true;
    root.innerHTML = `
      <style>
        :host { display: block; }
        /* Kartenhuelle bewusst als eigener <div> statt <ha-card>: ha-card
           bringt ein eigenes internes :host{border-radius}-Regelwerk mit, das
           von aussen nicht zu ueberschreiben ist (volle Begruendung im
           Kommentar in www/bitgrid_verlauf_chart.js). */
        .bgai-card {
          box-sizing: border-box;
          /* Bezug fuer die cqw-Einheiten der Legende (17.10.2026). */
          container-type: inline-size;
          padding: ${standalone ? "12px" : "6px 6px 2px 6px"};
          ${
            standalone
              ? `background: var(--ha-card-background);
          border-radius: 20px !important;
          border: var(--bgai-card-border-width-v3) solid var(--bgai-card-border-v3);
          box-shadow: var(--bgai-card-shadow-v3);
          overflow: hidden !important;`
              : "background: transparent;"
          }
        }
        #chart { width: 100%; }
        /* Legende, Divider-Fade und Halo 1:1 aus bitgrid_verlauf_chart.js —
           das ist der Stil, der hier angeglichen werden sollte. Eigene HTML-
           Legende statt ApexCharts' eingebauter: die rendert in einem
           SVG-foreignObject und bleibt dort trotz Flexbox einspaltig. */
        .bgai-legend {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          align-items: center;
          /* 17.10.2026: Abstand und Schrift (s. .bgai-legend-item) schrumpfen mit
             der Kartenbreite, damit die Legende mit den achsengleichen Namen
             (Sonnenstand / Batteriestand / Batteriestand (Schema)) auch auf dem
             Tablet (~1024 px Fenster, 522 px Karte, Bedarf 589 px) einzeilig
             bleibt. Bei 669 px Karte (1280er Fenster) greifen die Deckel 16/16 px,
             also unveraendert. Umbruch bleibt als Notloesung erlaubt. */
          column-gap: clamp(8px, 2.4cqw, 16px);
          row-gap: 4px;
          padding-top: 12px;
          /* 8px -> 18px (17.10.2026, Nutzer-Wunsch "ueber der Legende und dem
             Strich auch ein Space"): Luft zwischen Achsenbeschriftung und Trenner. */
          margin-top: 18px;
          background-image: linear-gradient(to right, transparent, var(--divider-color) 15%, var(--divider-color) 85%, transparent);
          background-repeat: no-repeat;
          background-size: 100% 2px;
          background-position: top;
        }
        .bgai-legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: clamp(12px, 2.6cqw, 16px);
          white-space: nowrap;
          font-family: Roboto, sans-serif;
          font-weight: 400;
          text-shadow: 0 0 4px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.9);
        }
        .bgai-legend-dot {
          --mdc-icon-size: 20px;
          width: 20px;
          height: 20px;
          flex: 0 0 auto;
          filter: drop-shadow(0 0 3px rgba(0,0,0,.9)) drop-shadow(0 0 3px rgba(0,0,0,.9));
        }
        .apexcharts-text,
        .apexcharts-xaxis-annotation-label,
        .apexcharts-yaxis-annotation-label,
        .apexcharts-point-annotation-label {
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
    // Lab-Replay: je Sim-Schritt neu zeichnen (Daten aus dem Profil, kein
    // History-Abruf), statt im 5-Minuten-Takt der echten Uhr.
    const sim = simProfile(this._hass);
    if (sim) {
      const key = `${sim.step}|${sim.minute}`;
      if (this._apexChart && key === this._lastSimKey) return;
      this._lastSimKey = key;
      await this._fetchAndRender();
      return;
    }
    if (this._lastSimKey) {
      this._lastSimKey = null;
      this._lastFetch = 0;
    }
    const now = Date.now();
    // 5-Minuten-Cache wie beim Verlauf-Chart: die History-Abfrage ist teurer
    // als ein State-Update, der Tagesverlauf braucht keine Sekundenaufloesung.
    // Schwellen-Aenderungen (input_number) wirken beim naechsten Zyklus.
    // 26.09.2026, gleicher Bug wie bitgrid_verlauf_chart.js: disconnectedCallback()
    // zerstoert this._apexChart beim View-Wechsel, ein Reconnect innerhalb der
    // Cache-Frist bemerkte das bisher nicht und liess den Container leer.
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

    // ── Schwellen + Saison-Gating ───────────────────────────────────────
    const eco = num(hass, ENTITY_ECO, 60);
    const std = num(hass, ENTITY_STD, 75);
    const sup = num(hass, ENTITY_SUPER, 90);
    const stop = num(hass, ENTITY_STOP, 50);
    // Eigene Runterschalt-Schwellen seit 23.08.2026 (vorher kollabierte Super
    // ueber den pauschalen Nachmittags-Cap, ohne eigene Runterschalt-Marke).
    const supOff = num(hass, ENTITY_SUPER_OFF, 95);
    const stdOff = num(hass, ENTITY_STD_OFF, 83);
    // Saisonale Automatik (packages/mvp_auto.yaml): in manchen Monaten werden
    // Standard/Super gar nicht erreicht. Dann auch keine Marker/Linien dafuer
    // zeichnen, sonst zeigt der Chart einen Schwellwert, der de facto nie
    // gilt (Nutzer-Feedback 27.08.2026: "wenn Super nicht aktiviert ist,
    // sollte auch kein Super-Wert angezeigt werden").
    const season = hass.states[ENTITY_SEASON]?.state || "Voll (Eco/Standard/Super)";
    const stdReachable = season !== "Nur Eco";
    const supReachable = season === "Voll (Eco/Standard/Super)";

    // ── Sonnenzeiten (sun.sun liefert UTC; liegt ein next_* mehr als 20h in
    // der Zukunft, gehoert es zu morgen und wird um 24h zurueckgesetzt) ──
    const sunAttrs = hass.states[ENTITY_SUN]?.attributes || {};
    const nowMs = Date.now();
    const sunMs = (iso) => {
      if (!iso) return null;
      let ms = new Date(iso).getTime();
      if (ms - nowMs > 20 * 3600000) ms -= 86400000;
      return ms;
    };
    const hourOf = (ms) => {
      if (!ms) return null;
      const d = new Date(ms);
      return d.getHours() + d.getMinutes() / 60;
    };
    // axisPos() ist hier in der Praxis die Identitaet (Sonnenauf-/untergang
    // liegen in unseren Breiten immer nach 3 Uhr), steht aber bewusst da:
    // ohne sie waere die Achsenlage der Sonnenkurve stillschweigend davon
    // abhaengig, dass X_START_HOUR klein genug bleibt.
    const sim = simProfile(hass);
    const simSun = sim ? simSunTimes(sim.steps) : null;
    const riseH = axisPos((simSun ? simSun.rise : hourOf(sunMs(sunAttrs.next_rising))) ?? FALLBACK_RISE_H);
    const noonH = axisPos((simSun ? simSun.noon : hourOf(sunMs(sunAttrs.next_noon))) ?? FALLBACK_NOON_H);
    const setH = axisPos((simSun ? simSun.set : hourOf(sunMs(sunAttrs.next_setting))) ?? FALLBACK_SET_H);

    const schematic = buildSchematic(riseH, noonH, setH);
    const sunPoints = buildSunCurve(riseH, noonH, setH);

    // ── Echter SoC-Verlauf heute ────────────────────────────────────────
    const now = new Date();
    // Ab Fensterbeginn, der bei X_START_HOUR = 0 mit Mitternacht zusammen-
    // faellt. Bewusst ueber windowStartFor() statt hart auf 00:00: sonst
    // haengt die Korrektheit der History-Abfrage still am Wert einer
    // Konstante, die heute schon dreimal geaendert wurde.
    const windowStart = windowStartFor(now);
    let trace = [];
    let traceStatus = "ok";
    if (sim) {
      // Replay: SoC der abgespielten Bloecke bis zum aktuellen.
      trace = sim.steps.slice(0, sim.step + 1).map((r) => [axisPos(r[9] / 60), r[4]]);
    } else try {
      const raw = await hass.callApi(
        "GET",
        `history/period/${windowStart.toISOString()}?filter_entity_id=${ENTITY_SOC}&end_time=${now.toISOString()}&minimal_response&significant_changes_only=0`
      );
      const hist = Array.isArray(raw) && raw.length ? raw[0] : [];
      trace = socTrace(hist, windowStart);
    } catch (e) {
      traceStatus = "error";
    }
    const hasTrace = trace.length > 3;

    // "jetzt" als Fensterstunde, vorgezogen (frueher erst bei den Annotationen
    // berechnet): die Legende braucht denselben Wert schon vorher fuer die
    // Live-Staende von Schematik und Sonne.
    const nowH = sim ? axisPos(sim.minute / 60) : axisPos(now.getHours() + now.getMinutes() / 60);
    const nowVisible = nowH >= X_MIN && nowH <= X_MAX;

    // ── Serien ──────────────────────────────────────────────────────────
    // Zeichenreihenfolge = Array-Reihenfolge, spaetere Serien liegen oben:
    // Sonne unten (nur Kontext), darueber die Schematik, ganz oben der echte
    // Verlauf. Die Legende unten nutzt bewusst eine ANDERE Reihenfolge
    // (Schematik / Verlauf heute / Sonne, wie im bisherigen SVG-Kopf) und ist
    // deshalb selbst gebaut, nicht aus dieser Liste abgeleitet.
    const seriesDefs = [
      {
        name: "Sonnenstand",
        icon: "mdi:white-balance-sunny",
        // 25.09.2026: PV-Rollenfarbe statt eines eigenen Sonnengelbs, gleiche
        // Begruendung wie bei der linken Achse (s. COLOR_PV oben).
        color: COLOR_PV,
        data: sunPoints,
        opacity: 0.12,
        dash: 5,
        width: 1.5,
        curve: "straight",
        unit: "",
        // Die Sonnenkurve ist eine normierte Tagesbogen-Schematik, kein
        // Messwert in Prozent — im Tooltip deshalb ohne Zahlenwert.
        schematicOnly: true,
      },
      {
        name: "Batteriestand (Schema)",
        // Icon: Miner-Rolle aus bitgrid_verlauf_chart.js (dort "Miner-
        // Verbrauch", mdi:pickaxe), weil die Kurve den Umschalt-Fahrplan der
        // Miner zeigt. Farbe seit 26.09.2026 neutrales Grau statt Miner-
        // Orange, s. COLOR_SCHEMATIC.
        icon: "mdi:pickaxe",
        color: COLOR_SCHEMATIC,
        data: schematic.points,
        // Liegt ein echter Verlauf vor, tritt die Schematik in den
        // Hintergrund und dient nur noch als Referenz (Regel aus dem
        // SVG-Stand: Fuellung 0.12 -> 0.04, Linie 2px -> 1px).
        opacity: hasTrace ? 0.04 : 0.12,
        // 26.09.2026, Nutzer-Wunsch: gestrichelt, aber anders als die Sonne
        // (dash 5). Doppelt so lange Striche (10) sind auf einen Blick von der
        // Sonnenlinie zu unterscheiden, auch bei gleicher Linienstaerke.
        dash: 10,
        width: hasTrace ? 1 : 2,
        curve: "straight",
        unit: "%",
        schematicOnly: true,
      },
      {
        name: "Batteriestand",
        // 25.09.2026: gleiches Icon wie "Batteriestand" im Verlauf-Chart
        // (mdi:battery statt battery-charging-medium) — einheitliches
        // Icon-Set, dieselbe Entitaet sensor.battery_soc_pct.
        icon: "mdi:battery",
        // 25.09.2026, Nutzer-Korrektur: Batteriegruen statt Weiss, dieselbe
        // Farbe wie die rechte Achse (COLOR_SOC) — beide zeigen dieselbe
        // Entitaet sensor.battery_soc_pct.
        color: COLOR_SOC,
        data: trace,
        opacity: 0,
        dash: 0,
        width: 2.5,
        curve: "smooth",
        unit: "%",
        schematicOnly: false,
      },
    ];

    // ── Legende ────────────────────────────────────────────────────────
    // Reihenfolge 27.09.2026 auf Nutzer-Wunsch getauscht (Schematik <-> Sonne),
    // vorher die des abgeloesten SVG-Kopfs. "Batteriestand" bleibt in der
    // Mitte: das ist der einzige echte Messwert, die beiden Referenzkurven
    // flankieren ihn.
    const soc = parseFloat(hass.states[ENTITY_SOC]?.state);
    const legendOrder = ["Sonnenstand", "Batteriestand", "Batteriestand (Schema)"];
    this._legendEl.innerHTML = "";
    legendOrder.forEach((name) => {
      const def = seriesDefs.find((s) => s.name === name);
      if (!def) return;
      const item = document.createElement("span");
      item.className = "bgai-legend-item";
      const dot = document.createElement("ha-icon");
      dot.className = "bgai-legend-dot";
      // 17.10.2026, Nutzer-Wunsch: das Batteriestand-Icon folgt dem Ladestand
      // wie in "Verlauf (heute)" und im Energiefluss (batteryIconForSoc oben).
      dot.setAttribute("icon", def.name === "Batteriestand" ? batteryIconForSoc(hass.states[ENTITY_SOC]) : def.icon);
      dot.style.color = def.color;
      const label = document.createElement("span");
      label.style.color = def.color;
      // 25.09.2026, Nutzer-Vorgabe: alle drei Serien zeigen einen "jetzt"-
      // Stand wie beim Verlauf-Chart, nicht nur der echte Verlauf. Schematik
      // und Sonne haben keinen eigenen Messwert (reine Referenzkurven), ihr
      // Stand ist deshalb der interpolierte Kurvenwert an der aktuellen
      // Fensterstunde (valueAtHour) — derselbe Wert, den die Kurve an dieser
      // Stelle im Chart zeichnet, keine zweite, abweichende Quelle.
      let valueText = "–";
      if (def.name === "Batteriestand" && !Number.isNaN(soc)) {
        valueText = `${Math.round(soc)} %`;
      } else if (def.name === "Batteriestand (Schema)" && nowVisible) {
        valueText = `${Math.round(valueAtHour(schematic.points, nowH))} %`;
      } else if (def.name === "Sonnenstand" && nowVisible) {
        valueText = `${Math.round(valueAtHour(sunPoints, nowH))} %`;
      }
      // 27.09.2026, Nutzer-Wunsch: nur der Zahlenwert in Weiss, der Name
      // behaelt seine Serienfarbe. Zwei Spans statt eines: eine Teilfarbe
      // innerhalb eines textContent gibt es nicht. Literales #FFFFFF statt
      // var(--primary-text-color) (#F5F8FC), weil ausdruecklich Weiss
      // gefordert war und die Chart-Farben in dieser Datei ohnehin alle
      // literal stehen.
      label.textContent = `${def.name}: `;
      const value = document.createElement("span");
      value.style.color = "#FFFFFF";
      value.textContent = valueText;
      item.appendChild(dot);
      item.appendChild(label);
      item.appendChild(value);
      this._legendEl.appendChild(item);
    });

    // Lüftung-Nachlauf: eigenes Legenden-Item, aber nur waehrend der 30-min-
    // Cooldown-Phase nach dem letzten Miner-Stopp (packages/mvp_auto.yaml,
    // "MVP: Lüftung Watchdog"). sensor.lueftung_status_display liefert dort
    // bereits "Aktiv" (Miner laeuft, Lüftung dauerhaft an, kein Countdown),
    // "M:SS" (Nachlauf laeuft) oder "Aus" — nur der M:SS-Fall ist hier
    // gemeint ("wie lange sie noch nachlaeuft"), die anderen beiden werden
    // laut Nutzer-Vorgabe ausgeblendet statt mit "Aktiv"/"Aus" angezeigt.
    const lueftungStatus = hass.states[ENTITY_LUEFTUNG_STATUS]?.state || "";
    if (/^\d+:\d{2}$/.test(lueftungStatus)) {
      const item = document.createElement("span");
      item.className = "bgai-legend-item";
      const dot = document.createElement("ha-icon");
      dot.className = "bgai-legend-dot";
      dot.setAttribute("icon", "mdi:fan");
      // var() statt Literal ist hier unproblematisch: dieses Element geht
      // nie durch ApexCharts, es ist gewoehnliches Shadow-DOM-HTML.
      dot.style.color = "var(--secondary-text-color)";
      const label = document.createElement("span");
      label.style.color = "var(--secondary-text-color)";
      label.textContent = `Lüftung Nachlauf: ${lueftungStatus}`;
      item.appendChild(dot);
      item.appendChild(label);
      this._legendEl.appendChild(item);
    }

    // ── Annotationen: Schwellenlinien, Marker, "jetzt" ──────────────────
    const yLines = [];
    const points = [];

    // Hausreserve: kraeftiger als die Modus-Schwellen, mit Label links auf der
    // Linie (wie im SVG "Haus 68%"). yAxisIndex 2 = die rechte Batteriestand-
    // Achse (s. yaxis-Array unten): seit es zwei Achsen gibt, muss jede
    // SoC-Annotation ihre Achse explizit nennen, sonst bindet ApexCharts
    // still an Achse 0 (Sonnenstand). Beide Achsen haben zwar dieselbe
    // 0-100-Skala, also keinen sichtbaren Unterschied, aber die explizite
    // Zuordnung ist die korrekte statt eine zufaellig passende.
    yLines.push({
      y: stop,
      yAxisIndex: 2,
      borderColor: withAlpha(COLOR_RESERVE, 0.75),
      strokeDashArray: 5,
      label: {
        text: `Haus ${stop}%`,
        position: "left",
        offsetX: 60,
        offsetY: -2,
        borderColor: "transparent",
        style: {
          color: COLOR_RESERVE,
          background: "transparent",
          fontSize: "15px",
          fontFamily: "Roboto, sans-serif",
        },
      },
    });

    const thinLine = (y, color) => ({
      y,
      yAxisIndex: 2,
      borderColor: withAlpha(color, 0.35),
      strokeDashArray: 4,
      label: { text: "", borderColor: "transparent", style: { background: "transparent" } },
    });
    yLines.push(thinLine(eco, COLOR_ECO));
    if (stdReachable) yLines.push(thinLine(std, COLOR_STD));
    if (supReachable) yLines.push(thinLine(sup, COLOR_SUPER));

    // Marker auf der Kurve. ApexCharts' pointAnnotation kennt keinen Connector
    // zwischen Label und Punkt, das Label kann also nicht wie im SVG am Ende
    // einer Fuehrungslinie sitzen.
    //
    // 26.09.2026, Nutzer-Vorgabe (loest die Ueber/Unter-Platzierung vom
    // 25.09. ab, dort ueberlagerten sich Label, Kurve und Nachbar-Labels):
    // Hochschalt-Punkte (Ladeast, linke Flanke) bekommen ihr Label LINKS vom
    // Punkt, Runterschalt-Punkte (Entladeast, rechte Flanke) RECHTS daneben.
    // Beide Labels zeigen damit von der Kurvenmitte weg nach aussen, ins
    // Freie. Offsets 1:1 vom Live-Punkt unten ("23%", rechts daneben,
    // textAnchor start / offsetX 12 / offsetY 6), der bereits sauber
    // mittig auf Punkthoehe sitzt; links gespiegelt (end / -12).
    const mark = (pt, color, text, opts = {}) => ({
      x: pt.x,
      y: pt.y,
      yAxisIndex: 2,
      marker: {
        size: opts.size || 5,
        fillColor: opts.dotColor || color,
        strokeColor: "rgba(20,10,50,0.9)",
        strokeWidth: 2,
      },
      label: {
        text,
        textAnchor: opts.direction === "down" ? "start" : "end",
        offsetX: opts.direction === "down" ? 12 : -12,
        offsetY: 6,
        borderColor: "transparent",
        style: {
          color,
          background: "transparent",
          fontSize: "15px",
          fontWeight: 600,
          fontFamily: "Roboto, sans-serif",
        },
      },
    });

    // Hochschalt-Punkte auf dem Ladeast, Labels links vom Punkt ...
    // 27.09.2026, Nutzer-Wunsch: Pfeil nach oben im Namen, analog zu den
    // Runterschalt-Markern darunter (die tragen seit jeher ein "↓").
    // Auch am Super-Marker, obwohl der in der laufenden Saison ausgeblendet
    // ist: sonst haette er als einziger Hochschaltpunkt keinen Pfeil,
    // sobald die Saison ihn wieder freigibt.
    points.push(mark(pointForSoc(schematic.ascend, eco, true), COLOR_ECO, `Eco↑${eco}%`, { direction: "up" }));
    if (stdReachable) {
      points.push(mark(pointForSoc(schematic.ascend, std, true), COLOR_STD, `Std↑${std}%`, { direction: "up" }));
    }
    if (supReachable) {
      points.push(mark(pointForSoc(schematic.ascend, sup, true), COLOR_SUPER, `Super↑${sup}%`, { direction: "up" }));
    }
    // ... Runterschalt-Punkte auf dem Entladeast, Labels rechts vom Punkt. SoC-
    // getrieben, nicht zeit- oder sonnenstandgetrieben (der frueher
    // pauschale "Eco-Cap ab Mittag" wurde am 23.08.2026 entfernt, s.
    // docs/architecture/09_design_decisions/092_soc_saison_schwellen_vorschlag_de.md).
    if (supReachable) {
      points.push(
        mark(pointForSoc(schematic.descend, supOff, false), COLOR_SUPER, `Super↓${supOff}%`, {
          dotColor: darken(COLOR_SUPER),
          size: 4,
          direction: "down",
        })
      );
    }
    if (stdReachable) {
      points.push(
        mark(pointForSoc(schematic.descend, stdOff, false), COLOR_STD, `Std↓${stdOff}%`, {
          dotColor: darken(COLOR_STD),
          size: 4,
          direction: "down",
        })
      );
    }

    // nowH/nowVisible sind bereits weiter oben berechnet (Legende braucht sie
    // zuerst), gelten unveraendert auch hier fuer die "jetzt"-Linie.
    const xLines = [];
    if (nowVisible) {
      // Bewusst OHNE "jetzt"-Textlabel, anders als beim Verlauf-Chart: dort
      // markiert die Linie allein den aktuellen Zeitpunkt, hier sitzt auf
      // derselben Linie zusaetzlich der Live-Punkt mit seinem Prozentwert.
      // Beide Labels ueberdeckten sich im Rendertest, und das Wort "jetzt"
      // sagt neben einem beschrifteten Live-Punkt nichts Zusaetzliches. Der
      // abgeloeste SVG-Stand hatte hier ebenfalls nur Linie und Punkt.
      xLines.push({
        x: nowH,
        borderColor: "rgba(255,255,255,0.5)",
        strokeDashArray: 4,
        label: { text: "", borderColor: "transparent", style: { background: "transparent" } },
      });
      if (!Number.isNaN(soc)) {
        points.push({
          x: nowH,
          y: Math.min(100, Math.max(0, soc)),
          yAxisIndex: 2,
          marker: { size: 5, fillColor: "rgba(255,255,255,0.9)", strokeColor: "rgba(100,200,255,0.9)", strokeWidth: 2 },
          label: {
            text: `${Math.round(soc)}%`,
            // 26.09.2026, Nutzer-Wunsch: mittig UEBER dem Punkt statt rechts
            // daneben, rechts kollidierte es mit dem Runterschalt-Label
            // ("81%Std↓83%"). Der fruehere Grund fuer "rechts statt darueber"
            // (eigenes Textlabel der "jetzt"-Linie an derselben Stelle) ist
            // weggefallen, die Linie hat kein Label mehr (s. xLines oben).
            // offsetY -2: bei offsetY 6 sass die Grundlinie live nur ~8px
            // ueber der Punktmitte, zu knapp fuer diesen groesseren Marker.
            textAnchor: "middle",
            offsetX: 0,
            offsetY: -2,
            borderColor: "transparent",
            style: {
              color: "#FFFFFF",
              background: "transparent",
              fontSize: "15px",
              fontWeight: 600,
              fontFamily: "Roboto, sans-serif",
            },
          },
        });
      }
    }

    // Diagnose-Einblendung nur auf Wunsch (config.debug), Gegenstueck zum
    // frueher fest sichtbaren "fetching/Npts" des SVG-Stands.
    if (this._config.debug === true) {
      xLines.push({
        x: X_MAX,
        borderColor: "transparent",
        label: {
          text: `${traceStatus}/${trace.length}pts`,
          orientation: "horizontal",
          offsetY: -6,
          offsetX: -10,
          textAnchor: "end",
          borderColor: "transparent",
          style: {
            color: "rgba(255,255,255,0.35)",
            background: "transparent",
            fontSize: "11px",
            fontFamily: "Roboto, sans-serif",
          },
        },
      });
    }

    // ── ApexCharts-Options, Stil-Bloecke 1:1 aus bitgrid_verlauf_chart.js ──
    const options = {
      chart: {
        type: "area",
        height: this._config.height || 280,
        toolbar: { show: false },
        zoom: { enabled: false },
        background: "transparent",
        foreColor: "#FFFFFF",
        // Chart-weiter Schatten unter allen Serien-Linien, wie beim Verlauf.
        dropShadow: { enabled: true, top: 0, left: 0, blur: 3, opacity: 0.5 },
        animations: { enabled: false },
      },
      series: seriesDefs.map((s) => ({ name: s.name, data: s.data })),
      colors: seriesDefs.map((s) => s.color),
      stroke: {
        // Pro Serie, nicht global: die beiden schematischen Kurven sind bereits
        // fein abgetastet und brauchen "straight" (kein Spline-Ueberschwingen
        // ueber 100% an den Plateau-Knicken), der echte 10-Minuten-Verlauf
        // profitiert dagegen von "smooth" wie im Verlauf-Chart.
        curve: seriesDefs.map((s) => s.curve),
        width: seriesDefs.map((s) => s.width),
        dashArray: seriesDefs.map((s) => s.dash),
      },
      fill: { type: "solid", opacity: seriesDefs.map((s) => s.opacity) },
      markers: { size: 0 },
      xaxis: {
        type: "numeric",
        min: X_MIN,
        max: X_MAX,
        tickAmount: X_TICK_AMOUNT,
        title: {
          text: "Uhrzeit",
          offsetY: -4,
          style: { color: "rgba(255,255,255,0.55)", fontSize: "15px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
        },
        labels: {
          style: { colors: "#FFFFFF", fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
          rotate: 0,
          offsetY: 4,
          // 3h-Schritte wie beim Verlauf-Chart: 0/3/6/9/12/15/18/21. Die
          // uebrigen Stunden behalten ihren Tick-Strich, nur das Label
          // entfaellt — das ist der Grund, warum die Achse ueberhaupt mit
          // tickAmount 24 statt 8 laeuft.
          //
          // Teilbarkeit wird auf der FENSTERSTUNDE geprueft, die Anzeige dann
          // per Modulo auf die echte Uhrzeit zurueckgerechnet. Der rechte Rand
          // (X_MAX) bleibt seit 26.09.2026 ohne Label (Nutzer-Wunsch "letzte 0
          // weg"): dort stand per Modulo ein zweites "0" neben dem linken Rand,
          // das den Tag optisch zweimal beginnen liess. Der Tick-Strich selbst
          // bleibt, die Achse endet weiterhin sichtbar bei Mitternacht.
          formatter: (value) => {
            const h = Math.round(parseFloat(value));
            if (!Number.isFinite(h) || h === X_MAX) return "";
            return h % 3 === 0 ? String(h % 24) : "";
          },
        },
        axisTicks: { show: true },
        tooltip: { enabled: false },
      },
      // 25.09.2026, Nutzer-Vorgabe: zwei Achsen statt einer, Stil 1:1 aus dem
      // Verlauf-Chart uebernommen (dort primaryPowerName/seriesName-Muster).
      // Reihenfolge MUSS positionsgleich zu seriesDefs sein (ApexCharts
      // bindet yaxis[i] an series[i], s. ausfuehrliche Begruendung dazu in
      // bitgrid_verlauf_chart.js): [0] Sonne, [1] Schematik, [2] Verlauf
      // heute. Schematik teilt sich per seriesName die rechte Achse mit dem
      // echten Verlauf (beide dieselbe Groesse: SoC in %), zeigt aber keine
      // eigene, doppelte Achsenbeschriftung (show: false).
      yaxis: [
        {
          // Links: Sonnenstand, PV-Rollenfarbe (COLOR_PV).
          seriesName: "Sonnenstand",
          opposite: false,
          min: 0,
          max: 100,
          tickAmount: 5,
          title: {
            text: "Sonnenstand",
            style: { color: COLOR_PV, fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
          },
          labels: {
            style: { colors: COLOR_PV, fontSize: "17px", fontFamily: "Roboto, sans-serif" },
            formatter: (value) => `${Math.round(value)}`,
          },
          decimalsInFloat: 0,
        },
        {
          seriesName: "Batteriestand",
          show: false,
          opposite: true,
          min: 0,
          max: 100,
        },
        {
          // Rechts: Batteriestand, dieselbe Farbe wie im Verlauf-Chart
          // (COLOR_SOC), weil dort dieselbe Entitaet sensor.battery_soc_pct
          // dargestellt wird.
          seriesName: "Batteriestand",
          opposite: true,
          min: 0,
          max: 100,
          tickAmount: 5,
          title: {
            text: "Batteriestand (%)",
            // 18.10.2026: rechte Achsenbeschriftung naeher an den Rand, damit der Graph
            // samt Achsen mittig in der Karte sitzt (links 10 px, rechts war 31 px).
            offsetX: 20,
            style: { color: COLOR_SOC, fontSize: "17px", fontFamily: "Roboto, sans-serif", fontWeight: 400 },
          },
          labels: {
            style: { colors: COLOR_SOC, fontSize: "17px", fontFamily: "Roboto, sans-serif" },
            formatter: (value) => `${Math.round(value)}`,
          },
          decimalsInFloat: 0,
        },
      ],
      grid: {
        borderColor: "rgba(255,255,255,0.07)",
        strokeDashArray: 4,
        padding: { left: 15, right: 15 },
      },
      legend: { show: false },
      annotations: { yaxis: yLines, xaxis: xLines, points },
      tooltip: {
        theme: "dark",
        // shared: false, weil die drei Serien hier unterschiedliche x-Raster
        // haben (zwei abgetastete Kurven + ein 10-Minuten-Messraster). Ein
        // geteilter Tooltip wuerde ueber den dataPointIndex Werte
        // zusammenfuehren, die gar nicht zur selben Uhrzeit gehoeren.
        shared: false,
        intersect: false,
        custom: ({ seriesIndex, dataPointIndex, w }) => {
          const def = seriesDefs[seriesIndex];
          const pt = w.config.series[seriesIndex]?.data?.[dataPointIndex];
          if (!def || !pt) return "";
          const [x, y] = pt;
          const hh = String(Math.floor(x)).padStart(2, "0");
          const mm = String(Math.round((x % 1) * 60)).padStart(2, "0");
          const valueText = def.schematicOnly && def.name === "Sonnenstand" ? "–" : `${Math.round(y)} ${def.unit}`;
          return `
            <div style="background:#1a1a2e;min-width:200px;border-radius:6px;overflow:hidden;">
              <div style="background:#000000;color:#FFFFFF;font-family:Roboto,sans-serif;font-weight:700;font-size:15px;padding:8px 14px;">${hh}:${mm}</div>
              <div style="padding:6px 14px;display:flex;align-items:center;gap:8px;">
                <span style="width:12px;height:12px;border-radius:50%;background:${def.color};flex:0 0 auto;box-shadow:0 0 4px rgba(0,0,0,.9);"></span>
                <span style="color:#FFFFFF;font-family:Roboto,sans-serif;font-size:14px;">${def.name}:</span>
                <span style="color:#FFFFFF;font-family:Roboto,sans-serif;font-size:14px;font-weight:700;margin-left:auto;">${valueText}</span>
              </div>
            </div>`;
        },
      },
      dataLabels: { enabled: false },
    };

    await this._drawChart(options, !!sim);
  }

  // 17.10.2026: Zeichnen serialisiert (Muster aus bitgrid_bar_trend_chart.js).
  // Im Lab-Replay kommt je Sim-Schritt ein Update; ueberholende updateOptions()
  // liessen den Chart sonst leer ("t.put is not a function"). Nach einem
  // Fehler wird einmal kurz darauf neu aufgebaut (im angehaltenen Replay kommt
  // sonst kein weiteres Update).
  async _drawChart(options, sim) {
    if (this._chartBusy) {
      this._pendingDraw = [options, sim];
      return;
    }
    this._chartBusy = true;
    let failed = false;
    try {
      if (this._apexChart) {
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

  // 3h-Tick-Striche etwas laenger als die dazwischenliegenden Stunden-Ticks,
  // exakt derselbe DOM-Eingriff wie im Verlauf-Chart: ApexCharts kennt kein
  // eingebautes Haupt-/Neben-Tick-Konzept (axisTicks.height gilt einheitlich),
  // deshalb nach jedem render/updateOptions erneut nachziehen. Index 0
  // entspricht X_MIN (0 Uhr), die Achse laeuft in 1h-Schritten, also trifft
  // jeder 3. Index genau die beschrifteten Stunden.
  // 26.09.2026, gleicher Bug wie bitgrid_verlauf_chart.js ("Striche werden
  // immer groesser"): urspruengliche Laenge einmalig pro DOM-Element
  // sichern und immer von dieser Basis aus rechnen, sonst kumuliert sich
  // die Verlaengerung bei jedem 5-Minuten-Refresh weiter auf.
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

customElements.define("bitgrid-regelschwellen-chart", BitgridRegelschwellenChart);
