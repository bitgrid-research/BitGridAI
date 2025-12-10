# 08.8 Build- & Release-Management

Von der Codezeile zum laufenden System.

Die Build- und Release-Pipeline überführt den von uns entwickelten Code in eine stabile, lauffähige Form auf dem Edge-Device des Nutzers. Da wir keine Cloud-Infrastruktur verwalten, ist unser Prozess auf die Erstellung von **lokal verteilbaren Artefakten (Docker Images, Tarballs)** fokussiert.

Das Ziel: Ein Nutzer soll Updates mit minimalem Aufwand und maximaler Sicherheit installieren können.

*(Platzhalter für ein Bild: Ein Hamster sitzt an einem Fließband, das Codezeilen in versionierte Pakete mit einem Checksummen-Etikett packt, die dann auf einem Raspberry Pi landen.)*
![Hamster verwaltet Build-Pipeline](../../media/pixel_art_hamster_ci_cd.png)

## 1. Prinzipien der Deployment-Disziplin

Das Build-Management sorgt für Vorhersagbarkeit und Auditierbarkeit:

* **Reproducible Builds:** Jeder Build (egal ob lokal per `make build` oder in der CI) muss zu identischen Artefakten (`.tar.gz` oder `.deb`) mit identischen **Checksums** führen. Dies gewährleistet, dass der Code nicht manipuliert wurde.
* **Konfigurationsdisziplin:** Alle Regeln, Schwellenwerte und Policies sind in versionierten **YAML-Dateien** abgelegt. Die Konfiguration wird beim Start per **Schema-Validierung** geprüft.
* **Deployment-Gates:** Ein Rollout in die Produktion (Freigabe des Release-Tags) erfolgt nur, wenn die automatischen **Replay-Tests** und **KPI-Checks** (z.B. Flapping-Rate, Safety-Stopps) erfolgreich bestanden wurden.
* **Security/Hardening:** Die Einrichtung des OS (Firewall, Nutzerrechte) wird durch dedizierte Skripte (`setup/ansible/*`) automatisiert.

## 2. Der Build-Prozess und Artefakte

Der Build-Prozess ist schlank und auf die Edge-Hardware (ARM64) ausgerichtet:

| Phase | Werkzeug/Pipeline | Artefakt | Ziel |
| :--- | :--- | :--- | :--- |
| **Build** | GitHub Actions/Dockerfile | Docker Images (ARM64) | Basis für einfache Container-Updates (`docker compose pull`). |
| **Packaging** | `make build` | `dist/bitgrid-core.tar.gz` | Fallback für manuelle Installationen oder Air-Gapped Networks. |
| **Check** | CI / Checksums | `checksums.txt` | Verifikation der Artefakt-Integrität vor dem Rollout. |
| **Hardening** | `ansible/playbooks/` | Skripte (`os_hardening.yml`) | Automatisierte Einrichtung von Firewall (`deny-all + Allowlist`) und Nutzerrechten (lokal). |

### Konfigurations-Artefakte
Die Trennung von Code und Konfiguration ist strikt. Der Code weiß, wo er die Config sucht; der Nutzer pflegt die Daten.

* `config/bitgrid_rules.yaml`: Enthält alle R1–R5 Schwellenwerte und Deadband-Längen.
* `config/flags.yaml`: Globale Feature-Flags (z.B. `r4_enabled=true`).
* `config/policies.yaml`: Erweiterte Hodl-Policies oder Spezialregeln.

## 3. Deployment, Security & Betrieb

### A. Konfigurations-Management (Laufzeit)
* **Hash/Version:** Der Hash der aktuell geladenen `config.yaml` wird im `EnergyState` und prominent in der **UI sichtbar** gemacht. So weiß der Nutzer (und das Log), welche Regeln gerade aktiv sind.
* **Geheimnisse:** API-Keys und Passwörter liegen in separaten `secrets` (lokal mit `chmod 600` geschützt) und werden über Docker Secrets in die Container injiziert.

### B. Update-Prozess
1.  **Release:** Ein neuer Tag (`vX.Y.Z`) wird in der Registry veröffentlicht (Docker Hub/GH Registry).
2.  **Deployment:** Der Nutzer führt `docker compose pull && docker compose up -d` aus.
3.  **Atomic & Sicher:** Die Daten-Volumes und Konfigurations-Dateien werden beibehalten. Ein automatischer Rollback auf die vorherige Version findet statt, wenn der neue Container fehlschlägt.

### C. Backup & Wartung
* **Tägliche Sicherung:** Die kritischen Verzeichnisse (`config/` und die SQLite-DB) werden täglich gesichert (z.B. auf ein lokales NAS).
* **Parquet Rotation:** Archivierung und Rotation der Langzeit-Parquet-Logs wird durch eine interne Routine des `bitgrid-core` gesteuert, um Festplattenspeicher freizugeben.

---
> **Nächster Schritt:** Wir haben alle Konzepte und Prozesse definiert. Nun dokumentieren wir die wichtigsten strategischen Entscheidungen, die zur aktuellen Architektur geführt haben.
>
> 👉 Weiter zu **[09 Designentscheidungen](../09_design_decisions/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
