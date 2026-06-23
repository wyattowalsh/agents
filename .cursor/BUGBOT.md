# Bugbot Project Rules

Review this repository as a cross-platform agent asset bundle. Treat `AGENTS.md`,
`instructions/global.md`, `config/*`, `agents/*.md`, `skills/*/SKILL.md`, and
`scripts/sync_agent_stack.py` as source-of-truth surfaces.

- Flag edits that mutate generated outputs without updating the source and
  rerunning the relevant generator.
- Flag new or changed Cursor support that mutates `~/.cursor`, dashboard/team
  settings, Cloud Agent settings, Bugbot Admin API state, OAuth state, or live
  installs without explicit maintainer approval.
- Flag `.cursor/permissions.json` changes that add `mcpAllowlist` or
  `terminalAllowlist` without a source config that explicitly opts into
  overriding Cursor UI allowlists.
- Flag `.cursor/cli.json` changes that include global-only CLI fields instead
  of project-level `permissions`.
- Flag Cursor MCP entries that expose secrets directly instead of using
  `${env:NAME}`, or repo paths that do not use `${workspaceFolder}`.
- Require focused tests for sync, adapter rendering, hooks, permissions, and
  schema/registry coverage after Cursor support changes.
