## Was wurde geändert?

<!-- Kurze Beschreibung: was und warum -->

## Typ

- [ ] `feat` — neue Funktion
- [ ] `fix` — Bugfix
- [ ] `docs` — nur Dokumentation
- [ ] `refactor` — Umstrukturierung
- [ ] `test` — Tests
- [ ] `chore` — Tooling, CI, Dependencies

## Checkliste

- [ ] `make check` lokal grün (fmt + lint + tests)
- [ ] Schichttrennung eingehalten (`core/` hat keine Imports aus `ui/`, `explain/`, `adapters/`)
- [ ] Keine hardcodierten IPs, Ports oder Secrets
- [ ] Neue Funktionen in `core/` haben Unit-Tests
- [ ] arc42-Doku angepasst (falls Architektur betroffen)

## Getestet mit

<!-- z.B. make test-unit, make test-replay, manuell im HA-Dashboard -->
