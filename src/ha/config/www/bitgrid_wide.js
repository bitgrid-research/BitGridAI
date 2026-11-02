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
  /* View-Titel (BitGridAI - vX.Y.Z) mittig im Header zentrieren.
     Absolut ueber die volle Toolbar-Breite, damit echtes Zentrum statt
     "rechts neben dem Hamburger". pointer-events:none, da nicht klickbar. */
  .header .toolbar {
    position: relative;
  }
  .header .toolbar .main-title {
    position: absolute;
    left: 0;
    right: 0;
    margin: 0 !important;
    text-align: center;
    pointer-events: none;
  }

  /* Eingabefelder ausserhalb von Lovelace-Karten (native Panels wie
     /profile): card-mod erreicht die nicht, das ist kein hui-card-Kontext
     und card-mod wird nur ueber die Lovelace-resources geladen (siehe
     configuration.yaml). walkAll() injiziert dieses <style> dagegen in
     JEDEN Shadow-Root der App.
     17.10.2026, Nutzer-Wunsch: Eingabefelder dunkelblau statt hell. Fuellung
     #222b47 (dunkler als die Kartenflaeche #313a55, gleicher Blauton), Schrift
     #FFFFFF, Label #D3DEEA. Dieselben Werte stehen in themes/bitgrid.yaml
     (Abschnitt Eingabefelder), dort auch die HA-2026.10-Tokens
     --ha-color-form-background*, die die neuen ha-input/ha-select fuellen.
     Aeltere MWC/MDC-Textfelder (z.B. input_text-Zeilen, input_number
     more-info-Dialoge): */
  ha-select, mwc-select, ha-textfield, mwc-textfield {
    --mdc-select-fill-color: #222b47 !important;
    --mdc-select-ink-color: #FFFFFF !important;
    --mdc-select-label-ink-color: #D3DEEA !important;
    --mdc-select-dropdown-icon-color: #D3DEEA !important;
    --mdc-text-field-fill-color: #222b47 !important;
    --mdc-text-field-ink-color: #FFFFFF !important;
    --mdc-text-field-label-ink-color: #D3DEEA !important;
  }
  .mdc-select__selected-text,
  .mdc-text-field__input {
    color: #FFFFFF !important;
  }
  .mdc-select__anchor,
  .mdc-text-field__ripple {
    background-color: #222b47 !important;
  }

  /* 26.09.2026, per DevTools verifiziert (Elements-Panel, Nutzer-Screenshot):
     die Profil-Picker (Sprache/Design/Dashboard) sind KEIN mwc-select,
     sondern Material-Design-3 ha-picker-field > ha-combo-box-item. Deren
     Wert-Text (span[slot=headline]) liest ueber die "md-item"-Klasse
     "color: var(--md-list-item-label-text-color,
     var(--md-sys-color-on-surface, #1d1b20))": der Fallback #1d1b20 waere
     dunkel/lesbar, aber --md-sys-color-on-surface wird global hell belegt
     (vermutlich ueber primary-text-color, das fuer die dunklen Dashboard-
     Karten hell sein muss). Scoped auf die Picker-Tags selbst, damit
     --md-sys-color-on-surface nicht app-weit umdefiniert wird.
     17.10.2026: mit der dunkelblauen Fuellung ist der Wert-Text hell. */
  ha-picker-field, ha-combo-box-item, ha-combo-box {
    --md-sys-color-on-surface: #FFFFFF !important;
    --md-list-item-label-text-color: #FFFFFF !important;
  }

  /* 26.09.2026, dritte Variante desselben Problems: Web Awesome (wa-input)
     im input_number-more-info-Dialog ("Naechtliche Grundlast"), per
     Screenshot verifiziert (weisser Text in weisser Box). Statt jede
     Komponenten-Familie einzeln zu jagen (MDC, MD3, jetzt Web Awesome):
     pauschal auf das tatsaechliche native <input>/<textarea> zielen, das
     hinter jedem dieser Wrapper letztlich die Tastatureingabe rendert.
     walkAll() injiziert dieses <style> auch in wa-inputs eigenen
     Shadow-Root, deshalb reicht ein einfacher Tag-Selektor ohne ::part().
     17.10.2026: hell, passend zur dunkelblauen Fuellung. */
  input, textarea {
    color: #FFFFFF !important;
  }
  /* 17.10.2026: Doppelpunkt zwischen Stunde und Minute (input_datetime-
     Zeilen) liest --ha-color-text-secondary, im hellen HA-Standard #5e5e5e,
     auf der dunkelblauen Fuellung nur 2,2:1 (gemessen). Gezielt hier statt
     das globale Token umzubiegen. */
  :host(ha-base-time-input) .time-separator {
    color: #D3DEEA !important;
  }
  /* 17.10.2026: aufgeklappte Auswahlliste (ha-select ab HA 2026.10). Der
     gewaehlte Eintrag liest --ha-color-fill-primary-quiet-resting, hell
     #eff9fe, eine weisse Box in der dunklen Liste. Nur hier umgesetzt: das
     Token faerbt app-weit auch Buttons (z.B. "Springen"), die bleiben, wie
     sie sind. Gruene Schrift (primary-color) auf #222b47 = 5,0:1. */
  ha-dropdown-item {
    --ha-color-fill-primary-quiet-resting: #222b47 !important;
    --ha-color-fill-primary-quiet-hover: #2a3452 !important;
    --wa-color-neutral-fill-normal: #2a3452 !important;
  }

  /* 26.09.2026, Nutzer-Wunsch: Tab-Leiste mittig statt linksbuendig direkt
     neben dem Hamburger-Menu. Per DevTools verifiziert: die Tab-Leiste ist
     Web Awesome (ha-tab-group), .tabs (role=tablist) ist deren eigener
     Flex-Container fuer die Tab-Buttons, in derselben Shadow-Root wie
     dieses <style> (kein Piercing noetig). flex:1 1 auto auf .tabs sorgt
     bereits dafuer, dass es die verfuegbare Breite zwischen Hamburger und
     den Action-Icons rechts ausfuellt, justify-content zentriert die
     Buttons darin. */
  .tab-group-top .tabs {
    justify-content: center;
    /* 26.09.2026, Nutzer-Wunsch: Tab-Beschriftungen in Grossbuchstaben.
       text-transform ist eine vererbte Eigenschaft, wandert also automatisch
       durch die Slot-Projektion bis zum eigentlichen Text in
       ha-tab-group-tab durch, kein zusaetzliches Piercing noetig. */
    text-transform: uppercase;
    /* 26.09.2026, Nutzer-Wunsch: mehr Abstand zwischen den Tabs. gap wirkt
       auf die direkten Flex-Kinder von .tabs (die ueber slot="nav"
       projizierten ha-tab-group-tab-Elemente), unabhaengig von deren
       eigenem internen Padding. */
    /* 13.10.2026, Nutzer-Vorgabe "alles muss auf 1920x1080 passen, nicht
       scrollen": Abstand, Schrift, Tab-Innenabstand und Icon skalieren
       unterhalb von 1400 CSS-px linear mit der Fensterbreite herunter, ab
       1400 px bleiben exakt die bisherigen Werte (32px/16px/16px/24px).
       Gemessen (Playwright, Lab, Seitenleiste zu): vorher Ueberlauf mit
       Scrollpfeil ab unter ~1280 CSS-px. 1920x1080 bei 150 % Windows-
       Skalierung = 1280 CSS-px, minus ~17px Bildlaufleiste -> Ueberlauf.
       Mit den clamp()-Werten passt die Leiste bis ca. 880 CSS-px. */
    gap: clamp(8px, calc(6vw - 52px), 32px);
    /* 26.09.2026, Nutzer-Wunsch: Schrift so gross wie die Icons. Wirkt hier
       nur als vererbter Default: ha-tab-group-tab setzt intern selbst eine
       feste font-size (per Konsole verifiziert: getComputedStyle() auf dem
       Text-Elternelement ergab 20px statt der hier vererbten 30px). Die
       eigentliche Ueberschreibung passiert weiter unten direkt im
       Shadow-Root von ha-tab-group-tab. 26.09.2026: 30px liess GRUNDRISS/
       EINSTELLUNGEN aus der Leiste rausrutschen (Scroll-Pfeil erschien),
       auf 22px, dann 16px, dann 12px, final 16px (Nutzer-Wunsch).
       13.10.2026: 16px bleibt der Wert ab 1400 CSS-px, darunter s. o. */
    font-size: clamp(12px, calc(1vw + 2px), 16px);
  }

  /* 26.09.2026, Nutzer-Wunsch: Kontur/Halo fuer Icon+Schrift der Tabs, gegen
     den unruhigen Gras-Hintergrund. Gleiches Muster wie die Chart-Legenden
     (bitgrid_verlauf_chart.js, .bgai-legend-item/.bgai-legend-dot):
     doppelter drop-shadow fuer eine kraeftigere Kontur. filter auf dem
     ha-tab-group-tab-Element selbst (nicht auf .tabs) deckt Icon UND Text
     zusammen ab, da beide in diesem einen Element sitzen und filter den
     gesamten gerenderten Inhalt eines Elements als eine Ebene faerbt. */
  ha-tab-group-tab {
    filter: drop-shadow(0 0 3px rgba(0,0,0,.85)) drop-shadow(0 0 3px rgba(0,0,0,.85));
    /* 13.10.2026: Tab-Icon (ha-svg-icon liest --mdc-icon-size) skaliert mit,
       24px ab 1400 CSS-px, 20px bei 1000 CSS-px. */
    --mdc-icon-size: clamp(20px, calc(1vw + 10px), 24px);
  }

  /* 13.10.2026: horizontaler Innenabstand des Tabs (Web-Awesome-Basis
     div[part=base].tab, per DevTools gemessen 16px 16px 14px). :host()
     beschraenkt die Regel auf den Shadow-Root von ha-tab-group-tab, obwohl
     walkAll() dieses <style> in JEDEN Shadow-Root injiziert, andere Tab-
     Komponenten in HA bleiben unberuehrt. 16px ab 1400 CSS-px, 8px bei 1000. */
  :host(ha-tab-group-tab) [part~="base"] {
    padding-left: clamp(8px, calc(2vw - 12px), 16px) !important;
    padding-right: clamp(8px, calc(2vw - 12px), 16px) !important;
  }

  /* 26.09.2026: Ueberschreibung der internen font-size von ha-tab-group-tab
     (Web Awesome setzt dort intern fest 20px, unabhaengig von der oben
     vererbten 30px auf .tabs). walkAll() injiziert dieses <style> auch in
     ha-tab-group-tabs EIGENEN Shadow-Root, "*" trifft dort also direkt das
     interne Element mit der 20px-Regel, !important gewinnt gegen dessen
     nicht-!important-Deklaration. */
  ha-tab-group-tab, ha-tab-group-tab * {
    font-size: clamp(12px, calc(1vw + 2px), 16px) !important;
  }

  /* 13.10.2026: Spalten-Zoom, unabhaengig von card-mod.
     Befund (Lab, Playwright): die Spalten-Stacks erzeugt layout-card selbst
     (ohne hui-card-Huelle), ihr card_mod ":host { zoom: 0.8 }" kommt dort
     nie an (kein card-mod-Element, getestet mit card-mod 3.5.0 und 4.2.1),
     und layout-card uebernimmt aus view_layout nur grid-area. Diese Regel
     liegt im Shadow-Root von grid-layout (walkAll injiziert ueberall) und
     liest den Wert aus der Theme-Variable --bgai-view-zoom. Ohne Variable
     = 1, also exakt der bisherige Zustand. Wo card-mods eigene ":host
     !important"-Regel doch greift, gewinnt diese (innere !important-Regel
     schlaegt aeussere), hier entsteht also nie ein Doppel-Zoom.
     Gilt fuer die Spalten-Stacks aller Grid-Tabs, per Bereichsname (live
     gemessen, das style-Attribut lautet exakt "grid-area: <name>;"; das
     Semikolon verhindert, dass "l" auch "left" trifft). Bewusst nur
     hui-vertical-stack-card: die unsichtbare Hintergrundkarte teilt sich
     den ersten Bereich jedes Tabs und darf nicht mitgezoomt werden.
     Uebersicht g1l..g3r, Steuerung miner/regel, Bitcoin-Info r1l..r3r,
     Energie-Info und Heizung left/right, Einstellungen l/r. Grundriss hat
     kein Grid und ist hier (noch) nicht erfasst. */
  hui-vertical-stack-card[style*="grid-area: g1l;"],
  hui-vertical-stack-card[style*="grid-area: g1r;"],
  hui-vertical-stack-card[style*="grid-area: g2l;"],
  hui-vertical-stack-card[style*="grid-area: g2r;"],
  hui-vertical-stack-card[style*="grid-area: g3l;"],
  hui-vertical-stack-card[style*="grid-area: g3r;"],
  hui-vertical-stack-card[style*="grid-area: miner;"],
  hui-vertical-stack-card[style*="grid-area: regel;"],
  hui-vertical-stack-card[style*="grid-area: r1l;"],
  hui-vertical-stack-card[style*="grid-area: r1r;"],
  hui-vertical-stack-card[style*="grid-area: r2l;"],
  hui-vertical-stack-card[style*="grid-area: r2r;"],
  hui-vertical-stack-card[style*="grid-area: r3l;"],
  hui-vertical-stack-card[style*="grid-area: r3r;"],
  hui-vertical-stack-card[style*="grid-area: left;"],
  hui-vertical-stack-card[style*="grid-area: right;"],
  hui-vertical-stack-card[style*="grid-area: l;"],
  hui-vertical-stack-card[style*="grid-area: r;"] {
    zoom: var(--bgai-view-zoom, 1) !important;
  }

  /* 17.10.2026, Nutzer-Wunsch "Karten nebeneinander immer buendig" (Uebersicht).
     Befund (Lab, Playwright, 1280 und 1100 px): HA setzt auf jeder
     hui-vertical-stack-card ":host { height: 100% }", layout-card gibt jedem
     Grid-Item "margin: 4px 4px 8px". height:100% ignoriert diesen Rand, die
     Zeile wird aber MIT Rand bemessen: jede Spalte war 12 px hoeher als ihr
     hoechster Inhalt (Leerraum unter jeder Karte, die kuerzere Karte einer
     Zeile endete 13 bis 19 px frueher). Unabhaengig vom zoom (mit 1/0.8/0.87
     gemessen). height:auto laesst align-items:stretch die Hoehe korrekt
     abzueglich Rand setzen, die Spalte ist dann exakt so hoch wie ihr
     hoechster Inhalt. Danach waechst die letzte Karte jeder Spalte (Inhalt
     unter dem Gruppentitel) auf diese Hoehe; der Wrapper hui-card ist
     display:block, deshalb wirkte flex auf der Karte selbst bisher nicht.
     Energiefluss (PFCP) und die Miner-Boxen wachsen innen nicht mit (frueher
     zweimal gescheitert, s. v3), sie sind aber jeweils die hoehere Karte ihrer
     Zeile, also bleibt ihre natuerliche Hoehe massgeblich. Gemessen danach:
     336/336, 716/715, 1053/1053. */
  /* 17.10.2026 nachmittags: gleiche Regel fuer alle Spalten-Tabs (Steuerung,
     Bitcoin-Info, Energie-Info, Heizung, Einstellungen), dieselbe Liste wie der
     zoom oben. Wo die sichtbare Karte ihren gestreckten Wrapper nicht von selbst
     fuellt, traegt sie height:100% (button-card styles.card bzw. .bgai-card in
     bitgrid_bar_trend_chart.js). Gemessen per Injektion vor dem Einbau. */
  hui-vertical-stack-card[style*="grid-area: g1l;"],
  hui-vertical-stack-card[style*="grid-area: g1r;"],
  hui-vertical-stack-card[style*="grid-area: g2l;"],
  hui-vertical-stack-card[style*="grid-area: g2r;"],
  hui-vertical-stack-card[style*="grid-area: g3l;"],
  hui-vertical-stack-card[style*="grid-area: g3r;"],
  hui-vertical-stack-card[style*="grid-area: miner;"],
  hui-vertical-stack-card[style*="grid-area: regel;"],
  hui-vertical-stack-card[style*="grid-area: r1l;"],
  hui-vertical-stack-card[style*="grid-area: r1r;"],
  hui-vertical-stack-card[style*="grid-area: r2l;"],
  hui-vertical-stack-card[style*="grid-area: r2r;"],
  hui-vertical-stack-card[style*="grid-area: r3l;"],
  hui-vertical-stack-card[style*="grid-area: r3r;"],
  hui-vertical-stack-card[style*="grid-area: left;"],
  hui-vertical-stack-card[style*="grid-area: right;"],
  hui-vertical-stack-card[style*="grid-area: l;"],
  hui-vertical-stack-card[style*="grid-area: r;"] {
    height: auto !important;
  }
  :host(hui-vertical-stack-card[style*="grid-area: g1l;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: g1r;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: g2l;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: g2r;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: g3l;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: g3r;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: miner;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: regel;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: r1l;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: r1r;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: r2l;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: r2r;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: r3l;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: r3r;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: left;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: right;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: l;"]) #root > :last-child,
  :host(hui-vertical-stack-card[style*="grid-area: r;"]) #root > :last-child {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
  }
  :host(hui-vertical-stack-card[style*="grid-area: g1l;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: g1r;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: g2l;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: g2r;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: g3l;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: g3r;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: miner;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: regel;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: r1l;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: r1r;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: r2l;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: r2r;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: r3l;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: r3r;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: left;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: right;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: l;"]) #root > :last-child > *,
  :host(hui-vertical-stack-card[style*="grid-area: r;"]) #root > :last-child > * {
    flex: 1 1 auto !important;
  }

  /* 26.09.2026, Nutzer-Wunsch: die Action-Icons rechts (Hinzufuegen, Suche,
     Assist-Chat) ausblenden, fuers Kiosk-Wandtablet nur Rauschen. Per
     DevTools verifiziert: alle vier teilen sich slot="actionItems" (gleiche
     Shadow-Root wie die Tab-Leiste oben). Das Ueberlauf-Menue "..." bleibt
     auf Nutzer-Wunsch sichtbar (enthaelt "Ressourcen neu laden"), gezielt
     ausgenommen ueber :has() auf seinen bekannten Trigger-Button
     (ha-icon-button#dashboardmenu, "Dashboard-Menue oeffnen"). */
  [slot="actionItems"]:not(:has(#dashboardmenu)) {
    display: none !important;
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

// 17.10.2026, Nutzer-Befund "in den Einstellungen wird der Hintergrund gar nicht
// geladen": die Grastextur kam nur ueber lovelace-background, das gilt nur in
// Dashboards. Ausserhalb (Einstellungen, Verlauf, Logbuch, Profil) blieb die
// einfarbige primary-background-color. Die HA-Panels dort sind durchsichtig
// (per Playwright gemessen bis hinunter zu <html>), die Textur auf <html> scheint
// also durch; Dashboards decken sie mit ihrem eigenen Hintergrund ab. Gleiche
// Datei und Kachelung wie lovelace-background in themes/bitgrid.yaml.
function injectRootBackground() {
  if (document.getElementById('bitgrid-wide-root')) return;
  const s = document.createElement('style');
  s.id = 'bitgrid-wide-root';
  s.textContent = "html { background: url('/local/bg_grass.jpg?v=20260930') repeat 0 0 / 800px auto, var(--primary-background-color, #1a2e1a) !important; }";
  document.head.appendChild(s);
}

function apply() {
  injectRootBackground();
  walkAll(document.querySelector('home-assistant'));
}

// Hinweis (16.09.2026): Hier lebte eine Automatik, die alle 15 s die PFCP-
// Variable --individual-left-top-color nach sensor.miner_total_power_w
// umgefaerbt hat (bei Miner aus auf #616161 Grau, per !important plus
// Inline-Style). Da PFCP seine Slots nach SICHTBARER Reihenfolge vergibt und
// die Miner-Bubbles bei Standby ausgeblendet sind, traf das Grau die
// Geraete-Bubble. Auf Nutzer-Wunsch entfernt: die Bubbles behalten ihre
// konfigurierten Farben, nichts wird mehr dynamisch umgefaerbt.

// ── Startup ──────────────────────────────────────────────────────────────────
let n = 0;
const t = setInterval(() => {
  apply();
  if (++n >= 20) clearInterval(t);
}, 800);


window.addEventListener('location-changed', () => {
  setTimeout(apply, 500);
});
document.addEventListener('visibilitychange', () => {
  setTimeout(apply, 500);
});
