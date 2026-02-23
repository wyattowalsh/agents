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
wagents docs generate --no-installed    # Skip installed skills from ~/.claude/skills/
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

# Or use make targets (see Makefile)
make install                                 # All skills → all agents
make install-claude                          # All skills → Claude
make install-skill SKILL=honest-review       # Specific skill → all agents
make help                                    # Show all make targets
```

> **CI/CD:** The `release-skills.yml` workflow validates on every PR and automatically packages + releases skills when a version tag (`v*.*.*`) is pushed.

---

## 5. Instructions & Progressive Disclosure

### Architecture

`~/.claude/CLAUDE.md` contains a single `@` import pointing to `instructions/global.md` in this repo. That file contains general rules + orchestration core (~500 tokens) — this is the only always-loaded instruction content.

Everything situational uses **skills as context loaders** — Claude sees skill descriptions at startup and auto-invokes relevant ones on demand:

| Skill | Type | Description in context | Body loads when |
|-------|------|----------------------|-----------------|
| `orchestrator` | User-invocable (`/orchestrator`) | ~40 tokens | Complex parallel work, teams |
| `python-conventions` | Auto-invoke only | ~45 tokens | Working on Python files |
| `javascript-conventions` | Auto-invoke only | ~25 tokens | Working on JS/TS files |
| `agent-conventions` | Auto-invoke only | ~30 tokens | Creating/modifying agents |
| `continuous-improvement` | Auto-invoke only | ~40 tokens | Proposing instruction changes |

Auto-invoke skills use `user-invocable: false` — hidden from `/` menu but descriptions remain in context for Claude's auto-discovery.

> All 12 custom skill descriptions are loaded at startup. The table above highlights the auto-invoke convention skills. User-invocable skills (honest-review, add-badges, host-panel, mcp-creator, prompt-engineer, skill-creator, wargame) are also visible in context for on-demand invocation.

### Token Budget

| Component | Tokens | Loading |
|-----------|--------|---------|
| `global.md` (general + orchestration core) | ~500 | Always |
| Skill descriptions (12 custom + installed) | ~500 | Always |
| **Total always-loaded** | **~1,000** | |
| Skill bodies (when invoked) | ~5,500 | On-demand |

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
