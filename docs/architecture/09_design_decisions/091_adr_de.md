# 09.1 - Architektur-Entscheidungen (Kurzfassung)

Die DNA von BitGridAI.

Dieses Dokument dient als zentrale Ankerstelle für alle **Architecture Decision Records (ADRs)**. ADRs sind strukturierte Dokumente, die wichtige, strukturprägende Entscheidungen transparent, nachvollziehbar und mit ihrer ursprünglichen Begründung festhalten.

Die hier gesammelten Entscheidungen legen die Kernprinzipien von BitGridAI fest: **Lokalität, Determinismus, Erklärbarkeit** und **Nachhaltigkeit**.

<img src="../../media/architecture/09_design_decisions/bithamster_09.png" alt="Hamster tech" width="1000" />

&nbsp;

## ADR-Übersicht (Auszug)

Diese Tabelle fasst die wichtigsten, das System prägenden strategischen Entscheidungen zusammen:

| ADR | Entscheidung | Begründung | Querschnittliche Konzepte |
| :--- | :--- | :--- | :--- |
| **001 Local-First** | Das gesamte System läuft on-prem im lokalen Netzwerk. **Keine Cloud-Abhängigkeit.** | Maximaler **Datenschutz**, Autonomie bei Internetausfall (**Resilienz**). | Deployment, Privacy-by-Default |
| **002 MQTT-Bus** | MQTT wird als zentraler Event-/Command-Bus für State/Cmd/Events verwendet. | Erzeugt lose Kopplung (Hexagonal), ist leichtgewichtig und Industriestandard (IoT). | Whitebox, Logging & Tracing |
| **003 SQLite + Parquet**| Nutzung von SQLite für Laufzeit-Daten (Hot Data) und **Parquet** für Langzeit-Logs/Replay (Cold Data). | Portabel, wartungsarm (SQLite), **Auditierbar** und **effizient** für analytische Abfragen. | Persistenz, Testbarkeit |
| **004 Explainability-UI**| Die UI muss nicht nur den State, sondern auch die **Regel** (`R1-R5`), den **Trigger** und die **Timeline** zeigen. | Baut **Vertrauen** auf, ermöglicht Auditierung durch den Nutzer. | UI, Explainability |
| **005 Nachhaltigkeit** | Surplus und Preis werden als primäre Steuergrößen (R1, R4) etabliert. | Effizienz, Autarkie, Forschung. | Anforderungen, Regeln R1/R4 |
| **006 10-Min-BlockScheduler** | Die Entscheidungen der Regel-Engine werden an den festen Takt `block=floor(epoch/600)` gebunden. | **Stabilität**, Anti-Flapping (R5), Vereinfacht **Audit** und **Replay**. | Laufzeit, Testbarkeit |
| **007 Deterministische R1–R5** | Der Kern der Regel-Engine verzichtet auf Black-Box-ML-Modelle. | Garantiert **Testbarkeit** und **Erklärbarkeit** (R1–R5 sind Code, keine Blackbox). | Regeln, Testbarkeit |
| **008 EnergyState SSoT** | Der `EnergyState` ist die Single Source of Truth mit einem Schreiber (Core) und vielen Lesern. | Gewährleistet Konsistenz und vermeidet Race-Conditions. | Domain Models, Whitebox |
| **009 Deadband/Hysterese** | R5 erzwingt ein Haltefenster (D Blöcke) nach jedem Schaltvorgang. | Reduziert Flapping und schont die angeschlossene Hardware. | Regeln R5, Fehlerbehandlung |
| **010 Manual Override** | Ein manueller Eingriff erhält eine **Block-TTL** und wird als `manual_override` im Log gespeichert. | Garantiert **Nutzerkontrolle** ohne Policy-Drift. | Laufzeit, UI |
| **011 Lokale Forecasts** | R4 nutzt nur lokale Quellen, keine externen Cloud-APIs. | Reduzierte Abhängigkeit, erhöhte Ausfallsicherheit. | Regeln R4, Deployment |
| **012 Append-only + YAML-Version** | Logs und Configs werden mit Version/Hash gespeichert. | Garantiert **Reproducibility** und Auditierbarkeit. | Persistenz, Logging |
| **013 Lizenz AGPLv3** | Das Projekt wird unter der Affero General Public License Version 3 veröffentlicht. | Stellt Offenheit und die Verfügbarkeit des Codes für Forschung sicher. | Legal, Querschnitt |
| **014 Privacy by Default** | Keine Telemetrie, minimale Ports, lokale Datenhaltung. | Erfüllung der DSGVO-Prinzipien, Aufbau von Vertrauen. | Deployment, Privacy |
| **015 Safety First** | Kritische Regeln (R3/R2) erzwingen immer den Zustand **Stop → Safe** und brechen alle Overrides. | Absoluter Schutz der Hardware und des Hauses. | Regeln R2/R3, Fehlerbehandlung |
| **016 MQTT/REST Contract** | Topics/Endpoints sind im Vorfeld klar definiert und versioniert. | Stellt Interoperabilität und Testbarkeit sicher. | Whitebox, Integration |
| **017 KPIs als Ziele** | Die Systemwirkung wird über lokal gemessene KPIs (Grid Import ↓, Flapping Rate ↓) evaluiert. | **Evidenz** der Wirksamkeit statt Behauptung. | Testbarkeit, UI |
| **018 Energy-Path-Policies** | Die Opportunitätskosten (Export/Heat/Hodl) werden transparent geloggt. | Transparenz über die ökonomische Entscheidungsgrundlage. | Regeln, Logging |
| **019 PoW Telemetrie & Hash-Proof** | Pflichtwerte/Proben (Hash-Proof) werden vom Miner erfasst. | Sicherheit, Compliance und Forschung an der Effizienz. | Domain Models, Logging |
| **020 Engine-Strategie** | Der Python-Kern ist das **deterministische Entscheidungs-Modell** (per Replay studiert); **HA steuert live** und spiegelt den Kern eng. Keine zweite Voll-Engine pflegen. | Studie ist replay-basiert → Kern-Korrektheit zählt, nicht Live-Steuerung. Ein Live-Kern-Service würde die reale Anlage ohne XAI-Nutzen riskieren. | Whitebox, Determinismus, Studien-Validität |

---

## ADR 020 — Engine-Strategie (Detail)

**Kontext.** Es existieren faktisch **zwei** Entscheidungs-Implementierungen: der
Python-Kern (`src/core/`, R1–R5, deterministisch, replay-fähig) und eine
**HA-Template-Nachbildung** (`configuration.yaml`: `bg_decision_*`, `r2_grid_import_ok`,
…). Der `ProductionRunner` (Kern live) ist gebaut, läuft aber nicht (`bg_runner_*`
unavailable) — gesteuert wird **live durch die HA-Templates**.

**Geprüfte Optionen.**
- **A — Voller Runner 24/7:** eigene Telemetrie-Topics, HA nur Aktuator. Hoher Aufwand + Risiko an der Live-Anlage.
- **B — Snapshot-Bridge:** HA-Snapshot (`bitgrid/rec/snapshot`) → kleiner Kern-Service → Entscheidung zurück → HA aktuiert; Template als Fallback. Elegant, mittleres Risiko.
- **C — Kern = Modell, HA steuert (gewählt):** Der Kern ist das *studierte* Artefakt; HA steuert live und spiegelt ihn eng. Gratuite Divergenz wird beseitigt, Rest dokumentiert.

**Entscheidung: Option C.** Begründung: Die Anwenderstudie läuft **per Replay des
Kerns** (offline, deterministisch) — entscheidend ist die **Korrektheit/Erklärbarkeit
des Kerns**, nicht dass er die reale Anlage steuert. Einen Live-Kern-Service
einzuführen, fügt der echten Energieanlage Ausfallrisiko hinzu, **ohne** den
XAI-Beitrag der Arbeit zu stärken.

**Konsequenzen.**
- Kern bleibt Single Source of Truth für **Entscheidungslogik** (Studie, Analyse, Replay).
- HA-Templates spiegeln den Kern **so eng wie möglich**; bei Regeländerungen werden beide angepasst (zuletzt: R2-Netto-Bezug in beiden).
- **Gratuite Divergenz wird beseitigt** (z. B. THROTTLE — wird als Eco-Modus *im Kern* erstklassig gemacht, damit beide Engines übereinstimmen; siehe Roadmap Phase 4).
- **Residuale Divergenz** (R4 Forecast, R5 Deadband sind im HA-Template nicht abgebildet) wird als **bekannte Limitation** dokumentiert (Kapitel 11 Risiken, FINDINGS).
- **B bleibt das spätere Upgrade**, falls die Arbeit „Kern steuert reale Anlage" behaupten soll.

---
> **Nächster Schritt:** Die ADRs erklären das "Warum". Im nächsten Schritt betrachten wir die wichtigsten Qualitätsanforderungen im Detail.
>
> 👉 Weiter zu **[10 - Qualitätsszenarien](../10_quality_scenarios/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
