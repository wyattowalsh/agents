# OpenCode Global Instructions

@./instructions/global.md

## OpenCode-Specific Overrides

### Model Preference

Use `opencode-go/kimi-k2.6` for all tasks, subagents, modes, and agents unless the user explicitly requests otherwise. This is the built-in provider/model pair for the OpenCode agent environment.

When editing OpenCode configuration files, enforce:
- `model`: `opencode-go/kimi-k2.6`
- `small_model`: `opencode-go/kimi-k2.6`
- `mode.*.model`: `opencode-go/kimi-k2.6`
- `agent.*.model`: `opencode-go/kimi-k2.6`

### Notification Setup

On macOS, ensure `notification_method` is set to `"auto"` in `~/.config/opencode/tui.json` to enable OSC terminal notifications and avoid osascript "Script Editor" popups.

### Subagent Delegation

When using OpenCode subagents or modes (`build`, `plan`, etc.), always inherit the parent model settings unless a different model is explicitly required for the subtask.

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
