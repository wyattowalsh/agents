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
