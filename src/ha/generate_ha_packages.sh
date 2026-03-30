#!/usr/bin/env bash
# Generates HA package YAML files from template + .env
# Usage: bash src/ha/generate_ha_packages.sh

set -euo pipefail

ENV_FILE="$(dirname "$0")/../../.env"
TEMPLATE="$(dirname "$0")/config/packages/avalonq.yaml.template"
OUT_DIR="$(dirname "$0")/config/packages"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2; exit 1
fi

# Load only the relevant variables
eval "$(grep -E '^(MINER[12]_IP|MINER_API_PORT|HA_PROXY_IP|HA_MINER[12]_PROXY_PORT)=' "$ENV_FILE")"

generate() {
  local name="$1" api_host="$2" api_port="$3" out="$4"
  sed "s/<DEVICE_NAME>/${name}/g; s/<API_HOST>/${api_host}/g; s/<API_PORT>/${api_port}/g" \
    "$TEMPLATE" > "$out"
  echo "Generated: $out (${name} → ${api_host}:${api_port})"
}

generate "miner1" "$HA_PROXY_IP" "$HA_MINER1_PROXY_PORT" "$OUT_DIR/avalonq_miner1.yaml"
generate "miner2" "$HA_PROXY_IP" "$HA_MINER2_PROXY_PORT" "$OUT_DIR/avalonq_miner2.yaml"
