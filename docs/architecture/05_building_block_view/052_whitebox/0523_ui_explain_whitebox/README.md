# 05.2.3 Whitebox UI und Explainability

Scope: lokale Web-UI, API-Layer und Explain-Agent zur Begruendung von Entscheidungen sowie fuer Overrides und Research-Opt-ins.

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **API-Layer** | REST/WS-Endpunkte (`/state`, `/timeline`, `/override`, `/preview`). | Auth optional, nur lokal; Rate Limits fuer Writes. |
| **Web-UI** | Frontend fuer State, Timeline, Overrides, Research-Opt-in. | Konsumiert WS-Events und REST-Previews. |
| **Explain-Agent** | Generiert Explain-Sessions (Textbausteine oder lokaler LLM). | Read-only auf DecisionEvents/State; keine Aktor-Commands. |
| **Preview/What-if** | Simuliert Regeln gegen hypothetische Inputs. | Nutzt Core-Regeln in Sandbox; schreibt nicht auf Geraete. |

## Level-3-Details

- [5.2.3.1 API-Layer](./05231_api_layer.md)
- [5.2.3.2 Web-UI](./05232_web_ui.md)
- [5.2.3.3 Explain-Agent](./05233_explain_agent.md)
- [5.2.3.4 Preview/What-if](./05234_preview.md)

## Schnittstellen

- **Provided:** REST/WS fuer State, Timeline, Overrides, Research-Opt-in; Explain-Sessions; Simulationsergebnisse.
- **Required:** DecisionEvents und State-Stream aus dem Core; Textbausteine (`explain/*.json`); Auth-Token (falls aktiviert).

## Hauptdatenfluesse

1) WS/REST State-Feed -> UI -> Rendering von Live- und Timeline-Ansichten.  
2) User-Action (Override, Opt-in) -> API-Layer -> Core -> Bestaetigung an UI.  
3) DecisionEvent -> Explain-Agent -> Explain-Session -> UI (Anzeige/Export).  
4) Preview Request -> Preview-Service -> Core-Regeln (Sandbox) -> Antwort an UI.

## Qualitaets- und Betriebsaspekte

- Keine Schreibrechte fuer Explain-Agent; strikte Trennung Anzeige vs. Aktorik.  
- UI ist offline-faehig (lokaler Host), keine Cloud-Abhaengigkeit.  
- Rueckverfolgbarkeit: jede User-Aenderung bekommt `command_id` und TTL.

---
> Zurueck zu **[5.2 Level-2-Whiteboxes](./README.md)**  
> Zurueck zu **[5.1 Whitebox Gesamtsystem](../051_blackbox/051_blackbox.md)**
