# 06.09 Szenario: Adapter- & Sensor-Ausfall

Blindflug vermeiden.

BitGridAI trifft Entscheidungen auf Basis von Telemetrie: Temperaturen, Netzstatus, PV-Leistung, Zustände externer Geräte.  
Fallen diese Signale ganz oder teilweise aus, muss das System **sofort erkennbar, deterministisch und sicher reagieren**.

Dieses Szenario beschreibt, wie BitGridAI mit fehlender oder degradierter Telemetrie umgeht – unabhängig davon, ob die Ursache ein Adapter, ein Sensor oder ein Kommunikationsprotokoll ist.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster schaut auf ein Kontrollpanel mit ausgegrauten Sensoranzeigen. Ein Warnlicht blinkt, daneben ein Schild „No Data – Safe Mode“.)*

---

## Das Ziel: Keine Entscheidung ohne belastbare Daten

Grundprinzip:
> **Keine Telemetrie ist auch eine Information.**

BitGridAI unterscheidet klar zwischen:
- optionalen Signalen (Komfort, Optimierung),
- **Pflichtsignalen**, ohne die kein sicherer Betrieb möglich ist.

Fehlen Pflichtsignale, wird nicht „geschätzt“, sondern **konservativ gehandelt**.

---

## Der Ablauf bei Telemetrie-Ausfall (vereinfacht)

1. **Erkennung (Detection):**  
   Der Health Monitor erkennt ausbleibende Telemetrie oder fehlende Quittungen von Adaptern (MQTT, Modbus, REST).  
   Der System-Health-Status wechselt auf `warn` oder `error`.

2. **Kontext-Markierung (Degradation):**  
   Der Energy Context markiert fehlende Pflichtfelder.  
   Der `EnergyState` wird explizit als `degraded` gekennzeichnet.

3. **Regelentscheidung (Fail Safe):**  
   Die Rule Engine prüft, ob Pflichtsignale fehlen (z.B. Temperatur, Grid-Status, PV-Leistung).  
   Ist dies der Fall, wird ein **Safe- oder Stop-Zustand** ausgelöst.

4. **Wiederherstellung (Recovery):**  
   Sobald die Telemetrie wieder vollständig und valide eintrifft:
   - Health-Status wechselt zurück auf `ok`
   - der `degraded`-Status wird entfernt
   - der normale Blockbetrieb wird fortgesetzt

---

## Verhalten der Rule Engine

- Entscheidungen ohne Pflichtsignale sind **nicht zulässig**.
- Bei Safe/Stop aufgrund fehlender Daten wird die Ursache explizit dokumentiert.
- Optimierungsregeln (R1, R4, R5) treten vollständig zurück.
- Sicherheitsregel R3 bleibt führend.

---

## Schnittstellen & Signale

- **Health-Events** aus den Adaptern (`health/#`)
- **State-Flag** `degraded` im `EnergyState`
- **DecisionEvent** mit Reason:
  - `missing_telemetry`
  - optional mit Angabe der fehlenden Signalgruppen

Diese Signale sind extern sichtbar (UI, Monitoring, Logs).

---

> **Nächster Schritt:** Die Datenbasis ist abgesichert.  
> Jetzt betrachten wir, **wie Konfigurationsänderungen zur Laufzeit sicher übernommen werden**.
>
> 👉 Weiter zu **[06.10 Config- & Feature-Flag-Reload](./0610_config_feature_reload.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
