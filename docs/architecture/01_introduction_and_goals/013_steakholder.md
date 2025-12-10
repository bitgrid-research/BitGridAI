# 013 – Stakeholder

TODO: Wer sind die Menschen (und Systeme), die BitGridAI nutzen oder beeinflussen?

> **Kurzüberblick:**  
> Kern-Stakeholder: Prosumer/Nutzende, BitGrid Core + Explain-Agent, externe Systeme (HA, Inverter, Meter, Miner) sowie Forschung/Entwicklung.

> **TL;DR (EN):**  
> Stakeholders are users/prosumers, BitGrid core + explain agent, external systems, and researchers/developers.

---

## Akteure / Actors

| Rolle | Erwartung |
| --- | --- |
| **Nutzer / Prosumer** | Transparente Energieentscheidungen sehen, Overrides setzen, Sicherheit spüren. |
| **BitGrid Core + Explain-Agent** | Lokale Entscheidungslogik (R1–R5), BlockScheduler, Logging, Explainability & On-Device-LLM. |
| **Externe Systeme** | Home Assistant, Inverter, Smart Meter/Sensorik, Speicher, Mining-Controller – liefern Daten oder erhalten Kommandos. |
| **Forschende / Entwickler** | Analysieren Verhalten, evaluieren Erklärbarkeit, entwickeln/integrieren Module, bauen Replays/KPIs. |

> | Role | Expectation |
> | --- | --- |
> | **User / Prosumer** | See transparent decisions, set overrides, feel safe. |
> | **BitGrid Core + Explain-Agent** | Local rule engine (R1–R5), block scheduler, logging, explainability on-device. |
> | **External Systems** | HA, inverter, meter/sensors, storage, miner controller – provide data or receive commands. |
> | **Researchers / Developers** | Analyse behaviour, evaluate explainability, build modules, run replays/KPIs. |

---

## Personas (HCI-Fokus)

- **P1 Prosumer:** will PV-Überschuss nutzen, Klarheit & Overrides; braucht Safety-Hinweise.  
- **P2 Researcher:** braucht Explainability-Daten, Timeline-Export, Opt-in-Toggle.  
- **P3 Developer:** testet Module/Policies, nutzt Replay & Debug-Ansicht.  
- **P4 Community Member:** vergleicht KPIs und Best Practices lokal.


> ---
> **Nächster Schritt:** Damit wissen wir, für wen wir BitGridAI bauen. Jetzt wird es ernst: Wir verlassen die Zielebene und schauen uns die harten Leitplanken an, die unsere Architektur einschränken.
>
> 👉 Weiter zu **[02 Randbedingungen](../02_architecture_constraints/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
