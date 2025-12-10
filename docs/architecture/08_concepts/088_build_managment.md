# 088 – Build- & Konfigurationsmanagement

TODO: Von der Codezeile zum laufenden System. Wie sieht unsere CI/CD-Pipeline aus und wie automatisieren wir den Weg in die Produktion?

> **Kurzüberblick:**  
> Versionierte YAML-Configs, reproducible Builds, klare Artefakte (Tarball/.deb), Checksums; Updates erst nach Replay/Tests. Keine Cloud-Builds nötig.

> **TL;DR (EN):**  
> Versioned configs, reproducible builds, clear artifacts with checksums; updates gated by replay/tests; no cloud builds required.

---

## Prinzipien

- **Konfigurationsdisziplin**: Änderungen über YAML mit Schema-Validation; Hash/Version sichtbar in UI.  
- **Reproducible Builds**: `make build` / CI erzeugt `.tar.gz` oder `.deb` inkl. Checksums.  
- **Deployment-Gates**: Rollout nur nach bestandenem Replay + KPI-Checks (Flapping, Safety).  
- **Security/Hardening**: `setup/ansible/*` für OS/Firewall; Secrets lokal (`chmod 600`).  
- **Backup & Rotation**: Tägliche Sicherung von `config/` und DB; Rotation für Parquet/Logs.  
- **Docs & ADRs**: Build-/Deploy-Änderungen werden in ADRs oder Runbooks referenziert.

---

## Artefakte & Pfade (Beispiele)

- `dist/bitgrid-core.tar.gz` / `.deb` (inkl. `checksums.txt`).  
- `config/bitgrid_rules.yaml`, `config/flags.yaml`, `config/policies.yaml`.  
- `setup/scripts/post_deploy_check.py` für Smoke-/Replay-Checks.  
- `ansible/playbooks/os_hardening.yml`, `scripts/lockdown.ps1` für Hardening.

> Build management keeps deployments predictable and auditable without external services.
