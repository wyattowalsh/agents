# OpenCode Plugins — Installation Notes

This directory uses a mixed OpenCode plugin model:

- `../opencode.json` keeps only plugins that are actually installable from npm.
- Local plugin source under `plugin/` is vendored in-repo when npm/registry install is not reliable.
- Some upstream plugins are documented as external/manual installs only when the repo does not vendor a safe implementation.

## NPM-Managed Plugins

These remain declared in `../opencode.json` and are expected to auto-install when OpenCode restarts:

| Plugin                                      | Version   | Purpose                                                                |
| ------------------------------------------- | --------- | ---------------------------------------------------------------------- |
| `opencode-antigravity-auth`                 | `@latest` | Antigravity authentication bridge                                      |
| `opencode-gemini-auth`                      | `@latest` | Gemini authentication bridge                                           |
| `cc-safety-net`                             | `@latest` | Safety checks for Claude-style workflows                               |
| `envsitter-guard`                           | `@latest` | Secret-safe dotenv inspection and mutation guardrails                  |
| `@tarquinen/opencode-dcp`                   | `@latest` | Dynamic context pruning and compression                                |
| `@morphllm/opencode-morph-plugin`           | `@latest` | Morph code editing/search integration when credentials are present     |
| `opencode-handoff`                          | `@latest` | Cross-session context transfer via `/handoff`                          |
| `@throwparty/opencode-plugin-session-title` | `@latest` | Session title generation                                               |
| `opencode-rules`                            | `@latest` | Conditional markdown rule discovery and injection for OpenCode prompts |
| `@devtheops/opencode-plugin-otel`           | `@latest` | OpenTelemetry support for runtime telemetry                            |
| `@plannotator/opencode`                     | `@latest` | Browser-based plan annotation UI scoped to the `plan` agent            |
| `@simonwjackson/opencode-direnv`            | `@latest` | direnv environment loading for OpenCode                                |
| `opencode-pty`                              | `@latest` | Interactive PTY sessions for long-running commands and dev servers     |
| `opencode-auto-resume`                      | `@latest` | Session auto-resume support after interrupted OpenCode turns           |
| `opencode-large-image-optimizer`            | `@latest` | Crop/compress oversized image payloads before provider requests        |
| `opencode-ignore`                           | `@latest` | Enforce project `.ignore` access restrictions for native file tools    |
| `opencode-wakatime`                         | `@latest` | WakaTime AI coding activity tracking via `~/.wakatime.cfg`             |
| `octto`                                     | `@latest` | Branch-based idea/design exploration workflows                         |
| `@json9512/opm`                             | `@latest` | Runtime plugin management commands such as `/opm list`                 |
| `@mohak34/opencode-notifier`                | `@latest` | OpenCode notifications                                                 |
| `opencode-terminal-progress`                | `@latest` | Terminal tab progress reporting via OSC 9;4 when supported             |
| `opencode-devcontainers`                    | `@latest` | Devcontainer workspace support                                         |
| `@ramarivera/opencode-model-announcer`      | `@latest` | Model announcement/status plugin                                       |
| `@mailshieldai/opencode-canvas`             | `@latest` | Interactive terminal canvases in tmux panes                            |
| `opencode-scheduler`                        | `@latest` | Inert scheduled-job support until explicitly configured                |
| `opencode-claude-auth`                      | `@latest` | Claude credential reuse without optional model/runtime overrides       |
| `opencode-plugin-langfuse`                  | `@latest` | Langfuse telemetry via user-owned environment variables                |
| `opencode-betterglob`                       | `@latest` | Enhanced glob file discovery tools                                     |
| `opencode-bettergrep`                       | `@latest` | Enhanced grep/content search tools                                     |
| `opencode-plugin-ast-lsp`                   | `@latest` | AST and LSP-backed code navigation tools                               |

To update: keep plugin specs in `../opencode.json` on `@latest` and restart OpenCode so its installer refreshes the cache. `opencode-terminal-progress` can be disabled per user/session with `OPENCODE_TERMINAL_PROGRESS=0` when terminal progress control sequences are not wanted.

### Rule Injection Caution

`opencode-rules` loads global rules from `~/.config/opencode/rules/` and project rules from `.opencode/rules/`. Keep broad always-on repository policy in `AGENTS.md` and `instructions/opencode-global.md`; use rule files for conditional guidance keyed by file globs, prompt keywords, tools, commands, project type, branch, OS, or CI state. This avoids duplicating always-loaded instructions and growing prompt context unnecessarily.

### Large Image Optimizer

**Package:** `opencode-large-image-optimizer@latest`
**Source:** `kargnas/opencode-large-image-optimizer`
**Config:** `../config/opencode-large-image-optimizer.json` is synced to `$XDG_CONFIG_HOME/opencode/large-image-optimizer.json` on this machine.

The repo-managed config enables Anthropic, Google, and OpenAI because this OpenCode setup currently uses `openai/gpt-5.5`; upstream defaults skip OpenAI unless configured. The plugin expects `sharp` as a peer dependency, so verify startup logs after OpenCode refreshes the plugin cache.

### Ignore Guard

**Package:** `opencode-ignore@latest`
**Source:** `lgladysz/opencode-ignore`
**Config:** `../.ignore`

The project `.ignore` blocks generated directories, local harness artifacts, secrets, credential files, and high-noise dependency/build outputs while preserving common example dotenv files. This complements, but does not replace, the global `credential-guard.ts` plugin because shell commands and MCP tools can still have separate access paths.

### Agent Skills Plugin

**Package:** `opencode-agent-skills@latest`
**Runtime status:** Disabled from OpenCode startup. The current package imports `@huggingface/transformers` for semantic skill matching, which loads `onnxruntime-node`; recent macOS crash reports show `onnxruntime_binding.node` / `InferenceSessionWrap` failures while this plugin is active. Keep the plugin out of `../opencode.json` until skill matching can run without the native ONNX runtime or that runtime is proven stable on this machine.

## TUI Plugins

These belong in the user-owned OpenCode TUI config (`~/.config/opencode/tui.json`), not repo runtime `../opencode.json`:

| Plugin                         | Version   | Purpose                                   |
| ------------------------------ | --------- | ----------------------------------------- |
| `@ishaksebsib/opencode-tree`   | `@latest` | PI-style `/tree` conversation branch view |
| `@slkiser/opencode-quota`      | `@latest` | Quota/status display                      |
| `opencode-subagent-statusline` | `@latest` | Subagent statusline display               |

### Tree Plugin

**Package:** `@ishaksebsib/opencode-tree@latest`
**Source:** `ishaksebsib/opencode-tree`
**Installed config:** `~/.config/opencode/tui.json` contains `["@ishaksebsib/opencode-tree@latest", { "storageScope": "global" }]`.

`storageScope: "global"` matches upstream's default and keeps branch state out of this repository. If project-scoped branch state is ever needed, switch to `{ "storageScope": "local" }` and keep `.opencode/opencode-tree/` ignored.

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
**Runtime status:** Disabled from OpenCode startup. Recent macOS crash reports show `onnxruntime_binding.node` / `InferenceSessionWrap` failures while this plugin's tokenizer dependency path is available, so the plugin and `/context` command stay quarantined outside OpenCode's auto-loaded directories until the native tokenizer runtime is replaced or proven stable.

**Files:**

- `command-disabled/context.md` — quarantined `/context` command definition
- `plugin-disabled/context-usage.ts` — quarantined core plugin logic
- `plugin/tokenizer-aliases.json` — model-to-tokenizer mappings
- `plugin/tokenizer-registry.d.ts` — type declarations
- `plugin/tokenizer-registry.mjs` — tokenizer resolution logic

**Tokenizer dependency layout:**

- upstream expects tokenizer/runtime dependencies under `plugin/vendor/node_modules`
- install with:
  - `npm install js-tiktoken@latest @huggingface/transformers@^3.3.3 --prefix .opencode/plugin/vendor`

### Context Cache

**Source:** `JackDrogon/opencode-context-cache`
**Why vendored:** Upstream is not published as `opencode-context-cache` on npm. The plugin must be loaded explicitly from a stable local file path.

**Files:**

- `../platforms/opencode/plugins/opencode-context-cache.mjs` — vendored OpenCode `chat.params` plugin

**Runtime config:**

- The OpenCode sync adapter copies the file to `~/.config/opencode/plugins/opencode-context-cache.mjs`.
- The live global OpenCode config includes `./plugins/opencode-context-cache.mjs`, resolved relative to `~/.config/opencode/`.
- `provider.openai.options.setCacheKey` remains enabled in `../opencode.json` so the plugin's `output.options.promptCacheKey` is forwarded.

**Tuning:**

- Default key source is a SHA-256 hash of `user@host:<absolute cwd>`, isolating cache identity per project path.
- `OPENCODE_PROMPT_CACHE_KEY` can intentionally share cache identity across paths.
- `OPENCODE_STICKY_SESSION_ID` is the secondary override.
- `OPENCODE_CONTEXT_CACHE_DEBUG=1` enables debug logs, but this vendored copy does not log raw cache keys.

## External / Manual Plugins

### OpenCode Manager

**Source:** `shuv1337/oc-manager`
**Package:** `opencode-manager`
**Why CLI-only:** This is a Bun TUI/CLI for inspecting, searching, renaming, moving, copying, and pruning OpenCode metadata. It is not an OpenCode runtime plugin.

**Canonical install:**

- `bun install --global opencode-manager`

**Canonical usage:**

- `opencode-manager --root ~/.local/share/opencode`
- `opencode-manager projects list --format json`
- `opencode-manager sessions list --format json`
- `opencode-manager tokens global --format json`

**Safety:**

- Destructive `projects delete` and `sessions delete` commands require confirmation or `--yes`.
- Use `--dry-run` and `--backup-dir` for pruning workflows.

### RTK

**Source:** `rtk-ai/rtk`
**Formula:** Homebrew `rtk`
**Why CLI/plugin hybrid:** RTK is a Rust CLI proxy plus optional OpenCode hook plugin. It is not an npm runtime plugin for `../opencode.json`.

**Canonical install:**

- `brew install rtk`
- `rtk init -g --opencode --auto-patch`

**Verification:**

- `rtk --version`
- `rtk gain`
- `rtk init --show`

**Tuning:**

- Telemetry is disabled by default upstream and can be hard-disabled with `RTK_TELEMETRY_DISABLED=1`.
- The OpenCode hook only rewrites shell commands that pass through OpenCode `tool.execute.before`; native OpenCode tools such as `read`, `grep`, and `glob` remain governed by OpenCode plugins/tooling.
- Keep RTK out of `../opencode.json`; `rtk init -g --opencode` owns the local `~/.config/opencode/plugins/rtk.ts` surface.

### FFF

**Source:** `dmtrKovalenko/fff`
**Why external/manual:** FFF is not the unrelated npm package named `fff`. Upstream provides an MCP server, a Pi extension, Neovim integration, and SDKs rather than a direct OpenCode runtime plugin package for `../opencode.json`.

**Canonical MCP install:**

- Review the upstream script first, then run `curl -L https://dmtrkovalenko.dev/install-fff-mcp.sh | bash` if you want FFF tools wired into MCP clients.

**Pi extension install:**

- `pi install npm:@ff-labs/pi-fff`

**Important:**

- Do not add `fff@latest` to `../opencode.json`; that package is unrelated to `dmtrKovalenko/fff`.
- FFF keeps repository indexes warm in a long-lived process; expect nonzero resident memory usage in exchange for faster repeated search.

### Worktrunk

**Source:** `max-sixty/worktrunk`
**Why CLI-only:** Worktrunk is a git worktree management CLI, not an OpenCode runtime plugin. It can create branches, worktrees, run hooks, and merge/remove worktrees, so setup remains explicit and user-driven.

**Canonical install:**

- `brew install worktrunk && wt config shell install`

**Alternative install:**

- `cargo install worktrunk && wt config shell install`

**Important:**

- Do not add `worktrunk@latest` to `../opencode.json`.
- Do not run `wt switch`, `wt remove`, `wt merge`, or hook-enabled workflows during repo plugin setup unless the user explicitly requests that worktree operation.

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

**Verification/update checks:**

- `ocx --version`
- `ocx verify`
- `ocx migrate` before `ocx migrate --apply` if OCX reports legacy receipt format warnings

**Important:**

- Do not add `ocx@latest` to `../opencode.json`; OCX manages copied components and receipts, not OpenCode runtime hooks.
- Do not create OCX profiles or launch `ocx oc -p ...` during repo plugin setup unless the user explicitly requests that workflow.

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
