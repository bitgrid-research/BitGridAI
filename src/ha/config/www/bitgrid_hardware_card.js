// BitGridAI: list of invested hardware (13.11.2026, user request).
//
// Replaces the default more-info dialog of input_number.hardware_cost_eur,
// which only showed a meaningless history line. Storage is the local todo
// list todo.hardware (HA local_todo, stays on the server):
//   summary     = device name
//   description = price in EUR ("85.00")
//   due         = purchase date (YYYY-MM-DD)
// After every change the card writes the sum into
// input_number.hardware_cost_eur, so the settings row keeps showing the total.
//
// Display and bookkeeping only, no influence on any control decision.

const TODO = "todo.hardware";
const TOTAL = "input_number.hardware_cost_eur";

const ICONS = [
  [/raspberry|\bpi\b/i, "mdi:raspberry-pi"],
  [/zigbee/i, "mdi:zigbee"],
  [/ssd|nvme|festplatte|hdd/i, "mdi:harddisk"],
  [/switch|router|lan|poe/i, "mdi:lan"],
  [/miner|avalon|antminer|bitaxe/i, "mdi:pickaxe"],
  [/akku|batterie|speicher/i, "mdi:battery-high"],
  [/pv|solar|modul|wechselrichter/i, "mdi:solar-panel"],
  [/shelly|steckdose|plug/i, "mdi:power-socket-de"],
  [/summe|bisher/i, "mdi:sigma"],
];

const eur = (v) =>
  v.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
const dateDe = (iso) => (iso ? iso.split("-").reverse().join(".") : "–");
const esc = (t) =>
  String(t ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const price = (it) => {
  const v = parseFloat(String(it.description ?? "").replace(",", "."));
  return Number.isFinite(v) ? v : 0;
};
// German input: "3.198,00", "3198,5", "3.198" -> 3198; "12.5" -> 12.5.
// Dots are thousands separators when a comma is present or when every dot
// group has exactly three digits.
const parseEur = (raw) => {
  let s = String(raw ?? "").trim().replace(/[\s€]/g, "");
  if (s.includes(",")) s = s.replace(/\./g, "").replace(",", ".");
  else if (/^\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, "");
  return /^\d+(\.\d+)?$/.test(s) ? parseFloat(s) : NaN;
};
const iconFor = (name) => (ICONS.find(([re]) => re.test(name)) || [null, "mdi:chip"])[1];

class BitgridHardwareCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._render([]);
    }
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    const st = hass.states[TODO];
    const stamp = st ? st.last_updated : "";
    if (first || stamp !== this._stamp) {
      this._stamp = stamp;
      this._load();
    }
  }

  async _load() {
    if (!this._hass) return;
    try {
      const res = await this._hass.callWS({ type: "todo/item/list", entity_id: TODO });
      const items = (res.items || []).slice().sort((a, b) => String(b.due || "").localeCompare(String(a.due || "")));
      this._items = items;
      this._render(items);
      this._syncTotal(items);
    } catch (e) {
      this._render([], `Liste ${TODO} nicht erreichbar: ${e.message || e}`);
    }
  }

  _syncTotal(items) {
    const sum = Math.round(items.reduce((s, it) => s + price(it), 0) * 100) / 100;
    const cur = parseFloat(this._hass.states[TOTAL]?.state);
    if (Number.isFinite(sum) && Math.abs(sum - cur) > 0.004) {
      this._hass.callService("input_number", "set_value", { entity_id: TOTAL, value: sum });
    }
  }

  async _add() {
    const r = this.shadowRoot;
    const name = r.getElementById("name").value.trim();
    const p = parseEur(r.getElementById("price").value);
    const date = r.getElementById("date").value;
    const msg = r.getElementById("msg");
    if (!name) return (msg.textContent = "Bitte einen Gerätenamen eingeben.");
    if (!Number.isFinite(p) || p < 0) return (msg.textContent = "Bitte einen gültigen Preis eingeben.");
    msg.textContent = "";
    const data = { entity_id: TODO, item: name, description: p.toFixed(2) };
    if (date) data.due_date = date;
    await this._hass.callService("todo", "add_item", data);
  }

  async _remove(uid, name) {
    if (!confirm(`"${name}" aus der Liste entfernen?`)) return;
    // HA has no "todo/item/delete" WS command; the service accepts uid or summary.
    try {
      await this._hass.callService("todo", "remove_item", { entity_id: TODO, item: uid || name });
    } catch (e) {
      this.shadowRoot.getElementById("msg").textContent = `Entfernen fehlgeschlagen: ${e.message || e}`;
    }
  }

  _render(items, error) {
    const today = new Date().toISOString().slice(0, 10);
    const sum = items.reduce((s, it) => s + price(it), 0);
    const rows = items
      .map(
        (it) => `
        <div class="row">
          <ha-icon icon="${iconFor(it.summary)}"></ha-icon>
          <span class="name">${esc(it.summary)}</span>
          <span class="date">${dateDe(it.due)}</span>
          <span class="price">${eur(price(it))}</span>
          <button class="del" data-uid="${esc(it.uid)}" data-name="${esc(it.summary)}" title="Entfernen">
            <ha-icon icon="mdi:trash-can-outline"></ha-icon></button>
        </div>`
      )
      .join("");
    // Keep typed input across re-renders.
    const old = this.shadowRoot.getElementById?.("name");
    const keep = old
      ? { name: old.value, price: this.shadowRoot.getElementById("price").value, date: this.shadowRoot.getElementById("date").value }
      : { name: "", price: "", date: today };
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        ha-card { padding:24px; background:var(--card-background-color, #313a55); border-radius:14px;
                  color:var(--primary-text-color); font-size:var(--bg-fs-body, 1rem); }
        .head { display:flex; align-items:center; gap:14px; margin-bottom:18px; }
        .head ha-icon { --mdc-icon-size:36px; color:var(--primary-text-color); }
        .title { font-size:1.4em; font-weight:700; line-height:1.1; }
        .sub { color:var(--secondary-text-color); margin-top:2px; }
        .form { display:grid; grid-template-columns:minmax(0,2fr) minmax(6em,1fr) minmax(10.5em,1.2fr) auto; gap:10px; align-items:end; }
        label { display:block; color:var(--secondary-text-color); font-size:0.85em; margin:0 0 4px 2px; }
        input { width:100%; box-sizing:border-box; padding:10px 12px; border-radius:10px; font:inherit;
                color:var(--primary-text-color); background:rgba(255,255,255,0.06);
                border:1px solid var(--divider-color); color-scheme:dark; }
        input:focus { outline:none; border-color:var(--bg-color-eco, #47c47a); }
        .add { height:42px; width:52px; border-radius:10px; border:1px solid var(--bg-color-eco, #47c47a);
               background:rgba(71,196,122,0.25); color:var(--primary-text-color); cursor:pointer; }
        .add ha-icon { --mdc-icon-size:26px; }
        .msg { color:var(--error-color, #e57373); min-height:1.2em; margin:6px 2px 0; font-size:0.9em; }
        .table { margin-top:10px; border-radius:12px; background:rgba(0,0,0,0.12); overflow:hidden; }
        .row, .th { display:grid; grid-template-columns:32px minmax(0,1fr) 6.5em 7em 40px; gap:10px;
                    align-items:center; padding:10px 14px; }
        .th { color:var(--secondary-text-color); font-size:0.85em; border-bottom:1px solid var(--divider-color); }
        .row + .row { border-top:1px solid rgba(255,255,255,0.06); }
        .row ha-icon { --mdc-icon-size:22px; color:var(--secondary-text-color); }
        .name { overflow-wrap:anywhere; }
        .date { color:var(--secondary-text-color); }
        .price { text-align:right; font-variant-numeric:tabular-nums; }
        .th .price { text-align:right; }
        .del { background:none; border:none; color:var(--secondary-text-color); cursor:pointer; padding:4px; }
        .del:hover { color:var(--error-color, #e57373); }
        .empty { padding:16px 14px; color:var(--secondary-text-color); }
        .total { display:flex; align-items:center; gap:12px; margin-top:18px; padding-top:16px;
                 border-top:1px solid var(--divider-color); }
        .total ha-icon { --mdc-icon-size:30px; }
        .total .lbl { flex:1; font-size:1.2em; font-weight:700; }
        .total .sum { font-size:1.45em; font-weight:800; padding:8px 16px; border-radius:12px;
                      background:rgba(71,196,122,0.18); border:1px solid var(--bg-color-eco, #47c47a); }
        @media (max-width:600px) {
          .form { grid-template-columns:1fr 1fr; }
          .form > div:first-child { grid-column:1 / -1; }
          .row, .th { grid-template-columns:24px minmax(0,1fr) 6em 32px; }
          .row .date, .th .date { display:none; }
        }
      </style>
      <ha-card>
        <div class="head">
          <ha-icon icon="mdi:chip"></ha-icon>
          <div><div class="title">Investierte Hardware</div>
               <div class="sub">Übersicht aller angeschafften Geräte</div></div>
        </div>
        <div class="form">
          <div><label for="name">Gerät</label><input id="name" placeholder="z. B. Raspberry Pi 5" value="${esc(keep.name)}"></div>
          <div><label for="price">Preis (€)</label><input id="price" inputmode="decimal" placeholder="0,00" value="${esc(keep.price)}"></div>
          <div><label for="date">Datum</label><input id="date" type="date" value="${esc(keep.date)}"></div>
          <button class="add" id="add" title="Hinzufügen"><ha-icon icon="mdi:plus"></ha-icon></button>
        </div>
        <div class="msg" id="msg">${error ? esc(error) : ""}</div>
        <div class="table">
          <div class="th"><span></span><span>Gerät</span><span class="date">Datum</span><span class="price">Preis</span><span></span></div>
          ${rows || `<div class="empty">Noch keine Geräte eingetragen.</div>`}
        </div>
        <div class="total">
          <ha-icon icon="mdi:cash-multiple"></ha-icon>
          <span class="lbl">Gesamt investiert</span>
          <span class="sum">${eur(sum)}</span>
        </div>
      </ha-card>`;
    const r = this.shadowRoot;
    r.getElementById("add").addEventListener("click", async () => {
      await this._add();
      if (!r.getElementById("msg").textContent) {
        r.getElementById("name").value = "";
        r.getElementById("price").value = "";
      }
    });
    r.querySelectorAll(".del").forEach((b) =>
      b.addEventListener("click", () => this._remove(b.dataset.uid, b.dataset.name))
    );
  }

  getCardSize() {
    return 6;
  }
}

customElements.define("bitgrid-hardware-card", BitgridHardwareCard);

// ── Own dialog (13.11.2026): the Bubble-Card pop-up dimmed and squeezed the
// card. The settings row navigates to "#hardware"; this opens a centred
// dialog with the card and closes on backdrop, Escape or the close button.
const HASH = "#hardware";
let dialog = null;
let hassTimer = null;

function haRoot() {
  return document.querySelector("home-assistant");
}

function closeDialog() {
  if (!dialog) return;
  dialog.remove();
  dialog = null;
  clearInterval(hassTimer);
  if (location.hash === HASH) {
    history.replaceState(history.state, "", location.pathname + location.search);
    window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: true } }));
  }
}

function openDialog() {
  if (dialog) return;
  const root = haRoot();
  if (!root || !root.hass) return setTimeout(openDialog, 300);
  dialog = document.createElement("div");
  dialog.style.cssText =
    "position:fixed;inset:0;z-index:9999;display:flex;align-items:flex-start;justify-content:center;" +
    "padding:6vh 16px 16px;box-sizing:border-box;background:rgba(0,0,0,0.55);overflow:auto;";
  const box = document.createElement("div");
  box.style.cssText = "position:relative;width:100%;max-width:820px;border-radius:16px;" +
    "box-shadow:0 12px 40px rgba(0,0,0,0.5);";
  const close = document.createElement("button");
  close.innerHTML = '<ha-icon icon="mdi:close"></ha-icon>';
  close.title = "Schließen";
  close.style.cssText = "position:absolute;top:14px;right:14px;z-index:1;background:none;border:none;" +
    "color:var(--secondary-text-color);cursor:pointer;padding:6px;";
  const card = document.createElement("bitgrid-hardware-card");
  card.setConfig({});
  card.hass = root.hass;
  box.append(card, close);
  dialog.append(box);
  dialog.addEventListener("click", (e) => { if (e.target === dialog) closeDialog(); });
  close.addEventListener("click", closeDialog);
  document.body.append(dialog);
  hassTimer = setInterval(() => { const r = haRoot(); if (r && r.hass) card.hass = r.hass; }, 1000);
}

function checkHash() {
  if (location.hash === HASH) openDialog();
  else closeDialog();
}

window.addEventListener("location-changed", () => setTimeout(checkHash, 0));
window.addEventListener("hashchange", checkHash);
window.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDialog(); });
setTimeout(checkHash, 1500);
