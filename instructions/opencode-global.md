# OpenCode Global Instructions

@./instructions/global.md

## OpenCode-Specific Overrides

### Model Preference

OpenCode model defaults are repo-managed. Repo and live OpenCode config set root `model: "openai/gpt-5.5"`, root `small_model: "openai/gpt-5.4-mini"`, and built-in agents `build`, `plan`, `explore`, and `general` to `openai/gpt-5.5` with variant `xhigh`. Use the `model` plus `variant` fields for high-level thinking; do not invent composite model IDs such as `openai/gpt-5.5-high` unless the provider metadata defines that exact model. Do not generate OpenAI, Vercel, Kimi, or other remote provider blocks unless a concrete runtime need is verified. OpenCode's built-in provider registry should own normal model definitions; the only repo-managed exception is a minimal `xai` provider block with empty `options` so the desktop model picker can select Grok routes without inheriting incompatible OpenAI options. The sync tooling strips vercel/opencode-go/kimi-for-coding entries on every write of the project opencode.json and the live ~/.config/opencode/opencode.json, and sanitizes any `xai.options` back to `{}`. This prevents auto-persisted blocks for picker-chosen models from accumulating keys that the target provider rejects ("invalid xai provider options" etc.). Preserve explicit local provider blocks such as LM Studio only when rendered from local provider policy. Do not define duplicate `gpt-5.5-fast` entries unless concrete runtime evidence requires them. Do not silently fall back to another OpenAI model when CLI/TUI runs warn or retry; compare `--pure`, plugin-loaded, TUI, and desktop paths first and keep exact request IDs from any `server_error` lines.

**Using Grok 4.3 (or other xai/vercel routes):** Use the TUI model picker (`<leader>m` / model list + variant list). After exercising a new remote route, re-run the normal opencode sync (wagents or equivalent) so the tooling can scrub transient provider blocks and reduce `provider.xai` to empty options. The OpenAI block remains the only repo-managed provider entry with model variants and plugin options.

Repo-managed OpenCode agent frontmatter must avoid `model`, `small_model`, `mode.*.model`, `agent.*.model`, and `steps` caps. Model selection belongs in config, not agent frontmatter.

Runtime-specific keys (`mode`, `temperature`, `color`, `permission`) for the built-in agents are stored in `instructions/opencode-agents-overlay.md` and loaded exclusively by the OpenCode harness. The canonical agent definitions in `agents/*.md` contain only the portable schema (`name`, `description`, `tools`, `permissionMode`, etc.).

When merging live user-owned OpenCode config, preserve unrelated user settings while enforcing repo-managed model, plugin, and tooling defaults.

### Formatter And LSP Setup

Enable OpenCode formatters and LSP for repo work. Keep the formatter matrix broad enough for Python, JS/TS, Markdown/MDX, YAML, TOML, shell/zsh, Just, Go, and Rust. Prefer local binaries for installed tools such as `ruff`, `ty`, `just`, `gofmt`, and `rustfmt`; use `npx -y` for portable Node-backed formatters when global installs are unavailable.

### Notification Setup

Do not add root `notification_method` to `~/.config/opencode/tui.json`; current OpenCode TUI schema rejects that key and logs `ConfigInvalidError`.

Use current TUI `keybinds`, not stale `keymap.sections`, for shortcut customization. Keep TUI-only plugins and keybind preferences in the user-owned live `~/.config/opencode/tui.json` surface unless this repo later adds a tracked TUI config source.

### Plugin Versioning

Repo-managed OpenCode npm plugin specs in `opencode.json` must use `@latest` so OpenCode's Bun-backed installer resolves the newest published plugin during install refreshes. If a plugin warns that an update is available, refresh the matching package under `~/.cache/opencode/packages/` or restart OpenCode; do not pin or range the repo-managed spec unless the user explicitly requests a rollback.

`@hueyexe/opencode-ensemble@latest` is the repo-managed OpenCode team orchestration plugin. Keep its npm spec on `@latest`; when OpenCode's package cache resolves it to an older package, remove only `~/.cache/opencode/packages/@hueyexe/opencode-ensemble@latest` and restart OpenCode so the installer resolves the current dist-tag. Keep `config/opencode-ensemble.json` tuned for this 10-core / 32 GiB workstation with `mergeOnCleanup: false`, `rateLimitCapacity: 10`, `timeoutMs: 3600000`, `peerMessageLimit: 10`, and empty Ensemble model fields so teammates inherit OpenCode's per-agent variants.

### Plugin Placement

Keep OpenCode runtime plugins in `opencode.json` and the live `~/.config/opencode/opencode.json` `plugin` array. Keep TUI-only plugins in `~/.config/opencode/tui.json` instead of the repo runtime mirror unless a repo-managed TUI source file is explicitly introduced.

Current TUI-only additions on this machine are `@slkiser/opencode-quota@latest` and `@ishaksebsib/opencode-tree@latest`. `opencode-subagent-statusline@latest` and `@thiagos1lva/opencode-token-usage-chart@latest` are disabled because OpenCode 1.14.50 reports an `OTUI_TREE_SITTER_WORKER_PATH` registration conflict when they load.

### Session Poisoning Recovery

If a `Retry Error` or OpenAI `server_error` loops on one OpenCode session while fresh `openai/gpt-5.5` `--pure` and plugin-loaded smoke tests succeed, treat it as session-local poisoning before changing model defaults. The observed failure mode was stale OpenAI encrypted reasoning parts plus retry-written incomplete turns in `~/.local/share/opencode/opencode.db`; reopening the same session replayed that state and produced new request IDs. Preserve request IDs, stop only processes attached to the affected session, back up the DB, remove poisoned rows only after inspection, and quarantine/archive the old session rather than repeatedly resuming it.

### Rule Injection Plugin

`opencode-rules@latest` is enabled for conditional markdown rule injection. Do not create broad unconditional repo rules that duplicate `AGENTS.md` or `instructions/opencode-global.md`; use `.opencode/rules/*.md` or `.opencode/rules/*.mdc` only for guidance that benefits from conditional matching by globs, keywords, tools, commands, project type, branch, OS, or CI state.

### Terminal Progress Plugin

`opencode-terminal-progress@latest` is enabled for terminal tab progress reporting in supported terminals. Do not set a repo-wide opt-out by default; users can disable it with `OPENCODE_TERMINAL_PROGRESS=0` in their own environment.

### Scheduler And Auth Plugins

`opencode-scheduler@latest` is installed only as an inert scheduler plugin by default. Do not create, enable, or mutate scheduled jobs unless the user explicitly asks for scheduler job changes; start with read-only jobs and explicit timeouts when jobs are requested.

`opencode-pty@latest` may run long-lived interactive sessions. Prefer explicit `timeoutSeconds`, `notifyOnExit`, and cleanup. Do not use PTY sessions to bypass normal command safety or secret-handling rules.

`opencode-incomplete-resume.mjs` is the repo-managed tuned local copy of `ilgizar-valiullin/opencode-incomplete-resume-plugin` because upstream is source-only. Keep the local file structurally close to upstream `auto-continue.ts`; only tune the hardcoded constants. Current required constants: `MAX_CONTINUES = 3`, `COOLDOWN_MS = 2000`, and explicit-only `TRIGGER_PHRASES = [/TASK_STATUS:\s*INCOMPLETE/i]`. Do not add generic phrase triggers such as `next step`, `resume task`, or `continue working`.

`octto@latest` and OCX/KDCO worktree components support branch/worktree-based exploration. Do not create, switch, delete, or auto-commit branches/worktrees unless the user explicitly asks for that workflow.

OCX is a CLI/component manager, not an OpenCode runtime plugin. Do not add `ocx@latest` to repo-managed plugin arrays; use `ocx verify` for copied component integrity checks and keep profile creation or `ocx oc -p ...` launches behind explicit user intent.

`opencode-wakatime@latest` reads credentials from `~/.wakatime.cfg` or `$WAKATIME_HOME/.wakatime.cfg`. Never commit or print WakaTime API keys, and do not place them in OpenCode config files.

`opencode-claude-auth@latest` may reuse Claude Code credentials for Anthropic auth. Do not enable optional 1M context behavior or other model/runtime overrides by default; preserve the repo-managed model-neutral policy.

CodeMCP workflow plugins are intentionally deferred. Do not add `@codemcp/workflows-opencode@latest`, `@codemcp/workflows-opencode-tui@latest`, or run broad CodeMCP setup commands unless the user explicitly requests local workflow-state management and accepts the additional artifacts those plugins can create.

### Langfuse Telemetry

`opencode-plugin-langfuse@latest` requires OpenTelemetry support and user-owned environment variables. It is safe for repo config to enable `experimental.openTelemetry`; never commit Langfuse credential values. Required environment keys are `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`; `LANGFUSE_BASEURL` is optional for non-default endpoints.

Treat missing Langfuse environment variables as setup warnings unless OpenCode reports a plugin load failure. Keep `@devtheops/opencode-plugin-otel@latest` until startup validation proves a concrete conflict.

### Plan Review Plugin

Use `@plannotator/opencode@latest` for OpenCode plan review and keep it scoped to the built-in `plan` agent with `workflow: "plan-agent"` and `planningAgents: ["plan"]`. This keeps `submit_plan` out of build/default agents while preserving visual plan annotation.

Do not re-add `open-plan-annotator@latest` by default. It injects a broader plan workflow and is no longer the preferred repo-managed plan review plugin for this machine.

### Chrome DevTools MCP Auth Flows

For OpenCode on this machine, prefer the local wrapper-based Chrome DevTools MCP launch instead of the generic shared repo default when Google sign-in or other sign-in-sensitive flows need a stable attached browser.

The live OpenCode config should point `mcp.chrome-devtools.command` at:

```json
["bash", "/Users/ww/.config/opencode/tools/chrome-devtools-launcher.sh"]
```

That launcher currently:

- starts or reuses a dedicated Chrome instance on `127.0.0.1:9333`
- uses profile dir `/Users/ww/.cache/chrome-devtools-mcp-browser-url-profile`
- verifies `http://127.0.0.1:9333/json/version` returns a real DevTools payload before continuing
- then execs `npx -y chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9333`

The current launcher path is:

```bash
/Users/ww/.config/opencode/tools/chrome-devtools-launcher.sh
```

Use this OpenCode-specific override only where needed. Keep the shared repo-managed MCP default on the generic headed persistent-profile launch shape documented in `AGENTS.md`.

OpenCode remains a repo-MCP owner for Chrome DevTools. Do not install an additional OpenCode Chrome DevTools plugin or second `mcp.chrome-devtools` entry unless the existing repo-managed entry is disabled or replaced in the same change.

### Subagent Delegation

When using OpenCode subagents or modes, inherit the invoking primary agent and harness runtime settings. Do not add subagent or mode model overrides unless the user explicitly asks for that workflow.

### Dynamic Context Pruning

The live DCP config at `~/.config/opencode/dcp.jsonc` is managed from repo canonical `config/opencode-dcp.jsonc`. It is tuned for long orchestration sessions with stable `range` compression and model-agnostic percentage thresholds.

Keep DCP model-neutral: do not add `compress.modelMaxLimits` or `compress.modelMinLimits` unless the user explicitly requests per-model context limits.

## Security & Secret Handling

### Credential Guard Plugin

A custom `credential-guard.ts` plugin is deployed via `sync_agent_stack.py` to `~/.config/opencode/plugins/`. It blocks AI tools from accessing sensitive files and commands:

**Blocked file patterns:**

- `.env*` files (except `.env.example`, `.env.sample`, `.env.template`, `.env.test`)
- `.pem`, `.p12`, `.pfx`, `.key` files
- `credentials.json`, `auth.json`, `secrets.toml`
- AWS, Docker, K8s, npm, SSH credential files

**Blocked bash commands:**

- File readers (`cat`, `less`, `head`, `tail`, etc.) on sensitive paths
- Password extractors (`security find-password`, `gh auth token`, `gcloud auth print-access-token`, etc.)
- Raw kubectl config dumps with `--raw`

### Scoped Bypass For Legitimate Use

Set the environment variable only for the specific command or short-lived shell that needs secret access:

```bash
OPENCODE_ALLOW_SECRET_FILES=1 opencode
```

**When to use:**

- Secret rotation or `.env` file editing requested by the user
- Debugging credential-related issues with explicit user approval
- Working with test/sample credentials that are safe to inspect

**Cleanup:**

```bash
unset OPENCODE_ALLOW_SECRET_FILES
```

Do not add `OPENCODE_ALLOW_SECRET_FILES` to shell profiles, repo config, or committed files. The guard exists to prevent accidental credential exposure in AI context windows.
