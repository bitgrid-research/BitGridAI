// BitGridAI — volle Bildschirmbreite + dynamische Miner-Flowfarbe
// Injiziert CSS in jeden Shadow Root rekursiv

const CSS = `
  #columns {
    max-width: 100% !important;
    justify-content: flex-start !important;
  }
  .column {
    max-width: 100% !important;
    min-width: 0 !important;
    flex: 1 1 0 !important;
  }
  .content {
    max-width: 100% !important;
  }
  hui-masonry-view, hui-sections-view, hui-panel-view {
    max-width: 100% !important;
  }
`;

function injectIntoRoot(root) {
  if (!root || root.querySelector('#bitgrid-wide')) return;
  const s = document.createElement('style');
  s.id = 'bitgrid-wide';
  s.textContent = CSS;
  root.appendChild(s);
}

function walkAll(node) {
  if (!node) return;
  if (node.shadowRoot) {
    injectIntoRoot(node.shadowRoot);
    node.shadowRoot.querySelectorAll('*').forEach(walkAll);
  }
}

function apply() {
  walkAll(document.querySelector('home-assistant'));
}

// ── Miner Flow Color ──────────────────────────────────────────────────────────

function getMinerColor(w) {
  if (w > 3200) return '#F7931A';  // Super    — Bitcoin Orange
  if (w > 2300) return '#26C6DA';  // Standard — Cyan
  if (w > 1500) return '#4CAF50';  // Eco      — Lime Green
  return '#616161';                // Off      — Grau
}

function applyMinerFlowColor() {
  const ha = document.querySelector('home-assistant');
  const hass = ha?.hass ?? ha?.__hass;
  if (!hass?.states) {
    console.debug('[BitGridAI] applyMinerFlowColor: hass not ready');
    return;
  }

  const raw = hass.states['sensor.miner_total_power_w']?.state;
  const w = parseFloat(raw ?? 0);
  const color = getMinerColor(w);
  console.debug(`[BitGridAI] miner=${w}W → color=${color}`);

  let found = 0;

  function walk(node) {
    if (!node) return;
    if (node.tagName === 'POWER-FLOW-CARD-PLUS') {
      found++;
      console.debug('[BitGridAI] found PFCP, shadowRoot=', !!node.shadowRoot);
      if (!node.shadowRoot) return;

      // Strategy A: inject !important style into shadow root
      let s = node.shadowRoot.querySelector('#bitgrid-miner-color');
      if (!s) {
        s = document.createElement('style');
        s.id = 'bitgrid-miner-color';
        node.shadowRoot.appendChild(s);
      }
      const css = `:host{--individual-left-top-color:${color}!important;--icon-individual-left-top-color:${color}!important;--icon-individual-top-color:${color}!important;}`;
      s.textContent = css;

      // Strategy B: also directly override inline style (last writer wins among same-level)
      node.style.setProperty('--individual-left-top-color', color);
      node.style.setProperty('--icon-individual-left-top-color', color);

      // Log current computed value for debugging
      const computed = getComputedStyle(node).getPropertyValue('--individual-left-top-color');
      console.debug('[BitGridAI] computed --individual-left-top-color=', computed);
      return;
    }
    if (node.shadowRoot) {
      node.shadowRoot.querySelectorAll('*').forEach(walk);
    }
  }

  walk(ha);
  console.debug(`[BitGridAI] walk done, found=${found} PFCP element(s)`);
}

// ── Startup ──────────────────────────────────────────────────────────────────
let n = 0;
const t = setInterval(() => {
  apply();
  applyMinerFlowColor();
  if (++n >= 20) clearInterval(t);
}, 800);

setInterval(applyMinerFlowColor, 15000);

window.addEventListener('location-changed', () => {
  setTimeout(apply, 500);
  setTimeout(applyMinerFlowColor, 1000);
});
document.addEventListener('visibilitychange', () => {
  setTimeout(apply, 500);
  setTimeout(applyMinerFlowColor, 500);
});
