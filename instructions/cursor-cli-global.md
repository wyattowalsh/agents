# Cursor Agent CLI Global Instructions

@./instructions/global.md

## Binary

Use `agent` (also `cursor-agent`).

## What this harness reads

Load `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, and this overlay.

## Shared with the editor

Consume the same project surfaces the Cursor adapter already renders (`harness="cursor"`):

- `.cursor/hooks.json` (fleet hooks only; no Plannotator)
- user `~/.cursor/hooks.json` (home-only Plannotator `CreatePlan` / `SwitchMode` gates)
- `.cursor/mcp.json`
- skills (`.cursor/skills/`, Skills CLI store)
- agents (`.cursor/agents/`)

Do not treat `cursor-cli` as a second hook-render target. Do not duplicate those files.

## CLI-only config

Keep project `.cursor/cli.json` **permissions only**. Repo sync writes that file from the Cursor adapter.

Treat `~/.cursor/cli-config.json` as user-owned. Operators SHOULD set `exploreSubagentModel=inherit`. Never write `cli-config.json` or live `state.vscdb` from repo sync.

## Modes

- Default: agent
- Plan: `--plan` or `--mode=plan`
- Ask (read-only): `--mode=ask`

## Headless

Use `agent -p` / `agent --print` for non-interactive runs. Apply writes with `--force` (`--yolo` is an alias). Auto-approve MCP servers with `--approve-mcps`.

## MCP

Manage the shared `mcp.json` (MCPHub **harness** group) with:

```bash
agent mcp list
agent mcp login <identifier>
agent mcp enable <identifier>
agent mcp disable <identifier>
```

Do not print bearer tokens or MCP auth material.

## Plugins

Load a local plugin with `--plugin-dir <path>` (repeatable). Treat `agent plugin marketplace` as operator-opt-in. Never run marketplace add from repo sync.

## Worktrees

Use `agent --worktree` only when the user asks. If `.cursor/worktrees.json` is present, CLI setup scripts come from that file. This repo does not author `worktrees.json`. Do not create, switch, or delete worktrees unless the user explicitly asks.

## ACP and worker

Use `agent acp` for Agent Client Protocol. ACP stays on the existing `cursor-acp` harness-surface row. Keep `agent worker` out of repo sync.

## Skills

Install with `npx skills add ... -a cursor` or `wagents install` / `wagents skills sync -a cursor`. There is no native `agent` / `cursor-cli` Skills CLI adapter. Do not use `-a cursor-cli`.

## Plannotator

Home-only plan review: `SwitchMode` (enter / `improve-context`, 5s) and `CreatePlan` (review, fail-open). The shim is `~/.cursor/hooks/plannotator-plan-hook.py`. Missing binary, empty plan, crash, or unmapped JSON allow; never exit code 2 / `failClosed: true`.

Do not add Plannotator to project `.cursor/hooks.json` (cloud agents load project hooks and would hang on the 345600s GUI review). `Shift+Tab` / `--plan` may skip `SwitchMode`; `CreatePlan` still fires when a plan is submitted.

```bash
uv run wagents cursor-cli plannotator sync
uv run wagents cursor-cli plannotator install
```

Home stack sync skips both Grok and Cursor Plannotator rows with `--no-plannotator-hooks`.

## Doctor

```bash
uv run wagents cursor-cli doctor --format json
```

Doctor warns (does not fail) when the Plannotator binary, home `CreatePlan`/`SwitchMode` rows, or home shim are missing.

## Update

Run `agent update` to refresh the CLI. A desktop-style restart is not typically required; update the binary when the CLI is stale.

## Secrets

Never print secrets, tokens, or account email. Do not dump `agent about` / `agent status` output that includes account identifiers.
