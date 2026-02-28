# 06.13 - Szenario: Forecast-Update-Zyklus

Vorausschau, ohne Hektik.

Prognosen ändern sich häufiger als der eigentliche Entscheidungsrhythmus.  
BitGridAI verarbeitet neue Wetter- und Preis-Forecasts gezielt, ohne bei jedem Update den kompletten Entscheidungsblock neu auszuführen.

Dieses Szenario beschreibt, wie Forecast-Updates in das System einfließen, wie Regel R4 (Forecast) bewertet wird und wann ein vorgezogener Re-Eval sinnvoll und erlaubt ist.

![Hamster steuert manuell](../../media/architecture/06_runtime_view/bithamster_06.png)

&nbsp;

## Das Ziel: Reaktionsfähig, aber stabil

Grundprinzip:
> **Neue Informationen führen nicht automatisch zu neuen Entscheidungen.**

Forecasts werden:
- inkrementell verarbeitet,
- gezielt bewertet,
- nur dann wirksam, wenn sie relevant sind.

So bleibt das System ruhig, nachvollziehbar und performant.

&nbsp;

## Der Ablauf bei Forecast-Updates (vereinfacht)

1. **Eingang (Update):**  
   Der Forecast-Service liefert neue Werte für:
   - Strompreise
   - Wetter / PV-Ertrag  
   Der Energy Context aktualisiert ausschließlich den Forecast-Anteil.

2. **Bewertung (Preview):**  
   Die Rule Engine bewertet Regel R4 isoliert:
   - als Vorschau („Preview“), oder
   - im nächsten regulären Block-Tick.

3. **Simulation (Optional):**  
   Preview- oder What-if-Funktionen können die neuen Forecasts nutzen, ohne den aktiven Betriebszustand zu verändern.

4. **Re-Evaluation (Optional):**  
   Bei einem signifikanten Delta (z.B. Preissturz, Wetterumschwung) kann ein **vorgezogener Re-Eval** ausgelöst werden.  
   Dieses Verhalten ist explizit konfigurierbar.

&nbsp;

## Verhalten der Rule Engine

- R4 (Forecast) wird getrennt von R1–R3/R5 betrachtet.
- Keine sofortige Aktion ohne:
  - Block-Tick oder
  - expliziten Re-Eval-Trigger.
- Sicherheits- und Stabilitätsregeln behalten Vorrang.

&nbsp;

## Schnittstellen & Signale

- **Forecast-Feed (lokal):**  
  Wetter- und Preis-Updates
- **Update-Event:**  
  Weitergabe an Core und UI
- **Optionaler Trigger:**  
  `forecast_update` für vorgezogene Auswertung

Alle Updates sind transparent und für UI sowie Monitoring sichtbar.

---

> **Nächster Schritt:** Prognosen sind nun integriert, ohne das System unruhig zu machen.  
> Im nächsten Kapitel wechseln wir die Perspektive und betrachten, **wie BitGridAI verteilt und betrieben wird**.
>
> 👉 Weiter zu **[07 - Verteilungssicht](../07_deployment_view/README.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
