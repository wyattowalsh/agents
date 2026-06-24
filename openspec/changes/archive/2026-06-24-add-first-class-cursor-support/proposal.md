# Change: Add First-Class Cursor Support

## Why

Cursor now has distinct editor, CLI, Cloud Agent, subagent, hooks, Bugbot, and
ACP surfaces. The repo previously treated Cursor mostly as a home MCP merge and
coarse support registry entry, which risked silent support claims across
different permission planes and dashboard-managed cloud state.

## What Changes

- Add repo-owned Cursor project rendering for MCP, hooks, permissions, CLI
  config, Bugbot rules, subagents, and ignored skill symlinks.
- Add an explicit `config/cursor-agents.json` overlay and schema so Cursor
  subagent `readonly` and model behavior are source-backed.
- Split Cursor editor, CLI, Cloud Agent, cloud subagent, Bugbot, and ACP support
  records with caveats for dashboard/API/global state.
- Render Cursor MCP with `${workspaceFolder}` and `${env:NAME}` syntax and only
  the managed MCPHub `harness-safe` group by default.
- Preserve user-owned `~/.cursor`, dashboard/team settings, OAuth, Bugbot Admin
  API state, and live installs.

## Non-Goals

- Mutating `~/.cursor` beyond the existing optional home MCP merge.
- Writing Cursor dashboard, team rules, Cloud Agent MCP/secrets, OAuth, or
  Bugbot Admin API state.
- Running live installs or `wagents skills sync --apply`.
- Claiming Cloud Agent parity with local Cursor hook or MCP behavior.
