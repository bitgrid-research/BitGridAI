#!/usr/bin/env bash
# deploy_ha.sh — deploy changed HA config files to Umbrel prod
# Usage: ./scripts/deploy_ha.sh [--restart] [--all]
#
# Default: only deploys files changed since last deploy (via git)
# --all:   deploys everything (full sync)
#
# Prerequisites: SSH key auth to Umbrel
#   ssh-copy-id umbrel@$UMBREL_HOST
# Env: UMBREL_HOST (default: umbrel.local), UMBREL_USER (default: umbrel)
#   UMBREL_SUDO_PASS — required for sudo cp (set in .env)
#   → in .env setzen: UMBREL_HOST=192.168.xxx.xxx

set -euo pipefail

# Load .env if present (for UMBREL_HOST, UMBREL_SUDO_PASS, etc.)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a; source "${ENV_FILE}"; set +a
fi

UMBREL_HOST="${UMBREL_HOST:-192.168.178.62}"
UMBREL_USER="${UMBREL_USER:-umbrel}"
UMBREL_SUDO_PASS="${UMBREL_SUDO_PASS:-}"
REMOTE_PATH="/home/umbrel/umbrel/app-data/home-assistant/data"
LOCAL_PATH="src/ha/config"
DEPLOY_TAG="deploy/ha-last"

RESTART=false
DEPLOY_ALL=false

for arg in "$@"; do
  case $arg in
    --restart) RESTART=true ;;
    --all)     DEPLOY_ALL=true ;;
  esac
done

echo "→ Deploying HA config to ${UMBREL_USER}@${UMBREL_HOST}:${REMOTE_PATH}"

# Deploy a single file via /tmp + sudo cp (handles permission-protected dest dir)
deploy_file() {
  local local_file="$1"
  local rel="$2"
  local remote_dir="${REMOTE_PATH}/$(dirname "${rel}")"
  local tmpfile="/tmp/ha_deploy_$(basename "${rel}")"

  echo "  → ${local_file}"
  scp "${local_file}" "${UMBREL_USER}@${UMBREL_HOST}:${tmpfile}"
  if [[ -n "${UMBREL_SUDO_PASS}" ]]; then
    ssh "${UMBREL_USER}@${UMBREL_HOST}" \
      "echo '${UMBREL_SUDO_PASS}' | sudo -S bash -c 'mkdir -p ${remote_dir} && cp ${tmpfile} ${REMOTE_PATH}/${rel} && rm -f ${tmpfile}'"
  else
    # Fallback: direct scp (works only if umbrel user has write permission)
    ssh "${UMBREL_USER}@${UMBREL_HOST}" "mkdir -p ${remote_dir}"
    scp "${local_file}" "${UMBREL_USER}@${UMBREL_HOST}:${REMOTE_PATH}/${rel}"
  fi
}

if [[ "${DEPLOY_ALL}" == true ]]; then
  echo "  Mode: full"
  for f in configuration.yaml automations.yaml scripts.yaml scenes.yaml ui-lovelace.yaml; do
    [[ -f "${LOCAL_PATH}/${f}" ]] && deploy_file "${LOCAL_PATH}/${f}" "${f}"
  done
  for dir in packages custom_components www; do
    [[ -d "${LOCAL_PATH}/${dir}" ]] || continue
    find "${LOCAL_PATH}/${dir}" -type f | while read -r file; do
      rel="${file#${LOCAL_PATH}/}"
      deploy_file "${file}" "${rel}"
    done
  done
else
  # Incremental: only files changed since last deploy tag
  if git rev-parse "${DEPLOY_TAG}" &>/dev/null; then
    BASE="${DEPLOY_TAG}"
  else
    echo "  No deploy tag found — running full deploy"
    DEPLOY_ALL=true
    exec "$0" --all ${RESTART:+--restart}
  fi

  mapfile -t CHANGED  < <(git diff --name-only "${BASE}" HEAD -- "${LOCAL_PATH}" 2>/dev/null)
  mapfile -t UNSTAGED < <(git status --porcelain "${LOCAL_PATH}" | awk '{print $2}')

  # Deduplicate
  declare -A seen
  ALL_FILES=()
  for f in "${CHANGED[@]:-}" "${UNSTAGED[@]:-}"; do
    [[ -z "$f" || -n "${seen[$f]:-}" || ! -f "$f" ]] && continue
    seen["$f"]=1
    ALL_FILES+=("$f")
  done

  if [[ ${#ALL_FILES[@]} -eq 0 ]]; then
    echo "  Nothing changed since last deploy."
  else
    echo "  Mode: incremental (${#ALL_FILES[@]} file(s))"
    for file in "${ALL_FILES[@]}"; do
      rel="${file#${LOCAL_PATH}/}"
      deploy_file "${file}" "${rel}"
    done
  fi
fi

# Update deploy tag
git tag -f "${DEPLOY_TAG}" HEAD 2>/dev/null || true

echo "✓ Sync complete"

if [[ "${RESTART}" == true ]]; then
  echo "→ Restarting Home Assistant..."
  CONTAINER=$(ssh "${UMBREL_USER}@${UMBREL_HOST}" \
    "echo '${UMBREL_SUDO_PASS}' | sudo -S docker ps --format '{{.Names}}' 2>/dev/null | grep -i 'home-assistant'" \
    | head -1)
  if [[ -n "${CONTAINER}" ]]; then
    ssh "${UMBREL_USER}@${UMBREL_HOST}" \
      "echo '${UMBREL_SUDO_PASS}' | sudo -S docker restart ${CONTAINER}"
    echo "✓ Restarted ${CONTAINER}"
  else
    echo "  ⚠ Container not found — restart HA manually in the UI"
  fi
else
  echo "  Tip: use --restart to auto-restart, --all for full sync"
fi
