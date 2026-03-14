# 20.2.3.1 - SIM-WQ1 - Home Assistant: Regelwerk, UI und Relais

Diese Unterseite bündelt die technische Exploration und den prototypischen Aufbau
des Simulationskontexts in Home Assistant.


## Ziel

- Das regelbasierte Energiemanagement in Home Assistant technisch abbilden.
- Eine UI entwerfen, die Regelgründe, Schwellen und Prioritäten nachvollziehbar macht.
- Relais als physische Rückmeldung in die Systemlogik integrieren.
- Einen stabilen Simulationsrahmen für reproduzierbare Tests aufbauen.

## Aufgabenpakete (TODO)

- `A1` UI-Exploration in Home Assistant (Views, Statuskarten, Verlaufsdarstellungen).
- `A2` Regelableitungen und Übersetzung der Logik in Automationen/Skripte.
- `A3` Forschung an Relais (Schaltverhalten, Latenz, Fehlerfälle, Sicherheitsstopps).
- `A4` Aufbau des physischen Simulationsrahmens (PV-Simulator, Lasten, Reserveanzeige, Miner-Attrappe).

## Ablauf (Integrationsplan)

1. Zielbild und Scope fixieren (Regeln R1-R5, Sensoren, Aktoren, Zeitraster).
2. Datenmodell in Home Assistant anlegen (Sensoren, input_number, input_boolean, Zustandsmodell).
3. Regelzustände R1-R5 als Template-Sensoren abbilden.
4. Entscheidungslogik blockbasiert implementieren (START/STOP/THROTTLE/NOOP) + R3-Override.
5. Erklärungsmodell integrieren (Textbausteine, decision_reason, decision_explanation).
6. UI-Prototyp bauen (Energiefluss, Decision Card, Kontrolle/Override).
7. Relais/LED-Feedback integrieren (zunächst virtuell, später physisch via ESPHome/MQTT).
8. Simulationsmodus und Replays vorbereiten (manuelle Slider, CSV-Feeds).
9. Testszenarien ausführen (SH-1 bis SH-3, Sicherheits- und Stabilitätsfälle).
10. Artefakte dokumentieren (Regelmatrix, Testprotokolle, Aufbau- und Integrationsdoku).

## Implementierungsvorgehen in Home Assistant (ausgearbeitet)

1. Basis und Struktur
   Ziel: konsistentes Setup, später reproduzierbar.
   Vorgehen: Repo-Struktur definieren, z. B. `packages/`, `scripts/`, `automations/`.
   Konventionen: Entities nach Schema `bg_` + Bereich + Funktion benennen.
   Beispiel: `sensor.bg_grid_power_w`, `input_number.bg_threshold_stop_w`.

2. Rohdaten und Grenzwerte
   Ziel: saubere Datenbasis für Regeln.
   Rohsensoren: PV-Leistung, Netzbezug, Batterie-SOC, Lasten, Miner-Status.
   Schwellwerte: `input_number` für Start/Stop/Throttle und Sicherheitsgrenzen.
   Modi: `input_boolean` für Simulation, Override, Wartung, Not-Aus.

3. Regelableitung R1-R5
   Ziel: jede Regel als eigenen Zustand abbilden.
   Umsetzung: Template-Sensoren, die booleans liefern, z. B. `sensor.bg_rule_r1_active`.
   Kriterium klar dokumentieren: Eingangssensoren und Schwellwerte je Regel.
   Ergebnis: eine Regelmatrix, die eindeutig in HA nachgebildet ist.

4. Entscheidungszustand ableiten
   Ziel: eine eindeutige Aktion pro Zyklus.
   Umsetzung: ein Template-Sensor `sensor.bg_decision_state` mit Werten `START`, `STOP`, `THROTTLE`, `NOOP`.
   Priorität: R3-Override und Sicherheitsstopps vor allen anderen Regeln.
   Zusatz: `sensor.bg_decision_priority` für Debugging.

5. Orchestrierung als Skripte
   Ziel: Aktionen zentral und testbar halten.
   Skripte: `script.bg_start`, `script.bg_stop`, `script.bg_throttle`, `script.bg_noop`.
   Orchestrator: `script.bg_apply_decision`, das nach `bg_decision_state` delegiert.
   Nebenwirkungen: Relais, Status-Flags und Logs zentral setzen.

6. Erklärungsebene
   Ziel: Entscheidung nachvollziehbar machen.
   Template-Sensoren: `sensor.bg_decision_reason` und `sensor.bg_decision_explanation`.
   Inhalt: kurze Textbausteine mit Regel, Schwelle, Sensorwert.
   Beispiel: "R2 aktiv: Netzbezug 1200W > Stop-Schwelle 800W".

7. Automationen
   Ziel: zyklische und eventbasierte Ausführung.
   Trigger: Zeitraster (z. B. jede Minute) und State-Änderungen relevanter Sensoren.
   Conditions: Not-Aus, Wartung, Override, Sensor-Validität.
   Actions: `script.bg_apply_decision`, plus persistente Logs (Logbook/History).

8. UI und Monitoring
   Ziel: Regeln und Aktionen sichtbar machen.
   Dashboard-Karten: Energiefluss, Regelstatus (R1-R5), Entscheidung, Schwellen, Overrides.
   Controls: Schwellwerte und Modusumschaltung.
   Verlauf: Diagramme für PV, Netz, Batterie, Entscheidung.

9. Feedback über Relais/LED
   Ziel: physische Rückmeldung der Logik.
   Phase 1: virtuelle Schalter (`input_boolean`) als Relais-Stub.
   Phase 2: ESPHome oder MQTT-Relais anbinden, gleiches Entity-Schema nutzen.
   Safety: Relais bei Not-Aus oder Fehlerzustand zwingend aus.

10. Simulation und Replay
   Ziel: reproduzierbare Tests.
   Simulation: manuelle Slider für Sensoren, CSV-Feeds oder feste Szenarien.
   Szenario-Sets: SH-1 bis SH-3 als definierte Sequenzen.
   Ergebnis: automatische Auswertung der erwarteten Decisions.

11. Tests und Abnahme
   Ziel: Stabilität und Sicherheit.
   Tests: Regelprioritäten, Grenzfälle, Sensor-Ausfall, Relais-Stuck.
   Dokumentation: Regelmatrix, Testprotokolle, offene Issues.
   Freigabe: klarer Schritt für Wechsel von Simulation zu physischem Betrieb.

## Simulationsdarstellung (nur virtuell)

Ziel: Das komplette System in Home Assistant ohne physische Hardware abbilden.

1. Virtuelle Sensorik
   Alle Eingangswerte als `input_number` modellieren (PV, Netz, Batterie, Last, Reserve).
   Simulation-Toggle `input_boolean.bg_simulation_mode` aktivieren.
   Template-Sensoren verwenden, die im Simulationsmodus die Slider-Werte lesen.

2. Virtuelle Aktoren
   Relais/Miner als `input_boolean` oder `switch` simulieren.
   Alle Skripte schreiben nur auf diese virtuellen Entities.
   Externe Integrationen (ESPHome/MQTT) deaktiviert lassen.

3. Reproduzierbarkeit
   Feste Szenarien als Scripts oder Blueprints definieren.
   CSV-Replays über `input_number`-Sequenzen abspielen.
   Zeitraster standardisieren (z. B. 60s Takt).

4. Sichtbarkeit in der UI
   Eine dedizierte "Simulation"-View erstellen.
   Karten für Slider, Entscheidung, Regelstatus und Logbook.
   Klarer Hinweis, dass es sich um Simulation handelt.

5. Schutzlogik
   Not-Aus und Sicherheitsbedingungen bleiben aktiv.
   Im Simulationsmodus keine externen Schaltungen zulassen.

## Implementierungsfortschritt (Stand: 2026-03-04)

### Status je Arbeitspaket

- `A1` UI-Exploration in Home Assistant: `in progress` (Dashboard deutlich erweitert, Feinschliff offen)
- `A2` Regelableitung + Automationen/Skripte: `in progress` (R1/R2/R3/R5 + Decision-Zyklus + SH-Testsuite umgesetzt)
- `A3` Relais-Forschung: `in progress` (virtuelles Relais komplett, physisches Relais bewusst noch aus)
- `A4` Physischer Simulationsrahmen: `not started` (ausserhalb des reinen Simulations-Scopes)

### Bereits umgesetzt im Repo

- `src/ha/config/configuration.yaml`
  - neue Helper für Override, Lockout, Deadband und Decision-Texte
  - Template-Sensoren für `bg_decision_action`, `bg_decision_priority`, `bg_decision_reason`, `bg_decision_explanation`
  - Rule-State-Sensoren inkl. `r3_safety_override`, `r5_deadband_active`, `r5_min_runtime_active`, `r5_min_pause_active`
- `src/ha/config/scripts.yaml`
  - zentraler `bg_decision_cycle` + Dispatcher `bg_apply_decision`
  - Aktionsskripte: `bg_start`, `bg_stop`, `bg_throttle`, `bg_noop`, `bg_force_safety_stop`
  - Simulationsszenarien: `sim_reset`, `sim_sh1_stable_surplus`, `sim_sh2_variable_pv`, `sim_sh3_soc_critical`, `sim_sh4_safety_overtemp`
  - automatisches Testprotokoll: `sim_tests_reset`, `sim_assert_action`, `sim_run_sh_suite`
- `src/ha/config/automations.yaml`
  - Block-Takt-Automation
  - reaktive Neuberechnung bei Input-Änderungen
  - sofortiger Safety-Stop
  - Override-Lifecycle (aktivieren, ablaufen, deaktivieren)
- `src/ha/config/ui-lovelace.yaml`
  - Decision/State um Explainability erweitert
  - Override-Control-Card integriert
  - Simulation-Action-Card für manuelle Tests und SH-Szenarien
  - Test-Protocol-Card mit PASS/FAIL-Zählern und Suite-Status

### Validierung

- Home-Assistant Config-Check im Container ausgeführt (`hass --script check_config --config /config`).
- Fehler aus erstem Lauf (ungültige `input_text`-Länge) korrigiert.
- SH-Suite kann nun per `script.sim_run_sh_suite` am Stück durchlaufen werden.

### Nächster technischer Schritt

1. SH-Suite einmal live laufen lassen und die Ist-Ergebnisse im Logbook/History gegen Erwartung spiegeln.
2. Tuning der R5-Deadband-Parameter anhand der Flapping-Rate.
3. Optional: R4-Forecast-Regel in derselben Struktur ergänzen.

### Abnahmeprotokoll SH-Suite (Template, ab 2026-03-14)

Ziel: `A2` von `in progress` auf `done` heben, sobald die Suite stabil reproduzierbar läuft.

#### Durchführung je Lauf

1. `script.sim_tests_reset` ausführen.
2. `script.sim_run_sh_suite` vollständig durchlaufen lassen.
3. Ergebniswerte aus der Test-Protocol-Card erfassen (`PASS`, `FAIL`, Suite-Status).
4. Logbook/History auf unerwartete Action-Wechsel prüfen (`START`/`STOP`/`THROTTLE`/`NOOP`).
5. Safety-Stop prüfen: `script.bg_force_safety_stop` auslösen und Reaktionszeit notieren.

#### Akzeptanzkriterien (Go/No-Go)

1. Drei aufeinanderfolgende Läufe ohne manuellen Eingriff.
2. Pro Lauf `FAIL = 0` und Suite-Status `PASS`.
3. Kein unerwartetes Flapping ausserhalb der definierten SH-Szenarien.
4. Safety-Stop reagiert innerhalb eines Zyklus (max. 60s bei 60s-Takt).
5. Im Simulationsmodus keine externen Schaltungen/Integrationen aktiv.

#### Protokolltabelle (auszufüllen)

| Lauf | Datum/Uhrzeit | PASS | FAIL | Suite-Status | Flapping beobachtet (ja/nein + kurz) | Safety-Stop Reaktionszeit | Abweichungen / Notizen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |

#### Entscheidung

- `A2 = done`, wenn alle Akzeptanzkriterien erfüllt sind.
- Bei `No-Go`: Abweichung als Issue dokumentieren und betroffene Regel (`R1`-`R5`) + Sensoren benennen.
- Nach `Go`: Deadband-Tuning (`R5`) mit definierter Parameter-Matrix starten.

## Geplante Artefakte

- Funktionsfähiger Home-Assistant-Prototyp für den Simulationsbetrieb.
- Dokumentierte Regelmatrix mit Triggern, Prioritäten und Ausnahmefällen.
- Testprotokolle für Relais- und Sicherheitsszenarien.
- Aufbau- und Integrationsdokumentation des physischen Laborsetups.
