// BitGridAI — volle Bildschirmbreite
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

// Run multiple times until HA is fully booted
let n = 0;
const t = setInterval(() => {
  apply();
  if (++n >= 20) clearInterval(t);
}, 800);

// Re-apply on navigation
window.addEventListener('location-changed', () => setTimeout(apply, 500));
document.addEventListener('visibilitychange', () => setTimeout(apply, 500));
