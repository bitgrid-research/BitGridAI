# Modell-Benchmarks fuer Neo

Lebendiges Protokoll, kein einmaliger Report: wird bei jedem neuen
Modelltest ergaenzt, nicht ueberschrieben. Werkzeug: `scripts/bench_model.py`.

## Unsere Kriterien (agentische Nutzung, Tool-Calling noetig)

1. **Nativer Kontext >= 64000**: Hermes-Minimum, sonst disqualifiziert.
2. **Kein erzwungenes `<think>`**: Reasoning-Modelle verzoegern jede Antwort.
3. **Tool-Calling, direktiver Befehl**: echter `tool_calls`-Eintrag, geprueft
   ueber `/api/chat` UND `/v1/chat/completions` (der Endpunkt, den Hermes
   tatsaechlich benutzt). Beide muessen bestehen, nicht nur einer.
4. **Tool-Calling, offene Aufforderung**: dieselbe Pruefung, aber mit
   persona-artiger, impliziter Aufforderung statt explizitem Befehl. Kein
   hartes Ausschlusskriterium, aber entscheidend fuer den echten
   Hermes-Einsatz (siehe Lehre vom 22.07.2026 unten).
5. **Cache-Wiederverwendung ueber mehrere Turns**: verarbeitet ein zweiter
   Turn nur die neuen Token, oder wird bei wachsender Historie immer wieder
   (fast) alles neu verarbeitet? Betrifft vor allem Architekturen mit
   Sliding-Window-Attention (z.B. Gemma).
6. **RAM bei aktuellem Kontext**: Vergleichsrahmen: 30-GB-Box, geteilt mit
   anderen Nutzern (siehe `docker-compose.yml` auf der Ollama-Box).
7. **Prefill-Tempo**: realistische Dossier-Groesse (~9000 Token Fuelltext).

Fuer andere Zwecke (z.B. ein reiner Chat-/Vision-Assistent ohne
Tool-Calling): Kriterien 3/4 entfallen, Kriterium 1 kann niedriger liegen,
5/6 bleiben sinnvoll. Details im Docstring von `bench_model.py`.

## Ergebnis-Historie

| Datum | Modell | 1 Kontext | 2 Denken | 3 Tool direktiv | 4 Tool offen | 5 Cache | 6 RAM | 7 Tempo | Ergebnis |
|---|---|---|---|---|---|---|---|---|---|
| 2026-07-21 | `llama3.1:8b` | 131072 OK | nein | **NEIN** (narriert nur) | n/a | n/a | n/a | n/a | disqualifiziert |
| 2026-07-21 | `qwen3:30b-a3b-instruct-2507-q4_K_M` | OK | nein | JA | nicht getestet (Kriterium kam erst 22.07. dazu) | nicht getestet | 22,6 GB (q8_0 KV) | 10-30 Tok/s (CPU-last-abhaengig) | bestanden, aber schwer/langsam |
| 2026-07-22 | `gemma4:e4b` | 131072 OK | nein | JA (beide Endpunkte) | **NEIN** (siehe unten) | uneinheitlich: reprocessing bei einem Turn beobachtet, Checkpoint-Wiederverwendung bei einem anderen auch gesehen | 10,1 GB | 40 Tok/s (isoliert), 20-35 Tok/s unter Alltagslast | bestanden bei 1-3, **schwach bei 4** |

## Lehre vom 22.07.2026: die Luecke, die Kriterium 4 schliesst

`bench_model.py` pruefte Tool-Calling urspruenglich nur mit einem kurzen,
direktiven Befehl ("Ruf read_file JETZT auf, beschreib es nicht"). gemma4:e4b
bestand das zuverlaessig, ueber beide Endpunkte. Im echten Hermes-Discord-
Gespraech (offene Vorstellung, SOUL.md-Kontext, keine explizite
Werkzeug-Anweisung: "Hallo Neo, ich bin GiGi... Merk dir das.") narrierte das
Modell stattdessen selbstsicher "Ich speichere folgende Fakten im
memory-Store ab", ohne dass ein einziger `tool_calls`-Eintrag entstand, ueber
mehrere lange Turns hinweg.

Erste Vermutung: falscher Endpunkt (`bench_model.py` testete `/api/chat`,
Hermes nutzt `/v1/chat/completions`). Direkt nachgeprueft und **widerlegt**:
ein kurzer direktiver Befehl ueber `/v1/chat/completions` lieferte ebenfalls
einen echten, sauber strukturierten `tool_calls`-Eintrag. Der Endpunkt ist
also nicht die Ursache.

Tatsaechliche Erklaerung: **Prompt-Direktivitaet**. Bei einem knappen,
expliziten Befehl ruft gemma4:e4b das Werkzeug zuverlaessig auf. Bei einer
offenen, persona-artigen Aufforderung faellt es zurueck ins Erzaehlen,
obwohl der Text ueberzeugend klingt ("ich speichere das jetzt"). Deshalb
Kriterium 4 als eigene Pruefung, getrennt von Kriterium 3.

**Konsequenz fuer den Betrieb:** Wichtige Anweisungen an Neo (z.B.
Gedaechtnis-Eintraege) sollten den Werkzeugaufruf explizit benennen ("ruf
jetzt `write_file` auf mit genau diesem Inhalt"), nicht nur implizieren.
Diese Erkenntnis ist auch in `memory_neo/modell.md` festgehalten (von Claude
Code geschrieben, nicht von Neo selbst, siehe Begruendung dort).
