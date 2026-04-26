@/Users/ww/dev/projects/agents/instructions/global.md

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

### Memory System

The `memory` field on agents enables persistent storage across sessions:

| Scope | Location | Persists across | Git-tracked |
|-------|----------|-----------------|-------------|
| `user` | `~/.claude/agent-memory/<agent-name>/` | All projects | No |
| `project` | `.claude/agent-memory/<agent-name>/` | Sessions in project | Yes |
| `local` | `.claude/agent-memory/<agent-name>/` | Sessions in project | No (gitignored) |

**When to use each scope:**
- `user` — Cross-project preferences, global workflow patterns
- `project` — Project-specific patterns, architecture decisions
- `local` — Temporary session insights, debugging notes

**Conventions:**
- Choose the narrowest scope that fits the use case
- Keep memory files under 200 lines (only the first 200 lines of the entrypoint are loaded)
- Organize by topic, not chronologically
- Use MEMORY.md as the entrypoint; create topic files for detailed notes

---

## 2. MCP Conventions

First-party MCP servers authored in this repository live in `mcp/<name>/` and follow FastMCP v3 conventions:

- **Entry point:** `server.py` with `mcp = FastMCP("Name")`
- **Config:** `fastmcp.json` pointing to `server.py` with `uv` environment
- **Package:** `pyproject.toml` with `fastmcp>=2` dependency
- **Workspace:** Root `pyproject.toml` includes `[tool.uv.workspace]` with the exact first-party member path, for example `members = ["mcp/<name>"]`
- **Local installs:** Third-party MCP checkouts, archives, caches, notes, and secrets live under `mcp/servers/`; that directory is machine-local and gitignored.

## 2.1 Bundle & Plugin Distribution

The repository root is the canonical bundle root. Do not duplicate `skills/`, `agents/`, `mcp/`, or `instructions/` into platform-specific plugin folders.

| Surface | Files | Purpose |
|---------|-------|---------|
| Bundle manifest | `agent-bundle.json` | Cross-agent source of truth for components, adapters, install commands, and update commands |
| Claude Code plugin | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Native Claude Code marketplace/plugin adapter for the repo root |
| Codex plugin | `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | Native Codex plugin and repo marketplace adapter for the repo root |
| Skills CLI fallback | `npx skills add github:wyattowalsh/agents ...` | Portable install path for supported agents without native plugin marketplaces |

Plugin manifests intentionally omit fixed `version` fields while this repo is distributed from Git. That lets downstream update checks follow new commits rather than requiring a manifest version bump for every skill edit.

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
wagents new skill <name>            # → skills/<name>/SKILL.md
wagents new skill <name> --no-docs  # Skip docs page scaffold
wagents new agent <name>            # → agents/<name>.md
wagents new mcp <name>              # → mcp/<name>/ (server.py + pyproject.toml + fastmcp.json)

# Validate all assets
wagents validate             # Checks frontmatter of all skills and agents

# Regenerate README
wagents readme               # Fully regenerates README.md from repo contents
wagents readme --check       # Exits 1 if README is stale

# Documentation site
wagents docs init                       # One-time: pnpm install in docs/
wagents docs generate                   # Generate MDX content pages
wagents docs generate --include-installed  # Opt in to installed skills from ~/.claude/skills/
wagents docs generate --include-drafts  # Include skills with TODO descriptions
wagents docs dev                        # Generate + launch dev server
wagents docs build                      # Generate + static build
wagents docs preview                    # Generate + build + preview server
wagents docs clean                      # Remove generated content pages

# Package skills
wagents package <name>              # Package a skill into portable ZIP
wagents package --all               # Package all skills into dist/
wagents package --dry-run           # Check portability without creating ZIPs

# Install skills into agent platforms (requires Node.js)
wagents install                              # All skills → all agents (global)
wagents install -y                           # All skills → all agents (no prompts)
wagents install honest-review skill-creator  # Specific skills → all agents
wagents install -a claude-code               # All skills → Claude only
wagents install -a cursor -a github-copilot  # All skills → Cursor + Copilot
wagents install --list                       # List available skills
wagents install --local                      # Project-local install
wagents update                               # Refresh installed skills from recorded sources

# Or use make targets (see Makefile)
make install                                 # All skills → all agents
make install-claude                          # All skills → Claude
make install-skill SKILL=honest-review       # Specific skill → all agents
make update                                  # Refresh installed skills
make help                                    # Show all make targets
```

> **CI/CD:** The `release-skills.yml` workflow validates on every PR and automatically packages + releases skills when a version tag (`v*.*.*`) is pushed.

---

## 5. Instructions & Progressive Disclosure

### Architecture

`instructions/global.md` is the canonical cross-platform instruction source in this repo. Platform-specific files in `instructions/` may import it to add runtime-specific guidance without bloating the shared base. Home entrypoints should point directly at it where the platform allows, except GitHub Copilot, which uses `instructions/copilot-global.md`; repo-local mirrors should be generated from the platform-specific source when a platform requires a specific filename.

Docs-facing authority follows the same pattern: keep repo policy and workflow truth in `AGENTS.md`, regenerate the public README from `wagents readme`, and regenerate generated docs pages from `wagents docs generate` instead of hand-editing derived output.

**Scoped rules** (`.claude/rules/*.md`) provide path-conditional instructions that load automatically when matching files are edited. Each rule uses YAML frontmatter with `paths` globs to declare its trigger scope. Rules cost zero tokens until a path match activates them, making them the lightest layer in the progressive disclosure hierarchy — between always-loaded instructions and on-demand skills.

Everything situational uses **skills as context loaders** — Claude sees skill descriptions at startup and auto-invokes relevant ones on demand:

| Skill | Type | Description in context | Body loads when |
|-------|------|----------------------|-----------------|
| `orchestrator` | User-invocable (`/orchestrator`) | ~40 tokens | Complex parallel work, teams |
| `python-conventions` | Auto-invoke only | ~45 tokens | Working on Python files |
| `javascript-conventions` | Auto-invoke only | ~25 tokens | Working on JS/TS files |
| `agent-conventions` | Auto-invoke only | ~30 tokens | Creating/modifying agents |
| `shell-conventions` | Auto-invoke only | ~30 tokens | Working on shell/Makefile files |
| `learn` | User-invocable + auto-invoke | ~50 tokens | Proposing instruction changes, capturing patterns |

Auto-invoke skills use `user-invocable: false` — hidden from `/` menu but descriptions remain in context for Claude's auto-discovery.

> All 42 custom skill descriptions are loaded at startup (~7,000 chars total). The table above highlights the auto-invoke convention skills. The remaining 38 repository skills are user-invocable, including `simplify` and `orchestrator`.

### Token Budget

| Component | Tokens | Loading |
|-----------|--------|---------|
| `global.md` (general + clarification gate + orchestration core + commit + docs lookup) | ~870 | Always |
| Skill descriptions (42 custom + installed) | ~1,600 | Always |
| **Total always-loaded** | **~2,470** | |
| Scoped rules (`.claude/rules/`) | ~0 | Conditional (path match) |
| Skill bodies (when invoked) | ~12,000 | On-demand |

---

## 6. Supported Agents

| Agent | Reads | Bridge File |
|-------|-------|-------------|
| Claude Code | `CLAUDE.md` → `instructions/global.md` | `instructions/claude-code-global.md` is compatibility only |
| Claude Code plugin | `.claude-plugin/marketplace.json` → repo root plugin | `.claude-plugin/plugin.json` |
| Gemini CLI | `GEMINI.md` → `@./AGENTS.md` → `@instructions/global.md` | `GEMINI.md` |
| Antigravity | `GEMINI.md` → `@./AGENTS.md` → `@instructions/global.md` | `GEMINI.md` |
| Codex | `AGENTS.md` → `@instructions/global.md` | `AGENTS.md` |
| Codex plugin | `.agents/plugins/marketplace.json` → repo root plugin | `.codex-plugin/plugin.json` |
| Crush | `AGENTS.md` → `@instructions/global.md` | `AGENTS.md` |
| OpenCode | `AGENTS.md` → `@instructions/global.md` | `AGENTS.md` |
| Cursor | `AGENTS.md` → `@instructions/global.md` | `AGENTS.md` |
| GitHub Copilot | Generated `.github/copilot-instructions.md` + repo `AGENTS.md` | `.github/copilot-instructions.md` |
