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

## Geplante Artefakte

- Funktionsfähiger Home-Assistant-Prototyp für den Simulationsbetrieb.
- Dokumentierte Regelmatrix mit Triggern, Prioritäten und Ausnahmefällen.
- Testprotokolle für Relais- und Sicherheitsszenarien.
- Aufbau- und Integrationsdokumentation des physischen Laborsetups.
