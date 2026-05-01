# Design

## Approach

Use the existing split between repo-managed runtime config and live user TUI config. Keep repo `opencode.json` limited to runtime npm plugins, add TUI-only plugins only to the live `tui.json`, and document the split so future syncs do not flatten these surfaces together.

## Data And Control Flow

- Repo `opencode.json` mirrors the runtime plugin specs that OpenCode can install with Bun.
- Live `~/.config/opencode/opencode.json` carries the same runtime plugin inventory plus user-owned providers, MCP servers, permissions, and secrets.
- Live `~/.config/opencode/tui.json` carries UI/TUI behavior, including `notification_method` and TUI plugin specs.
- Langfuse uses OpenTelemetry activation plus environment variables supplied outside version control.
- Plannotator registers `submit_plan` only for configured planning agents so build/default agents do not see the plan-review tool.

## Integration Points

- Runtime plugins:
  - `opencode-scheduler@latest`
  - `opencode-claude-auth@latest`
  - `@plannotator/opencode@latest` with `workflow: "plan-agent"` and `planningAgents: ["plan"]`
  - `opencode-plugin-langfuse@latest`
- TUI plugins:
  - `opencode-subagent-statusline@latest`
- Existing runtime plugins remain unchanged, including `@devtheops/opencode-plugin-otel@latest` until validation shows a concrete conflict.

## Alternatives Rejected

- Add every discovered UI plugin now: rejected because several candidates duplicate current quota/notify/canvas behavior or introduce remote-control/browser/tunnel surfaces.
- Put TUI plugins in repo `opencode.json`: rejected because live `tui.json` is the observed TUI plugin surface and repo `opencode.json` is the runtime mirror.
- Keep `open-plan-annotator@latest`: rejected because Plannotator's plan-agent workflow better preserves the plan/execution boundary.
- Add CodeMCP workflow plugins automatically: rejected by user request because the workflow plugins can create local workflow state and setup artifacts.
- Enable Claude Auth 1M context by default: rejected because it changes model/runtime behavior and conflicts with repo-managed model-neutral policy.

## Migration Or Compatibility Notes

- Missing Langfuse environment variables should be documented as setup warnings, not treated as secret values to commit.
- Plannotator should remain configured with an option tuple rather than a bare string so the intended workflow stays explicit in review.
- Scheduler is installed but inert until a user creates jobs.
- Future repo-managed TUI source files can add tests for TUI inventory; this pass only updates the live TUI config and docs it in the manifest.
