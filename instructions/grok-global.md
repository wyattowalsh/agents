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

Required exports: `GROK_WEB_FETCH`, `GROK_MEMORY`, `GROK_SUBAGENTS`, `GROK_LSP_TOOLS`. Run `uv run wagents grok doctor --format json` to verify.

### Cross-harness delegation

Other harnesses (Codex, OpenCode) may dispatch task-graph nodes to Grok via `/grok-delegate` using native headless CLI only. Grok itself should not re-orchestrate nested graphs beyond platform subagent depth 1.

### Plannotator (plan review)

Grok has no npm plugin equivalent to OpenCode's `@plannotator/opencode`. Use the Plannotator CLI, curated skills, and repo-synced hooks instead.

**Install (one command):**

```bash
uv run wagents grok plannotator install
```

This installs the `plannotator` binary, core slash skills (`/plannotator-review`, `/plannotator-annotate`, `/plannotator-last`), optional extras (`--no-extras` to skip), mirrors skills into `~/.grok/skills`, and writes hooks to `~/.grok/hooks/plannotator.json` (`--no-hooks` to skip).

**Repo sources:**

- Hook policy: `config/grok-plannotator-hooks.json` (placeholders resolved on sync)
- Exit-plan shim: `scripts/grok/plannotator-exit-plan-hook.sh` (maps Plannotator `block` → Grok `deny`)
- Project skill overlays: `.grok/skills/plannotator-{review,annotate,last}/`

**Ongoing sync (default-on):**

```bash
uv run wagents skills sync -a grok --apply
uv run wagents grok plannotator sync
uv run python scripts/sync_agent_stack.py --apply --platforms grok --targets home
```

Grok home sync writes `~/.grok/hooks/plannotator.json`, copies `plannotator-exit-plan-hook.py` into `~/.grok/hooks/`, and symlinks repo `.grok/skills/plannotator-*` overlays into `~/.grok/skills/`. Opt out with `--no-plannotator-hooks` on stack sync. Restart Grok Build after hook or skill changes.

**Manual use:** invoke `/plannotator-review`, `/plannotator-annotate`, or `/plannotator-last` in chat. Plan-mode hooks run automatically on `exit_plan_mode` / `enter_plan_mode` when hooks are installed (experimental — may interact with Grok's built-in plan UI).

### Restart

Restart Grok Build after config or env changes so MCP and feature flags reload.
