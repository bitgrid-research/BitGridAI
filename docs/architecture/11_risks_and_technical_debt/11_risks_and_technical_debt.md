# 11.1 Risiken & Technische Schulden (Kurzfassung)

Das Auge des Hamsters auf der Straße.

Dieses Dokument identifiziert und priorisiert die wichtigsten Risiken und technischen Schulden von BitGridAI. Da unser System direkt in die physische Umgebung (Stromflüsse, Hardware) eingreift, liegt der Fokus der Risikominderung klar auf **Betriebssicherheit (Stop → Safe)** und **Datenkonsistenz**.

*(Platzhalter für ein Bild: Ein Hamster mit einem Helm und einem Clipboard, der vor einem großen roten Warnschild steht, auf dem "THERMAL FAILURE" oder "RISK" steht.)*
![Hamster überprüft Risiken](../../media/pixel_art_hamster_risk_assessment.png)

&nbsp;

## 1. Hauptrisiken (Auszug)

Die folgenden Risiken wurden bewertet, ihre Auswirkung als mindestens **Mittel** eingestuft und sind direkt an die Architektur gekoppelt (Local-First, R1–R5, EnergyState).

| Risiko | Auswirkung | Wahrscheinlichkeit | Gegenmaßnahme (Architektur) |
| :--- | :--- | :--- | :--- |
| **Hardwareausfall (Lüfter/Sensor)** | Hoch | Mittel | Health-Monitor, **Thermal-Alarme (R3)**, System-Lockout. |
| **Storage-Überlauf** | Hoch | Mittel | **Rotation/Archiv** (Parquet), **Low-Disk-Alarm** (08.2). |
| **PoW-Telemetrielücke** | Hoch | Gering | Pflicht-Hashproben, Alerts aus S12 (Audit-Trail). |
| **MQTT-Broker-Ausfall** | Mittel | Mittel | Offline-Puffer, Retry/Backoff, **„offline hold“ (S3)**. |
| **Zeitdrift** | Mittel | Mittel | **Drift-Erkennung**, 1-Block-Hold + Re-Sync (RB-03). |
| **Fehlerhafte Regeldefinition** | Mittel | Gering | Schema-Validation (08.8), **Replay/Dry-Run (08.7)**, Unit-Tests R1–R5. |
| **Forecast-Fehler (R4)** | Mittel | Mittel | Confidence/Margin-Guardrails, R2/R3 priorisiert, schnelles Disable-Flag. |
| **Deadband falsch getuned** | Mittel | Mittel | **Replay A/B**, Flapping-KPI, adaptive Empfehlung. |
| **UI-Missverständnis** | Mittel | Gering | HCI-Tests, Glossar-Tooltips, **„Why?“ Dialog (08.3)**. |

&nbsp;

## 2. Technische Schulden (Technical Debt)

Diese Punkte sind Design-Kompromisse oder Bereiche, die aufgrund von Ressourcenknappheit noch nicht vollständig optimiert wurden. Sie müssen in zukünftigen Sprints adressiert werden, um die Wartbarkeit nicht zu gefährden.

* **Adapter-Modularität:** Die Adapter-Schnittstelle muss noch strikter definiert werden (Port-Definitionen, Plugin-Standard).
* **Logging-Schema:** Das Schema für `DecisionEvent` und `EnergyStateChangedEvent` muss versioniert und im Code zentralisiert werden, um die Konsistenz zu gewährleisten.
* **Integrationstests:** Die Test-Coverage für die MQTT/Rule-Integration und den Forecast-Evaluator muss ergänzt werden.
* **A11y-Gaps:** Barrierefreiheit (Keyboard/ARIA/Kontrast) im UI muss nachgezogen werden (A11y-Backlog).
* **Packaging:** Die Erstellung standardisierter Artefakte (`.deb/.tar.gz` mit Checksums) muss finalisiert und in der CI/CD-Pipeline verankert werden.

&nbsp;

## 3. Maßnahmenplan (Roadmap)

Diese Maßnahmen werden priorisiert, um die größten Risiken zu mindern und die kritischsten Schulden abzubauen:

1.  **Safety-Infrastruktur:** Implementierung des Health-Monitors und der zugehörigen UI-Alerts (Deckung von R3-Risiken).
2.  **Test-Suite-Abschluss:** Vollständige Test-Suite (Unit/Integration/Replay) als Deployment-Gate.
3.  **Storage-Governance:** Implementierung der Retention-Policy und der Low-Disk-Alarme.
4.  **Config-Governance:** Verankerung der Schema-Validation und der Versionierung/Hashing für die `config.yaml`.
5.  **Hardening:** Implementierung des Firewall-Profils (`deny-all + Allowlist`) über Ansible.
6.  **Runbook-Finalisierung:** Erstellung detaillierter Runbooks für Broker-Down, Übertemperatur, Zeitdrift und Low-Disk.

---
> **Nächster Schritt:** Wir haben die Risiken und Gegenmaßnahmen dokumentiert. Jetzt definieren wir das Glossar für eine einheitliche Terminologie.
>
> 👉 Weiter zu **[12 Glossar](../12_glossary/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
