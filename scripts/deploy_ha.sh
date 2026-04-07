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
#   → in .env setzen: UMBREL_HOST=192.168.xxx.xxx

set -euo pipefail

UMBREL_HOST="${UMBREL_HOST:-192.168.178.62}"
UMBREL_USER="${UMBREL_USER:-umbrel}"
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


if [[ "${DEPLOY_ALL}" == true ]]; then
  # Full deploy
  echo "  Mode: full"
  scp -r \
    "${LOCAL_PATH}/configuration.yaml" \
    "${LOCAL_PATH}/automations.yaml" \
    "${LOCAL_PATH}/scripts.yaml" \
    "${LOCAL_PATH}/scenes.yaml" \
    "${LOCAL_PATH}/ui-lovelace.yaml" \
    "${UMBREL_USER}@${UMBREL_HOST}:${REMOTE_PATH}/"
  scp -r "${LOCAL_PATH}/packages"          "${UMBREL_USER}@${UMBREL_HOST}:${REMOTE_PATH}/"
  scp -r "${LOCAL_PATH}/custom_components" "${UMBREL_USER}@${UMBREL_HOST}:${REMOTE_PATH}/"
  if [[ -d "${LOCAL_PATH}/www" ]]; then
    scp -r "${LOCAL_PATH}/www" "${UMBREL_USER}@${UMBREL_HOST}:${REMOTE_PATH}/"
  fi
else
  # Incremental: only files changed since last deploy tag
  if git rev-parse "${DEPLOY_TAG}" &>/dev/null; then
    BASE="${DEPLOY_TAG}"
  else
    # First time: deploy everything
    echo "  No deploy tag found — running full deploy"
    DEPLOY_ALL=true
    exec "$0" --all ${RESTART:+--restart}
  fi

  # Get changed files in src/ha/config/ since last deploy
  mapfile -t CHANGED < <(git diff --name-only "${BASE}" HEAD -- "${LOCAL_PATH}" 2>/dev/null)

  # Also include untracked/modified (uncommitted) files
  mapfile -t UNSTAGED < <(git status --porcelain "${LOCAL_PATH}" | awk '{print $2}')

  ALL_FILES=("${CHANGED[@]:-}" "${UNSTAGED[@]:-}")

  if [[ ${#ALL_FILES[@]} -eq 0 ]]; then
    echo "  Nothing changed since last deploy."
  else
    echo "  Mode: incremental (${#ALL_FILES[@]} file(s))"
    for file in "${ALL_FILES[@]}"; do
      [[ -z "$file" ]] && continue
      [[ ! -f "$file" ]] && continue
      # Strip src/ha/config/ prefix for remote path
      rel="${file#${LOCAL_PATH}/}"
      remote_dir="${REMOTE_PATH}/$(dirname "${rel}")"
      echo "  → ${file}"
      ssh "${UMBREL_USER}@${UMBREL_HOST}" "mkdir -p ${remote_dir}"
      scp "${file}" "${UMBREL_USER}@${UMBREL_HOST}:${REMOTE_PATH}/${rel}"
    done
  fi
fi

# Update deploy tag
git tag -f "${DEPLOY_TAG}" HEAD 2>/dev/null || true

echo "✓ Sync complete"

if [[ "${RESTART}" == true ]]; then
  echo "→ Restarting Home Assistant..."
  ssh "${UMBREL_USER}@${UMBREL_HOST}" \
    "docker restart homeassistant" 2>/dev/null || \
  echo "  ⚠ Docker restart failed — restart HA manually in the UI"
else
  echo "  Tip: use --restart to auto-restart, --all for full sync"
fi
