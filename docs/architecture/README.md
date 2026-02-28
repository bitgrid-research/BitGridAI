# 1. Architektur

Willkommen in der Architektur-Dokumentation von **BitGridAI**.  

Hier wird das System einmal komplett auseinander- und wieder zusammengedacht: von den grundlegenden Zielen über den Kontext und die Leitplanken bis hin zu Strategie, Design und Laufzeitverhalten.

Die Kapitel bauen bewusst aufeinander auf und führen dich Schritt für Schritt durchs System. Du kannst sie linear lesen – oder gezielt dort einsteigen, wo du gerade Klarheit brauchst.

<img src="../media/architecture/architectur.png" alt="Status" width="1000" />

&nbsp;

## Inhaltsverzeichnis

Übersicht aller Kapitel und Unterkapitel – die Landkarte durch die Architektur:

* [01 - Einführung & Ziele](./01_introduction_and_goals/README.md)
  * [01.1 - Anforderungen & Überblick](./01_introduction_and_goals/011_requirements_overview.md)
  * [01.2 - Qualitätsziele](./01_introduction_and_goals/012_quality_goals.md)
  * [01.3 - Stakeholder](./01_introduction_and_goals/013_steakholder.md)
&nbsp;

* [02 - Randbedingungen](./02_archtecture_constraints/README.md)
  * [02.1 – Technische Randbedingungen (Technical Constraints)](./02_archtecture_constraints/021_technical_constraints.md)
  * [02.2 - Organisatorische Randbedingungen (Organizational Constraints)](./02_archtecture_constraints/022_organizational_constraints.md)
  * [02.3 - Leitplanken & Konventionen (Conventions)](./02_archtecture_constraints/023_conventions.md)
&nbsp;

* [03 - Kontextabgrenzung](./03_context/README.md)
  * [03.1 - Fachlicher Kontext (Business Context)](./03_context/031_business_context.md)
  * [03.2 - Technischer Kontext (Technical Context)](./03_context/032_technical_context.md)
&nbsp;

* [04 - Lösungsstrategie](./04_solution_strategy/README.md)
  * [04.1 - Leitende Architekturprinzipien (Haltung)](./04_solution_strategy/041_principles.md)
  * [04.2 - Grobe Systemstruktur (Form)](./04_solution_strategy/042_structure.md)
  * [04.3 - Zentrale Architekturentscheidungen (Weichenstellungen)](./04_solution_strategy/043_decisions.md)
  * [04.4 - Abgrenzungen & bewusste Nicht-Ziele (Fokus)](./04_solution_strategy/044_non_goals.md)
&nbsp;

* [05 - Bausteinsicht](./05_building_block_view/README.md)
  * [05.1 - Level 1: Die Blackbox (Gesamtsicht)](./05_building_block_view/051_blackbox/README.md)
    * [05.1.1 - Blackbox: System und Schnittstellen](./05_building_block_view/051_blackbox/051_blackbox.md)
  * [5.2 - Level 2: Die Whitebox (Innenleben)](./05_building_block_view/052_whitebox/README.md)
    * [05.2.1 - Whitebox: Core-Orchestrierung](./05_building_block_view/052_whitebox/0521_core_whitebox/README.md)
      * [05.2.1.1 - Baustein: Block-Scheduler](./05_building_block_view/052_whitebox/0521_core_whitebox/05211_block_scheduler.md)
      * [05.2.1.2 - Baustein: Energy Context](./05_building_block_view/052_whitebox/0521_core_whitebox/05212_energy_context.md)
      * [05.2.1.3 - Baustein: Rule Engine](./05_building_block_view/052_whitebox/0521_core_whitebox/05213_rule_engine.md)
      * [05.2.1.4 - Baustein: Override Handler](./05_building_block_view/052_whitebox/0521_core_whitebox/05214_override_handler.md)
    * [05.2.2 - Whitebox: Adapter & Feld-I/O](./05_building_block_view/052_whitebox/0522_adapters_whitebox/README.md)
      * [05.2.2.1 - Baustein: Telemetry Ingest](./05_building_block_view/052_whitebox/0522_adapters_whitebox/05221_telemetry_ingest.md)
      * [05.2.2.2 - Baustein: Actuation Writer](./05_building_block_view/052_whitebox/0522_adapters_whitebox/05222_actuation_writer.md)
      * [05.2.2.3 - Baustein: Health Monitor](./05_building_block_view/052_whitebox/0522_adapters_whitebox/05223_health_monitor.md)
      * [05.2.2.4 - Baustein: Device Profiles](./05_building_block_view/052_whitebox/0522_adapters_whitebox/05224_device_profiles.md)
    * [05.2.3 - Whitebox: UI und Explainability](./05_building_block_view/052_whitebox/0523_ui_explain_whitebox/README.md)
      * [05.2.3.1 - Baustein: API-Layer](./05_building_block_view/052_whitebox/0523_ui_explain_whitebox/05231_api_layer.md)
      * [05.2.3.2 - Baustein: Web-UI](./05_building_block_view/052_whitebox/0523_ui_explain_whitebox/05232_web_ui.md)
      * [05.2.3.3 - Baustein: Explain-Agent](./05_building_block_view/052_whitebox/0523_ui_explain_whitebox/05233_explain_agent.md)
      * [05.2.3.4 - Baustein: Preview / What-if](./05_building_block_view/052_whitebox/0523_ui_explain_whitebox/05234_preview.md)
    * [05.2.4 - Whitebox: Data und Research](./05_building_block_view/052_whitebox/0524_data_research_whitebox/README.md)
      * [05.2.4.1 - Baustein: Operational DB](./05_building_block_view/052_whitebox/0524_data_research_whitebox/05241_operational_db.md)
      * [05.2.4.2  - Baustein: Event / Log Store](./05_building_block_view/052_whitebox/0524_data_research_whitebox/05242_event_log_store.md)
      * [05.2.4.3 - Baustein: KPI / Reporting](./05_building_block_view/052_whitebox/0524_data_research_whitebox/05243_kpi_reporting.md)
      * [05.2.4.4 - Baustein: Export / Replay Service](./05_building_block_view/052_whitebox/0524_data_research_whitebox/05244_export_replay.md)
    * [05.2.5 - Whitebox: Operations (Security / Config / Observability)](./05_building_block_view/052_whitebox/0525_operations_whitebox/README.md)
      * [05.2.5.1  - Baustein: Security & Auth](./05_building_block_view/052_whitebox/0525_operations_whitebox/05251_security_auth.md)
      * [05.2.5.2 - Baustein: Configuration & Feature Flags](./05_building_block_view/052_whitebox/0525_operations_whitebox/05252_config_feature_flags.md)
      * [05.2.5.3 - Baustein: Observability & Monitoring](./05_building_block_view/052_whitebox/0525_operations_whitebox/05253_observability.md)
&nbsp;

* [06 - Laufzeitsicht](./06_runtime_view/README.md)
  * [06.01 - Szenario: Normaler Start (Regel R1)](./06_runtime_view/0601_normal_start.md)
  * [06.02 - Szenario: Autarkie-Schutz (Regel R2)](./06_runtime_view/0602_autarky_protection.md)
  * [06.03 - Szenario: Sicherheitsstopp (Safety Stop - R3)](./06_runtime_view/0603_safety_stop.md)
  * [06.04 - Szenario: Prognose-Optimierung (Regel R4)](./06_runtime_view/0604_forecast_control.md)
  * [06.05 - Szenario: Stabilität & Totband (Regel R5)](./06_runtime_view/0605_deadband_stability.md)
  * [06.06 - Szenario: Manuelles Überschreiben (User Override)](./06_runtime_view/0606_manual_override.md)
  * [06.07 - Szenario: Autonomie-Stufen & Kontrollmodi](./06_runtime_view/0607_autonomy_levels.md)
  * [06.08 - Szenario: Boot & Recovery](./06_runtime_view/0608_boot_recovery.md)
  * [06.09 - Szenario: Adapter- & Sensor-Ausfall](./06_runtime_view/0609_adapter_sensor_failure.md)
  * [06.10 - Szenario: Config- & Feature-Flag-Reload](./06_runtime_view/0610_config_feature_reload.md)
  * [06.11 - Szenario: Export & Replay](./06_runtime_view/0611_export_replay.md)
  * [06.12 - Szenario: Authentifizierung & Rate-Limit (Fehlpfade)](./06_runtime_view/0612_auth_rate_limit_failures.md)
  * [06.13 - Szenario: Forecast-Update-Zyklus](./06_runtime_view/0613_forecast_update_cycle.md)
&nbsp;

* [07 - Verteilungssicht](./07_deployment_view/README.md)
  * [7.1 - Deployment (Docker-first, Umbrel-ready)](./07_deployment_view/071_deployment.md)
  * [7.2 - Infrastruktur & Betriebsvarianten](./07_deployment_view/072_infrastructure_variants.md)
&nbsp;

* [08 - Querschnittskonzepte](./08_concepts/README.md)
  * [8.1 - Fachliche Modelle (Domain Models)](./08_concepts/081_domain_models.md)
  * [8.2 - Sicherheits- & Vertrauenskonzept](./08_concepts/082_security_and_trust.md)
  * [8.3 - Datenhaltung & Datenlebenszyklus](./08_concepts/083_data_persistence.md)
  * [8.4 - Explainability & Transparenz](./08_concepts/084_explainability.md)
  * [8.5 - Autonomie, HCI & menschliche Kontrolle](./08_concepts/085_autonomy_and_hci.md)
  * [8.6 - Fail-Safe, Degradation & Robustheit](./08_concepts/086_fail_safe_and_degradation.md)
  * [8.7 - Logging, Events & Monitoring](./08_concepts/087_logging_and_monitoring.md)
  * [8.8 - Testbarkeit, Simulation & Replays](./08_concepts/088_testability_and_simulation.md)
  * [8.9 - Build-, Update- & Release-Prinzipien](./08_concepts/089_build_and_release.md)
&nbsp;

* [09 - Designentscheidungen](./09_design_decisions/README.md)
  * [09.1 - Architektur-Entscheidungen (Kurzfassung)](./09_design_decisions/091_adr_de.md)
&nbsp;

* [10 - Qualitätsszenarien](./10_quality_scenarios/README.md)
  * [10.1 - Qualitätsbaum](./10_quality_scenarios/101_quality_tree.md)
  * [10.2 – Qualitätsszenarien (Auszug)](./10_quality_scenarios/102_quality_scenarios/README.md)
    * [10.2.1 - Transparenz & Erklärbarkeit (Explainability)](./10_quality_scenarios/102_quality_scenarios/1021_explainability.md)
    * [10.2.2 - Autonomie & Privacy](./10_quality_scenarios/102_quality_scenarios/1022_autonomy_and_privacy.md)
    * [10.2.3 - Vorhersagbarkeit & Stabilität](./10_quality_scenarios/102_quality_scenarios/1023_predictability_and_stability.md)
    * [10.2.4 - Nachhaltigkeit & Wirtschaftlichkeit](./10_quality_scenarios/102_quality_scenarios/1024_sustainability_and_economics.md)
    * [10.2.5 - Safety: Schutz von Hardware & Infrastruktur](./10_quality_scenarios/102_quality_scenarios/1025_safety.md)
    * [10.2.6 - Reproduzierbarkeit & Erweiterbarkeit](./10_quality_scenarios/102_quality_scenarios/1026_reproducibility_and_extensibility.md)
    * [10.2.7 - Performance & Ressourceneffizienz](./10_quality_scenarios/102_quality_scenarios/1027_performance_and_efficiency.md) 
&nbsp;

* [11 - Risiken & Technische Schulden](./11_risks_and_technical_debt/README.md)
  * [11.1 - Risiken & Technische Schulden (Kurzfassung)](./11_risks_and_technical_debt/11_risks_and_technical_debt.md)
&nbsp;

* [12 - Glossar](./12_glossary/README.md)
  * [12 – Glossar](./12_glossary/12_glossary.md)

---
> **Nächster Schritt:** Bevor wir Bausteine stapeln und Regeln schrauben, lohnt sich ein Blick auf das Warum.  
> Die Einführung und Ziele stecken den Rahmen ab, in dem alle weiteren Kapitel sinnvoll einrasten.
>
> 👉 Weiter zu **[01 - Einführung & Ziele](./01_introduction_and_goals/README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../README.md)**
