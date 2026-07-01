# Design

## Deny transport contract

Subprocess hooks MUST emit deny JSON on **stdout** with **exit 0**. Harnesses:

| Harness | Deny shape |
|---------|------------|
| cursor | `{"permission":"deny",...}` |
| codex | `hookSpecificOutput.permissionDecision deny` |
| gemini-cli | `{"decision":"deny",...}` |
| opencode | `{"permission":"deny","hookSpecificOutput":{...}}` |
| grok-build | `grok_deny_payload()` → `decision: block` |

OpenCode bridge [`runPolicy`](platforms/opencode/plugins/wagents-hook-bridge.ts) catches
non-zero exit and fails open — never use stderr+exit 2 for opencode/grok denies.

## RV-001 dual fix

1. Bridge `POLICY_MAP.read` → `cursor-before-read-file-guard`
2. Dispatcher `POLICIES` alias `before-read-file-guard` → same handler

## Lane model

| Lane | Owner file |
|------|------------|
| D | `hooks/wagents-hook.py` |
| B | `platforms/opencode/plugins/wagents-hook-bridge.ts` |
| T | `tests/hooks/*`, `tests/test_wagents_hook.py` |
| O | OpenSpec markdown |
| H | docs, `apm.lock.yaml` |

## agents-*.json audit (T-001a)

Only consumer: `apm.lock.yaml` checksum list. Canonical projections:
`.cursor/hooks.json`, `.claude/settings.json`, `.github/hooks/policy.json`.
Safe to remove stale `agents-*.json` files and lock entries.

## RV-004 shell guard fail-closed (C-010a)

When `evaluate_git_commit_push` cannot load, `cursor-before-shell-execution-guard`
MUST fail-closed only on shell commands that match dangerous git shapes
(`git push`, `git commit`, `git reset`, `git rebase`, `filter-branch`, `filter-repo`).
Read-only git commands such as `git status` remain allowed so enforce-tier does not
block routine inspection when the policy module is unavailable.
