# OpenCode Plugins — Installation Notes

This directory uses a mixed OpenCode plugin model:
- `../opencode.json` keeps only plugins that are actually installable from npm.
- Local plugin source under `plugin/` is vendored in-repo when npm/registry install is not reliable.
- Some upstream plugins are documented as external/manual installs only when the repo does not vendor a safe implementation.

## NPM-Managed Plugins

These remain declared in `../opencode.json` and are expected to auto-install when OpenCode restarts:

| Plugin | Version | Purpose |
|--------|---------|---------|
| `opencode-antigravity-auth` | `@latest` | Antigravity authentication bridge |
| `opencode-gemini-auth` | `@latest` | Gemini authentication bridge |
| `cc-safety-net` | `@latest` | Safety checks for Claude-style workflows |
| `envsitter-guard` | `@latest` | Secret-safe dotenv inspection and mutation guardrails |
| `@tarquinen/opencode-dcp` | `@latest` | Dynamic context pruning and compression |
| `@morphllm/opencode-morph-plugin` | `@latest` | Morph code editing/search integration when credentials are present |
| `opencode-handoff` | `@latest` | Cross-session context transfer via `/handoff` |
| `opencode-agent-skills` | `@latest` | Agent Skill discovery and invocation support |
| `@devtheops/opencode-plugin-otel` | `@latest` | OpenTelemetry support for runtime telemetry |
| `@plannotator/opencode` | `@latest` | Browser-based plan annotation UI scoped to the `plan` agent |
| `@simonwjackson/opencode-direnv` | `@latest` | direnv environment loading for OpenCode |
| `opencode-pty` | `@latest` | Interactive PTY sessions for long-running commands and dev servers |
| `opencode-wakatime` | `@latest` | WakaTime AI coding activity tracking via `~/.wakatime.cfg` |
| `octto` | `@latest` | Branch-based idea/design exploration workflows |
| `@mohak34/opencode-notifier` | `@latest` | OpenCode notifications |
| `opencode-devcontainers` | `@latest` | Devcontainer workspace support |
| `@ramarivera/opencode-model-announcer` | `@latest` | Model announcement/status plugin |
| `@mailshieldai/opencode-canvas` | `@latest` | Interactive terminal canvases in tmux panes |
| `opencode-scheduler` | `@latest` | Inert scheduled-job support until explicitly configured |
| `opencode-claude-auth` | `@latest` | Claude credential reuse without optional model/runtime overrides |
| `opencode-plugin-langfuse` | `@latest` | Langfuse telemetry via user-owned environment variables |

To update: keep plugin specs in `../opencode.json` on `@latest` and restart OpenCode so its installer refreshes the cache.

## Vendored Local Plugins

### Background Agents

**Source:** `kdcokenny/opencode-background-agents`
**Why vendored:** The documented upstream is not the npm package named `opencode-background-agents`, and this repo needs a local `delegate` / `delegation_read` / `delegation_list` tool surface instead of an ambiguous runtime npm entry.

**Files:**
- `plugin/background-agents.ts` — local vendored fallback plugin

**Runtime dependency:** `unique-names-generator`

**Behavior in this repo:**
- records delegation requests under `~/.local/share/opencode/delegations/<sessionID>/`
- persists a markdown artifact per delegation ID
- exposes the same high-level tool names as upstream
- intentionally does **not** pretend to provide the full upstream async worker/event pipeline unless the upstream registry plugin is installed separately

### Context Analysis Plugin

**Source:** `IgorWarzocha/Opencode-Context-Analysis-Plugin`
**Why vendored/manual:** Not published to npm; copied from upstream into this repo.

**Files:**
- `command/context.md` — `/context` command definition
- `plugin/context-usage.ts` — core plugin logic
- `plugin/tokenizer-aliases.json` — model-to-tokenizer mappings
- `plugin/tokenizer-registry.d.ts` — type declarations
- `plugin/tokenizer-registry.mjs` — tokenizer resolution logic

**Tokenizer dependency layout:**
- upstream expects tokenizer/runtime dependencies under `plugin/vendor/node_modules`
- install with:
  - `npm install js-tiktoken@latest @huggingface/transformers@^3.3.3 --prefix .opencode/plugin/vendor`

## External / Manual Plugins

### Worktree

**Source:** `kdcokenny/opencode-worktree`
**Why OCX-managed:** Upstream recommends installing the KDCO registry component instead of adding a bare npm runtime plugin. The component can create branch-backed worktrees and spawn OpenCode sessions, so it is intentionally installed through OCX when requested.

**Canonical install:**
- `ocx add kdco/worktree --from https://registry.kdco.dev`

**Important:**
- Do not add `opencode-worktree@latest` to `../opencode.json` unless the user explicitly chooses npm-package installation over the KDCO component path.
- Do not create or delete worktrees during plugin setup.
- Repo-sourced worktree hooks are disabled unless `hooks.allowRepoCommands` is explicitly enabled.
- Worktree cleanup aborts when uncommitted changes are present or removal fails, preserving retry state instead of auto-committing or dropping the session.

### OCX

**Source:** `kdcokenny/ocx`
**Why CLI-only:** OCX is an OpenCode extension manager, not a runtime plugin loaded by OpenCode.

**Canonical install:**
- `npm install -g ocx`

### Notify

**Source:** `kdcokenny/opencode-notify`
**Why external/manual:** Upstream is not installable from npm, and the repo does not currently vendor a complete local copy of the plugin.

**Canonical install:**
- `ocx add kdco/notify --from https://registry.kdco.dev`

**Manual install note:**
- If needed, follow the upstream README and copy the plugin files into the OpenCode config plugin directory, then install its runtime deps (`node-notifier`, `detect-terminal`).

**Important:**
- This plugin was intentionally removed from `../opencode.json` because leaving it there makes OpenCode try to install a package that does not exist on npm.

This is distinct from the active npm notifier package `@mohak34/opencode-notifier@latest`, which is mirrored in `../opencode.json` and configured by `~/.config/opencode/opencode-notifier.json`.

## Installed

- Initial plugin set installed: 2026-04-27
- Install model corrected: 2026-04-27
