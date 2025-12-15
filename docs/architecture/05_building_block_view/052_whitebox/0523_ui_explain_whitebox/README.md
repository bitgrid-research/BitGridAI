# 05.2.3 Whitebox UI und Explainability

Das Gesicht und die Stimme des Systems.

Diese Whitebox beschreibt alles, womit **Menschen** mit BitGridAI interagieren:
Anzeige, Erklärung, Simulation und bewusste Eingriffe.
Keine Entscheidungen – aber volle Transparenz.

*(Platzhalter für ein Bild: Der Hamster steht vor einem Dashboard.
Sprechblasen zeigen „Warum?“, „Was wäre wenn?“ und „Override aktiv“.)*
![Hamster erklärt Entscheidungen](../media/pixel_art_ui_explain.png)

---

## Scope

- Lokale Web-UI ohne Cloud-Abhängigkeit  
- API-Layer für Anzeige, Overrides und Simulationen  
- Explain-Agent zur nachvollziehbaren Begründung von Entscheidungen  
- Vorschau- und What-if-Funktionen ohne Einfluss auf den Betrieb  

---

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **API-Layer** | REST/WS-Endpunkte (`/state`, `/timeline`, `/override`, `/preview`). | Lokal, optional Auth; Rate Limits für Writes. |
| **Web-UI** | Frontend für State, Timeline, Overrides, Research-Opt-in. | Konsumiert WS-Events und REST-Previews. |
| **Explain-Agent** | Erzeugt Explain-Sessions (Templates oder lokales LLM). | Read-only; keine Aktor-Kommandos. |
| **Preview / What-if** | Simulation hypothetischer Zustände. | Sandbox auf Core-Regeln; keine Geräteschreibzugriffe. |

---

## Level-3-Details

- [5.2.3.1 API-Layer](./05231_api_layer.md)
- [5.2.3.2 Web-UI](./05232_web_ui.md)
- [5.2.3.3 Explain-Agent](./05233_explain_agent.md)
- [5.2.3.4 Preview / What-if](./05234_preview.md)

---

## Schnittstellen

**Provided**
- REST/WS für State, Timeline, Overrides, Research-Opt-in
- Explain-Sessions (Text, Metadaten)
- Simulationsergebnisse (Preview)

**Required**
- `DecisionEvents` und State-Stream aus dem Core
- Textbausteine (`explain/*.json`)
- Auth-Token (falls aktiviert)

---

## Hauptdatenflüsse

1) Core -> WS/REST -> UI (Live-State & Timeline).  
2) UI -> API-Layer -> Core (Override, Opt-in) -> Rückmeldung an UI.  
3) DecisionEvent -> Explain-Agent -> Explain-Session -> UI.  
4) Preview-Request -> Preview-Service -> Core-Regeln (Sandbox) -> UI.

---

## Qualitäts- und Betriebsaspekte

- **Strikte Trennung:** Anzeige & Erklärung haben keine Aktor-Rechte.  
- **Offline-fähig:** UI läuft lokal, kein externer Dienst notwendig.  
- **Nachvollziehbarkeit:** Jede User-Aktion trägt `command_id`, TTL und Status.

---
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](./README.md)**
> 
> 🔙 Zurück zu **[5.1 Whitebox Gesamtsystem](../051_blackbox/051_blackbox.md)**
