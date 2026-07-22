# TOOLS.md - Local Notes & Tool Reference

Keep this file updated with connection details, device names, and tool-specific notes.

## Infrastructure

| Service | URL / Access | Notes |
|---|---|---|
| Umbrel | `192.168.178.96` | Home server, local network only |
| Hermes Agent (Neo) | `192.168.178.96:18790` | This AI interface (proxy port; 18789 is container-internal, dashboard) |
| Ollama | `192.168.178.104:11434` | Dedicated AI box, fixed IP, only LLM host |
| Home Assistant | `192.168.178.96:8123` | Smart home adapter |
| Vault search (RAG) | `192.168.178.96:8767` | Semantic search over the Obsidian vault |
| Bitsy status/chat | `192.168.178.96:8766` | Explanation service for the HA dashboard |
| BitGridAI repo | local dev machine | Claude Code (VS Code) for dev work |

## Neo's own mounts (not shared with other agents)

| Container path | Source | Access |
|---|---|---|
| `/opt/data/vault` | Obsidian `database_exploration/` | read-only |
| `/opt/data/memory` | Obsidian `memory_neo/` | read-write — Neo's own kurzzeit/langzeit/gedanken notes |
| `/opt/data/nachtberichte` | Hermes' own data volume | read-write — nightly hypothesis reports, Claude Code picks these up |

## Model — why gemma4:e4b, not qwen3:30b

Verified 2026-07-22 via `scripts/bench_model.py` against the five criteria that
matter for an agentic, tool-calling cron job: native context ≥ 64k, no forced
`<think>`, **genuine** `tool_calls` (not narrated text — `llama3.1:8b` failed
exactly here), RAM footprint, prefill throughput.

| Model | Ergebnis |
|---|---|
| `qwen3:30b-a3b-instruct-2507-q4_K_M` | bestand alle Kriterien, aber 22–26 GB RAM, 10–30 Tok/s Prefill (CPU-Last sinkt es weiter) |
| `llama3.1:8b` | **disqualifiziert** — narriert Tool-Aufrufe statt sie echt auszulösen |
| `gemma4:e4b` | bestand alle Kriterien: 131k Kontext, kein erzwungenes Denken, echtes Tool-Calling, nur 10.1 GB RAM, 40 Tok/s Prefill — aktuell aktiv |

`qwen3:30b` wurde von der Ollama-Box entfernt, um RAM für andere Dienste
(Vault-Suche, Bitsy-Chat) frei zu halten.

## Models Available

All models live on the Ollama box `192.168.178.104`.

| Model | ID | Use for |
|---|---|---|
| Neo (Nachtforscher) | `gemma4:e4b` | Nightly agentic analysis with tool-calling |
| Fast | `qwen3:8b` / `qwen3:4b-instruct` | Short answers, low latency |
| Embeddings | `nomic-embed-text` | Vault search index (do not change: the index dimensions depend on it) |

Not available any more: `qwen3:14b`, `qwen3.5:9b` (lived on the retired box
`.75`), `qwen3:30b-a3b-instruct-2507-q4_K_M` (removed 2026-07-22, see above).

## BitGridAI Key Paths

| What | Path |
|---|---|
| Architecture docs | `docs/architecture/` (arc42) |
| Research docs | `docs/research/` |
| Source code | `src/` |
| Dev environment | `docs/development/30_setup/dev_environment.md` |

## Arc42 Chapter Reference

| # | Topic |
|---|---|
| 01 | Einführung & Ziele |
| 02 | Randbedingungen |
| 03 | Kontext |
| 04 | Lösungsstrategie |
| 05 | Bausteinsicht |
| 06 | Laufzeitsicht |
| 07 | Verteilungssicht |
| 08 | Querschnittliche Konzepte |

## Notes

<!-- Add device names, SSH details, API tokens (local only), quirks, etc. here as you discover them -->
