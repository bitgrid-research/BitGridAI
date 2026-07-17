"""
sync_obsidian.py — Sync .md-Wissen aus dem Repo in den Obsidian-Vault (GIGI-Umbrel).

Richtung ist immer Repo -> Vault. Git bleibt einzige Quelle der Wahrheit; es wird
nie etwas aus Obsidian zurückgelesen (kein zweiter Schreibpfad, keine Drift).

Quellen (siehe SOURCE_DIRS/SOURCE_FILES): docs/architecture, docs/development,
docs/research, docs/status, README.md, CLAUDE.md. Bewusst ausgeschlossen: docs/thesis/
(separater Overleaf-Workflow), INFRASTRUCTURE.md und .env (Zugangsdaten/IPs,
gehören nicht in ein Vault, das später ggf. RAG-Agenten wie Bitsy-Home füttert).

Jede Vault-Kopie bekommt beim Sync generierte YAML-Frontmatter (title/tags/source/
updated) vorangestellt — siehe render(). Das Repo selbst bleibt unangetastet: die
Metadaten sind ein Tooling-Anliegen des Vaults, kein Teil der arc42-Dokumente.

Zusätzlich wird bei jedem Sync ein Codebase-Überblick (docs/status/codebase.md im
Vault) aus den Modul-Docstrings unter src/ generiert — siehe generate_codebase_
overview(). Nur die erste Docstring-Zeile pro Datei, kein Code-Duplikat: der
Quellcode selbst bleibt Git, nicht Obsidian. Wird bei jedem Lauf frisch erzeugt,
nicht im Repo committed.

Ein lokaler State-Cache (.obsidian_sync_state.json, gitignored) merkt sich die
Hashes der Quell-Dateien (nicht der gerenderten Vault-Kopie), damit wiederholte
Läufe nur echte Inhaltsänderungen und Löschungen übertragen.

Verwendung:
    python scripts/sync_obsidian.py             # inkrementell
    python scripts/sync_obsidian.py --all       # voller Resync (State-Cache ignorieren)
    python scripts/sync_obsidian.py --watch     # inkrementell, danach alle --interval Sekunden erneut

Env (in .env, siehe .env.example):
    UMBREL_HOST_GIGI, UMBREL_USER_GIGI, UMBREL_SUDO_PASS_GIGI
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import posixpath
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import paramiko
import yaml
from dotenv import dotenv_values

_DEFAULT_VAULT_SEARCH_PORT = "8767"

if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
STATE_FILE = REPO_ROOT / ".obsidian_sync_state.json"
CODEBASE_REMOTE_REL = "docs/status/codebase.md"

REMOTE_VAULT_ROOT = (
    "/home/umbrel/umbrel/app-data/obsidian/data/config/"
    "BitGridAI_Obisdian_RAG_MVP/BitGridAI_MVP"
)

SOURCE_DIRS = [
    (REPO_ROOT / "docs" / "architecture", "docs/architecture"),
    (REPO_ROOT / "docs" / "development", "docs/development"),
    (REPO_ROOT / "docs" / "research", "docs/research"),
    (REPO_ROOT / "docs" / "status", "docs/status"),
]
SOURCE_FILES = [
    (REPO_ROOT / "README.md", "README.md"),
    (REPO_ROOT / "CLAUDE.md", "CLAUDE.md"),
    (REPO_ROOT / "docs" / "README.md", "docs/README.md"),
]


def collect_current() -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for local_dir, remote_prefix in SOURCE_DIRS:
        for path in sorted(local_dir.rglob("*.md")):
            rel = path.relative_to(local_dir).as_posix()
            mapping[f"{remote_prefix}/{rel}"] = path
    for local_file, remote_rel in SOURCE_FILES:
        if local_file.is_file():
            mapping[remote_rel] = local_file
    return mapping


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_LEADING_NUM_RE = re.compile(r"^\d+_*")


def extract_title(text: str, fallback: str) -> str:
    match = _TITLE_RE.search(text)
    if match:
        return match.group(1)
    return fallback


def _clean_segment(part: str) -> str:
    return _LEADING_NUM_RE.sub("", part).replace("_", "-").lower()


def derive_tags(remote_rel: str) -> list[str]:
    parts = remote_rel.split("/")[:-1]  # Verzeichnis-Segmente, Dateiname weglassen
    tags = [_clean_segment(p) for p in parts if p != "docs"]
    tags = [t for t in tags if t]
    return tags or ["root"]


def derive_group(remote_rel: str) -> str:
    """Oberster Ordnername unter docs/ (architecture/development/research), sonst 'root'."""
    parts = remote_rel.split("/")[:-1]
    for part in parts:
        if part != "docs":
            return _clean_segment(part) or "root"
    return "root"


def render_text(
    text: str,
    remote_rel: str,
    updated: str,
    title_fallback: str,
    extra_tags: list[str] | None = None,
) -> bytes:
    tags = derive_tags(remote_rel) + (extra_tags or [])
    frontmatter = {
        "title": extract_title(text, title_fallback),
        "group": derive_group(remote_rel),
        "tags": tags,
        "source": remote_rel,
        "updated": updated,
    }
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
    return f"---\n{header}---\n\n{text}".encode("utf-8")


def render(local_path: Path, remote_rel: str) -> bytes:
    text = local_path.read_text(encoding="utf-8")
    updated = date.fromtimestamp(local_path.stat().st_mtime).isoformat()
    return render_text(text, remote_rel, updated, local_path.stem.replace("_", " "))


_SKIP_DIRS = {"__pycache__"}


def module_docstring(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return ""
    doc = ast.get_docstring(tree)
    if not doc:
        return ""
    return doc.strip().splitlines()[0]


def generate_codebase_overview() -> tuple[str, str]:
    """Baut einen Docstring-basierten Überblick über src/. Gibt (Markdown, ISO-Datum
    der jüngsten erfassten Datei) zurück — kein Code-Duplikat, nur die erste
    Docstring-Zeile je Datei."""
    lines = [
        "# Codebase-Überblick — src/",
        "",
        "Generiert aus Modul-Docstrings bei jedem Sync (nicht im Repo committed, siehe",
        "scripts/sync_obsidian.py). Zeigt nur die erste Docstring-Zeile je Datei — für",
        "Details den Quellcode direkt lesen, nicht diese Seite als Wahrheit behandeln.",
        "",
    ]
    latest_mtime = 0.0
    for module_dir in sorted(p for p in SRC_ROOT.iterdir() if p.is_dir()):
        if module_dir.name in _SKIP_DIRS or module_dir.name.endswith(".egg-info"):
            continue
        py_files = sorted(
            p
            for p in module_dir.rglob("*.py")
            if not (_SKIP_DIRS & set(p.parts)) and p.name != "__init__.py"
        )
        if not py_files:
            continue
        lines.append(f"## `{module_dir.name}/`")
        lines.append("")
        lines.append("| Datei | Zweck |")
        lines.append("|---|---|")
        for py_file in py_files:
            latest_mtime = max(latest_mtime, py_file.stat().st_mtime)
            rel = py_file.relative_to(module_dir).as_posix()
            doc = module_docstring(py_file) or "_(kein Docstring)_"
            lines.append(f"| `{rel}` | {doc} |")
        lines.append("")
    updated = (
        date.fromtimestamp(latest_mtime).isoformat()
        if latest_mtime
        else date.today().isoformat()
    )
    return "\n".join(lines), updated


def load_state() -> dict[str, str]:
    if STATE_FILE.exists():
        result: dict[str, str] = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return result
    return {}


def save_state(state: dict[str, str]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def remote_mkdirs(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts = remote_dir.split("/")
    cur = ""
    for part in parts:
        if not part:
            continue
        cur += "/" + part
        try:
            sftp.stat(cur)
        except FileNotFoundError:
            sftp.mkdir(cur)


def connect() -> paramiko.SSHClient:
    env = dotenv_values(REPO_ROOT / ".env")
    host = (env.get("UMBREL_HOST_GIGI") or "").rstrip("/")
    user = env.get("UMBREL_USER_GIGI") or "umbrel"
    password = env.get("UMBREL_SUDO_PASS_GIGI") or ""
    if not host or not password:
        raise SystemExit(
            "UMBREL_HOST_GIGI / UMBREL_SUDO_PASS_GIGI fehlen in .env (siehe .env.example)"
        )
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    return client


def sync_once(force_all: bool) -> tuple[int, int, int]:
    client = connect()
    try:
        sftp = client.open_sftp()
        current = collect_current()
        state = {} if force_all else load_state()

        overview_text, overview_updated = generate_codebase_overview()
        overview_hash = hashlib.sha256(overview_text.encode("utf-8")).hexdigest()

        all_keys = set(current) | {CODEBASE_REMOTE_REL}
        to_delete = set(state) - all_keys
        uploaded = 0
        for remote_rel, local_path in current.items():
            digest = sha256_of(local_path)
            if not force_all and state.get(remote_rel) == digest:
                continue
            remote_path = posixpath.join(REMOTE_VAULT_ROOT, remote_rel)
            remote_mkdirs(sftp, posixpath.dirname(remote_path))
            with sftp.open(remote_path, "wb") as remote_file:
                remote_file.write(render(local_path, remote_rel))
            state[remote_rel] = digest
            uploaded += 1

        if force_all or state.get(CODEBASE_REMOTE_REL) != overview_hash:
            remote_path = posixpath.join(REMOTE_VAULT_ROOT, CODEBASE_REMOTE_REL)
            remote_mkdirs(sftp, posixpath.dirname(remote_path))
            with sftp.open(remote_path, "wb") as remote_file:
                remote_file.write(
                    render_text(
                        overview_text,
                        CODEBASE_REMOTE_REL,
                        overview_updated,
                        "Codebase-Überblick",
                        extra_tags=["codebase"],
                    )
                )
            state[CODEBASE_REMOTE_REL] = overview_hash
            uploaded += 1

        for remote_rel in to_delete:
            remote_path = posixpath.join(REMOTE_VAULT_ROOT, remote_rel)
            try:
                sftp.remove(remote_path)
            except FileNotFoundError:
                pass
            del state[remote_rel]

        save_state(state)
        sftp.close()
        return uploaded, len(to_delete), len(all_keys) - uploaded
    finally:
        client.close()


def trigger_reindex() -> None:
    """Best-effort POST /reindex an den vault-search-Dienst (src/explain/vault_search_server.py).
    Nicht fatal, falls der Dienst nicht laeuft/erreichbar ist — reiner Anhang an den
    ohnehin manuell angestossenen Sync, kein neuer Automatismus."""
    env = dotenv_values(REPO_ROOT / ".env")
    host = (env.get("UMBREL_HOST_GIGI") or "").rstrip("/")
    port = env.get("VAULT_SEARCH_PORT") or _DEFAULT_VAULT_SEARCH_PORT
    if not host:
        return
    req = urllib.request.Request(f"http://{host}:{port}/reindex", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        print(f"  ↳ vault-search reindexiert: {data.get('chunks', '?')} Chunks")
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        print(f"  ⚠ vault-search nicht erreichbar, Reindex übersprungen ({exc})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all", action="store_true", help="Voller Resync, State-Cache ignorieren"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Nach Erstlauf alle --interval Sekunden erneut syncen",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Polling-Intervall in Sekunden für --watch (default: 10)",
    )
    args = parser.parse_args()

    print(f"→ Sync nach {REMOTE_VAULT_ROOT}")
    uploaded, deleted, unchanged = sync_once(force_all=args.all)
    print(f"✓ {uploaded} hochgeladen, {deleted} gelöscht, {unchanged} unverändert")
    if uploaded or deleted:
        trigger_reindex()

    if not args.watch:
        return

    print(
        f"  Watch-Modus: prüfe alle {args.interval}s auf Änderungen (Strg+C zum Beenden)"
    )
    try:
        while True:
            time.sleep(args.interval)
            uploaded, deleted, unchanged = sync_once(force_all=False)
            if uploaded or deleted:
                print(
                    f"✓ {uploaded} hochgeladen, {deleted} gelöscht, {unchanged} unverändert"
                )
                trigger_reindex()
    except KeyboardInterrupt:
        print("\n  Watch-Modus beendet.")


if __name__ == "__main__":
    main()
