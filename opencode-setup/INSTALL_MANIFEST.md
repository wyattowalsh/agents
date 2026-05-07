# OpenCode Plugin Installation Manifest

**Last verified:** 2026-05-07
**Primary config:** `~/.config/opencode/opencode.json`
**Project mirror:** `opencode.json`

This manifest records the OpenCode plugin inventory requested for this machine and mirrored into the repo-level OpenCode config. The live OpenCode config is the installation surface; the repo config mirrors the requested npm plugin specs so future sync/review work can detect drift.

## Runtime Plugin Inventory

The active runtime npm plugin list is configured as `@latest` in `~/.config/opencode/opencode.json` and mirrored in repo `opencode.json`:

1. `opencode-antigravity-auth@latest`
2. `opencode-gemini-auth@latest`
3. `cc-safety-net@latest`
4. `envsitter-guard@latest`
5. `@tarquinen/opencode-dcp@latest`
6. `@morphllm/opencode-morph-plugin@latest`
7. `opencode-handoff@latest`
8. `opencode-agent-skills@latest`
9. `@devtheops/opencode-plugin-otel@latest`
10. `@plannotator/opencode@latest` with `workflow: "plan-agent"` and `planningAgents: ["plan"]`
11. `@simonwjackson/opencode-direnv@latest`
12. `opencode-pty@latest`
13. `opencode-wakatime@latest`
14. `octto@latest`
15. `@mohak34/opencode-notifier@latest`
16. `opencode-devcontainers@latest`
17. `@ramarivera/opencode-model-announcer@latest`
18. `@mailshieldai/opencode-canvas@latest`
19. `opencode-scheduler@latest`
20. `opencode-claude-auth@latest`
21. `opencode-plugin-langfuse@latest`

Keep repo-managed npm plugin specs on `@latest`. If OpenCode reports a stale installed plugin, refresh the matching package under `~/.cache/opencode/packages/` with Bun or restart OpenCode so its automatic installer rebuilds the cache.

`opencode-shell-strategy` was removed from the requested inventory because npm returned 404 for that package and OpenCode logged `failed to resolve plugin server entry` for its empty cache directory. Re-add it only if a valid install source is confirmed.

`open-plan-annotator@latest` was replaced by `@plannotator/opencode@latest` because Plannotator's default plan-agent workflow scopes `submit_plan` to planning agents instead of exposing the older broader plan workflow to primary execution agents.

`@mohak34/opencode-notifier@latest` is the active npm notifier package. `config/opencode-notifier.json` is the repo-owned source for `~/.config/opencode/opencode-notifier.json` and intentionally uses `notificationSystem: "ghostty"` for reliable Ghostty notifications. In that mode the package sends OSC 9 terminal notifications and does not use `customIconPath`, so custom icon settings are intentionally disabled unless a separate opt-in terminal-notifier experiment is introduced.

`opencode-background-agents@latest` is intentionally excluded from the runtime plugin inventory because its npm package provenance does not match the documented `kdcokenny/opencode-background-agents` source. Use the repo-local vendored fallback in `.opencode/plugin/background-agents.ts` unless a trusted package source is explicitly approved.

## TUI Plugin Inventory

TUI-only plugins belong in `~/.config/opencode/tui.json`, not in the repo runtime mirror, unless a repo-managed TUI source file is introduced:

1. `@slkiser/opencode-quota@latest`
2. `opencode-subagent-statusline@latest`

Do not add `notification_method` to `~/.config/opencode/tui.json`; current OpenCode TUI schema rejects that key and logs `ConfigInvalidError`.

## Runtime Plugin Guardrails

- `opencode-scheduler@latest` is installed but intentionally has no scheduled jobs configured. Create jobs only on explicit request, prefer read-only jobs first, set `timeoutSeconds`, and inspect scheduler `job_logs` before trusting recurring automation.
- `opencode-pty@latest` can start long-running interactive PTY sessions. Prefer explicit `timeoutSeconds`, use `notifyOnExit` for long commands, and clean up sessions when finished.
- `opencode-wakatime@latest` reads credentials from `~/.wakatime.cfg` or `$WAKATIME_HOME/.wakatime.cfg`. Never store WakaTime API keys in repo config, docs, tests, or OpenCode plugin arrays.
- `octto@latest` explores ideas through branch-based workflows. Do not let it create branches or worktrees unless the user explicitly requests that workflow.
- `opencode-claude-auth@latest` can reuse Claude Code credentials. Claude Code must be authenticated first; prefer macOS Keychain-backed credentials and use redacted debug logs only. Do not enable optional 1M context or model/runtime overrides by default.
- `opencode-plugin-langfuse@latest` requires OpenTelemetry and user-owned environment variables. The config enables `experimental.openTelemetry`; do not commit credential values. Required keys are `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`; `LANGFUSE_BASEURL` is optional.
- `@plannotator/opencode@latest` must stay configured as `workflow: "plan-agent"` with `planningAgents: ["plan"]`; use `manual` mode only if the user wants command-only reviews.

## OCX-Managed Components

`ocx` is a CLI/extension manager, not an OpenCode runtime plugin. Install it as a local CLI and use it to add KDCO registry components when requested:

```bash
npm install -g ocx
ocx add kdco/worktree --from https://registry.kdco.dev
```

`opencode-worktree` is managed through the KDCO/OCX component path for this setup rather than the repo runtime `plugin` array. It can create branch-backed worktrees and spawn OpenCode sessions, so use it only when isolated workflow automation is explicitly intended. Repo-sourced worktree hooks are disabled unless `hooks.allowRepoCommands` is explicitly enabled, and cleanup aborts when uncommitted worktree changes are present or removal fails instead of auto-committing work or dropping retry state.

## Deferred UI And Control Plugins

The UI research pass found additional candidates that are not installed in this batch:

- Optional local experiments: `opencode-workspaces@latest`, `opencode-bytheway@latest`, `@leo000001/opencode-quota-sidebar@latest`, `@ramtinj95/opencode-tokenscope@latest`.
- Security-review first: `@lesquel/opencode-pilot@latest`, `@different-ai/opencode-browser`, `@igovet/opencode-tui-tunnel`, `@actualyze/opencode-monitor`, checkpoint/session-control plugins.
- Local workflow-state plugins deferred by user request: `@codemcp/workflows-opencode@latest` and `@codemcp/workflows-opencode-tui@latest`.
- Broad orchestration bundles deferred by policy: `opencode-nexus`, `opencode-swarm`, `oh-my-opencode`, and `oh-my-opencode-slim`.

## Local TypeScript Plugins

Repo-managed local plugins are deployed from `platforms/opencode/plugins/` to `~/.config/opencode/plugins/`:

- `approval-notify.ts`
- `credential-guard.ts`

The live directory also contains `compaction-context.ts`. It is currently treated as local machine state, not repo-managed inventory, unless it is explicitly promoted into `platforms/opencode/plugins/`.

## OpenCode Model Policy

Repo-managed OpenCode config and OpenCode agent frontmatter must stay model-free and step-cap-free. Do not introduce `model`, `small_model`, `mode.*.model`, `agent.*.model`, or `steps` selectors in generated repo surfaces; OpenCode should inherit harness/runtime defaults by default.

When merging live user-owned OpenCode config, preserve existing user model settings instead of replacing them with repo defaults.

The DCP config follows the same model-neutral policy. `config/opencode-dcp.jsonc` is the repo-owned source for `~/.config/opencode/dcp.jsonc`; sync merges it without adding OpenCode model fields, agent step caps, or DCP per-model limit maps.

The notifier config follows the Ghostty-first notification policy. `config/opencode-notifier.json` is copied to `~/.config/opencode/opencode-notifier.json` so concise approval/completion wording and the intentional no-custom-icon Ghostty behavior persist across machines.

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

# Confirm the repo-managed notifier config was synced.
cmp -s config/opencode-notifier.json ~/.config/opencode/opencode-notifier.json

```

Package registry resolution is not a complete installation check, but every npm plugin spec in the active inventory should resolve and have a package entry under `~/.cache/opencode/packages/`.

## Related Config Paths

- Main config: `~/.config/opencode/opencode.json`
- Project config mirror: `opencode.json`
- TUI config: `~/.config/opencode/tui.json`
- Local plugin files: `~/.config/opencode/plugins/`
- npm plugin cache: `~/.cache/opencode/packages/`
- Repo-managed local plugin sources: `platforms/opencode/plugins/`
- DCP config: `~/.config/opencode/dcp.jsonc`
- Repo-managed DCP source: `config/opencode-dcp.jsonc`
- Notifier config: `~/.config/opencode/opencode-notifier.json`
- Repo-managed notifier source: `config/opencode-notifier.json`
- Devcontainers config: `~/.config/opencode/devcontainers.json`
