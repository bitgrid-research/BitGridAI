# USER.md - Who You're Helping

## The Human

A developer and researcher building **BitGridAI** from the ground up.

## Their Setup

- **Home server:** Umbrel (`192.168.178.96`) — self-hosted, local network
- **AI box:** Ollama on `192.168.178.104:11434`, fixed IP, the only LLM host
- **AI interface:** Hermes Agent on the Umbrel (`192.168.178.96:18790`), persona "Neo", model `gemma4:e4b`
- **Development:** Claude Code (VS Code extension) for coding and documentation
- **Energy system:** PV installation, battery storage, flexible loads (incl. Bitcoin mining)
- **Smart home:** likely Home Assistant integration (local adapter)

## Their Work Style

- Documents everything in **German** using the **arc42** structure
- Follows a strict numbering convention (`21_`, `0521_`, etc.)
- Thinks in systems: clean separation of concerns, no magic, no black boxes
- Values reproducibility — decisions should be auditable and replayable
- Prefers local-first solutions; avoids cloud and vendor lock-in on principle

## Their Goals

- Build a transparent, explainable energy management system
- Use Bitcoin mining as a flexible load for PV surplus absorption
- Create a research-grade foundation (XAI, reproducible scenarios, KPI tracking)
- Keep full control and data sovereignty at home

## How to Work With Them

- Be direct and technical — no hand-holding unless asked
- Respect the arc42 structure and numbering scheme in all doc work
- When suggesting architecture changes, justify against the 6 quality goals
- If they write in German, respond in German
- Don't over-engineer. Simple and correct beats clever and fragile.
- When in doubt about scope, ask — they know exactly what they want
