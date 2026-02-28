# 05.2.3.3 - Baustein: Explain-Agent

Die Stimme des Systems.

Der Explain-Agent beantwortet die entscheidende Frage:
**„Warum macht BitGridAI das gerade?“**

Er erzeugt verständliche Explain-Sessions zu jeder Entscheidung – rein lesend, ohne Einfluss auf Aktoren oder Regeln.

![Hamster erklärt Entscheidungen](../../../../media/architecture/05_building_block_view/bithamster_052.png)

&nbsp;

## Scope

- Erklärungen zu Entscheidungen (Warum? Auslöser? Parameter?)
- Zuordnung zu `decision_id` / `command_id`
- Bereitstellung für UI und Research-Exporte
- **Kein** Eingriff in Steuerung oder Regeln

&nbsp;

## Struktur

- **Event Listener**  
  Konsumiert `DecisionEvent` und relevante State-Snapshots.

- **Template / LLM Engine**  
  Erzeugt Texte aus Templates oder optional lokalem LLM.

- **Session Manager**  
  Versioniert Explain-Sessions und verknüpft sie mit IDs.

- **Export Hook**  
  Stellt Sessions für UI und Research bereit.

&nbsp;

## Schnittstellen

**Provided**
- Explain-Sessions (Text / JSON)
- Metadaten zu Regeln, Triggern und Parametern

**Required**
- `DecisionEvent` und `EnergyState`
- Textbausteine (`explain/*.json`)
- Optional lokales LLM-Backend (read-only)

&nbsp;

## Ablauf (vereinfacht)

1) DecisionEvent trifft ein.  
2) Engine erzeugt Erklärung auf Basis von Regeln und Parametern.  
3) Session Manager speichert und versioniert die Session.  
4) UI erhält Push oder ruft Session gezielt ab.

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Read-only:** keinerlei Aktorik oder Rückwirkung auf Entscheidungen.  
- **Bevorzugt deterministisch:** Templates + Daten vor freiem LLM-Text.  
- **Reproduzierbar:** bei LLM-Nutzung mit Seed, Cache und Versionierung.  
- **Datenschutz:** keine externen API-Calls, alles lokal.

---
> **Nächster Schritt:**  
> Wir wissen jetzt, **warum** Entscheidungen getroffen werden.  
> Im nächsten Baustein schauen wir uns an, **was passiert wäre**, wenn sich die Rahmenbedingungen geändert hätten – ohne echte Eingriffe.
>
> 👉 Weiter zu **[5.2.3.4 - Baustein: Preview / What-if](./05234_preview.md)**
>
> 🔙 Zurück zu **[5.2.3 - Whitebox: UI & Explainability](./README.md)**
> 
> 🔙 Zurück zu **[5.2 - Level-2-Whiteboxes](../README.md)**

