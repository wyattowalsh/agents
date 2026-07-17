#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCPHUB_PACKAGE_VERSION="${MCPHUB_PACKAGE_VERSION:-1.0.24}"
MCPHUB_BIND_HOST="${MCPHUB_BIND_HOST:-127.0.0.1}"

case "${MCPHUB_BIND_HOST}" in
  127.0.0.1|::1|localhost) ;;
  *)
    printf 'MCPHUB_BIND_HOST must be loopback-only, got %s\n' "${MCPHUB_BIND_HOST}" >&2
    exit 1
    ;;
esac

if [[ ! "${MCPHUB_PACKAGE_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+([+-][0-9A-Za-z.-]+)?$ ]]; then
  printf 'MCPHUB_PACKAGE_VERSION must be an exact version, got %s\n' "${MCPHUB_PACKAGE_VERSION}" >&2
  exit 1
fi

export MCPHUB_BIND_HOST MCPHUB_PACKAGE_VERSION
export MCPHUB_PARENT_NODE_OPTIONS="${NODE_OPTIONS:-}"
export NODE_OPTIONS="--require=\"${SCRIPT_DIR}/bind-loopback.cjs\"${NODE_OPTIONS:+ ${NODE_OPTIONS}}"

exec npx -y "@samanhappy/mcphub@${MCPHUB_PACKAGE_VERSION}" "$@"
