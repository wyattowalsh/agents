# OpenCode Plugins — Installation Notes

This directory uses a mixed OpenCode plugin model:
- `../opencode.json` keeps only plugins that are actually installable from npm.
- Local plugin source under `plugin/` is vendored in-repo when npm/registry install is not reliable.
- Some upstream plugins are documented as external/manual installs only when the repo does not vendor a safe implementation.

## NPM-Managed Plugins

These remain declared in `../opencode.json` and are expected to auto-install when OpenCode restarts:

| Plugin | Version | Purpose |
|--------|---------|---------|
| `opencode-handoff` | `^0.5.0` | Cross-session context transfer via `/handoff` |
| `@plannotator/opencode` | `@latest` | Browser-based plan annotation UI scoped to the `plan` agent |
| `@mailshieldai/opencode-canvas` | `^0.1.2` | Interactive terminal canvases in tmux panes |
| `@slkiser/opencode-quota` | `^3.3.0` | Real-time token quota tracking |

To update: edit versions in `../opencode.json` and restart OpenCode.

## Vendored Local Plugins

### Background Agents

**Source:** `kdcokenny/opencode-background-agents`
**Why vendored:** Upstream is not installable from npm, and this repo needs a local `delegate` / `delegation_read` / `delegation_list` tool surface instead of a broken npm entry.

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

### Notify

**Source:** `kdcokenny/opencode-notify`
**Why external/manual:** Upstream is not installable from npm, and the repo does not currently vendor a complete local copy of the plugin.

**Canonical install:**
- `ocx add kdco/notify --from https://registry.kdco.dev`

**Manual install note:**
- If needed, follow the upstream README and copy the plugin files into the OpenCode config plugin directory, then install its runtime deps (`node-notifier`, `detect-terminal`).

**Important:**
- This plugin was intentionally removed from `../opencode.json` because leaving it there makes OpenCode try to install a package that does not exist on npm.

## Installed

- Initial plugin set installed: 2026-04-27
- Install model corrected: 2026-04-27
