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

  /* 14.11.2026, Nutzer-Wunsch: nur der aktive Tab ist gross, die anderen
     werden kleiner, damit alle Tabs in die Leiste passen; mit Animation.
     Web Awesome setzt das Attribut "active" auf den gewaehlten Tab (live
     gemessen). Der Tabtext ist ein loser Textknoten neben ha-icon und erbt
     seine Groesse ueber den Slot vom Basis-div [part=base]; deshalb steuern
     diese Regeln die Schrift dort, im Shadow-Root des Tabs (:host()). Das
     Icon skaliert per transform, das veraendert die Breite nicht und
     laesst sich animieren. */
  :host(ha-tab-group-tab) [part~="base"] {
    transition: font-size 0.35s ease, padding 0.35s ease;
  }
  :host(ha-tab-group-tab) ::slotted(ha-icon) {
    transition: transform 0.35s ease;
  }
  /* 15.11.2026, Nutzer-Wunsch: aktiver Tab 1,25-fach (Schrift und Icon)
     gegenueber der normalen Tabgroesse clamp(12px, 1vw + 2px, 16px). */
  :host(ha-tab-group-tab[active]) [part~="base"] {
    font-size: clamp(15px, calc(1.25vw + 2.5px), 20px) !important;
  }
  :host(ha-tab-group-tab[active]) ::slotted(ha-icon) {
    transform: scale(1.25);
  }
  :host(ha-tab-group-tab:not([active])) [part~="base"] {
    font-size: clamp(11px, calc(0.6vw + 3px), 13px) !important;
    padding-left: clamp(5px, calc(1vw - 6px), 10px) !important;
    padding-right: clamp(5px, calc(1vw - 6px), 10px) !important;
  }
  :host(ha-tab-group-tab:not([active])) ::slotted(ha-icon) {
    transform: scale(0.85);
  }
  /* Reicht auch das nicht (fitTabs() unten misst die Leiste und setzt dann
     bg-compact auf alle Tabs), zeigen die inaktiven Tabs nur ihr Icon: der
     Text schrumpft animiert auf 0. Der Name steht weiter als Tooltip am Icon
     (title) und als aria-label am Tab. */
  :host(ha-tab-group-tab[bg-compact]:not([active])) [part~="base"] {
    font-size: 0 !important;
    padding-left: 7px !important;
    padding-right: 7px !important;
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
// 14.11.2026: Hintergrund je Jahreszeit, gleiche Monate wie die Emojis in
// Einstellungen (Saisonale Schwellwerte) und wie bitgrid_dashboard_v3_3.yaml.
function seasonSuffix(month) {
  if ([12, 1, 2].includes(month)) return '_winter';
  if ([3, 4, 5].includes(month)) return '_fruehling';
  if ([9, 10, 11].includes(month)) return '_herbst';
  return '';
}
function grassUrl(night) {
  const sfx = seasonSuffix(new Date().getMonth() + 1);
  return `url('/local/bg_grass${sfx}${night ? '_night' : ''}.jpg?v=20261114') repeat 0 0 / 800px auto`;
}
function injectRootBackground() {
  let s = document.getElementById('bitgrid-wide-root');
  if (!s) {
    s = document.createElement('style');
    s.id = 'bitgrid-wide-root';
    document.head.appendChild(s);
  }
  s.textContent = `html { background: ${grassUrl(false)}, var(--primary-background-color, #1a2e1a) !important; }`;
}

// 13.11.2026, Befund Abfall-Tab: wird die Dashboard-Konfiguration bei offener
// Seite neu geladen (HA-Ereignis lovelace_updated, z. B. nach einem Deploy mit
// erzwungenem Neuladen), baut HA die Views neu auf. Die neuen Shadow-Roots
// bekamen dieses CSS bisher erst beim naechsten Tabwechsel, bis dahin waren
// nebeneinander stehende Karten nicht mehr buendig. Einmal abonnieren und
// danach mehrfach nachziehen (der Neuaufbau laeuft asynchron).
function watchLovelaceUpdates() {
  if (window._bgaiLovelaceWatch) return;
  const ha = document.querySelector('home-assistant');
  const conn = ha && ha.hass && ha.hass.connection;
  if (!conn) return;
  window._bgaiLovelaceWatch = true;
  conn.subscribeEvents(() => {
    [300, 1000, 2500, 5000].forEach((ms) => setTimeout(apply, ms));
  }, 'lovelace_updated').catch(() => { window._bgaiLovelaceWatch = false; });
}

function apply() {
  injectRootBackground();
  walkAll(document.querySelector('home-assistant'));
  applyKiosk();
  watchLovelaceUpdates();
}

// Hinweis (16.09.2026): Hier lebte eine Automatik, die alle 15 s die PFCP-
// Variable --individual-left-top-color nach sensor.miner_total_power_w
// umgefaerbt hat (bei Miner aus auf #616161 Grau, per !important plus
// Inline-Style). Da PFCP seine Slots nach SICHTBARER Reihenfolge vergibt und
// die Miner-Bubbles bei Standby ausgeblendet sind, traf das Grau die
// Geraete-Bubble. Auf Nutzer-Wunsch entfernt: die Bubbles behalten ihre
// konfigurierten Farben, nichts wird mehr dynamisch umgefaerbt.

// 13.11.2026, Nutzer-Wunsch: auf dem Raspberry-Pi-Display (.64, Chromium-Kiosk)
// keine aufklappbare Seitenleiste. Nur fuer dieses Geraet, nicht fuer andere
// Browser: der Pi ruft das Dashboard mit "?kiosk" auf, das wird hier in seinem
// localStorage gemerkt (die Tab-Navigation verliert den Query-Parameter).
// Dann (1) Seitenleiste per HA-eigenem Event "hass-dock-sidebar" dauerhaft
// ausblenden (dieselbe Einstellung wie im Profil "Seitenleiste immer
// ausblenden", HA speichert sie selbst) und (2) den Hamburger-Knopf, der sie
// wieder aufklappen wuerde, per CSS entfernen. "?kiosk=0" schaltet es ab.
const KIOSK_KEY = 'bgai_kiosk';
const KIOSK_CSS = 'ha-menu-button { display: none !important; }';

function kioskEnabled() {
  try {
    const q = new URLSearchParams(window.location.search);
    if (q.has('kiosk')) {
      if (q.get('kiosk') === '0') localStorage.removeItem(KIOSK_KEY);
      else localStorage.setItem(KIOSK_KEY, '1');
    }
    return localStorage.getItem(KIOSK_KEY) === '1';
  } catch (e) {
    return false;
  }
}

function applyKiosk() {
  if (!kioskEnabled()) return;
  const ha = document.querySelector('home-assistant');
  if (!ha) return;
  let docked = null;
  try { docked = JSON.parse(localStorage.getItem('dockedSidebar') || 'null'); } catch (e) { /* ignore */ }
  if (docked !== 'always_hidden') {
    ha.dispatchEvent(new CustomEvent('hass-dock-sidebar', {
      detail: { dock: 'always_hidden' }, bubbles: true, composed: true,
    }));
  }
  (function walk(node) {
    if (!node || !node.shadowRoot) return;
    const r = node.shadowRoot;
    if (!r.querySelector('#bitgrid-kiosk')) {
      const s = document.createElement('style');
      s.id = 'bitgrid-kiosk';
      s.textContent = KIOSK_CSS;
      r.appendChild(s);
    }
    r.querySelectorAll('*').forEach(walk);
  })(ha);
}

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

// ── Rasen-Hintergrund auch ausserhalb des Dashboards ─────────────────────────
// 13.11.2026, Nutzer-Wunsch: Profil, Einstellungen, Benachrichtigungen zeigten
// nur die flache primary-background-color. Das Dashboard legt den Rasen als
// eigene Karte hinter die Ansicht (bitgrid_dashboard_v3_3.yaml, gleiche Bilder,
// Tag/Nacht nach sun.sun). Hier dieselbe Ebene fuer alle Seiten: ein fester
// div ganz hinten, primary-background-color durchsichtig, damit er durch-
// scheint. Im Dashboard liegt die Dashboard-Karte darueber, nichts doppelt.
const GRASS = {
  day: () => `${grassUrl(false)}, linear-gradient(135deg, #5F8F4A 0%, #3F6B2E 100%)`,
  night: () => `${grassUrl(true)}, linear-gradient(135deg, #16232f 0%, #0d151c 100%)`,
};
function applyGrass() {
  if (!document.getElementById('bgai-grass-style')) {
    const st = document.createElement('style');
    st.id = 'bgai-grass-style';
    // !important in a stylesheet beats the theme's inline custom property.
    st.textContent = 'html { --primary-background-color: transparent !important; }';
    document.head.appendChild(st);
  }
  let layer = document.getElementById('bgai-grass');
  if (!layer) {
    layer = document.createElement('div');
    layer.id = 'bgai-grass';
    layer.style.cssText = 'position:fixed;inset:0;z-index:-1;pointer-events:none;';
    document.body.prepend(layer);
  }
  const hass = document.querySelector('home-assistant')?.hass;
  const sun = hass?.states?.['sun.sun']?.state;
  // 15.11.2026, Bug: right after a reload hass is not there yet; the unknown
  // sun counted as night and stayed until the next minute tick. Now nothing is
  // painted until the sun is known, and the check repeats every 0.5 s.
  if (!sun) {
    setTimeout(applyGrass, 500);
    return;
  }
  // Mode key includes the season, so the layer also switches at a month change.
  const mode = `${sun || ''}${seasonSuffix(new Date().getMonth() + 1)}`;
  if (layer.dataset.mode !== mode) {
    layer.style.background = sun === 'above_horizon' ? GRASS.day() : GRASS.night();
    layer.dataset.mode = mode;
  }
}
applyGrass();
setInterval(applyGrass, 60 * 1000);
window.addEventListener('location-changed', () => setTimeout(applyGrass, 300));
// Tablet wakes up after hours (sunrise or sunset while hidden): switch at once.
document.addEventListener('visibilitychange', () => setTimeout(applyGrass, 300));

// ── Tab Forschung: alles zugeklappt beim Oeffnen (15.11.2026, Nutzer-Wunsch) ──
// Die Karten (views/forschung_kpi.yaml, aufzeichnung_status.yaml) merken sich
// geoeffnete Abschnitte in window._bgOpen, damit das Neuzeichnen sie nicht
// schliesst. Beim Betreten des Tabs wird das vergessen und jeder schon
// gezeichnete Abschnitt geschlossen; der Umschalter ist das Element mit
// onclick="window._bgFold(...)", der Inhalt sein naechstes Geschwister.
function collapseFolds(node) {
  if (!node || !node.shadowRoot) return;
  node.shadowRoot.querySelectorAll('[onclick^="window._bgFold"]').forEach((el) => {
    const body = el.nextElementSibling;
    if (body && body.style.display !== 'none') {
      body.style.display = 'none';
      if (el.firstElementChild) el.firstElementChild.textContent = '▸';
    }
  });
  node.shadowRoot.querySelectorAll('*').forEach(collapseFolds);
}
// Klapp-Ueberschriften (15.11.2026, Bitsy-Karte): eine button-card mit
//   tap_action: {action: javascript, javascript: "[[[ window._bgaiFoldNext(this, 'key') ]]]"}
// klappt die Karten danach im selben Stapel auf und zu, bis zur naechsten
// solchen Ueberschrift. Zustand wie die uebrigen Abschnitte in window._bgOpen
// (zu beim Betreten des Tabs).
function foldKey(card) {
  const js = card && card._config && card._config.tap_action && card._config.tap_action.javascript;
  const m = typeof js === 'string' && js.match(/_bgaiFoldNext\(this,\s*'([^']+)'/);
  return m ? m[1] : null;
}
function foldTargets(card) {
  const el = card.parentElement && card.parentElement.tagName === 'HUI-CARD' ? card.parentElement : card;
  const out = [];
  for (let n = el.nextElementSibling; n; n = n.nextElementSibling) {
    const inner = n.tagName === 'HUI-CARD' ? n.firstElementChild : n;
    if (foldKey(inner)) break;
    out.push(n);
  }
  return out;
}
function setFold(card, open) {
  foldTargets(card).forEach((n) => { n.style.display = open ? '' : 'none'; });
  const nm = card.shadowRoot && card.shadowRoot.querySelector('#name');
  if (nm) nm.textContent = nm.textContent.replace(/^[▸▾]\s*/, '');
  // 15.11.2026, Nutzer-Wunsch: typical expander chevron on the right instead
  // of the small text triangle; turns 180° when open.
  const hc = card.shadowRoot && card.shadowRoot.querySelector('ha-card');
  if (!hc) return;
  let chev = hc.querySelector('.bgai-chev');
  if (!chev) {
    chev = document.createElement('ha-icon');
    chev.className = 'bgai-chev';
    chev.setAttribute('icon', 'mdi:chevron-down');
    chev.style.cssText = 'position:absolute;right:16px;top:calc(50% + 8px);--mdc-icon-size:24px;display:flex;' +
      'color:var(--secondary-text-color);transition:transform .2s ease;pointer-events:none;';
    if (getComputedStyle(hc).position === 'static') hc.style.position = 'relative';
    hc.append(chev);
  }
  // Centred on the rendered name text (measured), not on padding guesses.
  if (nm) {
    const nr = nm.getBoundingClientRect();
    const hr = hc.getBoundingClientRect();
    if (nr.height) chev.style.top = (nr.top - hr.top + nr.height / 2) + 'px';
  }
  chev.style.transform = 'translateY(-50%) ' + (open ? 'rotate(180deg)' : 'rotate(0deg)');
}
window._bgaiFoldNext = function (card, key) {
  window._bgOpen = window._bgOpen || {};
  window._bgOpen[key] = !window._bgOpen[key];
  setFold(card, window._bgOpen[key]);
};
function applyFoldHeaders(node) {
  if (!node || !node.shadowRoot) return;
  node.shadowRoot.querySelectorAll('*').forEach((el) => {
    if (el.tagName === 'BUTTON-CARD') {
      const key = foldKey(el);
      if (key) setFold(el, !!(window._bgOpen || {})[key]);
    }
    applyFoldHeaders(el);
  });
}
// Erster Aufruf des Tabs ohne Tabwechsel (Seite neu geladen): die
// Ueberschriften zeichnen sich erst nach und nach, darum mehrfach.
[1500, 3000, 6000, 10000].forEach((ms) => setTimeout(() => {
  if (/\/forschung\/?$/.test(window.location.pathname)) applyFoldHeaders(document.querySelector('home-assistant'));
}, ms));

function onResearchTab() {
  if (!/\/forschung\/?$/.test(window.location.pathname)) return;
  window._bgOpen = {};
  [300, 1200, 3000].forEach((ms) =>
    setTimeout(() => applyFoldHeaders(document.querySelector('home-assistant')), ms));
  // The view may still be building: collapse again once it is drawn.
  [200, 1000, 2500].forEach((ms) =>
    setTimeout(() => collapseFolds(document.querySelector('home-assistant')), ms));
}
window.addEventListener('location-changed', onResearchTab);

// ── Uhr in der Tab-Leiste (13.11.2026, Nutzer-Wunsch "Uhrzeit in jedem Tab") ──
// Sitzt rechts neben dem ⋮-Menue (Nutzer-Wunsch 13.11.2026) im Kopf von hui-root, damit sie in allen
// Tabs erscheint. Geraetezeit, Aktualisierung zum Minutenwechsel, keine Last
// auf HA. Die Kopfleiste wird beim Navigieren neu gerendert, daher prueft ein
// Intervall, ob die Uhr noch drin ist.
function findHuiRoot(node, depth = 0) {
  if (!node || depth > 12) return null;
  if (node.tagName === 'HUI-ROOT') return node;
  const kids = node.shadowRoot ? node.shadowRoot.querySelectorAll('*') : [];
  for (const k of kids) {
    if (k.tagName === 'HUI-ROOT') return k;
    if (k.shadowRoot) {
      const f = findHuiRoot(k, depth + 1);
      if (f) return f;
    }
  }
  return null;
}

function clockText() {
  return new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
}

function applyClock() {
  const hui = findHuiRoot(document.querySelector('home-assistant'));
  const r = hui && hui.shadowRoot;
  if (!r) return;
  let clock = r.getElementById('bgai-clock');
  if (!clock) {
    const anchor = r.querySelector('.action-items') || r.querySelector('.toolbar');
    if (!anchor) return;
    clock = document.createElement('div');
    clock.id = 'bgai-clock';
    clock.style.cssText =
      // 15.11.2026: 14px left gap so the clock no longer sits on the 3-dot menu.
      'display:flex;align-items:center;padding:2px 14px;margin:0 10px 0 14px;flex:0 0 auto;' +
      // 14.11.2026, Nutzer-Wunsch: Rahmen wie die Karten, gegen den Rasen.
      // 15.11.2026, Nutzer-Wunsch: nur leicht gerundete Ecken statt Kapsel.
      // 15.11.2026, test: light glass effect, card colour at ~60 % plus blur.
      'background:color-mix(in srgb, var(--ha-card-background) 60%, transparent);' +
      'backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);border-radius:10px;' +
      'border:var(--bgai-card-border-width-v3, 1px) solid var(--bgai-card-border-v3, rgba(0,0,0,.55));' +
      // Outline like the cards (1px border + 1px ring), no soft shadow: the
      // card token's 0 4px 16px looked like a thick dark halo here.
      'box-shadow:0 0 0 1px rgba(0,0,0,.7);' +
      'font-size:calc(var(--bg-fs-body, 1rem) * 1.5);font-weight:700;letter-spacing:0.04em;' +
      'color:var(--app-header-text-color, var(--primary-text-color));' +
      // No drop-shadow halo here: on the capsule it thickened the frame;
      // the card background already gives the contrast (14.11.2026).
      'font-variant-numeric:tabular-nums;white-space:nowrap;';
    anchor.append(clock);
  }
  const t = clockText();
  if (clock.textContent !== t) clock.textContent = t;
}

setInterval(applyClock, 2000);
applyClock();

// 14.11.2026: Passen die (schon verkleinerten) Tabs nicht in die Leiste,
// zeigen die inaktiven nur ihr Icon (CSS-Regel bg-compact oben). Gemessen
// wird die Breite im vollen Zustand; zurueck geht es erst, wenn genau diese
// Breite mit 16 px Reserve wieder passt, sonst wuerde die Leiste pendeln.
// Messung statt fester Bildschirmbreite, weil die Seitenleiste den Platz mit
// bestimmt (gemessen: ohne Icon-Modus passt die Leiste erst ab ca. 1800 px).
function fitTabs() {
  const hui = findHuiRoot(document.querySelector('home-assistant'));
  const r = hui && hui.shadowRoot;
  const group = r && r.querySelector('ha-tab-group');
  const sr = group && group.shadowRoot;
  const tabs = sr && sr.querySelector('.tabs');
  const nav = sr && sr.querySelector('.nav');
  if (!tabs || !nav) return;
  const items = [...group.querySelectorAll('ha-tab-group-tab')];
  if (!items.length) return;
  const avail = nav.clientWidth;
  const marked = items.filter((t) => t.hasAttribute('bg-compact')).length;
  if (marked && marked < items.length) {
    // Header re-rendered some tabs: keep the mode that was decided.
    items.forEach((t) => t.setAttribute('bg-compact', ''));
    return;
  }
  const compact = marked === items.length;
  if (!compact) {
    const need = tabs.scrollWidth;
    group.dataset.bgFull = String(need);
    if (need > avail + 2) items.forEach((t) => t.setAttribute('bg-compact', ''));
    return;
  }
  const full = Number(group.dataset.bgFull) || Infinity;
  if (full <= avail - 16) items.forEach((t) => t.removeAttribute('bg-compact'));
  syncScrollArrow(group, tabs, nav);
}

// 15.11.2026: the tab group only re-checks its scroll arrow on a resize of
// the nav, not when bg-compact shrinks the tabs. The arrow then stayed visible
// (and the strip scrolled) although everything fits. Re-sync it ourselves.
function syncScrollArrow(group, tabs, nav) {
  const overflow = tabs.scrollWidth > nav.clientWidth + 2;
  if (overflow) return;
  if (typeof group.updateScrollControls === 'function') group.updateScrollControls();
  if (typeof group.updateScrollButtons === 'function') group.updateScrollButtons();
  if ('hasScrollControls' in group && group.hasScrollControls) group.hasScrollControls = false;
  if (tabs.scrollLeft) tabs.scrollLeft = 0;
  if (nav.scrollLeft) nav.scrollLeft = 0;
}

setInterval(fitTabs, 1500);
window.addEventListener('resize', () => setTimeout(fitTabs, 400));
window.addEventListener('location-changed', () => setTimeout(fitTabs, 500));
