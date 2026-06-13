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
| `@slkiser/opencode-quota`                   | `@latest` | Server-side quota tools paired with the TUI sidebar plugin             |
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
| `btw-opencode`                              | `@latest` | `/btw` background side-session prompts                                 |
| `opencode-large-image-optimizer`            | `@latest` | Crop/compress oversized image payloads before provider requests        |
| `opencode-ignore`                           | `@latest` | Enforce project `.ignore` access restrictions for native file tools    |
| `opencode-token-monitor`                    | `@latest` | Token usage, cost, budget, history, and export tools                   |
| `opencode-history-search`                   | `@latest` | Search OpenCode SQLite/legacy session history                          |
| `opencode-lmstudio`                         | `@latest` | Local LM Studio provider discovery and health checks                   |
| `opencode-wakatime`                         | `@latest` | WakaTime AI coding activity tracking via `~/.wakatime.cfg`             |
| `octto`                                     | `@latest` | Branch-based idea/design exploration workflows                         |
| `@hueyexe/opencode-ensemble`                | `@latest` | Parallel teammate sessions with dashboard and task board               |
| `@json9512/opm`                             | `@latest` | Runtime plugin management commands such as `/opm list`                 |
| `@mohak34/opencode-notifier`                | `@latest` | OpenCode notifications                                                 |
| `opencode-terminal-progress`                | `@latest` | Terminal tab progress reporting via OSC 9;4 when supported             |
| `opencode-devcontainers`                    | `@latest` | Devcontainer workspace support                                         |
| `@gotgenes/opencode-agent-identity`         | `@latest` | Agent identity prompt injection and attribution tool                   |
| `@ramarivera/opencode-model-announcer`      | `@latest` | Model announcement/status plugin                                       |
| `opencode-adaptive-thinking`                | `@latest` | Reasoning-effort adjustment tool and prompt guidance                   |
| `@mailshieldai/opencode-canvas`             | `@latest` | Interactive terminal canvases in tmux panes                            |
| `opencode-scheduler`                        | `@latest` | Inert scheduled-job support until explicitly configured                |
| `opencode-claude-auth`                      | `@latest` | Claude credential reuse without optional model/runtime overrides       |
| `opencode-plugin-langfuse`                  | `@latest` | Langfuse telemetry via user-owned environment variables                |
| `opencode-betterglob`                       | `@latest` | Enhanced glob file discovery tools                                     |
| `opencode-bettergrep`                       | `@latest` | Enhanced grep/content search tools                                     |
| `opencode-plugin-ast-lsp`                   | `@latest` | AST and LSP-backed code navigation tools                               |

Local OpenCode plugins are deployed from `../platforms/opencode/plugins/` to `~/.config/opencode/plugins/` during sync. `octto-primary-inherit.mjs` runs after `octto@latest` and removes the upstream primary `octto` agent's hardcoded model pin so it inherits the active OpenCode model; Octto's managed `bootstrapper` and `probe` defaults are rendered from `../config/opencode-octto.json`. `opencode-incomplete-resume.mjs` is a tuned local copy of `ilgizar-valiullin/opencode-incomplete-resume-plugin` because upstream is source-only. Its local constant changes are: explicit `TASK_STATUS: INCOMPLETE` trigger only, `MAX_CONTINUES = 3`, and `COOLDOWN_MS = 2000`.

To update: keep plugin specs in `../opencode.json` on `@latest` and restart OpenCode so its installer refreshes the cache. `opencode-terminal-progress` can be disabled per user/session with `OPENCODE_TERMINAL_PROGRESS=0` when terminal progress control sequences are not wanted. If an `@latest` plugin remains stale because of OpenCode's package cache, remove only that plugin's directory under `~/.cache/opencode/packages/` and restart OpenCode; do not replace repo-managed plugin specs with semver pins unless the user explicitly asks for a rollback.

### Quota Sidebar

**Package:** `@slkiser/opencode-quota@latest`
**Source:** `slkiser/opencode-quota`
**Config:** `../config/opencode-quota-toast.json` is synced to `~/.config/opencode/opencode-quota/quota-toast.json`.

This plugin is loaded in both runtime OpenCode (`../opencode.json`) and TUI OpenCode (`~/.config/opencode/tui.json`). The TUI plugin list is merged from `../config/opencode-tui-plugins.json`, preserving user-owned TUI plugins while ensuring the quota sidebar stays installed. The sidecar enables the sidebar panel, OpenAI quota display, session token display, and remaining-percent display.

### Token Monitor

**Package:** `opencode-token-monitor@latest`
**Source:** `Ainsley0917/opencode-token-monitor`
**Config:** `../config/opencode-token-monitor.json` is synced to `~/.config/opencode/token-monitor.json`.

Use quota for live provider quota/sidebar status and token monitor for analytics, cost history, project-scoped reporting, and JSON/CSV/Markdown exports. The configured budget thresholds are warning thresholds only; they are intentionally high enough for GPT-5.5 work to avoid noisy duplicate alerts.

### LM Studio

**Package:** `opencode-lmstudio@latest`
**Source:** `agustif/opencode-lmstudio`

The global OpenCode sync logic already renders a `lmstudio` provider from `../config/tooling-policy.json`, defaulting to `http://127.0.0.1:1234/v1` and `local-model`. The plugin adds local server discovery, model listing, health checks, and provider merging. OpenAI remains the default model; select local models explicitly with `--model lmstudio/<model>`.

### History Search

**Package:** `opencode-history-search@latest`
**Source:** `joeyism/opencode-history-search`

Searches OpenCode session history from the SQLite store at `~/.local/share/opencode/opencode.db` and older JSON storage when present. Use it for keyword, regex, fuzzy, date, role, title, message, tool, and file-path history lookups.

### Agent Identity

**Package:** `@gotgenes/opencode-agent-identity@latest`
**Source:** `gotgenes/opencode-agent-identity`

Injects the active agent identity into the system prompt and exposes an `agent_attribution` tool for retrospective attribution. This complements `@ramarivera/opencode-model-announcer`; monitor prompt size if adding more identity/status plugins.

### Adaptive Thinking

**Package:** `opencode-adaptive-thinking@latest`
**Source:** `ian-pascoe/opencode-adaptive-thinking`

Configured inline in `../opencode.json` with tool name `set_reasoning_effort`. The prompt keeps xhigh reasoning as the steady-state default for every task and uses the tool only to restore or persist xhigh when a session is not already there. It relies on the active model exposing OpenCode reasoning-effort variants.

### Ensemble

**Package:** `@hueyexe/opencode-ensemble@latest`
**Source:** `hueyexe/opencode-ensemble`
**Config:** `../config/opencode-ensemble.json` is synced to `~/.config/opencode/ensemble.json`.
**Skill:** `../skills/opencode-ensemble/` vendors upstream tag `v0.14.2` / commit `b6bc7f706c13aa42d32e836ea647677d0b14c2f7`.

The repo grants Ensemble access to `~/.local/share/opencode/worktree/**` because the plugin uses isolated worktrees for teammate sessions. The managed config sets `mergeOnCleanup: false` so teammate work is not automatically merged; use `team_merge` only after reviewing changes. Dashboard port stays `4747`. `rateLimitCapacity: 10`, `timeoutMs: 3600000`, and `peerMessageLimit: 10` are tuned for this 10-core / 32 GiB workstation and substantial parallel work.

Ensemble model fields intentionally stay empty in `../config/opencode-ensemble.json`. The plugin only passes `provider/model` strings to OpenCode, while this repo expresses thinking levels through OpenCode agent variants: `build`, `plan`, `explore`, and `general` all use `variant: "xhigh"`. Avoid explicit `team_spawn.model` values unless a task deliberately needs to override the configured agent default.

If OpenCode resolves `@hueyexe/opencode-ensemble@latest` to a stale package, remove only `~/.cache/opencode/packages/@hueyexe/opencode-ensemble@latest`, restart OpenCode, and verify the cache package version from `node_modules/@hueyexe/opencode-ensemble/package.json`.

### BTW Background Sessions

**Package:** `btw-opencode@latest`
**Source:** `aptdnfapt/btw-opencode`

Adds `/btw <prompt>` for forked background side sessions. Treat `/btw` as a read-only/background research lane unless the prompt explicitly asks it to edit files.

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

## TUI Plugins

These belong in the user-owned OpenCode TUI config (`~/.config/opencode/tui.json`), not repo runtime `../opencode.json`:

| Plugin                       | Version   | Purpose                                   |
| ---------------------------- | --------- | ----------------------------------------- |
| `@ishaksebsib/opencode-tree` | `@latest` | PI-style `/tree` conversation branch view |
| `@slkiser/opencode-quota`    | `@latest` | Quota/status sidebar panel                |

`opencode-subagent-statusline@latest` and `@thiagos1lva/opencode-token-usage-chart@latest` are disabled on OpenCode 1.14.50 because they fail plugin load with an `OTUI_TREE_SITTER_WORKER_PATH` registration conflict.

TUI shortcuts must use the current `keybinds` shape in `~/.config/opencode/tui.json`. Do not add stale `keymap.sections` entries.

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

### Incomplete Resume

**Source:** `ilgizar-valiullin/opencode-incomplete-resume-plugin`
**Why vendored:** Upstream is a source-only plugin with hardcoded configuration constants. This repo keeps a local copy of the upstream plugin shape and tunes only the conservative constants needed for this environment. The unrelated npm `opencode-auto-resume@latest` loop produced aggressive resume behavior and malformed session IDs in logs, so sync filters it out to avoid running both continuation plugins.

**Files:**

- `../platforms/opencode/plugins/opencode-incomplete-resume.mjs` — tuned local copy of upstream `auto-continue.ts`

**Behavior in this repo:**

- keeps upstream event handling for `session.idle` and `message.updated`
- resumes only when the last assistant message contains `TASK_STATUS: INCOMPLETE`
- stops when the last assistant message contains `TASK_STATUS: COMPLETE` or `TASK_STATUS: BLOCKED`
- uses `MAX_CONTINUES = 3` and `COOLDOWN_MS = 2000`
- removes upstream broad phrase triggers such as `continue working`, `resume task`, and `next step`

`opencode-auto-resume@latest` is intentionally filtered out of live runtime config during sync and should not be re-added unless a safer upstream release is explicitly approved.

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

### Ralph Wiggum

**Source:** `Th0rgal/open-ralph-wiggum`
**Package:** `@th0rgal/ralph-wiggum`
**Why CLI-only:** Ralph Wiggum is an iterative CLI wrapper around OpenCode and other coding agents. Its README explicitly says not to load it as an OpenCode plugin.

**Canonical install:**

- `npm install -g @th0rgal/ralph-wiggum@latest`

**Usage:**

- `ralph "<verifiable task>" --agent opencode --max-iterations <n>`
- Use `--no-commit` when you want to preserve this repo's atomic/manual commit discipline.
- Use `--no-plugins` when debugging OpenCode plugin startup separately from Ralph's loop.

**State:**

- Ralph writes `.ralph/`; this repo ignores it in both `.gitignore` and `.ignore`.

### Subtask2

**Source:** `spoons-and-mirrors/subtask2`
**Package:** `@spoons-and-mirrors/subtask2`
**Status:** intentionally not installed.

The user explicitly excluded Subtask2 during the 2026-05-09 OpenCode plugin expansion. It also carries `PolyForm-Noncommercial-1.0.0` licensing and adds command/subtask loop behavior, so revisit licensing and loop guardrails before adding it later.

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
