# Affected Surfaces

## Canonical Sources

- `config/cursor-agents.json`
- `config/schemas/cursor-agents.schema.json`
- `config/mcp-registry.json`
- `config/hook-registry.json`
- `config/harness-surface-registry.json`
- `config/hook-surface-registry.json`
- `config/sync-manifest.json`
- `agents/*.md`
- `skills/*/SKILL.md`
- `instructions/global.md`

## Generated Repo Surfaces

- `.cursor/mcp.json`
- `.cursor/hooks.json`
- `.cursor/permissions.json`
- `.cursor/cli.json`
- `.cursor/BUGBOT.md`
- `.cursor/agents/*.md`
- `.cursor/rules/*.mdc`
- `.cursor/skills/repo/*`

## Explicitly Out Of Scope

- `~/.cursor` except the pre-existing optional home MCP merge.
- Cursor dashboard/team settings.
- Cursor Cloud Agent MCP/secrets/OAuth settings.
- Bugbot Admin API writes.
- Live installs or skill sync apply.
