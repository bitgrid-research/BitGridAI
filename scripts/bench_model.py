"""
bench_model.py: vergleichbare Kennzahlen fuer einen Modell-Kandidaten.

Formalisiert die Ad-hoc-Tests vom 2026-07-21/22 (llama3.1:8b faellt durch
narratives statt echtes Tool-Calling durch, qwen3:30b besteht) in EIN
wiederholbares Skript, damit ein neuer Kandidat (z.B. gemma4:e4b) sich mit
denselben Massstaeben pruefen laesst, statt jedes Mal von Hand zu testen.

Lehre vom 22.07.2026, Nachmittag: gemma4:e4b bestand den urspruenglichen
Tool-Calling-Test (kurzer, direktiver Befehl), versagte aber in einem echten
Hermes-Discord-Gespraech mit offener Persona-Prosa (SOUL.md-Kontext, keine
explizite Werkzeug-Anweisung) - narrierte "ich speichere das", ohne
`write_file` wirklich aufzurufen. Erste Vermutung war ein falscher Endpunkt
(bench_model.py testete /api/chat, Hermes nutzt /v1/chat/completions), das
wurde aber direkt widerlegt: /v1/chat/completions lieferte bei einem kurzen
direktiven Testbefehl ebenfalls einen echten tool_calls-Eintrag. Die
tatsaechliche Luecke ist Kriterium 3 unten (offene vs. direktive Aufforderung),
nicht der Endpunkt. Ergebnis-Historie: `docs/development/36_ai_tooling/neo/BENCHMARKS.md`.

Prueft in dieser Reihenfolge, 1-2 sind harte Ausschlusskriterien (frueher Abbruch):

  1. Nativer Kontext         >= 64000, sonst disqualifiziert (Hermes-Minimum)
  2. Denk-Mechanismus         Template-Check: erzwingt es <think> vor der Antwort?
  2b. Tool-Calling direktiv   ECHTER tool_calls-Eintrag bei explizitem Befehl,
                              geprueft ueber /api/chat UND /v1/chat/completions
                              (der Endpunkt, den Hermes tatsaechlich benutzt)
  3. Tool-Calling offen       dieselbe Pruefung, aber mit persona-artiger,
                              impliziter Aufforderung statt explizitem Befehl.
                              Kein hartes Ausschlusskriterium (nur Warnung),
                              aber entscheidend fuer echten Hermes-Einsatz.
  4. Cache-Wiederverwendung   zwei Turns mit wachsender Historie: verarbeitet
                              Turn 2 nur die neuen Token oder alles neu (SWA-
                              Falle bei manchen Architekturen wie Gemma)?
  5. RAM bei 64k Kontext      zum Vergleich mit der 30-GB-Box
  6. Prefill-Tempo            realistische Dossier-Groesse (~9000 Token Fuelltext)

Fuer andere Zwecke als Neos agentische Nutzung (z.B. ein reiner Chat- oder
Vision-Assistent ohne Tool-Calling): Kriterien 2b/3 (Tool-Calling) entfallen
komplett, Kriterium 1 (Kontext-Untergrenze 64k) kann niedriger angesetzt
werden, ein Chat braucht selten so viel Historie. Kriterien 5/6 (RAM/Tempo)
bleiben sinnvoll fuer jede Nutzung auf derselben Box. Tonfall/Persoenlichkeit
und ggf. Bildverstaendnis (bei Vision-Modellen) sind eigene Kriterien, die
dieses Skript nicht abdeckt.

WICHTIG: laedt das Modell auf der Ollama-Box. Bei einer knappen
OLLAMA_MAX_LOADED_MODELS-Grenze wirft das ggf. ein anderes laufendes Modell
raus - also nie waehrend eines echten Nachtforscher-Laufs ausfuehren.

    python scripts/bench_model.py gemma4:e4b
    python scripts/bench_model.py qwen3:4b-instruct --kein-pull

Env (.env): ollama_ip, ollama_user, ollama_pw (oder OLLAMA_HOST fuer reine API-Calls)
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

from dotenv import dotenv_values

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENV = dotenv_values(".env")
OLLAMA = (ENV.get("OLLAMA_HOST") or "http://192.168.178.104:11434").rstrip("/")
MINDEST_KONTEXT = 64_000


def api(
    path: str,
    payload: dict[str, object] | None = None,
    methode: str = "GET",
    timeout: float = 60,
) -> dict[str, Any]:
    daten = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        OLLAMA + path,
        data=daten,
        headers={"Content-Type": "application/json"},
        method=methode,
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())  # type: ignore[no-any-return]


def pull(modell: str) -> None:
    print(f"Ziehe {modell} ...", flush=True)
    req = urllib.request.Request(
        OLLAMA + "/api/pull",
        data=json.dumps({"model": modell, "stream": True}).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=1800) as r:
        for zeile in r:
            d = json.loads(zeile.decode())
            if d.get("error"):
                raise SystemExit(f"Pull fehlgeschlagen: {d['error']}")
    print(f"  fertig nach {int(time.time() - t0)}s")


def pruefe_kontext_und_denken(modell: str) -> tuple[int, bool]:
    d = api("/api/show", {"model": modell}, "POST", timeout=30)
    mi = d.get("model_info", {})
    nativer_kontext = 0
    for schluessel, wert in mi.items():
        if schluessel.endswith(".context_length"):
            nativer_kontext = int(wert)
            break
    tmpl = d.get("template", "")
    erzwingt_denken = tmpl.rstrip().endswith("<think>") or "<think>\n{{ end }}" in tmpl
    return nativer_kontext, erzwingt_denken


def _tool_schema() -> list[dict[str, object]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file from disk",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        }
    ]


_TOOL_PROMPT = (
    "Lies /opt/data/vault/00_START_HIER.md mit dem Werkzeug read_file. "
    "Rufe das Werkzeug auf, beschreibe es nicht."
)


def pruefe_tool_calling_nativ(modell: str) -> tuple[bool, str]:
    """Ollamas natives /api/chat. NICHT der Endpunkt, den Hermes benutzt."""
    d = api(
        "/api/chat",
        {
            "model": modell,
            "stream": False,
            "keep_alive": -1,
            "messages": [{"role": "user", "content": _TOOL_PROMPT}],
            "tools": _tool_schema(),
            "options": {"num_ctx": min(MINDEST_KONTEXT, 65536), "num_predict": 200},
        },
        "POST",
        timeout=900,
    )
    calls = d["message"].get("tool_calls") or []
    inhalt = d["message"].get("content", "")
    return bool(calls), inhalt[:120]


def pruefe_tool_calling_openai(modell: str) -> tuple[bool, str]:
    """/v1/chat/completions, der Endpunkt, den Hermes tatsaechlich benutzt
    (api_mode: chat_completions). Ollamas OpenAI-Kompatibilitaetsschicht kann
    bei manchen Modellfamilien (u.a. Gemma, siehe offizielle Hermes-Docs)
    Tool-Calls als Klartext-JSON statt als echtes tool_calls-Feld ausgeben,
    obwohl /api/chat sauber funktioniert. Deshalb beide Endpunkte pruefen,
    nicht nur einen."""
    d = api(
        "/v1/chat/completions",
        {
            "model": modell,
            "stream": False,
            "messages": [{"role": "user", "content": _TOOL_PROMPT}],
            "tools": _tool_schema(),
            "max_tokens": 200,
        },
        "POST",
        timeout=900,
    )
    msg = d["choices"][0]["message"]
    calls = msg.get("tool_calls") or []
    inhalt = msg.get("content", "") or ""
    return bool(calls), inhalt[:120]


def pruefe_tool_calling_offen(modell: str) -> tuple[bool, str]:
    """Offene, persona-artige Aufforderung statt direktivem Befehl. Genau die
    Luecke, die gemma4:e4b am 22.07.2026 in einem echten Hermes-Gespraech
    durchfallen liess: der Text behauptete narrativ "ich speichere das",
    ohne dass ein echter tool_calls-Eintrag entstand, obwohl derselbe Endpunkt
    bei einem kurzen direktiven Befehl (pruefe_tool_calling_openai) sauber
    funktioniert. Diese Pruefung deckt genau diesen Unterschied ab."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file on disk",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        }
    ]
    prompt = (
        "Du bist ein Assistent mit einem persoenlichen Gedaechtnisordner "
        "unter /opt/data/memory/. Ein Nutzer schreibt dir: 'Hallo, ich bin "
        "Alex, ich leite dieses Projekt. Merk dir das.' Halte fest, was du "
        "ueber Alex weisst, und geh dann auf seine Nachricht ein."
    )
    d = api(
        "/v1/chat/completions",
        {
            "model": modell,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "tools": tools,
            "max_tokens": 400,
        },
        "POST",
        timeout=900,
    )
    msg = d["choices"][0]["message"]
    calls = msg.get("tool_calls") or []
    inhalt = msg.get("content", "") or ""
    return bool(calls), inhalt[:200]


def pruefe_cache_wiederverwendung(modell: str) -> tuple[bool, int, int]:
    """Zwei aufeinanderfolgende Turns mit wachsender Historie: prueft, ob
    Turn 2 den Kontext-Praefix von Turn 1 wiederverwendet (kleiner
    prompt_eval_count, nur die neuen Token) oder komplett neu verarbeitet
    (SWA-Falle bei Gemma, siehe Ollama-Logs vom 22.07.2026: "forcing full
    prompt re-processing due to lack of cache data"). Gibt zurueck:
    (wiederverwendet, prompt_eval_count von Turn 2, geschaetzte Token-Summe
    aus Turn 1 + Turn 2 zusammen)."""
    fuellung_1 = "Der Speicher wird nach SoC-Schwellen geregelt. " * 200
    erste_nachricht = {"role": "user", "content": fuellung_1 + "Antworte mit OK."}
    d1 = api(
        "/api/chat",
        {
            "model": modell,
            "stream": False,
            "messages": [erste_nachricht],
            "options": {"num_predict": 10},
        },
        "POST",
        timeout=900,
    )
    eval_1 = int(d1.get("prompt_eval_count", 0))
    antwort_1 = d1["message"]["content"]

    fuellung_2 = "Der Miner folgt der Leiter aus fuenf Prioritaeten. " * 50
    messages = [
        erste_nachricht,
        {"role": "assistant", "content": antwort_1},
        {"role": "user", "content": fuellung_2 + "Antworte mit OK."},
    ]
    d2 = api(
        "/api/chat",
        {
            "model": modell,
            "stream": False,
            "messages": messages,
            "options": {"num_predict": 10},
        },
        "POST",
        timeout=900,
    )
    eval_2 = int(d2.get("prompt_eval_count", 0))
    # Wenn Turn 2 den Cache wiederverwendet, muss er ungefaehr nur die neuen
    # Token verarbeiten (deutlich weniger als Turn 1 + Turn 2 zusammen).
    # Reprocessing bedeutet: Turn 2 verarbeitet nochmal (fast) alles von Turn 1.
    wiederverwendet = eval_2 < eval_1 * 0.7
    return wiederverwendet, eval_2, eval_1 + eval_2


def ram_bei_64k(modell: str) -> float:
    ps = api("/api/ps")
    for m in ps.get("models", []):
        if m["name"] == modell:
            return float(m.get("size", 0)) / 1e9
    return -1.0


def prefill_tempo(modell: str) -> tuple[float, bool]:
    fuellung = (
        "Der Speicher wird nach SoC-Schwellen geregelt und der Miner folgt der Leiter. "
        * 350
    )
    prompt = (
        "MERKSATZ: Das Codewort lautet Vergleichstest.\n\n"
        + fuellung
        + "\n\nWelches Codewort steht im MERKSATZ ganz am Anfang? Antworte mit nur dem Wort."
    )
    t0 = time.time()
    d = api(
        "/api/chat",
        {
            "model": modell,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"num_predict": 20},
        },
        "POST",
        timeout=1800,
    )
    dt = time.time() - t0
    pc = d.get("prompt_eval_count", 0)
    pd = d.get("prompt_eval_duration", 1) / 1e9
    korrekt = "ergleichstest" in d["message"]["content"]
    return (pc / pd if pd else 0.0), korrekt


def main() -> None:
    p = argparse.ArgumentParser(
        description="Vergleichbare Kennzahlen fuer einen Modell-Kandidaten"
    )
    p.add_argument("modell", help="Ollama-Tag, z.B. gemma4:e4b")
    p.add_argument(
        "--kein-pull", action="store_true", help="Modell liegt schon auf der Box"
    )
    args = p.parse_args()

    print(f"=== Vergleichstest: {args.modell} ===\n")

    if not args.kein_pull:
        pull(args.modell)

    print("\n[1] Nativer Kontext & Denk-Mechanismus")
    kontext, denkt = pruefe_kontext_und_denken(args.modell)
    kontext_ok = kontext >= MINDEST_KONTEXT
    print(
        f"    nativer Kontext:  {kontext} {'OK' if kontext_ok else f'ZU KLEIN (< {MINDEST_KONTEXT})'}"
    )
    print(
        f"    erzwingt <think>: {denkt} {'(Risiko, siehe llama3.1-Vorfall)' if denkt else ''}"
    )
    if not kontext_ok:
        print(
            "\n=> DISQUALIFIZIERT: Kontext unter Hermes-Minimum, keine weiteren Tests noetig."
        )
        return

    print(
        "\n[2] Tool-Calling: BEIDE Endpunkte, nicht nur einen (Lehre 22.07.: gemma4:e4b"
    )
    print("    bestand /api/chat, versagte aber in echten Hermes-Gespraechen)")
    calls_ok_nativ, inhalt_nativ = pruefe_tool_calling_nativ(args.modell)
    print(f"    /api/chat (nativ):            {'JA' if calls_ok_nativ else 'NEIN'}")
    calls_ok_openai, inhalt_openai = pruefe_tool_calling_openai(args.modell)
    print(f"    /v1/chat/completions (Hermes): {'JA' if calls_ok_openai else 'NEIN'}")
    if not calls_ok_openai:
        print(f"    stattdessen im content: {inhalt_openai!r}")
        print(
            "\n=> DISQUALIFIZIERT: kein echtes Tool-Calling ueber den Endpunkt, den Hermes "
            "tatsaechlich benutzt. Ein JA bei /api/chat allein reicht nicht."
        )
        return
    calls_ok = calls_ok_openai
    inhalt = inhalt_openai

    print("\n[3] Tool-Calling bei OFFENER Aufforderung (nicht nur direktiv)")
    offen_ok, offen_inhalt = pruefe_tool_calling_offen(args.modell)
    print(f"    echter Aufruf: {'JA' if offen_ok else 'NEIN'}")
    if not offen_ok:
        print(f"    stattdessen im content: {offen_inhalt!r}")
        print(
            "\n=> WARNUNG, kein hartes Ausschlusskriterium: ruft bei einem direktiven "
            "Befehl echte Tools auf, aber nicht bei offener Persona-Prosa. Genau die "
            "Luecke vom 22.07.2026 (siehe BENCHMARKS.md). Wichtige Anweisungen an ein "
            "solches Modell muessen den Werkzeugaufruf explizit benennen."
        )

    print("\n[4] Cache-Wiederverwendung ueber zwei Turns")
    cache_ok, eval_2, gesamt = pruefe_cache_wiederverwendung(args.modell)
    print(
        f"    Turn 2 verarbeitet {eval_2} Token neu (Gesamt ueber beide Turns: {gesamt})"
    )
    print(
        f"    {'wiederverwendet Cache' if cache_ok else 'WARNUNG: verarbeitet fast alles neu (SWA-Falle?)'}"
    )

    print("\n[5] RAM bei aktuellem Kontext")
    ram = ram_bei_64k(args.modell)
    print(f"    {ram:.1f} GB (30-GB-Box zum Vergleich)")

    print("\n[6] Prefill-Tempo (realistische Dossier-Groesse, ~9000 Token)")
    tempo, korrekt = prefill_tempo(args.modell)
    print(
        f"    {tempo:.0f} Tok/s, Merksatz korrekt erinnert: {'ja' if korrekt else 'NEIN'}"
    )

    print(f"\n=== Ergebnis {args.modell}: BESTEHT alle harten Ausschlusskriterien ===")
    print(
        f"    Kontext {kontext} | Tool-Calling (direktiv) ok | "
        f"offene Aufforderung: {'ok' if offen_ok else 'SCHWACH'} | "
        f"Cache: {'ok' if cache_ok else 'SCHWACH'} | RAM {ram:.1f} GB | "
        f"Prefill {tempo:.0f} Tok/s"
    )


if __name__ == "__main__":
    main()
