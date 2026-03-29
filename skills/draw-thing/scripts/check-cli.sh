#!/usr/bin/env bash
set -euo pipefail

if ! command -v draw-things-cli >/dev/null 2>&1; then
  printf '%s\n' '{"status":"not_installed","install":"brew tap drawthingsai/draw-things && brew install --HEAD drawthingsai/draw-things/draw-things-cli"}'
  exit 1
fi

models_dir="${DRAWTHINGS_MODELS_DIR:-$HOME/Library/Containers/com.liuliu.draw-things/Data/Documents/Models}"
model_count=0

if [[ -d "$models_dir" ]]; then
  model_count="$(find "$models_dir" -maxdepth 1 \( -name '*.ckpt' -o -name '*.safetensors' \) 2>/dev/null | wc -l | tr -d ' ')"
fi

# Escape JSON-special chars in paths
cli_path="$(command -v draw-things-cli)"
escaped_path="${cli_path//\\/\\\\}"
escaped_path="${escaped_path//\"/\\\"}"
escaped_dir="${models_dir//\\/\\\\}"
escaped_dir="${escaped_dir//\"/\\\"}"

printf '{"status":"installed","path":"%s","models_dir":"%s","model_count":%s}\n' \
  "$escaped_path" "$escaped_dir" "$model_count"
