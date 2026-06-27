// BitGridAI — runde Ecken für custom cards (power-flow-card-plus,
// clock-weather-card, horizon-card).
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
// side effects (that is what the dormant bitgrid_wide.js used to do).

const RADIUS = "20px";
const SHAPED_CARDS = new Set([
  "POWER-FLOW-CARD-PLUS",
  "CLOCK-WEATHER-CARD",
  "HORIZON-CARD",
]);

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
  const css = `:host,ha-card{border-radius:${RADIUS}!important;overflow:hidden!important;}`;
  if (s.textContent !== css) s.textContent = css;
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

window.addEventListener("location-changed", () => setTimeout(apply, 500));
document.addEventListener("visibilitychange", () => setTimeout(apply, 500));
