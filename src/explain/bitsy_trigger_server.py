"""
BitsyTriggerServer — HTTP-Listener + eingebauter periodischer Takt fuer die
Bitsy-Erklaerschicht (src/explain/bitsy_status.py). Ersetzt zwei fragile
Windows-Scheduled-Tasks (Cron + Button-Server) durch einen einzigen Docker-
Container mit `restart: unless-stopped` (infra/docker-compose.yml), damit die
Erklaerung nicht mehr vom Dev-Rechner abhaengt (z.B. ein versehentlich
geschlossenes Konsolenfenster).

Drei Aufgaben in einem Prozess:
1. HTTP POST /trigger — fuer den "Jetzt aktualisieren"-Button im ₿itsy-Tab
   (HA rest_command.bitsy_trigger, configuration.yaml).
2. HTTP POST /ask — fuer den ₿itsy-Chat (Baustein 3): Freitextfrage rein,
   Antwort synchron zurueck (HA rest_command.bitsy_ask + response_variable,
   packages/bitsy_chat.yaml). Bewusst nur gegen Ollama direkt, kein Hermes-
   Agent-Framework (SYSTEM_PROMPT.md, "kein externer Chat-Kanal an diesem
   Agenten" — Entscheidung 2026-07-12).
3. Hintergrund-Thread, der bitsy_status alle BITSY_INTERVAL_SEC Sekunden
   von selbst auslöst (Default 600s = 10 Minuten).

Kein Auth: nur im vertrauten Heim-LAN gedacht, dieselbe Vertrauensgrenze wie
Ollama und HA selbst in diesem Setup. Kein Steuerpfad — startet nur einen
Lese-/Erklaer-Durchlauf (explain/), fasst core/ nicht an.

CLI:
    python -m src.explain.bitsy_trigger_server

Env-Vars (aus .env):
    BITSY_TRIGGER_PORT   — Listen-Port (default: 8766; 8765 ist fuer den
                           geplanten bitgrid-ui-Dienst reserviert, siehe
                           infra/docker-compose.override.yml)
    BITSY_INTERVAL_SEC   — periodischer Takt in Sekunden (default: 600)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.explain import bitsy_status

log = logging.getLogger(__name__)

_DEFAULT_PORT = 8766
_DEFAULT_INTERVAL_SEC = 600


# Verhindert, dass Button-Klick und periodischer Takt gleichzeitig laufen
# (zwei parallele bitsy_status-Laeufe waeren zwar nicht gefaehrlich, aber
# unnoetig und koennten sich beim MQTT-Publish ueberschneiden).
_run_lock = threading.Lock()


def _run_once(source: str) -> tuple[bool, str]:
    with _run_lock:
        try:
            bitsy_status.main()
            return True, "ok"
        except SystemExit as exc:
            return False, f"bitsy_status beendet mit Code {exc.code}"
        except Exception as exc:  # noqa: BLE001 - darf den Aufrufer nicht crashen
            log.exception("Unerwarteter Fehler im Bitsy-Status-Lauf (%s)", source)
            return False, str(exc)


def _periodic_loop(interval_sec: int) -> None:
    log.info("Periodischer Takt aktiv: alle %d Sekunden", interval_sec)
    while True:
        time.sleep(interval_sec)
        ok, detail = _run_once("periodisch")
        log.info("Periodischer Lauf: ok=%s (%s)", ok, detail)


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path == "/trigger":
            ok, detail = _run_once("button")
            self._respond(200 if ok else 500, {"ok": ok, "detail": detail})
            return

        if self.path == "/ask":
            self._handle_ask()
            return

        self._respond(404, {"ok": False, "detail": "unbekannter Pfad"})

    def _handle_ask(self) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = {}
        question = str(payload.get("question", "")).strip()
        if not question:
            self._respond(400, {"answer": "", "error": "keine Frage angegeben"})
            return

        # Gleicher Lock wie der periodische Takt/Button: verhindert, dass eine
        # Chat-Frage und der 10-Minuten-Status gleichzeitig HA/Ollama abfragen.
        with _run_lock:
            answer = bitsy_status.ask(question)
        self._respond(200, {"answer": answer})

    def _respond(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        log.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    port = int(os.getenv("BITSY_TRIGGER_PORT", str(_DEFAULT_PORT)))
    interval_sec = int(os.getenv("BITSY_INTERVAL_SEC", str(_DEFAULT_INTERVAL_SEC)))

    threading.Thread(target=_periodic_loop, args=(interval_sec,), daemon=True).start()

    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    log.info("Bitsy-Trigger-Server auf Port %d (POST /trigger)", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
