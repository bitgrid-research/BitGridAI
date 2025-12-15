# 05.2.3.4 Preview / What-if

Der Blick in die Zukunft.

Das Preview-Modul beantwortet die Frage:
**„Was würde BitGridAI tun, wenn …?“**

Es simuliert Regelentscheidungen mit hypothetischen Eingaben – **ohne** Aktorik, **ohne** Seiteneffekte, **ohne** Risiko.

*(Platzhalter für ein Bild: Der Hamster schaut in eine Glaskugel.
Darin erscheinen alternative Energieflüsse und ein gestrichelter Pfeil zur Entscheidung.)*
![Hamster mit Glaskugel](../media/pixel_art_preview.png)

&nbsp;

## Scope

- Simulation von Regel-Auswertungen gegen hypothetische Inputs
- Vorschau von Decisions und Explain-Informationen
- Unterstützung von UI-Interaktionen und Analyse
- **Kein** Schreiben auf Geräte oder State

&nbsp;

## Struktur

- **Sandbox Runner**  
  Führt die Rule Engine mit einem hypothetischen `EnergyState` aus (read-only).

- **Input Adapter**  
  Validiert User- und Tool-Inputs (z.B. PV-Leistung, Preise, Forecasts).

- **Result Mapper**  
  Übersetzt das Ergebnis in `Decision` / `DecisionEvent` für die UI.

- **Cache**  
  Zwischenspeichert Previews zur Beschleunigung häufiger Anfragen.

&nbsp;

## Schnittstellen

**Provided**
- Preview-Ergebnisse (`Decision`, `DecisionEvent`)
- Optionale Explain-Metadaten für die Vorschau

**Required**
- Rule Engine (Sandbox-Modus)
- Aktueller oder letzter konsistenter `EnergyState`
- Hypothetische Inputs aus UI oder API

&nbsp;

## Ablauf (vereinfacht)

1) UI sendet Preview-Request mit geänderten Werten.  
2) Input Adapter validiert und baut einen hypothetischen `EnergyState`.  
3) Sandbox Runner führt die Rule Engine read-only aus.  
4) Result Mapper liefert das erwartete Verhalten an die UI zurück.

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Keine Aktorik:** kein MQTT, kein REST nach außen, kein Seiteneffekt.  
- **Deterministisch:** identisch zur echten Regel-Engine (gleiche Version).  
- **Isoliert:** Sandbox verhindert State-Mutation.  
- **Timeboxed:** feste Laufzeitgrenzen, damit die UI reaktionsschnell bleibt.

---
> **Nächster Schritt:**  
> Wir haben gesehen, **was passieren würde**, ohne etwas auszulösen.  
> Jetzt verlassen wir die Benutzeroberfläche und schauen dahin, wo alles festgehalten wird:  
> **Daten, KPIs, Replays und Forschung.**
>
> 👉 Weiter zu **[5.2.4 Whitebox Data & Research](../0524_data_research_whitebox/README.md)**
>
> 🔙 Zurück zu **[5.2.3 Whitebox UI & Explainability](./README.md)**
>  
> 🏠 Zurück zu **[5.2 Level-2-Whiteboxes](../README.md)**

