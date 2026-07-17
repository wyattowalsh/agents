# LM Studio harness

LM Studio receives **compatible** repo surfaces via home sync under the resolved
user-data root.

## Surfaces

| Surface | Projection |
| --- | --- |
| **MCP** | `{home}/mcp.json` — MCPHub remote-stdio (Cursor-compatible) |
| **Instructions** | `{home}/config-presets/wagents-repo.preset.json` |
| **Agents** | `{home}/config-presets/wagents-agent-<name>.preset.json` from `agents/*.md` |
| **Skills** | Optional `{home}/skills/<name>/` symlinks — **default `none`** |
| **Hooks** | Unsupported |
| **Skills CLI** | No native `lm-studio` agent; use opt-in skills mirror + a Hub skills plugin |

## Home path

1. `~/.lmstudio-home-pointer` (existing directory)
2. `~/.lmstudio`

## Sync

```bash
uv run python scripts/sync_agent_stack.py --targets home --platforms lm-studio --check
uv run python scripts/sync_agent_stack.py --targets home --platforms lm-studio --apply
```

### Skill mirror policy (`WAGENTS_LM_STUDIO_SKILLS`)

Default is **no** skill symlinks (MCP + presets only). Prior managed repo skill
symlinks are purged on sync when mode is `none`.

| Value | Behavior |
| --- | --- |
| unset / empty / `none` | No skill links; remove managed repo skill symlinks |
| `all` | Symlink every repo `skills/*/SKILL.md` tree |
| `allowlist:a,b` or `a,b` | Symlink only named skills |
| unknown single token | Fail closed → `none` |

```bash
# Opt-in full mirror (check then apply)
WAGENTS_LM_STUDIO_SKILLS=all uv run python scripts/sync_agent_stack.py \
  --targets home --platforms lm-studio --check
WAGENTS_LM_STUDIO_SKILLS=all uv run python scripts/sync_agent_stack.py \
  --targets home --platforms lm-studio --apply
```

Non-symlink directories under `{home}/skills` are never deleted.

## Using projections in the app

1. **MCP** — Program → Edit `mcp.json` (or rely on synced file).
2. **Instructions / agents** — Configurations → Presets → select `wagents/repo-instructions` or `wagents/<agent>`.
3. **Skills** — After opt-in sync, install a community skills plugin and set its skills root to `{home}/skills`.

Only `wagents-*.preset.json` files are managed; other presets are left alone.
Instruction presets never embed absolute machine paths.

## Launch helper

```bash
scripts/mcphub/wrappers/lm-studio
```

## Orthogonal: local model provider

Codex/OpenCode may use `config/tooling-policy.json` → `local_llm_providers.lmstudio`
as an OpenAI-compatible endpoint. That is independent of this harness projection.

## Overlay

Maintainer instruction bridge: `instructions/lm-studio-global.md`.
