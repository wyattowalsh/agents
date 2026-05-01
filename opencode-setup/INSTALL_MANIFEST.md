# OpenCode Plugin Installation Manifest

**Last verified:** 2026-04-30
**Primary config:** `~/.config/opencode/opencode.json`
**Project mirror:** `opencode.json`

This manifest records the OpenCode plugin inventory requested for this machine and mirrored into the repo-level OpenCode config. The live OpenCode config is the installation surface; the repo config mirrors the requested npm plugin specs so future sync/review work can detect drift.

## Requested Plugin Inventory

The requested npm plugin list is configured as `@latest` in `~/.config/opencode/opencode.json` and mirrored in repo `opencode.json`:

1. `opencode-antigravity-auth@latest`
2. `opencode-gemini-auth@latest`
3. `cc-safety-net@latest`
4. `opencode-agent-memory@latest`
5. `envsitter-guard@latest`
6. `@tarquinen/opencode-dcp@latest`
7. `@morphllm/opencode-morph-plugin@latest`
8. `opencode-handoff@latest`
9. `opencode-agent-skills@latest`
10. `@devtheops/opencode-plugin-otel@latest`
11. `open-plan-annotator@latest`
12. `@simonwjackson/opencode-direnv@latest`
13. `opencode-background-agents@latest`
14. `opencode-notify@latest`
15. `opencode-devcontainers@latest`
16. `@ramarivera/opencode-model-announcer@latest`

## Repo-Local Project Plugins

The repo-level `opencode.json` also keeps these existing project plugins because they were already present before the requested inventory was mirrored:

- `@mailshieldai/opencode-canvas@latest`
- `@slkiser/opencode-quota@latest`

Keep repo-managed npm plugin specs on `@latest`. If OpenCode reports a stale installed plugin, refresh the matching package under `~/.cache/opencode/packages/` with Bun or restart OpenCode so its automatic installer rebuilds the cache.

`opencode-shell-strategy` was removed from the requested inventory because npm returned 404 for that package and OpenCode logged `failed to resolve plugin server entry` for its empty cache directory. Re-add it only if a valid install source is confirmed.

## Local TypeScript Plugins

Repo-managed local plugins are deployed from `platforms/opencode/plugins/` to `~/.config/opencode/plugins/`:

- `approval-notify.ts`
- `credential-guard.ts`

The live directory also contains `compaction-context.ts`. It is currently treated as local machine state, not repo-managed inventory, unless it is explicitly promoted into `platforms/opencode/plugins/`.

## OpenCode Model Policy

Repo-managed OpenCode config and OpenCode agent frontmatter must stay model-free and step-cap-free. Do not introduce `model`, `small_model`, `mode.*.model`, `agent.*.model`, or `steps` selectors in generated repo surfaces; OpenCode should inherit harness/runtime defaults by default.

When merging live user-owned OpenCode config, preserve existing user model settings instead of replacing them with repo defaults.

The DCP config follows the same model-neutral policy. `config/opencode-dcp.jsonc` is the repo-owned source for `~/.config/opencode/dcp.jsonc`; sync merges it without adding OpenCode model fields, agent step caps, or DCP per-model limit maps.

## Dynamic Context Pruning Config

`@tarquinen/opencode-dcp@latest` is configured by `~/.config/opencode/dcp.jsonc`, which is managed from `config/opencode-dcp.jsonc`. The managed config uses stable range compression, model-agnostic percentage thresholds, protected secret file patterns, and subagent-friendly tool protection for long orchestration sessions.

## Verification Notes

The installed OpenCode CLI in this environment does not provide a working plugin inventory command: `opencode plugin list --json` prints `opencode plugin <module>` installation help instead of an inventory. Use these checks instead:

```bash
# Confirm the OpenCode CLI can load the live config.
opencode stats

# Confirm repo-managed local plugins are deployed without drift.
cmp -s platforms/opencode/plugins/approval-notify.ts ~/.config/opencode/plugins/approval-notify.ts
cmp -s platforms/opencode/plugins/credential-guard.ts ~/.config/opencode/plugins/credential-guard.ts

# Confirm the repo-managed DCP config was synced.
cmp -s config/opencode-dcp.jsonc ~/.config/opencode/dcp.jsonc
```

Package registry resolution is not a complete installation check, but every npm plugin spec in the active inventory should resolve and have a package entry under `~/.cache/opencode/packages/`.

## Related Config Paths

- Main config: `~/.config/opencode/opencode.json`
- Project config mirror: `opencode.json`
- TUI config: `~/.config/opencode/tui.json`
- Local plugin files: `~/.config/opencode/plugins/`
- npm plugin cache: `~/.cache/opencode/packages/`
- Repo-managed local plugin sources: `platforms/opencode/plugins/`
- Agent memory data: `~/.config/opencode/memory/`
- DCP config: `~/.config/opencode/dcp.jsonc`
- Repo-managed DCP source: `config/opencode-dcp.jsonc`
- Devcontainers config: `~/.config/opencode/devcontainers.json`
