#!/usr/bin/env bash
# Mechanical pre-verify scope reset for kb-research-ingest goal closure.
# Reverts non-kb commits in wave-01..HEAD, discards dirty/untracked paths outside kb/.
# Run from repository root: bash kb/activity/goal-scope-reset.sh

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPO_ROOT}"

WAVE_ONE_SHA="$(git log --format=%H --grep='feat(kb): wave 01' -1)"
if [[ -z "${WAVE_ONE_SHA}" ]]; then
  echo "goal-scope-reset: FAILED — wave 01 commit not found"
  exit 1
fi

should_skip_subject() {
  case "$1" in
    feat\(kb\):*|fix\(kb\):*|chore\(kb\):*|test\(kb\):*) return 0 ;;
    Revert\ *) return 0 ;;
    *) return 1 ;;
  esac
}

already_reverted() {
  local sha="$1"
  local subject
  subject="$(git log -1 --pretty=format:%s "${sha}")"
  git log --grep="^Revert \"${subject}\"$" --format=%H -1 | grep -q .
}

discard_path() {
  local path="$1"
  [[ -z "${path}" || "${path}" == kb/* ]] && return 0
  if [[ -d "${path}" && ! -L "${path}" ]]; then
    git checkout -- "${path}" 2>/dev/null || rm -rf "${path}"
  else
    git checkout -- "${path}" 2>/dev/null || rm -f "${path}"
  fi
}

while IFS= read -r path; do
  discard_path "${path}"
done < <(git diff --name-only HEAD 2>/dev/null || true)

while IFS= read -r path; do
  discard_path "${path}"
done < <(git diff --cached --name-only 2>/dev/null || true)

while IFS= read -r path; do
  [[ -z "${path}" || "${path}" == kb/* ]] && continue
  rm -rf "${path}"
done < <(git ls-files -o --exclude-standard 2>/dev/null || true)

echo "goal-scope-reset: discarded non-kb dirty/untracked paths"

mapfile -t REVERT_LINES < <(git log --format='%H %s' "${WAVE_ONE_SHA}"..HEAD)

revert_count=0
for line in "${REVERT_LINES[@]}"; do
  [[ -z "${line}" ]] && continue
  sha="${line%% *}"
  subject="${line#* }"
  if should_skip_subject "${subject}"; then
    continue
  fi
  if already_reverted "${sha}"; then
    echo "goal-scope-reset: skip already reverted ${sha}"
    continue
  fi
  echo "goal-scope-reset: reverting ${sha} (${subject})"
  if git revert --no-edit "${sha}"; then
    revert_count=$((revert_count + 1))
    continue
  fi
  if [[ -f .git/REVERT_HEAD ]]; then
    git diff --name-only --diff-filter=U | while IFS= read -r conflict; do
      [[ -z "${conflict}" ]] && continue
      git checkout --theirs -- "${conflict}" 2>/dev/null || git rm -f -- "${conflict}" 2>/dev/null || true
      git add -- "${conflict}" 2>/dev/null || true
    done
    GIT_EDITOR=true git revert --continue
    revert_count=$((revert_count + 1))
    continue
  fi
  echo "goal-scope-reset: FAILED reverting ${sha}"
  exit 1
done

echo "goal-scope-reset: reverted ${revert_count} non-kb commit(s)"

while IFS= read -r path; do
  discard_path "${path}"
done < <(git diff --name-only HEAD 2>/dev/null || true)

while IFS= read -r path; do
  [[ -z "${path}" || "${path}" == kb/* ]] && continue
  rm -rf "${path}"
done < <(git ls-files -o --exclude-standard 2>/dev/null || true)

unrelated_dirty="$(git status --porcelain 2>/dev/null | { grep -v '^.. kb/' || true; } | wc -l | tr -d ' ')"
if [[ "${unrelated_dirty}" -ne 0 ]]; then
  echo "goal-scope-reset: FAILED — ${unrelated_dirty} non-kb path(s) still dirty"
  git status --porcelain | { grep -v '^.. kb/' || true; }
  exit 1
fi

echo "goal-scope-reset: PASS (tree=$(git rev-parse HEAD))"