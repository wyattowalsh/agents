# Proposal

## Why

Session review (RV-001–RV-010) found that OpenCode and Grok fleet hook projections invoke
`hooks/run-wagents-hook` with `--harness opencode` and `--harness grok-build`, but the
dispatcher did not emit harness-specific deny JSON on stdout. OpenCode's bridge only
parses stdout on exit 0, so denies were silently fail-open. Grok fleet hooks expected
`decision: block` per `grok_deny_adapter.py`.

## What Changes

- Wire `_deny()` and `_stop_retry()` for `opencode` and `grok-build` harnesses.
- Fix OpenCode bridge `POLICY_MAP.read` policy ID; add dispatcher alias
  `before-read-file-guard`.
- Fail closed when enforce-tier policy modules fail to load (`ENFORCE_POLICY_IDS`).
- Add integration tests for opencode/grok-build deny paths.
- Reconcile OpenSpec: close `fleet-hooks-parity` G0 narrative; document guard expansion here.
- Hygiene: remove stale `.github/hooks/agents-*.json` artifacts; document shell guard
  layering and convert lossy projection.

## Impact

- OpenCode `tool.execute.before` bridge blocks read/shell/write enforce policies.
- Grok `wagents-fleet.json` subprocess hooks emit structured block responses.
- Enforce hooks no longer silently allow when policy modules are missing.

## Scope

RV-001 through RV-010 from the Fleet Hooks v3 session review fix plan.

## Out Of Scope

- `sync --apply --targets home` (user-approved only).
- Full `wagents docs generate` catalog regen.
