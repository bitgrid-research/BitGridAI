# 05.2.3.4 Preview / What-if

Verantwortung: simuliert Regel-Auswertungen gegen hypothetische Inputs, ohne Aktorik auszuloesen; liefert UI eine Vorschau, was passieren wuerde.

## Struktur

- **Sandbox Runner:** fuehrt Rule Engine mit hypothetischem `EnergyState` aus (read-only).
- **Input Adapter:** nimmt User- oder Tool-Inputs (z.B. geaenderte PV/Preis/Forecast-Werte) und validiert sie.
- **Result Mapper:** liefert `Decision`/`DecisionEvent` als Simulationsergebnis.
- **Cache:** kann letzte Previews zwischenspeichern, um UI-Interaktionen zu beschleunigen.

## Schnittstellen

- **Provided:** Preview-Ergebnisse (Decision/DecisionEvent) an UI/API, optional als DTO/JSON.
- **Required:** Rule Engine in Sandbox-Modus, aktueller/letzter `EnergyState`, Input aus UI/API.

## Ablauf (vereinfacht)

1) UI sendet Preview-Request mit hypothetischen Werten.  
2) Input Adapter validiert und baut hypothetischen `EnergyState`.  
3) Sandbox Runner ruft Rule Engine (read-only) auf.  
4) Result Mapper gibt erwartete Decision/DecisionEvent an UI zurueck.

## Qualitaet und Betrieb

- Kein Schreiben auf Geraete, kein MQTT/REST nach aussen.  
- Deterministisch, identisch zur echten Rule Engine (gleiche Version/Schemas).  
- Abgesicherte Laufzeit (Timeout), um UI nicht zu blockieren.

---
> Zurueck zu **[5.2.3.x UI und Explainability (Level 3)](./README.md)**  
> Zurueck zu **[5.2.3 Whitebox UI und Explainability](../0523_ui_explain_whitebox.md)**
