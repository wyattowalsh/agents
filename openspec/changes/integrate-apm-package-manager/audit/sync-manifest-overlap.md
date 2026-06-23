# Sync Manifest vs APM Deploy Paths Overlap Matrix

**Purpose:** Compare paths declared in `config/sync-manifest.json` (current wagents/repo-sync model) against paths APM would write to (from Wave 1 spikes + `apm_cli/integration/targets.py` + mcp_integrator).  
**Categories (proposed for integrate-apm):**
- **own**: APM takes exclusive ownership / canonical source for these artifacts when using APM packages (e.g. deployed skills/prompts from deps).
- **merge**: Co-exist; APM and existing wagents/sync may both touch (e.g. settings.json, mcp configs, hooks.json -- require merge logic or post-process).
- **wagents-only**: Remain under current sync-manifest control; do not delegate to APM (repo core configs, schemas, wagents platform code, planning manifests, global instructions authored here).
- **conflict-risk**: High chance of file-level overlap/overwrite if both active (same dir + similar names).

Generated from:
- `config/sync-manifest.json` (read 2026-06-23)
- APM source profiles for copilot/claude/cursor/codex/gemini/opencode/antigravity/agent-skills
- Wave 1 spike observations (sample package + real deploys)
- Cross-ref to existing `.github/`, `.claude/`, `.cursor/`, `.agents/`, `platforms/`, `config/opencode-*` etc.

## High-Level Matrix

| Category | Sync-Manifest Example Paths | APM Deploy Equiv (per target) | Overlap Class | Notes / Conflict Risk |
|----------|-----------------------------|-------------------------------|---------------|-----------------------|
| Harness instructions/prompts/agents | `${REPO_ROOT}/.github/instructions`, `.github/prompts`, `.github/agents`, `.github/copilot-instructions.md`, `platforms/copilot/agents` | copilot: `.github/instructions/*.instructions.md`, `.github/prompts/*.prompt.md`, `.github/agents/*.agent.md` (also generates copilot-instructions.md) | conflict-risk / merge | Repo has authored + generated content here. APM from packages would land here. Platforms/ also canonical for some agents. |
| Claude harness | `.claude/*` (implied via settings + user), but many files in tree under sync? (settings merged) | claude: `.claude/rules/*.md`, `.claude/agents/*.md`, `.claude/commands/*.md`, `.claude/skills/*` | conflict-risk | Heavy existing `.claude/rules/`, `.claude/skills/`, `.claude/commands/`. Skills per-client vs shared. |
| Cursor harness | `.cursor/mcp.json`, `.cursor/hooks.json`, `.cursor/agents`, `.cursor/rules`, `.cursor/skills/repo`, `.cursor/cli.json`, `.cursor/BUGBOT.md`, `.cursor/permissions.json` | cursor: `.cursor/rules/*.mdc`, `.cursor/agents/*.md`, `.cursor/commands/*.md`, `.agents/skills/*` (skills shared) | conflict-risk | Very high; repo skills are extensive custom. Rules use .mdc |
| Codex | `~/.codex/config.toml` (merged), `~/.codex/hooks.json`, `~/.codex/skills` (symlinked), `config/codex-config.toml` (generated) | codex: `.codex/agents/*.toml`, `.agents/skills/*`, `.codex/hooks.json` | merge / wagents-only (core toml) | Workspace `.codex/agents` low in repo. User skills symlinked-entries. |
| Gemini | `~/.gemini/settings.json` (merged), `~/.gemini/GEMINI.md` (generated), `~/.gemini/antigravity/...` | gemini: `.gemini/commands/*.toml`, `.agents/skills/*` ; compile GEMINI.md | merge | Commands new; settings merged. Antigravity subpaths in sync. |
| OpenCode | `opencode.json` (generated), `config/opencode-*.json` (canonical), `.opencode/*` (package etc), `platforms/opencode/plugins/*`, `~/.config/opencode/*` (merged/generated) | opencode: `.opencode/agents/*.md`, `.opencode/commands/*.md`, `.agents/skills/*` | conflict-risk (plugins/agents) / merge (configs) | APM agents/commands under .opencode/ vs existing top-level json + plugins/ + platforms/. |
| Antigravity / shared agents | `~/.gemini/antigravity/mcp_config.json`, `~/.gemini/extensions/.../antigravity`, `.agents/*` (many skills) | antigravity: `.agents/rules/*.md`, `.agents/skills/*`, `.agents/hooks.json`, `.agents/mcp_config.json` | conflict-risk (shared .agents) | Explicit-only; .agents/ is cross-tool shared already populated by repo. No direct workspace `.agents/rules` yet. |
| Shared skills (agent-skills) | `${REPO_ROOT}/.agents/skills`? (via tree + symlinks), `~/.copilot/skills`, `~/.codex/skills`, `~/.gemini/skills`, `~/.cursor/skills/repo` (symlinked-entries) | all targets that use shared: `.agents/skills/*/SKILL.md` (agent-skills, copilot, cursor, codex, gemini, opencode, antigravity) ; claude per-client | own (for APM pkgs) / merge | Primary shared surface. Repo currently populates via skills/ + symlinks + .cursor/skills etc. APM packages would "own" the installed SKILL.md copies here. |
| MCP configs (project) | `mcp.json`, `.vscode/mcp.json`, `.cursor/mcp.json`, `opencode.json` | Depends: copilot (via adapters), claude (`.mcp.json`), cursor (`.cursor/mcp.json`), opencode (opencode.json "mcp"), gemini (`.gemini/settings.json`) | merge | APM writes mcp servers into these when --mcp or mcp deps declared. Sync has "generated"/"merged". |
| MCP configs (user/global) | `~/.copilot/mcp-config.json` (merged), `~/.copilot/settings.json`, `~/.claude.json` (and desktop), `~/.cursor/mcp.json`, `~/.gemini/settings.json`, `~/.gemini/antigravity/mcp_config.json`, `~/.config/opencode/...`, `~/.codex/config.toml` | Same + antigravity specific, copilot etc. (user scope -g) | merge | High merge need; some are settings mixed with mcp. |
| Hooks | `hooks/` (canonical), `.github/hooks` (generated), `.cursor/hooks.json`, `~/.codex/hooks.json`, `~/.claude/settings.json` etc. | copilot: `.github/hooks`, claude/cursor/gemini/codex/antigravity: respective hooks.json or settings merge | merge | Repo has top-level `hooks/` canonical + per harness. APM integrates package hooks. |
| Core repo / wagents / planning / config | `config/sync-manifest.json` (canonical), `config/*.json` (most), `config/schemas/`, `planning/manifests/*`, `instructions/*.md` (some symlink), `wagents/`, `platforms/`, `agent-bundle.json`, `mcp.json` (root), `AGENTS.md`? | None direct (APM does not manage repo config/ or wagents python). APM manages `apm.yml`, `apm.lock.yaml`, `apm_modules/`, and **deploys** into harness dirs. | wagents-only | APM integration would likely keep these under wagents/sync. `apm.yml` would be new canonical or generated? |
| Global instructions / compile outputs | `instructions/copilot-global.md` (canonical), `instructions/global.md` (symlink), `instructions/codex-global.md` (generated), `.grok/config.toml` etc. | Via `apm compile`: AGENTS.md, GEMINI.md, copilot-instructions.md, CLAUDE.md etc. | merge / wagents-only | APM compile produces distributed AGENTS.md family; repo may author globals separately. |
| Other generated | `external-skills.md`, plugin registries, opencode-*.json, `.github/workflows`, etc. | N/A (APM focuses on agent primitives: skills/agents/prompts/instructions/commands/hooks/mcp) | wagents-only |  |

## APM Primitive-to-Path Summary (condensed from source + spikes)

- **skills**: mostly `.agents/skills/.../SKILL.md` (cross) or per-client (claude: `.claude/skills/`, windsurf etc.)
- **instructions**: copilot `.github/instructions/`, claude `.claude/rules/`, cursor `.cursor/rules/*.mdc`, antigravity `.agents/rules/`, windsurf `.windsurf/rules/`
- **agents**: copilot `.github/agents/*.agent.md`, claude `.claude/agents/`, cursor `.cursor/agents/`, codex `.codex/agents/*.toml`, opencode `.opencode/agents/`
- **commands** (or workflows/prompts): varies (claude/cursor/opencode `.*/commands/*.md`, gemini `.gemini/commands/*.toml`, copilot uses prompts)
- **prompts**: copilot `.github/prompts/`
- **hooks**: per-target json or merged into settings; antigravity/codex special .*/hooks.json
- **MCP**: harness-specific json/toml under root or ~/.*
- **compile family**: produces root-level AGENTS.md / CLAUDE.md / GEMINI.md / copilot-instructions.md etc.

## Key Overlaps / Recommendations

- **High conflict surfaces**: `.github/instructions + prompts + agents`, `.claude/{rules,commands,skills,agents}`, `.cursor/{rules,agents,commands,skills}`, `.opencode/{agents,commands}`, `.agents/skills` (shared).
- **Merge candidates**: All MCP json/settings, hooks.json, generated instruction files (copilot-instructions.md, GEMINI.md).
- **APM own for packages**: Deployed artifacts originating from `apm install <pkg>` (the .apm/ primitives materialized to harness paths).
- **wagents-only keep**: `config/`, `platforms/`, `wagents/`, `planning/`, `instructions/*-global.md` (unless migrated), schemas, registries, sync-manifest itself, hooks/ top-level policy, most root `*.json` not mcp-related.
- **New for APM**: `apm.yml` (source of truth for deps), `apm.lock.yaml`, `apm_modules/`.
- **Antigravity special**: Treat as wagents + explicit APM opt-in; .agents/ already multi-owned.
- **Symlinks in manifest**: `symlinked-entries` for skills (user) -- APM may interact or replace some.
- **Next**: Produce `apm.yml` manifest from current surfaces; decide per-path "mode" (own/merge/wagents-only) and implement reconciliation in wagents or via apm hooks. Update CANONICAL_TARGETS if full antigravity support desired. Run `apm doctor`, `wagents validate` post-changes.

**Sources cited in this doc:**
- config/sync-manifest.json (full read + targeted grep)
- Wave1 spikes (temp installs + dry-runs)
- APM 0.21.0 installed package sources (targets.py, mcp_integrator.py, target_detection.py, apm_yml.py)
- Existing workspace tree (`.claude/`, `.cursor/`, `.github/`, `.agents/`, `platforms/`, `config/`)

See `wave1-target-spikes.md` for per-target command outputs and file lists.
