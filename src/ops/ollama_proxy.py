"""
OllamaProxy — Mitschnitt zwischen Agent und Sprachmodell.

Sitzt zwischen Hermes und Ollama und protokolliert jede Anfrage: welches
Modell, wie viele Nachrichten, wie gross der Prompt, **welche Werkzeuge
mitgeschickt wurden**, was zurueckkam und wie lange es dauerte.

Entstanden am 2026-07-21 aus einem verlorenen Abend: Hermes schickte dem Modell
stundenlang `Tools: 0`, weil sein Terminal-Backend nicht startete. Von aussen
sah das aus wie ein Modell, das halluziniert. Sichtbar wurde es erst, als der
Datenverkehr selbst im Log stand. Wer Agenten baut, braucht diese Sicht, sonst
debuggt er Vermutungen.

Er veraendert nichts am Verkehr, er reicht ihn nur durch. Streaming wird
unterstuetzt: Chunks gehen sofort weiter, die Auswertung passiert nebenher.

CLI:
    python -m src.ops.ollama_proxy

Env:
    OLLAMA_UPSTREAM     Ziel, z.B. http://<ollama-host>:11434 (eigener Host,
                        nicht Umbrel — siehe Projekt-Doku zur Infrastruktur).
                        Pflichtangabe, kein Default.
    PROXY_PORT          Listen-Port (default: 11435)
    PROXY_LOG           Logdatei (default: /data/ollama_proxy.log)
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

log = logging.getLogger("ollama_proxy")

_DEFAULT_PORT = 11435
_MAX_PREVIEW = 220


def _approx_tokens(text: str) -> int:
    """Grobe Schaetzung: 4 Zeichen je Token. Genau genug, um Groessenordnungen
    zu erkennen, und ohne Tokenizer-Abhaengigkeit."""
    return len(text) // 4


def _summarize_request(path: str, body: bytes) -> dict[str, Any]:
    """Zieht aus dem Anfrage-Body die Kennzahlen, die beim Debuggen zaehlen."""
    info: dict[str, Any] = {"pfad": path, "bytes": len(body)}
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return info

    info["modell"] = data.get("model", "?")
    messages = data.get("messages") or []
    info["nachrichten"] = len(messages)

    gesamt = ""
    for m in messages:
        inhalt = m.get("content")
        if isinstance(inhalt, str):
            gesamt += inhalt
    if "prompt" in data:
        gesamt += str(data["prompt"])
    info["prompt_zeichen"] = len(gesamt)
    info["prompt_token_ca"] = _approx_tokens(gesamt)

    # Der entscheidende Wert: bekommt das Modell ueberhaupt Werkzeuge?
    tools = data.get("tools") or []
    info["werkzeuge"] = len(tools)
    info["werkzeug_namen"] = [
        (t.get("function") or {}).get("name", "?") for t in tools
    ][:8]

    opts = data.get("options") or {}
    if "num_ctx" in opts:
        info["num_ctx"] = opts["num_ctx"]
    if data.get("stream"):
        info["stream"] = True
    return info


def _summarize_response(body: bytes, streamed: bool) -> dict[str, Any]:
    """Wertet die Antwort aus. Bei Streams die gesammelten Chunks."""
    info: dict[str, Any] = {"antwort_bytes": len(body)}
    text = body.decode("utf-8", errors="replace")

    if streamed:
        # SSE: mehrere "data: {...}"-Zeilen. Wir zaehlen Werkzeugaufrufe und
        # sammeln den Text, statt jeden Chunk einzeln zu protokollieren.
        inhalt = ""
        tool_calls = 0
        for zeile in text.splitlines():
            if not zeile.startswith("data:"):
                continue
            rest = zeile[5:].strip()
            if rest in ("", "[DONE]"):
                continue
            try:
                chunk = json.loads(rest)
            except json.JSONDecodeError:
                continue
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                if delta.get("content"):
                    inhalt += delta["content"]
                if delta.get("tool_calls"):
                    tool_calls += len(delta["tool_calls"])
        info["tool_calls"] = tool_calls
        info["text_zeichen"] = len(inhalt)
        info["text_anfang"] = inhalt[:_MAX_PREVIEW]
        return info

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        info["text_anfang"] = text[:_MAX_PREVIEW]
        return info

    if "choices" in data:
        msg = (data["choices"][0] or {}).get("message") or {}
        info["tool_calls"] = len(msg.get("tool_calls") or [])
        info["text_anfang"] = (msg.get("content") or "")[:_MAX_PREVIEW]
    elif "response" in data:
        info["text_anfang"] = str(data["response"])[:_MAX_PREVIEW]
    for feld in ("prompt_eval_count", "eval_count"):
        if feld in data:
            info[feld] = data[feld]
    return info


class _Handler(BaseHTTPRequestHandler):
    upstream: str = ""
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:
        self._proxy("POST")

    def do_GET(self) -> None:
        self._proxy("GET")

    def _proxy(self, method: str) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""
        anfrage = _summarize_request(self.path, body)

        ziel = f"{self.upstream}{self.path}"
        kopf = {
            k: v
            for k, v in self.headers.items()
            if k.lower() not in ("host", "content-length", "connection")
        }
        req = urllib.request.Request(
            ziel, data=body or None, headers=kopf, method=method
        )

        start = time.monotonic()
        gesammelt = bytearray()
        streamed = False
        status = 502
        try:
            with urllib.request.urlopen(req, timeout=1800) as resp:
                status = resp.status
                ctype = resp.headers.get("Content-Type", "")
                streamed = "event-stream" in ctype or anfrage.get("stream", False)

                self.send_response(status)
                for k, v in resp.headers.items():
                    if k.lower() not in (
                        "transfer-encoding",
                        "content-length",
                        "connection",
                    ):
                        self.send_header(k, v)
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()

                while True:
                    stueck = resp.read(4096)
                    if not stueck:
                        break
                    gesammelt.extend(stueck)
                    self.wfile.write(f"{len(stueck):X}\r\n".encode())
                    self.wfile.write(stueck)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
                self.wfile.write(b"0\r\n\r\n")
        except urllib.error.HTTPError as exc:
            status = exc.code
            fehler = exc.read()
            gesammelt.extend(fehler)
            self.send_response(status)
            self.send_header("Content-Length", str(len(fehler)))
            self.end_headers()
            self.wfile.write(fehler)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            log.error("Upstream nicht erreichbar: %s", exc)
            meldung = json.dumps({"error": str(exc)}).encode()
            self.send_response(502)
            self.send_header("Content-Length", str(len(meldung)))
            self.end_headers()
            self.wfile.write(meldung)

        dauer = time.monotonic() - start
        antwort = _summarize_response(bytes(gesammelt), streamed)
        self._protokoll(status, dauer, anfrage, antwort)

    def _protokoll(
        self,
        status: int,
        dauer: float,
        anfrage: dict[str, Any],
        antwort: dict[str, Any],
    ) -> None:
        if anfrage["pfad"] in ("/api/tags", "/api/ps", "/api/show"):
            return  # Statusabfragen fluten sonst das Log

        kopf = (
            f"{anfrage['pfad']} {status} {dauer:6.1f}s "
            f"modell={anfrage.get('modell', '?')} "
            f"nachrichten={anfrage.get('nachrichten', 0)} "
            f"prompt~{anfrage.get('prompt_token_ca', 0)}T "
            f"WERKZEUGE={anfrage.get('werkzeuge', 0)} "
            f"tool_calls={antwort.get('tool_calls', 0)}"
        )
        if "num_ctx" in anfrage:
            kopf += f" num_ctx={anfrage['num_ctx']}"
        log.info(kopf)
        if anfrage.get("werkzeug_namen"):
            log.info("    werkzeuge: %s", ", ".join(anfrage["werkzeug_namen"]))
        if antwort.get("text_anfang"):
            log.info("    antwort:   %s", antwort["text_anfang"].replace("\n", " "))

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass  # eigenes Protokoll, kein Zugriffslog


def main() -> None:
    pfad = os.getenv("PROXY_LOG", "/data/ollama_proxy.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[logging.FileHandler(pfad, encoding="utf-8"), logging.StreamHandler()],
    )
    upstream = os.getenv("OLLAMA_UPSTREAM")
    if not upstream:
        raise SystemExit(
            "OLLAMA_UPSTREAM ist nicht gesetzt (z.B. http://<ollama-host>:11434)"
        )
    _Handler.upstream = upstream.rstrip("/")
    port = int(os.getenv("PROXY_PORT", str(_DEFAULT_PORT)))

    log.info("Mitschnitt aktiv: Port %d -> %s, Log %s", port, _Handler.upstream, pfad)
    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
