# BitGridAI — Implementierungs-Tasks

> Letzte Prüfung: 2026-05-24  
> Basis: Audit von `src/` gegen arc42-Architektur und Thesis-Kapitel 4

---

## Legende

| Symbol | Bedeutung |
|---|---|
| ✅ | Erledigt |
| 🔄 | In Arbeit |
| ⬜ | Offen |
| ❌ | Geblockt / abgelehnt |

---

## KRITISCH — Studie kann nicht stattfinden ohne

| # | Aufgabe | Status | Datei(en) | Notiz |
|---|---|---|---|---|
| K1 | **ProductionRunner** — Orchestriert Adapter, BlockScheduler, RuleEngine, ExplainAgent, EventStore, API in einem Entrypoint | ✅ | `src/runner.py` | asyncio Block-Loop + uvicorn FastAPI |
| K2 | **Dashboard Frontend** — Studie-Dashboards in HA Lovelace | ✅ | `src/ha/config/ui-lovelace.yaml`, `src/ha/config/packages/bitgridai.yaml` | 2 neue Views: Studie B (strukturiert) + Studie E (LLM-Text); Runner publiziert Explain-Felder via MQTT |
| K3 | **LLM-Integration** — ExplainAgent ist rein YAML-template-basiert; Thesis beschreibt Ollama-Inferenz | ✅ | `src/explain/explain_agent.py` | Ollama-Fallback via urllib; `OLLAMA_HOST` env-var; 5s Timeout; Template-Fallback |

---

## HOCH — Architektur-Lücken

| # | Aufgabe | Status | Datei(en) | Notiz |
|---|---|---|---|---|
| H1 | **API: `GET /timeline`** — Entscheidungshistorie (letzten N DecisionEvents) | ✅ | `src/ui/api.py` | `?n=20` Query-Param, 1–200 |
| H2 | **API: `GET /explain/{id}`** — ExplainResult per `decision_id` abrufbar | ✅ | `src/ui/api.py` | Liest aus EventStore + ExplainAgent |
| H3 | **API: `POST /research/export`** — Export-Bundle (Parquet + Manifest + SHA256) | ✅ | `src/ui/api.py` | ZIP: events.parquet + manifest.json + CHECKSUMS.sha256; feature_flag `research_export` |
| H4 | **API: Auth-Middleware** — Bearer-Token-Validierung; Feature-Flag `auth_enabled` vorhanden, Impl fehlt | ✅ | `src/ui/api.py` | Bearer-Token Middleware; Public Paths: /health /docs /openapi.json /redoc |
| H5 | **API: Rate-Limiting `/override`** — max. 10 Req/min pro Client | ✅ | `src/ui/api.py` | Sliding-Window in-memory; 10 req/60s pro Client-IP; HTTP 429 |

---

## MITTEL — Korrektheit und Vollständigkeit

| # | Aufgabe | Status | Datei(en) | Notiz |
|---|---|---|---|---|
| M1 | **Override-Persistence** — OverrideHandler ist In-Memory; Neustart verliert aktive Overrides | ✅ | `src/core/override_handler.py`, `src/data/db.py` | SQLite `active_overrides` table; load-on-init, persist request/clear |
| M2 | **Config-Validation** — `_validate()` ist Stub (gibt immer `[]` zurück) | ✅ | `src/ops/config_loader.py` | Prüft r1–r5, SoC-Logik, Temp-Logik |
| M3 | **API: `POST /preview`** — What-if-Endpunkt (z.B. „Was wäre wenn SoC 15%?") | ✅ | `src/ui/api.py` | Sandbox: rule engine read-only auf hypothetischem EnergyState; kein Seiteneffekt |
| M4 | **Autonomy-Level-Endpunkt** — 4 Stufen (Manuell/Assistiert/Halb-Auto/Vollautomatisch) | ✅ | `src/ui/api.py`, `src/core/override_handler.py` | `GET /autonomy` + `POST /autonomy`; FULL/SEMI/MANUAL |

---

## NIEDRIG — Nice-to-have

| # | Aufgabe | Status | Datei(en) | Notiz |
|---|---|---|---|---|
| N1 | **Health Monitor ausbauen** — ConnState-Tracking pro Adapter-Verbindung fehlt | ✅ | `src/adapters/health_monitor.py`, `src/adapters/mqtt_client.py` | `report_connected/disconnected`; MqttClient-Callbacks; `/health` zeigt Adapter-Status |
| N2 | **`.env.example`** — docker-compose.yml referenziert `.env`, keine Vorlage vorhanden | ✅ | `.env.example` | Alle Runner-Variablen ergänzt |

---

## Bereits solide implementiert ✅

| Bereich | Dateien |
|---|---|
| Regelwerk R1–R5 | `src/core/rules/r1_*.py` … `r5_*.py` |
| EnergyState + RawMeasurements | `src/core/models.py`, `src/core/energy_context.py` |
| BlockScheduler (10-min-Takt) | `src/core/block_scheduler.py` |
| TelemetryIngest + Signal-Enum | `src/adapters/telemetry_ingest.py`, `src/core/signals.py` |
| Alle 13 Hardware-Adapter | `src/adapters/*.py` |
| SQLite DB + Migrations | `src/data/db.py` |
| EventStore (append-only) | `src/data/event_store.py` |
| StateStore | `src/data/state_store.py` |
| KPI-Logging | `src/data/kpi.py` |
| ExplainAgent (Template-basiert) | `src/explain/explain_agent.py`, `src/explain/mappings/text_blocks.yaml` |
| ConfigLoader + hot-reload | `src/ops/config_loader.py` |
| Simulation + Replay | `src/sim/*.py` |
| Docker-Compose-Stack | `infra/docker-compose.yml` |
| Dockerfiles | `src/core/Dockerfile`, `src/ui/Dockerfile` |
| REST API (3 Basis-Endpunkte) | `src/ui/api.py` |

---

## Änderungslog

| Datum | Was | Von |
|---|---|---|
| 2026-05-24 | Initialer Audit, 14 Tasks identifiziert | Claude Code |
| 2026-05-24 | K1 `src/runner.py` implementiert (ProductionRunner) | Claude Code |
| 2026-05-24 | H1 `GET /timeline`, H2 `GET /explain/{id}` in api.py ergänzt | Claude Code |
| 2026-05-24 | M2 Config-Validation in config_loader.py implementiert | Claude Code |
| 2026-05-24 | N2 `.env.example` mit Runner-Variablen erweitert | Claude Code |
| 2026-05-24 | K2 HA-Dashboards Studie B + E in `ui-lovelace.yaml` ergänzt; `packages/bitgridai.yaml` neu; Runner publiziert Explain-MQTT | Claude Code |
| 2026-05-24 | K3 Ollama-Fallback in ExplainAgent; H3/H4/H5 in api.py | Claude Code |
| 2026-05-24 | M1 Override-Persistence; M3 POST /preview; M4 GET+POST /autonomy | Claude Code |
| 2026-05-24 | N1 HealthMonitor ConnState-Tracking; MqttClient on_connect/disconnect callbacks; /health Adapter-Status | Claude Code |
