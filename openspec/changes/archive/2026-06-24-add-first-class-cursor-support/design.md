# Design

## Approach

Keep Cursor support file-backed and repo-local. The Cursor adapter owns all
generated `.cursor/*` project surfaces and reads canonical inputs from MCP,
hook, sync, and agent overlay registries. Existing tracked `.cursor/rules/*.mdc`
files remain repo-owned rules; `.cursor/skills/**` remains ignored and receives
symlinks back to canonical `skills/*` directories.

## Support Planes

- `cursor-editor`: repo-present and validated for `.cursor/mcp.json`,
  `.cursor/hooks.json`, `.cursor/permissions.json`, `.cursor/agents`,
  `.cursor/rules`, `.cursor/skills/repo`, and `.cursor/BUGBOT.md`.
- `cursor-cli`: repo-present and validated for project `.cursor/cli.json`, MCP,
  and subagent files. Global CLI config is user-owned.
- `cursor-cloud-agent`: represented by project rules/hooks and documented
  dashboard MCP/secrets caveats.
- `cursor-cloud-subagent`: represented by `.cursor/agents/*.md` plus dashboard
  MCP/secrets caveats.
- `cursor-bugbot`: represented by `.cursor/BUGBOT.md`; Bugbot Admin API state
  remains out of scope.
- `cursor-acp`: represented by project MCP and CLI permission files; ACP runtime
  smoke is optional and only non-mutating.

## Rendering Contracts

- MCPHub projection emits only `mcphub_group_harness-safe` by default.
- Cursor MCP config uses `${workspaceFolder}` for repo paths and `${env:NAME}`
  for secret placeholders.
- `.cursor/permissions.json` can steer `autoRun.block_instructions` but does not
  emit `mcpAllowlist` or `terminalAllowlist` without an explicit future source
  config.
- `.cursor/cli.json` contains project-level `permissions` only and avoids
  global-only CLI fields.
- `.cursor/agents/*.md` is generated from `agents/*.md` plus
  `config/cursor-agents.json`; missing or extra overlays fail sync.
- Cursor hook rendering uses native Cursor event names and flat Cursor hook
  output from `hooks/wagents-hook.py`.

## Compatibility

This change does not remove existing tracked Cursor rules or local OpenSpec
Cursor artifacts. The ignored `.cursor/skills/repo/*` symlinks are additive and
preserve non-symlink conflicts.
