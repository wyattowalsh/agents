# AGENTS.md — AI Agent Asset Standards

This file is the source of truth for asset formats, naming conventions, and workflows in this repository.

---

## 1. Asset Formats

### Skill Format (`skills/<name>/SKILL.md`)

Skills use YAML frontmatter followed by a markdown body.

**Required fields:**

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | kebab-case, max 64 chars, must match directory name |
| `description` | string | non-empty, max 1024 chars |

**Optional fields (cross-platform, agentskills.io spec):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `license` | string | — | SPDX identifier (e.g., `MIT`) |
| `compatibility` | string | — | Environment requirements, max 500 chars |
| `allowed-tools` | string | — | Space-delimited tool allowlist (experimental) |
| `metadata.author` | string | — | Skill author |
| `metadata.version` | string | — | Semantic version |
| `metadata.internal` | boolean | `false` | If true, hidden unless `INSTALL_INTERNAL_SKILLS=1` |

**Optional fields (Claude Code extensions):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `argument-hint` | string | — | Shown during autocomplete (e.g., `"[query]"`) |
| `model` | string | — | Model override: `sonnet` \| `opus` \| `haiku` |
| `context` | string | — | `fork` to run in isolated subagent |
| `agent` | string | — | Subagent type when `context: fork` |
| `user-invocable` | boolean | `true` | Set `false` to hide from `/` menu |
| `disable-model-invocation` | boolean | `false` | Set `true` to prevent auto-invocation |
| `hooks` | object | — | Lifecycle hooks scoped to this skill |

**Body substitutions:** `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `${CLAUDE_SESSION_ID}`, `` !`command` ``

### Agent Format (`agents/<name>.md`)

Agents use YAML frontmatter followed by a markdown system prompt.

**Required fields:**

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | kebab-case, must match filename (without `.md`) |
| `description` | string | non-empty |

**Optional fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tools` | string | all | Comma-separated tool allowlist |
| `disallowedTools` | string | — | Comma-separated tool denylist |
| `model` | string | `inherit` | `sonnet` \| `opus` \| `haiku` \| `inherit` |
| `permissionMode` | string | `default` | `default` \| `acceptEdits` \| `delegate` \| `dontAsk` \| `bypassPermissions` \| `plan` |
| `maxTurns` | integer | — | Maximum agentic turns before stopping |
| `skills` | list | — | Skills preloaded into agent context |
| `mcpServers` | list | — | MCP servers available to this agent |
| `memory` | string | — | Persistent memory: `user` \| `project` \| `local` |
| `hooks` | object | — | Lifecycle hooks scoped to this agent |

---

## 2. MCP Conventions

MCP servers live in `mcp/<name>/` and follow FastMCP v3 conventions:

- **Entry point:** `server.py` with `mcp = FastMCP("Name")`
- **Config:** `fastmcp.json` pointing to `server.py` with `uv` environment
- **Package:** `pyproject.toml` with `fastmcp>=2` dependency
- **Workspace:** Root `pyproject.toml` includes `[tool.uv.workspace]` with `members = ["mcp/*"]`

---

## 3. Naming Conventions

- **All names:** kebab-case (`^[a-z0-9][a-z0-9-]*$`)
- **Skills:** directory name matches frontmatter `name` field
- **Agents:** filename (without `.md`) matches frontmatter `name` field
- **MCP servers:** directory name matches package name (minus `mcp-` prefix)
- **Body text:** imperative voice ("Check the logs" not "Checks the logs")

---

## 4. Workflow

```bash
# Create new assets from reference templates
wagents new skill <name>    # → skills/<name>/SKILL.md
wagents new agent <name>    # → agents/<name>.md
wagents new mcp <name>      # → mcp/<name>/ (server.py + pyproject.toml + fastmcp.json)

# Validate all assets
wagents validate             # Checks frontmatter of all skills and agents

# Regenerate README
wagents readme               # Fully regenerates README.md from repo contents
wagents readme --check       # Exits 1 if README is stale

# Documentation site
wagents docs init        # One-time: pnpm install in docs/
wagents docs generate    # Generate MDX content pages from repo assets
wagents docs dev         # Generate + launch dev server
wagents docs build       # Generate + static build
wagents docs preview     # Generate + build + preview server
wagents docs clean       # Remove generated content pages
```

---

## 5. Instructions Directory (`instructions/`)

The `instructions/` directory contains global AI agent instruction files. These are **not skills** — they are always-loaded configuration that gets imported via `@` chains into every session.

### Progressive Disclosure Model

| File | Loaded | Tokens | Purpose |
|------|--------|--------|---------|
| `global.md` | Always (via `~/.claude/CLAUDE.md` → `@` import) | ~700 | Router: general rules, CI summary, `@` imports for sub-files |
| `python.md` | Always (via global.md) | ~85 | Python tooling preferences (uv, ty, preferred libraries) |
| `javascript.md` | Always (via global.md) | ~40 | JavaScript/Node.js tooling preferences (pnpm) |
| `orchestration-core.md` | Always (via global.md) | ~400 | Decomposition Gate, Tier Selection, Progress Visibility |

The full orchestration guide (~5,300 tokens) lives as a skill at `skills/orchestrator/SKILL.md` and loads on-demand via `/orchestrator`.

### Import Chain

```
~/.claude/CLAUDE.md
  → @~/dev/projects/agents/instructions/global.md (hop 1)
      → @~/dev/projects/agents/instructions/python.md (hop 2)
      → @~/dev/projects/agents/instructions/javascript.md (hop 2)
      → @~/dev/projects/agents/instructions/orchestration-core.md (hop 2)
```

---

## 6. Supported Agents

| Agent | Reads | Bridge File |
|-------|-------|-------------|
| Claude Code | `CLAUDE.md` → `@AGENTS.md` | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` → `@./AGENTS.md` | `GEMINI.md` |
| Antigravity | `GEMINI.md` → `@./AGENTS.md` | `GEMINI.md` |
| Codex | `AGENTS.md` | — |
| Crush | `AGENTS.md` | — |
| OpenCode | `AGENTS.md` | — |
| Cursor | `AGENTS.md` | — |
| GitHub Copilot | `AGENTS.md` + `CLAUDE.md` + `GEMINI.md` | — |
