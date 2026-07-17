# LM Studio Global Instructions

@./instructions/global.md

## LM Studio-Specific Overrides

### Surfaces this harness receives from the repo

| Surface | How it is projected |
| --- | --- |
| **MCP** | Home `mcp.json` via MCPHub **remote-stdio** (`scripts/mcphub/remote-stdio.sh`) |
| **Instructions** | Managed config preset `wagents-repo.preset.json` (system / `pre_prompt`) |
| **Agents** | One managed preset per portable agent: `wagents-agent-<name>.preset.json` |
| **Skills** | Optional symlink tree at `{lmstudio-home}/skills/<name>/` — **default none** |

### Home path

Resolve LM Studio user data in this order:

1. `~/.lmstudio-home-pointer` (if it names an existing directory)
2. `~/.lmstudio`

Docs often mention `~/.lmstudio/...`; some installs use `~/.cache/lm-studio` via the pointer.

### Sync

```bash
uv run python scripts/sync_agent_stack.py --targets home --platforms lm-studio --check
uv run python scripts/sync_agent_stack.py --targets home --platforms lm-studio --apply
```

Launch helper (starts MCPHub, opens app on macOS):

```bash
scripts/mcphub/wrappers/lm-studio
```

### Skills plugins

LM Studio has **no first-party Skills CLI adapter**. Skill directory mirroring is **opt-in**:

| `WAGENTS_LM_STUDIO_SKILLS` | Effect |
| --- | --- |
| unset / `none` | Default: no skill symlinks; purge prior managed repo skill links |
| `all` | Mirror every repo skill with `SKILL.md` |
| `allowlist:a,b` or `a,b` | Mirror only those skill directory names |

Point a skills-capable plugin at `{lmstudio-home}/skills` after an opt-in sync. Do **not** expect `npx skills add -a lm-studio` to work until upstream adds an adapter.

### Presets

- Only files prefixed `wagents-` / `wagents-agent-` are managed; user presets are preserved.
- Select a preset in the LM Studio Configurations / Presets UI to apply system prompt + params.
- Prefer shorter agent presets for local models; full `AGENTS.md` is not injected wholesale.
- Managed presets do not embed absolute filesystem paths to the repo clone.

### Explicitly unsupported

- Hooks / fleet hook registry
- Native Skills CLI install target
- OpenCode-style subagent depth tooling inside the LM Studio app

### Local model provider (orthogonal)

Codex and OpenCode may still use `tooling-policy.json` → `local_llm_providers.lmstudio` as an OpenAI-compatible provider. That path is independent of this MCP/preset/skills projection.
