"""
deploy_vault_search.py — Build & Deploy des vault-search-Dienstes auf die GIGI-Umbrel.

Bewusst Python + paramiko statt Bash + ssh/scp (wie scripts/deploy_ha.sh): die
GIGI-Box (.96) hat nur Passwort-Auth, kein SSH-Key wie die Haupt-Umbrel — dasselbe
Muster wie scripts/sync_obsidian.py.

Baut das Image auf dem Zielhost selbst (kein lokaler Cross-Arch-Build), mountet den
bereits existierenden Obsidian-Vault read-only in den Container.

Verwendung:
    python scripts/deploy_vault_search.py

Env (in .env, siehe .env.example):
    UMBREL_HOST_GIGI, UMBREL_USER_GIGI, UMBREL_SUDO_PASS_GIGI
    OLLAMA_HOST, OLLAMA_EMBED_MODEL (optional, default nomic-embed-text)
"""

from __future__ import annotations

import io
import sys
import tarfile
import urllib.request
import json
from pathlib import Path

import paramiko
from dotenv import dotenv_values

if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent

# Muss mit REMOTE_VAULT_ROOT in scripts/sync_obsidian.py übereinstimmen.
VAULT_HOST_PATH = (
    "/home/umbrel/umbrel/app-data/obsidian/data/config/"
    "BitGridAI_Obisdian_RAG_MVP/BitGridAI_MVP"
)
BUILD_DIR = "bitgridai-vault-search"
IMAGE_NAME = "bitgrid-vault-search"
CONTAINER_NAME = "bitgrid-vault-search"
DEFAULT_PORT = "8767"
DEFAULT_EMBED_MODEL = "nomic-embed-text"


def load_env() -> dict[str, str]:
    env = dotenv_values(REPO_ROOT / ".env")
    required = [
        "UMBREL_HOST_GIGI",
        "UMBREL_USER_GIGI",
        "UMBREL_SUDO_PASS_GIGI",
        "OLLAMA_HOST",
    ]
    missing = [k for k in required if not env.get(k)]
    if missing:
        raise SystemExit(f"Fehlt in .env: {', '.join(missing)} (siehe .env.example)")
    return {k: v for k, v in env.items() if v is not None}


def pull_embed_model(ollama_host: str, model: str) -> None:
    print(f"→ Ziehe Embedding-Modell {model} auf {ollama_host} (no-op falls vorhanden)")
    req = urllib.request.Request(
        f"{ollama_host.rstrip('/')}/api/pull",
        data=json.dumps({"name": model, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        print(f"  HTTP {resp.status}")


def build_context_tar() -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(REPO_ROOT / "pyproject.toml", arcname="pyproject.toml")
        tar.add(REPO_ROOT / "src", arcname="src")
    return buf.getvalue()


def run_sudo(client: paramiko.SSHClient, sudo_pass: str, command: str) -> str:
    _, stdout, stderr = client.exec_command(
        f"echo '{sudo_pass}' | sudo -S bash -c \"{command}\""
    )
    out: str = stdout.read().decode(errors="replace")
    err: str = stderr.read().decode(errors="replace")
    exit_code = stdout.channel.recv_exit_status()
    if exit_code != 0:
        raise RuntimeError(
            f"Remote-Kommando fehlgeschlagen ({exit_code}):\n{out}\n{err}"
        )
    return out


def main() -> None:
    env = load_env()
    host = env["UMBREL_HOST_GIGI"].rstrip("/")
    user = env["UMBREL_USER_GIGI"]
    sudo_pass = env["UMBREL_SUDO_PASS_GIGI"]
    ollama_host = env["OLLAMA_HOST"]
    embed_model = env.get("OLLAMA_EMBED_MODEL") or DEFAULT_EMBED_MODEL
    port = env.get("VAULT_SEARCH_PORT") or DEFAULT_PORT

    pull_embed_model(ollama_host, embed_model)

    print("→ Baue Build-Kontext (pyproject.toml + src/)")
    tar_bytes = build_context_tar()

    print(f"→ Verbinde mit {user}@{host}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=sudo_pass, timeout=10)
    try:
        sftp = client.open_sftp()
        remote_home = f"/home/{user}/{BUILD_DIR}"
        client.exec_command(f"mkdir -p {remote_home}")[1].channel.recv_exit_status()
        remote_tar = f"{remote_home}/build.tar.gz"
        print(f"→ Kopiere Build-Kontext nach {remote_tar}")
        with sftp.open(remote_tar, "wb") as f:
            f.write(tar_bytes)
        sftp.close()

        print("→ Entpacke + baue Image (sudo docker build)")
        run_sudo(
            client,
            sudo_pass,
            f"cd {remote_home} && tar -xzf build.tar.gz && rm -f build.tar.gz && "
            f"docker build -t {IMAGE_NAME} -f src/explain/Dockerfile . 2>&1 | tail -20",
        )

        print("→ Ersetze laufenden Container")
        run_sudo(
            client, sudo_pass, f"docker rm -f {CONTAINER_NAME} 2>/dev/null || true"
        )
        run_cmd = (
            f"docker run -d --name {CONTAINER_NAME} --restart unless-stopped "
            f"-p {port}:{port} "
            f"-v '{VAULT_HOST_PATH}:/vault:ro' "
            f"-e VAULT_PATH=/vault -e VAULT_SEARCH_PORT={port} "
            f"-e OLLAMA_HOST={ollama_host} -e OLLAMA_EMBED_MODEL={embed_model} "
            f"{IMAGE_NAME} python -m src.explain.vault_search_server"
        )
        run_sudo(client, sudo_pass, run_cmd)
    finally:
        client.close()

    print(f'✓ Deployed. Test: curl "http://{host}:{port}/search?q=test&k=3"')


if __name__ == "__main__":
    main()
