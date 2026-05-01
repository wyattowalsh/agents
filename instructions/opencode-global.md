# OpenCode Global Instructions

@./instructions/global.md

## OpenCode-Specific Overrides

### Model Preference

Repo-managed OpenCode configuration and agent frontmatter must stay model-free. Do not add `model`, `small_model`, `mode.*.model`, or `agent.*.model` selectors to repo-managed OpenCode surfaces.

Repo-managed OpenCode agent frontmatter must also avoid `steps` caps. Optimize for frontier high-thinking execution through instructions, decomposition, verification, and low deterministic temperatures rather than model selectors or step limits.

When merging live user-owned OpenCode config, preserve existing user model settings; do not introduce repo defaults for them.

### Notification Setup

On macOS, ensure `notification_method` is set to `"auto"` in `~/.config/opencode/tui.json` to enable OSC terminal notifications and avoid osascript "Script Editor" popups.

### Plugin Versioning

Repo-managed OpenCode npm plugin specs in `opencode.json` must use `@latest` so OpenCode's Bun-backed installer resolves the newest published plugin during install refreshes. If a plugin warns that an update is available, refresh the matching package under `~/.cache/opencode/packages/` or restart OpenCode; do not pin or range the repo-managed spec unless the user explicitly requests a rollback.

### Plugin Placement

Keep OpenCode runtime plugins in `opencode.json` and the live `~/.config/opencode/opencode.json` `plugin` array. Keep TUI-only plugins in `~/.config/opencode/tui.json` instead of the repo runtime mirror unless a repo-managed TUI source file is explicitly introduced.

Current TUI-only additions on this machine are `opencode-subagent-statusline@latest` and `@slkiser/opencode-quota@latest`. Preserve `notification_method: "auto"` when editing `tui.json`.

### Scheduler And Auth Plugins

`opencode-scheduler@latest` is installed only as an inert scheduler plugin by default. Do not create, enable, or mutate scheduled jobs unless the user explicitly asks for scheduler job changes; start with read-only jobs and explicit timeouts when jobs are requested.

`opencode-claude-auth@latest` may reuse Claude Code credentials for Anthropic auth. Do not enable optional 1M context behavior or other model/runtime overrides by default; preserve the repo-managed model-neutral policy.

CodeMCP workflow plugins are intentionally deferred. Do not add `@codemcp/workflows-opencode@latest`, `@codemcp/workflows-opencode-tui@latest`, or run broad CodeMCP setup commands unless the user explicitly requests local workflow-state management and accepts the additional artifacts those plugins can create.

### Langfuse Telemetry

`opencode-plugin-langfuse@latest` requires OpenTelemetry support and user-owned environment variables. It is safe for repo config to enable `experimental.openTelemetry`; never commit Langfuse credential values. Required environment keys are `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`; `LANGFUSE_BASEURL` is optional for non-default endpoints.

Treat missing Langfuse environment variables as setup warnings unless OpenCode reports a plugin load failure. Keep `@devtheops/opencode-plugin-otel@latest` until startup validation proves a concrete conflict.

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

### Subagent Delegation

When using OpenCode subagents or modes (`build`, `plan`, etc.), inherit the invoking primary agent and harness runtime settings. Do not add repo-managed subagent or mode model overrides.

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

### Bypass for Legitimate Use

Set the environment variable to intentionally bypass the guard:

```bash
export OPENCODE_ALLOW_SECRET_FILES=1
```

**When to use:**
- Secret rotation or `.env` file editing
- Debugging credential-related issues
- Working with test/sample credentials only

**Add to your shell profile for persistence:**
```bash
echo 'export OPENCODE_ALLOW_SECRET_FILES=1' >> ~/.zshrc
```

> ⚠️ **Warning:** Only enable this when actively working with secrets. The guard exists to prevent accidental credential exposure in AI context windows.
