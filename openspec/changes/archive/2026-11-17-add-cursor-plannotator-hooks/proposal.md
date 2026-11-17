# Change: Add Cursor Plannotator hook support (IDE + CLI)

## Why

`config/cursor-global-hooks.json` is already merged into `~/.cursor/hooks.json`
during Cursor home sync, but it still uses Claude/Grok matchers
(`exit_plan_mode|ExitPlanMode`, `enter_plan_mode|EnterPlanMode`). Cursor Agent
(IDE and CLI) never exposes those tools. Plan mode uses `CreatePlan` (plan body
in `plan` / `overview`) and `SwitchMode` (`target_mode_id`: `plan` | `agent`).

Upstream Plannotator has no Cursor plugin. This repo already follows a
CLI-binary + skills + repo-managed-hooks pattern for Grok. Cursor needs the
same treatment with Cursor-native matchers, a stdin shim that emits Cursor
`permission` JSON, and **home-only** projection so cloud agents never hang on a
345600s local GUI hook.

## What Changes

- Home-only Plannotator projection for Cursor IDE and Agent CLI via
  `~/.cursor/hooks.json` plus `~/.cursor/hooks/plannotator-plan-hook.py`.
- Cursor-native `preToolUse` matchers: `SwitchMode` (enter / improve-context)
  and `CreatePlan` (plan review).
- Fail-open shim: missing binary, empty plan, crash, or unmapped JSON → allow.
  Never Cursor exit code 2 / `failClosed: true`.
- Reuse `--no-plannotator-hooks` so home sync skips both Grok and Cursor
  Plannotator rows.
- `wagents cursor-cli plannotator sync|install` and warn-only doctor checks.
- Docs and registries: hook-surface, external-hooks, AGENTS.md, cursor-cli
  overlay, harness-master, hand-maintained Plannotator harness-config page.

## Non-Goals

- Project `.cursor/hooks.json` Plannotator rows (cloud agents load project
  hooks and would hang).
- Adding `cursor-cli` to hook-registry render lists (CLI is a consumer).
- Folding Cursor matchers into `config/plannotator-hooks.policy.json` (Claude
  nested shape). Keep `config/cursor-global-hooks.json` as the Cursor
  projection, analogous to `config/grok-plannotator-hooks.json`.
- Applying home sync on this machine (`--targets home`) without operator
  approval.
- An upstream Cursor Plannotator npm plugin.
- Scanning other projects' `plan.md` files from the Cursor shim.
