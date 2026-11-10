#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
EXPECTED="d2a48597e564e3f118d6a74fb088788246531893299da38b5db0dcc84fe5b1fc"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/chatgpt-exporter.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/extracted"
if base64 --help 2>&1 | grep -q -- '--decode'; then
  cat "$HERE"/source/payload.part* | base64 --decode > "$TMP/source.tar.xz"
else
  cat "$HERE"/source/payload.part* | base64 -D > "$TMP/source.tar.xz"
fi

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL="$(sha256sum "$TMP/source.tar.xz" | awk '{print $1}')"
else
  ACTUAL="$(shasum -a 256 "$TMP/source.tar.xz" | awk '{print $1}')"
fi
[[ "$ACTUAL" == "$EXPECTED" ]] || {
  printf 'checksum mismatch: expected %s, got %s\n' "$EXPECTED" "$ACTUAL" >&2
  exit 1
}

tar -xJf "$TMP/source.tar.xz" -C "$TMP/extracted"
rsync -a --exclude 'browser-artifacts/' "$TMP/extracted/" "$REPO/"
printf 'Materialized verified ChatGPT exporter source into %s\n' "$REPO"
