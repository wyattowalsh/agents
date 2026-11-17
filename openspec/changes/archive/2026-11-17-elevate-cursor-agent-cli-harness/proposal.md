# Change: Elevate Cursor Agent CLI to a first-class harness

## Why

Cursor Agent CLI (`agent` / `cursor-agent`) is a full terminal harness: it
loads project and user `hooks.json`, plugin hooks, `AGENTS.md`, `CLAUDE.md`,
`.cursor/rules`, shared skills/MCP/subagents, plus CLI-only permissions,
`cli-config.json`, plugin marketplaces, worktrees, and ACP. The repo already
has a thin `cursor-cli` surface-registry row, but harness-master still
collapses `cursor-cli` / `cursor-agent` / `agent-cli` into the editor umbrella
`cursor`. Maintainers cannot audit or document the CLI independently.

## What Changes

- Keep registry id `cursor-cli` (do not invent `agent` or `cursor-agent-cli`).
- Remap harness-master aliases `agent`, `cursor-agent`, `cursor-agent-cli`,
  `agent-cli`, `cursor-cli` to canonical `cursor-cli`. `cursor` stays editor
  (cloud/Bugbot aliases remain folded there). `all` order inserts `cursor-cli`
  after `cursor`.
- Expand the existing `cursor-cli` harness-surface row to all-inclusive
  projection surfaces. Shared files stay one SSOT owned by the Cursor adapter
  (`harness="cursor"` hook render). `cursor-cli` is a hook-surface **consumer**
  row, not a second render target.
- Add `instructions/cursor-cli-global.md`, a thin `.cursor/rules/cursor-cli.mdc`
  pointer, AGENTS.md Supported Agents row, maintainer README, and
  `wagents cursor-cli doctor` (redacts email/auth).
- Discover/usage/evals/authoring for harness-master `cursor-cli`.
- Do not add `cursor-cli` to Skills CLI `SUPPORTED_AGENTS`. Installs stay
  `-a cursor`.

## Non-Goals

- New Skills CLI agent id or `-a cursor-cli`.
- Adding `cursor-cli` to hook-registry render harness lists.
- Writing `~/.cursor/cli-config.json` or `state.vscdb`.
- Hand-editing generated `harness-support.mdx` or catalog pages.
- Live `skills sync --apply`, `npx skills add`, or `agent plugin marketplace add`.
- `/cursor-delegate`, a dedicated MCPHub client, authored `worktrees.json`, or
  a worker daemon.
- Editing `wagents/platforms/cursor.py` unless a later permission-token hole
  is proven and explicitly approved.
