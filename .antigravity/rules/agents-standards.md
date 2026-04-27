# AGENTS.md Compliance Standards

This repository is a cross-platform AI agent asset bundle. Every skill, agent, and MCP server must conform to the canonical standards defined in `AGENTS.md`. Violations break downstream packaging, installation, and documentation generation.

## Naming Conventions

- **All identifiers** must be `kebab-case`: `^[a-z0-9][a-z0-9-]*$`.
- **Skills:** directory name under `skills/<name>/` must exactly match the `name` field in YAML frontmatter.
- **Agents:** filename under `agents/<name>.md` (without `.md`) must exactly match the `name` field in YAML frontmatter.
- **MCP servers:** directory name under `mcp/<name>/` should match the package name minus any `mcp-` prefix.
- **Body text:** write in imperative voice ("Check the logs" not "Checks the logs").

## Skill Format (`skills/<name>/SKILL.md`)

Skills use **YAML frontmatter** followed by a **markdown body**.

### Required frontmatter fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | kebab-case, max 64 chars, must match directory name |
| `description` | string | non-empty, max 1024 chars |

### Optional cross-platform fields (agentskills.io spec)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `license` | string | — | SPDX identifier (e.g., `MIT`) |
| `compatibility` | string | — | Environment requirements, max 500 chars |
| `allowed-tools` | string | — | Space-delimited tool allowlist |
| `metadata.author` | string | — | Skill author |
| `metadata.version` | string | — | Semantic version |
| `metadata.internal` | boolean | `false` | Hidden unless `INSTALL_INTERNAL_SKILLS=1` |

### Optional Claude Code extension fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `argument-hint` | string | — | Shown during autocomplete |
| `model` | string | — | Model override: `sonnet` \| `opus` \| `haiku` |
| `context` | string | — | `fork` to run in isolated subagent |
| `agent` | string | — | Subagent type when `context: fork` |
| `user-invocable` | boolean | `true` | Set `false` to hide from `/` menu |
| `disable-model-invocation` | boolean | `false` | Set `true` to prevent auto-invocation |
| `hooks` | object | — | Lifecycle hooks scoped to this skill |

### Body substitutions

The markdown body supports these placeholders:
- `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `${CLAUDE_SESSION_ID}`
- `` !`command` `` for command substitution

## Agent Format (`agents/<name>.md`)

Agents use **YAML frontmatter** followed by a **markdown system prompt**.

### Required frontmatter fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | kebab-case, must match filename (without `.md`) |
| `description` | string | non-empty |

### Optional fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tools` | string | `all` | Comma-separated tool allowlist |
| `disallowedTools` | string | — | Comma-separated tool denylist |
| `model` | string | `inherit` | `sonnet` \| `opus` \| `haiku` \| `inherit` |
| `permissionMode` | string | `default` | `default` \| `acceptEdits` \| `delegate` \| `dontAsk` \| `bypassPermissions` \| `plan` |
| `maxTurns` | integer | — | Maximum agentic turns before stopping |
| `skills` | list | — | Skills preloaded into agent context |
| `mcpServers` | list | — | MCP servers available to this agent |
| `memory` | string | — | Persistent memory: `user` \| `project` \| `local` |
| `hooks` | object | — | Lifecycle hooks scoped to this agent |

### Memory scopes

| Scope | Location | Persists across | Git-tracked |
|-------|----------|-----------------|-------------|
| `user` | `~/.claude/agent-memory/<agent-name>/` | All projects | No |
| `project` | `.claude/agent-memory/<agent-name>/` | Sessions in project | Yes |
| `local` | `.claude/agent-memory/<agent-name>/` | Sessions in project | No (gitignored) |

Use the narrowest scope that fits. Keep memory entrypoints under 200 lines. Organize by topic, not chronologically. Use `MEMORY.md` as the entrypoint.

## Validation

Before committing any skill or agent change, run:

```bash
wagents validate
```

This checks frontmatter of all skills and agents. A failing validation blocks the release pipeline.

## Common Mistakes to Avoid

- Do **not** duplicate `skills/`, `agents/`, `mcp/`, or `instructions/` into platform-specific plugin folders. The repository root is the canonical bundle root.
- Do **not** add fixed `version` fields to plugin manifests while this repo is distributed from Git.
- Do **not** hand-edit generated docs pages or the README. Regenerate them via `wagents readme` and `wagents docs generate`.
