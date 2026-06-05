# 2. Forschung

Willkommen in der Forschungsdokumentation von **BitGridAI**.  

Hier werden die konzeptionellen Grundlagen gebündelt: Forschungsfragen, Prinzipien,
Annahmen & Grenzen, Systemmodell, Erklärungsmodell, Interface-Design, Szenarien,
Evaluation und Literatur.  

Die Kapitel bauen bewusst aufeinander auf und führen dich Schritt für Schritt
vom "Warum" bis zur empirischen Überprüfung. Du kannst sie linear lesen oder
gezielt dort einsteigen, wo du gerade Klarheit brauchst.

<img src="../media/research/research.png" alt="Status" width="1000" />

&nbsp;

## Inhaltsverzeichnis

Übersicht aller Kapitel und Unterkapitel - die Landkarte durch die Forschung:

* [20 - Forschungsfragen](./20_research_questions)
  * [20.1 - CRQ - Zentrale Forschungsfrage](./20_research_questions/201_central_research_question/README.md)
  * [20.2 - WQ - Zentrale Arbeitsfragen](./20_research_questions/202_working_questions/README.md)
    * [20.2.1 - SH-CONTEXT - Smart-Home-Kontext](./20_research_questions/202_working_questions/2021_smart_home_context/README.md)
      * [20.2.1.1 - SH-WQ1 - Verstehen der Entscheidung](./20_research_questions/202_working_questions/2021_smart_home_context/2021a_transparenz.md)
      * [20.2.1.2 - SH-WQ2 - Kontrolle und Override](./20_research_questions/202_working_questions/2021_smart_home_context/2021b_kontrolle.md)
      * [20.2.1.3 - SH-WQ3 - Vertrauen und Sicherheit](./20_research_questions/202_working_questions/2021_smart_home_context/2021c_vertrauen.md)
    * [20.2.2 - AUTO-CONTEXT - Automotive-Kontext](./20_research_questions/202_working_questions/2022_automotive_context/README.md)
      * [20.2.2.1 - AUTO-WQ1 - Verstehen der Ladeentscheidung](./20_research_questions/202_working_questions/2022_automotive_context/2022a_transparenz.md)
      * [20.2.2.2 - AUTO-WQ2 - Kontrolle im Auto](./20_research_questions/202_working_questions/2022_automotive_context/2022b_kontrolle.md)
      * [20.2.2.3 - AUTO-WQ3 - Vertrauen und Reichweitenangst](./20_research_questions/202_working_questions/2022_automotive_context/2022c_vertrauen.md)
    * [20.2.3 - SIM-CONTEXT - Simulations-Kontext](./20_research_questions/202_working_questions/2023_simulation_context/README.md)
      * [20.2.3.1 - SIM-WQ1 - Home Assistant: Regelwerk, UI und Relais](./20_research_questions/202_working_questions/2023_simulation_context/2023a_home_assistant_exploration.md)
      * [20.2.3.2 - SIM-WQ2 - Simulations- und Systementwicklung](./20_research_questions/202_working_questions/2023_simulation_context/2023b_simulation_system_development.md)
      * [20.2.3.3 - SIM-WQ3 - Interface, Explainability und Demonstratorentwicklung](./20_research_questions/202_working_questions/2023_simulation_context/2023c_interface_explainability_demonstrator.md)
      * [20.2.3.4 - SIM-WQ4 - Vertrauensdimensionen: Fundierung und Operationalisierung](./20_research_questions/202_working_questions/2023_simulation_context/2023d_trust_dimensions_operationalization.md)
    * [20.2.4 - SD-CONTEXT - Studiendesign-Kontext](./20_research_questions/202_working_questions/2024_study_design_context/README.md)
      * [20.2.4.1 - SD-WQ1 - Studiendesign und Stichprobe](./20_research_questions/202_working_questions/2024_study_design_context/2024a_study_design_sampling.md)
      * [20.2.4.2 - SD-WQ2 - Aufgaben, Instrumente und Messlogik](./20_research_questions/202_working_questions/2024_study_design_context/2024b_tasks_instruments_metrics.md)
      * [20.2.4.3 - SD-WQ3 - Ethik, Datenschutz und Analyseplan](./20_research_questions/202_working_questions/2024_study_design_context/2024c_ethics_privacy_analysis.md)
      * [20.2.4.4 - SD-WQ4 - Szenarien für Simulation und Studie](./20_research_questions/202_working_questions/2024_study_design_context/2024d_scenarios/README.md)
      * [20.2.4.5 - SD-WQ5 - Erkenntnisziele, Hypothesen & Pre-Registration](./20_research_questions/202_working_questions/2024_study_design_context/2024e_erkenntnisziele_prereg.md)
    * [20.2.5 - FIELD-CONTEXT - Feldstudie-Kontext](./20_research_questions/202_working_questions/2025_field_study_context/README.md)
      * [20.2.5.1 - FIELD-WQ1 - Verstehen der Entscheidungen im Alltag](./20_research_questions/202_working_questions/2025_field_study_context/2025a_understanding_in_the_wild.md)
      * [20.2.5.2 - FIELD-WQ2 - Kontrolle, Override und Recovery im Realbetrieb](./20_research_questions/202_working_questions/2025_field_study_context/2025b_control_override_recovery.md)
      * [20.2.5.3 - FIELD-WQ3 - Vertrauen, Sicherheit und Nutzung über Zeit](./20_research_questions/202_working_questions/2025_field_study_context/2025c_trust_safety_over_time.md)
      * [20.2.5.4 - FIELD-WQ4 - Notizen](./20_research_questions/202_working_questions/2025_field_study_context/2025d_notes.md)
  * [20.3 - DQ - Kontext- und Diskussionsfragen](./20_research_questions/203_discussion_questions/README.md)
&nbsp;

* [21 - BitGrid Prinzipien](./21_bitgrid_principles)
&nbsp;

* [22 - Annahmen & Grenzen](./22_assumptions_and_limits)
  * [22.1 - Annahmen zum Nutzungskontext](./22_assumptions_and_limits/221_usage_context_assumptions/README.md)
  * [22.2 - Annahmen zur Systemumgebung & Datenlage](./22_assumptions_and_limits/222_system_environment_assumptions/README.md)
  * [22.3 - Grenzen & Nicht-Ziele](./22_assumptions_and_limits/223_limits_and_non_goals/README.md)
&nbsp;

* [23 - Systemmodell & Entscheidungslogik](./23_system_model_and_decision_logic)
  * [23.1 - Komponenten & Datenflüsse (konzeptionell)](./23_system_model_and_decision_logic/231_components_and_flows/README.md)
  * [23.2 - Entscheidungsregeln & Auslöser](./23_system_model_and_decision_logic/232_decision_rules_and_triggers/README.md)
  * [23.3 - Abgrenzung zur Architektur](./23_system_model_and_decision_logic/233_architecture_boundary/README.md)
&nbsp;

* [24 - Erklärungsmodell](./24_explanation_model)
  * [24.1 - Bausteine einer Erklärung](./24_explanation_model/241_explanation_building_blocks/README.md)
  * [24.2 - Ableitung von Regeln zu erklärbaren Aussagen](./24_explanation_model/242_rule_to_statement_mapping/README.md)
  * [24.3 - Konsistenz zwischen Logs und UI-Begründung](./24_explanation_model/243_log_ui_consistency/README.md)
&nbsp;

* [25 - Interface Design](./25_interface_design)
  * [25.1 - Smart-Home-Interface (Dashboard)](./25_interface_design/251_smart_home_interface/README.md)
  * [25.2 - Automotive-Interface (In-Car-UI)](./25_interface_design/252_automotive_interface/README.md)
&nbsp;

* [26 - Szenarien & Use Cases](./26_scenarios_and_use_cases)
  * [26.1 - Szenarien im Smart-Home-Kontext](./26_scenarios_and_use_cases/261_smart_home_scenarios/README.md)
  * [26.2 - Szenarien im Automotive-Kontext](./26_scenarios_and_use_cases/262_automotive_scenarios/README.md)
  * [26.3 - Use Cases für Tests & Evaluation](./26_scenarios_and_use_cases/263_evaluation_use_cases/README.md)
&nbsp;

* [27 - Evaluationsrahmen](./27_evaluation_framework)
&nbsp;

* [28 - Reflexion & Transfer](./28_reflection_and_transfer)
  * [28.1 - Reflexion der Ergebnisse & Grenzen](./28_reflection_and_transfer/281_results_reflection/README.md)
  * [28.2 - Transfer auf andere Energiesysteme & Interfaces](./28_reflection_and_transfer/282_transfer_to_other_systems/README.md)
  * [28.3 - Offene Fragen & Ausblick](./28_reflection_and_transfer/283_open_questions_and_outlook/README.md)
&nbsp;

* [29 - Literaturübersicht](./29_literature_review)

---
> **Nächster Schritt:** Bevor wir Prinzipien, Modelle, Interfaces und Evaluationen ableiten,
> lohnt sich der Blick auf die Forschungsfragen.  
> Sie definieren den Rahmen, in dem alle weiteren Kapitel sinnvoll einrasten.
>
> 👉 Weiter zu **[20 - Forschungsfragen](./20_research_questions)**
>
> 🏠 Zurück zur **[Hauptübersicht](../README.md)**
