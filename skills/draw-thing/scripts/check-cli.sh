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

printf '{"status":"installed","path":"%s","models_dir":"%s","model_count":%s}\n' \
  "$(command -v draw-things-cli)" "$models_dir" "$model_count"
