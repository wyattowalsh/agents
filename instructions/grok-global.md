# Grok Build Global Instructions

@./instructions/global.md

## Grok-Specific Overrides

### Config surfaces

- **Home policy:** `~/.grok/config.toml` — models, features, memory, subagents, compat layers, plugins.
- **Project MCP:** `.grok/config.toml` — MCP servers only (plus optional plugins/permission).
- **Repo source:** `config/grok-config.toml` merged by `uv run python scripts/sync_agent_stack.py --apply --platforms grok`.

### Skills discovery

Grok reads `~/.grok/skills/`, project `.grok/skills/`, repo plugin skills, and Claude-compat `~/.claude/skills/`. Skills CLI has no native `grok` adapter; use `wagents install -a grok` or `wagents skills sync -a grok` (installs via `claude-code`, then mirrors to `~/.grok/skills`).

### Subagents

Grok hard-caps nested subagent depth at **1**. Do not invent deeper orchestration knobs in repo config.

### Experimental env vars

Some toggles are env-only. Source `config/grok-env.sh` in your shell:

```bash
source /path/to/agents/config/grok-env.sh
```

Required exports: `GROK_WEB_FETCH`, `GROK_MEMORY`, `GROK_SUBAGENTS`, `GROK_LSP_TOOLS`. Run `uv run wagents grok doctor` to verify.

### Restart

Restart Grok Build after config or env changes so MCP and feature flags reload.
