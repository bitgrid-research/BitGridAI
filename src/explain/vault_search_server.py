"""
VaultSearchServer — semantische Suche über den Obsidian-Wissens-Vault fuer den
DEV-BitHamster (Hermes-Agent, siehe docs/development/36_ai_tooling/hermes-bithamster/).

Der Agent laeuft in einer ephemeren Code-Execution-Sandbox ohne verlaesslichen
Datei-Zugriff auf den Host. Er erreicht Ollama und das Web aber schon heute per
HTTP aus der Sandbox heraus (siehe explain_agent.py::_call_ollama) — deshalb ist
dieser Dienst ein HTTP-Endpoint, kein Datei-Drop in die Sandbox.

Read-only auf den Vault (Bind-Mount, siehe scripts/deploy_vault_search.sh). Kein
Einfluss auf core/ oder Aktoren — reine Wissenssuche, dieselbe Rechtfertigung wie
der Rest von explain/ ("ML/SLM/XAI nur in explain/, solange kein Einfluss auf eine
Steuerentscheidung und lokal", CLAUDE.md).

Index liegt nur im Speicher, wird bei Start und bei POST /reindex neu aufgebaut
(kein Volume, kein Cache-Invalidierungs-Bug moeglich). Quelle der Chunks: die
vom Sync bereits mit YAML-Frontmatter (title/group/tags/source) versehenen
Vault-Dateien, siehe scripts/sync_obsidian.py::render_text.

CLI:
    python -m src.explain.vault_search_server

Env-Vars (aus .env):
    VAULT_PATH          — Pfad zum gemounteten Vault (default: /vault)
    VAULT_SEARCH_PORT    — Listen-Port (default: 8767)
    OLLAMA_HOST          — z.B. http://umbrel.local:11434
    OLLAMA_EMBED_MODEL   — Embedding-Modell (default: nomic-embed-text)
    OLLAMA_TIMEOUT_SEC   — Timeout fuer einzelne Anfragen (default: 30)
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import numpy as np
import yaml

log = logging.getLogger(__name__)

_DEFAULT_PORT = 8767
_DEFAULT_EMBED_MODEL = "nomic-embed-text"
_BATCH_SIZE = 32
_MAX_CHUNK_CHARS = 2000
_MIN_CHUNK_CHARS = 40
_HEADING_SPLIT_RE = re.compile(r"\n(?=## )")


@dataclass
class Chunk:
    source: str
    title: str
    group: str
    tags: list[str]
    text: str


def parse_note(path: Path) -> tuple[dict[str, Any], str]:
    """Trennt YAML-Frontmatter (von sync_obsidian.py geschrieben) vom Body."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            try:
                frontmatter = yaml.safe_load(text[4:end]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = text[end + 5 :]
            return frontmatter, body
    return {}, text


def chunk_body(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> list[str]:
    """Splittet an ## -Ueberschriften, faellt bei zu langen Abschnitten auf
    Absatzgrenzen zurueck. Kein Overlap noetig bei dieser Vault-Groesse."""
    chunks: list[str] = []
    for part in _HEADING_SPLIT_RE.split(text):
        part = part.strip()
        if not part:
            continue
        if len(part) <= max_chars:
            chunks.append(part)
            continue
        buf = ""
        for para in part.split("\n\n"):
            candidate = f"{buf}\n\n{para}" if buf else para
            if len(candidate) <= max_chars:
                buf = candidate
            else:
                if buf:
                    chunks.append(buf)
                buf = para
        if buf:
            chunks.append(buf)
    return chunks


def load_chunks(vault_path: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for md_file in sorted(vault_path.rglob("*.md")):
        if ".obsidian" in md_file.parts:
            continue
        frontmatter, body = parse_note(md_file)
        title = str(frontmatter.get("title") or md_file.stem)
        group = str(frontmatter.get("group") or "root")
        tags = [str(t) for t in (frontmatter.get("tags") or [])]
        source = str(frontmatter.get("source") or md_file.name)
        for piece in chunk_body(body):
            if len(piece) < _MIN_CHUNK_CHARS:
                continue
            chunks.append(
                Chunk(source=source, title=title, group=group, tags=tags, text=piece)
            )
    return chunks


def embed_batch(texts: list[str], timeout_sec: int) -> list[list[float]]:
    host = os.getenv("OLLAMA_HOST", "").rstrip("/")
    model = os.getenv("OLLAMA_EMBED_MODEL", _DEFAULT_EMBED_MODEL)
    if not host:
        raise RuntimeError("OLLAMA_HOST ist nicht gesetzt")
    body = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(
        f"{host}/api/embed",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        data: dict[str, Any] = json.loads(resp.read())
    embeddings: list[list[float]] = data["embeddings"]
    return embeddings


class VaultIndex:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._vectors: np.ndarray[Any, Any] | None = None
        self._lock = threading.Lock()

    def build(self) -> int:
        vault_path = Path(os.getenv("VAULT_PATH", "/vault"))
        timeout_sec = (
            int(os.getenv("OLLAMA_TIMEOUT_SEC", "30")) * 4
        )  # Batch, nicht Einzelanfrage
        chunks = load_chunks(vault_path)
        vectors: list[list[float]] = []
        for i in range(0, len(chunks), _BATCH_SIZE):
            batch = chunks[i : i + _BATCH_SIZE]
            vectors.extend(embed_batch([c.text for c in batch], timeout_sec))

        arr = np.array(vectors, dtype=np.float32)
        if arr.size:
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            arr = arr / norms

        with self._lock:
            self._chunks = chunks
            self._vectors = arr
        return len(chunks)

    def search(self, query: str, k: int) -> list[dict[str, Any]]:
        with self._lock:
            chunks, vectors = self._chunks, self._vectors
        if vectors is None or not chunks:
            return []
        timeout_sec = int(os.getenv("OLLAMA_TIMEOUT_SEC", "30"))
        q_vec = np.array(embed_batch([query], timeout_sec)[0], dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_vec = q_vec / q_norm
        scores = vectors @ q_vec
        top_idx = np.argsort(-scores)[:k]
        return [
            {
                "source": chunks[idx].source,
                "title": chunks[idx].title,
                "group": chunks[idx].group,
                "tags": chunks[idx].tags,
                "text": chunks[idx].text,
                "score": float(scores[idx]),
            }
            for idx in top_idx
        ]


_index = VaultIndex()


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/search":
            self._respond(404, {"ok": False, "detail": "unbekannter Pfad"})
            return
        params = urllib.parse.parse_qs(parsed.query)
        query = (params.get("q") or [""])[0].strip()
        if not query:
            self._respond(400, {"ok": False, "detail": "Parameter q fehlt"})
            return
        try:
            k = int((params.get("k") or ["5"])[0])
        except ValueError:
            k = 5
        try:
            results = _index.search(query, k)
            self._respond(200, {"ok": True, "results": results})
        except Exception as exc:  # noqa: BLE001 - darf den Server nicht crashen
            log.exception("Suche fehlgeschlagen")
            self._respond(500, {"ok": False, "detail": str(exc)})

    def do_POST(self) -> None:
        if self.path != "/reindex":
            self._respond(404, {"ok": False, "detail": "unbekannter Pfad"})
            return
        try:
            count = _index.build()
            self._respond(200, {"ok": True, "chunks": count})
        except Exception as exc:  # noqa: BLE001 - darf den Server nicht crashen
            log.exception("Reindex fehlgeschlagen")
            self._respond(500, {"ok": False, "detail": str(exc)})

    def _respond(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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
    port = int(os.getenv("VAULT_SEARCH_PORT", str(_DEFAULT_PORT)))

    log.info("Baue initialen Index...")
    count = _index.build()
    log.info("Index bereit: %d Chunks", count)

    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    log.info("Vault-Search-Server auf Port %d (GET /search?q=..., POST /reindex)", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
