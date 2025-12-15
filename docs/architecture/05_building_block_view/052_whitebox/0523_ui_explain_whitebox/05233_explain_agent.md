# 05.2.3.3 Explain-Agent

Verantwortung: erzeugt Explain-Sessions zu Decisions (Warum? Welcher Trigger? Welche Parameter?) und stellt sie UI/Export bereit. Hat nur Lesezugriff, keine Aktorik.

## Struktur

- **Event Listener:** konsumiert DecisionEvents/State.  
- **Template/LLM Engine:** generiert Texte aus Templates oder lokalem LLM.  
- **Session Manager:** ordnet Explain-Sessions zu `command_id`/`decision_id`, versioniert Antworten.  
- **Export Hook:** stellt Sessions fuer UI/Research bereit.

## Schnittstellen

- **Provided:** Explain-Sessions (Text/JSON) fuer UI und Export.  
- **Required:** DecisionEvents/State, Textbausteine (`explain/*.json`), optional LLM-Backend, Auth (read-only).

## Ablauf (vereinfacht)

1) Event Listener erhaelt DecisionEvent/State.  
2) Template/LLM Engine baut Erklaerung (reason/trigger/params, Bezug auf Regeln).  
3) Session Manager speichert Session und verknuepft sie mit IDs.  
4) UI/Export ruft Session ab oder erhaelt Push-Event.

## Qualitaet und Betrieb

- Read-only, keine Aktor-Kommandos.  
- Determinismus bevorzugt: Templates + Daten statt nondeterministische LLMs; falls LLM genutzt, mit Seed/Cache.  
- Datenschutz: keine externe API-Calls; alles lokal.

---
> Zurueck zu **[5.2.3.x UI und Explainability (Level 3)](./README.md)**  
> Zurueck zu **[5.2.3 Whitebox UI und Explainability](../0523_ui_explain_whitebox.md)**
