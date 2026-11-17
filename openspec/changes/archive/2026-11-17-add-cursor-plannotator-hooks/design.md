# Design: Cursor Plannotator home hooks

## Runtime

Cursor IDE and Agent CLI share one hook SSOT: project `.cursor/hooks.json` plus
user `~/.cursor/hooks.json`. Cloud agents load **project** hooks only. A
345600s local GUI review hook in the repo would hang cloud runs, so Plannotator
stays home-only.

```
SwitchMode(target_mode_id=plan) → preToolUse matcher SwitchMode
  → ~/.cursor/hooks/plannotator-plan-hook.py enter
  → plannotator improve-context (5s, fail-open)

CreatePlan(plan|overview) → preToolUse matcher CreatePlan
  → ~/.cursor/hooks/plannotator-plan-hook.py exit
  → Claude-shaped PermissionRequest/ExitPlanMode stdin to plannotator
  → Cursor {permission: allow|deny, agent_message, user_message?}
```

Known limit: user `Shift+Tab` / `--plan` may skip `SwitchMode`, so enter-context
can miss. `CreatePlan` still fires when a plan is submitted.

## Shim contract

Standalone stdlib script (`#!/usr/bin/env python3`) copied executable to
`~/.cursor/hooks/plannotator-plan-hook.py`.

- Parse Cursor camelCase/snake_case (`tool_name` / `toolName`, `tool_input` /
  `toolInput`).
- Enter: run improve-context only for `SwitchMode` when `target_mode_id` (also
  `target_mode` / `mode`) is `plan`.
- Exit: read inline `plan` then `overview`. Do not scan other projects' files.
- Map Plannotator/Claude/Codex/Gemini/Copilot decision shapes to Cursor
  `permission` JSON.
- Fail-open: missing binary, empty plan, crash, unmapped JSON → empty stdout,
  exit 0. Never exit 2.

## Sync

`render_cursor_global_hooks()` substitutes `__PLANNOTATOR_CURSOR_PLAN_HOOK__`
(and keeps `__PLANNOTATOR_BIN__` if still present). `sync_home()` copies the
shim and merges rendered rows only when `SyncContext.grok_plannotator_hooks` is
true (`--no-plannotator-hooks` skips both Grok and Cursor). User custom rows
are preserved via `merge_cursor_flat_hooks`. Nested leftover Claude-shaped
rows and stale ExitPlanMode / raw-`plannotator` plan matchers are treated as
managed and replaced.

## CLI / doctor

- `wagents cursor-cli plannotator sync` — copy shim + merge home hooks
- `wagents cursor-cli plannotator install [--hooks/--no-hooks]` — upstream
  `install.sh --non-interactive --minimal`, then sync (no Grok skill mirroring)
- Doctor checks are **warn-only** so `report["ok"]` stays true when the CLI
  binary itself is healthy

## Alternatives rejected

- Project hooks: hangs cloud agents.
- Second hook-registry render target for `cursor-cli`: violates one-Cursor-adapter
  render.
- Folding Cursor matchers into `plannotator-hooks.policy.json`: that file is
  Claude nested shape; Cursor is flat `preToolUse`.
- Fail-closed / exit 2: Cursor treats exit 2 as deny; Grok already fail-opens.
